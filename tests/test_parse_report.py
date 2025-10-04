#!/usr/bin/env python3
"""
Unit tests for the Playwright report parser.
"""

import json
import os
import sys
import tempfile
import unittest

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from error_handling import ErrorCodes, setup_error_handling
from parse_report import PlaywrightReportParser

try:
    from error_handling import ActionError
except ImportError:
    # Fallback for testing
    class ActionError(Exception):
        def __init__(self, code, message, severity, **kwargs):
            self.code = code
            self.message = message
            self.severity = severity
            super().__init__(message)


class TestPlaywrightReportParser(unittest.TestCase):
    """Test cases for PlaywrightReportParser."""

    def setUp(self):
        """Set up test fixtures."""
        self.error_handler = setup_error_handling(debug_mode=True)
        self.temp_dir = tempfile.mkdtemp()

        # Sample valid report data
        self.valid_report = {
            "stats": {"expected": 5, "unexpected": 2, "skipped": 1, "duration": 15000},
            "suites": [
                {
                    "title": "Login Tests",
                    "specs": [
                        {
                            "file": "tests/login.spec.ts",
                            "tests": [
                                {
                                    "title": "should login successfully",
                                    "location": {"file": "tests/login.spec.ts", "line": 10},
                                    "results": [
                                        {
                                            "status": "failed",
                                            "duration": 5000,
                                            "retry": 0,
                                            "error": {
                                                "message": "expect(page.locator('[data-testid=\"welcome\"]')).toBeVisible()",
                                                "stack": "Error: Timed out 5000ms waiting for expect(locator).toBeVisible()\n    at /home/runner/work/app/tests/login.spec.ts:23:5",
                                            },
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                },
                {
                    "title": "Dashboard Tests",
                    "specs": [
                        {
                            "file": "tests/dashboard.spec.ts",
                            "tests": [
                                {
                                    "title": "should load dashboard",
                                    "location": {"file": "tests/dashboard.spec.ts", "line": 15},
                                    "results": [
                                        {
                                            "status": "failed",
                                            "duration": 3000,
                                            "retry": 1,
                                            "error": {
                                                "message": "Navigation timeout of 30000ms exceeded",
                                                "stack": "TimeoutError: Navigation timeout of 30000ms exceeded\n    at /home/runner/work/app/tests/dashboard.spec.ts:15:3",
                                            },
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                },
            ],
            "config": {"version": "1.40.0", "projects": [{"name": "chromium"}], "workers": 4},
        }

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_temp_report(self, data):
        """Create a temporary report file with given data."""
        report_path = os.path.join(self.temp_dir, "test_report.json")
        with open(report_path, "w") as f:
            json.dump(data, f)
        return report_path

    def test_parse_valid_report(self):
        """Test parsing a valid Playwright report."""
        report_path = self.create_temp_report(self.valid_report)
        parser = PlaywrightReportParser(report_path, self.error_handler)

        summary = parser.parse_failures()

        self.assertEqual(summary.total_tests, 8)  # 5 + 2 + 1
        self.assertEqual(summary.passed_tests, 5)
        self.assertEqual(summary.failed_tests, 2)
        self.assertEqual(summary.skipped_tests, 1)
        self.assertEqual(summary.duration, 15000)
        self.assertEqual(len(summary.failures), 2)

        # Check first failure
        first_failure = summary.failures[0]
        self.assertEqual(first_failure.test_name, "Login Tests > should login successfully")
        self.assertEqual(first_failure.file_path, "tests/login.spec.ts")
        self.assertEqual(first_failure.line_number, 10)
        self.assertIn("expect(page.locator", first_failure.error_message)
        self.assertEqual(first_failure.duration, 5000)
        self.assertEqual(first_failure.retry_count, 0)

    def test_parse_with_max_failures(self):
        """Test parsing with max_failures limit."""
        report_path = self.create_temp_report(self.valid_report)
        parser = PlaywrightReportParser(report_path, self.error_handler)

        summary = parser.parse_failures(max_failures=1)

        self.assertEqual(len(summary.failures), 1)
        self.assertEqual(summary.failed_tests, 2)  # Still reports total failures

    def test_file_not_found(self):
        """Test handling of missing report file."""
        parser = PlaywrightReportParser("/nonexistent/path.json", self.error_handler)

        with self.assertRaises(ActionError) as context:
            parser.load_report()

        self.assertEqual(context.exception.code, ErrorCodes.FILE_NOT_FOUND)

    def test_invalid_json(self):
        """Test handling of invalid JSON."""
        report_path = os.path.join(self.temp_dir, "invalid.json")
        with open(report_path, "w") as f:
            f.write("{ invalid json }")

        parser = PlaywrightReportParser(report_path, self.error_handler)

        with self.assertRaises(ActionError) as context:
            parser.load_report()

        self.assertEqual(context.exception.code, ErrorCodes.INVALID_JSON)

    def test_missing_stats(self):
        """Test handling of report missing stats section."""
        invalid_report = {"suites": []}
        report_path = self.create_temp_report(invalid_report)
        parser = PlaywrightReportParser(report_path, self.error_handler)

        with self.assertRaises(ActionError) as context:
            parser.parse_failures()

        self.assertEqual(context.exception.code, ErrorCodes.INVALID_REPORT_FORMAT)

    def test_no_test_results(self):
        """Test handling of report with no test results."""
        empty_report = {
            "stats": {"expected": 0, "unexpected": 0, "skipped": 0, "duration": 0},
            "suites": [],
        }
        report_path = self.create_temp_report(empty_report)
        parser = PlaywrightReportParser(report_path, self.error_handler)

        with self.assertRaises(ActionError) as context:
            parser.parse_failures()

        self.assertEqual(context.exception.code, ErrorCodes.NO_TEST_RESULTS)

    def test_nested_suites(self):
        """Test parsing of nested test suites."""
        nested_report = {
            "stats": {"expected": 1, "unexpected": 1, "skipped": 0, "duration": 5000},
            "suites": [
                {
                    "title": "Parent Suite",
                    "suites": [
                        {
                            "title": "Child Suite",
                            "specs": [
                                {
                                    "file": "tests/nested.spec.ts",
                                    "tests": [
                                        {
                                            "title": "nested test",
                                            "location": {"file": "tests/nested.spec.ts", "line": 5},
                                            "results": [
                                                {
                                                    "status": "failed",
                                                    "duration": 1000,
                                                    "retry": 0,
                                                    "error": {
                                                        "message": "Test failed",
                                                        "stack": "Error: Test failed\n    at tests/nested.spec.ts:5:1",
                                                    },
                                                }
                                            ],
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ],
        }

        report_path = self.create_temp_report(nested_report)
        parser = PlaywrightReportParser(report_path, self.error_handler)

        summary = parser.parse_failures()

        self.assertEqual(len(summary.failures), 1)
        self.assertEqual(summary.failures[0].test_name, "Child Suite > nested test")

    def test_malformed_test_data(self):
        """Test handling of malformed test data."""
        malformed_report = {
            "stats": {"expected": 0, "unexpected": 1, "skipped": 0, "duration": 1000},
            "suites": [
                {
                    "title": "Test Suite",
                    "specs": [
                        {
                            "file": "tests/malformed.spec.ts",
                            "tests": [
                                {
                                    # Missing title and location
                                    "results": [
                                        {
                                            "status": "failed",
                                            "duration": 1000,
                                            # Missing error details
                                        }
                                    ]
                                }
                            ],
                        }
                    ],
                }
            ],
        }

        report_path = self.create_temp_report(malformed_report)
        parser = PlaywrightReportParser(report_path, self.error_handler)

        # Should handle malformed data gracefully
        summary = parser.parse_failures()

        # Should still create a failure entry with default values
        self.assertEqual(len(summary.failures), 1)
        failure = summary.failures[0]
        self.assertIn("Unknown", failure.test_name)


if __name__ == "__main__":
    unittest.main()
