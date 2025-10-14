# Playwright Failure Analyzer - Troubleshooting Guide

## Overview

This guide documents known issues, solutions, and best practices for the `decision-crafters/playwright-failure-analyzer@v1` GitHub Action when working with Playwright test automation in CI/CD pipelines.

---

## Critical Issues

### 🚨 Issue 1: Analyzer Not Running Despite Test Failures

**Severity**: Critical  
**Status**: Documented & Solved

#### Problem

The failure analyzer step is being skipped even when Playwright tests fail with exit code 1.

#### Root Cause

The `if: failure()` condition in GitHub Actions only triggers when a step fails AND doesn't have `continue-on-error: true`. When `continue-on-error: true` is set, the step is marked as "successful" even if it exits with a non-zero code.

**GitHub Actions Execution Model:**

```
Step with continue-on-error: true + exit code 1
  ↓
Step conclusion: "success" (not "failure")
  ↓
if: failure() evaluates to false
  ↓
Analyzer step: skipped ❌
```

#### Evidence

From GitHub Actions analysis:

- Tests failed with exit code 1 (confirmed by annotation: "Process completed with exit code 1")
- "Run Playwright tests" step conclusion: **"success"** (due to `continue-on-error: true`)
- "Analyze Playwright Test Failures" step: **"skipped"** (because `if: failure()` condition not met)

#### ✅ Solution: Custom Failure Detection

**Instead of relying on `if: failure()`, implement custom failure detection using step outputs:**

```yaml
- name: Run Playwright tests
  id: playwright-tests
  run: |
    set +e  # CRITICAL: Disable exit on error to capture test exit code
    npx playwright test --reporter=json > test-results.json 2>&1
    TEST_EXIT_CODE=$?
    set -e  # Re-enable exit on error

    # Set output for failure detection
    if [ $TEST_EXIT_CODE -ne 0 ]; then
      echo "test-failed=true" >> $GITHUB_OUTPUT
    else
      echo "test-failed=false" >> $GITHUB_OUTPUT
    fi

    exit $TEST_EXIT_CODE
  continue-on-error: true

- name: Analyze Playwright Test Failures
  if: steps.playwright-tests.outputs.test-failed == 'true'
  uses: decision-crafters/playwright-failure-analyzer@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    report-path: 'test-results.json'
    ai-analysis: true
    max-failures: 5
```

#### Why This Works

1. **`set +e` Disables Exit-on-Error**: GitHub Actions runs bash with `-e` flag by default. Without `set +e`, the script exits immediately when tests fail, preventing the exit code from being captured
2. **Explicit Exit Code Capture**: `TEST_EXIT_CODE=$?` captures the actual test exit code
3. **Custom Output Variable**: `test-failed` is set based on exit code logic
4. **Reliable Condition**: `if: steps.playwright-tests.outputs.test-failed == 'true'` uses the custom output
5. **Decoupled from GitHub's Step Conclusion**: Works regardless of `continue-on-error` setting

#### ⚠️ Common Mistake

**Forgetting `set +e` will cause the analyzer to never run:**

```yaml
# ❌ BROKEN - Will skip analyzer even when tests fail
run: |
  npx playwright test  # Exits immediately on failure due to bash -e
  TEST_EXIT_CODE=$?    # Never executed!
  echo "test-failed=..." >> $GITHUB_OUTPUT  # Never executed!
```

**The `set +e` and `set -e` pattern is REQUIRED for this to work correctly.**

---

### Issue 2: Test Results File Not Found

#### Problem

The analyzer reports "No test report found" even though tests ran.

#### Common Causes

1. **Incorrect output path** - JSON report not written to expected location
2. **Working directory mismatch** - Test runs in subdirectory but analyzer looks in root
3. **Missing reporter configuration** - Playwright not configured to output JSON

#### ✅ Solutions

**1. Verify Playwright Reporter Configuration:**

```yaml
- name: Run Playwright tests
  run: |
    npx playwright test --reporter=json > test-results.json 2>&1
    # Verify file creation
    if [ -f "test-results.json" ]; then
      echo "✅ Test results captured successfully"
      ls -lh test-results.json
    else
      echo "⚠️  Warning: No test results file generated"
    fi
```

**2. Handle Subdirectory Execution:**

```yaml
- name: Run Playwright tests
  id: playwright-tests
  run: |
    cd client
    npx playwright test --reporter=json > ../test-results.json 2>&1
    TEST_EXIT_CODE=$?
    echo "test-failed=$([ $TEST_EXIT_CODE -ne 0 ] && echo 'true' || echo 'false')" >> $GITHUB_OUTPUT
    exit $TEST_EXIT_CODE
  continue-on-error: true

- name: Analyze failures
  if: steps.playwright-tests.outputs.test-failed == 'true'
  uses: decision-crafters/playwright-failure-analyzer@v1
  with:
    report-path: 'test-results.json'  # Now in root directory
```

**3. Use Playwright Config File:**

```typescript
// playwright.config.ts
export default defineConfig({
  reporter: [
    ['json', { outputFile: 'test-results.json' }],
    ['html', { open: 'never' }],
    ['github'], // Adds GitHub Actions annotations
  ],
});
```

---

### Issue 3: Permissions Errors

#### Problem

Error: "Resource not accessible by integration" when creating issues.

#### ✅ Solution

Ensure your workflow has the required permissions:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    permissions:
      issues: write  # Required for creating issues
      pull-requests: write  # Optional: for PR comments
```

---

### Issue 4: AI Analysis Not Working

#### Problem

AI analysis is enabled but no AI insights appear in issues.

#### Common Causes

1. Missing API key in GitHub Secrets
2. Incorrect environment variable name
3. Invalid API key
4. API rate limits or quota exceeded

#### ✅ Solutions

**1. Verify API Key Configuration:**

```yaml
- name: Analyze with AI
  uses: decision-crafters/playwright-failure-analyzer@v1
  with:
    ai-analysis: true
  env:
    # Ensure secret name matches exactly
    OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
    AI_MODEL: 'openrouter/deepseek/deepseek-chat'
```

**2. Test API Key Validity:**

```bash
# Test OpenRouter API key locally
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

**3. Enable Debug Logging:**

```yaml
- name: Analyze with AI
  uses: decision-crafters/playwright-failure-analyzer@v1
  with:
    ai-analysis: true
  env:
    OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
    ACTIONS_STEP_DEBUG: true  # Enable debug logs
```

---

### Issue 5: Duplicate Issues Created

#### Problem

Multiple issues created for the same test failures.

#### ✅ Solution

Ensure deduplication is enabled (it's on by default):

```yaml
- name: Analyze failures
  uses: decision-crafters/playwright-failure-analyzer@v1
  with:
    deduplicate: true  # Default: true
```

**How Deduplication Works:**

1. Generates hash of failure signatures
2. Searches for open issues with matching hash in title/body
3. Skips creation if duplicate found
4. Only checks **open** issues (closed issues don't prevent new ones)

---

## Best Practices

### 1. Always Use Custom Failure Detection ⭐

**DON'T** rely on `if: failure()` alone with `continue-on-error: true`:

```yaml
# ❌ BAD - Analyzer will never run
- name: Run tests
  run: npx playwright test
  continue-on-error: true

- name: Analyze
  if: failure()  # This won't trigger!
  uses: decision-crafters/playwright-failure-analyzer@v1
```

**DO** use custom step outputs:

```yaml
# ✅ GOOD - Reliable failure detection
- name: Run tests
  id: tests
  run: |
    npx playwright test
    TEST_EXIT_CODE=$?
    echo "failed=$([ $TEST_EXIT_CODE -ne 0 ] && echo 'true' || echo 'false')" >> $GITHUB_OUTPUT
    exit $TEST_EXIT_CODE
  continue-on-error: true

- name: Analyze
  if: steps.tests.outputs.failed == 'true'
  uses: decision-crafters/playwright-failure-analyzer@v1
```

### 2. Verify Test Results Generation

Always confirm test results are captured:

```yaml
- name: Run tests
  run: |
    npx playwright test --reporter=json > test-results.json 2>&1

    # Verification
    if [ -f "test-results.json" ]; then
      echo "✅ Results captured"
      wc -l test-results.json
    else
      echo "❌ No results file"
      exit 1
    fi
```

### 3. Test Locally First

Before pushing workflow changes:

```bash
# Test Playwright JSON output locally
npx playwright test --reporter=json > test-results.json
echo "Exit code: $?"
ls -lh test-results.json
cat test-results.json | jq '.suites[].specs[] | select(.tests[].results[].status == "failed")'
```

### 4. Monitor GitHub Actions Logs

When debugging, check:

1. **Actual exit code** of test step
2. **Test result files** are being generated
3. **Step outputs** and their values
4. **Analyzer step condition** evaluation

```bash
# View run details
gh run view <run-id> --log

# Check step conclusions
gh api repos/OWNER/REPO/actions/runs/<run-id>/jobs \
  | jq '.jobs[0].steps[] | {name, conclusion, status}'
```

### 5. Use Multiple Reporters

Configure Playwright for comprehensive reporting:

```typescript
// playwright.config.ts
export default defineConfig({
  reporter: [
    ['json', { outputFile: 'test-results.json' }],  // For analyzer
    ['html', { open: 'never' }],                     // For manual review
    ['github'],                                       // For PR annotations
    ['junit', { outputFile: 'junit.xml' }],          // For CI dashboards
  ],
});
```

---

## Debugging Workflows

### GitHub CLI Commands

```bash
# View recent workflow runs
gh run list --limit 10

# View specific run details
gh run view <run-id>

# View job details
gh run view --job=<job-id>

# Check step conclusions
gh api repos/owner/repo/actions/runs/<run-id>/jobs \
  | jq '.jobs[0].steps[] | {name, conclusion, status}'

# Get full logs
gh run view --log --job=<job-id>
```

### Common Debug Patterns

**Check if test results exist:**

```yaml
- name: Debug test results
  if: always()
  run: |
    echo "=== Test Results Debug ==="
    ls -la test-results.json || echo "File not found"
    cat test-results.json | jq '.' || echo "Invalid JSON"
```

**Verify step outputs:**

```yaml
- name: Run tests
  id: tests
  run: |
    echo "failed=true" >> $GITHUB_OUTPUT

- name: Check output
  run: |
    echo "Test failed: ${{ steps.tests.outputs.failed }}"
```

---

## Alternative Approaches

### Option 1: Custom Analysis Script

If the action doesn't meet your needs:

```yaml
- name: Custom failure analysis
  if: steps.tests.outputs.failed == 'true'
  run: |
    echo "## Test Failure Summary" > failure-report.md

    if [ -f "test-results.json" ]; then
      # Extract failed tests
      jq -r '.suites[].specs[] |
        select(.tests[].results[].status == "failed") |
        "- \(.title): \(.tests[0].results[0].error.message)"' \
        test-results.json >> failure-report.md
    fi

    cat failure-report.md
```

### Option 2: Built-in Playwright Reporters

Use native Playwright GitHub integration:

```typescript
// playwright.config.ts
export default defineConfig({
  reporter: [
    ['github'],  // Automatic PR annotations
    ['html'],    // Local debugging
  ],
});
```

### Option 3: Third-Party Integrations

- **Currents.dev** - Test analytics dashboard
- **Argos** - Visual regression testing
- **Testomat.io** - Test management platform

---

## Quick Reference

### Working Example (Copy-Paste Ready)

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    permissions:
      issues: write

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '18'

      - run: npm ci
      - run: npx playwright install --with-deps

      - name: Run Playwright tests
        id: playwright
        run: |
          npx playwright test --reporter=json > test-results.json 2>&1
          EXIT_CODE=$?
          echo "failed=$([ $EXIT_CODE -ne 0 ] && echo 'true' || echo 'false')" >> $GITHUB_OUTPUT
          exit $EXIT_CODE
        continue-on-error: true

      - name: Analyze failures
        if: steps.playwright.outputs.failed == 'true'
        uses: decision-crafters/playwright-failure-analyzer@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          report-path: 'test-results.json'
          ai-analysis: true
        env:
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
          AI_MODEL: 'openrouter/deepseek/deepseek-chat'
```

---

## Related Resources

- [GitHub Actions: Using Outputs](https://docs.github.com/en/actions/using-jobs/defining-outputs-for-jobs)
- [Playwright: Test Reporters](https://playwright.dev/docs/test-reporters)
- [GitHub Actions: Expression Syntax](https://docs.github.com/en/actions/learn-github-actions/expressions)

---

## Contributing

Found a new issue or solution? Please:

1. 🐛 [Report a bug](https://github.com/decision-crafters/playwright-failure-analyzer/issues/new?template=bug_report.md)
2. 💡 [Suggest an improvement](https://github.com/decision-crafters/playwright-failure-analyzer/issues/new?template=feature_request.md)
3. 📝 Submit a PR to update this guide

---

**Last Updated**: October 8, 2025  
**Verified Against**: GitHub Actions run analysis and empirical testing
