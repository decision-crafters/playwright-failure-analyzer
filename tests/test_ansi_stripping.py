#!/usr/bin/env python3
"""
Tests for ANSI escape code stripping functionality.
"""

import os
import sys
import unittest

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from utils import format_stack_trace, strip_ansi_codes  # noqa: E402


class TestAnsiStripping(unittest.TestCase):
    """Test cases for ANSI escape code removal."""

    def test_strip_ansi_codes_basic(self):
        """Test basic ANSI code stripping."""
        # Real example from Playwright error message
        ansi_text = "\x1b[2mexpect(\x1b[22m\x1b[31mlocator\x1b[39m\x1b[2m).\x1b[22mtoHaveText\x1b[2m(\x1b[22m\x1b[32mexpected\x1b[39m\x1b[2m)\x1b[22m failed"
        expected = "expect(locator).toHaveText(expected) failed"

        result = strip_ansi_codes(ansi_text)
        self.assertEqual(result, expected)

    def test_strip_ansi_codes_color_only(self):
        """Test stripping color codes."""
        ansi_text = "\x1b[31mRed text\x1b[39m normal text \x1b[32mGreen text\x1b[39m"
        expected = "Red text normal text Green text"

        result = strip_ansi_codes(ansi_text)
        self.assertEqual(result, expected)

    def test_strip_ansi_codes_formatting(self):
        """Test stripping formatting codes."""
        ansi_text = "\x1b[1mBold\x1b[22m \x1b[2mDim\x1b[22m \x1b[3mItalic\x1b[23m"
        expected = "Bold Dim Italic"

        result = strip_ansi_codes(ansi_text)
        self.assertEqual(result, expected)

    def test_strip_ansi_codes_empty(self):
        """Test with empty string."""
        result = strip_ansi_codes("")
        self.assertEqual(result, "")

    def test_strip_ansi_codes_none(self):
        """Test with None."""
        result = strip_ansi_codes(None)
        self.assertIsNone(result)

    def test_strip_ansi_codes_no_codes(self):
        """Test with text that has no ANSI codes."""
        text = "Regular text without any codes"
        result = strip_ansi_codes(text)
        self.assertEqual(result, text)

    def test_format_stack_trace_strips_ansi(self):
        """Test that format_stack_trace strips ANSI codes."""
        stack_trace_with_ansi = """  at \x1b[31mObject.toHaveText\x1b[39m (playwright/lib/matchers.js:123)
  at \x1b[2mTestCase.run\x1b[22m (playwright/lib/test.js:456)
  at \x1b[32mWorker.runTest\x1b[39m (playwright/lib/worker.js:789)"""

        result = format_stack_trace(stack_trace_with_ansi)

        # Should not contain any ANSI escape sequences
        self.assertNotIn("\x1b[", result)
        self.assertNotIn("[31m", result)
        self.assertNotIn("[39m", result)

        # Should contain the cleaned text
        self.assertIn("Object.toHaveText", result)
        self.assertIn("TestCase.run", result)
        self.assertIn("Worker.runTest", result)

    def test_real_world_playwright_error(self):
        """Test with real Playwright error message."""
        error_msg = "\x1b[2mexpect(\x1b[22m\x1b[31mreceived\x1b[39m\x1b[2m).\x1b[22mtoEqual\x1b[2m(\x1b[22m\x1b[32mexpected\x1b[39m\x1b[2m)\x1b[22m // deep equality"
        expected = "expect(received).toEqual(expected) // deep equality"

        result = strip_ansi_codes(error_msg)
        self.assertEqual(result, expected)

    def test_complex_ansi_sequences(self):
        """Test with complex ANSI sequences."""
        # Test various ANSI codes
        text = "\x1b[0m\x1b[1;31mBold Red\x1b[0m \x1b[4;32mUnderline Green\x1b[0m"
        result = strip_ansi_codes(text)

        # Should not contain escape sequences
        self.assertNotIn("\x1b", result)
        # Should contain the text
        self.assertIn("Bold Red", result)
        self.assertIn("Underline Green", result)


if __name__ == "__main__":
    unittest.main()
