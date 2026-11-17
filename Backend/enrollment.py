"""Effective-dated employee carrier and plan changes."""
from datetime import date


def change_enrollment(cursor, employee, change, get_record, add_record, update_record):
    effective = date.fromisoformat(change["StartDate"])
    informed = date.fromisoformat(change.get("InformStartDate") or change["StartDate"])
    if effective < date.fromisoformat(str(employee["StartDate"])):
        raise ValueError("Plan change cannot precede employee coverage start.")
    if employee.get("EndDate") and effective >= date.fromisoformat(str(employee["EndDate"])):
        raise ValueError("Plan change must precede employee termination.")
    target = get_record(cursor, "Plan", int(change["PlanID"]))
    if int(target["EmployerID"]) != int(employee["EmployerID"]):
        raise ValueError("Selected plan belongs to another company.")
    if effective < date.fromisoformat(str(target["StartDate"])) or (
        target.get("EndDate") and effective >= date.fromisoformat(str(target["EndDate"]))
    ):
        raise ValueError("Selected plan does not cover the effective date.")
    cursor.execute("""SELECT EmployeePlanID, PlanID FROM EmployeePlan WHERE EmployeeID = %s
        AND StartDate <= %s AND (EndDate IS NULL OR EndDate > %s)""",
                   (employee["EmployeeID"], effective, effective))
    previous = cursor.fetchall()
    if len(previous) != 1:
        raise ValueError("Exactly one existing enrollment must cover the effective date.")
    if int(previous[0][1]) == int(change["PlanID"]):
        return
    cursor.execute("SELECT COUNT(*) FROM EmployeePlan WHERE EmployeeID = %s AND StartDate > %s",
                   (employee["EmployeeID"], effective))
    if cursor.fetchone()[0]:
        raise ValueError("A later plan change already exists. Review that change before inserting an earlier one.")
    update_record(cursor, "EmployeePlan", previous[0][0],
                  {"EndDate": effective.isoformat(), "InformEndDate": informed.isoformat()})
    add_record(cursor, "EmployeePlan", {
        "EmployeeID": employee["EmployeeID"], "PlanID": int(change["PlanID"]),
        "StartDate": effective.isoformat(), "InformStartDate": informed.isoformat(),
        "EndDate": None, "InformEndDate": None
    })
