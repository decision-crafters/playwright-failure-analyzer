# Critical Fix Needed for Demo Repository

## Repository
https://github.com/decision-crafters/playwright-failure-analyzer-demo

## Issue
The workflow at `.github/workflows/test-intentional-failures.yml` has a critical bug that prevents the analyzer from running when tests fail.

## Root Cause
GitHub Actions runs bash scripts with the `-e` flag (exit on error). When `npx playwright test` fails with exit code 1, the script exits immediately before:
1. Capturing the test exit code
2. Setting the `test-failed` output variable

As a result, the conditional `if: steps.tests.outputs.test-failed == 'true'` evaluates to false (because the output was never set), and the "Analyze failures" step is skipped.

## Evidence
From workflow run #18479018386:
- 5 tests failed (confirmed in logs)
- Step "Run failing tests" completed with exit code 1
- Step "Analyze failures" was **skipped**
- No `test-failed` output was set

## Required Fix

**Current broken code** (lines 41-55 in `.github/workflows/test-intentional-failures.yml`):

```yaml
- name: Run failing tests
  id: tests
  run: |
    npx playwright test sample-fail
    TEST_EXIT_CODE=$?
    echo "test-failed=$([ $TEST_EXIT_CODE -ne 0 ] && echo 'true' || echo 'false')" >> $GITHUB_OUTPUT
    exit $TEST_EXIT_CODE
  continue-on-error: true
```

**Fixed code** (add `set +e` and `set -e`):

```yaml
- name: Run failing tests
  id: tests
  run: |
    set +e  # Disable exit on error to capture test exit code
    npx playwright test sample-fail
    TEST_EXIT_CODE=$?
    set -e  # Re-enable exit on error
    echo "test-failed=$([ $TEST_EXIT_CODE -ne 0 ] && echo 'true' || echo 'false')" >> $GITHUB_OUTPUT
    exit $TEST_EXIT_CODE
  continue-on-error: true
```

## How to Apply Fix

### Option 1: Manual Edit
1. Edit `.github/workflows/test-intentional-failures.yml` in the demo repository
2. Add `set +e` before the test command (line 45)
3. Add `set -e` after capturing the exit code (line 48)
4. Commit and push

### Option 2: GitHub Web Interface
1. Go to: https://github.com/decision-crafters/playwright-failure-analyzer-demo/edit/main/.github/workflows/test-intentional-failures.yml
2. Make the changes shown above
3. Commit directly to main branch

## Testing the Fix

After applying the fix, trigger a new workflow run:
- Push a commit to main, OR
- Go to Actions → "Test with Intentional Failures" → "Run workflow"

Expected behavior:
1. Tests run and fail (5 failures)
2. `test-failed=true` is set as output
3. "Analyze failures" step **RUNS** (not skipped)
4. GitHub issue is created with failure analysis

## Additional Configuration

Once the analyzer runs successfully, you can add the DeepSeek API key to enable AI analysis:

1. Go to repository Settings → Secrets and variables → Actions
2. Add secret: `DEEPSEEK_API_KEY` or `OPENROUTER_API_KEY`
3. Update workflow to enable AI analysis:

```yaml
env:
  DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
  AI_MODEL: 'deepseek/deepseek-chat'
```

## Status

- [x] Issue identified in main repository
- [x] All example workflows fixed in main repository
- [x] Documentation updated in main repository
- [ ] **Demo repository needs manual fix** (awaiting user to apply)

## Related Files in Main Repository

All example workflows have been updated with the fix:
- `examples/basic-workflow.yml`
- `examples/advanced-workflow.yml`
- `examples/ai-analysis-workflow.yml`
- `examples/multi-suite-workflow.yml`
- `examples/pr-integration.yml`

Documentation updated:
- `CLAUDE.md` - Added to Common Pitfalls section
- `docs/TROUBLESHOOTING.md` - Updated Issue 1 with detailed explanation
