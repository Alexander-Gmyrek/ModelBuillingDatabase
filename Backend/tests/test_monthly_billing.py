"""Approved monthly coverage and notification rules."""
import sys
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from monthly_billing import MonthlyBilling


class MonthlyBillingTests(unittest.TestCase):
    def setUp(self):
        self.company = {"EmployerID": 1, "TierStructure": "4 Tier", "RenewalDate": "2026-01-01"}
        self.employee = {"EmployeeID": 1, "EmployeeFullName": "Synthetic Employee",
                         "StartDate": "2026-01-15", "InformStartDate": "2026-01-20",
                         "EndDate": None, "InformEndDate": None}
        self.enrollments = [{"EmployeePlanID": 1, "EmployeeID": 1, "PlanID": 1,
                             "StartDate": "2026-01-15", "InformStartDate": "2026-01-20",
                             "EndDate": None, "InformEndDate": None}]
        self.plans = [{"PlanID": 1, "CarrierID": 1, "TierID": 1, "StartDate": "2020-01-01",
                       "FundingAmount": "100", "GrenzFee": "10"},
                      {"PlanID": 2, "CarrierID": 2, "TierID": 2, "StartDate": "2020-01-01",
                       "FundingAmount": "150", "GrenzFee": "15"}]
        self.carriers = [{"CarrierID": 1, "CarrierName": "Carrier A"}, {"CarrierID": 2, "CarrierName": "Carrier B"}]
        self.tiers = [{"TierID": 1, "TierName": "Employee"}, {"TierID": 2, "TierName": "Family"}]
        self.dependents = []

    def bill(self, year, month):
        engine = MonthlyBilling(self.company, [self.employee], self.enrollments,
                                self.plans, self.carriers, self.tiers, self.dependents)
        rows, details = engine.build(date(year, month, 1))
        for field in ("Funding Amount", "Admin Fee", "Total Amount"):
            self.assertEqual(sum(row[field] for row in rows), sum(line[field] for line in details))
        return rows, details

    def total(self, month, year=2026):
        return sum((row["Total Amount"] for row in self.bill(year, month)[0]), Decimal("0"))

    def terminate(self, actual, informed):
        self.employee.update(EndDate=actual, InformEndDate=informed)
        self.enrollments[-1].update(EndDate=actual, InformEndDate=informed)

    def hire(self, actual, informed):
        self.employee.update(StartDate=actual, InformStartDate=informed)
        self.enrollments[0].update(StartDate=actual, InformStartDate=informed)

    def switch(self, actual, informed, plan=2):
        self.enrollments[-1].update(EndDate=actual, InformEndDate=informed)
        self.enrollments.append({"EmployeePlanID": len(self.enrollments) + 1,
                                 "EmployeeID": 1, "PlanID": plan, "StartDate": actual,
                                 "InformStartDate": informed, "EndDate": None, "InformEndDate": None})

    def test_late_termination_full_timeline(self):
        self.terminate("2026-03-15", "2026-06-15")
        self.assertEqual(self.total(2), Decimal("110"))
        self.assertEqual(self.bill(2026, 2)[0][0]["Notes"], "")
        for month in (3, 4, 5):
            self.assertEqual(self.total(month), Decimal("110"))
            self.assertEqual(self.bill(2026, month)[0][0]["Notes"], "Term (15-03-2026)")
        self.assertEqual(self.total(6), Decimal("-220"))
        rows, details = self.bill(2026, 6)
        self.assertEqual(rows[0]["Notes"], "Term (15-03-2026)")
        self.assertEqual({line["Coverage Month"] for line in details}, {"2026-04", "2026-05"})
        self.assertEqual(self.bill(2026, 7)[0], [])

    def test_on_time_midmonth_termination_charges_whole_month(self):
        self.terminate("2026-03-15", "2026-03-25")
        self.assertEqual(self.total(3), Decimal("110"))
        self.assertEqual(self.bill(2026, 4)[0], [])

    def test_first_day_termination_also_charges_termination_month(self):
        self.terminate("2026-03-01", "2026-03-01")
        self.assertEqual(self.total(3), Decimal("110"))
        self.assertEqual(self.total(4), 0)

    def test_notice_next_month_has_no_past_overcharge_to_credit(self):
        self.terminate("2026-03-31", "2026-04-20")
        self.assertEqual(self.total(3), Decimal("110"))
        self.assertEqual(self.total(4), 0)
        self.assertEqual(self.bill(2026, 4)[0][0]["Notes"], "Term (31-03-2026)")
        self.assertEqual(self.bill(2026, 5)[0], [])

    def test_late_hire_full_timeline(self):
        self.hire("2026-03-15", "2026-06-15")
        self.assertEqual(self.bill(2026, 2)[0], [])
        for month in (3, 4, 5):
            self.assertEqual(self.total(month), 0)
            self.assertEqual(self.bill(2026, month)[0][0]["Notes"], "Hire (15-03-2026)")
        self.assertEqual(self.total(6), Decimal("440"))
        rows, details = self.bill(2026, 6)
        self.assertEqual(rows[0]["Notes"], "Hire (15-03-2026)")
        self.assertEqual({line["Coverage Month"] for line in details},
                         {"2026-03", "2026-04", "2026-05", "2026-06"})
        self.assertEqual(self.total(7), Decimal("110"))
        self.assertEqual(self.bill(2026, 7)[0][0]["Notes"], "")

    def test_midmonth_hire_charges_whole_month(self):
        self.hire("2026-03-31", "2026-03-31")
        self.assertEqual(self.total(3), Decimal("110"))
        self.assertEqual(self.bill(2026, 2)[0], [])

    def test_advance_hire_notice_does_not_bill_before_hire(self):
        self.hire("2026-03-15", "2026-02-15")
        self.assertEqual(self.bill(2026, 2)[0], [])
        self.assertEqual(self.total(3), Decimal("110"))
        self.assertEqual(self.bill(2026, 3)[0][0]["Notes"], "")

    def test_late_more_expensive_plan_change(self):
        self.switch("2026-03-15", "2026-06-15")
        self.assertEqual(self.bill(2026, 2)[0][0]["Notes"], "")
        for month in (3, 4, 5):
            self.assertEqual(self.total(month), Decimal("110"))
            row = self.bill(2026, month)[0][0]
            self.assertEqual(row["Carrier"], "Carrier A")
            self.assertEqual(row["Notes"], "Plan change (15-03-2026)")
        self.assertEqual(self.total(6), Decimal("330"))
        self.assertEqual(self.total(7), Decimal("165"))
        self.assertEqual(self.bill(2026, 7)[0][0]["Notes"], "")

    def test_late_cheaper_plan_change(self):
        self.plans[0].update(FundingAmount="150", GrenzFee="15")
        self.plans[1].update(FundingAmount="100", GrenzFee="10")
        self.switch("2026-03-15", "2026-06-15")
        self.assertEqual(self.total(5), Decimal("165"))
        self.assertEqual(self.total(6), Decimal("-55"))
        self.assertEqual(self.total(7), Decimal("110"))

    def test_same_carrier_tier_change(self):
        self.plans[1]["CarrierID"] = 1
        self.switch("2026-03-15", "2026-06-15")
        self.assertEqual(self.total(6), Decimal("330"))
        self.assertEqual(self.bill(2026, 7)[0][0]["Tier"], "Family")

    def test_same_carrier_and_tier_rate_change(self):
        self.plans[1].update(CarrierID=1, TierID=1)
        self.switch("2026-03-15", "2026-06-15")
        self.assertEqual(self.total(6), Decimal("330"))
        self.assertEqual(self.total(7), Decimal("165"))

    def test_multiple_notices_do_not_repeat_prior_adjustments(self):
        self.plans.append({**self.plans[1], "PlanID": 3, "FundingAmount": "200", "GrenzFee": "20"})
        self.switch("2026-03-15", "2026-05-15")
        self.switch("2026-04-20", "2026-06-15", 3)
        self.assertEqual(self.total(5), Decimal("275"))
        self.assertEqual(self.total(6), Decimal("330"))
        self.assertEqual(self.total(7), Decimal("220"))

    def test_late_hire_and_termination_in_same_notification_month(self):
        self.hire("2026-03-15", "2026-06-15")
        self.terminate("2026-04-20", "2026-06-20")
        self.assertEqual(self.total(5), 0)
        self.assertEqual(self.total(6), Decimal("220"))
        self.assertIn("Hire (15-03-2026)", self.bill(2026, 6)[0][0]["Notes"])
        self.assertIn("Term (20-04-2026)", self.bill(2026, 6)[0][0]["Notes"])
        self.assertEqual(self.bill(2026, 7)[0], [])

    def test_hire_and_termination_within_one_month(self):
        self.hire("2026-03-15", "2026-06-15")
        self.terminate("2026-03-20", "2026-06-20")
        self.assertEqual(self.total(6), Decimal("110"))

    def test_late_hire_across_calendar_year(self):
        self.hire("2025-11-15", "2026-02-15")
        self.assertEqual(self.total(12, 2025), 0)
        self.assertEqual(self.total(2), Decimal("440"))
        self.assertEqual(self.total(3), Decimal("110"))

    def test_late_termination_across_calendar_year(self):
        self.hire("2025-01-15", "2025-01-15")
        self.terminate("2025-11-15", "2026-02-15")
        self.assertEqual(self.total(12, 2025), Decimal("110"))
        self.assertEqual(self.total(2), Decimal("-220"))
        self.assertEqual(self.bill(2026, 3)[0], [])

    def test_regeneration_is_deterministic(self):
        self.switch("2026-03-15", "2026-06-15")
        self.assertEqual(self.bill(2026, 6), self.bill(2026, 6))
        self.assertEqual(self.total(7), Decimal("165"))

    def age_banded_family(self):
        self.company["TierStructure"] = "Age Banded"
        self.employee["DOB"] = "1990-01-01"
        self.tiers[0].update(MinAge=0, MaxAge=120)
        self.tiers[1].update(MinAge=121, MaxAge=150)
        self.plans[0].update(GrenzFeeC="5", GrenzFeeS="7")
        self.dependents = [{"DependentID": 2, "EmployeeID": 1, "DependentName": "Synthetic Child",
                            "Relationship": "Child", "DOB": "2015-01-01",
                            "StartDate": "2026-01-15", "InformStartDate": "2026-01-20",
                            "EndDate": None, "InformEndDate": None}]

    def test_age_banded_employee_termination_includes_family_credit(self):
        self.age_banded_family()
        self.terminate("2026-03-15", "2026-06-15")
        self.dependents[0].update(EndDate="2026-03-15", InformEndDate="2026-06-15")
        self.assertEqual(self.total(3), Decimal("215"))
        self.assertEqual(self.total(5), Decimal("215"))
        self.assertEqual(self.total(6), Decimal("-430"))
        self.assertEqual(self.bill(2026, 7)[0], [])

    def test_late_dependent_hire_charges_all_missed_months(self):
        self.age_banded_family()
        self.dependents[0].update(StartDate="2026-03-15", InformStartDate="2026-06-15")
        self.assertEqual(self.total(3), Decimal("110"))
        self.assertEqual(self.total(6), Decimal("530"))
        self.assertEqual(self.total(7), Decimal("215"))

    def test_late_dependent_termination_preserves_employee_charge(self):
        self.age_banded_family()
        self.dependents[0].update(EndDate="2026-03-15", InformEndDate="2026-06-15")
        self.assertEqual(self.total(3), Decimal("215"))
        self.assertEqual(self.total(5), Decimal("215"))
        self.assertEqual(self.total(6), Decimal("-100"))
        self.assertEqual(self.total(7), Decimal("110"))

    def test_leap_day_termination_is_full_month(self):
        self.hire("2024-01-15", "2024-01-15")
        self.terminate("2024-02-29", "2024-04-15")
        self.assertEqual(self.total(2, 2024), Decimal("110"))
        self.assertEqual(self.total(4, 2024), Decimal("-110"))
        self.assertEqual(self.bill(2024, 4)[0][0]["Notes"], "Term (29-02-2024)")


if __name__ == "__main__":
    unittest.main()
