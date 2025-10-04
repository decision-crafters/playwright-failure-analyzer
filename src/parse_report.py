#!/usr/bin/env python3
"""
Playwright Report Parser

This module parses Playwright JSON test reports and extracts failure information
for bundling into GitHub issues.
"""

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from error_handling import (
    ActionError,
    ActionErrorHandler,
    ConfigValidator,
    ErrorCodes,
    ErrorSeverity,
    ReportValidator,
    error_handler,
    setup_error_handling,
)


@dataclass
class TestFailure:
    """Represents a single test failure with all relevant details."""

    test_name: str
    file_path: str
    line_number: Optional[int]
    error_message: str
    stack_trace: str
    duration: float
    retry_count: int
    project_name: Optional[str] = None
    browser: Optional[str] = None


@dataclass
class FailureSummary:
    """Summary of all test failures and metadata."""

    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    duration: float
    failures: List[TestFailure]
    metadata: Dict[str, Any]


class PlaywrightReportParser:
    """Parser for Playwright JSON test reports."""

    def __init__(self, report_path: str, error_handler: ActionErrorHandler):
        self.report_path = report_path
        self.report_data = None
        self.error_handler = error_handler
        self.validator = ReportValidator(error_handler)

    def load_report(self) -> None:
        """Load and validate the JSON report file."""
        if not os.path.exists(self.report_path):
            raise ActionError(
                code=ErrorCodes.FILE_NOT_FOUND,
                message=f"Report file not found: {self.report_path}",
                severity=ErrorSeverity.HIGH,
                suggestions=[
                    "Ensure Playwright tests have run and generated a JSON report",
                    "Check the report path configuration",
                    "Verify the report file wasn't deleted or moved",
                ],
            )

        try:
            with open(self.report_path, "r", encoding="utf-8") as f:
                self.report_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ActionError(
                code=ErrorCodes.INVALID_JSON,
                message=f"Invalid JSON in report file: {e}",
                severity=ErrorSeverity.HIGH,
                suggestions=[
                    "Ensure the report file is complete and not truncated",
                    "Regenerate the Playwright report",
                    "Check that Playwright completed successfully",
                ],
            )
        except Exception as e:
            raise ActionError(
                code=ErrorCodes.FILE_READ_ERROR,
                message=f"Failed to read report file: {e}",
                severity=ErrorSeverity.HIGH,
                suggestions=["Check file permissions and disk space"],
            )

    def parse_failures(self, max_failures: int = None) -> FailureSummary:
        """Parse the report and extract failure information."""
        if self.report_data is None:
            self.load_report()

        # Validate report structure
        self.validator.validate_report_structure(self.report_data)
        self.validator.validate_has_test_results(self.report_data)

        # Extract basic statistics
        stats = self.report_data.get("stats", {})
        total_tests = (
            stats.get("expected", 0) + stats.get("unexpected", 0) + stats.get("skipped", 0)
        )
        passed_tests = stats.get("expected", 0)
        failed_tests = stats.get("unexpected", 0)
        skipped_tests = stats.get("skipped", 0)
        duration = stats.get("duration", 0)

        # Extract failures from test results
        failures = []
        suites = self.report_data.get("suites", [])

        for suite in suites:
            failures.extend(self._extract_suite_failures(suite))

        # Limit failures if max_failures is specified
        if max_failures and len(failures) > max_failures:
            failures = failures[:max_failures]

        # Create metadata for AI analysis
        config = self.report_data.get("config", {})
        metadata = {
            "total_tests": total_tests,
            "playwright_version": config.get("version", "unknown"),
            "projects": [p.get("name", "default") for p in config.get("projects", [])],
            "workers": config.get("workers", 1),
            "test_dir": config.get("testDir", ""),
            "timeout": config.get("timeout", 30000),
            "reporter": "json",
            "report_slow_tests": config.get("reportSlowTests", {}),
            "use": config.get("use", {}),
        }

        return FailureSummary(
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=skipped_tests,
            duration=duration,
            failures=failures,
            metadata=metadata,
        )

    def _extract_suite_failures(self, suite: Dict[str, Any]) -> List[TestFailure]:
        """Extract failures from a test suite."""
        failures = []

        # Process nested suites recursively
        for nested_suite in suite.get("suites", []):
            failures.extend(self._extract_suite_failures(nested_suite))

        # Process tests in this suite
        for spec in suite.get("specs", []):
            failures.extend(self._extract_spec_failures(spec, suite.get("title", "")))

        return failures

    def _extract_spec_failures(self, spec: Dict[str, Any], suite_title: str) -> List[TestFailure]:
        """Extract failures from a test spec."""
        failures = []

        for test in spec.get("tests", []):
            for result in test.get("results", []):
                if result.get("status") in ["failed", "timedOut"]:
                    failure = self._create_test_failure(test, result, spec, suite_title)
                    if failure:
                        failures.append(failure)

        return failures

    def _create_test_failure(
        self, test: Dict[str, Any], result: Dict[str, Any], spec: Dict[str, Any], suite_title: str
    ) -> Optional[TestFailure]:
        """Create a TestFailure object from test result data."""
        try:
            # Extract error information
            error_info = result.get("error", {})
            error_message = error_info.get("message", "Unknown error")
            stack_trace = error_info.get("stack", "")

            # Extract location information
            location = test.get("location", {})
            file_path = location.get("file", spec.get("file", "unknown"))
            line_number = location.get("line")

            # Extract test metadata
            test_title = test.get("title", "Unknown test")
            full_title = f"{suite_title} > {test_title}" if suite_title else test_title

            duration = result.get("duration", 0)
            retry_count = result.get("retry", 0)

            # Extract project information if available
            project_name = None
            browser = None
            if "projectName" in result:
                project_name = result["projectName"]
            elif "workerIndex" in result:
                # Try to infer project from worker index
                project_name = f"worker-{result['workerIndex']}"

            return TestFailure(
                test_name=full_title,
                file_path=file_path,
                line_number=line_number,
                error_message=error_message,
                stack_trace=stack_trace,
                duration=duration,
                retry_count=retry_count,
                project_name=project_name,
                browser=browser,
            )

        except Exception as e:
            print(f"Warning: Failed to parse test failure: {e}", file=sys.stderr)
            return None


@error_handler(setup_error_handling())
def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Parse Playwright JSON report and extract failures"
    )
    parser.add_argument("--report-path", required=True, help="Path to the Playwright JSON report")
    parser.add_argument("--max-failures", help="Maximum number of failures to extract")
    parser.add_argument("--output-file", required=True, help="Output file for failure summary JSON")

    args = parser.parse_args()

    # Setup error handling
    error_handler_instance = setup_error_handling()
    validator = ConfigValidator(error_handler_instance)

    # Validate inputs
    validator.validate_report_path(args.report_path)
    max_failures = None
    if args.max_failures:
        max_failures = validator.validate_max_failures(args.max_failures)

    # Parse the report
    parser_instance = PlaywrightReportParser(args.report_path, error_handler_instance)
    summary = parser_instance.parse_failures(max_failures)

    # Convert to JSON-serializable format
    summary_dict = asdict(summary)

    # Write output
    try:
        with open(args.output_file, "w", encoding="utf-8") as f:
            json.dump(summary_dict, f, indent=2, ensure_ascii=False)
    except Exception as e:
        raise ActionError(
            code=ErrorCodes.FILE_WRITE_ERROR,
            message=f"Failed to write output file: {e}",
            severity=ErrorSeverity.HIGH,
            suggestions=["Check file permissions and disk space"],
        )

    # Set GitHub Actions outputs (using new format)
    from utils import set_github_output

    set_github_output("failures-count", str(summary.failed_tests))

    # Exit with appropriate code
    if summary.failed_tests > 0:
        print(f"Found {summary.failed_tests} test failures")
        sys.exit(1)  # Indicate failures were found
    else:
        print("No test failures found")
        sys.exit(0)


if __name__ == "__main__":
    main()
