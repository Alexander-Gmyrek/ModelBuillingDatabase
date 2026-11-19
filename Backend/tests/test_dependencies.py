"""Import, runtime and API contracts used by the frontend."""
import ast
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parents[1]))
import app as billing


class DependencyTests(unittest.TestCase):
    def test_backend_parses_on_docker_python_version(self):
        for source in Path(__file__).parents[1].rglob("*.py"):
            with self.subTest(source=source.name):
                ast.parse(source.read_text(), feature_version=(3, 9))

    def test_cold_import_does_not_require_a_database(self):
        script = """
from unittest.mock import patch
with patch('mysql.connector.connect', side_effect=AssertionError('Unexpected database connection')):
    import app
    import backup_validation
    import enrollment
    import employee_import
    import history
    import monthly_billing
    assert app.app
    print('COLD_IMPORT_OK')
"""
        command = [sys.executable]
        if sys.flags.no_site:
            command.append("-S")
        result = subprocess.run(command + ["-c", script], cwd=Path(__file__).parents[1],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("COLD_IMPORT_OK", result.stdout)

    def test_frontend_api_paths_are_registered(self):
        adapter = billing.app.url_map.bind("localhost")
        paths = [
            ("PATCH", "/employee/1/details", "save_employee_details"),
            ("PATCH", "/employee/1/terminate", "terminate_employee_route"),
            ("PATCH", "/employer/1/plan_setup", "save_employer_plan_setup_route"),
            ("POST", "/employer/1/import/preview", "preview_employee_import"),
            ("POST", "/employer/1/import", "commit_employee_import"),
            ("GET", "/employer/1/reports", "saved_reports"),
            ("GET", "/employer/1/reports/1", "download_saved_report"),
            ("GET", "/employer/1/history", "company_history"),
            ("GET", "/test/generatereport/1/2026/6", "test_generate_report"),
            ("GET", "/backup", "backup_database_route"),
            ("POST", "/restore", "restore_database_route"),
        ]
        for method, path, expected in paths:
            with self.subTest(path=path):
                endpoint, _ = adapter.match(path, method=method)
                self.assertEqual(endpoint, expected)

    def test_local_origins_can_use_employee_save(self):
        client = billing.app.test_client()
        for origin in ("http://localhost:8080", "http://127.0.0.1:8080"):
            response = client.options("/employee/1/details", headers={
                "Origin": origin, "Access-Control-Request-Method": "PATCH",
                "Access-Control-Request-Headers": "Content-Type"
            })
            self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), origin)
            self.assertIn("PATCH", response.headers.get("Access-Control-Allow-Methods", ""))
        blocked = client.options("/employee/1/details", headers={
            "Origin": "https://unrelated.example", "Access-Control-Request-Method": "PATCH"
        })
        self.assertIsNone(blocked.headers.get("Access-Control-Allow-Origin"))

    def test_disabled_development_tools_do_not_connect_to_database(self):
        connect = Mock(side_effect=AssertionError("Database must not be accessed"))
        with patch.dict(os.environ, {"BILLING_ENABLE_TEST_TOOLS": "0"}):
            with patch.object(billing, "get_db_connection", connect):
                self.assertEqual(billing.app.test_client().get("/test/cleardb").status_code, 404)
        connect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
