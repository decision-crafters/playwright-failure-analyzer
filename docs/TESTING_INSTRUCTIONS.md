# 🧪 Testing the Playwright Failure Analyzer

This guide shows you how to test the action in your own repository or use our public demo repository.

---

## Quick Start: Demo Repository (Recommended)

**The fastest way to see the action in action!**

### Option A: View Live Demos

Visit our public demo repository to see real examples:

**🔗 [playwright-failure-analyzer-demo](https://github.com/decision-crafters/playwright-failure-analyzer-demo)**

- ✅ Live workflows running the action
- ✅ Example issues created by the action
- ✅ Multiple test scenarios (failures, passing tests, flaky tests)
- ✅ Ready-to-use Playwright configuration

**See it working**:
1. Check the [Actions tab](https://github.com/decision-crafters/playwright-failure-analyzer-demo/actions) for recent runs
2. View [demo issues](https://github.com/decision-crafters/playwright-failure-analyzer-demo/issues?q=label%3Ademo) created automatically
3. Review workflow configurations in `.github/workflows/`

### Option B: Fork and Test

**Test the action in your own environment:**

1. **Fork the demo repository**:
   ```bash
   # Using GitHub CLI
   gh repo fork decision-crafters/playwright-failure-analyzer-demo

   # Or fork via web interface:
   # https://github.com/decision-crafters/playwright-failure-analyzer-demo/fork
   ```

2. **Enable GitHub Actions** in your fork:
   - Go to Actions tab
   - Click "I understand my workflows, go ahead and enable them"

3. **Run a workflow manually**:
   - Go to Actions → "Test with Intentional Failures"
   - Click "Run workflow"
   - Select branch: `main`
   - Click "Run workflow"

4. **Watch the magic happen**:
   - Workflow runs tests (which intentionally fail)
   - Action analyzes failures
   - Issue is created automatically
   - Check your Issues tab!

**Confidence**: 98% - This is the most reliable way to validate the action.

---

## Prerequisites (For Custom Testing)

1. A GitHub repository (public or private)
2. Playwright tests installed in your repository
3. GitHub Actions enabled
4. (Optional) OpenRouter or OpenAI API key for AI analysis testing

---

## Option 1: Test in Your Existing Playwright Project

### Step 1: Create the Workflow File

Create `.github/workflows/test-failure-analyzer.yml`:

```yaml
name: Test Playwright Failure Analyzer

on:
  push:
    branches: [main, develop]
  pull_request:
  workflow_dispatch:  # Allows manual triggering

jobs:
  test:
    runs-on: ubuntu-latest

    permissions:
      issues: write  # Required for creating issues

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright browsers
        run: npx playwright install --with-deps

      - name: Run Playwright tests
        id: tests
        run: npx playwright test --reporter=json > test-results.json
        continue-on-error: true  # Important: don't fail on test failures
        # Note: Playwright automatically finds tests based on your playwright.config.js
        # If you don't have a config, it searches for *.spec.js and *.test.js files

      - name: Analyze failures with the action
        if: always()  # Run even if tests pass
        uses: decision-crafters/playwright-failure-analyzer@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          report-path: 'test-results.json'
          max-failures: 5
          issue-title: '🧪 [TEST] Playwright Failures - ${{ github.ref_name }}'
          issue-labels: 'test,playwright,automated'
          deduplicate: false  # Always create new issue for testing
```

### Step 2: Commit and Push

```bash
git add .github/workflows/test-failure-analyzer.yml
git commit -m "Add Playwright failure analyzer test workflow"
git push
```

### Step 3: Trigger the Workflow

**Option A: Automatic** - Push to main/develop or create a PR

**Option B: Manual** - Go to GitHub → Actions → "Test Playwright Failure Analyzer" → Run workflow

### Step 4: Check Results

1. Go to **Actions** tab in your repository
2. Click on the workflow run
3. Check the "Analyze failures" step output
4. Go to **Issues** tab - you should see a new issue created!

---

## Option 2: Create a Test Repository from Scratch

Don't have Playwright tests? No problem! Create a test repository:

### Step 1: Create a New Repository

```bash
# Create a new directory
mkdir playwright-test-repo
cd playwright-test-repo
git init

# Initialize npm project
npm init -y

# Install Playwright
npm install -D @playwright/test
npx playwright install chromium
```

### Step 2: Create a Test with Intentional Failures

Create `tests/example.spec.js`:

```javascript
const { test, expect } = require('@playwright/test');

test('passing test', async ({ page }) => {
  await page.goto('https://playwright.dev/');
  await expect(page).toHaveTitle(/Playwright/);
});

test('failing test - wrong title', async ({ page }) => {
  await page.goto('https://playwright.dev/');
  // This will fail intentionally
  await expect(page).toHaveTitle(/This Will Fail/);
});

test('failing test - timeout', async ({ page }) => {
  await page.goto('https://playwright.dev/');
  // This will timeout
  await page.waitForSelector('.does-not-exist', { timeout: 5000 });
});

test('another passing test', async ({ page }) => {
  await page.goto('https://example.com');
  await expect(page.locator('h1')).toBeVisible();
});
```

### Step 3: Configure Playwright

Create `playwright.config.js`:

```javascript
module.exports = {
  testDir: './tests',
  timeout: 30000,
  use: {
    headless: true,
    viewport: { width: 1280, height: 720 },
  },
};
```

### Step 4: Create the GitHub Action Workflow

Create `.github/workflows/test-failure-analyzer.yml` with the content from Option 1.

### Step 5: Push to GitHub

```bash
# Create repository on GitHub first, then:
git add .
git commit -m "Initial commit with test failures"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/playwright-test-repo.git
git push -u origin main
```

---

## Option 3: Test Locally with the Test Script

You can test the action locally using the test directory:

```bash
# Clone the action repository
git clone https://github.com/decision-crafters/playwright-failure-analyzer.git
cd playwright-failure-analyzer

# Create a test Playwright project
mkdir -p /tmp/test-project
cd /tmp/test-project

# Set up test environment (copy from example above)
# ... create tests with failures ...

# Run your tests to generate a report
npx playwright test --reporter=json > test-results.json

# Run the action's parser
python /path/to/playwright-failure-analyzer/src/parse_report.py \
  --report-path test-results.json \
  --max-failures 5 \
  --output failure_summary.json

# Check the output
cat failure_summary.json
```

---

## Testing AI Analysis

### Step 1: Add Your API Key to GitHub Secrets

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `OPENROUTER_API_KEY` (or `OPENAI_API_KEY`)
5. Value: Your API key
6. Click **Add secret**

### Step 2: Update the Workflow

Modify `.github/workflows/test-failure-analyzer.yml` to add AI analysis:

```yaml
      - name: Analyze failures with AI
        if: always()
        uses: decision-crafters/playwright-failure-analyzer@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          report-path: 'test-results.json'
          ai-analysis: true  # Enable AI
        env:
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
          AI_MODEL: 'openrouter/deepseek/deepseek-chat'  # Cheapest option!
```

---

## What to Look For

### ✅ Success Indicators

1. **Workflow completes successfully** (green checkmark in Actions)
2. **Issue is created** in the Issues tab
3. **Issue contains:**
   - Test failure details
   - Stack traces
   - File paths and line numbers
   - Error messages
   - (If AI enabled) AI analysis section

### 📊 Example Issue Output

Your created issue should look like this:

```markdown
# 🚨 Playwright Test Failures Detected

## 📊 Test Run Summary

- **Total Tests:** 4
- **Passed:** 2 ✅
- **Failed:** 2 ❌
- **Flaky:** 0 ⚠️
- **Skipped:** 0 ⏭️

---

## ❌ Failed Tests

### 1. failing test - wrong title

**File:** `tests/example.spec.js:7`
**Duration:** 2.3s
**Retries:** 0

**Error:**
```
expect(page).toHaveTitle(expected)

Expected pattern: /This Will Fail/
Received string:  "Playwright | Fast and reliable end-to-end testing"
```

**Stack Trace:**
```
at tests/example.spec.js:10:18
```

---

### 2. failing test - timeout

**File:** `tests/example.spec.js:14`
...
```

---

## ❓ Frequently Asked Questions

### Q: Do I need to specify where my Playwright test files are located?

**A: No!** Playwright automatically discovers test files based on your configuration.

**How it works:**
1. Playwright reads your `playwright.config.js` (or `.ts`)
2. Uses the `testDir` setting (default: `./tests`)
3. Finds files matching `*.spec.js`, `*.test.js`, etc.

**In your workflow, this just works:**
```yaml
- run: npx playwright test --reporter=json > test-results.json
```

**Only specify the directory if:**
- You have no config file
- You want to run a subset of tests
- You have a non-standard setup

**Example with custom directory:**
```yaml
- run: npx playwright test e2e/ --reporter=json > test-results.json
```

### Q: What if my tests are in a custom location?

**A: Playwright will still find them if configured properly.**

**Option 1:** Update your `playwright.config.js`:
```javascript
module.exports = {
  testDir: './my-custom-tests',  // Point to your test directory
  // ...
};
```

**Option 2:** Specify in the workflow:
```yaml
- run: npx playwright test my-custom-tests/ --reporter=json > test-results.json
```

### Q: What's the difference between test location and report path?

**A: Two different things!**

- **Test location**: Where Playwright **finds** your `*.spec.js` files
  - Configured in `playwright.config.js`
  - Automatic discovery
  - You usually don't specify this in the workflow

- **Report path**: Where the JSON **report is saved**
  - You control this with `> test-results.json`
  - This is what you pass to the action's `report-path` input

**Example:**
```yaml
# Playwright finds tests automatically via config
# Report saved to 'test-results.json' (your choice)
- run: npx playwright test --reporter=json > test-results.json

# Action reads the report from where you saved it
- uses: decision-crafters/playwright-failure-analyzer@v1
  with:
    report-path: 'test-results.json'  # Must match above!
```

---

## 🔍 Troubleshooting

### Issue: No issue was created

**Possible causes:**
1. No test failures (all tests passed)
2. Missing `issues: write` permission
3. Deduplication found an existing issue

**Solutions:**
- Check workflow logs in Actions tab
- Verify permissions in workflow file
- Set `deduplicate: false` for testing

### Issue: "No report file found"

**Causes:**
- Playwright didn't generate JSON report
- Wrong report path

**Solutions:**
```yaml
# Make sure you're generating JSON output
run: npx playwright test --reporter=json > test-results.json

# Or use Playwright's built-in JSON reporter
run: npx playwright test --reporter=json
```

Then update `report-path` to match where Playwright saves the file.

### Issue: AI analysis not working

**Causes:**
- API key not set in GitHub Secrets
- `ai-analysis` not set to `true`
- API key environment variable not passed

**Solutions:**
1. Verify secret name matches: `OPENROUTER_API_KEY` or `OPENAI_API_KEY`
2. Ensure `ai-analysis: true` in workflow
3. Check `env:` section passes the API key correctly

---

## 🎯 Test Scenarios to Try

### 1. Basic Test (No Failures)
- All tests pass
- Verify action doesn't create issue when no failures

### 2. Single Failure
- Create 1 failing test
- Verify issue is created with 1 failure

### 3. Multiple Failures
- Create 3-5 failing tests
- Verify all failures are captured

### 4. Max Failures Limit
- Create 10 failing tests
- Set `max-failures: 3`
- Verify only first 3 failures are shown

### 5. AI Analysis
- Enable `ai-analysis: true`
- Add API key
- Verify AI section appears in issue

### 6. Custom Configuration
- Test custom labels
- Test custom issue title
- Test custom assignees

### 7. PR Integration
- Create a PR with failing tests
- Verify issue is created
- Test PR comment integration (if using advanced workflow)

---

## 📚 Next Steps After Testing

1. **Review the created issues** - Are they helpful? Clear?
2. **Test different configurations** - Try different inputs
3. **Test in production** - Use in your actual CI/CD pipeline
4. **Provide feedback** - Report any issues or suggestions

---

## 🆘 Need Help?

- **GitHub Issues:** [Report a problem](https://github.com/decision-crafters/playwright-failure-analyzer/issues)
- **Discussions:** [Ask a question](https://github.com/decision-crafters/playwright-failure-analyzer/discussions)
- **Examples:** Check the [examples directory](../examples/)

---

**Happy Testing!** 🎭✨
