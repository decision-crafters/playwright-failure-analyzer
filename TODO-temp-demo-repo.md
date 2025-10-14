# TODO: Create Demo Repository

## Quick Setup

```bash
# 1. Create the repository locally
git clone https://github.com/decision-crafters/playwright-failure-analyzer-demo.git
cd playwright-failure-analyzer-demo

# 2. Create all files (see below)
# 3. Initialize and push
npm install
git add .
git commit -m "Initial demo repository setup"
git push origin main

# 4. Enable Actions in GitHub repository settings
# 5. Trigger workflow: Actions → "Test with Intentional Failures" → Run workflow
```

---

## File Structure

```
playwright-failure-analyzer-demo/
├── .github/
│   └── workflows/
│       ├── test-intentional-failures.yml
│       └── test-all-passing.yml
├── tests/
│   ├── sample-fail.spec.js
│   └── sample-pass.spec.js
├── playwright.config.js
├── package.json
├── .gitignore
├── LICENSE
└── README.md
```

---

## Files to Create

### 1. `package.json`

```json
{
  "name": "playwright-failure-analyzer-demo",
  "version": "1.0.0",
  "description": "Live demonstration and testing repository for Playwright Failure Analyzer",
  "scripts": {
    "test": "playwright test",
    "test:fail": "playwright test sample-fail",
    "test:pass": "playwright test sample-pass"
  },
  "keywords": [
    "playwright",
    "testing",
    "github-actions",
    "demo",
    "failure-analysis"
  ],
  "author": "Decision Crafters",
  "license": "MIT",
  "devDependencies": {
    "@playwright/test": "^1.40.0"
  }
}
```

---

### 2. `playwright.config.js` ⭐ CRITICAL

```javascript
const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,

  // CRITICAL: JSON reporter is required for the action
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report/html', open: 'never' }],
    ['json', { outputFile: 'playwright-report/results.json' }]
  ],

  use: {
    baseURL: 'https://example.com',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { channel: 'chromium' },
    },
  ],
});
```

---

### 3. `tests/sample-fail.spec.js`

```javascript
const { test, expect } = require('@playwright/test');

test.describe('Intentional Failure Tests', () => {
  test('timeout failure - element not found', async ({ page }) => {
    await page.goto('https://example.com');
    await expect(page.locator('#non-existent-element')).toBeVisible({
      timeout: 2000
    });
  });

  test('assertion failure - wrong title', async ({ page }) => {
    await page.goto('https://example.com');
    const title = await page.title();
    expect(title).toBe('Wrong Title Expected');
  });

  test('navigation timeout - invalid domain', async ({ page }) => {
    await page.goto('https://this-domain-definitely-does-not-exist-12345.com', {
      timeout: 3000
    });
  });

  test('selector not found - click failure', async ({ page }) => {
    await page.goto('https://example.com');
    await page.click('#nonexistent-button', { timeout: 2000 });
  });

  test('text content mismatch', async ({ page }) => {
    await page.goto('https://example.com');
    await expect(page.locator('h1')).toHaveText('This Text Does Not Exist');
  });
});
```

---

### 4. `tests/sample-pass.spec.js`

```javascript
const { test, expect } = require('@playwright/test');

test.describe('Passing Tests Suite', () => {
  test('should navigate to example.com', async ({ page }) => {
    await page.goto('https://example.com');
    await expect(page).toHaveTitle(/Example Domain/);
  });

  test('should find heading element', async ({ page }) => {
    await page.goto('https://example.com');
    const heading = page.locator('h1');
    await expect(heading).toBeVisible();
    await expect(heading).toContainText('Example Domain');
  });

  test('should have paragraph text', async ({ page }) => {
    await page.goto('https://example.com');
    const paragraph = page.locator('p').first();
    await expect(paragraph).toBeVisible();
  });

  test('should load page successfully', async ({ page }) => {
    const response = await page.goto('https://example.com');
    expect(response?.status()).toBe(200);
  });

  test('should have correct page structure', async ({ page }) => {
    await page.goto('https://example.com');
    await expect(page.locator('body')).toBeVisible();
    await expect(page.locator('h1')).toBeVisible();
  });
});
```

---

### 5. `.github/workflows/test-intentional-failures.yml` ⭐ MAIN WORKFLOW

```yaml
name: Test with Intentional Failures

on:
  push:
    branches: [main]
  pull_request:
  workflow_dispatch:
  schedule:
    - cron: '0 */12 * * *'

jobs:
  test-failures:
    name: Run Tests with Failures
    runs-on: ubuntu-latest

    permissions:
      issues: write
      contents: read

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
          max-failures: 10
          issue-title: '[DEMO] Test Failures - Run #${{ github.run_number }}'
          issue-labels: 'demo,automated,expected-failure'
          deduplicate: false

      - name: Upload Playwright Report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report-failures
          path: playwright-report/
          retention-days: 7
```

---

### 6. `.github/workflows/test-all-passing.yml`

```yaml
name: Test All Passing

on:
  workflow_dispatch:
  schedule:
    - cron: '0 6 * * 1'

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
      - run: npx playwright test sample-pass

      - name: Upload Playwright Report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report-passing
          path: playwright-report/
          retention-days: 7
```

---

### 7. `.gitignore`

```
node_modules/
package-lock.json
playwright-report/
test-results/
.DS_Store
*.log
.env
.env.local
.vscode/
.idea/
```

---

### 8. `LICENSE`

```
MIT License

Copyright (c) 2025 Decision Crafters

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

### 9. `README.md`

```markdown
# Playwright Failure Analyzer - Demo Repository

[![Test with Intentional Failures](../../actions/workflows/test-intentional-failures.yml/badge.svg)](../../actions/workflows/test-intentional-failures.yml)

> Live demonstration of the [Playwright Failure Analyzer](https://github.com/decision-crafters/playwright-failure-analyzer) GitHub Action

---

## 🎯 Purpose

1. **📺 Live Demo**: See the action working with real test failures
2. **📋 Template**: Fork this repo to quickly set up the action
3. **🧪 Validation**: Automated testing environment for the action

---

## 🧪 Test Workflows

### 🔴 [Test with Intentional Failures](../../actions/workflows/test-intentional-failures.yml)

Runs tests that **intentionally fail** to demonstrate the action.

**What it does:**
- Runs 5 tests designed to fail (timeout, assertion, navigation errors)
- Action automatically creates a detailed GitHub issue
- Runs every 12 hours to keep demo active

**View Demo Issues**: [Issues with `demo` label →](../../issues?q=label%3Ademo)

### ✅ [Test All Passing](../../actions/workflows/test-all-passing.yml)

Runs tests that **all pass** to show no issues are created when tests succeed.

---

## 🚀 Try It Yourself!

### Option 1: Fork and Run

1. **Fork this repository**
2. **Enable Actions**: Go to Actions tab → Enable workflows
3. **Trigger workflow**: Actions → "Test with Intentional Failures" → Run workflow
4. **Check Issues tab** for automatically created issue!

### Option 2: Use as Template

Copy `playwright.config.js` and workflows to your repository.

---

## 📖 What You'll See

When the action runs, it creates a comprehensive GitHub issue:

### Issue Contents
- ✅ Test run summary (total/passed/failed/skipped)
- ✅ Failure details with error messages and stack traces
- ✅ File locations and line numbers
- ✅ Debug information (commit, workflow, Playwright version)
- ✅ Suggested next steps

---

## 📚 Learn More

- **[Action Repository](https://github.com/decision-crafters/playwright-failure-analyzer)**
- **[How It Works](https://github.com/decision-crafters/playwright-failure-analyzer/blob/main/docs/HOW_IT_WORKS.md)**
- **[Configuration Guide](https://github.com/decision-crafters/playwright-failure-analyzer/blob/main/docs/CONFIGURATION.md)**
- **[Troubleshooting](https://github.com/decision-crafters/playwright-failure-analyzer/blob/main/docs/TROUBLESHOOTING.md)**

---

## 🛠️ Repository Structure

```
playwright-failure-analyzer-demo/
├── .github/workflows/
│   ├── test-intentional-failures.yml
│   └── test-all-passing.yml
├── tests/
│   ├── sample-fail.spec.js
│   └── sample-pass.spec.js
├── playwright.config.js
├── package.json
└── README.md
```

---

## ❓ FAQ

**Q: Why do these tests fail?**
A: Tests in `sample-fail.spec.js` are intentionally designed to fail to demonstrate the action.

**Q: How often do workflows run?**
A: Intentional failures every 12 hours, passing tests weekly on Mondays.

**Q: Can I customize this?**
A: Yes! Fork and modify test files, schedules, labels, and titles.

---

## 📄 License

MIT License - See [LICENSE](https://github.com/decision-crafters/playwright-failure-analyzer/blob/main/LICENSE)

---

<div align="center">

**Made with ❤️ by the Decision Crafters team**

[⭐ Star the Action](https://github.com/decision-crafters/playwright-failure-analyzer) |
[📖 Docs](https://github.com/decision-crafters/playwright-failure-analyzer#readme)

</div>
```

---

## ✅ After Creating Files

1. **Verify structure**:
   ```bash
   tree -L 2 -a
   ```

2. **Install and test locally** (optional):
   ```bash
   npm install
   npx playwright install chromium
   npm run test:fail  # Should fail (expected)
   npm run test:pass  # Should pass
   ```

3. **Commit and push**:
   ```bash
   git add .
   git commit -m "Initial demo repository setup"
   git push origin main
   ```

4. **Enable Actions** in GitHub:
   - Go to repository → Settings → Actions → General
   - Enable "Allow all actions and reusable workflows"

5. **Trigger first workflow**:
   - Actions tab → "Test with Intentional Failures" → Run workflow
   - Wait ~2 minutes
   - Check Issues tab for new demo issue

6. **Validate with script** (from main repo):
   ```bash
   bash scripts/validate-demo-repo.sh
   ```

---

## 🎯 Expected Results

- ✅ Workflow runs successfully
- ✅ Tests fail as designed
- ✅ GitHub issue created with `demo` label
- ✅ Issue contains 5 test failures with details
- ✅ Workflow runs every 12 hours automatically

---

## 📝 Notes

- The repo URL is: `https://github.com/decision-crafters/playwright-failure-analyzer-demo.git`
- Make sure you have push access to the repository
- The `@v1` tag in workflows uses the latest v1.x release of the action
- Set `deduplicate: false` to always create new issues for demo purposes
