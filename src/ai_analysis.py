#!/usr/bin/env python3
"""
AI Analysis Module

This module provides AI-powered analysis of test failures using LiteLLM
to generate insights and potential root cause analysis.
"""

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import litellm


@dataclass
class AIAnalysisResult:
    """Result of AI analysis of test failures."""

    summary: str
    root_cause_analysis: str
    suggested_actions: List[str]
    confidence_score: float
    analysis_model: str
    error_patterns: List[str]
    # Enhanced fields for actionable analysis
    priority_assessment: Optional[Dict[str, List[str]]] = None
    work_order: Optional[List[str]] = None
    specific_fixes: Optional[List[Dict[str, str]]] = None
    failure_categories: Optional[Dict[str, List[str]]] = None
    quick_wins: Optional[List[str]] = None
    test_quality_feedback: Optional[List[Dict[str, str]]] = None


class AIAnalyzer:
    """AI-powered analyzer for test failures using LiteLLM."""

    def __init__(self, model: str = "gpt-4o-mini", max_tokens: int = 2500):
        """
        Initialize the AI analyzer.

        Args:
            model: The LLM model to use (supports OpenAI, Anthropic, etc.)
            max_tokens: Maximum tokens for the response (increased to support detailed analysis)
        """
        self.model = model
        self.max_tokens = max_tokens
        self.logger = logging.getLogger(__name__)

        # Configure LiteLLM
        self._setup_litellm()

    def _setup_litellm(self) -> None:
        """Setup LiteLLM configuration."""
        # LiteLLM will automatically use environment variables for API keys
        # OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.

        # Set logging level for LiteLLM
        litellm.set_verbose = False

        # Configure default settings
        litellm.drop_params = True  # Drop unsupported parameters
        litellm.modify_params = True  # Modify parameters for compatibility

    def analyze_failures(
        self, failures: List[Dict[str, Any]], metadata: Dict[str, Any]
    ) -> Optional[AIAnalysisResult]:
        """
        Analyze test failures using AI to provide insights.

        Args:
            failures: List of test failure data
            metadata: Additional context about the test run

        Returns:
            AIAnalysisResult if successful, None if analysis fails
        """
        try:
            # Prepare the prompt with failure data
            prompt = self._create_analysis_prompt(failures, metadata)

            # Call the LLM
            response = litellm.completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.max_tokens,
                temperature=0.3,  # Lower temperature for more consistent analysis
                timeout=30,
            )

            # Parse the response
            analysis_text = response.choices[0].message.content
            return self._parse_analysis_response(analysis_text)

        except Exception as e:
            self.logger.warning(f"AI analysis failed: {e}")
            return None

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the AI analysis."""
        return """You are an expert QA engineer and test automation specialist analyzing Playwright test failures.

CRITICAL: Respond with ONLY a valid JSON object. No markdown code blocks, no additional text, no formatting.

Your response must help developers quickly understand:
1. WHAT to fix first (priority)
2. HOW LONG it will take (effort)
3. WHERE to make changes (specific fixes)
4. WHY it's failing (root cause)

Required JSON structure (respond with this exact structure):
{
  "summary": "1-2 sentence executive summary",
  "priority_assessment": {
    "critical": ["List critical failures blocking core functionality"],
    "high": ["Failures affecting multiple features"],
    "medium": ["Isolated issues or flaky tests"],
    "low": ["Minor issues or test-only problems"]
  },
  "work_order": [
    "Recommended fix order for maximum efficiency",
    "Example: Fix test 1 first - unblocks 3 other failures"
  ],
  "specific_fixes": [
    {
      "test": "file.spec.js:line_number",
      "issue": "What's wrong",
      "fix": "Specific action to take",
      "code_hint": "Suggested code change",
      "estimated_time": "5 min | 30 min | 2 hours",
      "complexity": "trivial | easy | moderate | complex"
    }
  ],
  "failure_categories": {
    "test_code_issues": ["Broken selectors, bad waits"],
    "application_bugs": ["Real bugs in the app"],
    "infrastructure": ["Environment, network, CI issues"],
    "flaky_tests": ["Intermittent failures"]
  },
  "quick_wins": [
    "List 1-3 failures fixable in under 10 minutes"
  ],
  "root_cause_analysis": "Detailed explanation of underlying causes",
  "suggested_actions": [
    "Prioritized, specific action items",
    "Include file:line references where possible"
  ],
  "test_quality_feedback": [
    {
      "issue": "Problem with test approach",
      "recommendation": "How to improve reliability",
      "benefit": "Why this matters"
    }
  ],
  "confidence_score": 0.8,
  "error_patterns": ["timeout", "selector", "network"]
}

Guidelines:
- PRIORITIZE: Most critical/blocking failures first
- BE SPECIFIC: Provide file:line references and exact fixes
- ESTIMATE EFFORT: Help developers plan time
- GROUP RELATED: Identify failures with common causes
- QUICK WINS: Highlight fast fixes for immediate progress
- BE ACTIONABLE: Every suggestion should be immediately actionable
- CONSIDER CONTEXT: Note if failures are intentional, environmental, or genuine bugs

Remember: Developers need to know WHAT to fix, in WHAT ORDER, and HOW LONG it will take.
Respond with valid JSON only - no markdown formatting."""

    def _create_analysis_prompt(
        self, failures: List[Dict[str, Any]], metadata: Dict[str, Any]
    ) -> str:
        """Create the analysis prompt with failure data."""

        # Limit the number of failures to analyze to avoid token limits
        max_failures = 5
        limited_failures = failures[:max_failures]

        prompt_parts = [
            "Please analyze the following Playwright test failures:\n",
            "Test Run Context:",
            f"- Total Tests: {metadata.get('total_tests', 'unknown')}",
            f"- Failed Tests: {len(failures)}",
            f"- Playwright Version: {metadata.get('playwright_version', 'unknown')}",
            f"- Projects: {', '.join(metadata.get('projects', []))}",
            f"- Workers: {metadata.get('workers', 'unknown')}\n",
            "Failure Details:\n",
        ]

        for i, failure in enumerate(limited_failures, 1):
            # Extract key information from failure
            test_name = failure.get("test_name", "Unknown Test")
            file_path = failure.get("file_path", "unknown")
            error_message = failure.get("error_message", "No error message")
            stack_trace = failure.get("stack_trace", "")
            duration = failure.get("duration", 0)
            retry_count = failure.get("retry_count", 0)

            # Truncate long stack traces
            if len(stack_trace) > 500:
                stack_trace = stack_trace[:500] + "... (truncated)"

            prompt_parts.extend(
                [
                    f"\n{i}. Test: {test_name}",
                    f"   File: {file_path}",
                    f"   Duration: {duration}ms",
                    f"   Retries: {retry_count}",
                    f"   Error: {error_message}",
                    f"   Stack Trace: {stack_trace}\n",
                ]
            )

        if len(failures) > max_failures:
            prompt_parts.append(f"\n... and {len(failures) - max_failures} more similar failures")

        return "\n".join(prompt_parts)

    def _parse_analysis_response(self, response_text: str) -> AIAnalysisResult:
        """Parse the AI response into structured data."""
        try:
            # Extract JSON from potential markdown code blocks
            json_text = response_text.strip()

            # Remove markdown code fences if present
            if "```json" in json_text:
                # Extract content between ```json and ```
                start = json_text.find("```json") + 7
                end = json_text.find("```", start)
                if end > start:
                    json_text = json_text[start:end].strip()
            elif "```" in json_text:
                # Generic code block
                start = json_text.find("```") + 3
                end = json_text.find("```", start)
                if end > start:
                    json_text = json_text[start:end].strip()

            # Try to find JSON object boundaries
            if "{" in json_text:
                # Find first { and last }
                start = json_text.find("{")
                end = json_text.rfind("}")
                if start >= 0 and end > start:
                    json_text = json_text[start : end + 1]

                    # Parse JSON
                    data = json.loads(json_text)

                    return AIAnalysisResult(
                        summary=data.get("summary", "AI analysis completed"),
                        root_cause_analysis=data.get(
                            "root_cause_analysis", "No specific root cause identified"
                        ),
                        suggested_actions=data.get("suggested_actions", []),
                        confidence_score=float(data.get("confidence_score", 0.5)),
                        analysis_model=self.model,
                        error_patterns=data.get("error_patterns", []),
                        # Enhanced fields
                        priority_assessment=data.get("priority_assessment"),
                        work_order=data.get("work_order"),
                        specific_fixes=data.get("specific_fixes"),
                        failure_categories=data.get("failure_categories"),
                        quick_wins=data.get("quick_wins"),
                        test_quality_feedback=data.get("test_quality_feedback"),
                    )

            # Fallback: parse as plain text
            return self._parse_text_response(response_text)

        except (json.JSONDecodeError, ValueError) as e:
            self.logger.warning(f"Failed to parse JSON response: {e}")
            return self._parse_text_response(response_text)

    def _parse_text_response(self, response_text: str) -> AIAnalysisResult:
        """Parse plain text response as fallback."""
        lines = response_text.strip().split("\n")

        # Extract summary (first non-empty line)
        summary = next((line.strip() for line in lines if line.strip()), "AI analysis completed")

        # Look for action items or suggestions
        suggested_actions = []
        for line in lines:
            line = line.strip()
            if (
                line.startswith("- ")
                or line.startswith("* ")
                or line.startswith("1.")
                or line.startswith("2.")
            ):
                suggested_actions.append(line.lstrip("- *123456789. "))

        return AIAnalysisResult(
            summary=summary[:200],  # Limit summary length
            root_cause_analysis=response_text[:500],  # Limit analysis length
            suggested_actions=suggested_actions[:5],  # Limit to 5 actions
            confidence_score=0.7,  # Default confidence for text parsing
            analysis_model=self.model,
            error_patterns=[],
        )


class AIAnalysisFormatter:
    """Formats AI analysis results for inclusion in GitHub issues."""

    @staticmethod
    def format_analysis_section(analysis: AIAnalysisResult) -> str:
        """Format AI analysis for GitHub issue."""
        if not analysis:
            return ""

        sections = [
            "## 🤖 AI-Powered Analysis & Recommendations",
            "",
            f"**Summary**: {analysis.summary}",
            "",
        ]

        # Priority Assessment
        if analysis.priority_assessment:
            sections.extend(["### 🎯 Priority Assessment", ""])
            priority_emojis = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🟢",
            }
            for level in ["critical", "high", "medium", "low"]:
                failures = analysis.priority_assessment.get(level, [])
                if failures:
                    emoji = priority_emojis.get(level, "⚪")
                    sections.append(f"**{emoji} {level.title()}**: {', '.join(failures)}")
            sections.append("")

        # Work Order
        if analysis.work_order:
            sections.extend(["### 📋 Recommended Work Order", ""])
            for i, step in enumerate(analysis.work_order, 1):
                sections.append(f"{i}. {step}")
            sections.append("")

        # Quick Wins
        if analysis.quick_wins:
            sections.extend(["### ⚡ Quick Wins (< 10 minutes)", ""])
            for win in analysis.quick_wins:
                sections.append(f"- {win}")
            sections.append("")

        # Specific Fixes
        if analysis.specific_fixes:
            sections.extend(["### 🔧 Specific Fix Recommendations", ""])
            for fix in analysis.specific_fixes:
                sections.append(f"**{fix.get('test', 'Unknown')}**")
                sections.append(f"- **Issue**: {fix.get('issue', 'N/A')}")
                sections.append(f"- **Fix**: {fix.get('fix', 'N/A')}")
                if fix.get("code_hint"):
                    sections.append(f"- **Code suggestion**: `{fix['code_hint']}`")
                sections.append(
                    f"- **Effort**: {fix.get('estimated_time', 'Unknown')} "
                    f"({fix.get('complexity', 'unknown')} complexity)"
                )
                sections.append("")

        # Failure Categories
        if analysis.failure_categories:
            sections.extend(["### 📊 Failure Categories", ""])
            category_labels = {
                "test_code_issues": "🧪 Test Code Issues",
                "application_bugs": "🐛 Application Bugs",
                "infrastructure": "🏗️ Infrastructure",
                "flaky_tests": "🎲 Flaky Tests",
            }
            for category, label in category_labels.items():
                issues = analysis.failure_categories.get(category, [])
                if issues:
                    sections.append(f"**{label}**: {', '.join(issues)}")
            sections.append("")

        # Root Cause
        sections.extend(["### 🔍 Root Cause Analysis", analysis.root_cause_analysis, ""])

        # Suggested Actions
        if analysis.suggested_actions:
            sections.extend(["### ✅ Action Items", ""])
            for i, action in enumerate(analysis.suggested_actions, 1):
                sections.append(f"{i}. {action}")
            sections.append("")

        # Test Quality Feedback
        if analysis.test_quality_feedback:
            sections.extend(["### 💡 Test Quality Improvements", ""])
            for feedback in analysis.test_quality_feedback:
                sections.append(f"**Issue**: {feedback.get('issue', 'N/A')}")
                sections.append(f"**Recommendation**: {feedback.get('recommendation', 'N/A')}")
                sections.append(f"**Benefit**: {feedback.get('benefit', 'N/A')}")
                sections.append("")

        # Error Patterns
        if analysis.error_patterns:
            sections.extend(["### 🔎 Error Patterns Identified", ""])
            for pattern in analysis.error_patterns:
                sections.append(f"- {pattern}")
            sections.append("")

        # Metadata
        sections.extend(
            [
                "---",
                f"*Analysis generated by {analysis.analysis_model} "
                f"(confidence: {analysis.confidence_score:.1%})*",
                "",
                "💬 **Need help?** Comment on this issue with questions about the analysis.",
            ]
        )

        return "\n".join(sections)

    @staticmethod
    def format_analysis_summary(analysis: AIAnalysisResult) -> str:
        """Format a brief analysis summary for issue title or description."""
        if not analysis:
            return ""

        summary = analysis.summary
        if analysis.confidence_score >= 0.8:
            return f"🤖 AI Analysis: {summary}"
        elif analysis.confidence_score >= 0.6:
            return f"🤖 AI Insights: {summary}"
        else:
            return f"🤖 AI Notes: {summary}"


def create_ai_analyzer(model: str = None) -> Optional[AIAnalyzer]:
    """
    Create an AI analyzer instance with proper configuration.

    Args:
        model: Optional model override

    Returns:
        AIAnalyzer instance or None if not configured
    """
    # Check if AI analysis is enabled and configured
    # OpenRouter, DeepSeek, and other providers supported via LiteLLM
    has_key = (
        os.getenv("OPENAI_API_KEY")
        or os.getenv("ANTHROPIC_API_KEY")
        or os.getenv("OPENROUTER_API_KEY")
        or os.getenv("DEEPSEEK_API_KEY")
    )
    if not has_key:
        return None

    # Use provided model or default
    if not model:
        model = os.getenv("AI_MODEL", "gpt-4o-mini")

    try:
        return AIAnalyzer(model=model)
    except Exception as e:
        logging.warning(f"Failed to create AI analyzer: {e}")
        return None


def analyze_failures_with_ai(
    failures: List[Dict[str, Any]], metadata: Dict[str, Any], enabled: bool = True
) -> Optional[AIAnalysisResult]:
    """
    Convenience function to analyze failures with AI.

    Args:
        failures: List of test failure data
        metadata: Test run metadata
        enabled: Whether AI analysis is enabled

    Returns:
        AIAnalysisResult or None
    """
    if not enabled or not failures:
        return None

    analyzer = create_ai_analyzer()
    if not analyzer:
        return None

    return analyzer.analyze_failures(failures, metadata)
