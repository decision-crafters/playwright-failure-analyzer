# Intelligent Playwright Failure Bundler

[![GitHub release](https://img.shields.io/github/release/your-org/playwright-failure-bundler.svg)](https://github.com/your-org/playwright-failure-bundler/releases)
[![GitHub marketplace](https://img.shields.io/badge/marketplace-playwright--failure--bundler-blue?logo=github)](https://github.com/marketplace/actions/intelligent-playwright-failure-bundler)
[![CI](https://github.com/your-org/playwright-failure-bundler/workflows/CI/badge.svg)](https://github.com/your-org/playwright-failure-bundler/actions)

An intelligent GitHub Action that automatically halts Playwright test runs after a configurable number of failures and bundles error details into a single, actionable GitHub issue. This tool transforms reactive failure reporting into proactive failure management, reducing developer cognitive overload and improving debugging efficiency.

## 🚀 Features

- **🤖 AI-Powered Analysis**: Uses LiteLLM to provide intelligent root cause analysis and actionable suggestions
- **🎯 Smart Failure Detection**: Automatically parses Playwright JSON reports and detects failures
- **⚡ Configurable Thresholds**: Set custom failure limits to halt test runs early
- **📋 Intelligent Issue Creation**: Bundles multiple failures into a single, well-formatted GitHub issue
- **🔄 Deduplication**: Prevents duplicate issues for the same set of failures
- **📊 Rich Error Context**: Includes stack traces, error messages, and test metadata
- **🎨 Customizable Labels & Assignees**: Integrates seamlessly with your existing workflow
- **🧠 Multi-Model Support**: Compatible with OpenAI GPT, Anthropic Claude, and other LLM providers

## 📋 Quick Start

Add this action to your workflow after your Playwright tests:

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
        run: npx playwright test --reporter=json
        continue-on-error: true  # Important: don't fail the job on test failures

      - name: Bundle test failures
        if: always()  # Run even if tests failed
        uses: your-org/playwright-failure-bundler@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          report-path: 'test-results/results.json'
          max-failures: 5
          issue-title: '🚨 Playwright Test Failures - ${{ github.sha }}'
          issue-labels: 'bug,playwright,urgent'
          assignees: 'team-lead,qa-engineer'
```

## 🔧 Configuration

### Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `github-token` | GitHub token with `issues:write` permissions | ✅ | - |
| `report-path` | Path to the Playwright JSON report file | ❌ | `test-results/results.json` |
| `max-failures` | Maximum failures before creating an issue | ❌ | `3` |
| `issue-title` | Title for the created GitHub issue | ❌ | `Playwright Test Failures Detected` |
| `issue-labels` | Comma-separated list of labels | ❌ | `bug,playwright,test-failure` |
| `assignees` | Comma-separated list of GitHub usernames | ❌ | `` |
| `deduplicate` | Check for existing open issues | ❌ | `true` |
| `ai-analysis` | Enable AI-powered analysis using LiteLLM | ❌ | `true` |

### Outputs

| Output | Description |
|--------|-------------|
| `issue-number` | The number of the created GitHub issue |
| `issue-url` | The URL of the created GitHub issue |
| `failures-count` | Number of failures detected in the report |

## 📊 Example Issue Output

When failures are detected, the action creates a well-formatted issue like this:

```markdown
# 🚨 Playwright Test Failures Detected

**Summary**: 5 test failures detected in the latest run.

## 📋 Failure Details

### 1. Login Flow Test
- **File**: `tests/auth/login.spec.ts`
- **Error**: `expect(page.locator('[data-testid="welcome"]')).toBeVisible()`
- **Stack Trace**:
  ```
  Error: Timed out 5000ms waiting for expect(locator).toBeVisible()
  at /home/runner/work/app/tests/auth/login.spec.ts:23:5
  ```

### 2. Dashboard Navigation Test
- **File**: `tests/dashboard/navigation.spec.ts`
- **Error**: `Navigation timeout of 30000ms exceeded`
- **Stack Trace**:
  ```
  TimeoutError: Navigation timeout of 30000ms exceeded
  at /home/runner/work/app/tests/dashboard/navigation.spec.ts:15:3
  ```

## 🔍 Debug Information

- **Commit**: abc123def456
- **Branch**: feature/new-login
- **Run ID**: 1234567890
- **Total Tests**: 150
- **Failed Tests**: 5
- **Passed Tests**: 145

## 🚀 Next Steps

1. Review the failure patterns above
2. Check if this is a regression from recent changes
3. Run tests locally to reproduce the issues
4. Consider if infrastructure changes might be the cause
```

## 🛠️ Advanced Usage

### Custom Issue Templates

You can customize the issue format by modifying the action's behavior:

```yaml
- name: Bundle test failures with custom format
  uses: your-org/playwright-failure-bundler@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    issue-title: '🔥 Critical Test Failures - Build ${{ github.run_number }}'
    issue-labels: 'critical,regression,needs-investigation'
    assignees: 'senior-dev,team-lead'
    max-failures: 10
```

### Integration with Multiple Test Suites

For projects with multiple test suites:

```yaml
- name: Bundle E2E failures
  uses: your-org/playwright-failure-bundler@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    report-path: 'e2e-results/results.json'
    issue-title: '🚨 E2E Test Failures'
    issue-labels: 'e2e,critical'

- name: Bundle Integration failures  
  uses: your-org/playwright-failure-bundler@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    report-path: 'integration-results/results.json'
    issue-title: '⚠️ Integration Test Failures'
    issue-labels: 'integration,medium'
```

## 🧪 Testing

This action includes comprehensive testing:

```bash
# Run unit tests
npm test

# Run integration tests
npm run test:integration

# Run end-to-end tests
npm run test:e2e
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📖 [Documentation](docs/)
- 🐛 [Report Issues](https://github.com/your-org/playwright-failure-bundler/issues)
- 💬 [Discussions](https://github.com/your-org/playwright-failure-bundler/discussions)
- 📧 [Contact](mailto:support@your-org.com)

## 🗺️ Roadmap

- ✅ Core failure bundling functionality
- ✅ GitHub issue creation and deduplication
- 🔄 AI-powered failure analysis (in progress)
- 📋 Support for other test frameworks
- 🔗 Integration with Jira and other project management tools
- 📊 Advanced failure analytics and trends

---

Made with ❤️ by Tosin Akinosho
