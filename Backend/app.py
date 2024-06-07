from flask import Flask, request, jsonify
import mysql.connector
import pandas as pd
import json
import datetime

####################### Helper Functions #######################
app = Flask(__name__)


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


####################### Basic Methods #######################

### Plan Methods ###

# Add
@app.route('/plan', methods=['POST'])
def add_plan():
    data = request.get_json()
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            new_plan_id = add_plan(cursor, data)
            connection.commit()
        except Exception as e:
            return jsonify({"Error adding Plan ": str(e)}), 400
        cursor.close()
        connection.close()
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    return jsonify({"PlanID": new_plan_id})

# Change
@app.route('/plan/<int:id>', methods=['PATCH'])
def change_plan(id):
    data = request.get_json()
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            change_plan(cursor, id, data)
            connection.commit()
        except Exception as e:
            return jsonify({"Error changing Plan ": str(e)}), 400
        cursor.close()
        connection.close()
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    return jsonify({"PlanID": id})

# Delete
@app.route('/plan/<int:id>', methods=['DELETE'])
def delete_plan(id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            delete_plan(cursor, id)
            connection.commit()
        except Exception as e:
            return jsonify({"Error deleting Plan ": str(e)}), 400
        cursor.close()
        connection.close()
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    return jsonify({"PlanID": id})

### Tier Methods ###

# Add
@app.route('/tier', methods=['POST'])
def add_tier():
    data = request.get_json()
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            new_tier_id = add_tier(cursor, data)
            connection.commit()
        except Exception as e:
            return jsonify({"Error adding Tier ": str(e)}), 400
        cursor.close()
        connection.close()
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    return jsonify({"TierID": new_tier_id})

# Change
@app.route('/tier/<int:id>', methods=['PATCH'])
def change_tier(id):
    data = request.get_json()
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            change_tier(cursor, id, data)
            connection.commit()
        except Exception as e:
            return jsonify({"Error changing Tier ": str(e)}), 400
        cursor.close()
        connection.close()
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    return jsonify({"TierID": id})

# Delete
@app.route('/tier/<int:id>', methods=['DELETE'])
def delete_tier(id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            delete_tier(cursor, id)
            connection.commit()
        except Exception as e:
            return jsonify({"Error deleting Tier ": str(e)}), 400
        cursor.close()
        connection.close()
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    return jsonify({"TierID": id})

### Carrier Methods ###

# Add
@app.route('/carrier', methods=['POST'])
def add_carrier():
    data = request.get_json()
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            new_carrier_id = add_carrier(cursor, data)
            connection.commit()
        except Exception as e:
            return jsonify({"Error adding Carrier ": str(e)}), 400
        cursor.close()
        connection.close()
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    return jsonify({"CarrierID": new_carrier_id})

# Change
@app.route('/carrier/<int:id>', methods=['PATCH'])
def change_carrier(id):
    data = request.get_json()
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            change_carrier(cursor, id, data)
            connection.commit()
        except Exception as e:
            return jsonify({"Error changing Carrier ": str(e)}), 400
        cursor.close()
        connection.close()
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    return jsonify({"CarrierID": id})

# Delete
@app.route('/carrier/<int:id>', methods=['DELETE'])
def delete_carrier(id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            delete_carrier(cursor, id)
            connection.commit()
        except Exception as e:
            return jsonify({"Error deleting Carrier ": str(e)}), 400
        cursor.close()
        connection.close()
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    return jsonify({"CarrierID": id})

### Dependent Methods ###

# Add
@app.route('/dependent', methods=['POST'])
def add_dependent():
    data = request.get_json()
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            new_dependent_id = add_dependent(cursor, data)
            connection.commit()
        except Exception as e:
            return jsonify({"Error adding Dependent ": str(e)}), 400
        cursor.close()
        connection.close()
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    return jsonify({"DependentID": new_dependent_id})

# Change
@app.route('/dependent/<int:id>', methods=['PATCH'])
def change_dependent(id):
    data = request.get_json()
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            change_dependent(cursor, id, data)
            connection.commit()
        except Exception as e:
            return jsonify({"Error changing Dependent ": str(e)}), 400
        cursor.close()
        connection.close()
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    return jsonify({"DependentID": id})

# Delete
@app.route('/dependent/<int:id>', methods=['DELETE'])
def delete_dependent(id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            delete_dependent(cursor, id)
            connection.commit()
        except Exception as e:
            return jsonify({"Error deleting Dependent ": str(e)}), 400
        cursor.close()
        connection.close()
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    return jsonify({"DependentID": id})

### Employee Methods ###

# Add
@app.route('/employee', methods=['POST'])
def add_employee():
    data = request.get_json()
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            new_employee_id = add_employee(cursor, data)
            connection.commit()
        except Exception as e:
            return jsonify({"Error adding Employee ": str(e)}), 400
        cursor.close()
        connection.close()
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    return jsonify({"EmployeeID": new_employee_id})

# Change
@app.route('/employee/<int:id>', methods=['PATCH'])
def change_employee(id):
    data = request.get_json()
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            change_employee(cursor, id, data)
            connection.commit()
        except Exception as e:
            return jsonify({"Error changing Employee ": str(e)}), 400
        cursor.close()
        connection.close()
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    return jsonify({"EmployeeID": id})

# Delete
@app.route('/employee/<int:id>', methods=['DELETE'])
def delete_employee(id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            delete_employee(cursor, id)
            connection.commit()
        except Exception as e:
            return jsonify({"Error deleting Employee ": str(e)}), 400
        cursor.close()
        connection.close()
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    return jsonify({"EmployeeID": id})

### EmployeePlan Methods ###

# Add
@app.route('/employeeplan', methods=['POST'])
def add_employee_plan():
    data = request.get_json()
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            new_employee_plan_id = add_employee_plan(cursor, data)
            connection.commit()
        except Exception as e:
            return jsonify({"Error adding EmployeePlan ": str(e)}), 400
        cursor.close()
        connection.close()
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    return jsonify({"EmployeePlanID": new_employee_plan_id})

# Change
@app.route('/employeeplan/<int:id>', methods=['PATCH'])
def change_employee_plan(id):
    data = request.get_json()
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            change_employee_plan(cursor, id, data)
            connection.commit()
        except Exception as e:
            return jsonify({"Error changing EmployeePlan ": str(e)}), 400
        cursor.close()
        connection.close()
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    return jsonify({"EmployeePlanID": id})

# Delete
@app.route('/employeeplan/<int:id>', methods=['DELETE'])
def delete_employee_plan(id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            delete_employee_plan(cursor, id)
            connection.commit()
        except Exception as e:
            return jsonify({"Error deleting EmployeePlan ": str(e)}), 400
        cursor.close()
        connection.close()
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    return jsonify({"EmployeePlanID": id})

### Employer Methods ###

# Add
@app.route('/employer', methods=['POST'])
def add_employer():
    data = request.get_json()
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            new_employer_id = add_employer(cursor, data)
            connection.commit()
        except Exception as e:
            return jsonify({"Error adding Employer ": str(e)}), 400
        cursor.close()
        connection.close()
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    return jsonify({"EmployerID": new_employer_id})

# Change
@app.route('/employer/<int:id>', methods=['PATCH'])
def change_employer(id):
    data = request.get_json()
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            change_employer(cursor, id, data)
            connection.commit()
        except Exception as e:
            return jsonify({"Error changing Employer ": str(e)}), 400
        cursor.close()
        connection.close()
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    return jsonify({"EmployerID": id})

# Delete
@app.route('/employer/<int:id>', methods=['DELETE'])
def delete_employer(id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            delete_employer(cursor, id)
            connection.commit()
        except Exception as e:
            return jsonify({"Error deleting Employer ": str(e)}), 400
        cursor.close()
        connection.close()
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    return jsonify({"EmployerID": id})

####################### Getter Methods ######################

### GET Plan Methods ###
@app.route('/plan', methods=['GET'])
def get_plans():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Plan")
        plans = cursor.fetchall()
        cursor.close()
        connection.close()
        return jsonify(plans)
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    
@app.route('/plan/<int:id>', methods=['GET'])
def get_plan(id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM Plan WHERE PlanID={id}")
        plan = cursor.fetchone()
        cursor.close()
        connection.close()
        return jsonify(plan)
    except Exception as e:
        return jsonify({"Error": str(e)}), 400

### Search Plan Method ### 
@app.route('/plan/search', methods=['GET'])
def search_plans():
    data = request.get_json()
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        plans = SearchTable(cursor, "Plan", json.dumps(data))
        cursor.close()
        connection.close()
        return jsonify(json.loads(plans))
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    
### GET Tier Methods ###
@app.route('/tier', methods=['GET'])
def get_tiers():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Tier")
        tiers = cursor.fetchall()
        cursor.close()
        connection.close()
        return jsonify(tiers)
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    
@app.route('/tier/<int:id>', methods=['GET'])
def get_tier(id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM Tier WHERE TierID={id}")
        tier = cursor.fetchone()
        cursor.close()
        connection.close()
        return jsonify(tier)
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    
@app.route('/tier/<EmployerID>/<TierName>', methods=['GET'])
def search_tier_by_part_name(EmployerID, TierName):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM Tier WHERE EmployerID={EmployerID} AND TierName LIKE '%{TierName}%'")
        tier = cursor.fetchall()
        cursor.close()
        connection.close()
        return jsonify(tier)
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    
### Search Tier Method ###
@app.route('/tier/search', methods=['GET'])
def search_tiers():
    data = request.get_json()
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        tiers = SearchTable(cursor, "Tier", json.dumps(data))
        cursor.close()
        connection.close()
        return jsonify(json.loads(tiers))
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    
### GET Carrier Methods ###
@app.route('/carrier', methods=['GET'])
def get_carriers():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Carrier")
        carriers = cursor.fetchall()
        cursor.close()
        connection.close()
        return jsonify(carriers)
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    
@app.route('/carrier/<int:id>', methods=['GET'])
def get_carrier(id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM Carrier WHERE CarrierID={id}")
        carrier = cursor.fetchone()
        cursor.close()
        connection.close()
        return jsonify(carrier)
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    
@app.route('/carrier/<EmployerID>/<CarrierName>', methods=['GET'])
def search_carrier_by_part_name(EmployerID, CarrierName):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM Carrier WHERE EmployerID={EmployerID} AND CarrierName LIKE '%{CarrierName}%'")
        carrier = cursor.fetchall()
        cursor.close()
        connection.close()
        return jsonify(carrier)
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    
### Search Carrier Method ###
@app.route('/carrier/search', methods=['GET'])
def search_carriers():
    data = request.get_json()
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        carriers = SearchTable(cursor, "Carrier", json.dumps(data))
        cursor.close()
        connection.close()
        return jsonify(json.loads(carriers))
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    
### GET Dependent Methods ###
@app.route('/dependent', methods=['GET'])
def get_dependents():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Dependent")
        dependents = cursor.fetchall()
        cursor.close()
        connection.close()
        return jsonify(dependents)
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    
@app.route('/dependent/<int:id>', methods=['GET'])
def get_dependent(id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM Dependent WHERE DependentID={id}")
        dependent = cursor.fetchone()
        cursor.close()
        connection.close()
        return jsonify(dependent)
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    
@app.route('/dependent/<EmployerID>/<DependentName>', methods=['GET'])
def search_dependent_by_part_name(EmployerID, DependentName):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM Dependent WHERE EmployerID={EmployerID} AND DependentName LIKE '%{DependentName}%'")
        dependent = cursor.fetchall()
        cursor.close()
        connection.close()
        return jsonify(dependent)
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    
### Search Dependent Method ###
@app.route('/dependent/search', methods=['GET'])
def search_dependents():
    data = request.get_json()
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        dependents = SearchTable(cursor, "Dependent", json.dumps(data))
        cursor.close()
        connection.close()
        return jsonify(json.loads(dependents))
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    
### GET Employee Methods ###
@app.route('/employee', methods=['GET'])
def get_employees():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Employee")
        employees = cursor.fetchall()
        cursor.close()
        connection.close()
        return jsonify(employees)
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    
@app.route('/employee/<int:id>', methods=['GET'])
def get_employee(id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM Employee WHERE EmployeeID={id}")
        employee = cursor.fetchone()
        cursor.close()
        connection.close()
        return jsonify(employee)
    except Exception as e:
        return jsonify({"Error": str(e)}), 400

@app.route('/employee/<EmployerID>/<EmployeeFullName>', methods=['GET'])
def search_employee_by_part_name(EmployerID, EmployeeFullName):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM Employee WHERE EmployerID={EmployerID} AND EmployeeFullName LIKE '%{EmployeeFullName}%'")
        employee = cursor.fetchall()
        cursor.close()
        connection.close()
        return jsonify(employee)
    except Exception as e:
        return jsonify({"Error": str(e)}), 400

@app.route('/employee/<EmployerID>/active', methods=['GET'])   
def get_active_employees(EmployerID):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM Employee WHERE EmployerID={EmployerID} AND TermDate IS NULL")
        employees = cursor.fetchall()
        cursor.close()
        connection.close()
        return jsonify(employees)
    except Exception as e:
        return jsonify({"Error": str(e)}), 400

### Search Employee Method ###
@app.route('/employee/search', methods=['GET'])
def search_employees():
    data = request.get_json()
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        employees = SearchTable(cursor, "Employee", json.dumps(data))
        cursor.close()
        connection.close()
        return jsonify(json.loads(employees))
    except Exception as e:
        return jsonify({"Error": str(e)}), 400

### GET EmployeePlan Methods ###
@app.route('/employeeplan', methods=['GET'])
def get_employee_plans():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM EmployeePlan")
        employee_plans = cursor.fetchall()
        cursor.close()
        connection.close()
        return jsonify(employee_plans)
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    
@app.route('/employeeplan/<int:id>', methods=['GET'])
def get_employee_plan(id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM EmployeePlan WHERE EmployeePlanID={id}")
        employee_plan = cursor.fetchone()
        cursor.close()
        connection.close()
        return jsonify(employee_plan)
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    
@app.route('/employeeplan/<EmployeeID>/active', methods=['GET'])
def get_active_employee_plans(EmployeeID):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM EmployeePlan WHERE EmployeeID={EmployeeID} AND EndDate IS NULL")
        employee_plans = cursor.fetchall()
        cursor.close()
        connection.close()
        return jsonify(employee_plans)
    except Exception as e:
        return jsonify({"Error": str(e)}), 400

### Search EmployeePlan Method ###
@app.route('/employeeplan/search', methods=['GET'])
def search_employee_plans():
    data = request.get_json()
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        employee_plans = SearchTable(cursor, "EmployeePlan", json.dumps(data))
        cursor.close()
        connection.close()
        return jsonify(json.loads(employee_plans))
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    
### GET Employer Methods ###
@app.route('/employer', methods=['GET'])
def get_employers():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Employer")
        employers = cursor.fetchall()
        cursor.close()
        connection.close()
        return jsonify(employers)
    except Exception as e:
        return jsonify({"Error": str(e)}), 400

@app.route('/employer/<int:id>', methods=['GET'])
def get_employer(id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM Employer WHERE EmployerID={id}")
        employer = cursor.fetchone()
        cursor.close()
        connection.close()
        return jsonify(employer)
    except Exception as e:
        return jsonify({"Error": str(e)}), 400

@app.route('/employer/<EmployerName>', methods=['GET'])
def search_employer_by_name(EmployerName):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM Employer WHERE EmployerName LIKE '%{EmployerName}%'")
        employer = cursor.fetchall()
        cursor.close()
        connection.close()
        return jsonify(employer)
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    
### Search Employer Method ###
@app.route('/employer/search', methods=['GET'])
def search_employers():
    data = request.get_json()
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        employers = SearchTable(cursor, "Employer", json.dumps(data))
        cursor.close()
        connection.close()
        return jsonify(json.loads(employers))
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
        




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
def add_employer(cursor, employer_json):
    # Add new employer
    add_employer_query = """
    INSERT INTO Employer (EmployerName, TierStructure, UsesGlCode, UsesDivision, UsesLocation, UsesTitle, PerferedBillingDate, RenewalDate)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    employer_data = (
        employer_json['EmployerName'], employer_json['TierStructure'], employer_json['UsesGlCode'],
        employer_json['UsesDivision'], employer_json['UsesLocation'], employer_json['UsesTitle'],
        employer_json['PerferedBillingDate'], employer_json['RenewalDate']
    )
    cursor.execute(add_employer_query, employer_data)
    new_employer_id = cursor.lastrowid
    
    # Add carriers
    if 'carriers' in employer_json:
        carriers = employer_json['carriers']
        for carrier in carriers:
            carrier['EmployerID'] = new_employer_id
            add_carrier(cursor, carrier)
    
    # Add tiers
    if 'tiers' in employer_json:
        tiers = employer_json['tiers']
        for tier in tiers:
            tier['EmployerID'] = new_employer_id
            add_tier(cursor, tier)
    
    # Add plans
    if 'plans' in employer_json:
        plans = employer_json['plans']
        for plan in plans:
            plan['EmployerID'] = new_employer_id
            add_plan(cursor, plan)
    
    # Add employees
    if 'employees' in employer_json:
        employees = employer_json['employees']
        for employee in employees:
            employee['EmployerID'] = new_employer_id
            add_employee(cursor, employee)
    
    return new_employer_id

def get_current_employer(cursor, employer_id):
    get_employer_query = "SELECT * FROM Employer WHERE EmployerID = %s"
    cursor.execute(get_employer_query, (employer_id,))
    current_employer = cursor.fetchone()
    return current_employer

def change_employer(cursor, employer_id, employer_json):
    current_employer = get_current_employer(cursor, employer_id)
    
    if not current_employer:
        raise ValueError(f"Employer with ID {employer_id} does not exist.")
    
    update_fields = []
    update_values = []
    
    for key, value in employer_json.items():
        if key != 'EmployerID' and value != current_employer[key]:
            update_fields.append(f"{key} = %s")
            update_values.append(value)
    
    if update_fields:
        update_values.append(employer_id)
        update_employer_query = f"""
        UPDATE Employer
        SET {', '.join(update_fields)}
        WHERE EmployerID = %s
        """
        cursor.execute(update_employer_query, tuple(update_values))
    
    return employer_id

def delete_employer(cursor, employer_id):
    delete_employer_query = "DELETE FROM Employer WHERE EmployerID = %s"
    cursor.execute(delete_employer_query, (employer_id,))


### General Search Function ###
def SearchTable(cursor, table_name, search_criteria_json):
    """
    Retrieves all items in table that match the given criteria.
    Args:
        cursor: The MySQL database cursor.
        table_name: The name of the table to search.
        search_criteria_json: A JSON object containing the search criteria.
    Returns:
        A JSON array of items that match the criteria.
    """
    search_criteria = json.loads(search_criteria_json)
    
    base_query = f"SELECT * FROM {table_name} WHERE "
    conditions = []
    values = []

    for key, value in search_criteria.items():
        conditions.append(f"{key} = %s")
        values.append(value)

    query = base_query + " AND ".join(conditions)
    cursor.execute(query, tuple(values))
    results = cursor.fetchall()

    # Convert results to a list of dictionaries
    field_names = [i[0] for i in cursor.description]
    plans = [dict(zip(field_names, row)) for row in results]
    
    return json.dumps(plans)

####### Run on Start #######

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
