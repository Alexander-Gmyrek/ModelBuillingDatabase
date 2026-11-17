"""Persistent, read-only bill snapshots and database change history."""
import json
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO

from flask import jsonify, send_file

HISTORY_TABLES = ["ChangeLog", "ReportSnapshot", "ImportBatch"]


def json_value(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"Cannot serialize {type(value).__name__}")


def ensure_schema(connection):
    cursor = connection.cursor()
    try:
        cursor.execute("""CREATE TABLE IF NOT EXISTS ChangeLog (
            ChangeID BIGINT AUTO_INCREMENT PRIMARY KEY,
            CreatedAt DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
            EmployerID INT NULL, Action VARCHAR(60) NOT NULL,
            TableName VARCHAR(60) NOT NULL, RecordID BIGINT NULL,
            BeforeData LONGTEXT NULL, AfterData LONGTEXT NULL
        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS ReportSnapshot (
            ReportID BIGINT AUTO_INCREMENT PRIMARY KEY,
            EmployerID INT NOT NULL, BillingMonth DATE NOT NULL,
            CreatedAt DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
            Filename VARCHAR(255) NOT NULL, Workbook LONGBLOB NOT NULL
        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS ImportBatch (
            BatchKey VARCHAR(64) PRIMARY KEY, EmployerID INT NOT NULL,
            EmployeeCount INT NOT NULL,
            CreatedAt DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        )""")
        connection.commit()
    finally:
        cursor.close()


def record_change(cursor, action, table, record_id=None, before=None, after=None, employer_id=None):
    row = after or before or {}
    employer_id = employer_id or row.get("EmployerID")
    if table == "Employer":
        employer_id = record_id
    if employer_id is None and row.get("EmployeeID"):
        cursor.execute("SELECT EmployerID FROM Employee WHERE EmployeeID = %s", (row["EmployeeID"],))
        employee = cursor.fetchone()
        employer_id = employee[0] if employee else None
    cursor.execute(
        """INSERT INTO ChangeLog
        (EmployerID, Action, TableName, RecordID, BeforeData, AfterData)
        VALUES (%s, %s, %s, %s, %s, %s)""",
        (employer_id, action, table, record_id,
         json.dumps(before, default=json_value) if before is not None else None,
         json.dumps(after, default=json_value) if after is not None else None),
    )


def register_routes(app, connect):
    @app.get("/employer/<int:employer_id>/reports")
    def saved_reports(employer_id):
        connection = connect()
        cursor = connection.cursor()
        try:
            cursor.execute("""SELECT ReportID, BillingMonth, CreatedAt, Filename
                FROM ReportSnapshot WHERE EmployerID = %s ORDER BY ReportID DESC""", (employer_id,))
            return jsonify([{"ReportID": row[0], "BillingMonth": row[1].isoformat(),
                             "CreatedAt": row[2].isoformat(), "Filename": row[3]}
                            for row in cursor.fetchall()])
        finally:
            cursor.close()
            connection.close()

    @app.get("/employer/<int:employer_id>/reports/<int:report_id>")
    def download_saved_report(employer_id, report_id):
        connection = connect()
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT Filename, Workbook FROM ReportSnapshot WHERE ReportID = %s AND EmployerID = %s",
                           (report_id, employer_id))
            row = cursor.fetchone()
            if not row:
                return jsonify({"Error": "Saved bill not found."}), 404
            return send_file(BytesIO(bytes(row[1])), as_attachment=True, download_name=row[0],
                             mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        finally:
            cursor.close()
            connection.close()

    @app.get("/employer/<int:employer_id>/history")
    def company_history(employer_id):
        from flask import request
        try:
            before_id = int(request.args.get("before", 9223372036854775807))
        except ValueError:
            return jsonify({"Error": "Invalid history cursor."}), 400
        connection = connect()
        cursor = connection.cursor()
        try:
            cursor.execute("""SELECT ChangeID, CreatedAt, Action, TableName, RecordID, BeforeData, AfterData
                FROM ChangeLog WHERE (EmployerID = %s OR Action = 'Restore')
                AND ChangeID < %s ORDER BY ChangeID DESC LIMIT 100""", (employer_id, before_id))
            return jsonify([{"ChangeID": row[0], "CreatedAt": row[1].isoformat(),
                             "Action": row[2], "TableName": row[3], "RecordID": row[4],
                             "Before": json.loads(row[5]) if row[5] else None,
                             "After": json.loads(row[6]) if row[6] else None}
                            for row in cursor.fetchall()])
        finally:
            cursor.close()
            connection.close()
