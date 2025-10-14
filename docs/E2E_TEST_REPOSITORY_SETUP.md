# E2E Test Repository Setup Guide

This guide shows how to create and maintain the public demonstration repository for the Playwright Failure Analyzer.

---

## Overview

The E2E test repository (`decision-crafters/playwright-failure-analyzer-demo`) serves as:
- ✅ Live demonstration of the action in use
- ✅ Public test bed for validating releases
- ✅ Template for users to fork and customize
- ✅ Integration test suite for CI/CD validation

---

## Repository Structure

```
playwright-failure-analyzer-demo/
├── .github/
│   └── workflows/
│       ├── test-intentional-failures.yml    # Demonstrates failure handling
│       ├── test-all-passing.yml             # Demonstrates success case
│       ├── test-with-ai-analysis.yml        # AI-powered analysis demo
│       └── test-flaky-tests.yml             # Retry/flaky test handling
├── tests/
│   ├── sample-pass.spec.ts                  # Passing tests
│   ├── sample-fail.spec.ts                  # Intentional failures
│   ├── sample-timeout.spec.ts               # Timeout failures
│   ├── sample-assertion.spec.ts             # Assertion failures
│   └── sample-flaky.spec.ts                 # Flaky tests
├── playwright.config.ts                     # Standard Playwright config
├── package.json
├── tsconfig.json
├── .gitignore
└── README.md                                # Usage instructions
```

---

## Step 1: Create Repository

### GitHub Setup

1. **Create new repository**:
   ```bash
   gh repo create decision-crafters/playwright-failure-analyzer-demo \
     --public \
     --description "Live demonstration and testing repository for Playwright Failure Analyzer" \
     --homepage "https://github.com/decision-crafters/playwright-failure-analyzer"
   ```

2. **Configure repository settings**:
   - Enable Issues
   - Enable Discussions (optional)
   - Disable Wiki
   - Enable GitHub Actions

3. **Set up branch protection** (optional but recommended):
   - Require status checks before merging
   - Require branches to be up to date

---

## Step 2: Initialize Project

### Clone and Setup

```bash
# Clone the repository
git clone https://github.com/decision-crafters/playwright-failure-analyzer-demo.git
cd playwright-failure-analyzer-demo

# Initialize Node.js project
npm init -y

# Install Playwright
npm install -D @playwright/test@latest
npm install -D typescript@latest

# Install Playwright browsers
npx playwright install --with-deps
```

### Create package.json

```json
{
  "name": "playwright-failure-analyzer-demo",
  "version": "1.0.0",
  "description": "Demonstration repository for Playwright Failure Analyzer",
  "scripts": {
    "test": "playwright test",
    "test:fail": "playwright test sample-fail",
    "test:pass": "playwright test sample-pass",
    "test:flaky": "playwright test sample-flaky"
  },
  "keywords": ["playwright", "testing", "github-actions", "demo"],
  "author": "Decision Crafters",
  "license": "MIT",
  "devDependencies": {
    "@playwright/test": "^1.40.0",
    "typescript": "^5.3.0"
  }
}
```

---

## Step 3: Create Playwright Configuration

### playwright.config.ts

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',

  // Run tests in parallel
  fullyParallel: true,

  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,

  // Retry on CI only
  retries: process.env.CI ? 2 : 0,

  // Opt out of parallel tests on CI
  workers: process.env.CI ? 1 : undefined,

  // Reporter configuration - critical for the action
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report/html', open: 'never' }],
    ['json', { outputFile: 'playwright-report/results.json' }]  // Required for action
  ],

  use: {
    // Base URL to use in actions like `await page.goto('/')`
    baseURL: 'https://example.com',

    // Collect trace when retrying the failed test
    trace: 'on-first-retry',

    // Screenshot on failure
    screenshot: 'only-on-failure',
  },

  // Configure projects for major browsers
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
```

---

## Step 4: Create Test Files

### tests/sample-pass.spec.ts

```typescript
import { test, expect } from '@playwright/test';

test.describe('Passing Tests Suite', () => {
  test('should navigate to example.com', async ({ page }) => {
    await page.goto('https://example.com');
    await expect(page).toHaveTitle(/Example Domain/);
  });

  test('should find heading', async ({ page }) => {
    await page.goto('https://example.com');
    const heading = page.locator('h1');
    await expect(heading).toBeVisible();
    await expect(heading).toHaveText(/Example Domain/);
  });

  test('should have paragraph text', async ({ page }) => {
    await page.goto('https://example.com');
    const paragraph = page.locator('p').first();
    await expect(paragraph).toBeVisible();
  });
});
```

### tests/sample-fail.spec.ts

```typescript
import { test, expect } from '@playwright/test';

test.describe('Intentional Failure Tests', () => {
  test('demonstrates timeout failure', async ({ page }) => {
    await page.goto('https://example.com');
    // Intentionally wait for non-existent element
    await expect(page.locator('#non-existent-element')).toBeVisible({ timeout: 5000 });
  });

  test('demonstrates assertion failure', async ({ page }) => {
    await page.goto('https://example.com');
    const title = await page.title();
    // Intentional mismatch
    expect(title).toBe('Wrong Title Expected');
  });

  test('demonstrates navigation timeout', async ({ page }) => {
    // Try to navigate to invalid URL
    await page.goto('https://this-domain-definitely-does-not-exist-12345.com', {
      timeout: 5000
    });
  });
});
```

### tests/sample-flaky.spec.ts

```typescript
import { test, expect } from '@playwright/test';

test.describe('Flaky Test Examples', () => {
  test('randomly fails (demonstrates retry)', async ({ page }) => {
    await page.goto('https://example.com');

    // Simulate flaky test - fails 50% of the time
    const shouldFail = Math.random() > 0.5;

    if (shouldFail) {
      await expect(page.locator('#random-element')).toBeVisible({ timeout: 1000 });
    } else {
      await expect(page).toHaveTitle(/Example Domain/);
    }
  });
});
```

---

## Step 5: Create GitHub Workflows

### .github/workflows/test-intentional-failures.yml

```yaml
name: Test with Intentional Failures

on:
  push:
    branches: [main]
  pull_request:
  workflow_dispatch:
  schedule:
    - cron: '0 */6 * * *'  # Run every 6 hours

jobs:
  test-failures:
    name: Run Tests with Failures
    runs-on: ubuntu-latest

    permissions:
      issues: write

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'

      - run: npm ci

      - run: npx playwright install --with-deps chromium

      - name: Run failing tests
        id: tests
        run: |
          npx playwright test sample-fail
          TEST_EXIT_CODE=$?
          echo "test-failed=$([ $TEST_EXIT_CODE -ne 0 ] && echo 'true' || echo 'false')" >> $GITHUB_OUTPUT
          exit $TEST_EXIT_CODE
        continue-on-error: true

      - name: Analyze failures
        if: steps.tests.outputs.test-failed == 'true'
        uses: decision-crafters/playwright-failure-analyzer@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          issue-title: '[DEMO] Intentional Test Failures - Run #${{ github.run_number }}'
          issue-labels: 'demo,automated,expected-failure'
          max-failures: 5

      - name: Upload HTML report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report-failures
          path: playwright-report/html/
          retention-days: 7
```

### .github/workflows/test-all-passing.yml

```yaml
name: Test All Passing

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  test-passing:
    name: Run Passing Tests
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'

      - run: npm ci

      - run: npx playwright install --with-deps chromium

      - name: Run passing tests
        run: npx playwright test sample-pass

      - name: Upload HTML report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report-passing
          path: playwright-report/html/
          retention-days: 7
```

---

## Step 6: Create README

### README.md

```markdown
# Playwright Failure Analyzer - Demo Repository

This repository demonstrates the [Playwright Failure Analyzer](https://github.com/decision-crafters/playwright-failure-analyzer) in action.

## 🎯 Purpose

- **Live Demo**: See the action working with real test failures
- **Template**: Fork this repo to quickly set up the action
- **Validation**: Automated testing of the action itself

## 🧪 Test Scenarios

### Intentional Failures
[![Test with Intentional Failures](https://github.com/decision-crafters/playwright-failure-analyzer-demo/actions/workflows/test-intentional-failures.yml/badge.svg)](https://github.com/decision-crafters/playwright-failure-analyzer-demo/actions/workflows/test-intentional-failures.yml)

Demonstrates how the action handles various failure types:
- Timeout errors
- Assertion failures
- Navigation failures

**View Recent Issues**: [Issues with `demo` label](https://github.com/decision-crafters/playwright-failure-analyzer-demo/issues?q=label%3Ademo)

### All Passing
[![Test All Passing](https://github.com/decision-crafters/playwright-failure-analyzer-demo/actions/workflows/test-all-passing.yml/badge.svg)](https://github.com/decision-crafters/playwright-failure-analyzer-demo/actions/workflows/test-all-passing.yml)

Shows that the action doesn't create issues when tests pass.

## 🚀 Fork and Try

1. **Fork this repository**
2. **Enable Actions** in your fork
3. **Run workflows** manually from the Actions tab
4. **See issues created** automatically

## 📖 Learn More

- [Action Documentation](https://github.com/decision-crafters/playwright-failure-analyzer)
- [Configuration Guide](https://github.com/decision-crafters/playwright-failure-analyzer/blob/main/docs/CONFIGURATION.md)
- [Playwright Reporter Setup](https://github.com/decision-crafters/playwright-failure-analyzer/blob/main/examples/playwright-reporters.md)

## 🤝 Contributing

Found an issue or want to add a test scenario? [Open an issue](https://github.com/decision-crafters/playwright-failure-analyzer/issues) in the main repository.
```

---

## Step 7: CI Integration

### Validation Script

Create `scripts/validate-demo-repo.sh`:

```bash
#!/bin/bash
# Validate the demo repository is working correctly

set -e

DEMO_REPO="decision-crafters/playwright-failure-analyzer-demo"
echo "Validating demo repository: $DEMO_REPO"

# Check recent workflow runs
echo "Checking recent workflow runs..."
RECENT_RUNS=$(gh run list --repo "$DEMO_REPO" --limit 5 --json status,conclusion --jq '.')

# Check if issues are being created
echo "Checking demo issues..."
DEMO_ISSUES=$(gh issue list --repo "$DEMO_REPO" --label demo --limit 5 --json number,title --jq 'length')

if [ "$DEMO_ISSUES" -gt 0 ]; then
  echo "✅ Demo repository is functioning ($DEMO_ISSUES demo issues found)"
  exit 0
else
  echo "⚠️  Warning: No demo issues found. Workflows may not be running."
  exit 1
fi
```

---

## Maintenance

### Regular Tasks

1. **Weekly**: Check that workflows are running
2. **Monthly**: Update Playwright version
3. **Per Release**: Test new action version
4. **Quarterly**: Review and close old demo issues

### Cleanup Script

```bash
#!/bin/bash
# Clean up old demo issues

gh issue list --repo decision-crafters/playwright-failure-analyzer-demo \
  --label demo \
  --state open \
  --json number,createdAt \
  --jq '.[] | select((.createdAt | fromdateiso8601) < (now - 604800)) | .number' \
  | xargs -I {} gh issue close {} --repo decision-crafters/playwright-failure-analyzer-demo \
  --comment "Automatically closing old demo issue."
```

---

## Integration with Main Repository

### Pre-Release Validation

Add to main repo's `.github/workflows/release.yml`:

```yaml
validate-demo:
  name: Validate Demo Repository
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4

    - name: Trigger demo workflow
      env:
        GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      run: |
        gh workflow run test-intentional-failures.yml \
          --repo decision-crafters/playwright-failure-analyzer-demo

    - name: Wait for completion
      run: sleep 60

    - name: Validate
      run: ./scripts/validate-demo-repo.sh
```

---

## Troubleshooting

### Issue: Workflows not running

**Check**:
1. Actions enabled in repository settings
2. Workflow permissions set correctly
3. GITHUB_TOKEN has `issues: write` permission

### Issue: Issues not being created

**Check**:
1. Tests are actually failing
2. Playwright report exists
3. Action logs for errors

### Issue: Too many demo issues

**Solution**: Run cleanup script or adjust workflow schedule

---

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Playwright Documentation](https://playwright.dev/)
- [Action Repository](https://github.com/decision-crafters/playwright-failure-analyzer)
