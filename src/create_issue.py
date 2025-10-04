#!/usr/bin/env python3
"""
GitHub Issue Creator

This module handles creating and managing GitHub issues for test failures.
"""

import argparse
import json
import os
import time
from typing import Any, Dict, List, Optional, Tuple

import requests

from error_handling import (
    ActionError,
    ActionErrorHandler,
    ConfigValidator,
    ErrorCodes,
    ErrorSeverity,
    GitHubAPIErrorHandler,
    error_handler,
    setup_error_handling,
)
from utils import (
    format_duration,
    format_stack_trace,
    format_timestamp,
    get_branch_name,
    get_github_context,
    get_relative_path,
    parse_comma_separated,
    sanitize_for_github,
    set_github_output,
    truncate_text,
)

try:
    from ai_analysis import AIAnalysisFormatter, analyze_failures_with_ai

    AI_ANALYSIS_AVAILABLE = True
except ImportError:
    # AI analysis not available - create dummy functions
    def analyze_failures_with_ai(*args, **kwargs):
        return None

    class AIAnalysisFormatter:
        @staticmethod
        def format_analysis_section(analysis):
            return ""

    AI_ANALYSIS_AVAILABLE = False


class GitHubAPIClient:
    """Client for interacting with the GitHub API."""

    def __init__(self, token: str, repository: str, error_handler: ActionErrorHandler):
        self.token = token
        self.repository = repository
        self.base_url = "https://api.github.com"
        self.error_handler = error_handler
        self.api_error_handler = GitHubAPIErrorHandler(error_handler)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "playwright-failure-bundler/1.0",
            }
        )

    def _make_request(
        self, method: str, endpoint: str, data: Dict = None, max_retries: int = 3
    ) -> requests.Response:
        """Make a request to the GitHub API with retry logic."""
        url = f"{self.base_url}{endpoint}"

        for attempt in range(max_retries):
            try:
                if method.upper() == "GET":
                    response = self.session.get(url, params=data)
                elif method.upper() == "POST":
                    response = self.session.post(url, json=data)
                elif method.upper() == "PATCH":
                    response = self.session.patch(url, json=data)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    print(f"Rate limited. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue

                # Handle other errors
                if response.status_code >= 400:
                    self.api_error_handler.handle_api_error(response)

                return response

            except requests.RequestException as e:
                if attempt == max_retries - 1:
                    raise
                print(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(2**attempt)  # Exponential backoff

        raise RuntimeError("Max retries exceeded")

    def search_issues(self, query: str) -> List[Dict[str, Any]]:
        """Search for issues matching the given query."""
        endpoint = "/search/issues"
        params = {"q": f"repo:{self.repository} {query}", "sort": "created", "order": "desc"}

        response = self._make_request("GET", endpoint, params)
        return response.json().get("items", [])

    def create_issue(
        self, title: str, body: str, labels: List[str] = None, assignees: List[str] = None
    ) -> Dict[str, Any]:
        """Create a new GitHub issue."""
        endpoint = f"/repos/{self.repository}/issues"

        data = {"title": title, "body": body}

        if labels:
            data["labels"] = labels

        if assignees:
            data["assignees"] = assignees

        response = self._make_request("POST", endpoint, data)
        return response.json()

    def update_issue(
        self, issue_number: int, title: str = None, body: str = None, state: str = None
    ) -> Dict[str, Any]:
        """Update an existing GitHub issue."""
        endpoint = f"/repos/{self.repository}/issues/{issue_number}"

        data = {}
        if title:
            data["title"] = title
        if body:
            data["body"] = body
        if state:
            data["state"] = state

        response = self._make_request("PATCH", endpoint, data)
        return response.json()


class IssueFormatter:
    """Formats test failure data into GitHub issue content."""

    def __init__(self, github_context: Dict[str, str]):
        self.github_context = github_context

    def format_issue_body(self, summary: Dict[str, Any], ai_analysis=None) -> str:
        """Format the complete issue body from failure summary."""
        sections = [
            self._format_header(summary),
            self._format_summary_stats(summary),
            self._format_failure_details(summary["failures"]),
            self._format_debug_info(summary),
            self._format_next_steps(),
        ]

        # Add AI analysis if available
        if ai_analysis:
            ai_section = AIAnalysisFormatter.format_analysis_section(ai_analysis)
            if ai_section:
                # Insert AI analysis after summary stats but before failure details
                sections.insert(2, ai_section)

        body = "\n\n".join(sections)
        return truncate_text(sanitize_for_github(body))

    def _format_header(self, summary: Dict[str, Any]) -> str:
        """Format the issue header."""
        failed_count = summary["failed_tests"]
        total_count = summary["total_tests"]

        return f"""# 🚨 Playwright Test Failures Detected

**Summary**: {failed_count} test failure{'s' if failed_count != 1 else ''} detected out of {total_count} total tests."""

    def _format_summary_stats(self, summary: Dict[str, Any]) -> str:
        """Format the summary statistics section."""
        stats = f"""## 📊 Test Run Summary

| Metric | Value |
|--------|-------|
| **Total Tests** | {summary['total_tests']} |
| **Passed** | ✅ {summary['passed_tests']} |
| **Failed** | ❌ {summary['failed_tests']} |
| **Skipped** | ⏭️ {summary['skipped_tests']} |
| **Duration** | {format_duration(summary['duration'])} |"""

        return stats

    def _format_failure_details(self, failures: List[Any]) -> str:
        """Format the detailed failure information."""
        if not failures:
            return "## 📋 Failure Details\n\nNo failure details available."

        details = ["## 📋 Failure Details"]

        for i, failure in enumerate(failures, 1):
            # Handle both dict and object formats
            if hasattr(failure, "test_name"):
                # TestFailure object
                test_name = failure.test_name
                file_path = get_relative_path(failure.file_path or "")
                error_message = failure.error_message or "No error message"
                stack_trace = format_stack_trace(failure.stack_trace or "")
                duration = format_duration(failure.duration or 0)
                retry_count = failure.retry_count or 0
            else:
                # Dictionary format
                test_name = failure.get("test_name", "Unknown Test")
                file_path = get_relative_path(failure.get("file_path", ""))
                error_message = failure.get("error_message", "No error message")
                stack_trace = format_stack_trace(failure.get("stack_trace", ""))
                duration = format_duration(failure.get("duration", 0))
                retry_count = failure.get("retry_count", 0)

            failure_section = f"""### {i}. {test_name}

- **File**: `{file_path}`
- **Duration**: {duration}
- **Retries**: {retry_count}
- **Error**: `{error_message}`

**Stack Trace**:
```
{stack_trace}
```"""

            details.append(failure_section)

        return "\n\n".join(details)

    def _format_debug_info(self, summary: Dict[str, Any]) -> str:
        """Format debug and context information."""
        context = self.github_context
        metadata = summary.get("metadata", {})

        debug_info = f"""## 🔍 Debug Information

| Field | Value |
|-------|-------|
| **Repository** | {context['repository']} |
| **Commit** | `{context['sha'][:8]}` |
| **Branch** | `{get_branch_name()}` |
| **Run ID** | [{context['run_id']}]({context['server_url']}/{context['repository']}/actions/runs/{context['run_id']}) |
| **Workflow** | {context['workflow']} |
| **Actor** | @{context['actor']} |
| **Timestamp** | {format_timestamp()} |"""

        if metadata.get("playwright_version"):
            debug_info += f"\n| **Playwright Version** | {metadata['playwright_version']} |"

        if metadata.get("projects"):
            projects = ", ".join(metadata["projects"])
            debug_info += f"\n| **Projects** | {projects} |"

        if metadata.get("workers"):
            debug_info += f"\n| **Workers** | {metadata['workers']} |"

        return debug_info

    def _format_next_steps(self) -> str:
        """Format the next steps section."""
        return """## 🚀 Next Steps

1. **Review the failure patterns** above to identify common issues
2. **Check recent changes** that might have introduced regressions
3. **Run tests locally** to reproduce the failures
4. **Verify test environment** and dependencies are up to date
5. **Consider infrastructure changes** that might affect test stability

💡 **Tip**: Look for patterns in the failed tests - are they all in the same area of the application?"""


class IssueManager:
    """Manages the creation and deduplication of GitHub issues."""

    def __init__(self, github_client: GitHubAPIClient, formatter: IssueFormatter):
        self.github_client = github_client
        self.formatter = formatter

    def create_or_update_issue(
        self,
        summary: Dict[str, Any],
        title: str,
        labels: List[str],
        assignees: List[str],
        deduplicate: bool = True,
        ai_analysis=None,
    ) -> Tuple[int, str, bool]:
        """
        Create a new issue or update existing one.

        Returns:
            Tuple of (issue_number, issue_url, was_created)
        """
        body = self.formatter.format_issue_body(summary, ai_analysis)

        # Check for existing issues if deduplication is enabled
        if deduplicate:
            existing_issue = self._find_existing_issue(title)
            if existing_issue:
                print(
                    f"Found existing issue #{existing_issue['number']}: {existing_issue['title']}"
                )
                # Update the existing issue with new information
                self.github_client.update_issue(existing_issue["number"], body=body)
                return existing_issue["number"], existing_issue["html_url"], False

        # Create new issue
        print(f"Creating new issue: {title}")
        issue = self.github_client.create_issue(title, body, labels, assignees)
        return issue["number"], issue["html_url"], True

    def _find_existing_issue(self, title: str) -> Optional[Dict[str, Any]]:
        """Find an existing open issue with the same title."""
        # Search for open issues with similar title
        query = f'is:open is:issue in:title "{title}"'
        issues = self.github_client.search_issues(query)

        # Look for exact title match
        for issue in issues:
            if issue["title"] == title:
                return issue

        return None


@error_handler(setup_error_handling())
def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Create GitHub issue from test failure summary")
    parser.add_argument("--summary-file", required=True, help="Path to failure summary JSON file")
    parser.add_argument("--issue-title", required=True, help="Title for the GitHub issue")
    parser.add_argument("--issue-labels", default="", help="Comma-separated list of labels")
    parser.add_argument("--assignees", default="", help="Comma-separated list of assignees")
    parser.add_argument(
        "--deduplicate", default="true", help="Whether to check for existing issues"
    )
    parser.add_argument(
        "--ai-analysis", default="false", help="Enable AI analysis (future feature)"
    )

    args = parser.parse_args()

    # Setup error handling
    error_handler_instance = setup_error_handling()
    validator = ConfigValidator(error_handler_instance)

    # Get GitHub context
    github_context = get_github_context()
    github_token = os.getenv("GITHUB_TOKEN")
    repository = github_context["repository"]

    # Validate configuration
    validator.validate_github_token(github_token)
    validator.validate_repository(repository)

    # Load failure summary
    if not os.path.exists(args.summary_file):
        raise ActionError(
            code=ErrorCodes.FILE_NOT_FOUND,
            message=f"Failure summary file not found: {args.summary_file}",
            severity=ErrorSeverity.HIGH,
            suggestions=["Ensure the parse_report.py script ran successfully"],
        )

    try:
        with open(args.summary_file, "r", encoding="utf-8") as f:
            summary = json.load(f)
    except json.JSONDecodeError as e:
        raise ActionError(
            code=ErrorCodes.INVALID_JSON,
            message=f"Invalid JSON in summary file: {e}",
            severity=ErrorSeverity.HIGH,
            suggestions=["Check that the parse_report.py script completed successfully"],
        )

    # Check if there are any failures to report
    if summary["failed_tests"] == 0:
        print("No test failures found. Skipping issue creation.")
        set_github_output("issue-number", "")
        set_github_output("issue-url", "")
        return

    # Parse configuration
    labels = parse_comma_separated(args.issue_labels)
    assignees = parse_comma_separated(args.assignees)
    deduplicate = args.deduplicate.lower() == "true"
    ai_analysis_enabled = args.ai_analysis.lower() == "true"

    # Run AI analysis if enabled and available
    ai_analysis = None
    if ai_analysis_enabled and summary["failed_tests"] > 0:
        if AI_ANALYSIS_AVAILABLE:
            print("Running AI analysis of test failures...")
            ai_analysis = analyze_failures_with_ai(
                summary["failures"], summary["metadata"], enabled=True
            )
            if ai_analysis:
                print(f"AI analysis completed with {ai_analysis.confidence_score:.1%} confidence")
            else:
                print("AI analysis failed or not configured")
        else:
            print("AI analysis requested but LiteLLM not available")

    # Initialize components
    github_client = GitHubAPIClient(github_token, repository, error_handler_instance)
    formatter = IssueFormatter(github_context)
    issue_manager = IssueManager(github_client, formatter)

    # Create or update issue
    issue_number, issue_url, was_created = issue_manager.create_or_update_issue(
        summary, args.issue_title, labels, assignees, deduplicate, ai_analysis
    )

    # Set outputs
    set_github_output("issue-number", str(issue_number))
    set_github_output("issue-url", issue_url)

    # Print results
    action = "Created" if was_created else "Updated"
    print(f"{action} issue #{issue_number}: {issue_url}")


if __name__ == "__main__":
    main()
