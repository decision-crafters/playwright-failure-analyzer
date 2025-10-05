#!/bin/bash
# AI Integration Testing Script
# Tests the AI analysis functionality with real API calls

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🤖 AI Integration Testing Script${NC}\n"

# Check for API keys
if [ -z "$OPENAI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$OPENROUTER_API_KEY" ]; then
    echo -e "${RED}❌ Error: No API key found!${NC}"
    echo ""
    echo "Please set one of the following environment variables:"
    echo "  - OPENAI_API_KEY (for OpenAI models)"
    echo "  - ANTHROPIC_API_KEY (for Anthropic models)"
    echo "  - OPENROUTER_API_KEY (for OpenRouter - recommended)"
    echo ""
    echo "Example (OpenRouter - cheapest option):"
    echo "  export OPENROUTER_API_KEY='your-key-here'  # pragma: allowlist secret"
    echo "  export AI_MODEL='openrouter/deepseek/deepseek-chat'"
    echo ""
    exit 1
fi

# Display configuration
echo -e "${GREEN}✅ API Key Found${NC}"
echo ""
echo "Configuration:"
if [ ! -z "$AI_MODEL" ]; then
    echo "  Model: $AI_MODEL"
else
    echo "  Model: gpt-4o-mini (default)"
fi
echo ""

# Create a test report with failures
echo -e "${BLUE}📋 Creating test report...${NC}"
TEST_REPORT="test-ai-report.json"

cat > $TEST_REPORT << 'EOF'
{
  "stats": {
    "expected": 45,
    "unexpected": 3,
    "skipped": 2,
    "duration": 125000
  },
  "suites": [{
    "title": "Login Tests",
    "file": "tests/login.spec.ts",
    "specs": [{
      "title": "should login with valid credentials",
      "tests": [{
        "title": "should login with valid credentials",
        "results": [{
          "status": "unexpected",
          "duration": 5000,
          "error": {
            "message": "Timeout 5000ms exceeded.\nexpect(locator).toBeVisible()\n\nLocator: locator('#submit-button')",
            "stack": "Error: Timeout 5000ms exceeded.\n  at Object.toBeVisible (/home/runner/work/project/tests/login.spec.ts:15:45)"
          }
        }]
      }]
    }]
  }, {
    "title": "Dashboard Tests",
    "file": "tests/dashboard.spec.ts",
    "specs": [{
      "title": "should display user statistics",
      "tests": [{
        "title": "should display user statistics",
        "results": [{
          "status": "unexpected",
          "duration": 3000,
          "error": {
            "message": "expect(received).toEqual(expected)\n\nExpected: \"100\"\nReceived: \"95\"",
            "stack": "Error: expect(received).toEqual(expected)\n  at Object.<anonymous> (/home/runner/work/project/tests/dashboard.spec.ts:23:50)"
          }
        }]
      }]
    }]
  }]
}
EOF

echo -e "${GREEN}✅ Test report created${NC}"
echo ""

# Run the AI analysis
echo -e "${BLUE}🧠 Running AI analysis...${NC}"
echo ""

python3 << PYTHON_SCRIPT
import sys
import os
import json

# Add src to path
sys.path.insert(0, 'src')

from ai_analysis import create_ai_analyzer, AIAnalysisFormatter
from parse_report import PlaywrightReportParser
from error_handling import setup_error_handling

try:
    # Parse the test report
    print("📊 Parsing test report...")
    error_handler = setup_error_handling()
    parser = PlaywrightReportParser("$TEST_REPORT", error_handler)
    summary = parser.parse_failures(max_failures=10)

    print(f"✅ Found {summary.failed_tests} failures")
    print("")

    # Create AI analyzer
    print("🤖 Initializing AI analyzer...")
    analyzer = create_ai_analyzer()

    if not analyzer:
        print("❌ Failed to create AI analyzer (no API key found)")
        sys.exit(1)

    print(f"✅ Using model: {analyzer.model}")
    print("")

    # Analyze failures
    print("🧠 Analyzing failures with AI...")
    print("(This may take 10-30 seconds depending on the model)")
    print("")

    from dataclasses import asdict
    failures_list = [asdict(f) for f in summary.failures]
    metadata = summary.metadata

    result = analyzer.analyze_failures(failures_list, metadata)

    if result:
        print("✅ AI Analysis Complete!")
        print("")
        print("═" * 60)
        print(AIAnalysisFormatter.format_analysis_section(result))
        print("═" * 60)
        print("")

        # Show cost estimate
        print("💰 Approximate Cost:")
        prompt_tokens = len(json.dumps(failures_list)) // 4  # Rough estimate
        response_tokens = len(result.summary + result.root_cause_analysis) // 4
        total_tokens = prompt_tokens + response_tokens

        print(f"  Estimated tokens: {total_tokens:,}")

        # Cost estimates for different providers
        if "deepseek" in analyzer.model.lower():
            cost = (total_tokens / 1_000_000) * 0.14
            print(f"  DeepSeek cost: ~${cost:.6f}")
        elif "gpt-4o-mini" in analyzer.model.lower():
            cost = (total_tokens / 1_000_000) * 0.15
            print(f"  GPT-4o-mini cost: ~${cost:.6f}")
        elif "gpt-4" in analyzer.model.lower():
            cost = (total_tokens / 1_000_000) * 10
            print(f"  GPT-4 cost: ~${cost:.4f}")

        print("")
        print("✅ AI integration test PASSED!")
    else:
        print("❌ AI analysis failed")
        sys.exit(1)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_SCRIPT

TEST_EXIT_CODE=$?

# Cleanup
rm -f $TEST_REPORT

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ All AI integration tests passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Test with different models (set AI_MODEL environment variable)"
    echo "  2. Test with larger failure reports"
    echo "  3. Validate analysis quality"
    echo "  4. Monitor costs with your provider"
else
    echo ""
    echo -e "${RED}❌ AI integration tests failed${NC}"
    exit 1
fi
