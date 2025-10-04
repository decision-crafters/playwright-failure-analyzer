#!/usr/bin/env python3
"""
Utility functions for the Playwright Failure Bundler action.
"""

import os
import re
import hashlib
from typing import List, Optional, Dict, Any
from datetime import datetime


def get_github_context() -> Dict[str, str]:
    """Extract GitHub context from environment variables."""
    return {
        'repository': os.getenv('GITHUB_REPOSITORY', ''),
        'sha': os.getenv('GITHUB_SHA', ''),
        'ref': os.getenv('GITHUB_REF', ''),
        'run_id': os.getenv('GITHUB_RUN_ID', ''),
        'run_number': os.getenv('GITHUB_RUN_NUMBER', ''),
        'actor': os.getenv('GITHUB_ACTOR', ''),
        'workflow': os.getenv('GITHUB_WORKFLOW', ''),
        'event_name': os.getenv('GITHUB_EVENT_NAME', ''),
        'server_url': os.getenv('GITHUB_SERVER_URL', 'https://github.com'),
    }


def parse_comma_separated(value: str) -> List[str]:
    """Parse a comma-separated string into a list of trimmed values."""
    if not value or not value.strip():
        return []
    return [item.strip() for item in value.split(',') if item.strip()]


def sanitize_for_github(text: str) -> str:
    """Sanitize text for safe inclusion in GitHub issues."""
    # Remove or escape potentially problematic characters
    # This is a basic implementation - could be expanded based on needs
    sanitized = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Limit extremely long lines to prevent formatting issues
    lines = sanitized.split('\n')
    sanitized_lines = []
    for line in lines:
        if len(line) > 1000:
            sanitized_lines.append(line[:997] + '...')
        else:
            sanitized_lines.append(line)
    
    return '\n'.join(sanitized_lines)


def truncate_text(text: str, max_length: int = 65536) -> str:
    """Truncate text to fit within GitHub's limits."""
    if len(text) <= max_length:
        return text
    
    truncated = text[:max_length - 100]  # Leave room for truncation message
    truncated += '\n\n... (content truncated due to length limits)'
    return truncated


def generate_issue_hash(title: str, failures: List[Dict[str, Any]]) -> str:
    """Generate a hash for deduplication based on issue content."""
    # Create a stable hash based on the title and failure signatures
    content = title
    for failure in failures:
        # Use test name and error message for signature
        signature = f"{failure.get('test_name', '')}{failure.get('error_message', '')}"
        content += signature
    
    return hashlib.md5(content.encode('utf-8')).hexdigest()[:8]


def format_duration(duration_ms: float) -> str:
    """Format duration in milliseconds to a human-readable string."""
    if duration_ms < 1000:
        return f"{duration_ms:.0f}ms"
    elif duration_ms < 60000:
        return f"{duration_ms / 1000:.1f}s"
    else:
        minutes = int(duration_ms / 60000)
        seconds = (duration_ms % 60000) / 1000
        return f"{minutes}m {seconds:.1f}s"


def extract_file_name(file_path: str) -> str:
    """Extract just the filename from a full path."""
    return os.path.basename(file_path) if file_path else 'unknown'


def get_relative_path(file_path: str, base_path: str = None) -> str:
    """Get relative path from base path, or just filename if base not provided."""
    if not file_path:
        return 'unknown'
    
    if base_path and file_path.startswith(base_path):
        return os.path.relpath(file_path, base_path)
    
    # If no base path or file doesn't start with base, try to make it relative to common dirs
    common_prefixes = ['/home/runner/work/', '/github/workspace/', os.getcwd()]
    for prefix in common_prefixes:
        if file_path.startswith(prefix):
            return os.path.relpath(file_path, prefix)
    
    return file_path


def format_stack_trace(stack_trace: str, max_lines: int = 20) -> str:
    """Format and truncate stack trace for better readability."""
    if not stack_trace:
        return 'No stack trace available'
    
    lines = stack_trace.strip().split('\n')
    
    # Remove empty lines and excessive whitespace
    cleaned_lines = []
    for line in lines:
        cleaned_line = line.strip()
        if cleaned_line:
            cleaned_lines.append(cleaned_line)
    
    # Truncate if too long
    if len(cleaned_lines) > max_lines:
        cleaned_lines = cleaned_lines[:max_lines]
        cleaned_lines.append('... (stack trace truncated)')
    
    return '\n'.join(cleaned_lines)


def validate_github_token(token: str) -> bool:
    """Basic validation of GitHub token format."""
    if not token:
        return False
    
    # GitHub tokens typically start with specific prefixes
    valid_prefixes = ['ghp_', 'gho_', 'ghu_', 'ghs_', 'ghr_']
    
    return any(token.startswith(prefix) for prefix in valid_prefixes) or len(token) == 40


def set_github_output(name: str, value: str) -> None:
    """Set a GitHub Actions output variable."""
    # Use the new format for setting outputs
    github_output = os.getenv('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a', encoding='utf-8') as f:
            f.write(f"{name}={value}\n")
    else:
        # Fallback to the old format (deprecated but still works)
        print(f"::set-output name={name}::{value}")


def get_branch_name() -> str:
    """Extract branch name from GitHub ref."""
    ref = os.getenv('GITHUB_REF', '')
    if ref.startswith('refs/heads/'):
        return ref[11:]  # Remove 'refs/heads/' prefix
    elif ref.startswith('refs/pull/'):
        return f"PR #{ref.split('/')[2]}"
    else:
        return ref or 'unknown'


def format_timestamp(timestamp: Optional[str] = None) -> str:
    """Format timestamp for display in issues."""
    if timestamp:
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S UTC')
        except ValueError:
            pass
    
    return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
