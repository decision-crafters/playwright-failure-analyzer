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

        # Type narrowing: report_data is guaranteed to be Dict after load_report()
        assert (
            self.report_data is not None
        ), "report_data must be loaded before parsing"  # nosec B101

        # Validate report structure
        self.validator.validate_report_structure(self.report_data)
        self.validator.validate_playwright_schema(self.report_data)
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
        self,
        test: Dict[str, Any],
        result: Dict[str, Any],
        spec: Dict[str, Any],
        suite_title: str,
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
    parser.add_argument(
        "--export-structured-json",
        help="Export structured JSON optimized for auto-fix tools",
        action="store_true",
    )
    parser.add_argument(
        "--structured-json-path",
        help="Path for structured JSON export (for auto-fix integration)",
        default="playwright-failures-structured.json",
    )

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

    # Export structured JSON if requested (for auto-fix tools)
    if args.export_structured_json:
        try:
            structured_data = _create_structured_export(summary)
            with open(args.structured_json_path, "w", encoding="utf-8") as f:
                json.dump(structured_data, f, indent=2, ensure_ascii=False)
            print(f"Structured JSON exported to: {args.structured_json_path}")
        except Exception as e:
            print(f"Warning: Failed to export structured JSON: {e}", file=sys.stderr)

    # Set GitHub Actions outputs (using new format)
    from utils import set_github_output

    set_github_output("failures-count", str(summary.failed_tests))
    if args.export_structured_json:
        set_github_output("structured-json-path", args.structured_json_path)

    # Print summary and exit successfully
    # Note: Finding failures is expected behavior, not an error condition
    if summary.failed_tests > 0:
        print(f"Found {summary.failed_tests} test failures")
    else:
        print("No test failures found")
    sys.exit(0)  # Exit successfully after parsing


def _create_structured_export(summary: FailureSummary) -> Dict[str, Any]:
    """
    Create structured JSON export optimized for auto-fix tools.

    This format is designed to be consumed by Dagger modules and other
    automated fixing tools. It includes:
    - Clean, machine-parseable failure data
    - File:line references for precise targeting
    - Error pattern classification
    - Metadata for context
    """
    failures_data = []

    for failure in summary.failures:
        failure_dict = {
            "test_name": failure.test_name,
            "file_path": failure.file_path,
            "line_number": failure.line_number,
            "error_message": failure.error_message,
            "error_type": _classify_error_type(failure.error_message),
            "stack_trace": failure.stack_trace,
            "duration_ms": failure.duration,
            "retry_count": failure.retry_count,
            "project_name": failure.project_name,
            "browser": failure.browser,
            # Add fields for auto-fix integration
            "fixability_hint": _get_fixability_hint(failure.error_message),
            "suggested_pattern": _detect_error_pattern(failure.error_message),
        }
        failures_data.append(failure_dict)

    return {
        "version": "1.0",
        "format": "playwright-failure-analyzer-structured",
        "generated_at": os.getenv("GITHUB_RUN_ID", "local"),
        "summary": {
            "total_tests": summary.total_tests,
            "passed_tests": summary.passed_tests,
            "failed_tests": summary.failed_tests,
            "skipped_tests": summary.skipped_tests,
            "duration_ms": summary.duration,
        },
        "failures": failures_data,
        "metadata": summary.metadata,
        "auto_fix_context": {
            "repository": os.getenv("GITHUB_REPOSITORY", "unknown"),
            "sha": os.getenv("GITHUB_SHA", "unknown"),
            "branch": os.getenv("GITHUB_REF_NAME", "unknown"),
            "workflow": os.getenv("GITHUB_WORKFLOW", "unknown"),
        },
    }


def _classify_error_type(error_message: str) -> str:
    """Classify the error type based on error message patterns."""
    error_lower = error_message.lower()

    if "timeout" in error_lower or "exceeded" in error_lower:
        return "timeout"
    elif "selector" in error_lower or "element" in error_lower:
        return "selector"
    elif "await" in error_lower or "promise" in error_lower:
        return "async"
    elif "type" in error_lower and ("error" in error_lower or "mismatch" in error_lower):
        return "type_error"
    elif "import" in error_lower or "module" in error_lower:
        return "import_error"
    elif "network" in error_lower or "fetch" in error_lower or "request" in error_lower:
        return "network"
    elif "assertion" in error_lower or "expect" in error_lower:
        return "assertion"
    else:
        return "unknown"


def _get_fixability_hint(error_message: str) -> str:
    """Provide a fixability hint based on error patterns."""
    error_type = _classify_error_type(error_message)

    fixability_map = {
        "timeout": "medium - consider increasing timeout or improving wait conditions",
        "selector": "high - check element selector matches DOM",
        "async": "high - likely missing await on async function",
        "type_error": "high - fix type annotation or value",
        "import_error": "high - fix import path or install dependency",
        "network": "low - may require infrastructure changes",
        "assertion": "low - may require business logic review",
        "unknown": "low - needs manual investigation",
    }

    return fixability_map.get(error_type, "unknown")


def _detect_error_pattern(error_message: str) -> str:
    """Detect specific error patterns for auto-fix pattern matching."""
    error_lower = error_message.lower()

    # Specific patterns that are commonly auto-fixable
    if "waiting for selector" in error_lower and "timeout" in error_lower:
        return "selector_timeout"
    elif "missing await" in error_lower or "did you forget to await" in error_lower:
        return "missing_await"
    elif "element is not attached" in error_lower:
        return "element_detached"
    elif "navigation timeout" in error_lower:
        return "navigation_timeout"
    elif "locator resolved to" in error_lower and "multiple" in error_lower:
        return "multiple_elements"
    elif "cannot find module" in error_lower:
        return "module_not_found"
    elif "type 'number' is not assignable" in error_lower:
        return "type_mismatch_number"
    elif "type 'string' is not assignable" in error_lower:
        return "type_mismatch_string"
    else:
        return "unknown_pattern"


if __name__ == "__main__":
    main()
