"""Validate backup relationships before replacing any saved records."""


def validate_backup(payload, required_tables, history_tables):
    if not isinstance(payload, dict) or not isinstance(payload.get("tables"), dict):
        raise ValueError("Backup file is not valid.")
    if payload.get("backupVersion", 1) not in (1, 2):
        raise ValueError("Unsupported backup version.")
    tables = payload["tables"]
    missing = set(required_tables) - set(tables)
    if missing:
        raise ValueError(f"Backup is missing tables: {', '.join(sorted(missing))}")
    keys = {table: table + "ID" for table in required_tables}
    keys.update(ChangeLog="ChangeID", ReportSnapshot="ReportID", ImportBatch="BatchKey")
    indexed = {}
    for table in required_tables + history_tables:
        rows = tables.get(table, [])
        if not isinstance(rows, list):
            raise ValueError(f"{table} must contain a list of records.")
        indexed[table] = {}
        for row in rows:
            if not isinstance(row, dict) or row.get(keys[table]) is None:
                raise ValueError(f"Invalid {table} record or missing identifier.")
            key = str(row[keys[table]])
            if table != "ImportBatch":
                try:
                    key = str(int(key))
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid identifier in {table}.")
            if key in indexed[table]:
                raise ValueError(f"Duplicate identifier in {table}.")
            indexed[table][key] = row
    relationships = [
        ("Contact", "EmployerID", "Employer"), ("Carrier", "EmployerID", "Employer"),
        ("Tier", "EmployerID", "Employer"), ("Plan", "EmployerID", "Employer"),
        ("Plan", "CarrierID", "Carrier"), ("Plan", "TierID", "Tier"),
        ("Employee", "EmployerID", "Employer"), ("EmployeePlan", "EmployeeID", "Employee"),
        ("EmployeePlan", "PlanID", "Plan"), ("Dependent", "EmployeeID", "Employee")
    ]
    for source, field, target in relationships:
        for row in indexed[source].values():
            try:
                key = str(int(row[field]))
            except (KeyError, TypeError, ValueError):
                raise ValueError(f"{source} has an invalid {field}.")
            if key not in indexed[target]:
                raise ValueError(f"{source} references a missing {target} record.")
    for plan in indexed["Plan"].values():
        for field, table in (("CarrierID", "Carrier"), ("TierID", "Tier")):
            parent = indexed[table][str(int(plan[field]))]
            if int(parent["EmployerID"]) != int(plan["EmployerID"]):
                raise ValueError("Plan carrier/tier belongs to a different company.")
    for enrollment in indexed["EmployeePlan"].values():
        employee = indexed["Employee"][str(int(enrollment["EmployeeID"]))]
        plan = indexed["Plan"][str(int(enrollment["PlanID"]))]
        if int(employee["EmployerID"]) != int(plan["EmployerID"]):
            raise ValueError("Enrollment plan belongs to a different company.")
    # Saved bills and audit records intentionally survive company deletion.
    return tables
