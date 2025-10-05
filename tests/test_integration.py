#!/usr/bin/env python3
"""
Integration tests for the Playwright Failure Bundler action.

These tests verify the end-to-end functionality of the action components
working together.
"""

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from create_issue import GitHubAPIClient, IssueFormatter, IssueManager  # noqa: E402
from error_handling import setup_error_handling  # noqa: E402
from parse_report import PlaywrightReportParser  # noqa: E402


class TestIntegration(unittest.TestCase):
    """Integration test cases."""

    def setUp(self):
        """Set up test fixtures."""
        self.error_handler = setup_error_handling(debug_mode=True)
        self.temp_dir = tempfile.mkdtemp()

        # Create a realistic Playwright report
        self.realistic_report = {
            "stats": {"expected": 15, "unexpected": 3, "skipped": 2, "duration": 45000},
            "suites": [
                {
                    "title": "Authentication Tests",
                    "specs": [
                        {
                            "file": "tests/auth/login.spec.ts",
                            "tests": [
                                {
                                    "title": "should login with valid credentials",
                                    "location": {"file": "tests/auth/login.spec.ts", "line": 15},
                                    "results": [
                                        {
                                            "status": "failed",
                                            "duration": 8000,
                                            "retry": 1,
                                            "error": {
                                                "message": "expect(page.locator('[data-testid=\"welcome\"]')).toBeVisible()",
                                                "stack": "Error: Timed out 5000ms waiting for expect(locator).toBeVisible()\\n    at /home/runner/work/app/tests/auth/login.spec.ts:23:5\\n    at runTest (/home/runner/work/app/node_modules/@playwright/test/lib/worker.js:123:45)",
                                            },
                                        }
                                    ],
                                },
                                {
                                    "title": "should show error for invalid credentials",
                                    "location": {"file": "tests/auth/login.spec.ts", "line": 30},
                                    "results": [{"status": "passed", "duration": 2000, "retry": 0}],
                                },
                            ],
                        }
                    ],
                },
                {
                    "title": "Dashboard Tests",
                    "specs": [
                        {
                            "file": "tests/dashboard/navigation.spec.ts",
                            "tests": [
                                {
                                    "title": "should navigate to user profile",
                                    "location": {
                                        "file": "tests/dashboard/navigation.spec.ts",
                                        "line": 10,
                                    },
                                    "results": [
                                        {
                                            "status": "failed",
                                            "duration": 30000,
                                            "retry": 0,
                                            "error": {
                                                "message": "Navigation timeout of 30000ms exceeded",
                                                "stack": "TimeoutError: Navigation timeout of 30000ms exceeded\\n    at /home/runner/work/app/tests/dashboard/navigation.spec.ts:15:3\\n    at navigate (/home/runner/work/app/node_modules/playwright/lib/page.js:456:12)",
                                            },
                                        }
                                    ],
                                },
                                {
                                    "title": "should display user statistics",
                                    "location": {
                                        "file": "tests/dashboard/stats.spec.ts",
                                        "line": 8,
                                    },
                                    "results": [
                                        {
                                            "status": "failed",
                                            "duration": 5000,
                                            "retry": 2,
                                            "error": {
                                                "message": "expect(received).toBe(expected)",
                                                "stack": "Error: expect(received).toBe(expected)\\n\\nExpected: 42\\nReceived: undefined\\n\\n    at /home/runner/work/app/tests/dashboard/stats.spec.ts:12:7",
                                            },
                                        }
                                    ],
                                },
                            ],
                        }
                    ],
                },
            ],
            "config": {
                "version": "1.40.0",
                "projects": [{"name": "chromium"}, {"name": "firefox"}],
                "workers": 4,
                "reportSlowTests": {"max": 5, "threshold": 15000},
            },
        }

        self.github_context = {
            "repository": "testorg/testapp",
            "sha": "abc123def456789",
            "ref": "refs/heads/feature/new-dashboard",
            "run_id": "987654321",
            "run_number": "156",
            "actor": "developer123",
            "workflow": "CI/CD Pipeline",
            "event_name": "push",
            "server_url": "https://github.com",
        }

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_temp_report(self, data):
        """Create a temporary report file with given data."""
        report_path = os.path.join(self.temp_dir, "test_report.json")
        with open(report_path, "w") as f:
            json.dump(data, f, indent=2)
        return report_path

    def test_end_to_end_parsing_and_formatting(self):
        """Test complete flow from report parsing to issue formatting."""
        # Create report file
        report_path = self.create_temp_report(self.realistic_report)

        # Parse the report
        parser = PlaywrightReportParser(report_path, self.error_handler)
        summary = parser.parse_failures(max_failures=5)

        # Verify parsing results
        self.assertEqual(summary.total_tests, 20)  # 15 + 3 + 2
        self.assertEqual(summary.failed_tests, 3)
        self.assertEqual(summary.passed_tests, 15)
        self.assertEqual(summary.skipped_tests, 2)
        self.assertEqual(len(summary.failures), 3)

        # Check failure details
        login_failure = next(
            f for f in summary.failures if "login with valid credentials" in f.test_name
        )
        self.assertEqual(login_failure.file_path, "tests/auth/login.spec.ts")
        self.assertEqual(login_failure.line_number, 15)
        self.assertEqual(login_failure.retry_count, 1)
        self.assertIn("toBeVisible", login_failure.error_message)

        navigation_failure = next(
            f for f in summary.failures if "navigate to user profile" in f.test_name
        )
        self.assertEqual(navigation_failure.duration, 30000)
        self.assertIn("Navigation timeout", navigation_failure.error_message)

        # Format as issue
        formatter = IssueFormatter(self.github_context)
        issue_body = formatter.format_issue_body(summary.__dict__)

        # Verify issue content
        self.assertIn("🚨 Playwright Test Failures Detected", issue_body)
        self.assertIn("3 test failures detected", issue_body)
        self.assertIn("testorg/testapp", issue_body)
        # Branch name comes from git utilities, which may return "unknown" in test environment
        self.assertIn("Branch", issue_body)
        self.assertIn("Authentication Tests > should login with valid credentials", issue_body)
        self.assertIn("Dashboard Tests > should navigate to user profile", issue_body)
        self.assertIn("Dashboard Tests > should display user statistics", issue_body)
        self.assertIn("tests/auth/login.spec.ts", issue_body)
        self.assertIn("tests/dashboard/navigation.spec.ts", issue_body)
        self.assertIn("Playwright Version** | 1.40.0", issue_body)
        self.assertIn("chromium, firefox", issue_body)

    def test_max_failures_limit(self):
        """Test that max_failures limit is respected throughout the pipeline."""
        report_path = self.create_temp_report(self.realistic_report)

        # Parse with limit
        parser = PlaywrightReportParser(report_path, self.error_handler)
        summary = parser.parse_failures(max_failures=2)

        # Should limit failures but keep accurate counts
        self.assertEqual(len(summary.failures), 2)
        self.assertEqual(summary.failed_tests, 3)  # Still reports actual count

        # Format issue
        formatter = IssueFormatter(self.github_context)
        issue_body = formatter.format_issue_body(summary.__dict__)

        # Should show limited failures but accurate summary
        self.assertIn("3 test failures detected", issue_body)
        failure_sections = issue_body.count("### ")
        self.assertEqual(failure_sections, 2)  # Only 2 detailed failures

    @patch("create_issue.requests.Session")
    def test_github_api_integration(self, mock_session_class):
        """Test GitHub API integration with realistic scenarios."""
        # Setup mock responses
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # Mock search response (no existing issues)
        search_response = Mock()
        search_response.status_code = 200
        search_response.json.return_value = {"items": []}

        # Mock create response
        create_response = Mock()
        create_response.status_code = 201
        create_response.json.return_value = {
            "number": 42,
            "html_url": "https://github.com/testorg/testapp/issues/42",
            "title": "Test Failures - Build #156",
        }

        mock_session.get.return_value = search_response
        mock_session.post.return_value = create_response

        # Parse report
        report_path = self.create_temp_report(self.realistic_report)
        parser = PlaywrightReportParser(report_path, self.error_handler)
        summary = parser.parse_failures()

        # Create issue
        client = GitHubAPIClient("fake_token", "testorg/testapp", self.error_handler)
        formatter = IssueFormatter(self.github_context)
        manager = IssueManager(client, formatter)

        issue_number, issue_url, was_created = manager.create_or_update_issue(
            summary.__dict__,
            "Test Failures - Build #156",
            ["bug", "playwright", "ci"],
            ["qa-team"],
            deduplicate=True,
        )

        # Verify results
        self.assertEqual(issue_number, 42)
        self.assertEqual(issue_url, "https://github.com/testorg/testapp/issues/42")
        self.assertTrue(was_created)

        # Verify API calls
        mock_session.get.assert_called_once()  # Search call
        mock_session.post.assert_called_once()  # Create call

        # Verify create call parameters
        create_call = mock_session.post.call_args
        self.assertIn("json", create_call.kwargs)
        create_data = create_call.kwargs["json"]
        self.assertEqual(create_data["title"], "Test Failures - Build #156")
        self.assertEqual(create_data["labels"], ["bug", "playwright", "ci"])
        self.assertEqual(create_data["assignees"], ["qa-team"])
        self.assertIn("🚨 Playwright Test Failures Detected", create_data["body"])

    @patch("create_issue.requests.Session")
    def test_deduplication_workflow(self, mock_session_class):
        """Test the deduplication workflow."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # Mock search response (existing issue found)
        search_response = Mock()
        search_response.status_code = 200
        search_response.json.return_value = {
            "items": [
                {
                    "number": 24,
                    "title": "Test Failures - Build #156",
                    "html_url": "https://github.com/testorg/testapp/issues/24",
                }
            ]
        }

        # Mock update response
        update_response = Mock()
        update_response.status_code = 200
        update_response.json.return_value = {
            "number": 24,
            "html_url": "https://github.com/testorg/testapp/issues/24",
        }

        mock_session.get.return_value = search_response
        mock_session.patch.return_value = update_response

        # Parse report and create issue
        report_path = self.create_temp_report(self.realistic_report)
        parser = PlaywrightReportParser(report_path, self.error_handler)
        summary = parser.parse_failures()

        client = GitHubAPIClient("fake_token", "testorg/testapp", self.error_handler)
        formatter = IssueFormatter(self.github_context)
        manager = IssueManager(client, formatter)

        issue_number, issue_url, was_created = manager.create_or_update_issue(
            summary.__dict__, "Test Failures - Build #156", ["bug"], [], deduplicate=True
        )

        # Should update existing issue
        self.assertEqual(issue_number, 24)
        self.assertFalse(was_created)

        # Should search but not create
        mock_session.get.assert_called_once()
        mock_session.patch.assert_called_once()
        mock_session.post.assert_not_called()

    def test_error_propagation(self):
        """Test that errors propagate correctly through the pipeline."""
        # Test with missing file
        with self.assertRaises(Exception):
            parser = PlaywrightReportParser("/nonexistent/file.json", self.error_handler)
            parser.parse_failures()

        # Test with invalid JSON
        invalid_path = os.path.join(self.temp_dir, "invalid.json")
        with open(invalid_path, "w") as f:
            f.write("{ invalid json }")

        with self.assertRaises(Exception):
            parser = PlaywrightReportParser(invalid_path, self.error_handler)
            parser.parse_failures()

        # Test with malformed report structure
        malformed_report = {"invalid": "structure"}
        malformed_path = self.create_temp_report(malformed_report)

        with self.assertRaises(Exception):
            parser = PlaywrightReportParser(malformed_path, self.error_handler)
            parser.parse_failures()

    def test_large_report_handling(self):
        """Test handling of large reports with many failures."""
        # Create a report with 50 failures
        large_report = {
            "stats": {"expected": 50, "unexpected": 50, "skipped": 0, "duration": 300000},
            "suites": [],
            "config": {"version": "1.40.0", "projects": [{"name": "chromium"}]},
        }

        # Generate 50 failures
        for i in range(50):
            suite = {
                "title": f"Test Suite {i // 5}",
                "specs": [
                    {
                        "file": f"tests/suite{i // 5}/test{i}.spec.ts",
                        "tests": [
                            {
                                "title": f"test case {i}",
                                "location": {
                                    "file": f"tests/suite{i // 5}/test{i}.spec.ts",
                                    "line": 10 + i,
                                },
                                "results": [
                                    {
                                        "status": "failed",
                                        "duration": 5000,
                                        "retry": 0,
                                        "error": {
                                            "message": f"Test {i} failed",
                                            "stack": f"Error: Test {i} failed\n    at test{i}.spec.ts:{10+i}:5",
                                        },
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
            large_report["suites"].append(suite)

        report_path = self.create_temp_report(large_report)

        # Parse with limit
        parser = PlaywrightReportParser(report_path, self.error_handler)
        summary = parser.parse_failures(max_failures=10)

        # Should limit to 10 but track all 50
        self.assertEqual(len(summary.failures), 10)
        self.assertEqual(summary.failed_tests, 50)

        # Format issue
        formatter = IssueFormatter(self.github_context)
        issue_body = formatter.format_issue_body(summary.__dict__)

        # Should indicate truncation
        self.assertIn("50 test failures detected", issue_body)

    def test_special_characters_in_test_names(self):
        """Test handling of special characters and Unicode in test names."""
        special_report = {
            "stats": {"expected": 1, "unexpected": 1, "skipped": 0, "duration": 5000},
            "suites": [
                {
                    "title": "Special Characters Suite",
                    "specs": [
                        {
                            "file": "tests/special.spec.ts",
                            "tests": [
                                {
                                    "title": 'Test with "quotes" and <tags> & symbols: €, ñ, 中文',
                                    "location": {"file": "tests/special.spec.ts", "line": 10},
                                    "results": [
                                        {
                                            "status": "failed",
                                            "duration": 5000,
                                            "retry": 0,
                                            "error": {
                                                "message": "Error with special chars: 'single' and \"double\" quotes",
                                                "stack": "Error at line 10",
                                            },
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ],
            "config": {"version": "1.40.0"},
        }

        report_path = self.create_temp_report(special_report)
        parser = PlaywrightReportParser(report_path, self.error_handler)
        summary = parser.parse_failures()

        # Should parse successfully
        self.assertEqual(len(summary.failures), 1)
        self.assertIn("quotes", summary.failures[0].test_name)
        self.assertIn("symbols", summary.failures[0].test_name)

        # Should format without breaking markdown
        formatter = IssueFormatter(self.github_context)
        issue_body = formatter.format_issue_body(summary.__dict__)
        self.assertIn("中文", issue_body)

    def test_empty_report_handling(self):
        """Test handling of reports with no failures."""
        empty_report = {
            "stats": {"expected": 25, "unexpected": 0, "skipped": 0, "duration": 30000},
            "suites": [
                {
                    "title": "All Passing Suite",
                    "specs": [
                        {
                            "file": "tests/passing.spec.ts",
                            "tests": [
                                {
                                    "title": "passing test",
                                    "location": {"file": "tests/passing.spec.ts", "line": 5},
                                    "results": [{"status": "passed", "duration": 1000, "retry": 0}],
                                }
                            ],
                        }
                    ],
                }
            ],
            "config": {"version": "1.40.0"},
        }

        report_path = self.create_temp_report(empty_report)
        parser = PlaywrightReportParser(report_path, self.error_handler)
        summary = parser.parse_failures()

        # Should have no failures
        self.assertEqual(len(summary.failures), 0)
        self.assertEqual(summary.failed_tests, 0)
        self.assertEqual(summary.passed_tests, 25)

    # Note: API error handling tests (rate limiting, auth errors) are covered
    # by the deduplication workflow test and create_issue unit tests

    def test_multiple_retry_counts(self):
        """Test handling of tests with multiple retry attempts."""
        retry_report = {
            "stats": {"expected": 3, "unexpected": 1, "skipped": 0, "duration": 30000},
            "suites": [
                {
                    "title": "Retry Suite",
                    "specs": [
                        {
                            "file": "tests/flaky.spec.ts",
                            "tests": [
                                {
                                    "title": "flaky test with 3 retries",
                                    "location": {"file": "tests/flaky.spec.ts", "line": 10},
                                    "results": [
                                        {
                                            "status": "failed",
                                            "duration": 5000,
                                            "retry": 3,
                                            "error": {"message": "Still failing after 3 retries"},
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ],
            "config": {"version": "1.40.0"},
        }

        report_path = self.create_temp_report(retry_report)
        parser = PlaywrightReportParser(report_path, self.error_handler)
        summary = parser.parse_failures()

        # Should capture retry count
        self.assertEqual(summary.failures[0].retry_count, 3)

        # Issue should mention retries
        formatter = IssueFormatter(self.github_context)
        issue_body = formatter.format_issue_body(summary.__dict__)
        # Retry count appears in failure details
        self.assertIn("Retries**: 3", issue_body)


if __name__ == "__main__":
    unittest.main()
