# 📥 Action Inputs Reference

Complete reference for all inputs accepted by the Playwright Failure Analyzer action.

---

## Required Inputs

### `github-token`

**Type**: `string`  
**Required**: ✅ Yes  
**Default**: None

GitHub token with permissions to create issues. Typically `${{ secrets.GITHUB_TOKEN }}`.

**Required Permissions**:
- `issues: write` - To create and update issues

**Examples**:
```yaml
# Standard usage (recommended)
github-token: ${{ secrets.GITHUB_TOKEN }}

# Using a personal access token (PAT)
github-token: ${{ secrets.MY_PAT }}
```

**Security Notes**:
- The action requires `issues: write` permission in your workflow
- Uses the token to create issues via GitHub REST API
- Token is not logged or exposed
- Handles rate limiting automatically

---

## Optional Inputs

### `report-path`

**Type**: `string`  
**Required**: No  
**Default**: `test-results/results.json`

Path to the Playwright JSON report file.

**Valid Values**:
- Any valid file path (relative or absolute)
- Must point to a Playwright JSON report

**Examples**:
```yaml
# Default location
report-path: 'test-results/results.json'

# Custom location
report-path: 'playwright-output/results.json'

# In subdirectory
report-path: 'output/e2e/test-results.json'

# Using environment variable
report-path: ${{ env.TEST_RESULTS_PATH }}
```

**Tips**:
- Ensure Playwright generates JSON report: `npx playwright test --reporter=json > results.json`
- Path is relative to workspace root
- File must exist before action runs

---

### `max-failures`

**Type**: `integer`  
**Required**: No  
**Default**: `3`  
**Valid Range**: `1-100`

Maximum number of test failures to include in the created issue.

**Examples**:
```yaml
# Include only first failure
max-failures: 1

# Default: 3 failures
max-failures: 3

# Include up to 10 failures
max-failures: 10

# Include all failures (not recommended for large test suites)
max-failures: 100
```

**Guidelines**:
- **Small projects**: Use 5-10 for comprehensive view
- **Large projects**: Use 3-5 to keep issues focused
- **Debugging**: Use 1 to focus on first failure only

**Impact**:
- Higher values = more comprehensive but longer issues
- Lower values = focused issues but may miss context
- AI analysis cost increases with more failures

---

### `issue-title`

**Type**: `string`  
**Required**: No  
**Default**: `Playwright Test Failures Detected`

Title for the created GitHub issue.

**Max Length**: 256 characters  
**Supports**: GitHub expressions and environment variables

**Examples**:
```yaml
# Basic title
issue-title: 'Test Failures Detected'

# With branch name
issue-title: 'E2E Failures on ${{ github.ref_name }}'

# With run number
issue-title: 'Test Failures - Run #${{ github.run_number }}'

# With PR number
issue-title: '🚨 PR #${{ github.event.pull_request.number }} - Test Failures'

# With date
issue-title: 'Test Failures - ${{ github.run_started_at }}'

# With actor
issue-title: 'Failures triggered by @${{ github.actor }}'

# Combined
issue-title: '🚨 E2E Failures [${{ github.ref_name }}] - Run #${{ github.run_number }}'
```

**Tips**:
- Use emojis for visual impact: 🚨 ⚠️ 🐛 ❌
- Include context for easier triage
- Keep under 80 chars for readability

---

### `issue-labels`

**Type**: `string` (comma-separated)  
**Required**: No  
**Default**: `bug,playwright,test-failure`

Comma-separated list of labels to add to the created issue.

**Format**: `label1,label2,label3`  
**Labels must exist** in your repository (created automatically if they don't)

**Examples**:
```yaml
# Default labels
issue-labels: 'bug,playwright,test-failure'

# Priority labels
issue-labels: 'bug,e2e,priority-high,needs-triage'

# Team labels
issue-labels: 'bug,e2e,team-frontend,sprint-23'

# Browser-specific
issue-labels: 'bug,e2e,browser-chrome,flaky'

# Environment-specific
issue-labels: 'bug,e2e,environment-staging,production-blocker'

# Status labels
issue-labels: 'bug,e2e,status-investigating,needs-reproduction'
```

**Best Practices**:
- Always include `bug` for issue filtering
- Add `e2e` or `playwright` for categorization
- Use consistent label naming across projects
- Include priority/severity when known

---

### `assignees`

**Type**: `string` (comma-separated)  
**Required**: No  
**Default**: `` (empty - no assignees)

Comma-separated list of GitHub usernames to assign to the issue.

**Format**: `username1,username2,username3`  
**Usernames must** have access to the repository

**Examples**:
```yaml
# Single assignee
assignees: 'qa-lead'

# Multiple assignees
assignees: 'qa-lead,dev-lead'

# Team notification
assignees: 'qa-lead,frontend-dev,backend-dev'

# Using actor (person who triggered workflow)
assignees: '${{ github.actor }}'

# Conditional based on branch
assignees: ${{ github.ref == 'refs/heads/main' && 'tech-lead,qa-lead' || 'developer' }}
```

**Limits**:
- GitHub allows up to 10 assignees per issue
- Assignees must be collaborators

**Tips**:
- Use team notification services (Slack, PagerDuty) for escalation
- Consider rotating assignees to distribute load
- Use CODEOWNERS file for automatic assignment

---

### `deduplicate`

**Type**: `boolean`  
**Required**: No  
**Default**: `true`

Whether to check for existing issues with the same failures before creating a new one.

**Values**: `true` | `false`

**How it works**:
1. Generates a hash from failure signatures
2. Searches for open issues with matching hash
3. If found, skips issue creation
4. If not found, creates new issue

**Examples**:
```yaml
# Enable deduplication (default - recommended)
deduplicate: true

# Disable deduplication (always create new issue)
deduplicate: false

# Conditional based on event
deduplicate: ${{ github.event_name != 'pull_request' }}
```

**When to disable**:
- **PRs**: You want per-PR tracking
- **Development**: You're testing the action
- **Temporary**: Debugging a specific issue
- **Scheduled runs**: You want historical tracking

**When to enable** (recommended):
- **CI/CD**: Prevent issue spam
- **Main branch**: Keep issue list clean
- **Production**: Avoid duplicate notifications

---

### `ai-analysis`

**Type**: `boolean`  
**Required**: No  
**Default**: `true`

Enable AI-powered failure analysis using LiteLLM.

**Values**: `true` | `false`

**Requirements**:
- At least one AI provider API key set in environment:
  - `OPENAI_API_KEY`
  - `ANTHROPIC_API_KEY`
  - `OPENROUTER_API_KEY`
  - `DEEPSEEK_API_KEY`

**Examples**:
```yaml
# Enable AI analysis (recommended)
ai-analysis: true
env:
  OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
  AI_MODEL: 'openrouter/deepseek/deepseek-chat'

# Disable AI analysis
ai-analysis: false

# Conditional based on branch (only on main)
ai-analysis: ${{ github.ref == 'refs/heads/main' }}

# Conditional based on PR (disable for PRs to save cost)
ai-analysis: ${{ github.event_name != 'pull_request' }}
```

**What AI provides**:
- 📝 High-level summary of failures
- 🔍 Root cause analysis
- 💡 Suggested fix actions
- 🎯 Error patterns across failures
- 📊 Confidence score

**Cost Comparison**:
| Provider | Model | Cost/1000 analyses |
|----------|-------|-------------------|
| OpenRouter | DeepSeek | ~$0.30 |
| OpenAI | gpt-4o-mini | ~$0.30 |
| OpenAI | gpt-4o | ~$5.00 |
| Anthropic | Claude 3.5 | ~$6.00 |

**Best Practices**:
- Start with DeepSeek (cheapest, good quality)
- Enable only on important branches (main, staging)
- Disable for PRs if cost is a concern
- Monitor API usage and costs

---

## Environment Variables

These are set as `env` in your workflow, not as `with` inputs.

### AI Provider Keys

**Variables**:
- `OPENAI_API_KEY` - For OpenAI models
- `ANTHROPIC_API_KEY` - For Anthropic models
- `OPENROUTER_API_KEY` - For OpenRouter models
- `DEEPSEEK_API_KEY` - For DeepSeek models

**Example**:
```yaml
env:
  OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
  AI_MODEL: 'openrouter/deepseek/deepseek-chat'
```

### `AI_MODEL`

**Type**: `string`  
**Required**: No  
**Default**: `gpt-4o-mini`

Specify which AI model to use for analysis.

**Supported Models**:
```yaml
# OpenRouter (100+ models)
AI_MODEL: 'openrouter/deepseek/deepseek-chat'  # Cheapest!
AI_MODEL: 'openrouter/anthropic/claude-3.5-sonnet'
AI_MODEL: 'openrouter/meta-llama/llama-3.2-90b-instruct'

# OpenAI
AI_MODEL: 'gpt-4o-mini'  # Good balance
AI_MODEL: 'gpt-4o'       # Premium

# Anthropic
AI_MODEL: 'claude-3-5-sonnet-20240620'

# DeepSeek (direct)
AI_MODEL: 'deepseek-chat'
```

---

## Complete Example

```yaml
- name: Analyze Playwright failures
  uses: decision-crafters/playwright-failure-analyzer@v1
  with:
    # Required
    github-token: ${{ secrets.GITHUB_TOKEN }}

    # Report configuration
    report-path: 'test-results/results.json'
    max-failures: 5

    # Issue configuration
    issue-title: '🚨 E2E Failures - ${{ github.ref_name }} - Run #${{ github.run_number }}'
    issue-labels: 'bug,e2e,playwright,priority-high'
    assignees: 'qa-lead,dev-lead'

    # Behavior
    deduplicate: true
    ai-analysis: true

  env:
    # AI configuration
    OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
    AI_MODEL: 'openrouter/deepseek/deepseek-chat'
```

---

## Validation & Errors

### Input Validation

The action validates all inputs before execution:

- **github-token**: Must not be empty
- **report-path**: File must exist
- **max-failures**: Must be 1-100
- **issue-labels**: Must be valid label format
- **assignees**: Usernames validated against repository

### Common Errors

**Error**: "No report file found"
```
Solution: Check report-path points to valid JSON file
```

**Error**: "Invalid token or insufficient permissions"
```
Solution: Ensure workflow has `issues: write` permission
```

**Error**: "AI analysis failed - no API key"
```
Solution: Set appropriate API key in GitHub Secrets
```

---

## Related Documentation

- [Outputs Reference](OUTPUTS.md)
- [Examples](../examples/README.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Main README](../README.md)
