# Auto-Fix Prompt Templates

This document provides reusable prompt templates for integrating automated fixing tools (like Dagger modules) with the Playwright Failure Analyzer.

## Overview

The analyzer now exports structured data that can be consumed by auto-fix tools. These prompt templates help you build effective AI-powered fixing agents.

## Table of Contents

- [Base Fix Generation Prompt](#base-fix-generation-prompt)
- [Pattern-Specific Prompts](#pattern-specific-prompts)
- [Confidence Validation Prompt](#confidence-validation-prompt)
- [Test Validation Prompt](#test-validation-prompt)
- [PR Description Prompt](#pr-description-prompt)

---

## Base Fix Generation Prompt

Use this template when reading the structured JSON export and generating fixes.

```python
BASE_FIX_PROMPT = """You are an expert Playwright test engineer tasked with fixing a test failure.

## Context
- Repository: {repository}
- Branch: {branch}
- Commit: {sha}
- AI Model Used for Analysis: {model} ({model_tier} tier)
- Analysis Confidence: {confidence_score}%
- Fixability Score: {fixability_score}%

## Failure Information
Test: {test_name}
File: {file_path}:{line_number}
Error Type: {error_type}
Error Pattern: {suggested_pattern}

Error Message:
```
{error_message}
```

Stack Trace:
```
{stack_trace}
```

## Task
Generate a minimal, precise fix for this test failure. Follow these guidelines:

1. **Read the current file content** at {file_path}
2. **Identify the exact line** causing the failure (line {line_number})
3. **Generate the fix** following the pattern for "{suggested_pattern}"
4. **Minimize changes** - only fix what's broken
5. **Preserve existing code style** and formatting
6. **Include comments** explaining the fix if non-obvious

## Output Format
Return a JSON object with:
{{
  "file_path": "path/to/file.spec.js",
  "changes": [
    {{
      "line_number": 42,
      "old_code": "await page.goto(url)",
      "new_code": "await page.goto(url, {{ timeout: 30000 }})",
      "reason": "Added explicit timeout to prevent timeout errors"
    }}
  ],
  "confidence": 0.85,
  "requires_testing": true
}}
"""

## Pattern-Specific Prompts

### Missing Await Pattern

```python
MISSING_AWAIT_PROMPT = """Fix a missing await in an async Playwright test.

File: {file_path}
Line: {line_number}
Error: {error_message}

Current code around line {line_number}:
```
{code_context}
```

Task: Add the missing `await` keyword before the async operation.

Rules:
- Only add await where it's actually missing
- Ensure the function is marked as async
- Check for any chained operations that also need await

Return the fixed code with the await keyword properly placed.
"""

SELECTOR_TIMEOUT_PROMPT = """Fix a selector timeout error in a Playwright test.

File: {file_path}
Line: {line_number}
Error: {error_message}

Current code around line {line_number}:
```
{code_context}
```

Possible fixes (apply the most appropriate):
1. Increase timeout: `await page.waitForSelector(selector, {{ timeout: 30000 }})`
2. Fix selector: Verify the selector matches actual DOM elements
3. Add wait condition: `await page.waitForLoadState('networkidle')`
4. Use better locator: Replace CSS with data-testid or role-based selector

Analyze the error and apply the best fix.
"""

NAVIGATION_TIMEOUT_PROMPT = """Fix a navigation timeout in a Playwright test.

File: {file_path}
Line: {line_number}
Error: {error_message}

Current code around line {line_number}:
```
{code_context}
```

Common fixes:
1. Increase timeout: `await page.goto(url, {{ timeout: 60000 }})`
2. Wait for load state: `await page.goto(url, {{ waitUntil: 'networkidle' }})`
3. Add retry logic for flaky endpoints
4. Check if URL is correct

Apply the most appropriate fix.
"""

TYPE_MISMATCH_PROMPT = """Fix a TypeScript type mismatch in a Playwright test.

File: {file_path}
Line: {line_number}
Error: {error_message}

Current code around line {line_number}:
```
{code_context}
```

Task: Fix the type annotation or value to match expected type.

Common fixes:
- Add type assertion: `as ExpectedType`
- Update variable type annotation
- Convert value to correct type (Number(), String(), Boolean())
- Fix return type of function

Apply the correct type fix.
"""
```

## Confidence Validation Prompt

Use this to validate whether a generated fix should be applied.

```python
CONFIDENCE_VALIDATION_PROMPT = """Evaluate the confidence level for this auto-generated fix.

## Original Error
{error_message}

## Generated Fix
File: {file_path}
Changes:
{proposed_changes}

## Context
- Error Pattern: {error_pattern}
- AI Model Tier: {model_tier}
- Base Confidence: {base_confidence}

## Evaluation Criteria
Score each from 0.0 to 1.0:

1. **Pattern Match** (40%): How well does the error match known fixable patterns?
2. **Fix Simplicity** (25%): Is the fix a simple, low-risk change?
3. **Test Coverage** (20%): Can the fix be validated by running tests?
4. **Side Effects** (15%): Is the blast radius minimal?

## Output
Return JSON:
{{
  "pattern_match_score": 0.95,
  "simplicity_score": 0.90,
  "test_coverage_score": 1.0,
  "side_effects_score": 0.85,
  "overall_confidence": 0.91,
  "recommendation": "APPLY" | "REVIEW" | "REJECT",
  "reasoning": "Explanation of scores"
}}

Thresholds:
- >= 0.90: APPLY (create regular PR)
- 0.75-0.89: REVIEW (create draft PR)
- 0.50-0.74: COMMENT (add suggestion to issue)
- < 0.50: REJECT (no automated action)
"""
```

## Test Validation Prompt

After applying a fix, validate it with tests.

```python
TEST_VALIDATION_PROMPT = """Validate that the fix resolves the test failure.

## Fix Applied
File: {file_path}
Changes: {changes_summary}

## Original Failure
Test: {test_name}
Error: {error_message}

## Task
1. Run the specific failing test: `npx playwright test {test_file}`
2. Check if test now passes
3. Run full test suite to check for regressions
4. Calculate success metrics

## Output Format
Return JSON:
{{
  "test_passed": true,
  "execution_time_ms": 2543,
  "regression_tests_affected": 0,
  "confidence_boost": 0.15,
  "recommendation": "Create PR with high confidence label"
}}
"""
```

## PR Description Prompt

Generate a comprehensive PR description for auto-fixed issues.

```python
PR_DESCRIPTION_PROMPT = """Generate a pull request description for an auto-fix.

## Context
- Issue: #{issue_number}
- Test: {test_name}
- File: {file_path}:{line_number}
- Error Pattern: {error_pattern}
- Fix Confidence: {confidence_score}%
- AI Model: {model} ({model_tier} tier)

## Changes Made
{changes_summary}

## Test Results
{test_results}

## Task
Generate a comprehensive PR description using this template:

---

# 🤖 Auto-Fix: {issue_title}

Fixes #{issue_number}

## Summary
<!-- 2-3 sentence overview of what was fixed -->

## Changes Made
<!-- Detailed list of changes -->

## Root Cause
<!-- Explanation of why the test was failing -->

## Testing
- [x] Failing test now passes
- [x] No regressions detected
- [x] Test execution time: {execution_time}ms

## Confidence Metrics
- **AI Confidence**: {confidence_score}% ({confidence_tier})
- **Model Used**: {model} ({model_tier} tier)
- **Fixability Score**: {fixability_score}%
- **Pattern Detected**: `{error_pattern}`

## Review Checklist
- [ ] Changes are minimal and focused
- [ ] No unintended side effects
- [ ] Test coverage remains intact
- [ ] Code style matches project standards

## Auto-Fix Metadata
```json
{metadata_json}
```

---

⚠️ **This is an automated fix** generated by [Playwright Failure Analyzer](https://github.com/decision-crafters/playwright-failure-analyzer). Please review carefully before merging.

💬 Questions? Comment on the original issue: #{issue_number}
"""
```

## Usage Example in Dagger Module

Here's how to use these prompts in a Dagger module:

```python
import dagger
from dagger import dag, function, object_type
import json

@object_type
class PlaywrightAutoFixer:

    @function
    async def attempt_fix(
        self,
        repo_dir: dagger.Directory,
        structured_json_path: str,
    ) -> str:
        # Read structured JSON from analyzer
        failures_data = await self._read_failures(repo_dir, structured_json_path)

        results = []
        for failure in failures_data["failures"]:
            # Generate fix using pattern-specific prompt
            fix_prompt = self._build_fix_prompt(failure, failures_data["metadata"])

            # Call AI to generate fix
            fix_result = await self._generate_fix(fix_prompt)

            # Validate fix confidence
            confidence_result = await self._validate_confidence(fix_result, failure)

            if confidence_result["recommendation"] in ["APPLY", "REVIEW"]:
                # Apply fix and test
                test_result = await self._apply_and_test(fix_result)

                if test_result["test_passed"]:
                    results.append({
                        "file": failure["file_path"],
                        "success": True,
                        "confidence": confidence_result["overall_confidence"],
                        "test_result": test_result
                    })

        return json.dumps({"fixes_applied": len(results), "results": results})

    def _build_fix_prompt(self, failure: dict, metadata: dict) -> str:
        """Build appropriate prompt based on error pattern."""
        pattern = failure.get("suggested_pattern", "unknown_pattern")

        if pattern == "missing_await":
            return MISSING_AWAIT_PROMPT.format(**failure, **metadata)
        elif pattern == "selector_timeout":
            return SELECTOR_TIMEOUT_PROMPT.format(**failure, **metadata)
        elif pattern == "navigation_timeout":
            return NAVIGATION_TIMEOUT_PROMPT.format(**failure, **metadata)
        else:
            return BASE_FIX_PROMPT.format(**failure, **metadata)
```

## Model-Specific Adjustments

Apply these confidence multipliers based on the model tier:

```python
MODEL_CONFIDENCE_MULTIPLIERS = {
    # Premium models (high confidence)
    'premium': 1.0,

    # Balanced models (medium confidence)
    'balanced': 0.85,

    # Budget models (lower confidence)
    'budget': 0.70,

    # Basic models (lowest confidence)
    'basic': 0.60,
}

def adjust_confidence(raw_confidence: float, model_tier: str) -> float:
    """Apply model-based confidence adjustment."""
    multiplier = MODEL_CONFIDENCE_MULTIPLIERS.get(model_tier, 0.60)
    return min(raw_confidence * multiplier, 1.0)
```

## Best Practices

1. **Always validate**: Run tests after applying fixes
2. **Start conservative**: Begin with high-confidence patterns only
3. **Iterate gradually**: Add more patterns as you gain confidence
4. **Monitor metrics**: Track success rates by pattern and model
5. **Human in the loop**: Require review for medium-confidence fixes
6. **Fail safely**: If unsure, create a comment instead of a PR

## Next Steps

1. Integrate these prompts into your Dagger module
2. Test with the demo repository first
3. Monitor success rates and adjust thresholds
4. Expand pattern library based on your codebase
5. Share learnings back with the community

---

**Related Documentation:**
- [Dagger Integration Guide](./DAGGER_INTEGRATION.md) (coming soon)
- [Auto-Fix Safety Guidelines](./AUTOFIX_SAFETY.md) (coming soon)
- [Pattern Library](./AUTOFIX_PATTERNS.md) (coming soon)

**Questions?** Open an issue at [decision-crafters/playwright-failure-analyzer](https://github.com/decision-crafters/playwright-failure-analyzer)
