import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import calendar

# Dependency Injection for the database connection
def get_connection(config):
    try:
        connection = mysql.connector.connect(**config)
        print("Connection successful")
        return connection
    except mysql.connector.Error as e:
        print("Error:", e)
        return None

def execute_query(cursor, query):
    cursor.execute(query)
    return cursor.fetchall()

def add_data_test(df, notes, employee_name, plan, tier, funding_amount):
    new_row = {"Notes": notes, "Employee Name": employee_name, "Plan": plan, "Tier": tier, "Funding Amount": funding_amount}
    return df._append(new_row, ignore_index=True)

def generate_month_range(start, end):
    current = start
    while current <= end:
        yield datetime(current.year, current.month, 1)
        current += timedelta(days=calendar.monthrange(current.year, current.month)[1])
        current = datetime(current.year, current.month, 1)

def calculate_funding_amount_normal(cursor, plan_id, date, employee_id=None):
    query = f"SELECT CarrierID, TierID, FundingAmount, GrenzFee FROM Plan WHERE PlanID = {plan_id}"
    plan_info = execute_query(cursor, query)
    if not plan_info:
        print(f"Plan {plan_id} info not found")
        return 0, "", ""

    carrier_id, tier_id, funding_amount, grenz_fee = plan_info[0]
    
    carrier_name = execute_query(cursor, f"SELECT CarrierName FROM Carrier WHERE CarrierID = {carrier_id}")[0][0]
    tier_name = execute_query(cursor, f"SELECT TierName FROM Tier WHERE TierID = {tier_id}")[0][0]

    return funding_amount + grenz_fee, carrier_name, tier_name, []

def calculate_funding_amount_age_banded(cursor, date, plan_id=None, employee_id=None):
    funding_amount = 0
    dependents = []
    # Get Renewal Date
    query = f"SELECT RenewalDate FROM Emloyer WHERE EmployerID = SELECT EmployerID FROM Plan WHERE PlanID = {plan_id}"
    renewal_date = execute_query(cursor, query)[0][0]
    # Get the year from the date and combine it with renewal date month
    date = datetime.strptime(date, '%Y-%m-%d') # Convert date to datetime
    date = renewal_date.replace(year=date.year) # Replace the year with the current year
    # Get the age of the employee
    query = f"SELECT DOB FROM Employee WHERE EmployeeID = {employee_id}"
    dob = execute_query(cursor, query)[0][0]
    age = date.year - dob.year - ((date.month, date.day) < (dob.month, dob.day))
    # Get the age banded tier
    query = f"SELECT TierID FROM Tier WHERE MinAge <= {age} AND MaxAge >= {age} AND EmployerID = SELECT EmployerID FROM Plan WHERE PlanID = {plan_id}"
    tier_id = execute_query(cursor, query)[0][0]
    # Get the funding amount for the Plan
    query = f"SELECT FundingAmount, GrenzFee FROM Plan WHERE TeirID = {tier_id} AND CarrierID = SELECT CarrierID FROM Plan WHERE PlanID = {plan_id}"
    fund_amount, grenz_fee = execute_query(cursor, query)
    funding_amount += fund_amount + grenz_fee
    tier = execute_query(cursor, f"SELECT TierName FROM Tier WHERE TierID = {tier_id}")[0][0]
    carrier_id = execute_query(cursor, f"SELECT CarrierID FROM Carrier WHERE CarrierID = SELECT CarrierID FROM Plan WHERE PlanID = {plan_id}")[0][0]
    carrier = execute_query(cursor, f"SELECT CarrierName FROM Carrier WHERE CarrierID = {carrier_id}")[0][0]
    # Get the dependents
    query = f"SELECT DependentID FROM Dependent WHERE EmployeeID = {employee_id}"
    dependent_ids = execute_query(cursor, query)
    for dependent_id in dependent_ids:
        # check if dependent is active
        query = f"SELECT StartDate, InformStartDate, EndDate, InformStartDate FROM Dependent WHERE DependentID = {dependent_id}"
        start_date, inform_start_date, end_date, inform_end_date = execute_query(cursor, query)[0]
        if inform_start_date == datetime(date.year, date.month, 1):
            query = f"SELECT DependentName, DOB, Relationship FROM Dependent WHERE DependentID = {dependent_id}"
            dep_name, dob, relationship = execute_query(cursor, query)[0][0]
            for back_date in generate_month_range(start_date, inform_start_date):
                age = back_date.year - dob.year - ((back_date.month, back_date.day) < (dob.month, dob.day))
                query = f"SELECT TierID FROM Tier WHERE MinAge <= {age} AND MaxAge >= {age} AND EmployerID = SELECT EmployerID FROM Plan WHERE PlanID = {plan_id}"
                tier_id = execute_query(cursor, query)[0][0]
                if relationship == "Spouse":
                    query = f"SELECT FundingAmount, GrenzFeeS FROM Plan WHERE TeirID = {tier_id} AND CarrierID = {carrier_id}"
                elif relationship == "Child":
                    query = f"SELECT FundingAmount, GrenzFeeC FROM Plan WHERE TeirID = {tier_id} AND CarrierID = {carrier_id}"
                else:
                    raise ValueError("Invalid Relationship")
                fund_amount, grenz_fee = execute_query(cursor, query)
                funding_amount += fund_amount + grenz_fee
                dep_tier = execute_query(cursor, f"SELECT TierName FROM Tier WHERE TierID = {tier_id}")[0][0]
                #add the dependent (name, tier, relationship) to the list
            dependents.append((dep_name, dep_tier, relationship))
        if inform_end_date == datetime(date.year, date.month, 1):
            query = f"SELECT DependentName, DOB, Relationship FROM Dependent WHERE DependentID = {dependent_id}"
            dep_name, dob, relationship = execute_query(cursor, query)[0][0]
            for back_date in generate_month_range(start_date, inform_start_date):
                age = back_date.year - dob.year - ((back_date.month, back_date.day) < (dob.month, dob.day))
                query = f"SELECT TierID FROM Tier WHERE MinAge <= {age} AND MaxAge >= {age} AND EmployerID = SELECT EmployerID FROM Plan WHERE PlanID = {plan_id}"
                tier_id = execute_query(cursor, query)[0][0]
                if relationship == "Spouse":
                    query = f"SELECT FundingAmount, GrenzFeeS FROM Plan WHERE TeirID = {tier_id} AND CarrierID = {carrier_id}"
                elif relationship == "Child":
                    query = f"SELECT FundingAmount, GrenzFeeC FROM Plan WHERE TeirID = {tier_id} AND CarrierID = {carrier_id}"
                else:
                    raise ValueError("Invalid Relationship")
                fund_amount, grenz_fee = execute_query(cursor, query)
                funding_amount -= fund_amount + grenz_fee
                dep_tier = execute_query(cursor, f"SELECT TierName FROM Tier WHERE TierID = {tier_id}")[0][0]
                #add the dependent (name, tier, relationship) to the list
            dependents.append((dep_name, dep_tier, relationship))
        #if the dependent is not active
        if ((inform_end_date is not None) and (inform_end_date < datetime(date.year, date.month, 1)) or (inform_start_date > datetime(date.year, date.month, 1))):
            continue
        query = f"SELECT DependentName, DOB, Relationship FROM Dependent WHERE DependentID = {dependent_id}"
        dep_name, dob, relationship = execute_query(cursor, query)[0][0]
        age = date.year - dob.year - ((date.month, date.day) < (dob.month, dob.day))
        query = f"SELECT TierID FROM Tier WHERE MinAge <= {age} AND MaxAge >= {age} AND EmployerID = SELECT EmployerID FROM Plan WHERE PlanID = {plan_id}"
        tier_id = execute_query(cursor, query)[0][0]
        if relationship == "Spouse":
            query = f"SELECT FundingAmount, GrenzFeeS FROM Plan WHERE TeirID = {tier_id} AND CarrierID = {carrier_id}"
        elif relationship == "Child":
            query = f"SELECT FundingAmount, GrenzFeeC FROM Plan WHERE TeirID = {tier_id} AND CarrierID = {carrier_id}"
        else:
            raise ValueError("Invalid Relationship")
        fund_amount, grenz_fee = execute_query(cursor, query)
        funding_amount += fund_amount + grenz_fee
        dep_tier = execute_query(cursor, f"SELECT TierName FROM Tier WHERE TierID = {tier_id}")[0][0]
        #add the dependent (name, tier, relationship) to the list
        dependents.append((dep_name, dep_tier, relationship))

    
    return funding_amount, carrier, tier, dependents

def calculate_funding_amount_composite(cursor, date, plan_id=None, employee_id=None):
    funding_amount = 0
    # Get Renewal Date
    query = f"SELECT RenewalDate FROM Emloyer WHERE EmployerID = SELECT EmployerID FROM Plan WHERE PlanID = {plan_id}"
    renewal_date = execute_query(cursor, query)[0][0]
    # Get the year from the date and combine it with renewal date month
    date = datetime.strptime(date, '%Y-%m-%d') # Convert date to datetime
    date = renewal_date.replace(year=date.year) # Replace the year with the current year
    # Get the age of the employee
    query = f"SELECT DOB FROM Employee WHERE EmployeeID = {employee_id}"
    dob = execute_query(cursor, query)[0][0]
    age = date.year - dob.year - ((date.month, date.day) < (dob.month, dob.day))
    # Get the age banded tier
    query = f"SELECT TierID FROM Tier WHERE MinAge <= {age} AND MaxAge >= {age} AND EmployerID = SELECT EmployerID FROM Plan WHERE PlanID = {plan_id}"
    tier_id = execute_query(cursor, query)[0][0]
    # Get the funding amount for the Plan
    query = f"SELECT FundingAmount, GrenzFee FROM Plan WHERE TeirID = {tier_id} AND CarrierID = SELECT CarrierID FROM Plan WHERE PlanID = {plan_id}"
    fund_amount, grenz_fee = execute_query(cursor, query)
    funding_amount += fund_amount + grenz_fee
    tier = execute_query(cursor, f"SELECT TierName FROM Tier WHERE TierID = {tier_id}")[0][0]
    carrier_id = execute_query(cursor, f"SELECT CarrierID FROM Carrier WHERE CarrierID = SELECT CarrierID FROM Plan WHERE PlanID = {plan_id}")[0][0]
    carrier = execute_query(cursor, f"SELECT CarrierName FROM Carrier WHERE CarrierID = {carrier_id}")[0][0]

    return funding_amount, carrier, tier, []

def get_format_normal(employer_info=None):
    columns = ["Notes", "Employee Name"]
    if employer_info:
        employer_id, tier_structure, uses_gl_code, uses_division, uses_location, uses_title = employer_info
        if uses_gl_code:
            columns.append("GL Code")
        if uses_division:
            columns.append("Division")
        if uses_location:
            columns.append("Location")
        if uses_title:
            columns.append("Title")
    columns += ["Plan", "Tier", "Funding Amount"]
    return add_data_normal, columns

def get_format_normal(employer_info=None):
    columns = ["Notes", "Employee Name"]
    if employer_info:
        employer_id, tier_structure, uses_gl_code, uses_division, uses_location, uses_title = employer_info
        if uses_gl_code:
            columns.append("GL Code")
        if uses_division:
            columns.append("Division")
        if uses_location:
            columns.append("Location")
        if uses_title:
            columns.append("Title")
    columns += ["Plan", "Tier", "Funding Amount"]
    return add_data_normal, columns


def add_data_normal(df, notes, employee_name, plan, tier, funding_amount, gl_code = None, division=None, location=None, title=None, dependents=[]):
    new_row = {"Notes": notes, "Employee Name": employee_name, "Plan": plan, "Tier": tier, "Funding Amount": funding_amount}
    if gl_code:
        new_row["GL Code"] = gl_code
    if division:
        new_row["Division"] = division
    if location:
        new_row["Location"] = location
    if title:
        new_row["Title"] = title
    return df._append(new_row, ignore_index=True)

def add_data_age_banded(df, notes, employee_name, plan, tier, funding_amount, gl_code = None, division=None, location=None, title=None, dependents=[]):
    new_row = {"Notes": notes, "Employee Name": employee_name, "Plan": plan, "Tier": tier, "Funding Amount": funding_amount}
    if gl_code:
        new_row["GL Code"] = gl_code
    if division:
        new_row["Division"] = division
    if location:
        new_row["Location"] = location
    if title:
        new_row["Title"] = title
    for dependent in dependents:
        new_row["Dependent Name"] = dependent[0]
        new_row["Dependent Tier"] = dependent[1]
        new_row["Dependent Relationship"] = dependent[2]
        df = df._append(new_row, ignore_index=True)

    return df._append(new_row, ignore_index=True)

def generate_report(config, employer_name, date, get_format=get_format_normal):
    connection = get_connection(config)
    if not connection:
        return

    cursor = connection.cursor()

    current_month = datetime.strptime(date, '%Y-%m-%d').month
    current_year = datetime.strptime(date, '%Y-%m-%d').year

    employer_info = execute_query(cursor, f"SELECT EmployerID, TierStructure, UsesGLCode, UsesDivision, UsesLocation, UsesTitle FROM Employer WHERE EmployerName = '{employer_name}'")[0]
    if not employer_info:
        print(f"Employer {employer_name} not found")
        return
    
    add_data, columns = get_format(employer_info)

    employer_id, tier_structure, uses_gl_code, uses_division, uses_location, uses_title = employer_info
    calculate_funding_amount = calculate_funding_amount_normal
    if (tier_structure == "AgeBanded"):
        calculate_funding_amount = calculate_funding_amount_age_banded
        add_data = add_data_age_banded
    if (tier_structure == "AgeBandedComposite"):
        calculate_funding_amount = calculate_funding_amount_composite
    
    df = pd.DataFrame(columns=columns)
    
    
    employees = execute_query(cursor, f"SELECT EmployeeID, EmployeeFullName, JoinDate, JoinInformDate, TermDate, TermEndDate FROM Employee WHERE EmployerID = {employer_id} AND JoinDate <= '{date}' AND (TermEndDate >= '{date}' OR TermEndDate IS NULL)")

    if not employees:
        print(f"No employees found for {employer_name} on {date}")
        return

    for employee in employees:
        employee_id, employee_name, join_date, join_inform_date, term_date, term_inform_date = employee
        notes = ""
        funding_amount = 0
        carrier_names = []
        tier_names = []
        dependents = []

        employee_plans = execute_query(cursor, f"SELECT PlanID, StartDate, InformStartDate, EndDate, InformEndDate FROM EmployeePlan WHERE EmployeeID = {employee_id} AND InformStartDate <= '{date}'")
        
        if not employee_plans:
            print(f"No plans found for {employee_name} on {date}")
            continue

        if term_date and term_inform_date == datetime(current_year, current_month, 1):
            notes = "Terminated"
            print(f"{employee_name} is terminated")
            for back_date in generate_month_range(term_date, term_inform_date):
                plan_id = execute_query(cursor, f"SELECT PlanID FROM EmployeePlan WHERE EmployeeID = {employee_id} AND StartDate <= '{back_date}' AND (EndDate >= '{back_date}' OR EndDate IS NULL)")[0][0]
                f_amount, carrier_name, tier_name, new_dependents = calculate_funding_amount(cursor, back_date, plan_id, employee_id)
                funding_amount -= f_amount
                carrier_names.append(carrier_name)
                tier_names.append(tier_name)
                dependents = new_dependents
                
        
        if join_date and join_inform_date == datetime(current_year, current_month, 1):
            notes = "Joined"
            print(f"{employee_name} joined")
            for back_date in generate_month_range(join_date, join_inform_date):
                plan_id = execute_query(cursor, f"SELECT PlanID FROM EmployeePlan WHERE EmployeeID = {employee_id} AND StartDate <= '{back_date}' AND (EndDate >= '{back_date}' OR EndDate IS NULL)")[0][0]
                f_amount, carrier_name, tier_name, new_dependents = calculate_funding_amount(cursor, back_date, plan_id, employee_id)
                funding_amount += f_amount
                carrier_names.append(carrier_name)
                tier_names.append(tier_name)
                dependents = new_dependents

        for plan in employee_plans:
            plan_id, start_date, inform_start_date, end_date, inform_end_date = plan
            if end_date and inform_end_date < datetime(current_year, current_month, 1):
                continue
            if inform_start_date == datetime(current_year, current_month, 1):
                for back_date in generate_month_range(start_date, inform_start_date):
                    f_amount, carrier_name, tier_name, new_dependents = calculate_funding_amount(cursor, back_date, plan_id, employee_id)
                    funding_amount += f_amount
                    carrier_names.append(carrier_name)
                    tier_names.append(tier_name)
                    dependents = new_dependents

            if inform_end_date == datetime(current_year, current_month, 1):
                for back_date in generate_month_range(end_date, inform_end_date):
                    f_amount, carrier_name, tier_name, new_dependents = calculate_funding_amount(cursor, back_date, plan_id, employee_id)
                    funding_amount -= f_amount
                    carrier_names.append(carrier_name)
                    tier_names.append(tier_name)
                    dependents = new_dependents
            

        if not carrier_names or not tier_names:
            plan_id = execute_query(cursor, f"SELECT PlanID FROM EmployeePlan WHERE EmployeeID = {employee_id} AND StartDate <= '{date}' AND (EndDate >= '{date}' OR EndDate IS NULL)")[0][0]
            f_amount, carrier_name, tier_name, new_dependents = calculate_funding_amount(cursor, f"{current_year}-{current_month}-01", plan_id, employee_id)
            funding_amount += f_amount
            carrier_names.append(carrier_name)
            tier_names.append(tier_name)
            dependents = new_dependents

        carrier_name = "/ ".join(set(carrier_names))
        tier_name = "/ ".join(set(tier_names))

        gl_code = execute_query(cursor, f"SELECT GLCode FROM Employee WHERE EmployeeID = {employee_id}")[0][0]
        division = execute_query(cursor, f"SELECT Division FROM Employee WHERE EmployeeID = {employee_id}")[0][0]
        location = execute_query(cursor, f"SELECT Location FROM Employee WHERE EmployeeID = {employee_id}")[0][0]
        title = execute_query(cursor, f"SELECT Title FROM Employee WHERE EmployeeID = {employee_id}")[0][0]

        df = add_data(df, notes, employee_name, carrier_name, tier_name, funding_amount, gl_code, division, location, title, dependents)

    total_funding = df["Funding Amount"].sum()
    df = df._append({"Funding Amount": total_funding}, ignore_index=True)
    df.to_excel("employee_funding1.xlsx", index=False, engine='openpyxl')

    cursor.close()
    connection.close()

# Configuration and function call
config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Root',
    'database': 'MySampleDB'
}

generate_report(config, 'CommuniCare OLE Health Centers', '2024-05-01')
