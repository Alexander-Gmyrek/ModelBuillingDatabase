"""Validate roster uploads before making an atomic, retry-safe import."""
from datetime import date
from flask import jsonify, request
from history import record_change


def validate_roster(cursor, employer_id, employees, get_record, get_tier):
    employer = get_record(cursor, "Employer", employer_id)
    cursor.execute("SELECT EmployeeFullName FROM Employee WHERE EmployerID = %s", (employer_id,))
    existing = {row[0].strip().casefold() for row in cursor.fetchall()}
    errors, warnings, accepted, seen = [], [], [], set()
    if not isinstance(employees, list) or not employees:
        raise ValueError("Upload at least one employee.")
    for index, source in enumerate(employees, 1):
        try:
            employee = dict(source)
            name = str(employee.get("EmployeeFullName") or "").strip()
            if not name:
                raise ValueError("Employee name is required.")
            if name.casefold() in seen:
                raise ValueError("Duplicate employee name in upload. Review these rows individually.")
            seen.add(name.casefold())
            if name.casefold() in existing:
                warnings.append(f"Employee {index}: already exists and will be skipped.")
                continue
            start = date.fromisoformat(employee["StartDate"])
            informed = date.fromisoformat(employee.get("InformStartDate") or employee["StartDate"])
            employee["InformStartDate"] = informed.isoformat()
            if informed < start:
                warnings.append(f"Employee {index}: informed date precedes coverage start.")
            if not employee.get("Carrier"):
                raise ValueError("Carrier is required.")
            cursor.execute("SELECT CarrierID FROM Carrier WHERE EmployerID = %s AND CarrierName = %s",
                           (employer_id, employee["Carrier"]))
            carrier = cursor.fetchone()
            if not carrier:
                raise ValueError("Carrier does not match this company's plan setup.")
            tier_id = get_tier(cursor, employee.get("Tier"), employee.get("DOB"), employer_id, start.year)
            cursor.execute("""SELECT PlanID FROM Plan WHERE EmployerID = %s AND CarrierID = %s
                AND TierID = %s AND StartDate <= %s AND (EndDate IS NULL OR EndDate > %s)""",
                           (employer_id, carrier[0], tier_id, start, start))
            if len(cursor.fetchall()) != 1:
                raise ValueError("Exactly one plan must cover this carrier, tier and coverage start date.")
            for dependent in employee.get("Dependents", []):
                if not all(dependent.get(field) for field in ("DependentName", "Relationship", "DOB")):
                    raise ValueError("Dependent name, relationship and birth date are required.")
                date.fromisoformat(dependent["DOB"])
                dependent["StartDate"] = dependent.get("StartDate") or employee["StartDate"]
                dependent["InformStartDate"] = dependent.get("InformStartDate") or employee["InformStartDate"]
                date.fromisoformat(dependent["StartDate"])
                date.fromisoformat(dependent["InformStartDate"])
            employee["EmployerID"] = employer_id
            employee.pop("EmployeeID", None)
            accepted.append(employee)
        except (ValueError, TypeError, KeyError) as error:
            errors.append(f"Employee {index}: {error}")
    return {"EmployeeCount": len(employees), "NewCount": len(accepted),
            "SkippedCount": len(employees) - len(accepted) - len(errors),
            "Errors": errors, "Warnings": warnings}, accepted


def register_import_routes(app, connect, get_record, get_tier, add_record):
    def run_import(employer_id, commit):
        payload = request.get_json() or {}
        connection = connect()
        cursor = connection.cursor()
        try:
            # Lock the company to serialize repeated/concurrent roster submissions.
            cursor.execute("SELECT EmployerID FROM Employer WHERE EmployerID = %s FOR UPDATE", (employer_id,))
            if not cursor.fetchone():
                raise ValueError("Company not found.")
            batch_key = payload.get("BatchKey")
            if commit:
                if not isinstance(batch_key, str) or not 16 <= len(batch_key) <= 64:
                    raise ValueError("An import batch key is required.")
                cursor.execute("SELECT EmployerID, EmployeeCount FROM ImportBatch WHERE BatchKey = %s", (batch_key,))
                prior = cursor.fetchone()
                if prior:
                    if prior[0] != employer_id:
                        raise ValueError("Import key belongs to another company.")
                    return jsonify({"message": "This upload was already imported.", "ImportedCount": prior[1]})
            preview, employees = validate_roster(cursor, employer_id, payload.get("Employees"), get_record, get_tier)
            if not commit:
                return jsonify(preview)
            if preview["Errors"]:
                return jsonify({"Error": "Correct the preview errors before importing.", **preview}), 400
            for employee in employees:
                add_record(cursor, "Employee", employee)
            cursor.execute("INSERT INTO ImportBatch (BatchKey, EmployerID, EmployeeCount) VALUES (%s, %s, %s)",
                           (batch_key, employer_id, len(employees)))
            record_change(cursor, "Import", "Employer", employer_id,
                          after={"ImportedCount": len(employees), "SkippedCount": preview["SkippedCount"]})
            connection.commit()
            return jsonify({"message": "Employees imported.", "ImportedCount": len(employees), **preview})
        except Exception as error:
            connection.rollback()
            return jsonify({"Error": str(error)}), 400
        finally:
            cursor.close()
            connection.close()

    app.add_url_rule("/employer/<int:employer_id>/import/preview", "preview_employee_import",
                     lambda employer_id: run_import(employer_id, False), methods=["POST"])
    app.add_url_rule("/employer/<int:employer_id>/import", "commit_employee_import",
                     lambda employer_id: run_import(employer_id, True), methods=["POST"])
