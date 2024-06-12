import json
from random import randint, choice
from datetime import datetime, timedelta

def generate_employer(employer_id):
    return {
        "EmployerID": employer_id,
        "EmployerName": f"Test Employer {employer_id}",
        "TierStructure": "4Tiered",
        "UsesGlCode": choice([True, False]),
        "UsesDivision": choice([True, False]),
        "UsesLocation": choice([True, False]),
        "UsesTitle": choice([True, False]),
        "PreferredBillingDate": (datetime.now() + timedelta(days=randint(1, 365))).strftime('%Y-%m-%d'),
        "RenewalDate": (datetime.now() + timedelta(days=randint(366, 730))).strftime('%Y-%m-%d'),
        "employees": [],
        "carriers": [],
        "tiers": [],
        "plans": []
    }

def generate_employee(employee_id, employer_id, carriers, tiers):
    first_name = choice(["John", "Jane", "Alex", "Alice", "Mike", "Michelle"])
    last_name = choice(["Doe", "Smith", "Johnson", "Williams", "Brown", "Jones"])
    return {
        "EmployeeID": employee_id,
        "EmployerID": employer_id,
        "EmployeeFullName": f"{first_name} {last_name}",
        "EmployeeFirstName": first_name,
        "EmployeeLastName": last_name,
        "JoinDate": "2000-01-01",
        "TermDate": None,
        "JoinInformDate": "2000-01-01",
        "TermEndDate": None,
        "DOB": "1990-06-25",
        "CobraStatus": choice([True, False]),
        "Notes": "This is a sample note.",
        "GL": f"GL{randint(10000, 99999)}",
        "Division": choice(["Finance", "HR", "Engineering", "Marketing"]),
        "Location": choice(["New York", "Los Angeles", "Chicago", "Houston"]),
        "Title": choice(["Analyst", "Manager", "Director", "Coordinator"]),
        "Dependents": [],
        "EmployeePlans": [],
        "Carrier": choice(carriers)["CarrierName"],
        "Tier": choice(tiers)["TierName"]
    }

def generate_employee_plan(employee_plan_id, employee_id, plan_id):
    start_date = datetime.now().strftime('%Y-%m-%d')
    end_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
    return {
        "EmployeePlanID": employee_plan_id,
        "EmployeeID": employee_id,
        "PlanID": plan_id,
        "StartDate": start_date,
        "InformStartDate": start_date,
        "EndDate": end_date,
        "InformEndDate": end_date
    }

def generate_dependent(dependent_id, employee_id):
    first_name = choice(["Chris", "Pat", "Sam", "Taylor", "Jordan", "Casey"])
    last_name = choice(["Doe", "Smith", "Johnson", "Williams", "Brown", "Jones"])
    return {
        "DependentID": dependent_id,
        "EmployeeID": employee_id,
        "DependentName": f"{first_name} {last_name}",
        "Relationship": choice(["Spouse", "Child"]),
        "DOB": "1990-06-25",
        "StartDate": "2023-01-01",
        "InformStartDate": "2023-01-01",
        "EndDate": "2024-01-01",
        "InformEndDate": "2024-01-01"
    }

def generate_plan(plan_id, employer_id, carrier_id, tier_id):
    return {
        "PlanID": plan_id,
        "EmployerID": employer_id,
        "CarrierID": carrier_id,
        "TierID": tier_id,
        "FundingAmount": round(randint(1000, 5000) / 100, 2),
        "GrenzFee": round(randint(100, 500) / 100, 2),
        "GrenzFeeC": round(randint(50, 250) / 100, 2),
        "GrenzFeeS": round(randint(50, 250) / 100, 2)
    }

def generate_tier(tier_id, employer_id):
    return {
        "TierID": tier_id,
        "EmployerID": employer_id,
        "TierName": f"Tier{tier_id}",
        "MaxAge": 100,
        "MinAge": 0
    }

def generate_carrier(carrier_id, employer_id):
    return {
        "CarrierID": carrier_id,
        "EmployerID": employer_id,
        "CarrierName": f"Carrier{carrier_id}"
    }

def generate_test_data(num_employers, num_employees, num_dependents, num_tiers, num_carriers, num_plans):
    data = {"employers": []}

    for emp_id in range(1, num_employers + 1):
        employer = generate_employer(emp_id)
        
        for tier_id in range(1, num_tiers + 1):
            tier = generate_tier(tier_id, emp_id)
            employer["tiers"].append(tier)
        
        for carrier_id in range(1, num_carriers + 1):
            carrier = generate_carrier(carrier_id, emp_id)
            employer["carriers"].append(carrier)
        
        for carrier_id in range(1, num_carriers + 1):
            for tier_id in range(1, num_tiers + 1):
                plan_id = (carrier_id - 1) * num_tiers + tier_id
                plan = generate_plan(plan_id, emp_id, carrier_id, tier_id)
                employer["plans"].append(plan)
        
        for emp in range(1, num_employees + 1):
            employee = generate_employee(emp, emp_id, employer["carriers"], employer["tiers"])
            for dep in range(1, num_dependents + 1):
                dependent = generate_dependent(dep, emp)
                employee["Dependents"].append(dependent)
            employer["employees"].append(employee)
        
        data["employers"].append(employer)
    
    return data

# User input for number of employers, employees, dependents, tiers, carriers, and plans
num_employers = int(input("Enter number of employers: "))
num_employees = int(input("Enter number of employees per employer: "))
num_dependents = int(input("Enter number of dependents per employee: "))
num_tiers = int(input("Enter number of tiers per employer: "))
num_carriers = int(input("Enter number of carriers per employer: "))
num_plans = int(input("Enter number of plans per employer: "))

# Generate test data
test_data = generate_test_data(num_employers, num_employees, num_dependents, num_tiers, num_carriers, num_plans)

# Display or save JSON data
print(json.dumps(test_data, indent=4))
