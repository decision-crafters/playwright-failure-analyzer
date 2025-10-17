# Auto-Fix Integration Guide

## Overview

The Playwright Failure Analyzer now supports auto-fix integration through structured JSON exports, enhanced AI analysis with fixability scoring, and machine-parseable metadata for automated fixing tools like Dagger modules.

**Version**: 1.1.0+
**Status**: Ready for integration

---

## New Features Summary

### 1. Model-Based Confidence Scoring

AI confidence scores are now adjusted based on the model tier being used:

| Model Tier | Multiplier | Models |
|------------|------------|--------|
| Premium | 1.0x | GPT-4o, Claude 3.5 Sonnet, Claude 3 Opus |
| Balanced | 0.85x | GPT-4o-mini, Claude 3.5 Haiku, Claude 3 Haiku |
| Budget | 0.70-0.75x | DeepSeek Chat/Coder, Llama 3.1-70B |
| Basic | 0.60x | Unknown/other models |

**Why this matters**: Budget models are less reliable for complex analysis. Adjusted confidence scores help auto-fix tools make better decisions about which fixes to apply automatically vs. requiring human review.

**Example**:
- Premium model reports 80% confidence → 80% final confidence
- Budget model reports 80% confidence → 56% final confidence (below auto-fix threshold)

### 2. Fixability Scoring

Each failure now receives a fixability score (0.0-1.0) indicating how suitable it is for automated fixing:

| Score Range | Classification | Action |
|-------------|----------------|--------|
| 0.9-1.0 | Trivial | Auto-fix with high confidence |
| 0.7-0.89 | Easy | Auto-fix with review required |
| 0.5-0.69 | Moderate | Add suggestion comment to issue |
| 0.3-0.49 | Complex | Manual investigation needed |
| 0.0-0.29 | Not fixable | Human-only |

**Example patterns**:
- Missing `await` → 0.95 (trivial)
- Wrong selector → 0.85 (easy)
- Timeout adjustment → 0.80 (easy)
- Business logic error → 0.25 (not fixable)

### 3. Structured JSON Export

Failures can now be exported in a machine-readable format optimized for auto-fix tools:

```json
{
  "version": "1.0",
  "format": "playwright-failure-analyzer-structured",
  "summary": {
    "total_tests": 50,
    "failed_tests": 3
  },
  "failures": [
    {
      "test_name": "Login flow should work",
      "file_path": "tests/auth.spec.ts",
      "line_number": 42,
      "error_type": "selector",
      "suggested_pattern": "selector_timeout",
      "fixability_hint": "high - check element selector matches DOM"
    }
  ],
  "metadata": {...},
  "auto_fix_context": {
    "repository": "owner/repo",
    "sha": "abc123",
    "branch": "main"
  }
}
```

### 4. Auto-Fix Labels

Issues are automatically labeled based on fixability:

- `auto-fix-ready` - High fixability (≥75%), ready for automated fixing
- `high-fixability` - Confidence ≥75%
- `auto-fix-candidate` - Medium fixability (50-74%)
- `medium-fixability` - Confidence 50-74%
- `ai-tier-{premium|balanced|budget}` - Model tier used
- `pattern-{pattern-name}` - Detected error patterns

### 5. Machine-Parseable Metadata in Issues

Issues now include a hidden section with structured metadata for auto-fix tools:

```markdown
<!-- AUTO-FIX-METADATA
```json
{
  "version": "1.0",
  "fixability_score": 0.85,
  "confidence_score": 0.78,
  "model_tier": "balanced",
  "error_patterns": ["selector_timeout"],
  "auto_fix_prompt": "...",
  "auto_fixable_issues": [...]
}
```
-->
```

---

## Usage

### Enable Structured JSON Export

Update your workflow to enable JSON export:

```yaml
- name: Analyze failures
  uses: decision-crafters/playwright-failure-analyzer@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    ai-analysis: true
    export-structured-json: true  # NEW: Enable JSON export
    structured-json-path: 'playwright-failures.json'  # Optional: custom path
  env:
    OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
    AI_MODEL: 'openrouter/deepseek/deepseek-chat'  # Budget model → lower confidence
```

### Access Structured Data

The structured JSON is now available for downstream steps:

```yaml
- name: Attempt auto-fix
  run: |
    # Read the structured JSON
    cat ${{ steps.analyze.outputs.structured-json-path }}

    # Pass to your auto-fix tool
    python scripts/auto_fix.py \
      --failures-json ${{ steps.analyze.outputs.structured-json-path }}
```

### Filter Issues by Fixability

Use GitHub's label filters to find auto-fixable issues:

```bash
# Find high-fixability issues
gh issue list --label "auto-fix-ready"

# Find medium-fixability issues
gh issue list --label "auto-fix-candidate"

# Find selector-related issues
gh issue list --label "pattern-selector-timeout"
```

---

## Integration Patterns

### Pattern 1: Selective Auto-Fix (Recommended)

Only auto-fix high-confidence, simple patterns:

```yaml
jobs:
  test-and-analyze:
    runs-on: ubuntu-latest
    steps:
      - name: Run tests
        id: tests
        run: |
          set +e
          npx playwright test
          TEST_EXIT_CODE=$?
          set -e
          echo "test-failed=$([ $TEST_EXIT_CODE -ne 0 ] && echo 'true' || echo 'false')" >> $GITHUB_OUTPUT
          exit $TEST_EXIT_CODE
        continue-on-error: true

      - name: Analyze failures
        if: steps.tests.outputs.test-failed == 'true'
        id: analyze
        uses: decision-crafters/playwright-failure-analyzer@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          ai-analysis: true
          export-structured-json: true
        env:
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
          AI_MODEL: 'openrouter/deepseek/deepseek-coder'  # Good for code fixes

  # Separate job triggered by issue creation
  auto-fix:
    runs-on: ubuntu-latest
    needs: test-and-analyze
    if: |
      github.event_name == 'issues' &&
      github.event.action == 'opened' &&
      contains(github.event.issue.labels.*.name, 'auto-fix-ready')
    steps:
      # Your auto-fix implementation here (see demo repo docs)
```

### Pattern 2: Progressive Auto-Fix

Start with comments, graduate to PRs:

```yaml
- name: Auto-fix decision
  run: |
    FIXABILITY=$(jq -r '.fixability_score' failures.json)

    if (( $(echo "$FIXABILITY >= 0.75" | bc -l) )); then
      echo "action=create-pr" >> $GITHUB_OUTPUT
    elif (( $(echo "$FIXABILITY >= 0.50" | bc -l) )); then
      echo "action=create-comment" >> $GITHUB_OUTPUT
    else
      echo "action=none" >> $GITHUB_OUTPUT
    fi
```

### Pattern 3: Model-Aware Workflow

Use cheaper models for analysis, premium for fixing:

```yaml
- name: Analyze with budget model
  uses: decision-crafters/playwright-failure-analyzer@v1
  with:
    ai-analysis: true
    export-structured-json: true
  env:
    AI_MODEL: 'openrouter/deepseek/deepseek-chat'  # $0.30/1000 calls

- name: Auto-fix with premium model
  if: steps.analyze.outputs.fixability-score >= 0.75
  env:
    AI_MODEL: 'openai/gpt-4o'  # $5.00/1000 calls - only for fixing
```

---

## Configuration Options

### Action Inputs

| Input | Default | Description |
|-------|---------|-------------|
| `export-structured-json` | `false` | Enable structured JSON export |
| `structured-json-path` | `playwright-failures-structured.json` | Path for JSON export |

### AI Analysis Inputs

| Input | Description | Example |
|-------|-------------|---------|
| `AI_MODEL` | Model to use for analysis | `openrouter/deepseek/deepseek-chat` |
| `OPENROUTER_API_KEY` | OpenRouter API key (recommended) | `sk-or-v1-...` |
| `OPENAI_API_KEY` | OpenAI API key (alternative) | `sk-...` |
| `ANTHROPIC_API_KEY` | Anthropic API key (alternative) | `sk-ant-...` |

### Action Outputs

| Output | Description |
|--------|-------------|
| `structured-json-path` | Path to the structured JSON export |
| `failures-count` | Number of failures detected |
| `issue-number` | Created issue number |
| `issue-url` | Created issue URL |

---

## Error Pattern Library

The analyzer detects these common patterns:

| Pattern | Fixability | Description |
|---------|------------|-------------|
| `missing_await` | 0.95 | Missing await before async function |
| `selector_timeout` | 0.85 | Element selector timeout |
| `navigation_timeout` | 0.80 | Page navigation timeout |
| `element_detached` | 0.75 | Element removed from DOM |
| `type_mismatch_*` | 0.85 | TypeScript type errors |
| `module_not_found` | 0.90 | Import/module errors |
| `multiple_elements` | 0.70 | Selector matches multiple elements |

See [AUTOFIX_PROMPT_TEMPLATES.md](./AUTOFIX_PROMPT_TEMPLATES.md) for fix prompts for each pattern.

---

## Best Practices

### 1. Start Conservative

Begin with high-fixability patterns only:

```yaml
- name: Only fix trivial issues
  if: steps.analyze.outputs.fixability-score >= 0.90
```

### 2. Monitor Success Rates

Track which patterns work well:

```python
success_metrics = {
    "missing_await": {"attempts": 50, "successes": 48, "rate": 0.96},
    "selector_timeout": {"attempts": 30, "successes": 24, "rate": 0.80},
    "navigation_timeout": {"attempts": 20, "successes": 15, "rate": 0.75}
}
```

### 3. Use Budget Models for Analysis

Save costs with cheaper models for initial analysis:

- Analysis: DeepSeek (~$0.30/1000) - 70% confidence multiplier
- Auto-fix: GPT-4o (~$5.00/1000) - 100% confidence multiplier

**Net effect**: Only spend on premium model for high-value fixes.

### 4. Require Human Review

Always require review for non-trivial changes:

```yaml
- name: Create PR
  uses: peter-evans/create-pull-request@v6
  with:
    draft: ${{ steps.analyze.outputs.fixability-score < 0.90 }}  # Draft if < 90%
    reviewers: ${{ github.actor }}
```

### 5. Test Before Merging

Run tests in the auto-fix PR:

```yaml
- name: Validate fix
  run: |
    npx playwright test ${{ steps.fix.outputs.test-file }}
    if [ $? -ne 0 ]; then
      gh pr close ${{ steps.pr.outputs.pr-number }}
      gh issue comment ${{ steps.analyze.outputs.issue-number }} \
        --body "Auto-fix failed validation. Manual intervention required."
    fi
```

---

## Security Considerations

### 1. Never Auto-Fix Sensitive Code

The analyzer automatically adds safety labels for:
- Authentication/authorization code
- Payment/billing logic
- Database operations
- Security-critical patterns

**Always review** these manually, even with high fixability scores.

### 2. Limit Auto-Fix Scope

Only auto-fix in specific directories:

```python
SAFE_DIRECTORIES = [
    "tests/",
    "e2e/",
    "integration/"
]

def is_safe_to_autofix(file_path: str) -> bool:
    return any(file_path.startswith(d) for d in SAFE_DIRECTORIES)
```

### 3. Use Branch Protection

Require approvals for auto-fix PRs:

```yaml
# .github/branch-protection.yml
require_pull_request_reviews:
  required_approving_review_count: 1
  dismiss_stale_reviews: true
  require_code_owner_reviews: true
```

---

## Troubleshooting

### Issue: Structured JSON not created

**Cause**: `export-structured-json` not enabled or path issue.

**Solution**:
```yaml
export-structured-json: 'true'  # Must be string 'true', not boolean
```

### Issue: Low fixability scores

**Cause**: Using budget model reduces confidence.

**Solution**: This is intentional. Budget models should have lower confidence. Either:
1. Accept lower confidence and require more review
2. Use premium model for higher confidence

### Issue: Auto-fix labels not appearing

**Cause**: AI analysis not enabled or fixability score below threshold.

**Solution**:
```yaml
ai-analysis: 'true'
# Labels only added if fixability >= 0.50
```

---

## Next Steps

1. ✅ **Local features complete** - All analyzer enhancements done
2. 🔄 **Demo repo integration** - See [DEMO_REPO_DAGGER_GUIDE.md](./DEMO_REPO_DAGGER_GUIDE.md)
3. ⏭️ **Community validation** - Test with real repositories
4. 📊 **Metrics collection** - Track success rates by pattern
5. 🚀 **Iterate and improve** - Expand pattern library

---

## Related Documentation

- [Auto-Fix Prompt Templates](./AUTOFIX_PROMPT_TEMPLATES.md) - Ready-to-use prompts for Dagger modules
- [Demo Repo Dagger Guide](./DEMO_REPO_DAGGER_GUIDE.md) - Reference implementation (next step)
- [NEW_FEATURE.md](/NEW_FEATURE.md) - Full research and business case

---

## Support

**Questions?** Open an issue at [decision-crafters/playwright-failure-analyzer](https://github.com/decision-crafters/playwright-failure-analyzer)

**Contributing?** We welcome PRs with new error patterns and improvements!
