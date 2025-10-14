# Playwright Reporter Configurations

This guide shows you how to configure Playwright to generate JSON reports that work seamlessly with the Playwright Failure Analyzer action.

---

## Table of Contents

- [Recommended Setup](#recommended-setup)
- [Configuration Methods](#configuration-methods)
- [Multiple Reporters](#multiple-reporters)
- [Common Patterns](#common-patterns)
- [Troubleshooting](#troubleshooting)

---

## Recommended Setup

The **recommended approach** is to configure the JSON reporter in your `playwright.config.js` file:

```javascript
// playwright.config.js
import { defineConfig } from '@playwright/test';

export default defineConfig({
  // Your existing config...

  reporter: [
    ['json', { outputFile: 'playwright-report/results.json' }]
  ],

  // Other settings...
});
```

**Advantages:**
- ✅ Consistent across all test runs
- ✅ No need to remember command-line flags
- ✅ Works with `npx playwright test` (no additional arguments)
- ✅ Integrates with other reporters

**Workflow Usage:**
```yaml
- name: Run Playwright tests
  run: npx playwright test
  continue-on-error: true

- name: Analyze failures
  if: always()
  uses: decision-crafters/playwright-failure-analyzer@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    # Uses default: playwright-report/results.json
```

---

## Configuration Methods

### Method 1: Config File (Recommended)

**File:** `playwright.config.js` or `playwright.config.ts`

```javascript
// playwright.config.js
export default {
  reporter: [['json', { outputFile: 'playwright-report/results.json' }]]
};
```

**TypeScript version:**
```typescript
// playwright.config.ts
import { PlaywrightTestConfig } from '@playwright/test';

const config: PlaywrightTestConfig = {
  reporter: [['json', { outputFile: 'playwright-report/results.json' }]]
};

export default config;
```

**Confidence: 95%** - This is Playwright's recommended approach.

---

### Method 2: Command Line

For quick testing or one-off runs:

```bash
npx playwright test --reporter=json --reporter-output=playwright-report/results.json
```

**Workflow Usage:**
```yaml
- name: Run Playwright tests
  run: |
    npx playwright test \
      --reporter=json \
      --reporter-output=playwright-report/results.json
  continue-on-error: true
```

**Note:** Command-line options override config file settings.

---

### Method 3: Shell Redirection (Simple Projects)

For minimal configuration:

```bash
npx playwright test --reporter=json > test-results.json 2>&1
```

**Workflow Usage:**
```yaml
- name: Run Playwright tests
  run: npx playwright test --reporter=json > test-results.json 2>&1
  continue-on-error: true

- name: Analyze failures
  if: always()
  uses: decision-crafters/playwright-failure-analyzer@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    report-path: 'test-results.json'
```

**Caveats:**
- ⚠️ Includes stderr output in the JSON file
- ⚠️ May produce invalid JSON if Playwright prints warnings
- ⚠️ Not recommended for production use

---

## Multiple Reporters

Playwright supports using multiple reporters simultaneously:

### HTML + JSON (Most Common)

```javascript
// playwright.config.js
export default {
  reporter: [
    ['html', { outputFolder: 'playwright-report/html' }],
    ['json', { outputFile: 'playwright-report/results.json' }],
  ]
};
```

**Benefits:**
- 📊 HTML report for manual review
- 🤖 JSON report for automated analysis

---

### All Built-in Reporters

```javascript
// playwright.config.js
export default {
  reporter: [
    ['list'],                                             // Console output
    ['html', { outputFolder: 'playwright-report/html' }], // Interactive HTML
    ['json', { outputFile: 'playwright-report/results.json' }], // For automation
    ['junit', { outputFile: 'playwright-report/junit.xml' }],   // CI integration
  ]
};
```

**When to use:**
- Large projects with multiple stakeholders
- Need different formats for different purposes
- Integration with multiple CI/CD tools

---

## Common Patterns

### Pattern 1: Separate Reports per Project

If you test multiple browsers/projects:

```javascript
// playwright.config.js
export default {
  projects: [
    {
      name: 'chromium',
      use: { browserName: 'chromium' }
    },
    {
      name: 'firefox',
      use: { browserName: 'firefox' }
    },
    {
      name: 'webkit',
      use: { browserName: 'webkit' }
    }
  ],

  reporter: [
    ['json', { outputFile: 'playwright-report/results.json' }],
  ]
};
```

**Note:** All projects write to the same JSON file by default. Use the workflow to analyze combined results:

```yaml
- name: Analyze all browser failures
  if: always()
  uses: decision-crafters/playwright-failure-analyzer@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    issue-title: 'Multi-Browser Test Failures'
```

---

### Pattern 2: Different Reports for Different Suites

```yaml
# E2E tests
- name: Run E2E tests
  run: |
    npx playwright test e2e/ \
      --reporter=json \
      --reporter-output=e2e-results.json

# Integration tests  
- name: Run integration tests
  run: |
    npx playwright test integration/ \
      --reporter=json \
      --reporter-output=integration-results.json

# Analyze separately
- name: Analyze E2E failures
  if: always()
  uses: decision-crafters/playwright-failure-analyzer@v1
  with:
    report-path: 'e2e-results.json'
    issue-title: 'E2E Test Failures'

- name: Analyze integration failures
  if: always()
  uses: decision-crafters/playwright-failure-analyzer@v1
  with:
    report-path: 'integration-results.json'
    issue-title: 'Integration Test Failures'
```

---

### Pattern 3: Environment-Specific Configuration

Use environment variables to customize output:

```javascript
// playwright.config.js
const isCI = process.env.CI === 'true';
const reportPath = process.env.PLAYWRIGHT_REPORT_PATH || 'playwright-report/results.json';

export default {
  reporter: isCI
    ? [
        ['json', { outputFile: reportPath }],
        ['github'], // GitHub Actions annotations
      ]
    : [
        ['html'],
        ['list'],
      ]
};
```

---

## Troubleshooting

### Issue: "Report file not found"

**Cause:** Mismatch between Playwright output location and action input.

**Solution 1 - Use default paths:**
```javascript
// playwright.config.js
reporter: [['json', { outputFile: 'playwright-report/results.json' }]]
```
```yaml
# workflow.yml - don't specify report-path, uses default
uses: decision-crafters/playwright-failure-analyzer@v1
with:
  github-token: ${{ secrets.GITHUB_TOKEN }}
```

**Solution 2 - Explicit matching:**
```javascript
// playwright.config.js
reporter: [['json', { outputFile: 'custom-location/report.json' }]]
```
```yaml
# workflow.yml
uses: decision-crafters/playwright-failure-analyzer@v1
with:
  github-token: ${{ secrets.GITHUB_TOKEN }}
  report-path: 'custom-location/report.json'
```

---

### Issue: "Invalid JSON in report file"

**Cause:** Using shell redirection with stderr output mixed in.

**Solution:** Use config file or `--reporter-output`:

```yaml
# ❌ BAD - stderr mixes with JSON
- run: npx playwright test --reporter=json > results.json 2>&1

# ✅ GOOD - Clean JSON output
- run: npx playwright test --reporter=json --reporter-output=results.json
```

Or redirect stderr separately:
```yaml
# ✅ ALSO GOOD
- run: npx playwright test --reporter=json > results.json 2>/dev/null
```

---

### Issue: "Report missing required fields"

**Cause:** Not using Playwright's JSON reporter, or very old Playwright version.

**Solution:**

1. **Check Playwright version:**
   ```bash
   npx playwright --version
   ```
   Minimum supported: **1.30.0**

2. **Verify reporter configuration:**
   ```javascript
   // Must use 'json' reporter specifically
   reporter: [['json', { outputFile: 'results.json' }]]
   ```

3. **Test locally:**
   ```bash
   npx playwright test --reporter=json --reporter-output=test.json
   cat test.json | jq '.config.version'
   ```

---

### Issue: "No test results found in the report"

**Cause:** Tests didn't run or were filtered out.

**Solution:**

Check test discovery:
```bash
# List all tests
npx playwright test --list

# Verify tests are found
npx playwright test --reporter=list
```

Ensure tests are actually executing:
```javascript
// playwright.config.js
export default {
  testDir: './tests',  // ← Verify this path
  testMatch: '**/*.spec.{js,ts}',  // ← Verify pattern
  // ...
};
```

---

## Reporter Options Reference

### JSON Reporter Options

```javascript
reporter: [[
  'json',
  {
    outputFile: 'results.json',  // Output file path
    // No other options available for JSON reporter
  }
]]
```

**Note:** The JSON reporter has minimal configuration. Most customization happens through test configuration.

---

## Best Practices

1. ✅ **Use config file** instead of command-line for consistency
2. ✅ **Use default paths** when possible to reduce configuration
3. ✅ **Combine with HTML reporter** for best debugging experience
4. ✅ **Test locally first** before running in CI
5. ✅ **Version control your config** (commit `playwright.config.js`)
6. ✅ **Use `continue-on-error: true`** in workflows to allow analysis step to run
7. ✅ **Add `if: always()`** to analysis step

---

## Quick Reference

| Method | Command | Report Path | Pros | Cons |
|--------|---------|-------------|------|------|
| **Config File** | `npx playwright test` | `playwright-report/results.json` | ✅ Consistent<br>✅ Reusable | Requires config file |
| **CLI Flag** | `npx playwright test --reporter=json --reporter-output=results.json` | Custom | ✅ Quick testing<br>✅ Flexible | ❌ Must remember flags |
| **Shell Redirect** | `npx playwright test --reporter=json > results.json 2>&1` | Custom | ✅ Simple | ❌ Fragile<br>❌ stderr issues |

---

## Example: Complete Setup

**playwright.config.js:**
```javascript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 30000,

  reporter: [
    ['html', { outputFolder: 'playwright-report/html', open: 'never' }],
    ['json', { outputFile: 'playwright-report/results.json' }],
    ['list']
  ],

  use: {
    trace: 'on-first-retry',
  },

  projects: [
    { name: 'chromium', use: { browserName: 'chromium' } },
    { name: 'firefox', use: { browserName: 'firefox' } },
  ],
});
```

**GitHub Workflow:**
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
        run: npx playwright test
        continue-on-error: true

      - name: Upload HTML report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: playwright-report/html

      - name: Analyze test failures
        if: always()
        uses: decision-crafters/playwright-failure-analyzer@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          max-failures: 5
          issue-labels: 'bug,playwright,e2e'
```

---

## Further Resources

- [Playwright Reporters Documentation](https://playwright.dev/docs/test-reporters)
- [Playwright Configuration Guide](https://playwright.dev/docs/test-configuration)
- [Action Troubleshooting Guide](../docs/TROUBLESHOOTING.md)
- [Action Configuration Guide](../docs/CONFIGURATION.md)

---

**Questions or issues?** See the [Troubleshooting Guide](../docs/TROUBLESHOOTING.md) or [open an issue](https://github.com/decision-crafters/playwright-failure-analyzer/issues).
