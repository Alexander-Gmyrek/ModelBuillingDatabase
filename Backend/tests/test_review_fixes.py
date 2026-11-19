"""Regression coverage for the deep-review findings."""
import copy
import os
import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import Mock, patch
from urllib.parse import quote

import test_features as fixtures
from monthly_billing import MonthlyBilling


class ReviewFixTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.BillingWorkflowTests()
        self.fixture.setUp()
        self.db = self.fixture.db
        self.client = self.fixture.client
        self.employee_id = self.fixture.employee_id

    def tearDown(self):
        self.fixture.tearDown()

    def test_destructive_test_urls_are_disabled_by_default(self):
        with patch.dict(os.environ, {"BILLING_ENABLE_TEST_TOOLS": "0"}):
            for path in ("/test/cleardb", "/test/resetdb?confirmReset=true",
                         "/test/addemployer", "/test/deleteemployer", "/test/executeCommand"):
                self.assertEqual(self.client.get(path).status_code, 404, path)
        self.assertEqual(self.db.database.execute("SELECT COUNT(*) FROM Employer").fetchone()[0], 1)

    def test_removed_plan_stops_billing_and_preserves_earlier_month(self):
        response = self.client.patch("/employer/1/plan_setup", json={
            "effectiveDate": "2026-03-01",
            "Carriers": [{"CarrierID": 2, "CarrierName": "Carrier B"}],
            "Tiers": [{"TierID": 1, "TierName": "Employee"}],
            "Plans": [{"PlanID": 2, "CarrierID": 2, "TierID": 1,
                       "StartDate": "2026-01-01", "FundingAmount": "200",
                       "GrenzFee": "20", "GrenzFeeC": "0", "GrenzFeeS": "0"}]
        })
        self.assertEqual(response.status_code, 200, response.json)
        self.assertEqual(self.db.database.execute("SELECT EndDate FROM EmployeePlan").fetchone()[0], "2026-03-01")
        self.assertEqual(self.fixture.bill(2)[0], Decimal("110"))
        self.assertEqual(self.fixture.bill(3)[0], 0)
        self.assertEqual(self.fixture.bill(4)[0], 0)

    def test_legacy_removed_plan_without_enrollment_end_is_not_billed(self):
        self.db.database.execute("UPDATE Plan SET EndDate='2026-03-01' WHERE PlanID=1")
        self.db.commit()
        self.assertEqual(self.fixture.bill(2)[0], Decimal("110"))
        self.assertEqual(self.fixture.bill(4)[0], 0)

    def test_invalid_start_correction_rejected_before_saving(self):
        response = self.client.patch(f"/employee/{self.employee_id}/details", json={
            "Employee": {"EmployeeFullName": "Synthetic Employee", "StartDate": "2025-12-15",
                         "InformStartDate": "2026-01-15"}, "Dependents": []
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("historical plan coverage", response.json["Error"])
        self.assertEqual(self.db.database.execute("SELECT StartDate FROM Employee").fetchone()[0], "2026-01-01")
        self.assertEqual(self.fixture.bill(1)[0], Decimal("110"))

    def test_valid_start_correction_updates_enrollment_and_bill(self):
        self.db.database.execute("UPDATE Plan SET StartDate='2025-01-01' WHERE PlanID=1")
        self.db.commit()
        response = self.client.patch(f"/employee/{self.employee_id}/details", json={
            "Employee": {"EmployeeFullName": "Synthetic Employee", "StartDate": "2025-12-15",
                         "InformStartDate": "2026-01-15"}, "Dependents": []
        })
        self.assertEqual(response.status_code, 200, response.json)
        enrollment = self.db.database.execute("SELECT StartDate,InformStartDate FROM EmployeePlan").fetchone()
        self.assertEqual(enrollment, ("2025-12-15", "2026-01-15"))
        self.assertEqual(self.fixture.bill(1)[0], Decimal("220"))

    def test_informed_start_correction_updates_enrollment(self):
        response = self.client.patch(f"/employee/{self.employee_id}", json={"InformStartDate": "2026-03-15"})
        self.assertEqual(response.status_code, 200, response.json)
        self.assertEqual(self.db.database.execute("SELECT InformStartDate FROM EmployeePlan").fetchone()[0], "2026-03-15")
        self.assertEqual(self.fixture.bill(2)[0], 0)
        self.assertEqual(self.fixture.bill(3)[0], Decimal("330"))
        self.assertEqual(self.fixture.bill(4)[0], Decimal("110"))

    def test_restore_rejects_missing_relationships_and_preserves_database(self):
        backup = fixtures.billing.create_backup_payload()
        for table, field in (("Plan", "CarrierID"), ("Plan", "TierID"),
                             ("EmployeePlan", "EmployeeID"), ("EmployeePlan", "PlanID"),
                             ("Employee", "EmployerID")):
            damaged = copy.deepcopy(backup)
            damaged["tables"][table][0][field] = 999999
            with self.assertRaisesRegex(ValueError, "missing"):
                fixtures.billing.restore_backup_payload(damaged)
            self.assertEqual(self.fixture.bill(2)[0], Decimal("110"))

    def test_restore_rejects_cross_company_plan_relationship(self):
        backup = fixtures.billing.create_backup_payload()
        other = dict(backup["tables"]["Employer"][0], EmployerID=2, EmployerName="Other")
        backup["tables"]["Employer"].append(other)
        backup["tables"]["Carrier"][0]["EmployerID"] = 2
        with self.assertRaisesRegex(ValueError, "different company"):
            fixtures.billing.restore_backup_payload(backup)
        self.assertEqual(self.fixture.bill(2)[0], Decimal("110"))

    def test_restore_rejects_bad_shape_version_and_duplicate_ids(self):
        backup = fixtures.billing.create_backup_payload()
        cases = []
        wrong_version = copy.deepcopy(backup)
        wrong_version["backupVersion"] = 999
        cases.append(wrong_version)
        bad_rows = copy.deepcopy(backup)
        bad_rows["tables"]["Employee"] = {}
        cases.append(bad_rows)
        duplicates = copy.deepcopy(backup)
        duplicates["tables"]["Employee"].append(dict(duplicates["tables"]["Employee"][0]))
        cases.append(duplicates)
        for case in cases:
            with self.assertRaises(ValueError):
                fixtures.billing.restore_backup_payload(case)
        self.assertEqual(self.fixture.bill(2)[0], Decimal("110"))

    def test_apostrophe_and_sql_text_are_search_values(self):
        self.db.database.execute("UPDATE Employer SET EmployerName=?", ("O'Brien",))
        self.db.commit()
        response = self.client.get("/employer/" + quote("O'Brien", safe=""))
        self.assertEqual(response.status_code, 200, response.json)
        self.assertEqual(response.json[0]["EmployerName"], "O'Brien")
        injected = self.client.get("/employer/" + quote("' OR 1=1 -- ", safe=""))
        self.assertEqual(injected.status_code, 200)
        self.assertEqual(injected.json, [])
        employees = self.client.get("/employee/1/Synthetic")
        self.assertEqual(employees.status_code, 200, employees.json)
        self.assertEqual(len(employees.json), 1)

    def test_invalid_search_field_is_rejected(self):
        response = self.client.post("/employee/search", json={"EmployeeID OR 1=1 --": 1})
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid search field", response.json["Error"])

    def test_edit_delete_and_search_connections_close(self):
        close = Mock(wraps=self.db.close)
        rollback = Mock(wraps=self.db.rollback)
        with patch.object(self.db, "close", close), patch.object(self.db, "rollback", rollback):
            result = self.client.patch(f"/employee/{self.employee_id}", json={"Notes": "Edited"})
            self.assertEqual(result.status_code, 200)
            self.assertEqual(close.call_count, 1)
            result = self.client.patch("/employee/99999", json={"Notes": "Missing"})
            self.assertEqual(result.status_code, 400)
            self.assertEqual(close.call_count, 2)
            self.assertEqual(rollback.call_count, 1)
            result = self.client.post("/employee/search", json={"BadField": 1})
            self.assertEqual(result.status_code, 400)
            self.assertEqual(close.call_count, 3)
            result = self.client.delete(f"/employee/{self.employee_id}")
            self.assertEqual(result.status_code, 200)
            self.assertEqual(close.call_count, 4)

    def test_age_band_advances_at_renewal_month(self):
        company = {"TierStructure": "Age Banded", "RenewalDate": "2025-11-01"}
        employee = {"EmployeeID": 1, "EmployeeFullName": "Synthetic", "DOB": "2008-05-01",
                    "StartDate": "2025-01-01", "InformStartDate": "2025-01-01"}
        enrollment = {"EmployeePlanID": 1, "EmployeeID": 1, "PlanID": 1,
                      "StartDate": "2025-01-01", "InformStartDate": "2025-01-01"}
        plans = [
            {"PlanID": 1, "CarrierID": 1, "TierID": 1, "StartDate": "2024-01-01",
             "FundingAmount": "50", "GrenzFee": "5"},
            {"PlanID": 2, "CarrierID": 1, "TierID": 2, "StartDate": "2024-01-01",
             "FundingAmount": "100", "GrenzFee": "10"}
        ]
        tiers = [{"TierID": 1, "TierName": "Under 18", "MinAge": 0, "MaxAge": 17},
                 {"TierID": 2, "TierName": "18 plus", "MinAge": 18, "MaxAge": 120}]
        engine = MonthlyBilling(company, [employee], [enrollment], plans,
                                [{"CarrierID": 1, "CarrierName": "Synthetic"}], tiers, [])
        for month, expected in ((3, 55), (10, 55), (11, 110), (12, 110)):
            rows, _ = engine.build(date(2026, month, 1))
            self.assertEqual(rows[0]["Total Amount"], expected)


if __name__ == "__main__":
    unittest.main()
