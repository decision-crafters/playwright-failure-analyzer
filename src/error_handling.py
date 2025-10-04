#!/usr/bin/env python3
"""
Error Handling and Validation

This module provides comprehensive error handling, validation, and recovery
mechanisms for the Playwright Failure Bundler action.
"""

import json
import logging
import os
import sys
import traceback
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional


class ErrorSeverity(Enum):
    """Error severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ActionError:
    """Represents an error that occurred during action execution."""

    code: str
    message: str
    severity: ErrorSeverity
    details: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None


class ErrorCodes:
    """Standard error codes for the action."""

    # File and I/O errors
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_READ_ERROR = "FILE_READ_ERROR"
    FILE_WRITE_ERROR = "FILE_WRITE_ERROR"
    INVALID_JSON = "INVALID_JSON"

    # Configuration errors
    MISSING_TOKEN = "MISSING_TOKEN"
    INVALID_TOKEN = "INVALID_TOKEN"
    MISSING_REPOSITORY = "MISSING_REPOSITORY"
    INVALID_CONFIG = "INVALID_CONFIG"

    # GitHub API errors
    API_RATE_LIMIT = "API_RATE_LIMIT"
    API_PERMISSION_DENIED = "API_PERMISSION_DENIED"
    API_NOT_FOUND = "API_NOT_FOUND"
    API_SERVER_ERROR = "API_SERVER_ERROR"
    API_NETWORK_ERROR = "API_NETWORK_ERROR"

    # Report parsing errors
    INVALID_REPORT_FORMAT = "INVALID_REPORT_FORMAT"
    NO_TEST_RESULTS = "NO_TEST_RESULTS"
    CORRUPTED_REPORT = "CORRUPTED_REPORT"

    # General errors
    UNEXPECTED_ERROR = "UNEXPECTED_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"


class ActionErrorHandler:
    """Centralized error handling for the action."""

    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.setup_logging()

    def setup_logging(self):
        """Setup logging configuration."""
        level = logging.DEBUG if self.debug_mode else logging.INFO
        logging.basicConfig(
            level=level,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stderr)],
        )
        self.logger = logging.getLogger(__name__)

    def handle_error(self, error: ActionError) -> None:
        """Handle an action error with appropriate logging and exit."""
        self.logger.error(f"[{error.code}] {error.message}")

        if error.details:
            self.logger.debug(f"Error details: {json.dumps(error.details, indent=2)}")

        if error.suggestions:
            print("\n💡 Suggestions:", file=sys.stderr)
            for suggestion in error.suggestions:
                print(f"  • {suggestion}", file=sys.stderr)

        # Set GitHub Actions error annotation
        print(f"::error title={error.code}::{error.message}")

        # Exit with appropriate code based on severity
        exit_code = {
            ErrorSeverity.LOW: 0,
            ErrorSeverity.MEDIUM: 1,
            ErrorSeverity.HIGH: 2,
            ErrorSeverity.CRITICAL: 3,
        }.get(error.severity, 1)

        sys.exit(exit_code)

    def create_error(
        self,
        code: str,
        message: str,
        severity: ErrorSeverity,
        details: Dict[str, Any] = None,
        suggestions: List[str] = None,
    ) -> ActionError:
        """Create a new ActionError with standard formatting."""
        return ActionError(
            code=code, message=message, severity=severity, details=details, suggestions=suggestions
        )


def error_handler(handler: ActionErrorHandler):
    """Decorator for automatic error handling in functions."""

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ActionError as e:
                handler.handle_error(e)
            except Exception as e:
                # Convert unexpected exceptions to ActionError
                error = handler.create_error(
                    code=ErrorCodes.UNEXPECTED_ERROR,
                    message=f"Unexpected error in {func.__name__}: {str(e)}",
                    severity=ErrorSeverity.CRITICAL,
                    details={
                        "function": func.__name__,
                        "exception_type": type(e).__name__,
                        "traceback": traceback.format_exc() if handler.debug_mode else None,
                    },
                )
                handler.handle_error(error)

        return wrapper

    return decorator


class ConfigValidator:
    """Validates action configuration and inputs."""

    def __init__(self, error_handler: ActionErrorHandler):
        self.error_handler = error_handler

    def validate_github_token(self, token: str) -> None:
        """Validate GitHub token format and presence."""
        if not token:
            raise ActionError(
                code=ErrorCodes.MISSING_TOKEN,
                message="GitHub token is required but not provided",
                severity=ErrorSeverity.CRITICAL,
                suggestions=[
                    "Ensure GITHUB_TOKEN is set in your workflow",
                    "Check that the token is passed to the action correctly",
                    "Verify the token has not expired",
                ],
            )

        # Basic format validation
        valid_prefixes = ["ghp_", "gho_", "ghu_", "ghs_", "ghr_"]
        if not any(token.startswith(prefix) for prefix in valid_prefixes) and len(token) != 40:
            raise ActionError(
                code=ErrorCodes.INVALID_TOKEN,
                message="GitHub token appears to have invalid format",
                severity=ErrorSeverity.HIGH,
                suggestions=[
                    "Verify the token is a valid GitHub personal access token",
                    "Check that the token hasn't been truncated or modified",
                    "Generate a new token if necessary",
                ],
            )

    def validate_repository(self, repository: str) -> None:
        """Validate repository format."""
        if not repository:
            raise ActionError(
                code=ErrorCodes.MISSING_REPOSITORY,
                message="Repository information is required but not available",
                severity=ErrorSeverity.CRITICAL,
                suggestions=[
                    "Ensure this action is running in a GitHub Actions workflow",
                    "Check that GITHUB_REPOSITORY environment variable is set",
                ],
            )

        if "/" not in repository or repository.count("/") != 1:
            raise ActionError(
                code=ErrorCodes.INVALID_CONFIG,
                message=f"Invalid repository format: {repository}",
                severity=ErrorSeverity.HIGH,
                details={"repository": repository},
                suggestions=[
                    "Repository should be in format 'owner/repo'",
                    "Check GITHUB_REPOSITORY environment variable",
                ],
            )

    def validate_report_path(self, report_path: str) -> None:
        """Validate that the report file exists and is readable."""
        if not report_path:
            raise ActionError(
                code=ErrorCodes.INVALID_CONFIG,
                message="Report path is required",
                severity=ErrorSeverity.HIGH,
                suggestions=["Specify a valid path to the Playwright JSON report"],
            )

        if not os.path.exists(report_path):
            raise ActionError(
                code=ErrorCodes.FILE_NOT_FOUND,
                message=f"Playwright report file not found: {report_path}",
                severity=ErrorSeverity.HIGH,
                details={"report_path": report_path},
                suggestions=[
                    "Ensure Playwright tests have run and generated a JSON report",
                    "Check the report path configuration",
                    "Verify the report file wasn't deleted or moved",
                    "Make sure Playwright is configured to output JSON reports",
                ],
            )

        if not os.access(report_path, os.R_OK):
            raise ActionError(
                code=ErrorCodes.FILE_READ_ERROR,
                message=f"Cannot read report file: {report_path}",
                severity=ErrorSeverity.HIGH,
                details={"report_path": report_path},
                suggestions=[
                    "Check file permissions",
                    "Ensure the file is not locked by another process",
                ],
            )

    def validate_max_failures(self, max_failures: str) -> int:
        """Validate and convert max_failures parameter."""
        try:
            value = int(max_failures)
            if value < 1:
                raise ValueError("Must be positive")
            if value > 100:
                self.error_handler.logger.warning(
                    f"max_failures is very high ({value}). Consider using a lower value."
                )
            return value
        except ValueError:
            raise ActionError(
                code=ErrorCodes.INVALID_CONFIG,
                message=f"Invalid max_failures value: {max_failures}",
                severity=ErrorSeverity.MEDIUM,
                details={"max_failures": max_failures},
                suggestions=[
                    "max_failures must be a positive integer",
                    "Typical values are between 1 and 10",
                ],
            )


class ReportValidator:
    """Validates Playwright report structure and content."""

    def __init__(self, error_handler: ActionErrorHandler):
        self.error_handler = error_handler

    def validate_report_structure(self, report_data: Dict[str, Any]) -> None:
        """Validate that the report has the expected structure."""
        required_fields = ["stats", "suites"]
        missing_fields = [field for field in required_fields if field not in report_data]

        if missing_fields:
            raise ActionError(
                code=ErrorCodes.INVALID_REPORT_FORMAT,
                message=f"Report missing required fields: {', '.join(missing_fields)}",
                severity=ErrorSeverity.HIGH,
                details={
                    "missing_fields": missing_fields,
                    "available_fields": list(report_data.keys()),
                },
                suggestions=[
                    "Ensure Playwright is configured to generate JSON reports",
                    "Check that the report file is complete and not truncated",
                    "Verify you're using a compatible version of Playwright",
                ],
            )

        # Validate stats structure
        stats = report_data.get("stats", {})
        if not isinstance(stats, dict):
            raise ActionError(
                code=ErrorCodes.CORRUPTED_REPORT,
                message="Report stats section is not in expected format",
                severity=ErrorSeverity.HIGH,
                suggestions=["Regenerate the Playwright report"],
            )

        # Validate suites structure
        suites = report_data.get("suites", [])
        if not isinstance(suites, list):
            raise ActionError(
                code=ErrorCodes.CORRUPTED_REPORT,
                message="Report suites section is not in expected format",
                severity=ErrorSeverity.HIGH,
                suggestions=["Regenerate the Playwright report"],
            )

    def validate_has_test_results(self, report_data: Dict[str, Any]) -> None:
        """Validate that the report contains test results."""
        stats = report_data.get("stats", {})
        total_tests = (
            stats.get("expected", 0) + stats.get("unexpected", 0) + stats.get("skipped", 0)
        )

        if total_tests == 0:
            raise ActionError(
                code=ErrorCodes.NO_TEST_RESULTS,
                message="No test results found in the report",
                severity=ErrorSeverity.MEDIUM,
                suggestions=[
                    "Ensure tests were actually executed",
                    "Check that test files are being discovered by Playwright",
                    "Verify the test configuration is correct",
                ],
            )


class GitHubAPIErrorHandler:
    """Specialized error handling for GitHub API interactions."""

    def __init__(self, error_handler: ActionErrorHandler):
        self.error_handler = error_handler

    def handle_api_error(self, response: "requests.Response") -> None:
        """Handle GitHub API error responses."""
        status_code = response.status_code

        if status_code == 401:
            raise ActionError(
                code=ErrorCodes.INVALID_TOKEN,
                message="GitHub API authentication failed",
                severity=ErrorSeverity.CRITICAL,
                details={"status_code": status_code, "response": response.text},
                suggestions=[
                    "Check that GITHUB_TOKEN is valid and not expired",
                    "Ensure the token has the required permissions",
                    "Generate a new token if necessary",
                ],
            )

        elif status_code == 403:
            if "rate limit" in response.text.lower():
                raise ActionError(
                    code=ErrorCodes.API_RATE_LIMIT,
                    message="GitHub API rate limit exceeded",
                    severity=ErrorSeverity.MEDIUM,
                    details={"status_code": status_code, "response": response.text},
                    suggestions=[
                        "Wait for the rate limit to reset",
                        "Consider using a different token with higher limits",
                        "Reduce the frequency of API calls",
                    ],
                )
            else:
                raise ActionError(
                    code=ErrorCodes.API_PERMISSION_DENIED,
                    message="Insufficient permissions for GitHub API operation",
                    severity=ErrorSeverity.CRITICAL,
                    details={"status_code": status_code, "response": response.text},
                    suggestions=[
                        "Ensure the token has 'issues: write' permissions",
                        "Check repository access permissions",
                        "Verify the workflow has the correct permissions block",
                    ],
                )

        elif status_code == 404:
            raise ActionError(
                code=ErrorCodes.API_NOT_FOUND,
                message="GitHub API resource not found",
                severity=ErrorSeverity.HIGH,
                details={"status_code": status_code, "response": response.text},
                suggestions=[
                    "Check that the repository exists and is accessible",
                    "Verify the repository name is correct",
                    "Ensure the token has access to the repository",
                ],
            )

        elif status_code >= 500:
            raise ActionError(
                code=ErrorCodes.API_SERVER_ERROR,
                message="GitHub API server error",
                severity=ErrorSeverity.MEDIUM,
                details={"status_code": status_code, "response": response.text},
                suggestions=[
                    "This is likely a temporary issue with GitHub",
                    "Try running the action again",
                    "Check GitHub's status page for known issues",
                ],
            )

        else:
            raise ActionError(
                code=ErrorCodes.API_SERVER_ERROR,
                message=f"GitHub API error: {status_code}",
                severity=ErrorSeverity.HIGH,
                details={"status_code": status_code, "response": response.text},
                suggestions=[
                    "Check the GitHub API documentation",
                    "Verify the request format is correct",
                ],
            )


def setup_error_handling(debug_mode: bool = False) -> ActionErrorHandler:
    """Setup centralized error handling for the action."""
    debug_env = os.getenv("RUNNER_DEBUG", "").lower() in ("1", "true")
    return ActionErrorHandler(debug_mode or debug_env)
