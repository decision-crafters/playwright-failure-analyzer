# Release v1.0.2

## 🐛 Critical Bug Fix

### Fixed Default Report Path

**Issue**: The v1.0.0 and v1.0.1 releases had an incorrect default value for `report-path` input, causing the analyzer to fail when the path wasn't explicitly specified.

**What was wrong:**
```yaml
# v1.0.0 & v1.0.1 (BROKEN)
report-path:
  default: 'test-results.json'
```

**What's fixed:**
```yaml
# v1.0.2 (FIXED)
report-path:
  default: 'playwright-report/results.json'
```

### Impact

**Before this fix (v1.0.0, v1.0.1):**
- Users had to explicitly set `report-path: 'playwright-report/results.json'` in their workflows
- Workflows using the action without specifying `report-path` would fail with:
  ```
  ERROR: Playwright report file not found: test-results.json
  ```

**After this fix (v1.0.2):**
- Works out of the box without specifying `report-path`
- Matches Playwright's default JSON report location

### Migration Guide

#### If you're on v1, v1.0.0, or v1.0.1:

**Option 1: Update to v1.0.2 (Recommended)**
```yaml
- name: Analyze failures
  uses: decision-crafters/playwright-failure-analyzer@v1.0.2
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    # No need to specify report-path anymore!
```

**Option 2: Keep current version and specify path explicitly**
```yaml
- name: Analyze failures
  uses: decision-crafters/playwright-failure-analyzer@v1.0.1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    report-path: 'playwright-report/results.json'  # Required with old versions
```

### Breaking Changes

None. This is a bug fix that makes the action work as originally intended.

### Acknowledgments

Special thanks to @tosin2013 for identifying this issue in the demo repository testing!

---

## Full Changelog

**Fixed:**
- Corrected default `report-path` from `test-results.json` to `playwright-report/results.json` in action.yml

**Documentation:**
- Moved internal documentation to `.github/internal/`
- Added comprehensive HOW_IT_WORKS and AI_ASSISTANT guides

---

## Upgrade Instructions

```bash
# Update your workflow file
sed -i 's/@v1.0.1/@v1.0.2/g' .github/workflows/your-workflow.yml

# Or update to track latest v1.x
sed -i 's/@v1.0.1/@v1/g' .github/workflows/your-workflow.yml
```

The `@v1` tag will be updated to point to v1.0.2, so workflows using `@v1` will automatically get the fix.
