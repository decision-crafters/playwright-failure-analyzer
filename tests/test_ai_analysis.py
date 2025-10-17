#!/usr/bin/env python3
"""
Unit tests for AI analysis functionality.
"""

import json
import os
import sys
import unittest
from unittest.mock import Mock, patch

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ai_analysis import (  # noqa: E402
    AIAnalysisFormatter,
    AIAnalysisResult,
    AIAnalyzer,
    analyze_failures_with_ai,
    create_ai_analyzer,
)


class TestAIAnalyzer(unittest.TestCase):
    """Test cases for AIAnalyzer."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_failures = [
            {
                "test_name": "Login Test",
                "file_path": "tests/login.spec.ts",
                "error_message": 'Element not found: [data-testid="login-button"]',
                "stack_trace": "Error: Element not found\n    at tests/login.spec.ts:15:5",
                "duration": 5000,
                "retry_count": 1,
            },
            {
                "test_name": "Dashboard Test",
                "file_path": "tests/dashboard.spec.ts",
                "error_message": "Navigation timeout of 30000ms exceeded",
                "stack_trace": "TimeoutError: Navigation timeout\n    at tests/dashboard.spec.ts:20:3",
                "duration": 30000,
                "retry_count": 0,
            },
        ]

        self.sample_metadata = {
            "total_tests": 10,
            "playwright_version": "1.40.0",
            "projects": ["chromium", "firefox"],
            "workers": 4,
        }

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    def test_analyzer_initialization(self):
        """Test AIAnalyzer initialization."""
        analyzer = AIAnalyzer(model="gpt-4.1-mini")
        self.assertEqual(analyzer.model, "gpt-4.1-mini")
        self.assertEqual(analyzer.max_tokens, 2500)  # Updated from 1000 to 2500

    def test_create_analysis_prompt(self):
        """Test prompt creation for AI analysis."""
        analyzer = AIAnalyzer()
        prompt = analyzer._create_analysis_prompt(self.sample_failures, self.sample_metadata)

        # Check that prompt contains key information
        self.assertIn("Login Test", prompt)
        self.assertIn("Dashboard Test", prompt)
        self.assertIn("Element not found", prompt)
        self.assertIn("Navigation timeout", prompt)
        self.assertIn("Playwright Version: 1.40.0", prompt)
        self.assertIn("Total Tests: 10", prompt)

    def test_parse_json_response(self):
        """Test parsing of JSON response from AI."""
        analyzer = AIAnalyzer()

        json_response = json.dumps(
            {
                "summary": "Multiple test failures due to element selector issues",
                "root_cause_analysis": "The failures appear to be caused by outdated selectors",
                "suggested_actions": [
                    "Update element selectors",
                    "Add explicit waits",
                    "Review page object model",
                ],
                "confidence_score": 0.85,
                "error_patterns": ["Selector not found", "Timeout errors"],
            }
        )

        result = analyzer._parse_analysis_response(json_response)

        self.assertIsInstance(result, AIAnalysisResult)
        self.assertEqual(result.summary, "Multiple test failures due to element selector issues")
        self.assertEqual(len(result.suggested_actions), 3)
        # Confidence is adjusted by model multiplier: 0.85 * 0.85 (balanced tier) = 0.7225
        self.assertAlmostEqual(result.confidence_score, 0.7225, places=3)
        self.assertEqual(len(result.error_patterns), 2)

    def test_parse_text_response(self):
        """Test parsing of plain text response as fallback."""
        analyzer = AIAnalyzer()

        text_response = """The main issue appears to be selector problems.

        Suggested actions:
        - Update selectors to use more stable attributes
        - Add explicit waits for dynamic content
        - Consider using data-testid attributes
        """

        result = analyzer._parse_analysis_response(text_response)

        self.assertIsInstance(result, AIAnalysisResult)
        self.assertIn("selector problems", result.summary)
        self.assertEqual(len(result.suggested_actions), 3)
        self.assertEqual(result.confidence_score, 0.7)  # Default for text parsing

    @patch("ai_analysis.litellm.completion")
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    def test_analyze_failures_success(self, mock_completion):
        """Test successful AI analysis."""
        # Mock the LiteLLM response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "summary": "Test failures due to timing issues",
                "root_cause_analysis": "Tests are failing due to race conditions",
                "suggested_actions": ["Add explicit waits", "Use stable selectors"],
                "confidence_score": 0.9,
                "error_patterns": ["Timeout", "Element not found"],
            }
        )
        mock_completion.return_value = mock_response

        analyzer = AIAnalyzer()
        result = analyzer.analyze_failures(self.sample_failures, self.sample_metadata)

        self.assertIsNotNone(result)
        self.assertEqual(result.summary, "Test failures due to timing issues")
        # Confidence is adjusted by model multiplier: 0.9 * 0.85 (balanced tier) = 0.765
        self.assertAlmostEqual(result.confidence_score, 0.765, places=3)

        # Verify LiteLLM was called correctly
        mock_completion.assert_called_once()
        call_args = mock_completion.call_args
        self.assertEqual(call_args.kwargs["model"], "gpt-4o-mini")  # Default model
        self.assertEqual(len(call_args.kwargs["messages"]), 2)

    @patch("ai_analysis.litellm.completion")
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    def test_analyze_failures_api_error(self, mock_completion):
        """Test handling of API errors."""
        mock_completion.side_effect = Exception("API Error")

        analyzer = AIAnalyzer()
        result = analyzer.analyze_failures(self.sample_failures, self.sample_metadata)

        # Should return None on error
        self.assertIsNone(result)

    def test_create_ai_analyzer_no_api_key(self):
        """Test analyzer creation without API key."""
        with patch.dict(os.environ, {}, clear=True):
            analyzer = create_ai_analyzer()
            self.assertIsNone(analyzer)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    def test_create_ai_analyzer_with_api_key(self):
        """Test analyzer creation with API key."""
        analyzer = create_ai_analyzer()
        self.assertIsNotNone(analyzer)
        self.assertIsInstance(analyzer, AIAnalyzer)

    def test_analyze_failures_with_ai_disabled(self):
        """Test convenience function with AI disabled."""
        result = analyze_failures_with_ai(self.sample_failures, self.sample_metadata, enabled=False)
        self.assertIsNone(result)

    def test_analyze_failures_with_ai_no_failures(self):
        """Test convenience function with no failures."""
        result = analyze_failures_with_ai([], self.sample_metadata, enabled=True)
        self.assertIsNone(result)


class TestAIAnalysisFormatter(unittest.TestCase):
    """Test cases for AIAnalysisFormatter."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_analysis = AIAnalysisResult(
            summary="Multiple test failures due to selector issues",
            root_cause_analysis="The failures appear to be caused by outdated element selectors that no longer match the current DOM structure.",
            suggested_actions=[
                "Update element selectors to use more stable attributes",
                "Add explicit waits for dynamic content",
                "Consider implementing a page object model",
            ],
            confidence_score=0.85,
            analysis_model="gpt-4.1-mini",
            error_patterns=["Selector not found", "Timeout errors", "Element not visible"],
        )

    def test_format_analysis_section(self):
        """Test formatting of complete AI analysis section."""
        formatted = AIAnalysisFormatter.format_analysis_section(self.sample_analysis)

        # Check that all sections are present
        self.assertIn("🤖 AI-Powered Analysis & Recommendations", formatted)
        self.assertIn("Root Cause Analysis", formatted)
        self.assertIn("Action Items", formatted)  # Changed from "Suggested Actions"
        self.assertIn("Error Patterns Identified", formatted)

        # Check specific content
        self.assertIn("selector issues", formatted)
        self.assertIn("Update element selectors", formatted)
        self.assertIn("Selector not found", formatted)
        self.assertIn("gpt-4.1-mini", formatted)
        self.assertIn("85.0%", formatted)  # Confidence score

    def test_format_analysis_section_empty(self):
        """Test formatting with no analysis."""
        formatted = AIAnalysisFormatter.format_analysis_section(None)
        self.assertEqual(formatted, "")

    def test_format_analysis_summary_high_confidence(self):
        """Test summary formatting with high confidence."""
        summary = AIAnalysisFormatter.format_analysis_summary(self.sample_analysis)
        self.assertIn("🤖 AI Analysis:", summary)
        self.assertIn("selector issues", summary)

    def test_format_analysis_summary_medium_confidence(self):
        """Test summary formatting with medium confidence."""
        medium_confidence_analysis = AIAnalysisResult(
            summary="Possible timing issues",
            root_cause_analysis="",
            suggested_actions=[],
            confidence_score=0.7,
            analysis_model="gpt-4.1-mini",
            error_patterns=[],
        )

        summary = AIAnalysisFormatter.format_analysis_summary(medium_confidence_analysis)
        self.assertIn("🤖 AI Insights:", summary)

    def test_format_analysis_summary_low_confidence(self):
        """Test summary formatting with low confidence."""
        low_confidence_analysis = AIAnalysisResult(
            summary="Unclear failure pattern",
            root_cause_analysis="",
            suggested_actions=[],
            confidence_score=0.4,
            analysis_model="gpt-4.1-mini",
            error_patterns=[],
        )

        summary = AIAnalysisFormatter.format_analysis_summary(low_confidence_analysis)
        self.assertIn("🤖 AI Notes:", summary)

    def test_format_minimal_analysis(self):
        """Test formatting with minimal analysis data."""
        minimal_analysis = AIAnalysisResult(
            summary="Basic analysis",
            root_cause_analysis="Limited information available",
            suggested_actions=[],
            confidence_score=0.5,
            analysis_model="gpt-4.1-mini",
            error_patterns=[],
        )

        formatted = AIAnalysisFormatter.format_analysis_section(minimal_analysis)

        self.assertIn("🤖 AI-Powered Analysis & Recommendations", formatted)
        self.assertIn("Basic analysis", formatted)
        self.assertIn("Limited information available", formatted)
        # Should not include empty sections
        self.assertNotIn("Action Items", formatted)  # Changed from "Suggested Actions"
        self.assertNotIn("Error Patterns Identified", formatted)


if __name__ == "__main__":
    unittest.main()
