# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a GitHub Action that analyzes Playwright test failures and creates comprehensive GitHub issues with error details. The action has two main execution phases:
1. **Parse Report** (`parse_report.py`): Parses Playwright JSON reports and extracts failure data
2. **Create Issue** (`create_issue.py`): Creates or updates GitHub issues with formatted failure information and optional AI analysis

## Core Architecture

### Data Flow
```
Playwright JSON Report → parse_report.py → /tmp/failure_summary.json → create_issue.py → GitHub Issue
```

### Module Structure

**`parse_report.py`** - Report parsing module
- `PlaywrightReportParser`: Main parser class that loads and validates JSON reports
- `TestFailure` dataclass: Represents individual test failures with metadata
- `FailureSummary` dataclass: Aggregates all failures and statistics
- Recursively traverses nested test suites to extract all failures
- Outputs failure summary as JSON to `/tmp/failure_summary.json`

**`create_issue.py`** - GitHub issue creation module
- `GitHubAPIClient`: Handles all GitHub API interactions with retry logic and rate limiting
- `IssueFormatter`: Formats failure data into markdown for GitHub issues
- `IssueManager`: Manages issue creation and deduplication
- Conditionally imports `ai_analysis` module (optional dependency)

**`ai_analysis.py`** - AI-powered failure analysis (optional)
- `AIAnalyzer`: Uses LiteLLM to analyze test failures with various LLM providers
- `AIAnalysisResult` dataclass: Structured AI analysis output
- `AIAnalysisFormatter`: Formats AI analysis for GitHub issue inclusion
- Requires environment variables: `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`

**`error_handling.py`** - Comprehensive error handling
- `ActionErrorHandler`: Centralized error handling with severity levels
- `ConfigValidator`: Validates inputs (tokens, paths, repository format)
- `ReportValidator`: Validates Playwright report structure
- `GitHubAPIErrorHandler`: Specialized GitHub API error handling
- Uses `@error_handler` decorator for automatic error wrapping

**`utils.py`** - Utility functions
- GitHub context extraction from environment variables
- Text formatting, sanitization, and truncation for GitHub issues
- Duration formatting, path manipulation, stack trace cleaning
- `set_github_output()`: Sets GitHub Actions output variables (uses new GITHUB_OUTPUT format)

## Development Commands

### Testing
```bash
# Run all tests with linting and type checking
python tests/run_tests.py

# Run specific test file
python -m pytest tests/test_parse_report.py -v

# Run with coverage report
python -m pytest tests/ --cov=src --cov-report=html
```

### Code Quality
```bash
# Format code (line length: 100)
black src/ tests/

# Sort imports
isort src/ tests/

# Lint (ignores E501, W503)
flake8 src/ tests/ --max-line-length=100 --ignore=E501,W503
```

### Local Testing
```bash
# Test report parsing
python src/parse_report.py \
  --report-path test-results/results.json \
  --max-failures 5 \
  --output-file /tmp/failure_summary.json

# Test issue creation (requires GITHUB_TOKEN)
GITHUB_TOKEN=<token> GITHUB_REPOSITORY=owner/repo \
python src/create_issue.py \
  --summary-file /tmp/failure_summary.json \
  --issue-title "Test Failures" \
  --deduplicate true
```

## Key Implementation Details

### Error Handling Pattern
All entry point functions use the `@error_handler` decorator:
```python
@error_handler(setup_error_handling())
def main():
    # Function implementation
```

This provides:
- Automatic error catching and formatting
- GitHub Actions annotations (::error::)
- Severity-based exit codes
- Actionable suggestions in error messages

### GitHub API Retry Logic
The `GitHubAPIClient._make_request()` method implements:
- Exponential backoff (2^attempt seconds)
- Rate limit detection and automatic waiting (Retry-After header)
- 3 retry attempts by default
- Status code-specific error handling via `GitHubAPIErrorHandler`

### Issue Deduplication
When `deduplicate=true`, `IssueManager.create_or_update_issue()`:
1. Searches for open issues with exact title match
2. If found, updates existing issue body with new failure data
3. If not found, creates new issue

### AI Analysis Integration
AI analysis is optional and conditional:
1. Checks if `AI_ANALYSIS_AVAILABLE` (import success)
2. Only runs if `--ai-analysis true` and API keys present
3. Limits to first 5 failures to avoid token limits
4. Expects JSON response but falls back to text parsing
5. Inserts AI section between summary stats and failure details

### Test Suite Traversal
`PlaywrightReportParser._extract_suite_failures()` recursively:
1. Processes nested suites depth-first
2. Extracts specs from current suite
3. Filters for 'failed' or 'timedOut' status
4. Applies `max_failures` limit after collecting all failures

## Environment Variables

**Required:**
- `GITHUB_TOKEN`: Token with `issues:write` permissions
- `GITHUB_REPOSITORY`: Format `owner/repo`

**Optional:**
- `RUNNER_DEBUG`: Set to `1` or `true` for debug logging
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`: For AI analysis
- `AI_MODEL`: Override default model (default: `gpt-4.1-mini`)

**GitHub Actions Context (auto-set):**
- `GITHUB_SHA`, `GITHUB_REF`, `GITHUB_RUN_ID`, `GITHUB_ACTOR`, `GITHUB_WORKFLOW`

## Dependencies

**Core:**
- `requests>=2.28.0`: GitHub API interaction
- `litellm>=1.40.0`: Multi-provider LLM interface
- `openai>=1.0.0`: OpenAI client (for LiteLLM)

**Development:**
- `pytest`, `flake8`, `mypy`, `black`, `isort`

## Testing Strategy

The test suite follows this pattern:
- **Unit tests**: Mock external dependencies (GitHub API, file I/O)
- **Integration tests**: Test component interactions with realistic data
- Test data uses actual Playwright report structures
- `tests/run_tests.py` orchestrates linting → type checking → unit tests

## Code Style

- **Line length**: 100 characters (not PEP 8's 79)
- **String quotes**: Double quotes for user-facing strings
- **Imports**: Grouped by standard library, third-party, local modules
- **Dataclasses**: Preferred over dictionaries for structured data
- **Type hints**: Used throughout (validated by mypy with `--ignore-missing-imports`)

## Action Workflow Integration

This action is designed to run after Playwright tests in CI:
```yaml
- name: Run Playwright tests
  run: npx playwright test --reporter=json
  continue-on-error: true  # Important: don't fail job on test failures

- name: Bundle test failures
  if: always()  # Run even if tests failed
  uses: ./
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    report-path: 'test-results/results.json'
```

The composite action (`action.yml`) executes:
1. Setup Python 3.11
2. Install requirements.txt
3. Run parse_report.py (outputs to `/tmp/failure_summary.json`)
4. Run create_issue.py (consumes summary, creates issue)
