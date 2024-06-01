from flask import Flask, request, jsonify
import mysql.connector
import pandas as pd
import json
import base64

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
    return "Hello, Flask!"

@app.route('/api', methods=['GET'])
def api():
    data = {"message": "Welcome to the API"}
    return jsonify(data)

@app.route('/testconection', methods=['GET'])
def testconection():
    connection = get_db_connection()
    if connection.is_connected():
        db_Info = connection.get_server_info()
        connection.close()
        return jsonify({"message": "Connected to MySQL Server version ", "version": db_Info})
    else:
        return jsonify({"message": "Connection to MySQL Server failed"})

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
    cursor.execute(f"SELECT * FROM Employer WHERE id={id}")
    user = cursor.fetchone()
    cursor.close()
    connection.close()
    return jsonify(user)

@app.route('/employer/<int:id>', methods=['DELETE'])
def delete_employer(id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(f"DELETE FROM Employer WHERE id={id}")
    connection.commit()
    cursor.close()
    connection.close()
    return jsonify({"message": "Employer deleted"})

# Get employer by name
@app.route('/employer/<string:name>', methods=['GET'])
def get_employer_by_name(name):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM Employer WHERE employer_name='{name}'")
    user = cursor.fetchone()
    cursor.close()
    connection.close()
    return jsonify(user)

# Search for employers by name
@app.route('/employer/search/<string:name>', methods=['GET'])
def search_employers(name):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM Employer WHERE employer_name LIKE '%{name}%'")
    users = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(users)

# Update an employer
@app.route('/employer/<int:id>', methods=['PATCH'])
def update_employer(id):
    return jsonify({"message": "method not fully implemented"})


# Add a new employer
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



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
