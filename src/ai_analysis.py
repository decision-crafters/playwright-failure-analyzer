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


class AIAnalyzer:
    """AI-powered analyzer for test failures using LiteLLM."""

    def __init__(self, model: str = "gpt-4o-mini", max_tokens: int = 1000):
        """
        Initialize the AI analyzer.

        Args:
            model: The LLM model to use (supports OpenAI, Anthropic, etc.)
            max_tokens: Maximum tokens for the response
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
        return """You are an expert software testing engineer specializing in analyzing test failures.
Your task is to analyze Playwright test failures and provide actionable insights.

Please analyze the provided test failures and respond with a JSON object containing:
1. "summary": A brief 1-2 sentence summary of the main issues
2. "root_cause_analysis": Detailed analysis of potential root causes
3. "suggested_actions": Array of specific actionable steps to resolve the issues
4. "confidence_score": Float between 0.0-1.0 indicating confidence in the analysis
5. "error_patterns": Array of common error patterns identified

Focus on:
- Common patterns across multiple failures
- Potential infrastructure or environment issues
- Code-related problems (selectors, timing, logic)
- Suggestions for improving test stability
- Prioritized action items

Be concise but thorough. Provide practical, actionable advice."""

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
            # Try to parse as JSON first
            if response_text.strip().startswith("{"):
                data = json.loads(response_text)
                return AIAnalysisResult(
                    summary=data.get("summary", "AI analysis completed"),
                    root_cause_analysis=data.get(
                        "root_cause_analysis", "No specific root cause identified"
                    ),
                    suggested_actions=data.get("suggested_actions", []),
                    confidence_score=float(data.get("confidence_score", 0.5)),
                    analysis_model=self.model,
                    error_patterns=data.get("error_patterns", []),
                )
            else:
                # Fallback: parse as plain text
                return self._parse_text_response(response_text)

        except json.JSONDecodeError:
            # Fallback to text parsing
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
            "## 🤖 AI Analysis",
            "",
            f"**Summary**: {analysis.summary}",
            "",
            "### Root Cause Analysis",
            analysis.root_cause_analysis,
            "",
        ]

        if analysis.suggested_actions:
            sections.extend(["### Suggested Actions", ""])
            for i, action in enumerate(analysis.suggested_actions, 1):
                sections.append(f"{i}. {action}")
            sections.append("")

        if analysis.error_patterns:
            sections.extend(["### Error Patterns Identified", ""])
            for pattern in analysis.error_patterns:
                sections.append(f"- {pattern}")
            sections.append("")

        # Add metadata
        sections.extend(
            [
                "---",
                f"*Analysis generated by {analysis.analysis_model} "
                f"(confidence: {analysis.confidence_score:.1%})*",
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
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
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
