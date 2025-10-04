# Configuration Guide

This guide covers all configuration options and advanced usage patterns for the Playwright Failure Bundler action.

## Table of Contents

- [Basic Configuration](#basic-configuration)
- [Input Parameters](#input-parameters)
- [Output Variables](#output-variables)
- [Permissions](#permissions)
- [Advanced Patterns](#advanced-patterns)
- [Troubleshooting](#troubleshooting)

## Basic Configuration

The minimal configuration requires only a GitHub token:

```yaml
- name: Bundle test failures
  uses: your-org/playwright-failure-bundler@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

## Input Parameters

### Required Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `github-token` | GitHub token with `issues:write` permissions | `${{ secrets.GITHUB_TOKEN }}` |

### Optional Parameters

| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| `report-path` | Path to Playwright JSON report | `test-results/results.json` | `e2e-results/report.json` |
| `max-failures` | Maximum failures before creating issue | `3` | `5` |
| `issue-title` | Title for the GitHub issue | `Playwright Test Failures Detected` | `🚨 E2E Failures - Build #${{ github.run_number }}` |
| `issue-labels` | Comma-separated list of labels | `bug,playwright,test-failure` | `critical,e2e,regression` |
| `assignees` | Comma-separated list of assignees | `` | `qa-team,tech-lead` |
| `deduplicate` | Check for existing open issues | `true` | `false` |
| `ai-analysis` | Enable AI analysis (future feature) | `false` | `true` |

### Parameter Details

#### `report-path`

Specifies the location of the Playwright JSON report file. The path is relative to the workspace root.

**Common patterns:**
- Default Playwright output: `test-results/results.json`
- Custom output directory: `reports/playwright/results.json`
- Multiple test suites: `e2e-results/results.json`, `integration-results/results.json`

#### `max-failures`

Controls how many test failures are included in the issue details. This helps prevent extremely large issues when many tests fail.

**Recommendations:**
- For small test suites (< 50 tests): `5-10`
- For medium test suites (50-200 tests): `3-5`
- For large test suites (> 200 tests): `1-3`

#### `issue-title`

The title of the created GitHub issue. Supports GitHub Actions expressions.

**Best practices:**
- Include context: build number, branch, commit SHA
- Use emojis for visual distinction: 🚨, ⚠️, 🔥
- Keep under 80 characters for readability

**Examples:**
```yaml
issue-title: 'Test Failures - ${{ github.event_name }} on ${{ github.ref_name }}'
issue-title: '🚨 Critical E2E Failures - Build #${{ github.run_number }}'
issue-title: 'Playwright Failures - ${{ github.actor }} - ${{ github.sha }}'
```

#### `issue-labels`

Labels help categorize and filter issues in your repository.

**Recommended label strategies:**
- **Severity**: `critical`, `high`, `medium`, `low`
- **Type**: `bug`, `regression`, `flaky-test`
- **Component**: `playwright`, `e2e`, `integration`, `unit`
- **Environment**: `staging`, `production`, `ci`

#### `assignees`

GitHub usernames to automatically assign to the issue.

**Best practices:**
- Assign to teams or individuals responsible for test maintenance
- Use team mentions for broader visibility
- Consider rotating assignments to distribute workload

#### `deduplicate`

When enabled, the action searches for existing open issues with the same title before creating a new one.

**When to disable:**
- Integration tests where each failure should be tracked separately
- When using dynamic titles that change frequently
- For critical failures that always need immediate attention

## Output Variables

The action provides outputs that can be used in subsequent workflow steps:

| Output | Description | Example Value |
|--------|-------------|---------------|
| `issue-number` | Number of the created/updated issue | `42` |
| `issue-url` | URL of the created/updated issue | `https://github.com/owner/repo/issues/42` |
| `failures-count` | Number of failures detected | `3` |

### Using Outputs

```yaml
- name: Bundle test failures
  id: bundle-failures
  uses: your-org/playwright-failure-bundler@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}

- name: Comment on PR
  if: github.event_name == 'pull_request' && steps.bundle-failures.outputs.issue-number
  uses: actions/github-script@v7
  with:
    script: |
      github.rest.issues.createComment({
        issue_number: context.issue.number,
        owner: context.repo.owner,
        repo: context.repo.repo,
        body: `⚠️ Test failures detected. See issue #${{ steps.bundle-failures.outputs.issue-number }} for details.`
      })
```

## Permissions

The action requires specific permissions to function correctly:

### Minimal Permissions

```yaml
permissions:
  issues: write  # Required for creating/updating issues
```

### Recommended Permissions

```yaml
permissions:
  contents: read    # For accessing repository content
  issues: write     # For creating/updating issues
  pull-requests: write  # For commenting on PRs (if using outputs)
```

### Token Scopes

When using a personal access token instead of `GITHUB_TOKEN`:

**Required scopes:**
- `repo` (for private repositories)
- `public_repo` (for public repositories)

**Optional scopes:**
- `write:discussion` (for future discussion features)

## Advanced Patterns

### Multiple Test Suites

Handle different types of tests with separate configurations:

```yaml
- name: Bundle E2E failures
  uses: your-org/playwright-failure-bundler@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    report-path: 'e2e-results/results.json'
    issue-title: '🚨 E2E Test Failures'
    issue-labels: 'e2e,critical'
    max-failures: 3

- name: Bundle integration failures
  uses: your-org/playwright-failure-bundler@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    report-path: 'integration-results/results.json'
    issue-title: '⚠️ Integration Test Failures'
    issue-labels: 'integration,medium'
    max-failures: 5
```

### Conditional Execution

Only create issues for specific conditions:

```yaml
- name: Bundle failures (main branch only)
  if: github.ref == 'refs/heads/main' && always()
  uses: your-org/playwright-failure-bundler@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    issue-title: '🔥 Production Branch Failures'
    issue-labels: 'critical,production'

- name: Bundle failures (PR)
  if: github.event_name == 'pull_request' && always()
  uses: your-org/playwright-failure-bundler@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    issue-title: 'PR Test Failures - #${{ github.event.number }}'
    issue-labels: 'pr,review-required'
    deduplicate: false
```

### Matrix Strategy Integration

Use with matrix strategies for comprehensive testing:

```yaml
strategy:
  matrix:
    browser: [chromium, firefox, webkit]

steps:
  - name: Run tests
    run: npx playwright test --project=${{ matrix.browser }}
    continue-on-error: true

  - name: Bundle failures
    uses: your-org/playwright-failure-bundler@v1
    with:
      github-token: ${{ secrets.GITHUB_TOKEN }}
      report-path: 'test-results-${{ matrix.browser }}/results.json'
      issue-title: '${{ matrix.browser }} Test Failures'
      issue-labels: 'playwright,${{ matrix.browser }}'
```

### Custom Report Paths

Handle non-standard Playwright configurations:

```yaml
- name: Run Playwright with custom config
  run: |
    npx playwright test \
      --config=custom.config.js \
      --reporter=json \
      --output-dir=custom-results

- name: Bundle failures
  uses: your-org/playwright-failure-bundler@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    report-path: 'custom-results/results.json'
```

## Troubleshooting

### Common Issues

#### Issue: "Report file not found"

**Cause:** The specified report path doesn't exist or Playwright didn't generate a report.

**Solutions:**
1. Verify Playwright is configured to output JSON reports
2. Check the `report-path` parameter matches your Playwright configuration
3. Ensure the test step completed (use `continue-on-error: true`)

```yaml
# Playwright config
export default {
  reporter: [['json', { outputFile: 'test-results/results.json' }]]
}
```

#### Issue: "Permission denied" or "403 Forbidden"

**Cause:** Insufficient GitHub token permissions.

**Solutions:**
1. Add `issues: write` permission to your workflow
2. Verify the token has access to the repository
3. For organization repositories, check organization settings

```yaml
permissions:
  issues: write
```

#### Issue: "No test failures found" but tests actually failed

**Cause:** Playwright report doesn't contain failure information.

**Solutions:**
1. Verify Playwright version compatibility (1.30.0+)
2. Check that tests are actually failing (not just timing out)
3. Ensure JSON reporter is properly configured

#### Issue: Issues not being deduplicated

**Cause:** Title variations or search limitations.

**Solutions:**
1. Use consistent issue titles
2. Check for typos in titles
3. Verify existing issues are open (not closed)

### Debug Mode

Enable debug logging for troubleshooting:

```yaml
- name: Bundle failures (debug)
  uses: your-org/playwright-failure-bundler@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
  env:
    RUNNER_DEBUG: 1
```

### Validation

Test your configuration with a minimal setup:

```yaml
- name: Validate configuration
  uses: your-org/playwright-failure-bundler@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    report-path: 'test-results/results.json'
    max-failures: 1
    issue-title: 'Test Configuration'
    issue-labels: 'test'
```

## Best Practices

1. **Always use `continue-on-error: true`** for test steps
2. **Use `if: always()`** for the bundler step
3. **Include context in issue titles** (branch, build number, etc.)
4. **Use appropriate labels** for filtering and organization
5. **Set reasonable `max-failures`** limits to avoid overwhelming issues
6. **Enable deduplication** for most use cases
7. **Assign issues to appropriate teams** for faster resolution
8. **Test your configuration** in a development environment first
