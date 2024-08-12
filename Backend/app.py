import calendar
from flask import Flask, request, jsonify, send_file
import mysql.connector
import pandas as pd
import json
import datetime
from datetime import datetime, timedelta, date
from mysql.connector.cursor import MySQLCursor
import os
from flask_cors import CORS

####################### Helper Functions #######################
app = Flask(__name__)
# CORS(app)
CORS(app, expose_headers=['Content-Disposition'])

def get_db_connection():
    connection = mysql.connector.connect(
        host='host.docker.internal',  # This matches the service name defined in docker-compose.yml
        user='root',
        password='Root',
        database='modelBillingDBv1'
    )
    return connection

def setup_db():
    connection = get_db_connection()
    cursor = connection.cursor()

    # Get the path to init.sql dynamically
    script_dir = os.path.dirname(__file__)  # Directory of the script
    sql_file_path = os.path.join(script_dir, 'init.sql')
    
    with open(sql_file_path, 'r') as f:
        sql_commands = f.read()
    
    # Split the commands by semicolon to execute them individually
    for command in sql_commands.split(';'):
        if command.strip():
            cursor.execute(command)
    
    connection.commit()
    cursor.close()
    connection.close()
    return "Database setup complete"

@app.route('/setup_db', methods=['GET'])
def setup_db_route():
    try:
        message = setup_db()
        return jsonify({'message': message})
    except Exception as e:
        return jsonify({'error': str(e)})


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
        
@app.route('/apiFunctions.js', methods=['GET'])
def get_api_functions():
    return send_file('./apiFunctions.js')

@app.route('/config.js', methods=['GET'])
def get_config():
    return send_file('./config.js')
    


# table fields
get_table_fields = lambda key, subkey: {
    "Plan":{ 
        "RequiredFields" : ["EmployerID", "CarrierID", "TierID", "FundingAmount", "GrenzFee", "StartDate"],
        "OptionalFields": ["PlanID", "GrenzFeeC", "GrenzFeeS", "EndDate"],
        "DenormalizedData" : ["CarrierName", "TierName", "EmployerID"],
        "DenormalizeDataFunctions" : {"CarrierName": getCarrierNameForPlan, "TierName": getTierNameForPlan, "EmployerID": getEmployerIDForPlan}
    },
    "Tier": {
        "RequiredFields" : ["EmployerID", "TierName"],
        "OptionalFields": ["TierID", "MaxAge", "MinAge"]
    },
    "Carrier": {
        "RequiredFields" : ["EmployerID", "CarrierName"],
        "OptionalFields": ["CarrierID"]
    },
    "Dependent": {
        "RequiredFields" : ["EmployeeID", "DependentName", "Relationship", "DOB", "StartDate"],
        "OptionalFields": ["InformStartDate", "EndDate", "InformEndDate", "Notes"],
    },
    "Employee": {
        "RequiredFields" : ["EmployerID", "EmployeeFullName", "StartDate"],
        "OptionalFields": ["EmployeeID", "EndDate", "InformStartDate", "InformEndDate", "DOB", "CobraStatus", "Notes", "GlCode", "Division", "Location", "Title", "EmployeeFirstName", "EmployeeLastName"],
        "Subtables": ["Dependents", "EmployeePlan"],
        "DenormalizedData" : ['Carrier', 'Tier'],
        "DenormalizedDataFunctions" : {'Carrier': getCarrierForEmployee, 'Tier': getTierForEmployee}
    },
    "EmployeePlan": {
        "RequiredFields" : ["EmployeeID", "PlanID", "StartDate"],
        "OptionalFields": ["EmployeePlanID", "EndDate", "InformEndDate", "InformStartDate"],
    },
    "Employer": {
        "RequiredFields" : ["EmployerName", "TierStructure", "RenewalDate"],
        "OptionalFields": ["EmployerID", "UsesGlCode", "UsesDivision", "UsesLocation", "UsesTitle", "PerferedBillingDate"],
        "OptionalSetToFalse": ["UsesGlCode", "UsesDivision", "UsesLocation", "UsesTitle"],
        "Subtables": ["Carriers", "Tiers", "Plans", "Employees"]
    }
}.get(key, {}).get(subkey, [])


#### Denormalize Data Functions ####

def getCarrierNameForPlan(cursor, plan):
    try:
        return execute_query(cursor, f"SELECT CarrierName FROM Carrier WHERE CarrierID = {plan['CarrierID']}")[0][0]
    except Exception as e:
        raise ValueError(f"Get Carrier Name for Plan: " + str(e))
    
def getTierNameForPlan(cursor, plan):
    try:
        return execute_query(cursor, f"SELECT TierName FROM Tier WHERE TierID = {plan['TierID']}")[0][0]
    except Exception as e:
        raise ValueError(f"Get Tier Name for Plan: " + str(e))
    
def getEmployerIDForPlan(cursor, plan):
    try:
        try:
            EmployerID = execute_query(cursor, f"SELECT EmployerID FROM Tier WHERE TierID (SELECT PlanID = {plan['PlanID']}")[0][0]
        except Exception as e:
            EmployerID = execute_query(cursor, f"SELECT EmployerID FROM Carrier WHERE CarrierID (SELECT PlanID = {plan['PlanID']}")[0][0]
            return EmployerID
        return EmployerID
    except Exception as e:
        raise ValueError(f"Get EmployerID for Plan: " + str(e))
    
def getCarrierForEmployee(cursor, employee):
    try:
        return execute_query(cursor, f"SELECT CarrierName FROM Carrier WHERE CarrierID = (SELECT CarrierID FROM Plan WHERE PlanID = (SELECT PlanID FROM EmployeePlan WHERE EmployeeID = {employee['EmployeeID']}))")[0][0]
    except Exception as e:
        raise ValueError(f"Get Carrier for Employee: " + str(e))
    
def getTierForEmployee(cursor, employee):
    try:
        planid = get_plan_for_employee(cursor, employee['EmployeeID'])
        tier = execute_query(cursor, f"SELECT TierName FROM Tier WHERE TierID = (SELECT TierID FROM Plan WHERE PlanID = {planid})")[0][0]
        return tier
    except Exception as e:
        raise ValueError(f"Get Tier for Employee: " + str(e))
####################### Basic Methods #######################

### Plan Methods ###

# Add
@app.route('/plan', methods=['POST'])
def add_new_plan():
    data = request.get_json()
    return route_add_element("Plan", data)

# Change
@app.route('/plan/<int:id>', methods=['PATCH'])
def change_plan(id):
    data = request.get_json()
    return route_change_element("Plan", id, data)

# Delete
@app.route('/plan/<int:id>', methods=['DELETE'])
def delete_plan(id):
    return route_delete_element(id, "Plan")

# modify
@app.route('/plan/<int:id>/modify', methods=['PATCH'])
def modify_plan_route(id):
    data = request.get_json()
    return modify_plan(id, data)

# End
@app.route('/plan/<int:id>/end', methods=['PATCH'])
def end_plan(id):
    data = request.get_json()
    return end_plan(id, "Plan", data)

### Tier Methods ###

# Add
@app.route('/tier', methods=['POST'])
def add_tier():
    data = request.get_json()
    return route_add_element("Tier", data)

# Change
@app.route('/tier/<int:id>', methods=['PATCH'])
def change_tier(id):
    data = request.get_json()
    return route_change_element("Tier", id, data)

# Delete
@app.route('/tier/<int:id>', methods=['DELETE'])
def delete_tier(id):
    return route_delete_element(id, "Tier")

### Carrier Methods ###

# Add
@app.route('/carrier', methods=['POST'])
def add_carrier():
    data = request.get_json()
    return route_add_element("Carrier", data)

# Change
@app.route('/carrier/<int:id>', methods=['PATCH'])
def change_carrier(id):
    data = request.get_json()
    return route_change_element("Carrier", id, data)

# Delete
@app.route('/carrier/<int:id>', methods=['DELETE'])
def delete_carrier(id):
    return route_delete_element(id, "Carrier")

### Dependent Methods ###

# Add
@app.route('/dependent', methods=['POST'])
def add_dependent():
    data = request.get_json()
    return route_add_element("Dependent", data)

# Change
@app.route('/dependent/<int:id>', methods=['PATCH'])
def change_dependent(id):
    data = request.get_json()
    return route_change_element("Dependent", id, data)

# Delete
@app.route('/dependent/<int:id>', methods=['DELETE'])
def delete_dependent(id):
    return route_delete_element(id, "Dependent")

### Employee Methods ###

# Add
@app.route('/employee', methods=['POST'])
def add_employee():
    data = request.get_json()
    return route_add_element("Employee", data)

# Change
@app.route('/employee/<int:id>', methods=['PATCH'])
def change_employee(id):
    data = request.get_json()
    return route_change_element("Employee", id, data)

# Delete
@app.route('/employee/<int:id>', methods=['DELETE'])
def delete_employee(id):
    return route_delete_element(id, "Employee")

@app.route('/employee/<int:id>/terminate', methods=['PATCH'])
def terminate_employee_route(id):
    data = request.get_json()
    return terminate_employee(id, data["EndDate"], data["InformEndDate"])

### EmployeePlan Methods ###

# Add
@app.route('/employeeplan', methods=['POST'])
def add_employee_plan():
    data = request.get_json()
    return route_add_element("EmployeePlan", data)

# Change
@app.route('/employeeplan/<int:id>', methods=['PATCH'])
def change_employee_plan(id):
    data = request.get_json()
    return route_change_element("EmployeePlan", id, data)

# Delete
@app.route('/employeeplan/<int:id>', methods=['DELETE'])
def delete_employee_plan(id):
    return route_delete_element(id, "EmployeePlan")

### Employer Methods ###

# Add
@app.route('/employer', methods=['POST'])
def add_employer():
    data = request.get_json()
    return route_add_element("Employer", data)

# Change
@app.route('/employer/<int:id>', methods=['PATCH'])
def change_employer(id):
    data = request.get_json()
    return route_change_element("Employer", id, data)

# Delete
@app.route('/employer/<int:id>', methods=['DELETE'])
def delete_employer(id):
    return route_delete_element(id, "Employer")

####################### Getter Methods ######################

### GET Plan Methods ###
@app.route('/plan', methods=['GET'])
def get_plans():
    return get_all("Plan")
    
@app.route('/plan/<int:id>', methods=['GET'])
def get_plan(id):
    return get_by_id("Plan", id)

### Search Plan Method ### 
@app.route('/plan/search', methods=['POST'])
def search_plans():
    data = request.get_json()
    return search_table("Plan", data)

@app.route('/plan/<EmployerID>/active', methods=['GET'])
def get_active_plans(EmployerID):
    return get_active("Plan", EmployerID, "EndDate")
    
### GET Tier Methods ###
@app.route('/tier', methods=['GET'])
def get_tiers():
    return get_all("Tier")
    
@app.route('/tier/<int:id>', methods=['GET'])
def get_tier(id):
    return get_by_id("Tier", id)
    
@app.route('/tier/<EmployerID>/<TierName>', methods=['GET'])
def search_tier_by_part_name(EmployerID, TierName):
    return search_by_part_name("Tier", TierName, EmployerID)
    
### Search Tier Method ###
@app.route('/tier/search', methods=['POST'])
def search_tiers():
    data = request.get_json()
    return search_table("Tier", data)
    
### GET Carrier Methods ###
@app.route('/carrier', methods=['GET'])
def get_carriers():
    return get_all("Carrier")
    
@app.route('/carrier/<int:id>', methods=['GET'])
def get_carrier(id):
    return get_by_id("Carrier", id)
    
@app.route('/carrier/<EmployerID>/<CarrierName>', methods=['GET'])
def search_carrier_by_part_name(EmployerID, CarrierName):
    return search_by_part_name("Carrier", CarrierName, EmployerID)
    
### Search Carrier Method ###
@app.route('/carrier/search', methods=['POST'])
def search_carriers():
    data = request.get_json()
    return search_table("Carrier", data)
    
### GET Dependent Methods ###
@app.route('/dependent', methods=['GET'])
def get_dependents():
    return get_all("Dependent")
    
@app.route('/dependent/<int:id>', methods=['GET'])
def get_dependent(id):
    return get_by_id("Dependent", id)
    
@app.route('/dependent/<EmployerID>/<DependentName>', methods=['GET'])
def search_dependent_by_part_name(EmployerID, DependentName):
    return search_by_part_name("Dependent", DependentName, EmployerID)
    
### Search Dependent Method ###
@app.route('/dependent/search', methods=['POST'])
def search_dependents():
    data = request.get_json()
    return search_table("Dependent", data)
    
### GET Employee Methods ###
@app.route('/employee', methods=['GET'])
def get_employees():
    return get_all("Employee")
    
@app.route('/employee/<int:id>', methods=['GET'])
def get_employee(id):
    return get_by_id("Employee", id)

@app.route('/employee/<EmployerID>/<EmployeeFullName>', methods=['GET'])
def search_employee_by_part_name(EmployerID, EmployeeFullName):
    return search_by_part_name("Employee", EmployeeFullName, EmployerID)

@app.route('/employee/<EmployerID>/active', methods=['GET'])   
def get_active_employees(EmployerID):
    return get_active("Employee", EmployerID, "EndDate")

### Search Employee Method ###
@app.route('/employee/search', methods=['POST'])
def search_employees():
    data = request.get_json()
    return search_table("Employee", data)

### GET EmployeePlan Methods ###
@app.route('/employeeplan', methods=['GET'])
def get_employee_plans():
    return get_all("EmployeePlan")

@app.route('/employeeplan/<int:id>', methods=['GET'])
def get_employee_plan(id):
    return get_by_id("EmployeePlan", id)
    
@app.route('/employeeplan/<EmployeeID>/active', methods=['GET'])
def get_active_employee_plans(EmployeeID):
    return get_active("EmployeePlan", EmployeeID, "EndDate", "EmployeeID")

### Search EmployeePlan Method ###
@app.route('/employeeplan/search', methods=['POST'])
def search_employee_plans():
    data = request.get_json()
    return search_table("EmployeePlan", data)
    
### GET Employer Methods ###
@app.route('/employer', methods=['GET'])
def get_employers():
    return get_all("Employer")

@app.route('/employer/<int:id>', methods=['GET'])
def get_employer(id):
    return get_by_id("Employer", id)

@app.route('/employer/<EmployerName>', methods=['GET'])
def search_employer_by_part_name(EmployerName):
    return search_by_part_name("Employer", EmployerName)
    
### Search Employer Method ###
@app.route('/employer/search', methods=['POST'])
def search_employers():
    data = request.get_json()
    return search_table("Employer", data)
    
###### Refactoring ######

### Get full element ###
def get_full_element_by_id(cursor: MySQLCursor, table_name: str, id: int):
    soft_errors = []
    try:
        # make sure the table name is capitalized
        if get_table_fields(table_name, "RequiredFields") == []:
            table_name = table_name.capitalize()
        # check if the table name is valid
        if get_table_fields(table_name, "RequiredFields") == []:
            #remove the last leter of the table name to get the singular form
            table_name = table_name[:-1]
        if get_table_fields(table_name, "RequiredFields") == []:
            raise ValueError(f"Table {table_name} does not exist.")
        
        element = get_element_by_id(cursor, table_name, id)

        # denormalize the data
        for field in get_table_fields(table_name, "DenormalizedData"):
            try:
                if not (field in element):
                    element[field] = get_table_fields(table_name, "DenormalizedDataFunctions")[field](cursor, element)
            except Exception as e:
                soft_errors.append(f"Error denormalizing {field}: {str(e)}")

        # get subtables
        for subtable in get_table_fields(table_name, "Subtables"):
            try:
                subtable_name = subtable
                # make sure the table name is capitalized
                if get_table_fields(subtable_name, "RequiredFields") == []:
                    subtable_name = subtable_name.capitalize()
                # check if the table name is valid
                if get_table_fields(subtable_name, "RequiredFields") == []:
                    #remove the last leter of the table name to get the singular form
                    subtable_name = subtable_name[:-1]
                if get_table_fields(subtable_name, "RequiredFields") == []:
                    raise ValueError(f"Table {subtable_name} does not exist.")
                element_ids = execute_query(cursor, f"SELECT {subtable_name}ID FROM {subtable_name} WHERE {table_name}ID = {id}")
                element[subtable] = []
                for element_id in element_ids:
                    element[subtable].append(get_full_element_by_id(cursor, subtable_name, element_id[0]))
            except Exception as e:
                soft_errors.append(f"Error getting subtable {subtable}: {str(e)}")
        return element
    except Exception as e:
        raise ValueError(f"Get Full Element by ID: " + str(e))

@app.route('/full/<table_name>/<int:id>', methods=['GET'])
def route_get_full_element_by_id(table_name, id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        # Note: Not using softerrors rn
        element = get_full_element_by_id(cursor, table_name, id)
        soft_errors = []
        cursor.close()
        connection.close()
        response = {"status": "success", "Element": element}
        if soft_errors:
            response["warnings"] = soft_errors
        return jsonify(response), 201
    except ValueError as ve:
        # raise ValueError(ve)
        return jsonify({"Error": str(ve)}), 400
    except Exception as e:
        return jsonify({"Error": str(e)}), 500

### General Search Function ###
def SearchTable(cursor: MySQLCursor, table_name: str, search_criteria_json: json):
    """
    Retrieves all items in table that match the given criteria.
    Args:
        cursor: The MySQL database cursor.
        table_name: The name of the table to search.
        search_criteria_json: A JSON object containing the search criteria.
    Returns:
        A JSON array of items that match the criteria.
    """
    try:
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
        try:
            # Convert results to a list of dictionaries
            field_names = [i[0] for i in cursor.description]
            plans = [dict(zip(field_names, row)) for row in results]
        except Exception as e:
            raise ValueError(f"Error converting results: " + str(e))
        
        try:
            return json.dumps(plans)
        except Exception as e:
            try:
                return json.dumps(plans, default=str)
            except Exception as e:
                raise ValueError("Error converting results: " + str(e) + " Data being converted: " + str(plans))
    except Exception as e:
        raise ValueError(f"SearchTable: " + str(e))


def get_all(table_name):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(f"SELECT {table_name}ID FROM {table_name}")
        employers = cursor.fetchall()
        new_employers = []
        for employer in employers:
            new_employers.append(get_element_by_id(cursor, table_name, employer[0]))
        cursor.close()
        connection.close()
        return jsonify(new_employers)
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    
def get_by_id(table_name, id):
    return route_get_element_by_id(table_name, id)
    
def search_by_part_name(table_name, Name, EmployerID=None):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        if EmployerID is None:
            cursor.execute(f"SELECT * FROM {table_name} WHERE {table_name}Name LIKE '%{Name}%'")
        else:
            cursor.execute(f"SELECT {table_name}ID FROM {table_name} WHERE EmployerID={EmployerID} AND {table_name}Name LIKE '%{Name}%'")
        employers = cursor.fetchall()
        new_employers = []
        for employer in employers:
            new_employers.append(get_element_by_id(cursor, table_name, employer[0]))
        cursor.close()
        connection.close()
        return jsonify(new_employers)
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    
def search_table(table_name, data: json):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        employers = SearchTable(cursor, table_name, json.dumps(data))
        cursor.close()
        connection.close()
        return jsonify(json.loads(employers))
    except Exception as e:
        # raise ValueError(f"search_table: data json:" + str(data) + " Error: " + str(e) )
        return jsonify({"Error": str(e)}), 400
    
def get_active(table_name, EmployerID, end_term, Identifyer="EmployerID"):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        employees = get_active_depfree(cursor, table_name, EmployerID, end_term, Identifyer)
        for employee in employees:
            employee = get_element_by_id(cursor, table_name, employee[0])
        cursor.close()
        connection.close()
        return jsonify(employees)
    except Exception as e:
        return jsonify({"Error": str(e)}), 400
    
def get_active_depfree(cursor, table_name, EmployerID, end_term="InformEndDate", Identifyer="EmployerID"):
    try:
        cursor.execute(f"SELECT * FROM {table_name} WHERE {Identifyer}={EmployerID} AND {end_term} IS NULL")
        employees = cursor.fetchall()
        return employees
    except Exception as e:
        raise ValueError(f"Get Active: " + str(e))
      
def get_active_on_date(cursor, table_name, EmployerID, Date, Identifyer="EmployerID"):
    try:
        employees = execute_query(cursor, f"SELECT * FROM {table_name} WHERE {Identifyer}={EmployerID} AND InformStartDate <= '{Date}' AND (InformEndDate >= '{Date}' OR InformEndDate IS NULL)")
        return employees
    except Exception as e:
        raise ValueError(f"Get Active on Date: " + str(e))


######################### Functions #########################

def add_element_by_table_name(cursor: MySQLCursor, table_name, element_json):
    soft_errors = []
    # Make sure element_json is a dictionary
    if isinstance(element_json, str):
        element_json = json.loads(element_json)
    # Make sure it's not a list
    if isinstance(element_json, list):
        raise ValueError("Element cannot be a list. Please provide a dictionary.")

    # make sure the table name is capitalized
    if get_table_fields(table_name, "RequiredFields") == []:
        table_name = table_name.capitalize()
    # check if the table name is valid
    if get_table_fields(table_name, "RequiredFields") == []:
        #remove the last leter of the table name to get the singular form
        table_name = table_name[:-1]
    if get_table_fields(table_name, "RequiredFields") == []:
        raise ValueError(f"Table {table_name} does not exist.")
    
    # get the required and optional fields for the table
    required_fields = get_table_fields(table_name, "RequiredFields")
    optional_fields = get_table_fields(table_name, "OptionalFields")

    # auto fill holes
    if table_name == "Employee":
        try:
            try:
                if "EmployeeFullName" not in element_json:
                    element_json["EmployeeFullName"] = element_json["EmployeeFirstName"] + " " + element_json["EmployeeLastName"]
            except Exception as e:
                raise ValueError(f"Auto fill EmployeeFullName: " + str(e))
            try:
                element_json["StartDate"], message = get_date_with_message(element_json, "StartDate", "InformStartDate")
                if message:
                    soft_errors.append(message)
                element_json["InformStartDate"], message = get_date_with_message(element_json, "InformStartDate", "StartDate")
                if message:
                    soft_errors.append(message)
            except Exception as e:
                raise ValueError(f"Auto fill StartDate: " + str(e))
            try:
                if "EmployeePlan" not in element_json:
                    try:
                        # Get CarrierID
                        carrier_id = get_carrier_id(cursor, element_json['Carrier'], element_json['EmployerID'])
                    except Exception as e:
                        raise ValueError(f"Get CarrierID: " + str(e) + " " + str(element_json['Carrier']) + " " + str(element_json['EmployerID']))
                    
                    try:
                        if (get_employer_tier_structure(cursor, element_json['EmployerID']).lower().find("age") != -1):
                            tier_id = get_tier_id(cursor, element_json['Tier'], datetime.strptime(str(element_json['DOB']).split(" ")[0], "%Y-%m-%d"), element_json['EmployerID'])
                        else:
                            tier_id = execute_query(cursor, f"SELECT TierID FROM Tier WHERE TierName = \"{element_json['Tier']}\" AND EmployerID = {element_json['EmployerID']}")[0][0]
                    except Exception as e:
                        raise ValueError(f"Get TierID: " + str(e))
                    
                    try:    
                        # Get PlanID
                        plan_id = get_only_active_plan_on_date(cursor, carrier_id, tier_id, element_json['StartDate'])
                    except Exception as e:
                        raise ValueError(f"Get PlanID: " + str(e))
                    
                    try:
                        # Add EmployeePlan
                        element_json["EmployeePlan"] =[{
                            'PlanID': plan_id,
                            'InformStartDate': element_json['StartDate'],
                            'StartDate': element_json['StartDate'],
                            'EndDate': None,
                            'InformEndDate': None
                        }]
                    except Exception as e:
                        raise ValueError(f"Add EmployeePlan: " + str(e))
            except Exception as e:
                raise ValueError(f"Auto fill EmployeePlan: " + str(e))
        except Exception as e:
            raise ValueError(f"Auto fill Employee: " + str(e))
        
    elif table_name == "Dependent":
        element_json["StartDate"], message = get_date_with_message(element_json, "StartDate", "InformStartDate")
        if message:
            soft_errors.append(message)
        element_json["InformStartDate"], message = get_date_with_message(element_json, "InformStartDate", "StartDate")
        if message:
            soft_errors.append(message)
        if "DepentdentID" in element_json:
            depstuff = cursor.execute(f"SELECT * FROM Dependent WHERE DependentID = {element_json['DependentID']}")
            if (depstuff != None):
                if(cursor.fetchall() != []):
                    soft_errors.append("DependentID already exists, new id will be generated.")
                    element_json.remove("DependentID")

    elif table_name == "EmployeePlan":
        element_json["StartDate"], message = get_date_with_message(element_json, "StartDate", "InformStartDate")
        if message:
            soft_errors.append(message)
        element_json["InformStartDate"], message = get_date_with_message(element_json, "InformStartDate", "StartDate")
        if message:
            soft_errors.append(message)

    elif table_name == "Employer":
        element_json["PreferredBillingDate"], message = get_date_with_message(element_json, "PreferredBillingDate", "RenewalDate")
        if message:
            soft_errors.append(message)
        if "RenewalDate" not in element_json:
            #set the renewal date to the first of the month and notify the user
            element_json["RenewalDate"] = datetime.strptime(datetime.now, '%Y-%m-%d').replace(day=1).strftime('%Y-%m-%d')
            soft_errors.append("Renewal Date was not provided, using the first of the month.")
        #check if renewal date is the first of the month
        if element_json["RenewalDate"].split('-')[2] != '01':
            soft_errors.append("Renewal Date is not the first of the month.")
        for field in get_table_fields(table_name, "OptionalSetToFalse"):
            if field not in element_json:
                element_json[field] = False

    elif table_name == "Plan":
        
        element_json["CarrierID"] = get_carrier_id(cursor, element_json["CarrierName"], element_json["EmployerID"])
        
        element_json["TierID"] = get_tier_id(cursor, element_json["TierName"], datetime.today(), element_json["EmployerID"])

        if "StartDate" not in element_json:
            element_json["StartDate"] = execute_query(cursor, f"SELECT RenewalDate FROM Employer WHERE EmployerID = {element_json['EmployerID']}")[0][0]

    elif table_name == "Tier":
        #if max age contains a +, set it to 999
        if "MaxAge" in element_json:
            if isinstance(element_json["MaxAge"], str):
                if element_json["MaxAge"].find("+") != -1:
                    element_json["MaxAge"] = 9999
        #if min age contains a -, set it to 0
        if "MinAge" in element_json:
            if isinstance(element_json["MinAge"], str):
                if element_json["MinAge"].find("-") != -1:
                    element_json["MinAge"] = 0
    
    # add the element to the table
    try:
        try:
            element_id, s_errors = add_element(cursor, table_name, element_json, required_fields, optional_fields)
            soft_errors.append(s_errors)
        except Exception as e:
            raise ValueError(f"Adding {table_name}: " + str(e))
        try:
            for subtable in get_table_fields(table_name, "Subtables"):
                if subtable in element_json:
                    for sub_element in element_json[subtable]:
                        try:
                            sub_element[table_name + "ID"] = str(element_id)
                        except Exception as e:
                            raise ValueError(f"Adding ID: " + str(e) + " Subelement:" + str(sub_element))
                        try:
                            s_errors, sub_element_id = add_element_by_table_name(cursor, subtable, sub_element)
                        except Exception as e:
                            raise ValueError(f"Subtable {subtable}: " + str(e))
    
                        for errorKey in s_errors:
                            el_errors = []
                            error = s_errors[errorKey]
                            if error != None and error != [] and error != [[]]:
                                el_errors.append(error)
                            if el_errors != []:
                                soft_errors.append({errorKey: el_errors})                                             
        except Exception as e:
            raise ValueError(f"Adding Subtables: " + str(e))
        if soft_errors == []:
            soft_errors = None
        if element_json.get(f"{table_name}Name" , "") == "":
            if table_name == "Plan":
                carrier_name = element_json["CarrierName"]
                tier_name = element_json["TierName"]
                element_json["PlanName"] = f"{carrier_name} + {tier_name}"
            elif table_name == "EmployeePlan":
                element_json["EmployeePlanName"] = f"Plan"
            elif table_name == "Employee":
                element_json['EmployeeName'] = element_json['EmployeeFullName']
        return {element_json[f"{table_name}Name"]: soft_errors}, element_id
    except Exception as e:
        raise ValueError(f"Add {table_name}: " + str(e))
    


try_set_dates = lambda element_json, preferred_datename, backup_datename: (
    element_json.get(preferred_datename, "") if element_json.get(preferred_datename, "") != "" else
    element_json.get(backup_datename, "") if element_json.get(backup_datename, "") != "" else
    (datetime.now().strftime('%Y-%m-%d'), f"{preferred_datename} Date was not provided, using the current date.")
)

def get_date_with_message(element_json, preferred_datename, backup_datename):
    result = try_set_dates(element_json, preferred_datename, backup_datename)
    if isinstance(result, tuple):
        return result
    return result, None

def change_element_by_table_name(cursor, table_name: str, element_id, element_json):
    soft_errors = []
    # make sure the table name is capitalized
    table_name = table_name.capitalize()
    # check if the table name is valid
    if get_table_fields(table_name, "RequiredFields") == []:
        raise ValueError(f"Table {table_name} does not exist.")
    # get the required and optional fields for the table
    required_fields = get_table_fields(table_name, "RequiredFields")
    optional_fields = get_table_fields(table_name, "OptionalFields")
    soft_errors, element_id = change_element(cursor, table_name, element_id, element_json, required_fields, optional_fields)
    return soft_errors, element_id

### Plan Functions ###


def modify_plan(cursor, plan_id, plan_json):
    # this function will end the old plan and create a new one then move all the employees on the old plan to the new one. Use the old plan to fill in any missing fields
    try:
        # Get the old plan
        old_plan = get_element_by_id(cursor, "Plan", plan_id)
        # End the old plan
        renew_date = get_element_by_id(cursor, "Employer", old_plan["EmployerID"])["RenewalDate"]
        #set the end date to the last day of the month before the renewal date
        renew_date = datetime.strptime(renew_date, '%Y-%m-%d')
        renew_date.year = datetime.today().year
        end_date = datetime.strptime(renew_date, '%Y-%m-%d')
        old_plan["EndDate"] = end_date
        
        # Create the new plan
        new_plan = old_plan
        new_plan["StartDate"] = renew_date
        new_plan["EndDate"] = None

        #add the new info
        for key in plan_json:
            new_plan[key] = plan_json[key]

        new_plan_id = add_element_by_table_name(cursor, "Plan", new_plan)
        # Move all employees on the old plan to the new plan
        move_employees_to_new_plan(cursor, plan_id, new_plan_id)
        return new_plan_id
    except Exception as e:
        raise ValueError(f"Modify Plan: " + str(e))
    
def move_employees_to_new_plan(cursor, old_plan_id, new_plan_id):
    try:
        # Get all employees on the old plan
        employees = get_employees_on_plan(cursor, old_plan_id)

        old_plan = get_element_by_id(cursor, "Plan", old_plan_id)

        new_plan = get_element_by_id(cursor, "Plan", new_plan_id)
        # Move each employee to the new plan
        for employee in employees:
            # End the old plan

            employee_plan_id = employee["EmployeePlanID"]
            employee_plan = get_element_by_id(cursor, "EmployeePlan", employee_plan_id)
            employee_plan["EndDate"] = old_plan["EndDate"] if old_plan["EndDate"] else new_plan["StartDate"]
            employee_plan["InformEndDate"] = old_plan["EndDate"] if old_plan["EndDate"] else new_plan["StartDate"]
            change_element_by_table_name(cursor, "EmployeePlan", employee_plan_id, employee_plan)
            # Create a new plan for the employee
            new_employee_plan = {
                "EmployeeID": employee["EmployeeID"],
                "PlanID": new_plan_id,
                "StartDate": new_plan["StartDate"],
                "InformStartDate": new_plan["StartDate"],
                "EndDate": None
            }
            add_element_by_table_name(cursor, "EmployeePlan", new_employee_plan)
    except Exception as e:
        raise ValueError(f"Move Employees to New Plan: " + str(e))
    
def get_employees_on_plan(cursor, plan_id):
    try:
        return get_active_depfree(cursor, "EmployeePlan", plan_id, "EndDate", "PlanID")
    except Exception as e:
        raise ValueError(f"Get Employees on Plan: " + str(e))
    
def end_plan(cursor, plan_id):
    employer_id = (get_element_by_id(cursor, "Plan", plan_id)["EmployerID"])
    renew_date = get_element_by_id(cursor, "Employer", employer_id)["RenewalDate"]
    #set the end date to the last day of the month before the renewal date
    renew_date = datetime.strptime(renew_date, '%Y-%m-%d')
    renew_date.year = datetime.today().year
    end_date = renew_date
    try:
        change_element_by_table_name(cursor, "Plan", plan_id, {"EndDate": end_date, "InformEndDate": end_date})
        #end all the employee plans
        employee_plans = get_active_depfree(cursor, "EmployeePlan", plan_id, "EndDate", "PlanID")
        for employee_plan in employee_plans:
            change_element_by_table_name(cursor, "EmployeePlan", employee_plan["EmployeePlanID"], {"EndDate": end_date, "InformEndDate": end_date})
    except Exception as e:
        raise ValueError(f"End Plan: " + str(e))

    
### Employee Functions ###

def get_carrier_id(cursor, carrier_name, employer_id):
    get_carrier_query = "SELECT CarrierID FROM Carrier WHERE CarrierName = %s AND EmployerID = %s"
    cursor.execute(get_carrier_query, (carrier_name, employer_id))
    carrier = cursor.fetchall()
    if carrier:
        return carrier[0][0]
    raise ValueError(f"Carrier with name {carrier_name} and employer ID {employer_id} does not exist.")

def get_tier_id(cursor: MySQLCursor, tier_name, dob, employer_id, year=None):
    if not (tier_name == None or tier_name == ""):
        get_tier_query = "SELECT TierID FROM Tier WHERE TierName = %s AND EmployerID = %s"
        cursor.execute(get_tier_query, (tier_name, employer_id))
    else:
        try:
            get_tier_query = "SELECT TierID FROM Tier WHERE %s BETWEEN MinAge AND MaxAge AND EmployerID = %s"
            if not year:
                year = datetime.today().year
            cursor.execute(get_tier_query, (calculate_age(employer_id, dob, year, cursor), employer_id))
        except Exception as e:
            raise ValueError(f"Get TierID by date: " + str(e))
    
    tier = cursor.fetchall()
    if tier:
        return tier[0][0]
    raise ValueError(f"Tier with name {tier_name} and employer ID {employer_id} does not exist.")



def calculate_age(employer_id, dob, year, cursor):
    try:
        #Ages are only updated on the renewal date
        query = f"SELECT RenewalDate FROM Employer WHERE EmployerID = {employer_id}"
        cursor.execute(query)
        renewal_date = cursor.fetchall()[0][0]
        #make sure dob is date
        try:
            if isinstance(dob, str) and (not isinstance(dob, date) or not isinstance(dob, datetime)):
                dob = (datetime.strptime(str(dob).split(" ")[0], '%Y-%m-%d')).date()
            if isinstance(dob, datetime):
                dob = dob.date()
            if not isinstance(dob, date):
                raise ValueError("DOB is not a date")
        except Exception as e:
            raise ValueError(f"Check DOB: " + str(e))
        try:
            if not isinstance(renewal_date, date) and not isinstance(renewal_date, datetime):
                renewal_date = (datetime.strptime(renewal_date.split(" ")[0], '%Y-%m-%d')).date()
        except Exception as e:
            raise ValueError(f"Check Renewal Date: " + str(e))
        #renewal_date = datetime.sy(int(year), renewal_date.month, 1).date()
        try:
            age = year - dob.year - ((renewal_date.month, renewal_date.day) < (dob.month, dob.day))
        except Exception as e:
            raise ValueError(f"Check Calculate Age: " + str(e))
        return age
    except Exception as e:
        raise ValueError(f"Calculate Age: " + str(e))
    
def terminate_employee(cursor, employee_id, end_date=None, inform_end_date=None):
    try:
        # Get the employee
        employee = get_element_by_id(cursor, "Employee", employee_id)
        # End the employee
        if not end_date:
            raise ValueError("End Date is required to terminate an employee.")
        employee["EndDate"] = end_date
        employee["InformEndDate"] = inform_end_date if inform_end_date else end_date
        change_element_by_table_name(cursor, "Employee", employee_id, employee)
        #end plan and dependents
        employee_plans = get_active_depfree(cursor, "EmployeePlan", employee_id, "EndDate", "EmployeeID")
        for employee_plan in employee_plans:
            change_element_by_table_name(cursor, "EmployeePlan", employee_plan["EmployeePlanID"], {"EndDate": end_date, "InformEndDate": end_date})
        dependents = get_active_depfree(cursor, "Dependent", employee_id, "EndDate", "EmployeeID")
        for dependent in dependents:
            change_element_by_table_name(cursor, "Dependent", dependent["DependentID"], {"EndDate": end_date, "InformEndDate": end_date})
        return True
    except Exception as e:
        raise ValueError(f"Terminate Employee: " + str(e))

### EmployeePlan Functions ###


def swap_employee_plan(cursor, employeeplan_id, new_plan_id, start_date, inform_start_date, end_date=None, inform_end_date=None):
    # this function will end the old plan and create a new one then move the employee on the old plan to the new one
    try:
        # Get the old plan
        old_employee_plan = get_element_by_id(cursor, "EmployeePlan", employeeplan_id)
        # End the old plan
        if not end_date:
            end_date = datetime.strptime(start_date, '%Y-%m-%d') - timedelta(days=1)
        old_employee_plan["EndDate"] = end_date
        old_employee_plan["InformEndDate"] = inform_end_date if inform_end_date else end_date
        change_element_by_table_name(cursor, "EmployeePlan", employeeplan_id, old_employee_plan)
        # Create the new plan for the employee
        new_employee_plan = {
            "EmployeeID": old_employee_plan["EmployeeID"],
            "PlanID": new_plan_id,
            "StartDate": start_date,
            "InformStartDate": inform_start_date,
            "EndDate": None
        }
        new_employee_plan_id = add_element_by_table_name(cursor, "EmployeePlan", new_employee_plan)
        return new_employee_plan_id
    except Exception as e:
        raise ValueError(f"Swap Employee Plan: " + str(e))


### Employer Functions ###
def add_employer(cursor, employer_json):
    soft_errors, element_id = add_element_by_table_name(cursor, "Employer", employer_json)
    return element_id

def delete_employer(cursor, employer_id):
    try:
        delete_element(cursor, "Employer", employer_id)
        return True
    except Exception as e:
        return False


##### Refactoring #####
def add_element(cursor, table_name, element_json, required_fields, optional_fields):
    # if json is a string, convert it to a dictionary
    if isinstance(element_json, str):
        data_to_add = json.loads(element_json)
    else:
        data_to_add = element_json
    soft_errors = []

    if isinstance(data_to_add, list):
        raise ValueError("Element cannot be a list. Please provide a dictionary!")

    try:
        # Check for missing required fields
        missing_required = [field for field in required_fields if field not in data_to_add]
        if missing_required:
            raise ValueError(f"{table_name} Missing required fields: {', '.join(missing_required)}")
    except ValueError as e:
        raise ValueError(e)
    except Exception as e:
        raise ValueError(f"Check missing required fields: {str(e)}")
    
    try:
        # Identify invalid fields
        valid_fields = required_fields + optional_fields
        subfields = get_table_fields(table_name, "Subtables")
        denormalized_fields = get_table_fields(table_name, "DenormalizedData")
        possible_fields = valid_fields + subfields + denormalized_fields
        invalid_fields = [field for field in data_to_add if field not in possible_fields]

        # Log soft errors for invalid fields
        if invalid_fields:
            soft_errors.append(f"Invalid fields: {', '.join(invalid_fields)}")
    except Exception as e:
        raise ValueError(f"Identify invalid fields: {str(e)}")
    try:
        # Filter data to include only valid fields
        filtered_data = {key: value for key, value in data_to_add.items() if key in valid_fields}

        columns = ", ".join(filtered_data.keys())
        placeholders = ", ".join(["%s"] * len(filtered_data))
        values = tuple(filtered_data.values())
    except Exception as e:
        raise ValueError(f"Filter data: {str(e)}")
    
    try:
        query = f"INSERT INTO {str(table_name)} ({str(columns)}) VALUES ({str(placeholders)})"
        cursor.execute(query, values)
    except Exception as e:
        try:
            #try removing the id and trying again
            del filtered_data[table_name + "ID"]
            columns = ", ".join(filtered_data.keys())
            placeholders = ", ".join(["%s"] * len(filtered_data))
            values = tuple(filtered_data.values())
            query = f"INSERT INTO {str(table_name)} ({str(columns)}) VALUES ({str(placeholders)})"
            cursor.execute(query, values)
        except Exception as e:
            raise ValueError(f"Insert into {table_name}: {str(e)} Query: {query} FilteredData: {filtered_data}")
        
    try:
        # Retrieve the ID of the newly inserted row
        new_id = cursor.lastrowid
    except Exception as e:
        raise ValueError(f"Select last insert ID: {str(e)}")
    if(new_id == 0 or new_id == None):
        raise ValueError("Error inserting new element no value")
    if not isinstance(new_id, int):
        raise ValueError("Error inserting new element not int")
    
    return new_id, soft_errors

def route_add_element(table_name, element_json):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        soft_errors, new_id = add_element_by_table_name(cursor, table_name, element_json)
        connection.commit()
        cursor.close()
        response = {"status": "success", "new_id": new_id}
        if soft_errors:
            response["warnings"] = soft_errors
        return jsonify(response), 201
    except ValueError as ve:
        # raise ValueError(ve)
        return jsonify({"Error": str(ve)}), 400
    except Exception as e:
        return jsonify({"Error": str(e)}), 500
    
def change_element(cursor, table_name, element_id, element_json, required_fields, optional_fields):
    data_to_change = json.loads(element_json)
    soft_errors = []

    # check to see if the element exists
    cursor.execute(f"SELECT * FROM {table_name} WHERE {table_name}ID = %s", (element_id,))
    if not cursor.fetchall():
        raise ValueError("Element does not exist")

    # Identify invalid fields
    valid_fields = required_fields + optional_fields
    invalid_fields = [field for field in data_to_change if field not in valid_fields]

    # Log soft errors for invalid fields
    if invalid_fields:
        soft_errors.append(f"Invalid fields: {', '.join(invalid_fields)}")
    
    # Filter data to include only valid fields
    filtered_data = {key: value for key, value in data_to_change.items() if key in valid_fields}

    update_fields = ", ".join([f"{key} = %s" for key in filtered_data])
    update_values = tuple(filtered_data.values())

    query = f"UPDATE {table_name} SET {update_fields} WHERE {table_name}ID = %s"
    cursor.execute(query, update_values + (element_id,))
    
    return soft_errors, element_id

def route_change_element(table_name, element_id, element_json):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        element_id, soft_errors = change_element_by_table_name(cursor, table_name, element_id, element_json)
        connection.commit()
        cursor.close()
        response = {"status": "success"}
        if soft_errors:
            response["warnings"] = soft_errors
        return jsonify(response), 200
    except ValueError as ve:
        return jsonify({"Error": str(ve)}), 400
    except Exception as e:
        return jsonify({"Error": str(e)}), 500
    
def delete_element(cursor, table_name, element_id):
    soft_errors = []
    # check to see if the element exists
    cursor.execute(f"SELECT * FROM {table_name} WHERE {table_name}ID = %s", (element_id,))
    if not cursor.fetchall():
        soft_errors.append("Element does not exist")
        return soft_errors, element_id
    query = f"DELETE FROM {table_name} WHERE {table_name}ID = %s"
    cursor.execute(query, (element_id,))
    return soft_errors, element_id
    
def route_delete_element(element_id, table_name):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        soft_errors, element_id = delete_element(cursor, table_name, element_id)
        connection.commit()
        cursor.close()
        response = {"status": "success"}
        if soft_errors:
            response["warnings"] = soft_errors
        return jsonify(response), 200
    except ValueError as ve:
        return jsonify({"Error": str(ve)}), 400
    except Exception as e:
        return jsonify({"Error": str(e)}), 500
    

def get_element_by_id(cursor, table_name, element_id):
    try:
        cursor.execute(f"SELECT * FROM {table_name} WHERE {table_name}ID = %s", (element_id,))
        column_names = [desc[0] for desc in cursor.description]
        element = cursor.fetchone()
        if not element:
            raise ValueError(f"{table_name} with ID {element_id} does not exist.")
        
        element_dict = dict(zip(column_names, element))
        return element_dict
    except Exception as e:
        raise ValueError(f"Get Element by ID: " + str(e))
    
def route_get_element_by_id(table_name, element_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        element = get_element_by_id(cursor, table_name, element_id)
        cursor.close()
        connection.close()
        return jsonify(element)
    except ValueError as ve:
        return jsonify({"Error": str(ve)}), 400
    except Exception as e:
        return jsonify({"Error": str(e)}), 500



######### Generate Report #########
def execute_query(cursor: MySQLCursor, query):
    try:
        cursor.execute(query)
        return cursor.fetchall()
    except Exception as e:
        raise Exception(f"Error Executing Queary: {query} Error: " + str(e))
    
def get_only_active_on_date(cursor, table_name, employer_id, date, Identifyer="EmployerID"):
    try:
        employees = execute_query(cursor, f"SELECT {table_name}ID FROM {table_name} WHERE {Identifyer}={employer_id} AND InformStartDate <= '{date}' AND (InformEndDate >= '{date}' OR InformEndDate IS NULL)")
        if len(employees) > 1:
            employees = execute_query(cursor, f"SELECT {table_name}ID FROM {table_name} WHERE {Identifyer}={employer_id} AND InformStartDate <= '{date}' AND (InformEndDate > '{date}' OR InformEndDate IS NULL)")
        if len(employees) > 1:
            raise ValueError(f"Multiple active {table_name} on {date}")
        return employees[0][0]
    except Exception as e:
        raise ValueError(f"Get Only Active on Date: " + str(e))
    
def get_employeeplan_on_date(cursor, employee_id, date):
    try:
        employeeplan_id = get_only_active_on_date(cursor, "EmployeePlan", employee_id, date, "EmployeeID")
        return employeeplan_id
    except Exception as e:
        raise ValueError(f"Get EmployeePlan on Date: " + str(e))
    
def select_planid_from_employeeplan(cursor, employeeplan_id):
    try:
        query = f"SELECT PlanID FROM EmployeePlan WHERE EmployeePlanID = {employeeplan_id}"
        plan_id = execute_query(cursor, query)[0][0]
        return plan_id
    except Exception as e:
        raise ValueError(f"Select PlanID from EmployeePlan: " + str(e))
    
def get_only_active_plan_on_date(cursor, carrierid, tierid, date):
    try:
        query = f"SELECT PlanID FROM Plan WHERE CarrierID = {carrierid} AND TierID = {tierid} AND StartDate <= '{date}' AND (EndDate >= '{date}' OR EndDate IS NULL)"
        plans = execute_query(cursor, query)
        if len(plans) < 1:
            raise ValueError(f"No active plans on {date}")
        if len(plans) > 1:
            plans = execute_query(cursor, f"SELECT PlanID FROM Plan WHERE CarrierID = {carrierid} AND TierID = {tierid} AND StartDate <= '{date}' AND (EndDate > '{date}' OR EndDate IS NULL)")
        if len(plans) > 1:
            raise ValueError(f"Multiple active plans on {date}")
        plan_id = plans[0][0]
        return plan_id
    except Exception as e:
        raise ValueError(f"Get Only Active Plan on Date: " + str(e))
    

    
def get_plan_for_employee(cursor, employee_id, current_date=None):
    try:
        if current_date is None:
            current_date = datetime.now().strftime('%Y-%m-%d')
        try:
            employeeplan_id = get_employeeplan_on_date(cursor, employee_id, current_date)
            plan_id = select_planid_from_employeeplan(cursor, employeeplan_id)
        except Exception as e:
            raise ValueError(f"Find EmployePlan for Employee: " + str(e))
        if not plan_id:
            raise ValueError(f"Employee {employee_id} does not have a plan on {date}")
        employer_id = get_employer_id_from_employee(cursor, employee_id)
        try:
            if(get_employer_tier_structure(cursor, employer_id).lower().find("age") != -1):
                query = f"SELECT DOB FROM Employee WHERE EmployeeID = {employee_id}"
                dob = execute_query(cursor, query)[0][0]
                # query = f"SELECT RenewalDate FROM Employer WHERE EmployerID = {employer_id}"
                # renewal_date = execute_query(cursor, query)[0][0]
                # age = calculate_age(employer_id, dob, renewal_date.year, cursor)
                # query = f"SELECT TierID FROM Tier WHERE MinAge <= {age} AND MaxAge >= {age} AND EmployerID = {employer_id}"
                # tier_id = execute_query(cursor, query)[0][0]
                tier_id = get_tier_id(cursor, None, dob, employer_id, current_date.year)
                query = f"SELECT CarrierID FROM Plan WHERE PlanID = {plan_id}"
                carrier_id = execute_query(cursor, query)[0][0]
                plan_id = get_only_active_plan_on_date(cursor, carrier_id, tier_id, current_date)
        except Exception as e:
            raise ValueError(f"Geting AgeBanded: " + str(e))
        return plan_id
    except Exception as e:
        raise ValueError(f"Get Plan for Employee: " + str(e))
        
def get_plan_for_dependent(cursor, dependent_id, Date=None):
    try:
        if Date is None:
            Date = datetime.now().strftime('%Y-%m-%d')
        query = f"SELECT PlanID FROM EmployeePlan WHERE EmployeeID = (SELECT EmployeeID FROM Dependent WHERE DependentID = {dependent_id}) AND InformStartDate <= '{Date}' AND (InformEndDate IS NULL OR InformEndDate >= '{Date}')"
        plan_id = execute_query(cursor, query)[0][0]
        if not plan_id:
            raise ValueError(f"Dependent {dependent_id} does not have a plan on {Date}")
        query = f"SELECT EmployeeID FROM Dependent WHERE DependentID = {dependent_id}"
        employee_id = execute_query(cursor, query)[0][0]
        employer_id = get_employer_id_from_employee(cursor, employee_id)
        query = f"SELECT DOB FROM Dependent WHERE DependentID = {dependent_id}"
        dob = execute_query(cursor, query)[0][0]
        query = f"SELECT RenewalDate FROM Employer WHERE EmployerID = {employer_id}"
        renewal_date = execute_query(cursor, query)[0][0]
        age = calculate_age(employer_id, dob, renewal_date.year, cursor)
        query = f"SELECT TierID FROM Tier WHERE MinAge <= {age} AND MaxAge >= {age} AND EmployerID = {employer_id}"
        tier_id = execute_query(cursor, query)[0][0]
        query = f"SELECT CarrierID FROM Plan WHERE PlanID = {plan_id}"
        carrier_id = execute_query(cursor, query)[0][0]
        plan_id = get_only_active_plan_on_date(cursor, carrier_id, tier_id, Date)
        return plan_id
    except Exception as e:
        raise ValueError(f"Get Plan for Dependent: " + str(e))


def get_dependent_fund_info(cursor, dependent_id, current_date, plan_id):
    if not isinstance(dependent_id, int):
        dependent_id = dependent_id[0]      
    plan_id = get_plan_for_dependent(cursor, dependent_id, current_date)
    relationship = execute_query(cursor, f"SELECT Relationship FROM Dependent WHERE DependentID = {dependent_id}")[0][0]
    #if Spouse to GrenzFeeS, if Child to GrenzFeeC else raise an error
    fee_type = "GrenzFeeS" if relationship == "Spouse" else "GrenzFeeC" if relationship == "Child" else None
    if fee_type is None:
        raise ValueError("Invalid Relationship")
    query = f"SELECT TierID, FundingAmount, {fee_type} FROM Plan WHERE PlanID = {plan_id}"
    tier_id, fund_amount, g_fee = execute_query(cursor, query)[0]
    dep_funding_amount = fund_amount 
    dep_grenz_fee = g_fee
    dep_tier = execute_query(cursor, f"SELECT TierName FROM Tier WHERE TierID = {tier_id}")[0][0]
    return dep_funding_amount, dep_grenz_fee, dep_tier

def process_dependent(cursor, dependent_id, current_date, plan_id, employee_id):
    def fetch_and_process_dependent_info(start_date, inform_start_date, dependent_id, process_range=True):
        if not isinstance(dependent_id, int):
            dependent_id = dependent_id[0]
        query = f"SELECT DependentName, Relationship FROM Dependent WHERE DependentID = {dependent_id}"
        dep_name, relationship = execute_query(cursor, query)[0]
        dep_funding_amount, dep_grenz_fee = 0, 0
        if process_range:
            for back_date in generate_month_range(start_date, inform_start_date):
                dep_f_amount, dep_g_fee, dep_tier = get_dependent_fund_info(cursor, dependent_id, back_date, plan_id)
                dep_funding_amount += dep_f_amount
                dep_grenz_fee += dep_g_fee
        else:
            dep_f_amount, dep_g_fee, dep_tier = get_dependent_fund_info(cursor, dependent_id, current_date, plan_id)
            dep_funding_amount += dep_f_amount
            dep_grenz_fee += dep_g_fee
        return {"DependentID": dependent_id, "DependentName": dep_name, "Relationship": relationship, "FundingAmount": dep_funding_amount, "GrenzFee": dep_grenz_fee, "Tier": dep_tier}
    
    if not isinstance(dependent_id, int):
            dependent_id = dependent_id[0]
    query = f"SELECT StartDate, InformStartDate, EndDate, InformEndDate FROM Dependent WHERE DependentID = {dependent_id}"
    start_date, inform_start_date, end_date, inform_end_date = execute_query(cursor, query)[0]
    
    current_month_start = datetime(current_date.year, current_date.month, 1).date()
    dep_fund_amount, dep_grenz_fee = 0, 0
    dep_info = None
    
    if inform_start_date == current_month_start:
        dep_info = fetch_and_process_dependent_info(start_date, inform_start_date, dependent_id)
        dep_fund_amount += dep_info['FundingAmount']
        dep_grenz_fee += dep_info['GrenzFee']
    
    if inform_end_date == current_month_start:
        dep_info = fetch_and_process_dependent_info(inform_end_date, end_date, dependent_id)
        dep_fund_amount -= dep_info['FundingAmount']
        dep_grenz_fee -= dep_info['GrenzFee']
        dep_info = fetch_and_process_dependent_info(current_month_start, current_month_start, dependent_id, False)
        dep_fund_amount += dep_info['FundingAmount']
        dep_grenz_fee += dep_info['GrenzFee']
    if inform_start_date >= current_month_start or inform_end_date <= current_month_start:
        if dep_info is not None:
            dep_info['FundingAmount'] = dep_fund_amount
            dep_info['GrenzFee'] = dep_grenz_fee
            return dep_info
        return None
    dep_info = fetch_and_process_dependent_info(current_month_start, current_month_start, dependent_id, False)
    return dep_info
    

    


def get_employer_id (cursor, employer_name): 
    try:
        return execute_query(cursor, f"SELECT EmployerID FROM Employer WHERE EmployerName = \"{employer_name}\"")[0][0]
    except Exception as e:
        raise ValueError(f"Finding employer id: {e}")
    
def get_employer_id_from_employee (cursor, employee_id): 
    try:
        return execute_query(cursor, f"SELECT EmployerID FROM Employee WHERE EmployeeID = {employee_id}")[0][0]
    except Exception as e:
        raise ValueError(f"Finding employer id: {e}")

def get_employer_tier_structure (cursor, employer_id) -> str: 
    try:
        return execute_query(cursor, f"SELECT TierStructure FROM Employer WHERE EmployerID = {employer_id}")[0][0]
    except Exception as e:
        raise ValueError(f"Finding employer tier structure: {e}")

def add_data_test(df, notes, employee_name, plan, tier, funding_amount):
    new_row = {"Notes": notes, "Employee Name": employee_name, "Plan": plan, "Tier": tier, "Funding Amount": funding_amount}
    return df._append(new_row, ignore_index=True)

def generate_month_range(start, end):
    # Convert start and end to date objects if they aren't already
    if isinstance(start, datetime):
        start = start.date()
    if isinstance(end, datetime):
        end = end.date()
    current = start
    while current <= end:
        yield date(current.year, current.month, 1)
        current += timedelta(days=calendar.monthrange(current.year, current.month)[1])
        current = date(current.year, current.month, 1)

def update_dependents(dependents, new_entries):
    try:
        if (new_entries == None):
            return dependents
        for entry in new_entries:
            # make sure it is the correct type
            if entry == None:
                continue
            if not isinstance(entry, dict):
                raise ValueError("Entry must be a dictionary")
            
            inlist = False
            try:
                dep_id = entry['DependentID']
                funding_amount = entry['FundingAmount']
                grenz_fee = entry['GrenzFee']
            except Exception as e:
                raise ValueError(f"Error Geting Dependent Info: " + str(e))
            for dependent in dependents:
                if dependent['DependentID'] == dep_id:
                    dependent['FundingAmount'] = funding_amount + dependent['FundingAmount']
                    dependent['GrenzFee'] = grenz_fee + dependent['GrenzFee']
                    inlist = True
                    break
            if not inlist: 
                try:
                    dependents.append(entry)
                except Exception as e:
                    raise ValueError(f"Error Appending Entry: " + str(e))
        return dependents
    except Exception as e:
        raise ValueError(f"Update Dependents: " + str(e))

def flip_funding_amounts(dependents):
    try:
        for dependent in dependents:
            if dependent == None:
                continue
            dependent['FundingAmount'] = -dependent['FundingAmount']
            dependent['GrenzFee'] = -dependent['GrenzFee']
        return dependents
    except Exception as e:
        raise ValueError(f"Flip Funding Amounts: " + str(e))

def calculate_funding_amount_normal(cursor, date, plan_id, employee_id=None):
    query = f"SELECT CarrierID, TierID, FundingAmount, GrenzFee FROM Plan WHERE PlanID = {plan_id}"
    plan_info = execute_query(cursor, query)
    if not plan_info:
        raise ValueError (f"Plan {plan_id} info not found")


    carrier_id, tier_id, funding_amount, grenz_fee = plan_info[0]
    
    carrier_name = execute_query(cursor, f"SELECT CarrierName FROM Carrier WHERE CarrierID = {carrier_id}")[0][0]
    tier_name = execute_query(cursor, f"SELECT TierName FROM Tier WHERE TierID = {tier_id}")[0][0]

    return funding_amount, grenz_fee, carrier_name, tier_name, []

def calculate_funding_amount_age_banded(cursor, current_date, plan_id=None, employee_id=None):
    funding_amount = 0
    grenz_fee = 0
    dependents = []
    try: 
        plan_id = get_plan_for_employee(cursor, employee_id, current_date)
        query = f"SELECT CarrierID, TierID, FundingAmount, GrenzFee FROM Plan WHERE PlanID = {plan_id}"
        try:
            carrier_id, tier_id, funding_amount, grenz_fee = execute_query(cursor, query)[0]
        except Exception as e:
            raise ValueError(f"Error getting info from Plan queary: {e}")
    except Exception as e:
        raise ValueError(f"Error getting plan info: {e}")
    try:
        tier = execute_query(cursor, f"SELECT TierName FROM Tier WHERE TierID = {tier_id}")[0][0]
    except Exception as e:
        raise ValueError(f"Error getting tier: {e}")
    try:
        carrier = execute_query(cursor, f"SELECT CarrierName FROM Carrier WHERE CarrierID = {carrier_id}")[0][0]
    except Exception as e:
        raise ValueError(f"Error getting carrier: {e}")
    # Get the dependents
    try:
        query = f"SELECT DependentID FROM Dependent WHERE EmployeeID = {employee_id}"
        dependent_ids = execute_query(cursor, query)
    except Exception as e:
        raise ValueError(f"Error getting dependent ids: {e}")
    try:
        for dependent_id in dependent_ids:
            try:
                dependents.append(process_dependent(cursor, dependent_id, current_date, plan_id, employee_id))
            except Exception as e:
                raise ValueError(f"Error processing dependent: {e}")
    except Exception as e:
        raise Exception(f"Error getting dependents: {e}")
    
    return funding_amount, grenz_fee, carrier, tier, dependents

def calculate_funding_amount_composite(cursor, date, plan_id=None, employee_id=None):
    if employee_id is None:
        raise ValueError("No EmployeeID provided")
    plan_id = get_plan_for_employee(cursor, employee_id, date)
    query = f"SELECT CarrierID, TierID, FundingAmount, GrenzFee FROM Plan WHERE PlanID = {plan_id}"
    carrier_id, tier_id, funding_amount, grenz_fee = execute_query(cursor, query)[0]

    tier = execute_query(cursor, f"SELECT TierName FROM Tier WHERE TierID = {tier_id}")[0][0]
    carrier = execute_query(cursor, f"SELECT CarrierName FROM Carrier WHERE CarrierID = {carrier_id}")[0][0]

    return funding_amount, grenz_fee, carrier, tier, []

def get_format_normal(employer_info=None):
    columns = ["Notes", "Employee Name"]
    if employer_info:
        employer_id, tier_structure, uses_gl_code, uses_division, uses_location, uses_title = employer_info
        if tier_structure.casefold().find("age"):
            columns.append("DOB")
        if uses_gl_code:
            columns.append("GL Code")
        if uses_division:
            columns.append("Division")
        if uses_location:
            columns.append("Location")
        if uses_title:
            columns.append("Title")
    columns += ["Carrier", "Tier", "Funding Amount", "Admin Fee", "Total Amount"]
    return add_data_normal, columns



def add_data_normal(df, notes, employee_name, plan, tier, funding_amount, grenz_fee, total, gl_code = None, division=None, location=None, title=None, dependents=[], DOB = None):
    new_row = {"Notes": notes, "Employee Name": employee_name, "Carrier": plan, "Tier": tier, "Funding Amount": funding_amount, "Admin Fee": grenz_fee, "Total Amount": total}
    if gl_code:
        new_row["GL Code"] = gl_code
    if division:
        new_row["Division"] = division
    if location:
        new_row["Location"] = location
    if title:
        new_row["Title"] = title
    if DOB:
        new_row["DOB"] = DOB
    df = df._append(new_row, ignore_index=True)
    return df

def add_data_age_banded(df, notes, employee_name, plan, tier, funding_amount, grenz_fee, total, gl_code = None, division=None, location=None, title=None, dependents=[], DOB = None) -> pd.DataFrame:
    new_df = df
    new_row = {"Notes": notes, "Employee Name": employee_name, "Carrier": plan, "Tier": tier, "Funding Amount": funding_amount, "Admin Fee": grenz_fee, "Total Amount": total}
    if gl_code:
        new_row["GL Code"] = gl_code
    if division:
        new_row["Division"] = division
    if location:
        new_row["Location"] = location
    if title:
        new_row["Title"] = title
    if DOB: 
        new_row["DOB"] = DOB

    new_df = new_df._append(new_row, ignore_index=True)
    new_row = {}
    for dependent in dependents:
        new_row["Notes"] = "Dependent:"
        new_row["Employee Name"] = employee_name
        new_row["Dependent Name"] = dependent["DependentName"]
        new_row["Dependent Tier"] = dependent["Tier"]
        new_row["Dependent Relationship"] = dependent["Relationship"]
        new_row["Funding Amount"] = dependent["FundingAmount"]
        new_row["Admin Fee"] = dependent["GrenzFee"]
        new_row["Total Amount"] = dependent["FundingAmount"] + dependent["GrenzFee"]
        new_df = new_df._append(new_row, ignore_index=True)
    return new_df

def generate_report(connection, employer_name, Date, get_format=get_format_normal):
    if not connection:
        raise ValueError("No connection to the database")

    cursor = connection.cursor()
    try:
        current_month = Date.month
        current_year = Date.year

        employer_info = execute_query(cursor, f"SELECT EmployerID, TierStructure, UsesGlCode, UsesDivision, UsesLocation, UsesTitle FROM Employer WHERE EmployerName = '{employer_name}'")[0]
        if not employer_info:
            raise ValueError(f"Employer {employer_name} not found")
        
        add_data, columns = get_format(employer_info)
    except Exception as e:
        raise ValueError(f"Error getting employer info: {e}")

    try:
        employer_id, tier_structure, uses_gl_code, uses_division, uses_location, uses_title = employer_info
        calculate_funding_amount = calculate_funding_amount_normal
        if (tier_structure == "AgeBanded"):
            calculate_funding_amount = calculate_funding_amount_age_banded
            add_data = add_data_age_banded
        if (tier_structure == "AgeBandedComposite"):
            calculate_funding_amount = calculate_funding_amount_composite  
    except Exception as e:
        raise ValueError(f"Error setting up funding calculation: {e}")
    
    df = pd.DataFrame(columns=columns)
    
    
    
    employees = execute_query(cursor, f"SELECT EmployeeID, EmployeeFullName, StartDate, InformStartDate, EndDate, InformEndDate FROM Employee WHERE EmployerID = {employer_id} AND InformStartDate <= '{Date}' AND (InformEndDate >= '{Date}' OR InformEndDate IS NULL)")

    if not employees:
        raise ValueError(f"No employees found for {employer_name} on {Date}")
        
    try:
        for employee in employees:
            employee_id, employee_name, join_date, join_inform_date, term_date, term_inform_date = employee
            notes = []
            funding_amount = 0
            grenz_fee = 0
            carrier_names = []
            tier_names = []
            dependents = []
            #raise ValueError(f"We made it to employee {employee_name}")
            try:
                employee_plans = execute_query(cursor, f"SELECT PlanID, StartDate, InformStartDate, EndDate, InformEndDate FROM EmployeePlan WHERE EmployeeID = {employee_id} AND InformStartDate <= '{Date}' ")
            except Exception as e:
                raise ValueError(f"Error getting employee plans for {employee_name}: {e}")
            if not employee_plans:
                raise ValueError(f"No plans found for {employee_name} on {Date}")
                continue
            try:
                try:
                    if not isinstance(term_inform_date, date):
                        if term_inform_date != None:
                            term_inform_date = datetime.strptime(str(term_inform_date), "%Y-%m-%d").date()
                except Exception as e:
                    raise ValueError(f"Error getting term inform date for {employee_name}: {e}")
                try:
                    if term_date and term_inform_date == datetime(current_year, current_month, 1).date():
                        notes.append("Terminated " + str(current_month) + "/" +  str(current_year))
                        for back_date in generate_month_range(term_date, term_inform_date):
                            if(back_date == datetime(current_year, current_month, 1).date()):
                                continue
                            try:
                                plan_id = get_plan_for_employee(cursor, employee_id, back_date)
                            except Exception as e:
                                raise ValueError(f"Error getting plan for {employee_name}: {e}")
                            if not plan_id:
                                raise ValueError(f"Backedate, No plan found for {employee_name} on {back_date}")
                            try:
                                f_amount, g_fee, carrier_name, tier_name, new_dependents = calculate_funding_amount(cursor, back_date, plan_id, employee_id)
                            except Exception as e:
                                raise ValueError(f"Error calculating funding amount for {employee_name}: {e}")
                            funding_amount -= f_amount
                            grenz_fee -= g_fee
                            carrier_names.append(carrier_name)
                            tier_names.append(tier_name)
                            new_dependents = flip_funding_amounts(new_dependents)
                            dependents = update_dependents(dependents, new_dependents)
                except Exception as e:
                    raise ValueError(f"Error handling if statement term date for {employee_name}: {e}")
            except Exception as e:
                raise ValueError(f"Error handleing term date for {employee_name}: {e}")
            #raise Exception("Join Test Join date:" + str(join_date) + " Join inform Date: " + str(join_inform_date) + " CurrentDate: " + str(current_date))
            date_format = "%Y-%m-%d"
            join_inform_date = datetime.strptime(str(join_inform_date), date_format)
            join_date = datetime.strptime(str(join_date), date_format)
            try:
                if join_date and join_inform_date.date() == datetime(current_year, current_month, 1).date():
                    notes.append("Joined " + str(current_month) + "/" +  str(current_year))
                    #raise ValueError("Join Worked")
                    print(f"{employee_name} joined")
                    for back_date in generate_month_range(join_date, join_inform_date):
                        plan_id = get_plan_for_employee(cursor, employee_id, back_date)
                        f_amount, g_fee, carrier_name, tier_name, new_dependents = calculate_funding_amount(cursor, back_date, plan_id, employee_id)
                        funding_amount += f_amount
                        grenz_fee += g_fee
                        carrier_names.append(carrier_name)
                        tier_names.append(tier_name)
                        dependents = update_dependents(dependents, new_dependents)
            except Exception as e:
                raise ValueError(f"Error handeling join inform date for {employee_name}: {e}")
            try:
                for plan in employee_plans:
                    plan_id, start_date, inform_start_date, end_date, inform_end_date = plan
                    if end_date and inform_end_date < date(current_year, current_month, 1):
                        continue
                    if inform_start_date == date(current_year, current_month, 1):
                        notes.append("Started Plan " + start_date.month() + "/" +  start_date.year())
                        for back_date in generate_month_range(start_date, inform_start_date):
                            f_amount, g_fee, carrier_name, tier_name, new_dependents = calculate_funding_amount(cursor, back_date, plan_id, employee_id)
                            funding_amount += f_amount
                            grenz_fee += g_fee
                            carrier_names.append(carrier_name)
                            tier_names.append(tier_name)
                            dependents = update_dependents(dependents, new_dependents)

                    if inform_end_date == date(current_year, current_month, 1):
                        notes.append("Ended Plan " + end_date.month() + "/" +  end_date.year())
                        for back_date in generate_month_range(end_date, inform_end_date):
                            if(back_date == datetime(current_year, current_month, 1).date()):
                                continue
                            #Update the plan_id incase the end date is less then the start date 
                            plan_id = get_plan_for_employee(cursor, employee_id, back_date)
                            f_amount, g_fee, carrier_name, tier_name, new_dependents = calculate_funding_amount(cursor, back_date, plan_id, employee_id)
                            funding_amount -= f_amount
                            grenz_fee -= g_fee
                            carrier_names.append(carrier_name)
                            tier_names.append(tier_name)
                            dependents = update_dependents(dependents, new_dependents)
            except Exception as e:
                raise ValueError(f"Error handling plans for {employee_name}: {e}")
                
            try:
                if not carrier_names or not tier_names:
                    try:
                        plan_id = get_plan_for_employee(cursor, employee_id, datetime(current_year, current_month, 1).date())
                    except Exception as e:
                        raise ValueError(f"Error getting plan for {employee_name}: {e}")
                    if not plan_id:
                            raise ValueError(f"No plan found for {employee_name} on {back_date}")
                    try:
                        f_amount, g_fee, carrier_name, tier_name, new_dependents = calculate_funding_amount(cursor, datetime(current_year, current_month, 1).date(), plan_id, employee_id)
                    except Exception as e:
                        raise ValueError(f"Error calculating funding amount for {employee_name}: {e}")
                    try:
                        funding_amount += f_amount
                        grenz_fee += g_fee
                        carrier_names.append(carrier_name)
                        tier_names.append(tier_name)
                        dependents = update_dependents(dependents, new_dependents)
                    except Exception as e:
                        raise ValueError(f"Error summing data for {employee_name}: {e}")
            except Exception as e:
                raise ValueError(f"Error getting defult funding amount for {employee_name}: {e}")
            try:
                carrier_name = "/ ".join(set(carrier_names))
                tier_name = "/ ".join(set(tier_names))
                try:
                    empDOB = execute_query(cursor, f"SELECT DOB FROM Employee WHERE EmployeeID = {employee_id}")[0][0]
                    # format dob
                    empDOB = empDOB.strftime("%m/%d/%Y")
                except Exception as e:
                    empDOB = None

                if(uses_gl_code):
                    gl_code = execute_query(cursor, f"SELECT GlCode FROM Employee WHERE EmployeeID = {employee_id}")[0][0]
                else:
                    gl_code = None
                if(uses_division):
                    division = execute_query(cursor, f"SELECT Division FROM Employee WHERE EmployeeID = {employee_id}")[0][0]
                else:
                    division = None
                if(uses_location):
                    location = execute_query(cursor, f"SELECT Location FROM Employee WHERE EmployeeID = {employee_id}")[0][0]
                else:
                    location = None
                if(uses_title):
                    title = execute_query(cursor, f"SELECT Title FROM Employee WHERE EmployeeID = {employee_id}")[0][0]
                else:
                    title = None
                try:
                    total = funding_amount + grenz_fee
                    df = add_data(df, str(notes).strip("[]"), employee_name, carrier_name, tier_name, funding_amount, grenz_fee, total, gl_code, division, location, title, dependents, empDOB)
                except Exception as e:
                    raise ValueError(f"Error adding data for {employee_name}: {e}")
            except Exception as e:
                raise ValueError(f"Error managing data for {employee_name}: {e}")
    except Exception as e:
        raise ValueError(f"Error itorating employees: {e}")
    try:
        total_funding = df["Total Amount"].sum()
        total_admin = df["Admin Fee"].sum()
        total_funding_amount = df["Funding Amount"].sum()
        df = df._append({"Notes": "Total:", "Funding Amount": total_funding_amount, "Admin Fee": total_admin, "Total Amount": total_funding}, ignore_index=True)
        filePath = f"{employer_name}_report_{current_year}_{current_month}.xlsx"
    except Exception as e:
        raise ValueError(f"Error calculating totals: {e}")
    try:
        #filePath = "output.xlsx"
        df.to_excel(filePath, index=False, engine='openpyxl')
    except Exception as e:
        raise ValueError(f"Error generating report: {e}")

    cursor.close()
    return filePath


########### Test Data ############
test_json_1 = """{
    "employers": [
        {
            "EmployerName": "Test Employer 1",
            "TierStructure": "4Tiered",
            "UsesGlCode": false,
            "UsesDivision": true,
            "UsesLocation": false,
            "UsesTitle": false,
            "PerferedBillingDate": "2025-02-01",
            "RenewalDate": "2000-01-01",
            "Employees": [
                {
                    "EmployerID": 1,
                    "EmployeeFullName": "John Jones",
                    "EmployeeFirstName": "John",
                    "EmployeeLastName": "Jones",
                    "StartDate": "2000-01-01",
                    "EndDate": null,
                    "InformStartDate": "2020-01-01",
                    "InformEndDate": null,
                    "DOB": "1990-06-25",
                    "CobraStatus": true,
                    "Notes": "This is a sample note.",
                    "GlCode": "GL85327",
                    "Division": "HR",
                    "Location": "Houston",
                    "Title": "Manager",
                    "Dependents": [],
                    "Carrier": "Carrier1",
                    "Tier": "Tier3"
                },
                {
                    "EmployerID": 1,
                    "EmployeeFullName": "Michelle Johnson",
                    "EmployeeFirstName": "Michelle",
                    "EmployeeLastName": "Johnson",
                    "StartDate": "2000-01-01",
                    "EndDate": null,
                    "InformStartDate": "2000-01-01",
                    "InformEndDate": null,
                    "DOB": "1990-06-25",
                    "CobraStatus": true,
                    "Notes": "This is a sample note.",
                    "GlCode": "GL61683",
                    "Division": "Marketing",
                    "Location": "Houston",
                    "Title": "Manager",
                    "Dependents": [],
                    "Carrier": "Carrier2",
                    "Tier": "Tier1"
                },
                {
                    "EmployerID": 1,
                    "EmployeeFullName": "Jane Doe",
                    "EmployeeFirstName": "Jane",
                    "EmployeeLastName": "Doe",
                    "StartDate": "2019-01-01",
                    "EndDate": null,
                    "InformStartDate": "2020-01-01",
                    "InformEndDate": null,
                    "DOB": "1990-06-25",
                    "CobraStatus": false,
                    "Notes": "This is a sample note.",
                    "GlCode": "GL99914",
                    "Division": "Marketing",
                    "Location": "Houston",
                    "Title": "Director",
                    "Dependents": [],
                    "Carrier": "Carrier1",
                    "Tier": "Tier4"
                }
            ],
            "carriers": [
                {
                    "EmployerID": 1,
                    "CarrierName": "Carrier1"
                },
                {
                    "EmployerID": 1,
                    "CarrierName": "Carrier2"
                }
            ],
            "tiers": [
                {
                    "EmployerID": 1,
                    "TierName": "Tier1",
                    "MaxAge": 100,
                    "MinAge": 0
                },
                {
                    "EmployerID": 1,
                    "TierName": "Tier2",
                    "MaxAge": 100,
                    "MinAge": 0
                },
                {
                    "EmployerID": 1,
                    "TierName": "Tier3",
                    "MaxAge": 100,
                    "MinAge": 0
                },
                {
                    "EmployerID": 1,
                    "TierName": "Tier4",
                    "MaxAge": 100,
                    "MinAge": 0
                }
            ],
            "plans": [
                {
                    "EmployerID": 1,
                    "CarrierID": 1,
                    "TierID": 1,
                    "FundingAmount": 26.76,
                    "GrenzFee": 1.06,
                    "GrenzFeeC": 1.2,
                    "GrenzFeeS": 1.56,
                    "CarrierName": "Carrier1",
                    "TierName": "Tier1"
                },
                {
                    "EmployerID": 1,
                    "CarrierID": 1,
                    "TierID": 2,
                    "FundingAmount": 33.2,
                    "GrenzFee": 4.11,
                    "GrenzFeeC": 1.91,
                    "GrenzFeeS": 2.15,
                    "CarrierName": "Carrier1",
                    "TierName": "Tier2"

                },
                {
                    "EmployerID": 1,
                    "CarrierID": 1,
                    "TierID": 3,
                    "FundingAmount": 40.04,
                    "GrenzFee": 3.19,
                    "GrenzFeeC": 0.96,
                    "GrenzFeeS": 1.11,
                    "CarrierName": "Carrier1",
                    "TierName": "Tier3"
                },
                {
                    "EmployerID": 1,
                    "CarrierID": 1,
                    "TierID": 4,
                    "FundingAmount": 28.0,
                    "GrenzFee": 3.26,
                    "GrenzFeeC": 1.35,
                    "GrenzFeeS": 0.75,
                    "CarrierName": "Carrier1",
                    "TierName": "Tier4"
                },
                {
                    "EmployerID": 1,
                    "CarrierID": 2,
                    "TierID": 1,
                    "FundingAmount": 14.88,
                    "GrenzFee": 2.75,
                    "GrenzFeeC": 2.11,
                    "GrenzFeeS": 1.36,
                    "CarrierName": "Carrier2",
                    "TierName": "Tier1"
                },
                {
                    "EmployerID": 1,
                    "CarrierID": 2,
                    "TierID": 2,
                    "FundingAmount": 40.75,
                    "GrenzFee": 3.72,
                    "GrenzFeeC": 2.33,
                    "GrenzFeeS": 1.75,
                    "CarrierName": "Carrier2",
                    "TierName": "Tier2"
                },
                {
                    "EmployerID": 1,
                    "CarrierID": 2,
                    "TierID": 3,
                    "FundingAmount": 29.47,
                    "GrenzFee": 4.61,
                    "GrenzFeeC": 2.05,
                    "GrenzFeeS": 1.13,
                    "CarrierName": "Carrier2",
                    "TierName": "Tier3"
                },
                {
                    "EmployerID": 1,
                    "CarrierID": 2,
                    "TierID": 4,
                    "FundingAmount": 26.77,
                    "GrenzFee": 1.82,
                    "GrenzFeeC": 1.93,
                    "GrenzFeeS": 2.06,
                    "CarrierName": "Carrier2",
                    "TierName": "Tier4"
                }
            ]
        },
        {
            "EmployerID": 2,
            "EmployerName": "Test Employer 2 AgeBanded",
            "TierStructure": "AgeBanded",
            "UsesGlCode": true,
            "UsesDivision": false,
            "UsesLocation": true,
            "UsesTitle": true,
            "PerferedBillingDate": "2025-05-01",
            "RenewalDate": "2000-01-01",
            "Employees": [
                {
                    "EmployeeID": 1,
                    "EmployerID": 1,
                    "EmployeeFullName": "Jane Johnson",
                    "EmployeeFirstName": "Jane",
                    "EmployeeLastName": "Johnson",
                    "StartDate": "2023-12-01",
                    "EndDate": null,
                    "InformStartDate": "2024-01-01",
                    "InformEndDate": null,
                    "DOB": "1990-06-25",
                    "CobraStatus": true,
                    "Notes": "This is a sample note.",
                    "GlCode": "GL35688",
                    "Division": "Marketing",
                    "Location": "Houston",
                    "Title": "Director",
                    "Dependents": [
                        {
                            "DependentID": 1,
                            "EmployeeID": 1,
                            "DependentName": "Chris Smith",
                            "Relationship": "Child",
                            "DOB": "1990-06-25",
                            "StartDate": "2023-12-01",
                            "InformStartDate": "2024-01-01",
                            "EndDate": "2024-02-01",
                            "InformEndDate": "2024-02-01"
                        },
                        {
                            "DependentID": 2,
                            "EmployeeID": 1,
                            "DependentName": "Casey Smith",
                            "Relationship": "Spouse",
                            "DOB": "1990-06-25",
                            "StartDate": "2023-12-01",
                            "InformStartDate": "2024-01-01",
                            "EndDate": "2024-02-01",
                            "InformEndDate": "2024-02-01"
                        }
                    ],
                    "Carrier": "Carrier1",
                    "Tier": null
                },
                {
                    "EmployeeID": 2,
                    "EmployerID": 1,
                    "EmployeeFullName": "Alice Smith",
                    "EmployeeFirstName": "Alice",
                    "EmployeeLastName": "Smith",
                    "StartDate": "2019-01-01",
                    "EndDate": null,
                    "InformStartDate": "2020-02-01",
                    "InformEndDate": null,
                    "DOB": "1990-06-25",
                    "CobraStatus": false,
                    "Notes": "This is a sample note.",
                    "GlCode": "GL78881",
                    "Division": "Finance",
                    "Location": "New York",
                    "Title": "Analyst",
                    "Dependents": [
                        {
                            "DependentID": 1,
                            "EmployeeID": 2,
                            "DependentName": "Sam Jones",
                            "Relationship": "Spouse",
                            "DOB": "1990-06-25",
                            "StartDate": "2023-01-01",
                            "InformStartDate": "2023-01-01",
                            "EndDate": "2024-01-01",
                            "InformEndDate": "2024-01-01"
                        },
                        {
                            "DependentID": 2,
                            "EmployeeID": 2,
                            "DependentName": "Casey Jones",
                            "Relationship": "Child",
                            "DOB": "1990-06-25",
                            "StartDate": "2023-01-01",
                            "InformStartDate": "2023-01-01",
                            "EndDate": "2024-01-01",
                            "InformEndDate": "2024-01-01"
                        }
                    ],
                    "Carrier": "Carrier1",
                    "Tier": null
                },
                {
                    "EmployeeID": 3,
                    "EmployerID": 1,
                    "EmployeeFullName": "Alice Brown",
                    "EmployeeFirstName": "Alice",
                    "EmployeeLastName": "Brown",
                    "StartDate": "2000-01-01",
                    "EndDate": null,
                    "InformStartDate": "2000-01-01",
                    "InformEndDate": null,
                    "DOB": "1990-06-25",
                    "CobraStatus": false,
                    "Notes": "This is a sample note.",
                    "GlCode": "GL38764",
                    "Division": "Marketing",
                    "Location": "Chicago",
                    "Title": "Manager",
                    "Dependents": [
                        {
                            "DependentID": 1,
                            "EmployeeID": 3,
                            "DependentName": "Jordan Johnson",
                            "Relationship": "Child",
                            "DOB": "1990-06-25",
                            "StartDate": "2023-01-01",
                            "InformStartDate": "2023-01-01",
                            "EndDate": "2024-01-01",
                            "InformEndDate": "2024-01-01"
                        },
                        {
                            "DependentID": 2,
                            "EmployeeID": 3,
                            "DependentName": "Jordan Brown",
                            "Relationship": "Spouse",
                            "DOB": "1990-06-25",
                            "StartDate": "2023-01-01",
                            "InformStartDate": "2023-01-01",
                            "EndDate": "2024-01-01",
                            "InformEndDate": "2024-01-01"
                        }
                    ],
                    "Carrier": "Carrier1",
                    "Tier": null
                },
                {
                    "EmployeeID": 4,
                    "EmployerID": 1,
                    "EmployeeFullName": "Mike Doe",
                    "EmployeeFirstName": "Mike",
                    "EmployeeLastName": "Doe",
                    "StartDate": "2000-01-01",
                    "EndDate": null,
                    "InformStartDate": "2000-01-01",
                    "InformEndDate": null,
                    "DOB": "1990-06-25",
                    "CobraStatus": false,
                    "Notes": "This is a sample note.",
                    "GlCode": "GL44430",
                    "Division": "HR",
                    "Location": "Chicago",
                    "Title": "Director",
                    "Dependents": [
                        {
                            "DependentID": 1,
                            "EmployeeID": 4,
                            "DependentName": "Sam Jones",
                            "Relationship": "Spouse",
                            "DOB": "1990-06-25",
                            "StartDate": "2023-01-01",
                            "InformStartDate": "2023-01-01",
                            "EndDate": "2024-01-01",
                            "InformEndDate": "2024-01-01"
                        },
                        {
                            "DependentID": 2,
                            "EmployeeID": 4,
                            "DependentName": "Taylor Jones",
                            "Relationship": "Child",
                            "DOB": "1990-06-25",
                            "StartDate": "2023-01-01",
                            "InformStartDate": "2023-01-01",
                            "EndDate": "2024-01-01",
                            "InformEndDate": "2024-01-01"
                        }
                    ],
                    "Carrier": "Carrier1",
                    "Tier": null
                },
                {
                    "EmployeeID": 5,
                    "EmployerID": 1,
                    "EmployeeFullName": "Alex Williams",
                    "EmployeeFirstName": "Alex",
                    "EmployeeLastName": "Williams",
                    "StartDate": "2000-01-01",
                    "EndDate": "2023-12-01",
                    "InformStartDate": "2000-01-01",
                    "InformEndDate": "2024-01-01",
                    "DOB": "1990-06-25",
                    "CobraStatus": true,
                    "Notes": "This is a sample note.",
                    "GlCode": "GL35279",
                    "Division": "Finance",
                    "Location": "Los Angeles",
                    "Title": "Manager",
                    "Dependents": [
                        {
                            "DependentID": 1,
                            "EmployeeID": 5,
                            "DependentName": "Pat Williams",
                            "Relationship": "Spouse",
                            "DOB": "1990-06-25",
                            "StartDate": "2023-01-01",
                            "InformStartDate": "2023-01-01",
                            "EndDate": "2024-01-01",
                            "InformEndDate": "2024-01-01"
                        },
                        {
                            "DependentID": 2,
                            "EmployeeID": 5,
                            "DependentName": "Pat Jones",
                            "Relationship": "Spouse",
                            "DOB": "1990-06-25",
                            "StartDate": "2023-01-01",
                            "InformStartDate": "2023-01-01",
                            "EndDate": "2024-01-01",
                            "InformEndDate": "2024-01-01"
                        }
                    ],
                    "Carrier": "Carrier1",
                    "Tier": null
                }
            ],
            "carriers": [
                {
                    "CarrierID": 1,
                    "EmployerID": 1,
                    "CarrierName": "Carrier1"
                }
            ],
            "tiers": [
                {
                    "TierID": 1,
                    "EmployerID": 1,
                    "TierName": "Tier1",
                    "MaxAge": 50,
                    "MinAge": 0
                },
                {
                    "TierID": 2,
                    "EmployerID": 1,
                    "TierName": "Tier2",
                    "MaxAge": 10000,
                    "MinAge": 51
                }
            ],
            "plans": [
                {
                    "PlanID": 1,
                    "EmployerID": 1,
                    "CarrierID": 1,
                    "TierID": 1,
                    "FundingAmount": 3,
                    "GrenzFee": 0.2,
                    "GrenzFeeC": 0.3,
                    "GrenzFeeS": 0.7,
                    "CarrierName": "Carrier1",
                    "TierName": "Tier1"
                },
                {
                    "PlanID": 2,
                    "EmployerID": 1,
                    "CarrierID": 1,
                    "TierID": 2,
                    "FundingAmount": 5,
                    "GrenzFee": 0.2,
                    "GrenzFeeC": 0.3,
                    "GrenzFeeS": 0.7,
                    "CarrierName": "Carrier1",
                    "TierName": "Tier2"
                }
            ]
        },
        {
        "EmployerID": 2,
            "EmployerName": "Template",
            "TierStructure": "AgeBanded",
            "UsesGlCode": true,
            "UsesDivision": true,
            "UsesLocation": true,
            "UsesTitle": true,
            "PerferedBillingDate": "2025-05-01",
            "RenewalDate": "2000-01-01"
        }
    ]
}"""
@app.route('/test/addemployer', methods=['GET'])
def test_add_employer():
    response = ""
    connection = get_db_connection()
    cursor = connection.cursor()
    test_json = json.loads(test_json_1)
    for employer in test_json['employers']:
        employer_id, warnings = add_element_by_table_name(cursor, "Employer", employer)
        response += employer['EmployerName'] + " " + str(employer_id) + " " + str(warnings) + " | "
    connection.commit()
    cursor.close()
    connection.close()
    return jsonify("Employer added: " + response)

@app.route('/test/deleteemployer', methods=['GET'])
def test_delete_employer():
    connection = get_db_connection()
    cursor = connection.cursor()
    test_json = json.loads(test_json_1)
    for employer in test_json['employers']:
        delete_employer(cursor, employer['EmployerID'])
    connection.commit()
    cursor.close()
    connection.close()
    return jsonify("Employer deleted")

@app.route('/test/cleardb', methods=['GET'])
def clear_database():
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT EmployerID FROM Employer")
        employers = cursor.fetchall()
    except Exception as e:
        return jsonify({"Error Getting Employers ": str(e)}), 400

    for employer in employers:
        delete_employer(cursor, employer[0])
    connection.commit()
    cursor.close()
    connection.close()
    return jsonify("Database cleared")

@app.route('/test/resetdb', methods=['GET'])
def reset_database():
    clear_database()
    employers = test_add_employer()
    return jsonify("Database reset! Employers: " + str(employers))

@app.route('/test/generatereport/<EmployerID>/<Year>/<Month>', methods=['GET'])
def test_generate_report(EmployerID, Year, Month):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(f"SELECT EmployerName FROM Employer WHERE EmployerID = {EmployerID}")
    try:
        EmployerName = cursor.fetchall()[0][0]
    except Exception as e:
        return jsonify({"Error Getting Employer Name": str(e)}), 400
    Date = datetime(int(Year), int(Month), 1)
    cursor.close()
    try:
        report = generate_report(connection, EmployerName, Date, get_format=get_format_normal)
    except Exception as e:
        return jsonify({"Error Gennerating Report": str(e)}), 500
    
    
        #report = "output.xlsx"
    connection.close()
    if(not report):
        return jsonify("Report not generated"), 400
    # set the header
    response = send_file(report, as_attachment=True, download_name=(report))
    # response.headers.set('Content-Disposition', 'attachment', filename=(report))
    # response.headers.set('content-disposition', 'attachment', filename=(report))
    # response.headers.set('Content-Disposition', 'attachment; filename=' + report)
    # response.headers.set('content-disposition', 'attachment; filename=' + report)
    # response.headers.add("Content-Disposition", "attachment", filename=(report))
    # response.headers.add("Content-Type", "application/xlsx")
    #header = {"Content-Type": "application/xlsx", "Content-Disposition": "attachment; filename=" + (report + ".xlsx")}
    #response.headers = header
    # raise ValueError (response.headers)
    return response
    
@app.route('/test/getelementbyid', methods=['GET'])
def test_get_element_by_id():
    connection = get_db_connection()
    cursor = connection.cursor()
    element = get_element_by_id(cursor, "Employer", 2)
    cursor.close()
    connection.close()
    return jsonify(element)

@app.route('/test/executeCommand', methods=['GET'])
def test_execute_command():
    test_commands = [
        # "ALTER TABLE Dependent ADD COLUMN Notes TEXT",
    ]
    connection = get_db_connection()
    cursor = connection.cursor()
    for command in test_commands:
        cursor.execute(command)
    result = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(result)

####### Run on Start #######

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)

