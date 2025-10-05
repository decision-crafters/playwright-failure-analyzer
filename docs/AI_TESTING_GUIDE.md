# 🤖 AI Integration Testing Guide

This guide helps you test the AI analysis functionality with real API calls using OpenRouter or DeepSeek.

## 🎯 Quick Start

### Option 1: OpenRouter (Recommended - Access to 100+ Models)

1. **Get API Key**: Sign up at [openrouter.ai](https://openrouter.ai/)
2. **Set Environment Variables**:
   ```bash
   export OPENROUTER_API_KEY='your-key-here'  # pragma: allowlist secret
   export AI_MODEL='openrouter/deepseek/deepseek-chat'  # Cheapest option!
   ```

3. **Run Test**:
   ```bash
   chmod +x scripts/test-ai-integration.sh
   ./scripts/test-ai-integration.sh
   ```

### Option 2: DeepSeek Direct

1. **Get API Key**: Sign up at [platform.deepseek.com](https://platform.deepseek.com/)
2. **Set Environment Variables**:
   ```bash
   export DEEPSEEK_API_KEY='your-key-here'  # pragma: allowlist secret
   export AI_MODEL='deepseek/deepseek-chat'
   ```

3. **Run Test**:
   ```bash
   ./scripts/test-ai-integration.sh
   ```

---

## 💰 Cost Comparison

### Recommended Models (Cheapest to Most Expensive)

| Provider | Model | Cost per 1M tokens | Best For |
|----------|-------|-------------------|----------|
| **DeepSeek** | `deepseek/deepseek-chat` | $0.14 | Testing, Production (cheap) |
| **OpenRouter** | `openrouter/deepseek/deepseek-chat` | $0.14 | Same as above via OpenRouter |
| **OpenRouter** | `openrouter/google/gemini-flash-1.5` | $0.075 | Fast, cheap, good quality |
| **OpenRouter** | `openrouter/meta-llama/llama-3.1-8b` | $0.06 | Very cheap, decent quality |
| **OpenAI** | `gpt-4o-mini` | $0.15 | Good balance (default) |
| **OpenAI** | `gpt-4o` | $2.50 | High quality, expensive |
| **Anthropic** | `claude-3.5-sonnet` | $3.00 | Premium quality |

### Typical Cost per Analysis

For a typical failure report with 3-5 failures:
- **Input**: ~1,500 tokens (failure data + prompt)
- **Output**: ~500 tokens (analysis)
- **Total**: ~2,000 tokens

**Cost Examples:**
- DeepSeek: ~$0.0003 per analysis (practically free!)
- GPT-4o-mini: ~$0.0003 per analysis
- GPT-4o: ~$0.005 per analysis
- Claude-3.5: ~$0.006 per analysis

**For 1,000 analyses:**
- DeepSeek: ~$0.30
- GPT-4o-mini: ~$0.30
- GPT-4o: ~$5.00
- Claude-3.5: ~$6.00

---

## 🔧 Configuration Options

### Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `OPENROUTER_API_KEY` | OpenRouter API key | None | `sk-or-v1-...` |
| `DEEPSEEK_API_KEY` | DeepSeek API key | None | `sk-...` |
| `OPENAI_API_KEY` | OpenAI API key | None | `sk-...` |
| `ANTHROPIC_API_KEY` | Anthropic API key | None | `sk-ant-...` |
| `AI_MODEL` | Model to use | `gpt-4o-mini` | `openrouter/deepseek/deepseek-chat` |

### LiteLLM Model Format

The `AI_MODEL` variable uses LiteLLM format:

**OpenRouter:**
```bash
openrouter/deepseek/deepseek-chat
openrouter/google/gemini-flash-1.5
openrouter/meta-llama/llama-3.1-8b
openrouter/anthropic/claude-3.5-sonnet
```

**Direct Providers:**
```bash
deepseek/deepseek-chat
gpt-4o-mini
gpt-4o
claude-3-5-sonnet-20240620
```

---

## 🧪 Testing Scenarios

### Test 1: Basic Functionality
```bash
# Test with cheapest model
export OPENROUTER_API_KEY='your-key'  # pragma: allowlist secret
export AI_MODEL='openrouter/deepseek/deepseek-chat'
./scripts/test-ai-integration.sh
```

### Test 2: Model Comparison
```bash
# Test multiple models to compare quality
for model in \
  "openrouter/deepseek/deepseek-chat" \
  "gpt-4o-mini" \
  "openrouter/google/gemini-flash-1.5"; do

  echo "Testing $model..."
  export AI_MODEL=$model
  ./scripts/test-ai-integration.sh
  echo ""
done
```

### Test 3: Real Playwright Report
```bash
# Use your actual Playwright JSON report
export OPENROUTER_API_KEY='your-key'  # pragma: allowlist secret
export AI_MODEL='openrouter/deepseek/deepseek-chat'

python3 << EOF
import sys
sys.path.insert(0, 'src')

from ai_analysis import create_ai_analyzer
from parse_report import PlaywrightReportParser
from error_handling import setup_error_handling

# Parse your real report
parser = PlaywrightReportParser('path/to/your/report.json', setup_error_handling())
summary = parser.parse_failures(max_failures=10)

# Analyze with AI
analyzer = create_ai_analyzer()
result = analyzer.analyze_failures(
    [vars(f) for f in summary.failures],
    summary.metadata
)

if result:
    print(result.summary)
    print(result.root_cause_analysis)
    print("Suggested actions:")
    for action in result.suggested_actions:
        print(f"  - {action}")
EOF
```

---

## 📊 What the AI Analyzes

The AI analysis provides:

1. **Summary** - High-level overview of failures
2. **Root Cause Analysis** - Potential underlying issues
3. **Suggested Actions** - Specific steps to fix
4. **Error Patterns** - Common patterns across failures
5. **Confidence Score** - How confident the AI is (0.0-1.0)

### Example Output

```markdown
## 🤖 AI Analysis

**Model**: deepseek-chat | **Confidence**: 0.85

### Summary
The test failures indicate a systematic issue with element visibility...

### Root Cause Analysis
The primary cause appears to be timing-related. The application is loading...

### 💡 Suggested Actions
1. Increase timeout for visibility assertions
2. Add explicit wait for page load
3. Check network conditions during test run

### 🔍 Error Patterns
- Timeout on element visibility (2 occurrences)
- Assertion mismatch on text content (1 occurrence)
```

---

## ✅ Validation Checklist

After running AI tests, validate:

- [ ] AI analysis completes without errors
- [ ] Summary is relevant to the failures
- [ ] Root cause makes technical sense
- [ ] Suggested actions are actionable
- [ ] Cost is within acceptable range
- [ ] Response time is reasonable (<30s)

---

## 🚨 Troubleshooting

### "No API key found"
**Solution**: Set one of: `OPENROUTER_API_KEY`, `DEEPSEEK_API_KEY`, `OPENAI_API_KEY`, or `ANTHROPIC_API_KEY`

### "Model not found" or "Invalid model"
**Solution**: Check the model name format. For OpenRouter, use: `openrouter/provider/model-name`

### "Rate limit exceeded"
**Solution**:
- Wait a few minutes
- Use a cheaper model with higher rate limits
- Check your API usage dashboard

### "API key invalid"
**Solution**:
- Verify your API key is correct
- Check if your account has credits
- Ensure the key has proper permissions

### Analysis quality is poor
**Solution**:
- Try a better model (e.g., GPT-4o or Claude)
- Ensure failure data is detailed
- Check if errors have stack traces

---

## 📈 Recommended Testing Strategy

### Phase 1: Initial Validation (Use DeepSeek - $0.30 for 1000 tests)
1. Test basic functionality
2. Validate output structure
3. Check error handling
4. Measure typical costs

### Phase 2: Quality Testing (Use GPT-4o-mini - $0.30 for 1000 tests)
1. Compare analysis quality
2. Test with various failure types
3. Validate suggested actions
4. Benchmark response times

### Phase 3: Production Decision
Based on testing:
- **Budget-conscious**: Use DeepSeek ($0.14 per 1M tokens)
- **Quality-focused**: Use GPT-4o-mini ($0.15 per 1M tokens)
- **Premium**: Use GPT-4o or Claude-3.5 ($2.50-3.00 per 1M tokens)

---

## 💡 Best Practices

1. **Start Cheap**: Test with DeepSeek first
2. **Monitor Costs**: Set up billing alerts in your provider dashboard
3. **Cache Results**: Don't re-analyze the same failures
4. **Rate Limiting**: Implement backoff for production
5. **Fallback**: Always have graceful degradation if AI fails
6. **User Control**: Let users enable/disable AI analysis
7. **Document Model**: Include which model was used in the output

---

## 🔗 Useful Links

- [OpenRouter Docs](https://openrouter.ai/docs)
- [DeepSeek Docs](https://platform.deepseek.com/docs)
- [LiteLLM Docs](https://docs.litellm.ai/)
- [Model Pricing](https://openrouter.ai/models)

---

## 📝 Example: Full Integration Test

```bash
#!/bin/bash
# Complete AI integration test

# 1. Set up OpenRouter (cheapest option)
export OPENROUTER_API_KEY='your-key-here'
export AI_MODEL='openrouter/deepseek/deepseek-chat'

# 2. Run the test
./scripts/test-ai-integration.sh

# 3. Check the output for:
#    - ✅ AI Analysis Complete!
#    - Summary of failures
#    - Root cause analysis
#    - Suggested actions
#    - Cost estimate

# 4. If successful, update TODO.md:
#    [x] Task 2.6 - Test AI analysis with live API ✅
```

---

**Next Steps After Successful Testing:**
1. Update TODO.md Task 2.6 as fully complete
2. Document recommended model in README.md
3. Add AI analysis examples to documentation
4. Consider making it a v1.1 feature (promoted from beta)
