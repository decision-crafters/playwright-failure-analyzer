# 🤖 AI Assistant Quick Reference

**For AI assistants (Claude, ChatGPT, etc.) helping developers integrate this action**

---

## 🎯 Quick Template

When a developer asks to add Playwright failure reporting, use this template:

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    permissions:
      issues: write  # REQUIRED for creating issues

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright
        run: npx playwright install --with-deps

      - name: Run Playwright tests
        run: npx playwright test --reporter=json > test-results.json
        continue-on-error: true  # REQUIRED so action runs even on failures

      - name: Analyze failures
        if: failure()  # Only run when tests fail
        uses: decision-crafters/playwright-failure-analyzer@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

---

## ✅ Required Elements Checklist

Before providing a workflow, verify it has ALL of these:

### 1. Permissions Block
```yaml
permissions:
  issues: write  # ← MUST have this
```

### 2. Continue on Error
```yaml
run: npx playwright test --reporter=json > test-results.json
continue-on-error: true  # ← MUST have this
```

### 3. Conditional Execution
```yaml
if: failure()  # ← MUST have this (or if: always() for testing)
```

### 4. Matching Report Paths
```yaml
# These MUST match:
run: ... > test-results.json
         ↑
with:
  report-path: 'test-results.json'
```

---

## 🚨 Common Mistakes to Avoid

### ❌ Missing Permissions
```yaml
# BAD - No permissions
jobs:
  test:
    runs-on: ubuntu-latest
```

```yaml
# GOOD - Has permissions
jobs:
  test:
    runs-on: ubuntu-latest
    permissions:
      issues: write
```

### ❌ Missing continue-on-error
```yaml
# BAD - Workflow stops on test failure, action never runs
- run: npx playwright test --reporter=json > test-results.json
```

```yaml
# GOOD - Workflow continues, action can run
- run: npx playwright test --reporter=json > test-results.json
  continue-on-error: true
```

### ❌ Wrong Report Path
```yaml
# BAD - Mismatch
- run: npx playwright test --reporter=json > results.json
- uses: decision-crafters/playwright-failure-analyzer@v1
  with:
    report-path: 'test-results.json'  # Different filename!
```

```yaml
# GOOD - Matching
- run: npx playwright test --reporter=json > test-results.json
- uses: decision-crafters/playwright-failure-analyzer@v1
  with:
    report-path: 'test-results.json'  # Same filename
```

### ❌ No Conditional
```yaml
# BAD - Runs even when tests pass (wastes time, confusing)
- uses: decision-crafters/playwright-failure-analyzer@v1
```

```yaml
# GOOD - Only runs when needed
- if: failure()
  uses: decision-crafters/playwright-failure-analyzer@v1
```

---

## 🎨 Configuration Variants

### Variant 1: Basic (No customization)
```yaml
- uses: decision-crafters/playwright-failure-analyzer@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

### Variant 2: Custom Labels
```yaml
- uses: decision-crafters/playwright-failure-analyzer@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    issue-labels: 'bug,e2e,priority-high'
    issue-title: 'E2E Failures - ${{ github.ref_name }}'
```

### Variant 3: With AI Analysis
```yaml
- uses: decision-crafters/playwright-failure-analyzer@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    ai-analysis: true
  env:
    OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
    AI_MODEL: 'openrouter/deepseek/deepseek-chat'
```

### Variant 4: PR Integration
```yaml
- name: Analyze failures
  if: failure()
  id: analyze
  uses: decision-crafters/playwright-failure-analyzer@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    deduplicate: false  # Always create for PRs

- name: Comment on PR
  if: failure() && github.event_name == 'pull_request'
  uses: actions/github-script@v7
  with:
    script: |
      github.rest.issues.createComment({
        issue_number: context.issue.number,
        owner: context.repo.owner,
        repo: context.repo.repo,
        body: `⚠️ Tests failed. See #${{ steps.analyze.outputs.issue-number }}`
      })
```

---

## 🤖 AI Analysis Setup

### When to Recommend AI Analysis

**✅ Recommend when:**
- Developer mentions wanting "insights" or "root cause"
- Multiple tests are failing
- They want to understand patterns
- Budget is mentioned or unlimited

**❌ Don't recommend when:**
- Developer explicitly says "no AI" or "no cost"
- Very frequent test runs (thousands per day)
- Extremely tight budget
- Single obvious failure

### AI Setup Instructions

**Step 1:** User needs to:
1. Get API key from OpenRouter (https://openrouter.ai) or OpenAI
2. Add to GitHub Secrets as `OPENROUTER_API_KEY` or `OPENAI_API_KEY`

**Step 2:** Add to workflow:
```yaml
env:
  OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
  AI_MODEL: 'openrouter/deepseek/deepseek-chat'  # Cheapest!
```

**Cost transparency:**
- DeepSeek: ~$0.0003 per analysis (~$0.30 per 1000 runs)
- GPT-4o-mini: ~$0.0003 per analysis
- GPT-4o: ~$0.005 per analysis (~$5 per 1000 runs)

---

## 💬 Response Templates

### When Developer Asks: "How do I add Playwright failure reporting?"

```
I'll help you set up the Playwright Failure Analyzer! This will automatically
create GitHub issues when your tests fail.

Here's what you need:

1. Create `.github/workflows/playwright-tests.yml`:
[provide full template from top of this guide]

2. Commit and push this file

3. The action will run automatically when tests fail

Key points:
- ✅ Runs automatically on push/PR
- ✅ Creates beautiful GitHub issues
- ✅ Optional AI analysis available
- ✅ Free to use (except optional AI costs)

Would you like me to add AI analysis for intelligent insights?
```

### When Developer Asks: "My tests are failing but no issue is created"

```
Let me check your workflow. Common issues:

1. Missing `permissions: issues: write`
2. Missing `continue-on-error: true` on test step  
3. Missing `if: failure()` on analyzer step
4. Report path mismatch

Can you share your workflow file? I'll identify the issue.

Meanwhile, here's a working reference:
[provide template]
```

### When Developer Asks: "How do I add AI analysis?"

```
To enable AI-powered failure analysis:

1. Get an API key:
   - OpenRouter (cheapest): https://openrouter.ai
   - OpenAI: https://platform.openai.com

2. Add to GitHub Secrets:
   - Go to: Settings → Secrets and variables → Actions
   - New secret: OPENROUTER_API_KEY
   - Value: [paste your key]

3. Update your workflow:
```yaml
- uses: decision-crafters/playwright-failure-analyzer@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    ai-analysis: true  # ← Add this
  env:
    OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}  # ← Add this
    AI_MODEL: 'openrouter/deepseek/deepseek-chat'  # ← Add this (optional)
```

Cost: ~$0.0003 per analysis with DeepSeek (practically free!)
```

### When Developer Reports: "File not found: test-results/results.json"

```
This is a path mismatch. Here's how to fix it:

The issue is that your test command creates the file in one location,
but the action looks in another.

Your current setup probably has:
```yaml
run: npx playwright test --reporter=json > test-results.json
```

But the action is looking for: `test-results/results.json`

**Fix:** Explicitly set the report path:
```yaml
- uses: decision-crafters/playwright-failure-analyzer@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    report-path: 'test-results.json'  # ← Add this line
```

This tells the action to look for the file where you actually created it.
```

---

## 🔧 Debugging Steps

When helping debug issues:

### 1. Verify Workflow Structure
```yaml
✅ Has permissions block with issues: write
✅ Test step has continue-on-error: true  
✅ Action step has if: failure()
✅ Report path matches between test and action
✅ Using @v1 tag (not @main)
```

### 2. Check GitHub Actions Log
Ask developer to:
1. Go to Actions tab
2. Click failed workflow run
3. Expand "Analyze failures" step
4. Share the error message

### 3. Common Error Messages

| Error | Cause | Fix |
|-------|-------|-----|
| "File not found" | Path mismatch | Match `report-path` to output file |
| "Permission denied" | Missing permission | Add `issues: write` |
| "Action step skipped" | Wrong conditional | Change `if:` condition |
| "AI analysis failed" | Missing API key | Add secret and env var |

---

## 📚 Quick Links to Share

- **Full Documentation:** https://github.com/decision-crafters/playwright-failure-analyzer
- **How It Works:** [docs/HOW_IT_WORKS.md](HOW_IT_WORKS.md)
- **Examples:** [examples/](../examples/)
- **Input Reference:** [docs/INPUTS.md](INPUTS.md)
- **Output Reference:** [docs/OUTPUTS.md](OUTPUTS.md)

---

## 🎓 Understanding Levels

Match your explanation to the developer's level:

### Beginner Developer
- Explain what GitHub Actions are
- Show complete working example
- Explain each line
- Offer to walk through setup

### Intermediate Developer
- Provide working template
- Highlight key configuration options
- Link to examples for customization

### Advanced Developer
- Concise config reference
- Link directly to INPUTS.md
- Mention advanced features (AI, outputs, etc.)

---

## ✅ Pre-Response Checklist

Before sending a workflow to a developer, verify:

- [ ] Has `permissions: issues: write`
- [ ] Has `continue-on-error: true` on test step
- [ ] Has `if: failure()` or `if: always()` on action
- [ ] Report paths match
- [ ] Uses `@v1` tag (not `@main`)
- [ ] If AI enabled: has API key secret and env var
- [ ] Syntax is valid YAML (proper indentation)
- [ ] All required inputs are present

---

**Remember:** The goal is to help developers successfully integrate the action
with minimal friction. Always provide complete, working examples!

🤖✨
