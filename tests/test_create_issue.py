#!/usr/bin/env python3
"""
Unit tests for GitHub issue creation functionality.
"""

import json
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock, Mock
import sys

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from create_issue import GitHubAPIClient, IssueFormatter, IssueManager
from error_handling import setup_error_handling, ErrorCodes
try:
    from error_handling import ActionError
except ImportError:
    # Fallback for testing
    class ActionError(Exception):
        def __init__(self, code, message, severity, **kwargs):
            self.code = code
            self.message = message
            self.severity = severity
            super().__init__(message)
import requests


class TestGitHubAPIClient(unittest.TestCase):
    """Test cases for GitHubAPIClient."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.error_handler = setup_error_handling(debug_mode=True)
        self.client = GitHubAPIClient("fake_token", "owner/repo", self.error_handler)
    
    @patch('create_issue.requests.Session.get')
    def test_search_issues_success(self, mock_get):
        """Test successful issue search."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'items': [
                {'number': 1, 'title': 'Test Issue', 'html_url': 'https://github.com/owner/repo/issues/1'}
            ]
        }
        mock_get.return_value = mock_response
        
        issues = self.client.search_issues('test query')
        
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]['number'], 1)
        mock_get.assert_called_once()
    
    @patch('create_issue.requests.Session.post')
    def test_create_issue_success(self, mock_post):
        """Test successful issue creation."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'number': 42,
            'html_url': 'https://github.com/owner/repo/issues/42',
            'title': 'Test Issue'
        }
        mock_post.return_value = mock_response
        
        issue = self.client.create_issue(
            title="Test Issue",
            body="Test body",
            labels=["bug", "test"],
            assignees=["user1"]
        )
        
        self.assertEqual(issue['number'], 42)
        self.assertEqual(issue['title'], 'Test Issue')
        
        # Verify the request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertIn('json', call_args.kwargs)
        request_data = call_args.kwargs['json']
        self.assertEqual(request_data['title'], 'Test Issue')
        self.assertEqual(request_data['body'], 'Test body')
        self.assertEqual(request_data['labels'], ['bug', 'test'])
        self.assertEqual(request_data['assignees'], ['user1'])
    
    @patch('create_issue.requests.Session.get')
    def test_rate_limiting(self, mock_get):
        """Test handling of rate limiting."""
        # First call returns rate limit error
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {'Retry-After': '1'}
        
        # Second call succeeds
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {'items': []}
        
        mock_get.side_effect = [rate_limit_response, success_response]
        
        with patch('time.sleep') as mock_sleep:
            issues = self.client.search_issues('test')
            
            self.assertEqual(issues, [])
            mock_sleep.assert_called_once_with(1)
            self.assertEqual(mock_get.call_count, 2)
    
    @patch('create_issue.requests.Session.post')
    def test_permission_error(self, mock_post):
        """Test handling of permission errors."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        mock_post.return_value = mock_response
        
        with self.assertRaises(ActionError) as context:
            self.client.create_issue("Test", "Body")
        
        self.assertEqual(context.exception.code, ErrorCodes.API_PERMISSION_DENIED)
    
    @patch('create_issue.requests.Session.post')
    def test_invalid_token_error(self, mock_post):
        """Test handling of invalid token errors."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response
        
        with self.assertRaises(ActionError) as context:
            self.client.create_issue("Test", "Body")
        
        self.assertEqual(context.exception.code, ErrorCodes.INVALID_TOKEN)


class TestIssueFormatter(unittest.TestCase):
    """Test cases for IssueFormatter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.github_context = {
            'repository': 'owner/repo',
            'sha': 'abc123def456',
            'ref': 'refs/heads/main',
            'run_id': '123456789',
            'run_number': '42',
            'actor': 'testuser',
            'workflow': 'CI',
            'event_name': 'push',
            'server_url': 'https://github.com'
        }
        self.formatter = IssueFormatter(self.github_context)
        
        self.sample_summary = {
            'total_tests': 10,
            'passed_tests': 7,
            'failed_tests': 3,
            'skipped_tests': 0,
            'duration': 45000,
            'failures': [
                {
                    'test_name': 'Login Test',
                    'file_path': 'tests/login.spec.ts',
                    'line_number': 15,
                    'error_message': 'Element not found',
                    'stack_trace': 'Error: Element not found\n    at tests/login.spec.ts:15:5',
                    'duration': 5000,
                    'retry_count': 1
                },
                {
                    'test_name': 'Dashboard Test',
                    'file_path': 'tests/dashboard.spec.ts',
                    'line_number': 20,
                    'error_message': 'Timeout exceeded',
                    'stack_trace': 'TimeoutError: Timeout exceeded\n    at tests/dashboard.spec.ts:20:3',
                    'duration': 30000,
                    'retry_count': 0
                }
            ],
            'metadata': {
                'playwright_version': '1.40.0',
                'projects': ['chromium', 'firefox'],
                'workers': 4
            }
        }
    
    def test_format_issue_body(self):
        """Test formatting of complete issue body."""
        body = self.formatter.format_issue_body(self.sample_summary)
        
        # Check that all major sections are present
        self.assertIn('🚨 Playwright Test Failures Detected', body)
        self.assertIn('📊 Test Run Summary', body)
        self.assertIn('📋 Failure Details', body)
        self.assertIn('🔍 Debug Information', body)
        self.assertIn('🚀 Next Steps', body)
        
        # Check specific content
        self.assertIn('3 test failures detected', body)
        self.assertIn('Login Test', body)
        self.assertIn('Dashboard Test', body)
        self.assertIn('owner/repo', body)
        self.assertIn('abc123de', body)  # Truncated SHA
    
    def test_format_summary_stats(self):
        """Test formatting of summary statistics."""
        stats = self.formatter._format_summary_stats(self.sample_summary)
        
        self.assertIn('| **Total Tests** | 10 |', stats)
        self.assertIn('| **Passed** | ✅ 7 |', stats)
        self.assertIn('| **Failed** | ❌ 3 |', stats)
        self.assertIn('| **Duration** | 45.0s |', stats)
    
    def test_format_failure_details(self):
        """Test formatting of failure details."""
        details = self.formatter._format_failure_details(self.sample_summary['failures'])
        
        self.assertIn('### 1. Login Test', details)
        self.assertIn('### 2. Dashboard Test', details)
        self.assertIn('`tests/login.spec.ts`', details)
        self.assertIn('Element not found', details)
        self.assertIn('Timeout exceeded', details)
        self.assertIn('**Stack Trace**:', details)
    
    def test_format_debug_info(self):
        """Test formatting of debug information."""
        debug_info = self.formatter._format_debug_info(self.sample_summary)
        
        self.assertIn('| **Repository** | owner/repo |', debug_info)
        self.assertIn('| **Commit** | `abc123de` |', debug_info)
        self.assertIn('| **Run ID** | [123456789]', debug_info)
        self.assertIn('| **Playwright Version** | 1.40.0 |', debug_info)
        self.assertIn('| **Projects** | chromium, firefox |', debug_info)
    
    def test_empty_failures(self):
        """Test handling of empty failures list."""
        empty_summary = self.sample_summary.copy()
        empty_summary['failures'] = []
        
        details = self.formatter._format_failure_details([])
        self.assertIn('No failure details available', details)


class TestIssueManager(unittest.TestCase):
    """Test cases for IssueManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.error_handler = setup_error_handling(debug_mode=True)
        self.mock_client = Mock(spec=GitHubAPIClient)
        self.mock_formatter = Mock(spec=IssueFormatter)
        self.manager = IssueManager(self.mock_client, self.mock_formatter)
        
        self.sample_summary = {
            'failed_tests': 2,
            'failures': [{'test_name': 'Test 1'}, {'test_name': 'Test 2'}]
        }
    
    def test_create_new_issue(self):
        """Test creating a new issue when no existing issue found."""
        self.mock_formatter.format_issue_body.return_value = "Formatted body"
        self.mock_client.search_issues.return_value = []
        self.mock_client.create_issue.return_value = {
            'number': 42,
            'html_url': 'https://github.com/owner/repo/issues/42'
        }
        
        issue_number, issue_url, was_created = self.manager.create_or_update_issue(
            self.sample_summary, "Test Issue", ["bug"], ["user1"], True
        )
        
        self.assertEqual(issue_number, 42)
        self.assertEqual(issue_url, 'https://github.com/owner/repo/issues/42')
        self.assertTrue(was_created)
        
        self.mock_client.create_issue.assert_called_once_with(
            "Test Issue", "Formatted body", ["bug"], ["user1"]
        )
    
    def test_update_existing_issue(self):
        """Test updating an existing issue when deduplication is enabled."""
        self.mock_formatter.format_issue_body.return_value = "Updated body"
        self.mock_client.search_issues.return_value = [
            {
                'number': 24,
                'title': 'Test Issue',
                'html_url': 'https://github.com/owner/repo/issues/24'
            }
        ]
        self.mock_client.update_issue.return_value = {
            'number': 24,
            'html_url': 'https://github.com/owner/repo/issues/24'
        }
        
        issue_number, issue_url, was_created = self.manager.create_or_update_issue(
            self.sample_summary, "Test Issue", ["bug"], ["user1"], True
        )
        
        self.assertEqual(issue_number, 24)
        self.assertEqual(issue_url, 'https://github.com/owner/repo/issues/24')
        self.assertFalse(was_created)
        
        self.mock_client.update_issue.assert_called_once_with(24, body="Updated body")
    
    def test_skip_deduplication(self):
        """Test skipping deduplication when disabled."""
        self.mock_formatter.format_issue_body.return_value = "Formatted body"
        self.mock_client.create_issue.return_value = {
            'number': 42,
            'html_url': 'https://github.com/owner/repo/issues/42'
        }
        
        issue_number, issue_url, was_created = self.manager.create_or_update_issue(
            self.sample_summary, "Test Issue", ["bug"], ["user1"], False
        )
        
        self.assertEqual(issue_number, 42)
        self.assertTrue(was_created)
        
        # Should not search for existing issues
        self.mock_client.search_issues.assert_not_called()
        self.mock_client.create_issue.assert_called_once()


if __name__ == '__main__':
    unittest.main()
