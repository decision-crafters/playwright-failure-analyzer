# 📤 Action Outputs Reference

Complete reference for all outputs provided by the Playwright Failure Analyzer action.

---

## Available Outputs

### `issue-number`

**Type**: `string`  
**Description**: The number of the created or found GitHub issue.

**Value**:
- Integer as string (e.g., `"42"`)
- Empty string if no issue was created (no failures or deduplication hit)

**Examples**:
```yaml
- name: Analyze failures
  id: analyze
  uses: decision-crafters/playwright-failure-analyzer@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}

- name: Use issue number
  run: |
    echo "Created issue #${{ steps.analyze.outputs.issue-number }}"
```

**Use Cases**:
- Link to issue in PR comments
- Reference in subsequent workflow steps
- Track in external systems
- Generate notifications

---

### `issue-url`

**Type**: `string`  
**Description**: Direct URL to the created or found GitHub issue.

**Format**: `https://github.com/{owner}/{repo}/issues/{number}`

**Value**:
- Full HTTPS URL (e.g., `"https://github.com/org/repo/issues/42"`)
- Empty string if no issue was created

**Examples**:
```yaml
- name: Analyze failures
  id: analyze
  uses: decision-crafters/playwright-failure-analyzer@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}

- name: Use issue URL
  run: |
    echo "Issue created: ${{ steps.analyze.outputs.issue-url }}"
```

**Use Cases**:
- Direct links in notifications
- Embed in Slack/Discord messages
- Add to PR comments
- Reference in documentation

---

### `failures-count`

**Type**: `string`  
**Description**: Total number of test failures detected in the report.

**Value**:
- Integer as string (e.g., `"3"`)
- `"0"` if no failures detected

**Note**: This is the total count, which may be higher than the number shown in the issue if `max-failures` limit is set.

**Examples**:
```yaml
- name: Analyze failures
  id: analyze
  uses: decision-crafters/playwright-failure-analyzer@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    max-failures: 3

- name: Check failure count
  run: |
    count="${{ steps.analyze.outputs.failures-count }}"
    echo "Detected $count test failure(s)"

    if [ "$count" -gt 10 ]; then
      echo "⚠️ High failure count detected!"
    fi
```

**Use Cases**:
- Conditional logic based on severity
- Metrics and reporting
- Alerting thresholds
- Dashboard updates

---

## Complete Usage Examples

### Example 1: Basic Output Usage

```yaml
- name: Run tests
  run: npx playwright test --reporter=json > test-results.json
  continue-on-error: true

- name: Analyze failures
  id: analyze
  uses: decision-crafters/playwright-failure-analyzer@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    report-path: 'test-results.json'

- name: Print results
  if: always()
  run: |
    echo "Issue Number: ${{ steps.analyze.outputs.issue-number }}"
    echo "Issue URL: ${{ steps.analyze.outputs.issue-url }}"
    echo "Failures: ${{ steps.analyze.outputs.failures-count }}"
```

---

### Example 2: PR Comment with Issue Link

```yaml
- name: Analyze failures
  if: failure()
  id: analyze
  uses: decision-crafters/playwright-failure-analyzer@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}

- name: Comment on PR
  if: github.event_name == 'pull_request' && steps.analyze.outputs.issue-number
  uses: actions/github-script@v7
  with:
    script: |
      const issueNumber = '${{ steps.analyze.outputs.issue-number }}';
      const issueUrl = '${{ steps.analyze.outputs.issue-url }}';
      const failureCount = '${{ steps.analyze.outputs.failures-count }}';

      const comment = `## ⚠️ Test Failures Detected

      **${failureCount} test failure(s)** were detected in this PR.

      📋 [View detailed failure report](#${issueNumber})

      Please fix the failing tests before merging.

      <details>
      <summary>Quick Actions</summary>

      - [View full report](${issueUrl})
      - [Re-run workflow](${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }})

      </details>`;

      github.rest.issues.createComment({
        issue_number: context.issue.number,
        owner: context.repo.owner,
        repo: context.repo.repo,
        body: comment
      });
```

---

### Example 3: Conditional Workflow Steps

```yaml
- name: Analyze failures
  id: analyze
  if: failure()
  uses: decision-crafters/playwright-failure-analyzer@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}

# Only run for high failure counts
- name: Alert on high failure rate
  if: steps.analyze.outputs.failures-count > 10
  run: |
    echo "::error::Critical: More than 10 tests failing!"
    # Send alert to monitoring system
    curl -X POST ${{ secrets.ALERT_WEBHOOK }} \
      -d '{"failures": ${{ steps.analyze.outputs.failures-count }}}'

# Only run if issue was created
- name: Update project board
  if: steps.analyze.outputs.issue-number != ''
  uses: actions/github-script@v7
  with:
    script: |
      // Add issue to project board
      const issueNumber = parseInt('${{ steps.analyze.outputs.issue-number }}');
      // ... project board logic
```

---

### Example 4: Slack Notification

```yaml
- name: Analyze failures
  id: analyze
  if: failure()
  uses: decision-crafters/playwright-failure-analyzer@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}

- name: Send Slack notification
  if: steps.analyze.outputs.issue-number != ''
  uses: slackapi/slack-github-action@v1
  with:
    payload: |
      {
        "text": "🚨 E2E Test Failures Detected",
        "blocks": [
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "*E2E Test Failures*\n${{ steps.analyze.outputs.failures-count }} test(s) failed"
            }
          },
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "<${{ steps.analyze.outputs.issue-url }}|View Detailed Report #${{ steps.analyze.outputs.issue-number }}>"
            }
          }
        ]
      }
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

---

### Example 5: Metrics Collection

```yaml
- name: Analyze failures
  id: analyze
  if: failure()
  uses: decision-crafters/playwright-failure-analyzer@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}

- name: Record metrics
  if: always()
  run: |
    # Send metrics to monitoring system (DataDog, New Relic, etc.)
    FAILURE_COUNT="${{ steps.analyze.outputs.failures-count }}"

    # Example: DataDog StatsD
    echo "playwright.failures:${FAILURE_COUNT}|c" | nc -u -w1 statsd.example.com 8125

    # Example: Custom metrics endpoint
    curl -X POST https://metrics.example.com/api/test-results \
      -H "Content-Type: application/json" \
      -d '{
        "repository": "${{ github.repository }}",
        "branch": "${{ github.ref_name }}",
        "run_id": "${{ github.run_id }}",
        "failures": '"${FAILURE_COUNT}"',
        "issue_url": "${{ steps.analyze.outputs.issue-url }}",
        "timestamp": "'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'"
      }'
```

---

### Example 6: Multi-Step Workflow with Outputs

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    outputs:
      issue-number: ${{ steps.analyze.outputs.issue-number }}
      issue-url: ${{ steps.analyze.outputs.issue-url }}
      failures-count: ${{ steps.analyze.outputs.failures-count }}

    steps:
      - uses: actions/checkout@v4

      - name: Run tests
        run: npx playwright test --reporter=json > test-results.json
        continue-on-error: true

      - name: Analyze failures
        id: analyze
        if: failure()
        uses: decision-crafters/playwright-failure-analyzer@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}

  notify:
    needs: test
    if: needs.test.outputs.issue-number != ''
    runs-on: ubuntu-latest

    steps:
      - name: Send notifications
        run: |
          echo "Issue created: ${{ needs.test.outputs.issue-url }}"
          echo "Failures: ${{ needs.test.outputs.failures-count }}"

          # Send to multiple channels
          # Email, Slack, PagerDuty, etc.
```

---

### Example 7: Update Existing PR Description

```yaml
- name: Analyze failures
  id: analyze
  if: failure()
  uses: decision-crafters/playwright-failure-analyzer@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}

- name: Update PR description
  if: github.event_name == 'pull_request' && steps.analyze.outputs.issue-number
  uses: actions/github-script@v7
  with:
    script: |
      const { data: pr } = await github.rest.pulls.get({
        owner: context.repo.owner,
        repo: context.repo.repo,
        pull_number: context.issue.number,
      });

      const testBadge = `\n\n---\n\n⚠️ **Test Status**: ${
        '${{ steps.analyze.outputs.failures-count }}'
      } failure(s) - [View Report](#${{ steps.analyze.outputs.issue-number }})`;

      await github.rest.pulls.update({
        owner: context.repo.owner,
        repo: context.repo.repo,
        pull_number: context.issue.number,
        body: pr.body + testBadge,
      });
```

---

## Output Availability Matrix

| Scenario | issue-number | issue-url | failures-count |
|----------|--------------|-----------|----------------|
| New issue created | ✅ Set | ✅ Set | ✅ Set |
| Duplicate issue found (dedup enabled) | ✅ Set (existing) | ✅ Set (existing) | ✅ Set |
| No failures detected | ❌ Empty | ❌ Empty | `"0"` |
| Action skipped (no report) | ❌ Empty | ❌ Empty | ❌ Empty |

---

## Best Practices

### 1. Always Check If Output Exists

```yaml
- name: Use output safely
  if: steps.analyze.outputs.issue-number != ''
  run: echo "Issue: ${{ steps.analyze.outputs.issue-number }}"
```

### 2. Use Outputs in Conditional Steps

```yaml
- name: High severity alert
  if: steps.analyze.outputs.failures-count > 5
  run: echo "::error::High failure rate!"
```

### 3. Pass Outputs Between Jobs

```yaml
jobs:
  test:
    outputs:
      issue-url: ${{ steps.analyze.outputs.issue-url }}
    steps:
      - id: analyze
        uses: decision-crafters/playwright-failure-analyzer@v1

  notify:
    needs: test
    steps:
      - run: echo "${{ needs.test.outputs.issue-url }}"
```

### 4. Combine Multiple Outputs

```yaml
- name: Comprehensive summary
  run: |
    cat << EOF
    ## Test Results Summary

    - Failures Detected: ${{ steps.analyze.outputs.failures-count }}
    - Issue Number: #${{ steps.analyze.outputs.issue-number }}
    - Issue URL: ${{ steps.analyze.outputs.issue-url }}
    EOF
```

---

## Troubleshooting

### Output is Empty

**Possible causes**:
1. Action didn't run (check `if` conditions)
2. No failures detected
3. Deduplication found existing issue (check `deduplicate` setting)
4. Action failed (check logs)

**Solution**:
```yaml
- name: Debug outputs
  if: always()
  run: |
    echo "Issue Number: '${{ steps.analyze.outputs.issue-number }}'"
    echo "Issue URL: '${{ steps.analyze.outputs.issue-url }}'"
    echo "Failures: '${{ steps.analyze.outputs.failures-count }}'"
```

### Output Shows Wrong Value

**Check**:
1. Step ID matches: `steps.analyze.outputs.*`
2. Output is accessed after action runs
3. Job outputs are correctly defined

---

## Related Documentation

- [Inputs Reference](INPUTS.md)
- [Examples](../examples/README.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Main README](../README.md)
