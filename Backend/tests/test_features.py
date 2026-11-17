"""API and workbook checks with synthetic data and an isolated SQLite adapter."""
import io
import sqlite3
import re
import sys
import unittest
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parents[1]))
import app as billing
from flask import Flask
from openpyxl import load_workbook
from history import register_routes, record_change
from employee_import import register_import_routes


class Cursor:
    def __init__(self, database):
        self.cursor = database.cursor()

    def execute(self, sql, params=()):
        if sql.startswith("SET FOREIGN_KEY_CHECKS"):
            return self
        if sql.startswith("SHOW COLUMNS FROM "):
            table = sql.split()[-1]
            self.cursor.execute("SELECT name FROM pragma_table_info(?)", (table,))
            return self
        params = tuple(value.isoformat() if isinstance(value, (date, datetime))
                       else str(value) if isinstance(value, Decimal) else value for value in params)
        self.cursor.execute(sql.replace("%s", "?").replace(" FOR UPDATE", ""), params)
        return self

    @property
    def lastrowid(self):
        return self.cursor.lastrowid

    @property
    def description(self):
        return self.cursor.description

    def convert(self, row):
        if row is None:
            return None
        values = list(row)
        for index, column in enumerate(self.description or []):
            if values[index] is not None and (column[0].endswith("Date") or column[0] in ("DOB", "BillingMonth")):
                values[index] = date.fromisoformat(values[index])
            if column[0] == "CreatedAt":
                values[index] = datetime.fromisoformat(values[index])
            if values[index] is not None and column[0] in ("FundingAmount", "GrenzFee", "GrenzFeeC", "GrenzFeeS"):
                values[index] = Decimal(str(values[index]))
        return tuple(values)

    def fetchone(self):
        return self.convert(self.cursor.fetchone())

    def fetchall(self):
        return [self.convert(row) for row in self.cursor.fetchall()]

    def close(self):
        self.cursor.close()


class Database:
    def __init__(self):
        self.database = sqlite3.connect(":memory:")
        self.database.executescript("""
            CREATE TABLE Employer (EmployerID INTEGER PRIMARY KEY, EmployerName TEXT);
            INSERT INTO Employer VALUES (1, 'Example');
            CREATE TABLE Employee (EmployeeID INTEGER PRIMARY KEY, EmployerID INT, EmployeeFullName TEXT);
            CREATE TABLE Carrier (CarrierID INTEGER PRIMARY KEY, EmployerID INT, CarrierName TEXT);
            INSERT INTO Carrier VALUES (1, 1, 'Example Carrier');
            CREATE TABLE Plan (PlanID INTEGER PRIMARY KEY, EmployerID INT, CarrierID INT,
                TierID INT, StartDate TEXT, EndDate TEXT);
            INSERT INTO Plan VALUES (1, 1, 1, 1, '2026-01-01', NULL);
            CREATE TABLE ImportBatch (BatchKey TEXT PRIMARY KEY, EmployerID INT, EmployeeCount INT);
            CREATE TABLE ReportSnapshot (ReportID INTEGER PRIMARY KEY, EmployerID INT, BillingMonth TEXT,
                CreatedAt TEXT DEFAULT CURRENT_TIMESTAMP, Filename TEXT, Workbook BLOB);
            CREATE TABLE ChangeLog (ChangeID INTEGER PRIMARY KEY, CreatedAt TEXT DEFAULT CURRENT_TIMESTAMP,
                EmployerID INT, Action TEXT, TableName TEXT, RecordID INT, BeforeData TEXT, AfterData TEXT);
        """)

    def cursor(self):
        return Cursor(self.database)

    def commit(self):
        self.database.commit()

    def rollback(self):
        self.database.rollback()

    def close(self):
        pass


class FeatureTests(unittest.TestCase):
    def setUp(self):
        self.db = Database()
        self.app = Flask(__name__)
        register_routes(self.app, lambda: self.db)
        self.added = []

        def add(cursor, table, employee):
            cursor.execute("INSERT INTO Employee (EmployerID, EmployeeFullName) VALUES (%s,%s)",
                           (employee["EmployerID"], employee["EmployeeFullName"]))
            self.added.append(employee)
        register_import_routes(self.app, lambda: self.db,
                               lambda *args: {"EmployerID": 1},
                               lambda *args: 1, add)
        self.client = self.app.test_client()
        self.employee = {"EmployeeFullName": "Synthetic Employee", "Carrier": "Example Carrier",
                         "Tier": "Employee", "StartDate": "2026-01-01",
                         "InformStartDate": "2026-06-01", "Dependents": []}

    def tearDown(self):
        self.db.database.close()

    def test_import_preview_and_retry_safe_commit(self):
        payload = {"Employees": [self.employee], "BatchKey": "synthetic-batch-key"}
        preview = self.client.post("/employer/1/import/preview", json=payload)
        self.assertEqual(preview.status_code, 200)
        self.assertEqual(preview.json["NewCount"], 1)
        self.assertFalse(self.added)
        first = self.client.post("/employer/1/import", json=payload)
        second = self.client.post("/employer/1/import", json=payload)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(len(self.added), 1)
        self.assertEqual(self.client.get("/employer/1/history").json[0]["Action"], "Import")

    def test_import_coverage_error_prevents_writes(self):
        employee = {**self.employee, "StartDate": "2025-01-01"}
        payload = {"Employees": [employee], "BatchKey": "synthetic-batch-key"}
        self.assertTrue(self.client.post("/employer/1/import/preview", json=payload).json["Errors"])
        self.assertEqual(self.client.post("/employer/1/import", json=payload).status_code, 400)
        self.assertFalse(self.added)

    def test_existing_employee_is_skipped(self):
        self.db.database.execute("INSERT INTO Employee VALUES (1,1,'Synthetic Employee')")
        result = self.client.post("/employer/1/import/preview", json={"Employees": [self.employee]})
        self.assertEqual(result.json["SkippedCount"], 1)
        self.assertEqual(result.json["NewCount"], 0)

    def test_saved_bill_download_is_immutable(self):
        self.db.database.execute("""INSERT INTO ReportSnapshot
            (EmployerID,BillingMonth,Filename,Workbook) VALUES (1,'2026-06-01','bill.xlsx',?)""",
                                 (b"original workbook",))
        self.db.database.commit()
        self.db.database.execute("UPDATE Employer SET EmployerName='Changed'")
        listing = self.client.get("/employer/1/reports")
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.json[0]["BillingMonth"], "2026-06-01")
        saved = self.client.get("/employer/1/reports/1")
        self.assertEqual(saved.data, b"original workbook")
        self.assertEqual(self.client.get("/employer/2/reports/1").status_code, 404)

    def test_history_records_before_and_after_and_paginates(self):
        cursor = self.db.cursor()
        record_change(cursor, "Update", "Employee", 1,
                      before={"EmployerID": 1, "Notes": "old"},
                      after={"EmployerID": 1, "Notes": "new"})
        self.db.commit()
        changes = self.client.get("/employer/1/history").json
        self.assertEqual(changes[0]["Before"]["Notes"], "old")
        self.assertEqual(changes[0]["After"]["Notes"], "new")
        self.assertEqual(self.client.get("/employer/1/history?before=1").json, [])

    def test_dependent_credit_details_reconcile(self):
        cursor = Mock()
        cursor.fetchone.return_value = ("Synthetic Child", "Child", date(2026, 1, 1),
                                        date(2026, 1, 1), date(2026, 3, 1), date(2026, 6, 15))
        with patch.object(billing, "get_dependent_fund_info",
                          return_value=(Decimal("50"), Decimal("5"), "Child")):
            result = billing.process_dependent(cursor, 2, date(2026, 6, 1), 1, 1)
        self.assertEqual(result["FundingAmount"], Decimal("-150"))
        self.assertEqual(sum(line["FundingAmount"] for line in result["Adjustments"]), Decimal("-150"))
        self.assertEqual({line["Month"] for line in result["Adjustments"]},
                         {"2026-03-01", "2026-04-01", "2026-05-01", "2026-06-01"})

    def test_workbook_contains_monthly_adjustment_breakdown(self):
        current = (1, "Current", date(2026, 1, 1), date(2026, 1, 1), None, None)
        late_add = (2, "Late add", date(2026, 3, 1), date(2026, 6, 15), None, None)
        late_term = (3, "Late term", date(2026, 1, 1), date(2026, 1, 1),
                     date(2026, 3, 1), date(2026, 6, 15))
        connection = Mock()
        connection.cursor.return_value.fetchone.return_value = (1, "4 Tier", 0, 0, 0, 0)
        def query(cursor, sql):
            if "EmployeeFullName" in sql:
                return [current, late_add, late_term]
            if "FROM EmployeePlan" in sql:
                return [(1, date(2026, 1, 1), date(2026, 1, 1), None, None)]
            if "SELECT DOB" in sql:
                return [(date(1990, 1, 1),)]
            raise AssertionError(sql)
        with (
            patch.object(billing, "execute_query", side_effect=query),
            patch.object(billing, "get_plan_for_employee", return_value=1),
            patch.object(billing, "calculate_funding_amount_normal",
                         return_value=(Decimal("100"), Decimal("10"), "Carrier", "Employee", [])),
        ):
            output = io.BytesIO()
            billing.generate_report(connection, "Example", date(2026, 6, 1), output=output)
        workbook = load_workbook(io.BytesIO(output.getvalue()), data_only=True)
        self.assertEqual(workbook.sheetnames, ["Monthly Bill", "Adjustment Details"])
        rows = list(workbook["Adjustment Details"].values)
        self.assertEqual(len(rows), 9)
        self.assertEqual(sum(Decimal(str(row[-1])) for row in rows[1:]), Decimal("220"))
        credits = [row for row in rows[1:] if row[3] == "Late termination credit"]
        self.assertEqual([row[2] for row in credits], ["2026-03", "2026-04", "2026-05"])


class BillingWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.db = Database()
        cursor = self.db.database
        for table in ["Employer", "Employee", "Carrier", "Plan"]:
            cursor.execute(f"DROP TABLE {table}")
        schema = (Path(__file__).parents[1] / "init.sql").read_text()
        schema = re.sub(r"CREATE DATABASE[^;]+;|USE [^;]+;", "", schema)
        schema = re.sub(r"(\w+ID) INT AUTO_INCREMENT", r"\1 INTEGER PRIMARY KEY AUTOINCREMENT", schema)
        schema = re.sub(r"\s*PRIMARY KEY \(\w+\),?", "", schema)
        schema = re.sub(r",\s*\)", "\n)", schema)
        cursor.executescript(schema)
        cursor.execute("""INSERT INTO Employer
            (EmployerID,EmployerName,TierStructure,RenewalDate,UsesGlCode,UsesDivision,UsesLocation,UsesTitle)
            VALUES (1,'Synthetic Company','4 Tier','2026-01-01',0,0,0,0)""")
        cursor.execute("INSERT INTO Carrier VALUES (1,1,'Carrier A')")
        cursor.execute("INSERT INTO Carrier VALUES (2,1,'Carrier B')")
        cursor.execute("INSERT INTO Tier VALUES (1,1,'Employee',NULL,NULL)")
        cursor.execute("""INSERT INTO Plan (PlanID,EmployerID,PlanName,CarrierID,TierID,
            FundingAmount,GrenzFee,GrenzFeeC,GrenzFeeS,StartDate)
            VALUES (1,1,'Plan A',1,1,100,10,0,0,'2026-01-01')""")
        cursor.execute("""INSERT INTO Plan (PlanID,EmployerID,PlanName,CarrierID,TierID,
            FundingAmount,GrenzFee,GrenzFeeC,GrenzFeeS,StartDate)
            VALUES (2,1,'Plan B',2,1,200,20,0,0,'2026-01-01')""")
        self.db.commit()
        self.connection_patch = patch.object(billing, "get_db_connection", lambda **kwargs: self.db)
        self.connection_patch.start()
        self.client = billing.app.test_client()
        result = self.client.post("/employee", json={
            "EmployerID": 1, "EmployeeFullName": "Synthetic Employee",
            "StartDate": "2026-01-01", "InformStartDate": "2026-01-01",
            "Carrier": "Carrier A", "Tier": "Employee", "DOB": "1990-01-01",
            "Dependents": [],
        })
        self.assertEqual(result.status_code, 201, result.json)
        self.employee_id = result.json["new_id"]

    def tearDown(self):
        self.connection_patch.stop()
        self.db.database.close()

    def bill(self, month):
        result = self.client.get(f"/test/generatereport/1/2026/{month}")
        self.assertEqual(result.status_code, 200, result.json)
        workbook = load_workbook(io.BytesIO(result.data), data_only=True)
        total = list(workbook["Monthly Bill"].values)[-1][-1]
        return Decimal(str(total or 0)), result.data

    def test_termination_and_billing_after_termination(self):
        self.assertEqual(self.bill(2)[0], Decimal("110"))
        result = self.client.patch(f"/employee/{self.employee_id}/terminate",
                                   json={"EndDate": "2026-03-01", "InformEndDate": "2026-03-01"})
        self.assertEqual(result.status_code, 200, result.json)
        self.assertEqual(self.bill(3)[0], 0)
        self.assertEqual(self.bill(4)[0], 0)
        self.assertEqual(self.db.database.execute("SELECT EndDate FROM EmployeePlan").fetchone()[0], "2026-03-01")

    def test_late_termination_credit_once(self):
        result = self.client.patch(f"/employee/{self.employee_id}/terminate",
                                   json={"EndDate": "2026-03-01", "InformEndDate": "2026-06-15"})
        self.assertEqual(result.status_code, 200, result.json)
        self.assertEqual(self.bill(6)[0], Decimal("-330"))
        self.assertEqual(self.bill(7)[0], 0)

    def test_plan_and_carrier_change_preserves_history_and_bills(self):
        result = self.client.patch(f"/employee/{self.employee_id}/details", json={
            "Employee": {"EmployeeFullName": "Renamed Employee", "StartDate": "2026-01-01", "Notes": "Updated"},
            "Dependents": [], "PlanChange": {"PlanID": 2, "StartDate": "2026-03-01", "InformStartDate": "2026-06-15"}
        })
        self.assertEqual(result.status_code, 200, result.json)
        rows = self.db.database.execute("SELECT PlanID,StartDate,EndDate FROM EmployeePlan ORDER BY EmployeePlanID").fetchall()
        self.assertEqual(rows, [(1,"2026-01-01","2026-03-01"), (2,"2026-03-01",None)])
        self.assertEqual(self.bill(2)[0], Decimal("110"))
        self.assertEqual(self.bill(6)[0], Decimal("550"))
        self.assertEqual(self.bill(7)[0], Decimal("220"))
        self.assertEqual(self.db.database.execute("SELECT EmployeeFullName,Notes FROM Employee").fetchone(),
                         ("Renamed Employee", "Updated"))

    def test_invalid_plan_change_rolls_back_profile_edit(self):
        result = self.client.patch(f"/employee/{self.employee_id}/details", json={
            "Employee": {"EmployeeFullName": "Should Roll Back", "StartDate": "2026-01-01"},
            "Dependents": [], "PlanChange": {"PlanID": 999, "StartDate": "2026-03-01"}
        })
        self.assertEqual(result.status_code, 400)
        self.assertEqual(self.db.database.execute("SELECT EmployeeFullName FROM Employee").fetchone()[0],
                         "Synthetic Employee")

    def test_company_import_assigns_employee_to_renamed_carrier(self):
        response = self.client.post("/employer", json={
            "EmployerName": "Renamed Carrier Import", "TierStructure": "4 Tier",
            "RenewalDate": "2026-01-01", "PerferedBillingDate": "2026-01-01",
            "Carriers": [{"CarrierName": "Renamed Carrier"}],
            "Tiers": [{"TierName": "Employee"}],
            "Plans": [{"CarrierName": "Renamed Carrier", "TierName": "Employee",
                       "StartDate": "2026-01-01", "FundingAmount": "100", "GrenzFee": "10"}],
            "Employees": [{"EmployeeFullName": "Imported Employee", "Carrier": "Renamed Carrier",
                           "Tier": "Employee", "StartDate": "2026-01-01",
                           "InformStartDate": "2026-01-01", "Dependents": []}]
        })
        self.assertEqual(response.status_code, 201, response.json)
        assigned = self.db.database.execute("""SELECT Carrier.CarrierName FROM Employee
            JOIN EmployeePlan ON Employee.EmployeeID = EmployeePlan.EmployeeID
            JOIN Plan ON EmployeePlan.PlanID = Plan.PlanID
            JOIN Carrier ON Plan.CarrierID = Carrier.CarrierID
            WHERE Employee.EmployerID = ?""", (response.json["new_id"],)).fetchone()
        self.assertEqual(assigned[0], "Renamed Carrier")

    def test_cobra_boolean_and_unchanged_profile_save(self):
        for value in (True, False, None):
            self.db.database.execute("UPDATE Employee SET CobraStatus=? WHERE EmployeeID=?",
                                     (value, self.employee_id))
            self.db.commit()
            employee = self.client.get(f"/employee/{self.employee_id}").json
            self.assertIs(employee["CobraStatus"], value)
            response = self.client.patch(f"/employee/{self.employee_id}/details", json={
                "Employee": {"EmployeeFullName": "Synthetic Employee", "StartDate": "2026-01-01",
                             "Notes": "Unrelated edit"}, "Dependents": []
            })
            self.assertEqual(response.status_code, 200, response.json)
            self.assertIs(self.client.get(f"/employee/{self.employee_id}").json["CobraStatus"], value)
        for value in (True, False):
            response = self.client.patch(f"/employee/{self.employee_id}/details", json={
                "Employee": {"EmployeeFullName": "Synthetic Employee", "StartDate": "2026-01-01",
                             "CobraStatus": value}, "Dependents": []
            })
            self.assertEqual(response.status_code, 200, response.json)
            self.assertIs(self.client.get(f"/employee/{self.employee_id}").json["CobraStatus"], value)

    def test_backup_restore_preserves_saved_bills_and_employee_state(self):
        expected, content = self.bill(2)
        backup = billing.create_backup_payload()
        self.assertEqual(backup["backupVersion"], 2)
        self.assertIn("base64", backup["tables"]["ReportSnapshot"][0]["Workbook"])
        self.client.patch(f"/employee/{self.employee_id}", json={"EmployeeFullName": "Changed"})
        billing.restore_backup_payload(backup)
        self.assertEqual(self.db.database.execute("SELECT EmployeeFullName FROM Employee").fetchone()[0],
                         "Synthetic Employee")
        saved = self.db.database.execute("SELECT Workbook FROM ReportSnapshot").fetchone()[0]
        self.assertEqual(saved, content)
        self.assertEqual(self.bill(2)[0], expected)
        self.assertEqual(self.db.database.execute("SELECT Action FROM ChangeLog ORDER BY ChangeID DESC LIMIT 1").fetchone()[0],
                         "Generate bill")

    def test_invalid_backup_rolls_back_database(self):
        backup = billing.create_backup_payload()
        backup["tables"]["Employee"][0]["UnknownColumn"] = "bad"
        with self.assertRaises(ValueError):
            billing.restore_backup_payload(backup)
        self.assertEqual(self.db.database.execute("SELECT EmployeeFullName FROM Employee").fetchone()[0],
                         "Synthetic Employee")

    def test_restore_accepts_older_backup_without_history_tables(self):
        backup = billing.create_backup_payload()
        for table in ("ChangeLog", "ReportSnapshot", "ImportBatch"):
            backup["tables"].pop(table)
        backup["backupVersion"] = 1
        billing.restore_backup_payload(backup)
        self.assertEqual(self.db.database.execute("SELECT COUNT(*) FROM Employee").fetchone()[0], 1)
        self.assertEqual(self.db.database.execute("SELECT Action FROM ChangeLog").fetchone()[0], "Restore")

    def test_termination_closes_dependents_and_rejects_invalid_date(self):
        dependent = self.client.post("/dependent", json={
            "EmployeeID": self.employee_id, "DependentName": "Synthetic Child", "Relationship": "Child",
            "DOB": "2015-01-01", "StartDate": "2026-01-01", "InformStartDate": "2026-01-01"
        })
        self.assertEqual(dependent.status_code, 201, dependent.json)
        invalid = self.client.patch(f"/employee/{self.employee_id}/terminate",
                                    json={"EndDate": "2025-01-01"})
        self.assertEqual(invalid.status_code, 400)
        self.assertIsNone(self.db.database.execute("SELECT EndDate FROM Employee").fetchone()[0])
        valid = self.client.patch(f"/employee/{self.employee_id}/terminate",
                                  json={"EndDate": "2026-03-01", "InformEndDate": "2026-06-15"})
        self.assertEqual(valid.status_code, 200, valid.json)
        self.assertEqual(self.db.database.execute("SELECT EndDate,InformEndDate FROM Dependent").fetchone(),
                         ("2026-03-01", "2026-06-15"))

    def test_billing_after_rate_change_preserves_earlier_rates(self):
        _, original = self.bill(2)
        payload = {
            "effectiveDate": "2026-03-01",
            "Carriers": [{"CarrierID": 1, "CarrierName": "Carrier A"}, {"CarrierID": 2, "CarrierName": "Carrier B"}],
            "Tiers": [{"TierID": 1, "TierName": "Employee", "MinAge": None, "MaxAge": None}],
            "Plans": [
                {"PlanID": 1, "CarrierID": 1, "TierID": 1, "StartDate": "2026-01-01",
                 "FundingAmount": "150", "GrenzFee": "15", "GrenzFeeC": "0", "GrenzFeeS": "0"},
                {"PlanID": 2, "CarrierID": 2, "TierID": 1, "StartDate": "2026-01-01",
                 "FundingAmount": "200", "GrenzFee": "20", "GrenzFeeC": "0", "GrenzFeeS": "0"}
            ]
        }
        result = self.client.patch("/employer/1/plan_setup", json=payload)
        self.assertEqual(result.status_code, 200, result.json)
        self.assertEqual(self.bill(2)[0], Decimal("110"))
        self.assertEqual(self.bill(3)[0], Decimal("165"))
        self.assertEqual(self.bill(4)[0], Decimal("165"))
        self.assertEqual(self.db.database.execute("SELECT Workbook FROM ReportSnapshot ORDER BY ReportID LIMIT 1").fetchone()[0], original)

    def test_termination_after_carrier_switch_credits_new_rate(self):
        result = self.client.patch(f"/employee/{self.employee_id}/details", json={
            "Employee": {"EmployeeFullName": "Synthetic Employee", "StartDate": "2026-01-01"},
            "Dependents": [], "PlanChange": {"PlanID": 2, "StartDate": "2026-03-01", "InformStartDate": "2026-03-01"}
        })
        self.assertEqual(result.status_code, 200, result.json)
        result = self.client.patch(f"/employee/{self.employee_id}/terminate",
                                   json={"EndDate": "2026-04-01", "InformEndDate": "2026-06-15"})
        self.assertEqual(result.status_code, 200, result.json)
        self.assertEqual(self.bill(6)[0], Decimal("-440"))
        self.assertEqual(self.bill(7)[0], 0)


if __name__ == "__main__":
    unittest.main()
