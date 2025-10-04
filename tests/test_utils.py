#!/usr/bin/env python3
"""
Unit tests for utility functions.
"""

import os
import tempfile
import unittest
from unittest.mock import patch, mock_open
import sys

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils import (
    get_github_context, parse_comma_separated, sanitize_for_github,
    truncate_text, generate_issue_hash, format_duration, extract_file_name,
    get_relative_path, format_stack_trace, validate_github_token,
    set_github_output, get_branch_name, format_timestamp
)


class TestUtilityFunctions(unittest.TestCase):
    """Test cases for utility functions."""
    
    def test_parse_comma_separated(self):
        """Test parsing comma-separated strings."""
        # Normal case
        result = parse_comma_separated("bug,test,urgent")
        self.assertEqual(result, ["bug", "test", "urgent"])
        
        # With spaces
        result = parse_comma_separated("bug, test , urgent ")
        self.assertEqual(result, ["bug", "test", "urgent"])
        
        # Empty string
        result = parse_comma_separated("")
        self.assertEqual(result, [])
        
        # None input
        result = parse_comma_separated(None)
        self.assertEqual(result, [])
        
        # Single item
        result = parse_comma_separated("bug")
        self.assertEqual(result, ["bug"])
        
        # Empty items
        result = parse_comma_separated("bug,,test,")
        self.assertEqual(result, ["bug", "test"])
    
    def test_sanitize_for_github(self):
        """Test sanitizing text for GitHub issues."""
        # Normal text
        result = sanitize_for_github("Normal text")
        self.assertEqual(result, "Normal text")
        
        # Text with different line endings
        result = sanitize_for_github("Line 1\r\nLine 2\rLine 3\n")
        self.assertEqual(result, "Line 1\nLine 2\nLine 3\n")
        
        # Very long line
        long_line = "x" * 1500
        result = sanitize_for_github(long_line)
        self.assertTrue(len(result) < len(long_line))
        self.assertTrue(result.endswith("..."))
    
    def test_truncate_text(self):
        """Test text truncation."""
        # Short text
        short_text = "Short text"
        result = truncate_text(short_text, 100)
        self.assertEqual(result, short_text)
        
        # Long text
        long_text = "x" * 1000
        result = truncate_text(long_text, 500)
        self.assertTrue(len(result) <= 500)
        self.assertTrue(result.endswith("(content truncated due to length limits)"))
    
    def test_generate_issue_hash(self):
        """Test issue hash generation for deduplication."""
        failures1 = [
            {"test_name": "Test 1", "error_message": "Error 1"},
            {"test_name": "Test 2", "error_message": "Error 2"}
        ]
        failures2 = [
            {"test_name": "Test 1", "error_message": "Error 1"},
            {"test_name": "Test 2", "error_message": "Error 2"}
        ]
        failures3 = [
            {"test_name": "Test 1", "error_message": "Different Error"},
            {"test_name": "Test 2", "error_message": "Error 2"}
        ]
        
        hash1 = generate_issue_hash("Title", failures1)
        hash2 = generate_issue_hash("Title", failures2)
        hash3 = generate_issue_hash("Title", failures3)
        
        # Same content should produce same hash
        self.assertEqual(hash1, hash2)
        
        # Different content should produce different hash
        self.assertNotEqual(hash1, hash3)
        
        # Hash should be 8 characters
        self.assertEqual(len(hash1), 8)
    
    def test_format_duration(self):
        """Test duration formatting."""
        # Milliseconds
        self.assertEqual(format_duration(500), "500ms")
        
        # Seconds
        self.assertEqual(format_duration(1500), "1.5s")
        self.assertEqual(format_duration(5000), "5.0s")
        
        # Minutes
        self.assertEqual(format_duration(65000), "1m 5.0s")
        self.assertEqual(format_duration(125000), "2m 5.0s")
    
    def test_extract_file_name(self):
        """Test file name extraction."""
        self.assertEqual(extract_file_name("/path/to/file.ts"), "file.ts")
        self.assertEqual(extract_file_name("file.ts"), "file.ts")
        self.assertEqual(extract_file_name(""), "unknown")
        self.assertEqual(extract_file_name(None), "unknown")
    
    def test_get_relative_path(self):
        """Test relative path calculation."""
        # With base path
        result = get_relative_path("/home/user/project/tests/file.ts", "/home/user/project")
        self.assertEqual(result, "tests/file.ts")
        
        # Without base path
        result = get_relative_path("/some/path/file.ts")
        self.assertEqual(result, "/some/path/file.ts")
        
        # Empty path
        result = get_relative_path("")
        self.assertEqual(result, "unknown")
    
    def test_format_stack_trace(self):
        """Test stack trace formatting."""
        # Normal stack trace
        stack_trace = """Error: Test failed
    at test.spec.ts:10:5
    at Object.test (test.spec.ts:5:3)
    at runTest (runner.js:100:10)"""
        
        result = format_stack_trace(stack_trace)
        lines = result.split('\n')
        self.assertEqual(len(lines), 4)
        self.assertIn("Error: Test failed", result)
        
        # Empty stack trace
        result = format_stack_trace("")
        self.assertEqual(result, "No stack trace available")
        
        # Very long stack trace
        long_stack = '\n'.join([f"    at line{i}" for i in range(50)])
        result = format_stack_trace(long_stack, max_lines=10)
        lines = result.split('\n')
        self.assertLessEqual(len(lines), 11)  # 10 + truncation message
        self.assertIn("truncated", result)
    
    def test_validate_github_token(self):
        """Test GitHub token validation."""
        # Valid tokens
        self.assertTrue(validate_github_token("ghp_1234567890abcdef"))
        self.assertTrue(validate_github_token("gho_1234567890abcdef"))
        self.assertTrue(validate_github_token("x" * 40))  # Classic token format
        
        # Invalid tokens
        self.assertFalse(validate_github_token(""))
        self.assertFalse(validate_github_token("invalid"))
        self.assertFalse(validate_github_token("short"))
    
    @patch.dict(os.environ, {'GITHUB_REF': 'refs/heads/main'})
    def test_get_branch_name(self):
        """Test branch name extraction."""
        result = get_branch_name()
        self.assertEqual(result, "main")
    
    @patch.dict(os.environ, {'GITHUB_REF': 'refs/pull/123/merge'})
    def test_get_branch_name_pr(self):
        """Test branch name extraction for pull requests."""
        result = get_branch_name()
        self.assertEqual(result, "PR #123")
    
    @patch.dict(os.environ, {'GITHUB_REF': 'refs/tags/v1.0.0'})
    def test_get_branch_name_tag(self):
        """Test branch name extraction for tags."""
        result = get_branch_name()
        self.assertEqual(result, "refs/tags/v1.0.0")
    
    def test_format_timestamp(self):
        """Test timestamp formatting."""
        # Valid ISO timestamp
        result = format_timestamp("2023-12-01T10:30:00Z")
        self.assertIn("2023-12-01", result)
        self.assertIn("UTC", result)
        
        # Invalid timestamp
        result = format_timestamp("invalid")
        self.assertIn("UTC", result)  # Should fall back to current time
        
        # None timestamp
        result = format_timestamp(None)
        self.assertIn("UTC", result)  # Should fall back to current time
    
    @patch.dict(os.environ, {
        'GITHUB_REPOSITORY': 'owner/repo',
        'GITHUB_SHA': 'abc123',
        'GITHUB_REF': 'refs/heads/main',
        'GITHUB_RUN_ID': '123456',
        'GITHUB_ACTOR': 'testuser'
    })
    def test_get_github_context(self):
        """Test GitHub context extraction."""
        context = get_github_context()
        
        self.assertEqual(context['repository'], 'owner/repo')
        self.assertEqual(context['sha'], 'abc123')
        self.assertEqual(context['ref'], 'refs/heads/main')
        self.assertEqual(context['run_id'], '123456')
        self.assertEqual(context['actor'], 'testuser')
    
    @patch('builtins.open', new_callable=mock_open)
    @patch.dict(os.environ, {'GITHUB_OUTPUT': '/tmp/github_output'})
    def test_set_github_output_new_format(self, mock_file):
        """Test setting GitHub output using new format."""
        set_github_output('test-name', 'test-value')
        
        mock_file.assert_called_once_with('/tmp/github_output', 'a', encoding='utf-8')
        mock_file().write.assert_called_once_with('test-name=test-value\n')
    
    @patch('builtins.print')
    @patch.dict(os.environ, {}, clear=True)
    def test_set_github_output_fallback(self, mock_print):
        """Test setting GitHub output using fallback format."""
        set_github_output('test-name', 'test-value')
        
        mock_print.assert_called_once_with('::set-output name=test-name::test-value')


if __name__ == '__main__':
    unittest.main()
