"""Focused regression checks runnable without a MySQL server."""
import ast
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock


SOURCE = ast.parse((Path(__file__).parents[1] / "app.py").read_text())


def load_function(name, scope):
    function = next(node for node in SOURCE.body
                    if isinstance(node, ast.FunctionDef) and node.name == name)
    function.decorator_list = []
    exec(compile(ast.Module(body=[function], type_ignores=[]), name, "exec"), scope)
    return scope[name]


class BillingRegressions(unittest.TestCase):
    def test_employee_plan_update_keeps_table_case(self):
        change = Mock(return_value=([], 21))
        scope = {
            "BILLING_TABLES": ["Employee", "EmployeePlan"],
            "get_table_fields": lambda table, field: ["EmployeeID"] if table == "EmployeePlan" else [],
            "change_element": change,
            "get_element_by_id": lambda *args: {"EmployeePlanID": 21},
            "row_changed": lambda *args: False,
        }
        function = load_function("change_element_by_table_name", scope)
        function(None, "EmployeePlan", 21, {"EndDate": "2026-11-01"})
        self.assertEqual(change.call_args.args[1], "EmployeePlan")

    def test_employee_validation_precedes_changes(self):
        connection = Mock()
        connection.cursor.return_value.fetchone.return_value = (1,)
        change = Mock()
        scope = {
            "request": SimpleNamespace(get_json=lambda: {
                "Employee": {"EmployeeFullName": "Example", "StartDate": "2026-01-01"},
                "Dependents": [{"DependentName": "Incomplete"}],
            }),
            "get_db_connection": lambda: connection,
            "change_element_by_table_name": change,
            "jsonify": lambda value: value,
        }
        function = load_function("save_employee_details", scope)
        self.assertEqual(function(1)[1], 400)
        change.assert_not_called()
        connection.rollback.assert_called_once()

    def test_termination_handles_database_tuples(self):
        changes = Mock()
        scope = {
            "get_element_by_id": lambda *args: {"StartDate": "2026-01-01"},
            "as_date": date.fromisoformat,
            "change_element_by_table_name": changes,
            "record_change": Mock(),
            "get_active_depfree": lambda cursor, table, *args:
                [(21,)] if table == "EmployeePlan" else [(31,)],
        }
        terminate = load_function("terminate_employee", scope)
        terminate(None, 1, "2026-09-01", "2026-11-17")
        self.assertEqual(changes.call_args_list[1].args[2], 21)
        self.assertEqual(changes.call_args_list[2].args[2], 31)
        for call in changes.call_args_list:
            self.assertEqual(call.args[3]["InformEndDate"], "2026-11-17")

    def test_dependent_age_uses_report_year(self):
        age = Mock(return_value=12)
        query = Mock(side_effect=[
            [(1,)], [(2,)], [(date(2014, 1, 1),)],
            [(date(2020, 1, 1),)], [(3,)], [(4,)],
        ])
        scope = {
            "datetime": datetime,
            "execute_query": query,
            "get_employer_id_from_employee": lambda *args: 5,
            "calculate_age": age,
            "as_date": date.fromisoformat,
            "get_only_active_plan_on_date": lambda *args: 7,
        }
        function = load_function("get_plan_for_dependent", scope)
        self.assertEqual(function(None, 6, "2026-11-01"), 7)
        self.assertEqual(age.call_args.args[2], 2026)

    def test_employee_save_rolls_back_on_dependent_failure(self):
        connection = Mock()
        cursor = connection.cursor.return_value
        cursor.fetchone.return_value = (1,)
        scope = {
            "request": SimpleNamespace(get_json=lambda: {
                "Employee": {"EmployeeFullName": "Example", "StartDate": "2026-01-01"},
                "Dependents": [{"DependentName": "Child", "Relationship": "Child",
                                "DOB": "2015-01-01", "StartDate": "2026-01-01"}],
            }),
            "get_db_connection": lambda: connection,
            "change_element_by_table_name": Mock(),
            "add_element_by_table_name": Mock(side_effect=ValueError("insertion failed")),
            "jsonify": lambda value: value,
        }
        save = load_function("save_employee_details", scope)
        result, status = save(1)
        self.assertEqual(status, 400)
        self.assertIn("insertion failed", result["Error"])
        connection.rollback.assert_called_once()
        connection.commit.assert_not_called()
        cursor.close.assert_called_once()
        connection.close.assert_called_once()

    def test_legacy_plan_modification_preserves_old_record(self):
        old = {"PlanID": 1, "EmployerID": 2, "CarrierID": 3, "TierID": 4,
               "StartDate": date(2025, 1, 1), "EndDate": None}
        changes = Mock()
        add = Mock(return_value=({}, 9))
        move = Mock()
        scope = {
            "date": date,
            "as_date": lambda value: date.fromisoformat(value) if isinstance(value, str) else value,
            "get_element_by_id": lambda cursor, table, key:
                dict(old) if table == "Plan" else {"RenewalDate": date(2026, 1, 1)},
            "change_element_by_table_name": changes,
            "add_element_by_table_name": add,
            "move_employees_to_new_plan": move,
        }
        modify = load_function("modify_plan", scope)
        self.assertEqual(modify(None, 1, {"StartDate": "2026-11-01"}), 9)
        self.assertNotIn("PlanID", add.call_args.args[2])
        self.assertEqual(changes.call_args.args[3]["EndDate"], date(2026, 11, 1))
        move.assert_called_once_with(None, 1, 9)
        self.assertIsNone(old["EndDate"])


if __name__ == "__main__":
    unittest.main()
