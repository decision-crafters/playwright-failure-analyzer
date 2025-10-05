# 📚 Workflow Examples

This directory contains practical examples showing different ways to use the Playwright Failure Analyzer in your GitHub Actions workflows.

## 📖 Available Examples

### 1. [Basic Workflow](basic-workflow.yml)
**Use this if**: You're just getting started and want the simplest setup.

**Features**:
- Minimal configuration
- Default settings
- Perfect for quick setup

**Copy-paste ready**: Yes ✅

---

### 2. [Advanced Workflow](advanced-workflow.yml)
**Use this if**: You want full control over all options.

**Features**:
- All configuration options demonstrated
- Custom labels and assignees
- AI analysis enabled
- Artifact uploads
- PR comments

**Best for**: Production environments

---

### 3. [PR Integration](pr-integration.yml)
**Use this if**: You want to block PRs that have failing tests.

**Features**:
- Automatic PR comments with test results
- Links to detailed failure issues
- Status check integration
- Per-PR failure tracking

**Best for**: Teams using PR-based workflows

---

### 4. [AI Analysis](ai-analysis-workflow.yml)
**Use this if**: You want to compare different AI providers or understand AI setup.

**Features**:
- 4 different AI provider configurations:
  - OpenRouter + DeepSeek (cheapest)
  - OpenAI GPT-4o-mini (good balance)
  - Anthropic Claude 3.5 (premium)
  - No AI (fastest, free)
- Cost comparisons
- Side-by-side examples

**Best for**: Evaluating AI options

---

### 5. [Multi-Suite Workflow](multi-suite-workflow.yml)
**Use this if**: You run tests on multiple browsers or devices.

**Features**:
- Separate jobs for Chrome, Firefox, Mobile
- Individual failure tracking per browser
- Combined summary
- Browser-specific labels

**Best for**: Cross-browser testing

---

## 🚀 Quick Start Guide

### Step 1: Choose Your Example

Pick the example that best matches your needs from the list above.

### Step 2: Copy to Your Repository

```bash
# Copy the example to your .github/workflows/ directory
cp examples/basic-workflow.yml .github/workflows/e2e-tests.yml
```

### Step 3: Customize

Update these values in your workflow:
- `report-path`: Path to your Playwright JSON report
- `issue-labels`: Labels that make sense for your project
- `assignees`: Team members to notify (optional)

### Step 4: Set Up AI (Optional)

If using AI analysis:

1. Choose a provider (OpenRouter recommended for cost)
2. Get an API key
3. Add it to GitHub Secrets:
   - Go to: Settings → Secrets and variables → Actions
   - Add: `OPENROUTER_API_KEY`
4. Ensure `ai-analysis: true` in your workflow

### Step 5: Commit and Push

```bash
git add .github/workflows/e2e-tests.yml
git commit -m "Add Playwright failure analysis"
git push
```

---

## 💡 Tips & Best Practices

### 1. Always Use `continue-on-error: true`

```yaml
- name: Run Playwright tests
  run: npx playwright test --reporter=json > test-results.json
  continue-on-error: true  # ← Important!
```

This ensures the failure analyzer runs even when tests fail.

### 2. Use `if: failure()` Condition

```yaml
- name: Analyze failures
  if: failure()  # Only run when tests fail
  uses: decision-crafters/playwright-failure-analyzer@v1
```

Saves GitHub Actions minutes by only running when needed.

### 3. Set Appropriate Permissions

```yaml
permissions:
  issues: write  # Required!
  pull-requests: write  # Optional, for PR comments
```

Without `issues: write`, the action can't create issues.

### 4. Start Simple, Then Enhance

1. Start with `basic-workflow.yml`
2. Get it working
3. Add AI analysis
4. Customize labels and assignees
5. Add PR integration if needed

### 5. Cost Management for AI

**Budget-conscious**:
```yaml
env:
  OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
  AI_MODEL: 'openrouter/deepseek/deepseek-chat'
  # ~$0.30 per 1000 analyses
```

**Quality-focused**:
```yaml
env:
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  AI_MODEL: 'gpt-4o'
  # ~$5.00 per 1000 analyses
```

---

## 🔧 Common Customizations

### Change the Report Path

```yaml
with:
  report-path: 'playwright-results/results.json'
```

### Limit Number of Failures

```yaml
with:
  max-failures: 3  # Only include first 3 failures
```

### Custom Issue Title

```yaml
with:
  issue-title: '🚨 E2E Failures - ${{ github.ref_name }} - Run #${{ github.run_number }}'
```

### Multiple Labels

```yaml
with:
  issue-labels: 'bug,e2e,playwright,priority-high,needs-triage'
```

### Assign to Team

```yaml
with:
  assignees: 'qa-lead,dev-lead,team-member'
```

---

## 📊 Cost Estimates

### Without AI
- **Cost**: $0.00
- **Time**: ~2 seconds
- **Best for**: Budget-conscious teams

### With AI (DeepSeek via OpenRouter)
- **Cost**: ~$0.0003 per analysis
- **Time**: ~7 seconds
- **Best for**: Most teams (best value)

### With AI (GPT-4o-mini)
- **Cost**: ~$0.0003 per analysis
- **Time**: ~5 seconds
- **Best for**: Good balance

### With AI (Claude 3.5)
- **Cost**: ~$0.006 per analysis
- **Time**: ~8 seconds
- **Best for**: Premium quality needs

---

## 🆘 Troubleshooting

### Issue: "No report file found"

**Solution**: Ensure Playwright generates a JSON report:
```yaml
run: npx playwright test --reporter=json > test-results.json
```

### Issue: "Permission denied"

**Solution**: Add permissions to your workflow:
```yaml
permissions:
  issues: write
```

### Issue: "AI analysis not working"

**Solution**: Check that:
1. API key is in GitHub Secrets
2. `ai-analysis: true` is set
3. API key environment variable is set correctly

### Issue: "Too many failures in issue"

**Solution**: Reduce `max-failures`:
```yaml
with:
  max-failures: 3  # Lower number
```

---

## 📚 Additional Resources

- [Main Documentation](../README.md)
- [AI Testing Guide](../docs/AI_TESTING_GUIDE.md)
- [Input/Output Reference](../docs/INPUTS.md)
- [Troubleshooting Guide](../docs/TROUBLESHOOTING.md)
- [Contributing Guidelines](../CONTRIBUTING.md)

---

## 🤝 Need Help?

- 💬 [GitHub Discussions](https://github.com/decision-crafters/playwright-failure-analyzer/discussions)
- 🐛 [Report an Issue](https://github.com/decision-crafters/playwright-failure-analyzer/issues)
- 📖 [Full Documentation](https://github.com/decision-crafters/playwright-failure-analyzer)

---

**Happy Testing!** 🎭✨
