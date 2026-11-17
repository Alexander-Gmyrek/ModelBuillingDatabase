"""Whole-month billing using coverage dates and the month changes were reported."""
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal

ZERO = Decimal("0")


def as_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value).split(" ")[0]) if value else None


def month(value):
    value = as_date(value)
    return date(value.year, value.month, 1) if value else None


def next_month(value):
    return date(value.year + (value.month == 12), value.month % 12 + 1, 1)


def previous_month(value):
    return date(value.year - (value.month == 1), (value.month - 2) % 12 + 1, 1)


def months(first, last):
    current = month(first)
    while current <= last:
        yield current
        current = next_month(current)


def informed(row, field="StartDate"):
    return month(row.get("Inform" + field) or row.get(field))


def covered(row, coverage_month, knowledge_month):
    """Starts and terminations include their entire calendar month."""
    start = month(row.get("StartDate"))
    if not start:
        raise ValueError("Coverage start date is missing.")
    if coverage_month < start or informed(row) > knowledge_month:
        return False
    end = month(row.get("EndDate"))
    return not (end and informed(row, "EndDate") <= knowledge_month and coverage_month > end)


def date_note(label, value):
    return f"{label} ({as_date(value).strftime('%d-%m-%Y')})"


class MonthlyBilling:
    def __init__(self, employer, employees, enrollments, plans, carriers, tiers, dependents):
        self.employer = employer
        self.employees = employees
        self.plans = {int(row["PlanID"]): row for row in plans}
        self.carriers = {int(row["CarrierID"]): row["CarrierName"] for row in carriers}
        self.tiers = {int(row["TierID"]): row for row in tiers}
        self.enrollments = defaultdict(list)
        self.dependents = defaultdict(list)
        for row in enrollments:
            self.enrollments[int(row["EmployeeID"])].append(row)
        for row in dependents:
            self.dependents[int(row["EmployeeID"])].append(row)
        self.age_banded = str(employer["TierStructure"]).replace(" ", "").casefold() == "agebanded"

    def enrollment(self, employee, coverage_month, knowledge_month, ignore_notice=False):
        candidates = []
        for row in self.enrollments[int(employee["EmployeeID"])]:
            if month(row["StartDate"]) > coverage_month:
                continue
            if not ignore_notice and informed(row) > knowledge_month:
                continue
            end = month(row.get("EndDate"))
            if end:
                # Termination ends coverage after its month; a plan switch replaces
                # the old enrollment at the beginning of its effective month.
                is_termination = (as_date(row.get("EndDate")) == as_date(employee.get("EndDate"))
                                  and informed(row, "EndDate") == informed(employee, "EndDate"))
                exclusive_end = next_month(end) if is_termination else end
                if coverage_month >= exclusive_end and (ignore_notice or informed(row, "EndDate") <= knowledge_month):
                    continue
            candidates.append(row)
        if not candidates:
            raise ValueError(f"No enrollment covers {employee['EmployeeFullName']} for {coverage_month:%Y-%m}.")
        return max(candidates, key=lambda row: (as_date(row["StartDate"]), int(row["EmployeePlanID"])))

    def rate(self, enrollment, person, coverage_month, dependent=False):
        plan = self.plans[int(enrollment["PlanID"])]
        if self.age_banded:
            dob = as_date(person.get("DOB"))
            if not dob:
                raise ValueError(f"A birth date is required for age-banded coverage in {coverage_month:%Y-%m}.")
            renewal = as_date(self.employer["RenewalDate"])
            age = coverage_month.year - dob.year - ((renewal.month, renewal.day) < (dob.month, dob.day))
            tiers = [tier for tier in self.tiers.values()
                     if tier.get("MinAge") is not None and tier.get("MaxAge") is not None
                     and int(tier["MinAge"]) <= age <= int(tier["MaxAge"])]
            if len(tiers) != 1:
                raise ValueError(f"Exactly one age band must cover age {age}.")
            candidates = [candidate for candidate in self.plans.values()
                          if int(candidate["CarrierID"]) == int(plan["CarrierID"])
                          and int(candidate["TierID"]) == int(tiers[0]["TierID"])
                          and month(candidate["StartDate"]) <= coverage_month
                          and (not candidate.get("EndDate") or coverage_month < month(candidate["EndDate"]))]
            if int(plan["TierID"]) != int(tiers[0]["TierID"]):
                if len(candidates) != 1:
                    raise ValueError(f"Exactly one age-banded rate must cover {coverage_month:%Y-%m}.")
                plan = candidates[0]
        fee = "GrenzFee"
        if dependent:
            relation = str(person.get("Relationship") or "").casefold()
            if relation not in ("spouse", "child"):
                raise ValueError("Dependent relationship must be Spouse or Child.")
            fee = "GrenzFeeS" if relation == "spouse" else "GrenzFeeC"
        return {
            "Carrier": self.carriers[int(plan["CarrierID"])],
            "Tier": self.tiers[int(plan["TierID"])]["TierName"],
            "Funding Amount": Decimal(str(plan.get("FundingAmount") or 0)),
            "Admin Fee": Decimal(str(plan.get(fee) or 0)),
        }

    def amounts(self, employee, coverage_month, knowledge_month):
        if not covered(employee, coverage_month, knowledge_month):
            return {}
        enrollment = self.enrollment(employee, coverage_month, knowledge_month)
        amounts = {None: self.rate(enrollment, employee, coverage_month)}
        if self.age_banded:
            for dependent in self.dependents[int(employee["EmployeeID"])]:
                if covered(dependent, coverage_month, knowledge_month):
                    amounts[int(dependent["DependentID"])] = self.rate(enrollment, dependent, coverage_month, True)
        return amounts

    def notes(self, person, bill_month):
        result = []
        if month(person["StartDate"]) <= bill_month <= informed(person):
            result.append(date_note("Hire", person["StartDate"]))
        end = person.get("EndDate")
        if end and month(end) <= bill_month <= informed(person, "EndDate"):
            result.append(date_note("Term", end))
        return result

    def build(self, bill_date):
        bill_month = month(bill_date)
        prior_month = previous_month(bill_month)
        rows, details = [], []
        for employee in sorted(self.employees, key=lambda row: row["EmployeeFullName"].casefold()):
            start = month(employee["StartDate"])
            if start > bill_month:
                continue
            end = month(employee.get("EndDate"))
            if end and bill_month > max(end, informed(employee, "EndDate")):
                continue
            changes = sorted(self.enrollments[int(employee["EmployeeID"])],
                             key=lambda row: (as_date(row["StartDate"]), int(row["EmployeePlanID"])))[1:]
            notes = self.notes(employee, bill_month)
            notes.extend(date_note("Plan change", row["StartDate"]) for row in changes
                         if month(row["StartDate"]) <= bill_month <= informed(row))

            # A notification changes what is owed for earlier coverage months.
            # Comparing knowledge before/after this bill prevents adjustments from
            # repeating and handles hire, plan and termination notices together.
            amounts_by_person = defaultdict(lambda: {"Funding Amount": ZERO, "Admin Fee": ZERO,
                                                     "Carriers": set(), "Tiers": set()})
            for coverage_month in months(start, bill_month):
                current = self.amounts(employee, coverage_month, bill_month)
                prior = self.amounts(employee, coverage_month, prior_month) if coverage_month < bill_month else {}
                for person_id in set(current) | set(prior):
                    new, old = current.get(person_id), prior.get(person_id)
                    if coverage_month < bill_month and new == old:
                        continue
                    # Preserve separate credit/charge lines when carrier or tier changes.
                    parts = [(1, new), (-1, old)] if new and old and (
                        new["Carrier"], new["Tier"]) != (old["Carrier"], old["Tier"]) else [
                            (1, {**(new or old),
                                 "Funding Amount": (new or {}).get("Funding Amount", ZERO) - (old or {}).get("Funding Amount", ZERO),
                                 "Admin Fee": (new or {}).get("Admin Fee", ZERO) - (old or {}).get("Admin Fee", ZERO)})
                        ]
                    for sign, amount in parts:
                        if amount is None:
                            continue
                        funding, fee = sign * amount["Funding Amount"], sign * amount["Admin Fee"]
                        if not funding and not fee and coverage_month < bill_month:
                            continue
                        totals = amounts_by_person[person_id]
                        totals["Funding Amount"] += funding
                        totals["Admin Fee"] += fee
                        totals["Carriers"].add(amount["Carrier"])
                        totals["Tiers"].add(amount["Tier"])
                        person = next((dep for dep in self.dependents[int(employee["EmployeeID"])]
                                       if dep["DependentID"] == person_id), employee)
                        reason = "Current coverage" if coverage_month == bill_month else "Backdated charge" if funding + fee >= 0 else "Backdated credit"
                        details.append({"Employee Name": employee["EmployeeFullName"],
                                        "Dependent": person.get("DependentName", ""),
                                        "Coverage Month": coverage_month.strftime("%Y-%m"),
                                        "Reason": reason, "Carrier": amount["Carrier"], "Tier": amount["Tier"],
                                        "Funding Amount": funding, "Admin Fee": fee, "Total Amount": funding + fee})
            if None not in amounts_by_person:
                # A late hire is visible before notification, with zero charges.
                enrollment = self.enrollment(employee, min(bill_month, end) if end else bill_month,
                                             bill_month, ignore_notice=True)
                rate = self.rate(enrollment, employee, bill_month)
                amounts_by_person[None]["Carriers"].add(rate["Carrier"])
                amounts_by_person[None]["Tiers"].add(rate["Tier"])
            for person_id, totals in amounts_by_person.items():
                person = employee if person_id is None else next(
                    dep for dep in self.dependents[int(employee["EmployeeID"])] if dep["DependentID"] == person_id)
                row_notes = notes if person_id is None else self.notes(person, bill_month)
                rows.append({"Notes": "; ".join(dict.fromkeys(row_notes)),
                             "Employee Name": employee["EmployeeFullName"],
                             "Carrier": " / ".join(sorted(totals["Carriers"])),
                             "Tier": " / ".join(sorted(totals["Tiers"])),
                             "Funding Amount": totals["Funding Amount"], "Admin Fee": totals["Admin Fee"],
                             "Total Amount": totals["Funding Amount"] + totals["Admin Fee"],
                             "DOB": as_date(person.get("DOB")).strftime("%d-%m-%Y") if person.get("DOB") else "",
                             "Dependent Name": person.get("DependentName", "") if person_id is not None else "",
                             **{field: employee.get(source) for field, source in
                                [("GL Code", "GlCode"), ("Division", "Division"), ("Location", "Location"), ("Title", "Title")]}})
        return rows, details
