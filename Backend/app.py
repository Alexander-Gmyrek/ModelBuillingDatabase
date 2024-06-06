from flask import Flask, request, jsonify
import mysql.connector
import pandas as pd
import json
import base64
import datetime

app = Flask(__name__)

###
# What is needed for a MVP
# 1. Add an employer
# 2. 


###

#test data for the database
def get_test_data(x):
    return{
    1: {
        "employer_name": "Test Employer 1",
        "billing_system": "4Tiered",
        "employee_data": "Test_Employee_Data_1.xlsx",
        "carriers": [
            {
                "carrier_name": "Test Carrier1",
            },
            {
                "carrier_name": "Test Carrier2",
            }
        ],
        "carrier_plans": {
            "Carrier1": [
                {"tier name": "Employee", "funding amount": 10, "grenz fee": 1}, 
                {"tier name": "Spouce", "funding amount": 15, "grenz fee": 1},
                {"tier name": "Child(ren)", "funding amount": 20, "grenz fee": 1},
                {"tier name": "Family", "funding amount": 25, "grenz fee": 1}
            ],
            "Carrier2": [
                {"tier name": "Employee", "funding amount": 10.1, "grenz fee": 1}, 
                {"tier name": "Spouce", "funding amount": 15.1, "grenz fee": 1},
                {"tier name": "Child(ren)", "funding amount": 20.1, "grenz fee": 1},
                {"tier name": "Family", "funding amount": 25.1, "grenz fee": 1}
            ]
        },
        "tiers": [
            {"tier name":"Employee"}, 
            {"tier name":"Spouce"}, 
            {"tier name":"Child(ren)"}, 
            {"tier name":"Family"}
        ]
    }
    }.get(x, 400)

def get_db_connection():
    connection = mysql.connector.connect(
        host='mysql',  # This matches the service name defined in docker-compose.yml
        user='server',
        password='Server',
        database='modelBillingDBv1'
    )
    return connection

@app.route('/')
def home():
    return "Up and Running!"

@app.route('/api', methods=['GET'])
def api():
    data = {"message": "Welcome to the API"}
    return jsonify(data)

@app.route('/testconection', methods=['GET'])
def testconection():
    with get_db_connection() as connection:
        if connection.is_connected():
            db_info = connection.get_server_info()
            return jsonify({"message": "Connected to MySQL Server version", "version": db_info})
        else:
            return jsonify({"message": "Connection to MySQL Server failed"})

# TODO: Finish add test data
@app.route('/add_test_data/<int:id>', methods=['POST'])
def add_test_data(id):

    with get_db_connection() as connection:
        cursor = connection.cursor()
        data = get_test_data(id)
        if data == 404:
            return jsonify({"message": "Test data not found"}), 404
        
        return jsonify({"message": "function not fully implemented"})
        connection.commit()
        cursor.close()
        return jsonify({"message": "Test data added"})

@app.route('/remove_test_data/<int:id>', methods=['DELETE'])
def delete_test_data(id):
    connection = get_db_connection()
    cursor = connection.cursor()
    employer_info = get_test_data(id)
    employer_name = employer_info['employer_name']
    cursor.execute(f"SELECT EmployerID FROM Employer WHERE EmployerName = {employer_name}")
    employer_id = cursor.fetchall()[0][0]
    if not employer_id:
        return jsonify({"message": "Employer not found"}), 400
    cursor.execute(f"DELETE FROM Employer WHERE EmployerID={employer_id}")
    connection.commit()
    cursor.close()
    connection.close()
    return jsonify({"message": "Test data deleted"})

@app.route('/employer', methods=['GET'])
def get_employers():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Employer")
    users = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(users)

@app.route('/employer/<int:id>', methods=['GET'])
def get_employer(id):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(f"SELECT * FROM Employer WHERE EmployerID={id}")
    except:
        return jsonify({"message": "Employer not found"}), 404
    user = cursor.fetchone()
    cursor.close()
    connection.close()
    return jsonify(user)

@app.route('/employer/<int:id>', methods=['DELETE'])
def delete_employer(id):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(f"DELETE FROM Employer WHERE EmployerID={id}")
    except:
        return jsonify({"message": "Employer not found"}), 404
    connection.commit()
    cursor.close()
    connection.close()
    return jsonify({"message": "Employer deleted"})

# Get employer by name
@app.route('/employer/<string:name>', methods=['GET'])
def get_employer_by_name(name):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(f"SELECT * FROM Employer WHERE employer_name='{name}'")
    except:
        return jsonify({"message": "Employer not found"}), 404
    user = cursor.fetchone()
    cursor.close()
    connection.close()
    return jsonify(user)

# Search for employers by name
@app.route('/employer/search/<string:name>', methods=['GET'])
def search_employers(name):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM Employer WHERE EmployerName LIKE '%{name}%'")
    users = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(users)

# Update an employer
# TODO: Finish PATCH employer
@app.route('/employer/<int:id>', methods=['PATCH'])
def update_employer(id):
    return jsonify({"message": "method not yet implemented"})


# Add a new employer
# TODO: Finish Add Employer
@app.route('/add_employer', methods=['POST'])
def add_employer():
    data = request.get_json()

    # Extract required fields
    employer_name = data.get('employer_name')
    billing_system = data.get('billing_system')
    carriers = data.get('carriers')
    carrier_plans = data.get('carrier_plans')
    employee_data = data.get('employee_data')
    tiers = data.get('tiers', None)

    if not employer_name or not billing_system or not carriers or not carrier_plans or not employee_data:
        return jsonify({'error': 'Missing required fields'}), 400

    # Process employee data if it's an Excel file in base64 encoding
    if 'employee_file' in employee_data:
        file_content = employee_data['employee_file']
        if employee_data['file_type'] == 'xlsx':
            employee_df = pd.read_excel(pd.io.common.BytesIO(base64.b64decode(file_content)))
        else:
            return jsonify({'error': 'Unsupported file type'}), 400
    else:
        employee_df = pd.DataFrame(employee_data['employees'])

    # Process data and insert into the database
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.close()
    connection.close()
    return jsonify({"message": "method not fully implemented"})


######################### Functions #########################

### Plan Functions ###
def add_plan(cursor, plan_json):
    add_plan_query = """
    INSERT INTO Plan (EmployerID, CarrierID, TierID, FundingAmount, GrenzFee, GrenzFeeC, GrenzFeeS)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    plan_data = (
        plan_json['EmployerID'], plan_json['CarrierID'], plan_json['TierID'],
        plan_json['FundingAmount'], plan_json['GrenzFee'], plan_json['GrenzFeeC'], plan_json['GrenzFeeS']
    )
    cursor.execute(add_plan_query, plan_data)
    new_plan_id = cursor.lastrowid
    return new_plan_id

def change_plan(cursor, plan_id, plan_json):
    current_plan = cursor.execute("SELECT * FROM Plan WHERE PlanID = %s", (plan_id,)).fetchall()[0][0]
    
    if not current_plan:
        raise ValueError(f"Plan with ID {plan_id} does not exist.")
    
    update_fields = []
    update_values = []
    
    for key, value in plan_json.items():
        if key != 'PlanID' and value != current_plan[key]:
            update_fields.append(f"{key} = %s")
            update_values.append(value)
    
    if update_fields:
        update_values.append(plan_id)
        update_plan_query = f"""
        UPDATE Plan
        SET {', '.join(update_fields)}
        WHERE PlanID = %s
        """
        cursor.execute(update_plan_query, tuple(update_values))

def delete_plan(cursor, plan_id):
    delete_plan_query = "DELETE FROM Plan WHERE PlanID = %s"
    cursor.execute(delete_plan_query, (plan_id,))

### Carrier Functions ###
def add_carrier(cursor, carrier_json):
    
    
    # Check if the carrier already exists
    check_carrier_query = "SELECT CarrierID FROM Carrier WHERE CarrierName = %s, EmployerID = %s"
    cursor.execute(check_carrier_query, (carrier_json['CarrierName'], carrier_json['EmployerID']))
    existing_carrier = cursor.fetchall()
    
    if existing_carrier:
        return existing_carrier[0]
    
    # Add new carrier
    add_carrier_query = """
    INSERT INTO Carrier (EmployerID, CarrierName)
    VALUES (%s, %s)
    """
    carrier_data = (
        carrier_json['EmployerID'], carrier_json['CarrierName']
    )
    cursor.execute(add_carrier_query, carrier_data)
    new_carrier_id = cursor.lastrowid
    return new_carrier_id

def change_carrier(cursor, carrier_id, carrier_json):
    current_carrier = cursor.execute("SELECT * FROM Carrier WHERE CarrierID = %s", (carrier_id,)).fetchall()[0][0]
    
    if not current_carrier:
        raise ValueError(f"Carrier with ID {carrier_id} does not exist.")
    
    update_fields = []
    update_values = []
    
    for key, value in carrier_json.items():
        if key != 'CarrierID' and value != current_carrier[key]:
            update_fields.append(f"{key} = %s")
            update_values.append(value)
    
    if update_fields:
        update_values.append(carrier_id)
        update_carrier_query = f"""
        UPDATE Carrier
        SET {', '.join(update_fields)}
        WHERE CarrierID = %s
        """
        cursor.execute(update_carrier_query, tuple(update_values))
    
    return carrier_id

def delete_carrier(cursor, carrier_id):
    
    delete_carrier_query = "DELETE FROM Carrier WHERE CarrierID = %s"
    cursor.execute(delete_carrier_query, (carrier_id,))

### Tier Functions ###
def add_tier(cursor, tier_json):
    # Check if the tier already exists
    check_tier_query = "SELECT TierID FROM Tier WHERE TierName = %s AND EmployerID = %s"
    cursor.execute(check_tier_query, (tier_json['TierName'], tier_json['EmployerID']))
    existing_tier = cursor.fetchall()
    
    if existing_tier:
        return existing_tier[0][0]
    
    # Add new tier
    add_tier_query = """
    INSERT INTO Tier (EmployerID, TierName, MaxAge, MinAge)
    VALUES (%s, %s, %s, %s)
    """
    tier_data = (
        tier_json['EmployerID'], tier_json['TierName'], tier_json['MaxAge'], tier_json['MinAge']
    )
    cursor.execute(add_tier_query, tier_data)
    new_tier_id = cursor.lastrowid
    return new_tier_id

def get_current_tier(cursor, tier_id):
    get_tier_query = "SELECT * FROM Tier WHERE TierID = %s"
    cursor.execute(get_tier_query, (tier_id,))
    current_tier = cursor.fetchone()
    return current_tier

def change_tier(cursor, tier_id, tier_json):
    current_tier = get_current_tier(cursor, tier_id)
    
    if not current_tier:
        raise ValueError(f"Tier with ID {tier_id} does not exist.")
    
    update_fields = []
    update_values = []
    
    for key, value in tier_json.items():
        if key != 'TierID' and value != current_tier[key]:
            update_fields.append(f"{key} = %s")
            update_values.append(value)
    
    if update_fields:
        update_values.append(tier_id)
        update_tier_query = f"""
        UPDATE Tier
        SET {', '.join(update_fields)}
        WHERE TierID = %s
        """
        cursor.execute(update_tier_query, tuple(update_values))
    
    return tier_id

def delete_tier(cursor, tier_id):
    delete_tier_query = "DELETE FROM Tier WHERE TierID = %s"
    cursor.execute(delete_tier_query, (tier_id,))

### Dependent Functions ###

def add_dependent(cursor, dependent_json):
    add_dependent_query = """
    INSERT INTO Dependent (EmployeeID, DependentName, Relationship, DOB, StartDate, InformStartDate)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    dependent_data = (
        dependent_json['EmployeeID'], dependent_json['DependentName'], dependent_json['Relationship'],
        dependent_json['DOB'], dependent_json['StartDate'], dependent_json['InformStartDate']
    )
    cursor.execute(add_dependent_query, dependent_data)
    new_dependent_id = cursor.lastrowid
    return new_dependent_id

def get_current_dependent(cursor, dependent_id):
    get_dependent_query = "SELECT * FROM Dependent WHERE DependentID = %s"
    cursor.execute(get_dependent_query, (dependent_id,))
    current_dependent = cursor.fetchall()
    return current_dependent

def change_dependent(cursor, dependent_id, dependent_json):
    """
    Updates an existing dependent in the database with only new values.
    Args:
        cursor: The MySQL database cursor.
        dependent_id: The ID of the dependent to update.
        dependent_json: The dependent data as a dictionary.
    Returns:
        Boolean indicating whether the employer consistency check passed.
    """
    current_dependent = get_current_dependent(cursor, dependent_id)
    
    if not current_dependent:
        raise ValueError(f"Dependent with ID {dependent_id} does not exist.")
    
    update_fields = []
    update_values = []
    
    for key, value in dependent_json.items():
        if key != 'DependentID' and value != current_dependent[key]:
            update_fields.append(f"{key} = %s")
            update_values.append(value)
    
    if update_fields:
        update_values.append(dependent_id)
        update_dependent_query = f"""
        UPDATE Dependent
        SET {', '.join(update_fields)}
        WHERE DependentID = %s
        """
        cursor.execute(update_dependent_query, tuple(update_values))
    return get_current_dependent(cursor, dependent_id)

def delete_dependent(cursor, dependent_id):
    try:
        delete_dependent_query = "DELETE FROM Dependent WHERE DependentID = %s"
        cursor.execute(delete_dependent_query, (dependent_id,))
        return True
    except:
        return False
    
### Employee Functions ###
def add_employee(cursor, employee_json):
    # Add new employee
    add_employee_query = """
    INSERT INTO Employee (EmployerID, EmployeeFullName, EmployeeFirstName, EmployeeLastName, JoinDate, TermDate, 
                          JoinInformDate, TermEndDate, DOB, CobraStatus, Notes, GL, Division, Location, Title)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    employee_data = (
        employee_json['EmployerID'], employee_json['EmployeeFullName'], employee_json['EmployeeFirstName'], 
        employee_json['EmployeeLastName'], employee_json['JoinDate'], employee_json['TermDate'], 
        employee_json['JoinInformDate'], employee_json['TermEndDate'], employee_json['DOB'], 
        employee_json['CobraStatus'], employee_json['Notes'], employee_json['GL'], employee_json['Division'], 
        employee_json['Location'], employee_json['Title']
    )
    cursor.execute(add_employee_query, employee_data)
    new_employee_id = cursor.lastrowid
    
    # Add dependents
    if 'Dependents' in employee_json:
        dependents = employee_json['Dependents']
        for dependent in dependents:
            dependent['EmployeeID'] = new_employee_id
            add_dependent(cursor, dependent)
    
    # Add employee plans
    if 'EmployeePlans' in employee_json:
        employee_plans = employee_json['EmployeePlans']
        for plan in employee_plans:
            plan['EmployeeID'] = new_employee_id
            add_employee_plan(cursor, plan)
        return new_employee_id
    
    # Get CarrierID
    carrier_id = get_carrier_id(cursor, employee_json['Carrier'], employee_json['EmployerID'])
    
    # Get TierID
    tier_id = get_tier_id(cursor, employee_json['Tier'], employee_json['DOB'], employee_json['EmployerID'])
    
    # Get PlanID
    plan_id = get_plan_id(cursor, carrier_id, tier_id)
    
    # Add EmployeePlan
    add_employee_plan(cursor, {
        'EmployeeID': new_employee_id,
        'PlanID': plan_id,
        'StartDate': employee_json['JoinDate'],
        'EndDate': employee_json['TermDate']
    })
    
    
    return new_employee_id

def get_carrier_id(cursor, carrier_name, employer_id):
    """
    Retrieves the CarrierID based on the carrier name and employer ID.
    Args:
        cursor: The MySQL database cursor.
        carrier_name: The name of the carrier.
        employer_id: The ID of the employer.
    Returns:
        The ID of the carrier.
    """
    get_carrier_query = "SELECT CarrierID FROM Carrier WHERE CarrierName = %s AND EmployerID = %s"
    cursor.execute(get_carrier_query, (carrier_name, employer_id))
    carrier = cursor.fetchone()
    if carrier:
        return carrier[0]
    raise ValueError(f"Carrier with name {carrier_name} and employer ID {employer_id} does not exist.")

def get_tier_id(cursor, tier_name, dob, employer_id):
    """
    Retrieves the TierID based on the tier name, date of birth, and employer ID.
    Args:
        cursor: The MySQL database cursor.
        tier_name: The name of the tier.
        dob: The date of birth of the employee.
        employer_id: The ID of the employer.
    Returns:
        The ID of the tier.
    """
    if tier_name:
        get_tier_query = "SELECT TierID FROM Tier WHERE TierName = %s AND EmployerID = %s"
        cursor.execute(get_tier_query, (tier_name, employer_id))
    else:
        from datetime import date
        get_tier_query = "SELECT TierID FROM Tier WHERE %s BETWEEN MinAge AND MaxAge AND EmployerID = %s"
        cursor.execute(get_tier_query, (calculate_age(employer_id, dob, date.today().year, cursor), employer_id))
    tier = cursor.fetchall()
    if tier:
        return tier[0]
    raise ValueError(f"Tier with name {tier_name} and employer ID {employer_id} does not exist.")

def get_plan_id(cursor, carrier_id, tier_id):
    """
    Retrieves the PlanID based on the carrier ID and tier ID.
    Args:
        cursor: The MySQL database cursor.
        carrier_id: The ID of the carrier.
        tier_id: The ID of the tier.
    Returns:
        The ID of the plan.
    """
    get_plan_query = "SELECT PlanID FROM Plan WHERE CarrierID = %s AND TierID = %s"
    cursor.execute(get_plan_query, (carrier_id, tier_id))
    plan = cursor.fetchone()
    if plan:
        return plan[0]
    raise ValueError(f"Plan with carrier ID {carrier_id} and tier ID {tier_id} does not exist.")

def calculate_age(employer_id, dob, year, cursor):
    #Ages are only updated on the renewal date
    query = f"SELECT RenewalDate FROM Employer WHERE EmployerID = {employer_id}"
    cursor.execute(query)
    renewal_date = cursor.fetchone()[0]
    dob = dob.split('-')
    dob = datetime.date(int(dob[0]), int(dob[1]), int(dob[2]))
    renewal_date = renewal_date.split('-')
    renewal_date = datetime.date(int(year), int(renewal_date[1]), int(renewal_date[2]))
    age = renewal_date.year - dob.year - ((renewal_date.month, renewal_date.day) < (dob.month, dob.day))
    return age

def change_employee(cursor, employee_id, employee_json):
    """
    Updates an existing employee in the database with only new values.
    Args:
        cursor: The MySQL database cursor.
        employee_id: The ID of the employee to update.
        employee_json: The employee data as a dictionary.
    Returns:
        Boolean indicating whether the employer consistency check passed.
    """
    current_employee = get_current_employee(cursor, employee_id)
    
    if not current_employee:
        raise ValueError(f"Employee with ID {employee_id} does not exist.")
    
    update_fields = []
    update_values = []
    
    for key, value in employee_json.items():
        if key != 'EmployeeID' and value != current_employee[key]:
            update_fields.append(f"{key} = %s")
            update_values.append(value)
    
    if update_fields:
        update_values.append(employee_id)
        update_employee_query = f"""
        UPDATE Employee
        SET {', '.join(update_fields)}
        WHERE EmployeeID = %s
        """
        cursor.execute(update_employee_query, tuple(update_values))
    
    return employee_id

def get_current_employee(cursor, employee_id):
    get_employee_query = "SELECT * FROM Employee WHERE EmployeeID = %s"
    cursor.execute(get_employee_query, (employee_id,))
    current_employee = cursor.fetchone()
    return current_employee

def delete_employee(cursor, employee_id):
    delete_employee_query = "DELETE FROM Employee WHERE EmployeeID = %s"
    cursor.execute(delete_employee_query, (employee_id,))

### EmployeePlan Functions ###
def add_employee_plan(cursor, employee_plan_json):
    # Add new employee plan
    add_employee_plan_query = """
    INSERT INTO EmployeePlan (EmployeeID, PlanID, StartDate, InformStartDate, EndDate, InformEndDate)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    employee_plan_data = (
        employee_plan_json['EmployeeID'], employee_plan_json['PlanID'], employee_plan_json['StartDate'],
        employee_plan_json['InformStartDate'], employee_plan_json['EndDate'], employee_plan_json['InformEndDate']
    )
    cursor.execute(add_employee_plan_query, employee_plan_data)
    new_employee_plan_id = cursor.lastrowid
    return new_employee_plan_id

def get_current_employee_plan(cursor, employee_plan_id):
    get_employee_plan_query = "SELECT * FROM EmployeePlan WHERE EmployeePlanID = %s"
    cursor.execute(get_employee_plan_query, (employee_plan_id,))
    current_employee_plan = cursor.fetchone()
    return current_employee_plan

def change_employee_plan(cursor, employee_plan_id, employee_plan_json):
    current_employee_plan = get_current_employee_plan(cursor, employee_plan_id)
    
    if not current_employee_plan:
        raise ValueError(f"Employee plan with ID {employee_plan_id} does not exist.")
    
    update_fields = []
    update_values = []
    
    for key, value in employee_plan_json.items():
        if key != 'EmployeePlanID' and value != current_employee_plan[key]:
            update_fields.append(f"{key} = %s")
            update_values.append(value)
    
    if update_fields:
        update_values.append(employee_plan_id)
        update_employee_plan_query = f"""
        UPDATE EmployeePlan
        SET {', '.join(update_fields)}
        WHERE EmployeePlanID = %s
        """
        cursor.execute(update_employee_plan_query, tuple(update_values))
    
    return employee_plan_id

def delete_employee_plan(cursor, employee_plan_id):
    delete_employee_plan_query = "DELETE FROM EmployeePlan WHERE EmployeePlanID = %s"
    cursor.execute(delete_employee_plan_query, (employee_plan_id,))

### Employer Functions ###

####### Run on Start #######

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
