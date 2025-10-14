# Suggested README Update for Demo Repository

Add this section to the demo repository's README.md to explain the dual workflow setup.

---

## 🎯 Demo Workflows

This repository demonstrates the Playwright Failure Analyzer with **two workflow configurations**:

### 1. Basic Failure Analysis (No AI)
**File:** `.github/workflows/test-intentional-failures.yml`

Demonstrates core functionality without requiring AI configuration:
- Automatic GitHub issue creation
- Structured failure reports
- Error messages and stack traces
- File paths and line numbers

**✅ No API key required**
**✅ Free to run**
**✅ Quick setup**

[View Example Issue](#) <!-- Link to an example issue -->

---

### 2. AI-Powered Analysis with DeepSeek
**File:** `.github/workflows/test-with-ai-analysis.yml`

Demonstrates enhanced analysis with AI insights:
- Everything from basic workflow
- **🤖 Root cause analysis**
- **🤖 Suggested fixes**
- **🤖 Priority recommendations**
- **🤖 Pattern detection**

**Requires:**
- DeepSeek API key (via OpenRouter)
- Repository secret: `DEEPSEEK_API_KEY`

**Cost:** ~$0.0003 per analysis (less than a penny)

[Setup Instructions](.github/AI_SETUP.md) | [View AI Example Issue](#) <!-- Link to AI-enhanced example -->

---

## 🚀 Quick Start

### Try Basic Analysis (No Setup)
1. Fork this repository
2. Push a commit or create a PR
3. Check the Issues tab for automatically created failure reports

### Try AI Analysis (5-Minute Setup)
1. Get an API key from [OpenRouter](https://openrouter.ai) ($5 minimum)
2. Add secret `DEEPSEEK_API_KEY` in repository settings
3. Manually trigger the "Test with AI Analysis" workflow
4. Compare the AI-enhanced issue with the basic one

---

## 📊 Comparison

| Feature | Basic Workflow | AI Workflow |
|---------|---------------|-------------|
| Test failure detection | ✅ | ✅ |
| Error messages & stack traces | ✅ | ✅ |
| File paths & line numbers | ✅ | ✅ |
| Retry information | ✅ | ✅ |
| Root cause analysis | ❌ | ✅ |
| Suggested fixes | ❌ | ✅ |
| Priority recommendations | ❌ | ✅ |
| Pattern detection | ❌ | ✅ |
| **Setup required** | None | API key |
| **Cost per run** | Free | ~$0.0003 |
| **Execution time** | ~30s | ~40s |

---

## 🛠️ Using in Your Project

Choose the workflow that fits your needs:

### For Quick Setup (Basic)
```yaml
- name: Analyze failures
  if: steps.tests.outputs.test-failed == 'true'
  uses: decision-crafters/playwright-failure-analyzer@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

### For Enhanced Insights (AI)
```yaml
- name: Analyze failures with AI
  if: steps.tests.outputs.test-failed == 'true'
  uses: decision-crafters/playwright-failure-analyzer@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    ai-analysis: true
  env:
    OPENROUTER_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
    AI_MODEL: 'openrouter/deepseek/deepseek-chat'
```

Full examples available in the [main repository](https://github.com/decision-crafters/playwright-failure-analyzer/tree/main/examples).

---

## 📖 Documentation

- [Full Setup Guide](.github/AI_SETUP.md)
- [Main Repository](https://github.com/decision-crafters/playwright-failure-analyzer)
- [Configuration Options](https://github.com/decision-crafters/playwright-failure-analyzer/blob/main/docs/CONFIGURATION.md)
- [Troubleshooting](https://github.com/decision-crafters/playwright-failure-analyzer/blob/main/docs/TROUBLESHOOTING.md)

---

## 💡 Why Two Workflows?

**Flexibility:** Users can see both options and choose what works for them

**Learning:** Compare basic vs AI-enhanced reports side by side

**Cost Control:** Not everyone wants or needs AI analysis

**Demonstration:** Shows the full capabilities without forcing AI adoption
