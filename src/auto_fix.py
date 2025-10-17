#!/usr/bin/env python3
"""
Auto-Fix Module

Generates suggested fixes for test failures and can create branches or PRs.
"""

import json
import logging
import subprocess  # nosec B404
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

try:
    import litellm

    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False


@dataclass
class FixSuggestion:
    """Represents a suggested fix for a test failure."""

    file_path: str
    line_number: Optional[int]
    original_code: str
    suggested_code: str
    reasoning: str
    confidence: float
    pattern: str


class AutoFixGenerator:
    """Generates code fixes for test failures using AI."""

    # Pattern-specific fix prompts
    FIX_PROMPTS = {
        "missing_await": """Fix missing await in async Playwright test.

File: {file_path}
Line: {line_number}
Error: {error_message}

Task: Add missing 'await' keyword before the async operation.

Return ONLY valid JSON:
{{
  "original_code": "const response = page.goto(url)",
  "suggested_code": "const response = await page.goto(url)",
  "reasoning": "Added missing await for async operation",
  "confidence": 0.95
}}""",
        "selector_timeout": """Fix selector timeout in Playwright test.

File: {file_path}
Line: {line_number}
Error: {error_message}

Task: Fix the selector or add appropriate timeout.

Return ONLY valid JSON:
{{
  "original_code": "await page.click('.button')",
  "suggested_code": "await page.click('.button', {{ timeout: 30000 }})",
  "reasoning": "Added explicit timeout to prevent timeout errors",
  "confidence": 0.85
}}""",
        "navigation_timeout": """Fix navigation timeout in Playwright test.

File: {file_path}
Line: {line_number}
Error: {error_message}

Task: Add or increase timeout for page navigation.

Return ONLY valid JSON:
{{
  "original_code": "await page.goto(url)",
  "suggested_code": "await page.goto(url, {{ timeout: 60000, waitUntil: 'networkidle' }})",
  "reasoning": "Increased timeout and wait for network idle",
  "confidence": 0.80
}}""",
        "type_mismatch": """Fix TypeScript type mismatch in Playwright test.

File: {file_path}
Line: {line_number}
Error: {error_message}

Task: Fix the type annotation or convert the value.

Return ONLY valid JSON:
{{
  "original_code": "const count: string = await page.locator('.items').count()",
  "suggested_code": "const count: number = await page.locator('.items').count()",
  "reasoning": "Changed type from string to number to match count() return type",
  "confidence": 0.90
}}""",
    }

    def __init__(self, model: str = "gpt-4o-mini"):
        """Initialize the auto-fix generator."""
        self.model = model
        self.logger = logging.getLogger(__name__)

    def generate_fix(
        self, failure: Dict[str, Any], file_content: Optional[str] = None
    ) -> Optional[FixSuggestion]:
        """
        Generate a fix suggestion for a test failure.

        Args:
            failure: Failure data from structured JSON
            file_content: Optional full file content for context

        Returns:
            FixSuggestion if successful, None otherwise
        """
        if not AI_AVAILABLE:
            self.logger.warning("AI not available for fix generation")
            return None

        try:
            pattern = failure.get("suggested_pattern", "unknown_pattern")
            prompt = self._build_fix_prompt(failure, pattern, file_content)

            # Call AI to generate fix
            response = litellm.completion(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a Playwright test fixing expert. Return ONLY valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,  # Low temperature for deterministic fixes
                max_tokens=500,
                timeout=20,
            )

            fix_data = self._parse_fix_response(response.choices[0].message.content)

            if fix_data:
                return FixSuggestion(
                    file_path=failure["file_path"],
                    line_number=failure.get("line_number"),
                    original_code=fix_data["original_code"],
                    suggested_code=fix_data["suggested_code"],
                    reasoning=fix_data["reasoning"],
                    confidence=float(fix_data.get("confidence", 0.7)),
                    pattern=pattern,
                )

            return None

        except Exception as e:
            self.logger.warning(f"Failed to generate fix: {e}")
            return None

    def _build_fix_prompt(
        self, failure: Dict[str, Any], pattern: str, file_content: Optional[str] = None
    ) -> str:
        """Build the appropriate prompt based on error pattern."""
        # Get pattern-specific prompt or use generic
        prompt_template = self.FIX_PROMPTS.get(pattern, self.FIX_PROMPTS["selector_timeout"])

        # Format with failure data
        return prompt_template.format(
            file_path=failure["file_path"],
            line_number=failure.get("line_number", "unknown"),
            error_message=failure["error_message"],
        )

    def _parse_fix_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse AI response into fix data."""
        try:
            # Extract JSON from response
            json_text = response_text.strip()

            # Remove markdown code blocks
            if "```json" in json_text:
                start = json_text.find("```json") + 7
                end = json_text.find("```", start)
                if end > start:
                    json_text = json_text[start:end].strip()
            elif "```" in json_text:
                start = json_text.find("```") + 3
                end = json_text.find("```", start)
                if end > start:
                    json_text = json_text[start:end].strip()

            # Find JSON object
            if "{" in json_text:
                start = json_text.find("{")
                end = json_text.rfind("}")
                if start >= 0 and end > start:
                    json_text = json_text[start:end + 1]
                    return json.loads(json_text)

            return None

        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse fix response: {e}")
            return None


class GitHubBranchManager:
    """Manages GitHub branch operations for auto-fix."""

    def __init__(self, token: str, repository: str):
        """Initialize the branch manager."""
        self.token = token
        self.repository = repository
        self.logger = logging.getLogger(__name__)

    def create_fix_branch(
        self, issue_number: int, pattern: str, fix_suggestions: List[FixSuggestion]
    ) -> Optional[str]:
        """
        Create a branch with suggested fixes.

        Args:
            issue_number: GitHub issue number
            pattern: Error pattern name
            fix_suggestions: List of fix suggestions to apply

        Returns:
            Branch name if successful, None otherwise
        """
        branch_name = f"autofix/issue-{issue_number}-{pattern}"

        try:
            # Configure git
            subprocess.run(
                ["git", "config", "user.name", "Playwright Auto-Fixer"], check=True
            )  # nosec B603 B607
            subprocess.run(
                ["git", "config", "user.email", "autofix@playwright-analyzer"],
                check=True,  # nosec B603 B607
            )

            # Create and checkout new branch
            subprocess.run(["git", "checkout", "-b", branch_name], check=True)  # nosec B603 B607

            # Apply fixes
            for fix in fix_suggestions:
                self._apply_fix_to_file(fix)

            # Commit changes
            commit_message = f"""🤖 Auto-fix: Apply suggested fixes for issue #{issue_number}

Pattern: {pattern}
Fixes applied: {len(fix_suggestions)}

⚠️ This is an AI-generated fix. Review before merging.

Co-authored-by: Playwright Failure Analyzer <noreply@playwright-analyzer>
"""
            subprocess.run(["git", "add", "."], check=True)  # nosec B603 B607
            subprocess.run(["git", "commit", "-m", commit_message], check=True)  # nosec B603 B607

            # Push branch
            subprocess.run(
                ["git", "push", "-u", "origin", branch_name], check=True
            )  # nosec B603 B607

            self.logger.info(f"Created fix branch: {branch_name}")
            return branch_name

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to create fix branch: {e}")
            return None

    def _apply_fix_to_file(self, fix: FixSuggestion) -> None:
        """Apply a fix suggestion to a file."""
        try:
            with open(fix.file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Simple replacement (in production, use more sophisticated line-based replacement)
            if fix.original_code in content:
                updated_content = content.replace(fix.original_code, fix.suggested_code, 1)

                with open(fix.file_path, "w", encoding="utf-8") as f:
                    f.write(updated_content)

                self.logger.info(f"Applied fix to {fix.file_path}")
            else:
                self.logger.warning(f"Could not find original code in {fix.file_path}")

        except Exception as e:
            self.logger.error(f"Failed to apply fix to {fix.file_path}: {e}")


def format_fix_for_issue(fix: FixSuggestion) -> str:
    """Format a fix suggestion for display in GitHub issue."""
    confidence_emoji = "🟢" if fix.confidence >= 0.85 else "🟡" if fix.confidence >= 0.70 else "🟠"

    return f"""### 📝 {fix.file_path}:{fix.line_number or '?'}

**Pattern**: `{fix.pattern}`
**Confidence**: {confidence_emoji} {fix.confidence:.0%}

**Original code:**
```typescript
{fix.original_code}
```

**Suggested fix:**
```typescript
{fix.suggested_code}
```

**Reasoning**: {fix.reasoning}

---
"""


def create_fix_suggestions_section(
    fixes: List[FixSuggestion], mode: str, branch_name: Optional[str] = None
) -> str:
    """Create the fix suggestions section for GitHub issue."""
    if not fixes:
        return ""

    sections = [
        "<details>",
        "<summary>🤖 AI-Generated Fix Suggestions (Click to expand)</summary>",
        "",
    ]

    # Add mode-specific header
    if mode == "branch" and branch_name:
        sections.extend(
            [
                f"✅ **Auto-fix branch created**: `{branch_name}`",
                "",
                "**To test this fix:**",
                "```bash",
                f"git fetch origin {branch_name}",
                f"git checkout {branch_name}",
                "npx playwright test  # Run tests to verify",
                "```",
                "",
                "If the fix works, create a PR from this branch.",
                "",
                "---",
                "",
            ]
        )
    elif mode == "issue-only":
        sections.extend(
            [
                "⚠️ **Review carefully** - These are AI-generated suggestions",
                "",
                "Copy the suggested fixes below and test them locally before committing.",
                "",
                "---",
                "",
            ]
        )

    # Add each fix
    for i, fix in enumerate(fixes, 1):
        sections.append(f"## Fix {i}/{len(fixes)}")
        sections.append(format_fix_for_issue(fix))

    sections.extend(
        [
            "---",
            "",
            "💡 **Tips:**",
            "- Test each fix individually",
            "- Run the full test suite to check for regressions",
            "- Adjust the suggested code to match your coding style",
            "",
            "</details>",
        ]
    )

    return "\n".join(sections)
