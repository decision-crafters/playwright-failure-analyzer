# 🎭 Intelligent Playwright Failure Analyzer

[![GitHub release](https://img.shields.io/github/v/release/decision-crafters/playwright-failure-analyzer)](https://github.com/decision-crafters/playwright-failure-analyzer/releases)
[![CI Status](https://github.com/decision-crafters/playwright-failure-analyzer/workflows/CI/badge.svg)](https://github.com/decision-crafters/playwright-failure-analyzer/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

> **Transform Playwright test failures into actionable GitHub issues with AI-powered insights**

An intelligent GitHub Action that automatically analyzes Playwright test failures and creates comprehensive, well-formatted GitHub issues with optional AI-powered root cause analysis and suggestions.

---

## ✨ **Key Features**

- 🤖 **AI-Powered Analysis** - Optional intelligent root cause analysis using OpenAI, Anthropic, OpenRouter, or DeepSeek
- 📊 **Smart Failure Bundling** - Groups multiple failures into a single, organized issue
- 🎯 **Configurable Limits** - Control how many failures to include
- 🔄 **Deduplication** - Prevents duplicate issues for the same failures
- 📋 **Rich Formatting** - Beautiful Markdown issues with stack traces, metadata, and context
- 🏷️ **Custom Labels & Assignees** - Integrates seamlessly with your workflow
- ⚡ **Fast & Lightweight** - Python-based with minimal dependencies
- 🔒 **Secure** - No data storage, runs entirely in your GitHub Actions environment

---

## 🚀 **Quick Start**

### Basic Usage

Add this to your workflow after your Playwright tests:

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    permissions:
      issues: write  # Required for creating issues

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright
        run: npx playwright install --with-deps

      - name: Run Playwright tests
        run: npx playwright test --reporter=json > test-results.json
        continue-on-error: true  # Don't fail the job on test failures

      - name: Analyze test failures
        if: failure()  # Only run if tests failed
        uses: decision-crafters/playwright-failure-analyzer@v1  # or @v1.0.0 for locked version
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          report-path: 'test-results.json'
          max-failures: 5
          issue-labels: 'bug,playwright,automated'
```

### With AI Analysis (Recommended)

Get intelligent insights and suggestions with AI:

```yaml
      - name: Analyze test failures with AI
        if: failure()
        uses: decision-crafters/playwright-failure-analyzer@v1  # Stable release
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          report-path: 'test-results.json'
          max-failures: 5
          issue-labels: 'bug,playwright,automated'
          ai-analysis: true  # Enable AI analysis
        env:
          # Use OpenRouter for cheapest option (~$0.0003 per analysis!)
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
          AI_MODEL: 'openrouter/deepseek/deepseek-chat'
```

---

## 📚 **Configuration**

### Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `github-token` | ✅ Yes | N/A | GitHub token with `issues: write` permission |
| `report-path` | No | `test-results/results.json` | Path to Playwright JSON report |
| `max-failures` | No | `3` | Maximum failures to include in issue |
| `issue-title` | No | `Playwright Test Failures Detected` | Title for created issues |
| `issue-labels` | No | `bug,playwright,test-failure` | Comma-separated list of labels |
| `assignees` | No | `` | Comma-separated list of GitHub usernames |
| `deduplicate` | No | `true` | Check for existing issues before creating |
| `ai-analysis` | No | `true` | Enable AI-powered analysis (requires API key) |

### Outputs

| Output | Description | Example |
|--------|-------------|---------|
| `issue-number` | Number of the created GitHub issue | `42` |
| `issue-url` | Direct URL to the created issue | `https://github.com/owner/repo/issues/42` |
| `failures-count` | Number of failures detected | `3` |

### Using Outputs

```yaml
- name: Analyze failures
  id: analyze
  uses: decision-crafters/playwright-failure-analyzer@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}

- name: Comment on PR
  if: github.event_name == 'pull_request'
  uses: actions/github-script@v7
  with:
    script: |
      github.rest.issues.createComment({
        issue_number: context.issue.number,
        owner: context.repo.owner,
        repo: context.repo.repo,
        body: `⚠️ Test failures detected: ${{ steps.analyze.outputs.failures-count }} failures. See issue #${{ steps.analyze.outputs.issue-number }}`
      })
```

---

## 🤖 **AI Analysis Setup**

The action supports multiple AI providers. Choose based on your budget and needs:

### Option 1: OpenRouter (Recommended - Cheapest)

**Cost**: ~$0.0003 per analysis (practically free!)

```yaml
env:
  OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
  AI_MODEL: 'openrouter/deepseek/deepseek-chat'
```

1. Sign up at [openrouter.ai](https://openrouter.ai/)
2. Add your API key to GitHub Secrets as `OPENROUTER_API_KEY`
3. Enable `ai-analysis: true` in your workflow

### Option 2: OpenAI

**Cost**: ~$0.0003 per analysis (gpt-4o-mini)

```yaml
env:
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  AI_MODEL: 'gpt-4o-mini'
```

### Option 3: Anthropic Claude

**Cost**: ~$0.006 per analysis (premium quality)

```yaml
env:
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  AI_MODEL: 'claude-3-5-sonnet-20240620'
```

### AI Analysis Features

When enabled, AI analysis provides:
- 📝 **Summary** - High-level overview of test failures
- 🔍 **Root Cause Analysis** - Potential underlying issues
- 💡 **Suggested Actions** - Specific steps to fix problems
- 🎯 **Error Patterns** - Common patterns across failures
- 📊 **Confidence Score** - How confident the AI is in its analysis

**Example AI Analysis Output** in GitHub Issue:
```markdown
## 🤖 AI Analysis

**Model**: deepseek-chat | **Confidence**: 85%

### Summary
The test failures indicate timing issues with element visibility. Two tests
timeout waiting for elements, suggesting async loading problems.

### Root Cause Analysis
The primary cause appears to be race conditions in the application's
asynchronous rendering. Elements are present in the DOM but not immediately
visible...

### 💡 Suggested Actions
1. Add explicit waitFor conditions before assertions
2. Increase default timeout for visibility checks
3. Implement retry logic for flaky selectors
```

---

## 📖 **Examples**

### Example 1: Basic Workflow

See [examples/basic-workflow.yml](examples/basic-workflow.yml)

### Example 2: Advanced Configuration

See [examples/advanced-workflow.yml](examples/advanced-workflow.yml)

### Example 3: Multiple Test Suites

See [examples/multi-suite-workflow.yml](examples/multi-suite-workflow.yml)

### Example 4: Integration with PR Comments

See [examples/pr-integration.yml](examples/pr-integration.yml)

---

## 🎯 **Real-World Usage**

### Issue Output Example

When failures are detected, the action creates an issue like this:

![Example Issue](docs/images/example-issue.png)

The issue includes:
- ✅ Test run summary with pass/fail counts
- ✅ Detailed failure information for each test
- ✅ Stack traces and error messages
- ✅ File locations and line numbers
- ✅ Test metadata (duration, retries, etc.)
- ✅ GitHub workflow context
- ✅ Optional AI analysis with insights

---

## 🛠️ **Troubleshooting**

### Common Issues

**Issue**: "No test report found"
```
Solution: Ensure Playwright generates a JSON report:
npx playwright test --reporter=json > test-results.json
```

**Issue**: "Permission denied when creating issue"
```
Solution: Add 'issues: write' permission to your workflow:
permissions:
  issues: write
```

**Issue**: "AI analysis not working"
```
Solution: Ensure you've set the API key in GitHub Secrets and
enabled ai-analysis: true in your workflow
```

**Issue**: "Duplicate issues being created"
```
Solution: Enable deduplication (it's on by default):
deduplicate: true
```

### Debugging

Enable debug logging in your workflow:

```yaml
- name: Analyze failures
  uses: decision-crafters/playwright-failure-analyzer@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
  env:
    ACTIONS_STEP_DEBUG: true  # Enable debug logs
```

---

## 📊 **Cost Analysis**

### AI Provider Costs (per 1000 analyses)

| Provider | Model | Cost | Best For |
|----------|-------|------|----------|
| OpenRouter | DeepSeek | ~$0.30 | Budget-conscious teams |
| OpenAI | gpt-4o-mini | ~$0.30 | Good balance |
| OpenAI | gpt-4o | ~$5.00 | High quality |
| Anthropic | Claude-3.5 | ~$6.00 | Premium quality |

💡 **Recommendation**: Start with OpenRouter + DeepSeek for excellent quality at minimal cost.

---

## ❓ **FAQ**

<details>
<summary><b>Q: Does this work with other test frameworks besides Playwright?</b></summary>

A: Currently, the action is specifically designed for Playwright JSON reports. Support for other frameworks may be added in future versions.
</details>

<details>
<summary><b>Q: Is my test data sent to third parties?</b></summary>

A: Only if you enable AI analysis. In that case, failure information is sent to your chosen AI provider (OpenAI, Anthropic, OpenRouter, etc.) for analysis. All processing happens in your GitHub Actions environment. We don't store or access any data.
</details>

<details>
<summary><b>Q: Can I customize the issue format?</b></summary>

A: Currently, the issue format is standardized for consistency. Custom templates may be added in future versions. You can customize labels, assignees, and titles.
</details>

<details>
<summary><b>Q: What happens if I hit GitHub API rate limits?</b></summary>

A: The action implements automatic retry logic with exponential backoff. Rate limits are unlikely with the standard `GITHUB_TOKEN` which has higher limits.
</details>

<details>
<summary><b>Q: Does this work with private repositories?</b></summary>

A: Yes! The action works in both public and private repositories. Just ensure you have the `issues: write` permission.
</details>

<details>
<summary><b>Q: How does deduplication work?</b></summary>

A: The action generates a hash of the failure set and checks for existing open issues with the same failures. If found, it won't create a duplicate.
</details>

---

## 🤝 **Contributing**

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

- 🐛 [Report a bug](https://github.com/decision-crafters/playwright-failure-analyzer/issues/new?template=bug_report.md)
- ✨ [Request a feature](https://github.com/decision-crafters/playwright-failure-analyzer/issues/new?template=feature_request.md)
- 💬 [Join discussions](https://github.com/decision-crafters/playwright-failure-analyzer/discussions)

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 **Acknowledgments**

- Built with [LiteLLM](https://github.com/BerriAI/litellm) for multi-provider AI support
- Inspired by the need for better test failure management in CI/CD pipelines
- Thanks to all [contributors](https://github.com/decision-crafters/playwright-failure-analyzer/graphs/contributors)

---

## 📈 **Roadmap**

- [ ] Support for additional test frameworks (Jest, Cypress, etc.)
- [ ] Custom issue templates
- [ ] Slack/Discord notifications
- [ ] Historical failure tracking
- [ ] Failure trend analysis
- [ ] Integration with issue tracking systems (Jira, Linear, etc.)

---

## 🔗 **Links**

- [📖 Full Documentation](https://github.com/decision-crafters/playwright-failure-analyzer/tree/main/docs)
- [🎯 Examples](https://github.com/decision-crafters/playwright-failure-analyzer/tree/main/examples)
- [📝 Changelog](CHANGELOG.md)
- [🐛 Issue Tracker](https://github.com/decision-crafters/playwright-failure-analyzer/issues)
- [💬 Discussions](https://github.com/decision-crafters/playwright-failure-analyzer/discussions)

---

<div align="center">

**Made with ❤️ by the Decision Crafters team**

[⭐ Star this repo](https://github.com/decision-crafters/playwright-failure-analyzer) | [🐦 Follow us on Twitter](https://twitter.com/decision_crafters) | [💼 Visit our website](https://decisioncrafters.io)

</div>
