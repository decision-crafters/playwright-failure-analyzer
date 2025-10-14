#!/bin/bash
# Validate the demo repository is working correctly
# This script checks that the demo repository is functioning and creating issues

set -e

DEMO_REPO="${DEMO_REPO:-decision-crafters/playwright-failure-analyzer-demo}"

echo "════════════════════════════════════════════════════════════"
echo "  Validating Demo Repository: $DEMO_REPO"
echo "════════════════════════════════════════════════════════════"
echo ""

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ Error: GitHub CLI (gh) is not installed"
    echo "   Install from: https://cli.github.com/"
    exit 1
fi

# Check authentication
if ! gh auth status &> /dev/null; then
    echo "❌ Error: Not authenticated with GitHub CLI"
    echo "   Run: gh auth login"
    exit 1
fi

echo "✅ GitHub CLI authenticated"
echo ""

# Check repository exists
echo "Checking repository exists..."
if ! gh repo view "$DEMO_REPO" &> /dev/null; then
    echo "❌ Error: Repository $DEMO_REPO not found or not accessible"
    echo ""
    echo "   This repository needs to be created manually."
    echo "   See docs/E2E_TEST_REPOSITORY_SETUP.md for setup instructions."
    exit 1
fi

echo "✅ Repository exists and is accessible"
echo ""

# Check recent workflow runs
echo "Checking recent workflow runs..."
WORKFLOW_RUNS=$(gh run list \
    --repo "$DEMO_REPO" \
    --limit 10 \
    --json status,conclusion,name,createdAt \
    --jq 'length')

if [ "$WORKFLOW_RUNS" -eq 0 ]; then
    echo "⚠️  Warning: No workflow runs found"
    echo "   Workflows may not be configured yet."
    echo "   See docs/E2E_TEST_REPOSITORY_SETUP.md for setup."
else
    echo "✅ Found $WORKFLOW_RUNS recent workflow runs"

    # Show recent runs
    echo ""
    echo "Recent runs:"
    gh run list \
        --repo "$DEMO_REPO" \
        --limit 5 \
        --json status,conclusion,name,createdAt \
        --jq '.[] | "  - \(.name): \(.conclusion // .status) (\(.createdAt | fromdateiso8601 | strftime("%Y-%m-%d %H:%M")))"'
fi

echo ""

# Check if demo issues exist
echo "Checking demo issues..."
DEMO_ISSUES=$(gh issue list \
    --repo "$DEMO_REPO" \
    --label demo \
    --state all \
    --limit 100 \
    --json number \
    --jq 'length')

if [ "$DEMO_ISSUES" -eq 0 ]; then
    echo "⚠️  Warning: No demo issues found"
    echo "   The action may not have run yet, or no tests have failed."
    echo "   Try manually triggering the 'Test with Intentional Failures' workflow."
else
    echo "✅ Found $DEMO_ISSUES demo issues (all time)"

    # Count open issues
    OPEN_ISSUES=$(gh issue list \
        --repo "$DEMO_REPO" \
        --label demo \
        --state open \
        --limit 100 \
        --json number \
        --jq 'length')

    echo "   - Open: $OPEN_ISSUES"
    echo "   - Closed: $((DEMO_ISSUES - OPEN_ISSUES))"

    # Show recent issues
    echo ""
    echo "Recent demo issues:"
    gh issue list \
        --repo "$DEMO_REPO" \
        --label demo \
        --limit 3 \
        --json number,title,state,createdAt \
        --jq '.[] | "  #\(.number): \(.title) [\(.state)] (\(.createdAt | fromdateiso8601 | strftime("%Y-%m-%d")))"'
fi

echo ""
echo "════════════════════════════════════════════════════════════"

# Determine overall status
if [ "$DEMO_ISSUES" -gt 0 ] && [ "$WORKFLOW_RUNS" -gt 0 ]; then
    echo "✅ VALIDATION PASSED"
    echo ""
    echo "   The demo repository is functioning correctly!"
    echo "   View at: https://github.com/$DEMO_REPO"
    exit 0
elif [ "$WORKFLOW_RUNS" -gt 0 ]; then
    echo "⚠️  VALIDATION WARNING"
    echo ""
    echo "   Workflows are running but no issues found yet."
    echo "   This may be normal if tests haven't failed."
    echo ""
    echo "   Action needed:"
    echo "   1. Check workflow logs: https://github.com/$DEMO_REPO/actions"
    echo "   2. Ensure intentional failure tests are configured"
    echo "   3. Manually trigger the failure test workflow"
    exit 0
else
    echo "❌ VALIDATION FAILED"
    echo ""
    echo "   The demo repository exists but appears not to be configured."
    echo ""
    echo "   Action needed:"
    echo "   1. Set up workflows in .github/workflows/"
    echo "   2. See docs/E2E_TEST_REPOSITORY_SETUP.md for complete guide"
    echo "   3. Push changes and enable Actions in repository settings"
    exit 1
fi
