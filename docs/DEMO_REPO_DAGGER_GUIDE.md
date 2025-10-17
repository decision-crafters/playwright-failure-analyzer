# Demo Repository Dagger Integration Guide

**Target Repository**: [playwright-failure-analyzer-demo](https://github.com/decision-crafters/playwright-failure-analyzer-demo)

**Purpose**: Reference implementation of Dagger-powered auto-fix for Playwright test failures

**Audience**: Developers implementing the Dagger module

**Status**: Implementation Ready ✅

---

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Architecture](#architecture)
- [Implementation Plan](#implementation-plan)
- [Phase 1: Setup](#phase-1-setup-1-2-days)
- [Phase 2: Core Dagger Module](#phase-2-core-dagger-module-3-4-days)
- [Phase 3: GitHub Integration](#phase-3-github-integration-2-3-days)
- [Phase 4: Testing & Documentation](#phase-4-testing--documentation-2-3-days)
- [Testing Locally](#testing-locally)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

---

## Overview

This guide walks you through building a Dagger module that:

1. **Reads** structured JSON from the analyzer
2. **Generates** code fixes using AI (leveraging Dagger's LLM features)
3. **Applies** fixes in isolated containers
4. **Validates** fixes by running tests
5. **Creates** PRs for successful fixes

**Expected Duration**: 8-12 days (160-240 hours with 2 developers)

---

## Prerequisites

### Required Tools

```bash
# Dagger CLI
curl -L https://dl.dagger.io/dagger/install.sh | sh

# Python 3.11+
python --version

# Node.js 18+ (for Playwright)
node --version

# Git
git --version

# GitHub CLI (optional but helpful)
gh --version
```

### Required Access

- [ ] Write access to `decision-crafters/playwright-failure-analyzer-demo`
- [ ] GitHub token with `repo` and `workflow` permissions
- [ ] OpenRouter or OpenAI API key
- [ ] Familiarity with Dagger concepts (read https://docs.dagger.io/quickstart)

### Knowledge Requirements

- Python programming (Dagger modules are Python)
- Playwright testing basics
- GitHub Actions workflows
- Git branching and PRs

---

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ GitHub Actions Workflow                                     │
│                                                              │
│  ┌──────────────────┐      ┌─────────────────────────────┐ │
│  │ 1. Run Tests     │      │ 2. Analyze Failures         │ │
│  │ (Playwright)     │─────▶│ (failure-analyzer)          │ │
│  │                  │      │                              │ │
│  │ - Execute tests  │      │ - Parse JSON report         │ │
│  │ - Generate JSON  │      │ - AI analysis               │ │
│  │                  │      │ - Create GitHub issue       │ │
│  └──────────────────┘      │ - Export structured JSON    │ │
│                             └──────────┬──────────────────┘ │
│                                        │                     │
│                                        │ failures.json       │
│                                        ▼                     │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 3. Dagger Auto-Fixer (NEW)                              ││
│  │                                                          ││
│  │  ┌────────────────┐  ┌──────────────┐  ┌─────────────┐ ││
│  │  │ Fix Generator  │  │ Container    │  │ PR Creator  │ ││
│  │  │                │  │ Runner       │  │             │ ││
│  │  │ - Read JSON    │─▶│ - Apply fix  │─▶│ - Validate  │ ││
│  │  │ - Call AI      │  │ - Run tests  │  │ - Create PR │ ││
│  │  │ - Build prompt │  │ - Isolate    │  │             │ ││
│  │  └────────────────┘  └──────────────┘  └─────────────┘ ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
playwright-failure-analyzer-demo/
├── dagger/                          # NEW: Dagger module directory
│   ├── dagger.json                  # Dagger module configuration
│   ├── pyproject.toml               # Python dependencies
│   ├── src/
│   │   ├── main.py                  # Main Dagger module entry point
│   │   ├── fix_generator.py         # AI-powered fix generation
│   │   ├── confidence_scorer.py     # Enhanced confidence calculation
│   │   ├── pattern_matcher.py       # Error pattern detection
│   │   ├── test_runner.py           # Test execution in containers
│   │   └── pr_creator.py            # GitHub PR automation
│   ├── tests/
│   │   ├── test_fix_generator.py
│   │   ├── test_confidence.py
│   │   └── test_integration.py
│   └── README.md
├── .github/
│   └── workflows/
│       ├── test-and-analyze.yml     # Existing analyzer workflow
│       └── auto-fix.yml             # NEW: Auto-fix workflow
├── docs/
│   ├── DAGGER_SETUP.md              # Setup instructions
│   ├── PATTERN_LIBRARY.md           # Supported fix patterns
│   └── AUTO_FIX_EXAMPLES.md         # Example fixes and results
└── tests/
    └── sample-fail.spec.js          # Existing intentional failures
```

---

## Implementation Plan

### Timeline Overview

| Phase | Duration | Description |
|-------|----------|-------------|
| Phase 1: Setup | 1-2 days | Initialize Dagger module, configure dependencies |
| Phase 2: Core Module | 3-4 days | Build fix generation and testing logic |
| Phase 3: GitHub Integration | 2-3 days | PR creation, branch management |
| Phase 4: Testing & Docs | 2-3 days | Comprehensive testing, documentation |

**Total**: 8-12 days with 2 developers working in parallel

---

## Phase 1: Setup (1-2 days)

### Task 1.1: Initialize Dagger Module

**Assignee**: Dev 1
**Duration**: 2-4 hours

```bash
cd playwright-failure-analyzer-demo

# Initialize Dagger module
mkdir -p dagger/src
cd dagger
dagger init --sdk=python
```

**Expected Output**:
```
dagger/
├── dagger.json
├── pyproject.toml
└── src/
    └── main.py
```

**Deliverable**: Basic Dagger module structure

**Acceptance Criteria**:
- [ ] `dagger.json` exists with correct configuration
- [ ] `pyproject.toml` has Python SDK dependency
- [ ] Can run `dagger call --help` successfully

---

### Task 1.2: Configure Dependencies

**Assignee**: Dev 1
**Duration**: 2-3 hours

Edit `dagger/pyproject.toml`:

```toml
[project]
name = "playwright-auto-fixer"
version = "0.1.0"
description = "Dagger module for auto-fixing Playwright test failures"
requires-python = ">=3.11"

dependencies = [
    "dagger-io>=0.9.0",
    "litellm>=1.0.0",
    "requests>=2.31.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]
```

**Deliverable**: Configured Python environment

**Acceptance Criteria**:
- [ ] Dependencies install without errors
- [ ] Can import dagger and litellm in Python
- [ ] Tests run with pytest

---

### Task 1.3: Create Module Skeleton

**Assignee**: Dev 2
**Duration**: 3-4 hours

Create `dagger/src/main.py`:

```python
"""Playwright Auto-Fixer Dagger Module."""

import dagger
from dagger import dag, function, object_type
import json


@object_type
class PlaywrightAutoFixer:
    """Auto-fix Playwright test failures using AI and isolated containers."""

    @function
    async def hello(self) -> str:
        """Test function to verify module works."""
        return "Playwright Auto-Fixer v0.1.0"

    @function
    async def attempt_fix(
        self,
        repo_dir: dagger.Directory,
        failures_json_path: str,
        ai_model: str = "gpt-4o-mini",
        min_confidence: float = 0.75,
    ) -> str:
        """
        Attempt to fix test failures automatically.

        Args:
            repo_dir: Repository directory
            failures_json_path: Path to structured failures JSON
            ai_model: AI model to use for fix generation
            min_confidence: Minimum confidence threshold (0.0-1.0)

        Returns:
            JSON string with fix results
        """
        # TODO: Implement in Phase 2
        return json.dumps({
            "status": "not_implemented",
            "message": "Fix generation coming in Phase 2"
        })
```

**Test it**:

```bash
cd dagger
dagger call hello
# Expected: "Playwright Auto-Fixer v0.1.0"
```

**Deliverable**: Working Dagger module skeleton

**Acceptance Criteria**:
- [ ] `dagger call hello` returns success message
- [ ] `dagger call attempt-fix` can be invoked (returns placeholder)
- [ ] Module structure follows Dagger best practices

---

## Phase 2: Core Dagger Module (3-4 days)

### Task 2.1: Implement Fix Generator

**Assignee**: Dev 1
**Duration**: 8-10 hours

Create `dagger/src/fix_generator.py`:

```python
"""AI-powered fix code generation."""

import dagger
from dagger import dag
import json
from typing import Dict, Any, List, Optional
import litellm


class FixGenerator:
    """Generates code fixes using AI."""

    # Pattern-specific prompts (from AUTOFIX_PROMPT_TEMPLATES.md)
    PROMPTS = {
        "missing_await": """Fix missing await in Playwright test.

Current code at {file_path}:{line_number}:
{error_context}

Error: {error_message}

Return ONLY valid JSON:
{{
  "fixed_code": "await page.goto(url)",
  "explanation": "Added missing await keyword",
  "confidence": 0.95
}}""",

        "selector_timeout": """Fix selector timeout in Playwright test.

Current code at {file_path}:{line_number}:
{error_context}

Error: {error_message}

Return ONLY valid JSON with the fix.""",

        # Add more patterns from AUTOFIX_PROMPT_TEMPLATES.md
    }

    def __init__(self, model: str = "gpt-4o-mini"):
        """Initialize fix generator with AI model."""
        self.model = model

    async def generate_fix(
        self,
        failure: Dict[str, Any],
        file_content: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a fix for a single failure.

        Args:
            failure: Failure data from structured JSON
            file_content: Full file content for context

        Returns:
            Fix dict with fixed_code, explanation, confidence
        """
        pattern = failure.get("suggested_pattern", "unknown")
        prompt_template = self.PROMPTS.get(pattern, self.PROMPTS["selector_timeout"])

        # Extract code context around the failure line
        error_context = self._extract_context(
            file_content,
            failure.get("line_number")
        )

        # Build prompt
        prompt = prompt_template.format(
            file_path=failure["file_path"],
            line_number=failure.get("line_number", "unknown"),
            error_message=failure["error_message"],
            error_context=error_context,
        )

        # Call AI via LiteLLM
        try:
            response = litellm.completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a Playwright test fixing expert. Return ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=500,
                timeout=20,
            )

            # Parse response
            fix_data = self._parse_response(response.choices[0].message.content)
            return fix_data

        except Exception as e:
            print(f"Error generating fix: {e}")
            return None

    def _extract_context(self, file_content: str, line_number: Optional[int]) -> str:
        """Extract 5 lines of context around the error line."""
        if not line_number:
            return file_content[:500]  # Return first 500 chars

        lines = file_content.split('\n')
        start = max(0, line_number - 3)
        end = min(len(lines), line_number + 2)

        context_lines = []
        for i in range(start, end):
            prefix = ">>> " if i == line_number - 1 else "    "
            context_lines.append(f"{prefix}{i+1}: {lines[i]}")

        return '\n'.join(context_lines)

    def _parse_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse AI response JSON."""
        try:
            # Remove markdown code blocks
            text = response_text.strip()
            if "```json" in text:
                start = text.find("```json") + 7
                end = text.find("```", start)
                text = text[start:end].strip()
            elif "```" in text:
                start = text.find("```") + 3
                end = text.find("```", start)
                text = text[start:end].strip()

            # Find JSON object
            if "{" in text:
                start = text.find("{")
                end = text.rfind("}") + 1
                text = text[start:end]

            return json.loads(text)

        except json.JSONDecodeError:
            return None
```

**Deliverable**: Working fix generator

**Acceptance Criteria**:
- [ ] Generates fixes for at least 3 error patterns
- [ ] Parses AI responses correctly
- [ ] Extracts proper code context
- [ ] Returns structured fix data

---

### Task 2.2: Implement Test Runner

**Assignee**: Dev 2
**Duration**: 8-10 hours

Create `dagger/src/test_runner.py`:

```python
"""Test execution in isolated Dagger containers."""

import dagger
from dagger import dag
from typing import Dict, Any


class TestRunner:
    """Runs Playwright tests in isolated containers."""

    async def run_test(
        self,
        repo_dir: dagger.Directory,
        test_file: str,
        fixed_code: str = None,
    ) -> Dict[str, Any]:
        """
        Run a specific test file in a Playwright container.

        Args:
            repo_dir: Repository directory
            test_file: Path to test file
            fixed_code: Optional fixed code to apply before running

        Returns:
            Test results dict with passed, duration, output
        """
        # Create Playwright container
        container = (
            dag.container()
            .from_("mcr.microsoft.com/playwright:v1.40.0-jammy")
            .with_directory("/app", repo_dir)
            .with_workdir("/app")
            .with_exec(["npm", "ci"])
        )

        # Apply fix if provided
        if fixed_code:
            container = container.with_new_file(
                f"/app/{test_file}",
                contents=fixed_code
            )

        # Run the test
        try:
            output = await (
                container
                .with_exec([
                    "npx", "playwright", "test",
                    test_file,
                    "--reporter=json"
                ])
                .stdout()
            )

            # Parse Playwright JSON output
            result = self._parse_test_output(output)
            return {
                "passed": result.get("stats", {}).get("unexpected", 0) == 0,
                "duration_ms": result.get("stats", {}).get("duration", 0),
                "output": output[:1000],  # Truncate
                "total_tests": result.get("stats", {}).get("expected", 0),
            }

        except Exception as e:
            return {
                "passed": False,
                "duration_ms": 0,
                "output": str(e),
                "error": str(e),
            }

    def _parse_test_output(self, output: str) -> Dict[str, Any]:
        """Parse Playwright JSON reporter output."""
        try:
            import json
            return json.loads(output)
        except:
            return {"stats": {}}
```

**Deliverable**: Working test runner

**Acceptance Criteria**:
- [ ] Runs tests in Playwright container
- [ ] Can apply fixes before running
- [ ] Parses test results correctly
- [ ] Returns structured test data

---

### Task 2.3: Implement Confidence Scorer

**Assignee**: Dev 1
**Duration**: 6-8 hours

Create `dagger/src/confidence_scorer.py`:

```python
"""Enhanced confidence scoring for auto-fix decisions."""

from typing import Dict, Any


class ConfidenceScorer:
    """Calculates confidence scores for fixes."""

    # Model-based multipliers (from analyzer)
    MODEL_MULTIPLIERS = {
        'gpt-4o': 1.0,
        'gpt-4o-mini': 0.85,
        'claude-3.5-sonnet': 1.0,
        'deepseek-chat': 0.70,
        'deepseek-coder': 0.75,
    }

    def calculate_confidence(
        self,
        ai_confidence: float,
        test_passed: bool,
        pattern: str,
        model: str,
        fix_complexity: int = 1,
    ) -> Dict[str, Any]:
        """
        Calculate overall confidence score.

        Args:
            ai_confidence: AI's raw confidence (0.0-1.0)
            test_passed: Whether test passed after fix
            pattern: Error pattern detected
            model: AI model used
            fix_complexity: Number of lines changed

        Returns:
            Dict with confidence score and recommendation
        """
        # Get model multiplier
        model_key = self._normalize_model_name(model)
        model_multiplier = self.MODEL_MULTIPLIERS.get(model_key, 0.60)

        # Apply model multiplier to AI confidence
        adjusted_confidence = ai_confidence * model_multiplier

        # Boost if test passed
        if test_passed:
            adjusted_confidence = min(adjusted_confidence + 0.15, 1.0)

        # Pattern-based boost
        pattern_boost = self._get_pattern_boost(pattern)
        adjusted_confidence = min(adjusted_confidence + pattern_boost, 1.0)

        # Penalize complex fixes
        if fix_complexity > 5:
            adjusted_confidence *= 0.85
        elif fix_complexity > 10:
            adjusted_confidence *= 0.70

        # Determine action
        recommendation = self._get_recommendation(adjusted_confidence)

        return {
            "confidence": adjusted_confidence,
            "raw_confidence": ai_confidence,
            "model_multiplier": model_multiplier,
            "test_boost": 0.15 if test_passed else 0.0,
            "pattern_boost": pattern_boost,
            "recommendation": recommendation,
        }

    def _normalize_model_name(self, model: str) -> str:
        """Normalize model name for lookup."""
        model_lower = model.lower()
        for key in self.MODEL_MULTIPLIERS.keys():
            if key in model_lower:
                return key
        return "unknown"

    def _get_pattern_boost(self, pattern: str) -> float:
        """Get confidence boost based on error pattern."""
        pattern_boosts = {
            "missing_await": 0.10,
            "selector_timeout": 0.05,
            "navigation_timeout": 0.05,
            "type_mismatch": 0.08,
            "module_not_found": 0.10,
        }
        return pattern_boosts.get(pattern, 0.0)

    def _get_recommendation(self, confidence: float) -> str:
        """Get action recommendation based on confidence."""
        if confidence >= 0.90:
            return "CREATE_PR"
        elif confidence >= 0.75:
            return "CREATE_DRAFT_PR"
        elif confidence >= 0.50:
            return "COMMENT_ONLY"
        else:
            return "SKIP"
```

**Deliverable**: Working confidence scorer

**Acceptance Criteria**:
- [ ] Applies model-based multipliers correctly
- [ ] Boosts confidence when tests pass
- [ ] Provides clear recommendations
- [ ] Handles edge cases (unknown models, patterns)

---

### Task 2.4: Integrate Components in Main Module

**Assignee**: Dev 2
**Duration**: 6-8 hours

Update `dagger/src/main.py`:

```python
"""Playwright Auto-Fixer Dagger Module - Main Integration."""

import dagger
from dagger import dag, function, object_type
import json
from typing import Optional

from .fix_generator import FixGenerator
from .test_runner import TestRunner
from .confidence_scorer import ConfidenceScorer


@object_type
class PlaywrightAutoFixer:
    """Auto-fix Playwright test failures using AI and isolated containers."""

    @function
    async def attempt_fix(
        self,
        repo_dir: dagger.Directory,
        failures_json_path: str,
        ai_model: str = "gpt-4o-mini",
        min_confidence: float = 0.75,
    ) -> str:
        """
        Attempt to fix test failures automatically.

        Args:
            repo_dir: Repository directory
            failures_json_path: Path to structured failures JSON
            ai_model: AI model to use for fix generation
            min_confidence: Minimum confidence threshold (0.0-1.0)

        Returns:
            JSON string with fix results
        """
        # Read failures JSON
        failures_data = await self._read_failures(repo_dir, failures_json_path)

        if not failures_data or not failures_data.get("failures"):
            return json.dumps({"status": "no_failures", "fixes": []})

        # Initialize components
        fix_generator = FixGenerator(model=ai_model)
        test_runner = TestRunner()
        confidence_scorer = ConfidenceScorer()

        results = []

        # Process each failure
        for failure in failures_data["failures"][:5]:  # Limit to 5
            try:
                # Read file content
                file_content = await self._read_file(repo_dir, failure["file_path"])

                # Generate fix
                fix_data = await fix_generator.generate_fix(failure, file_content)

                if not fix_data:
                    continue

                # Apply fix and run test
                test_result = await test_runner.run_test(
                    repo_dir,
                    failure["file_path"],
                    fix_data["fixed_code"]
                )

                # Calculate confidence
                confidence_result = confidence_scorer.calculate_confidence(
                    ai_confidence=fix_data.get("confidence", 0.7),
                    test_passed=test_result["passed"],
                    pattern=failure.get("suggested_pattern", "unknown"),
                    model=ai_model,
                    fix_complexity=len(fix_data["fixed_code"].split('\n'))
                )

                # Store result if confidence meets threshold
                if confidence_result["confidence"] >= min_confidence:
                    results.append({
                        "file": failure["file_path"],
                        "pattern": failure.get("suggested_pattern"),
                        "fix": fix_data["fixed_code"],
                        "explanation": fix_data.get("explanation"),
                        "confidence": confidence_result["confidence"],
                        "recommendation": confidence_result["recommendation"],
                        "test_passed": test_result["passed"],
                    })

            except Exception as e:
                print(f"Error processing {failure.get('file_path')}: {e}")
                continue

        return json.dumps({
            "status": "completed",
            "total_failures": len(failures_data["failures"]),
            "fixes_generated": len(results),
            "fixes": results
        }, indent=2)

    async def _read_failures(
        self,
        repo_dir: dagger.Directory,
        path: str
    ) -> Optional[dict]:
        """Read and parse failures JSON."""
        try:
            content = await repo_dir.file(path).contents()
            return json.loads(content)
        except Exception as e:
            print(f"Error reading failures: {e}")
            return None

    async def _read_file(
        self,
        repo_dir: dagger.Directory,
        path: str
    ) -> str:
        """Read a file from the repository."""
        try:
            return await repo_dir.file(path).contents()
        except Exception as e:
            print(f"Error reading file {path}: {e}")
            return ""
```

**Test it**:

```bash
cd dagger

# Test with sample data
dagger call attempt-fix \
  --repo-dir=.. \
  --failures-json-path=test-data/sample-failures.json \
  --ai-model=gpt-4o-mini \
  --min-confidence=0.75
```

**Deliverable**: Integrated Dagger module

**Acceptance Criteria**:
- [ ] Reads failures JSON successfully
- [ ] Generates fixes for multiple patterns
- [ ] Runs tests in containers
- [ ] Calculates confidence scores
- [ ] Returns structured results
- [ ] Handles errors gracefully

---

## Phase 3: GitHub Integration (2-3 days)

### Task 3.1: Implement PR Creator

**Assignee**: Dev 1
**Duration**: 8-10 hours

Create `dagger/src/pr_creator.py`:

```python
"""GitHub PR creation for auto-fixes."""

import os
import subprocess
from typing import List, Dict, Any


class PRCreator:
    """Creates GitHub PRs with auto-fixes."""

    def __init__(self, token: str, repository: str):
        """Initialize PR creator."""
        self.token = token
        self.repository = repository

    def create_pr(
        self,
        fixes: List[Dict[str, Any]],
        issue_number: int,
        branch_name: str,
        confidence: float,
    ) -> Dict[str, Any]:
        """
        Create a PR with fixes.

        Args:
            fixes: List of fix dicts
            issue_number: Related issue number
            branch_name: Branch name for PR
            confidence: Overall confidence score

        Returns:
            PR details dict
        """
        # Create PR title and body
        title = f"🤖 Auto-fix: Resolve test failures (Issue #{issue_number})"

        body = self._format_pr_body(fixes, issue_number, confidence)

        # Create PR using gh CLI
        try:
            result = subprocess.run(
                [
                    "gh", "pr", "create",
                    "--title", title,
                    "--body", body,
                    "--head", branch_name,
                    "--base", "main",
                    "--label", "automated-fix",
                    "--label", "needs-review",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            pr_url = result.stdout.strip()

            return {
                "success": True,
                "pr_url": pr_url,
                "branch": branch_name,
            }

        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": e.stderr,
            }

    def _format_pr_body(
        self,
        fixes: List[Dict[str, Any]],
        issue_number: int,
        confidence: float,
    ) -> str:
        """Format PR description."""
        lines = [
            f"# 🤖 Automated Fix",
            "",
            f"Fixes #{issue_number}",
            "",
            "## Summary",
            "",
            f"This PR contains {len(fixes)} automated fix(es) for test failures.",
            "",
            f"**Overall Confidence**: {confidence:.0%}",
            "",
            "## Changes Made",
            "",
        ]

        for i, fix in enumerate(fixes, 1):
            lines.extend([
                f"### {i}. {fix['file']}",
                "",
                f"**Pattern**: `{fix['pattern']}`",
                f"**Confidence**: {fix['confidence']:.0%}",
                f"**Test Passed**: {'✅ Yes' if fix.get('test_passed') else '❌ No'}",
                "",
                "**Fix Applied**:",
                "```typescript",
                fix['fix'][:500],  # Truncate if too long
                "```",
                "",
                f"**Explanation**: {fix.get('explanation', 'N/A')}",
                "",
                "---",
                "",
            ])

        lines.extend([
            "## Testing",
            "",
            "- [x] Fixes generated by AI",
            "- [x] Tests run in isolated containers",
            "- [ ] Manual review required",
            "- [ ] Full test suite verification needed",
            "",
            "## ⚠️ Important",
            "",
            "This is an **automated fix** generated by AI. Please:",
            "",
            "1. Review the changes carefully",
            "2. Run the full test suite locally",
            "3. Verify no regressions were introduced",
            "4. Test edge cases not covered by automated tests",
            "",
            f"💬 Questions? Comment on issue #{issue_number}",
        ])

        return "\n".join(lines)
```

**Deliverable**: Working PR creator

**Acceptance Criteria**:
- [ ] Creates PRs with proper formatting
- [ ] Links to original issue
- [ ] Includes all fix details
- [ ] Adds appropriate labels
- [ ] Handles errors gracefully

---

### Task 3.2: Add PR Creation to Main Module

**Assignee**: Dev 2
**Duration**: 4-6 hours

Update `dagger/src/main.py` to add PR creation:

```python
@function
async def fix_and_create_pr(
    self,
    repo_dir: dagger.Directory,
    failures_json_path: str,
    issue_number: int,
    github_token: dagger.Secret,
    ai_model: str = "gpt-4o-mini",
    min_confidence: float = 0.75,
) -> str:
    """
    Attempt fixes and create PR if successful.

    Args:
        repo_dir: Repository directory
        failures_json_path: Path to failures JSON
        issue_number: GitHub issue number
        github_token: GitHub token (secret)
        ai_model: AI model to use
        min_confidence: Minimum confidence threshold

    Returns:
        JSON with PR details
    """
    from .pr_creator import PRCreator

    # Generate fixes (reuse attempt_fix logic)
    results_json = await self.attempt_fix(
        repo_dir, failures_json_path, ai_model, min_confidence
    )

    results = json.loads(results_json)

    if results["status"] != "completed" or not results["fixes"]:
        return json.dumps({"status": "no_fixes_generated"})

    # Get GitHub token value
    token_value = await github_token.plaintext()

    # Create PR
    pr_creator = PRCreator(
        token=token_value,
        repository=os.getenv("GITHUB_REPOSITORY", "owner/repo")
    )

    # Calculate overall confidence
    overall_confidence = sum(f["confidence"] for f in results["fixes"]) / len(results["fixes"])

    # Create branch name
    pattern = results["fixes"][0].get("pattern", "unknown")
    branch_name = f"autofix/issue-{issue_number}-{pattern}"

    # Create PR
    pr_result = pr_creator.create_pr(
        fixes=results["fixes"],
        issue_number=issue_number,
        branch_name=branch_name,
        confidence=overall_confidence,
    )

    return json.dumps({
        "status": "completed",
        "pr_created": pr_result.get("success", False),
        "pr_url": pr_result.get("pr_url"),
        "fixes_applied": len(results["fixes"]),
    }, indent=2)
```

**Deliverable**: Complete PR automation

**Acceptance Criteria**:
- [ ] Creates branch with fixes
- [ ] Commits changes
- [ ] Creates PR with all details
- [ ] Links issue and PR
- [ ] Returns success/failure status

---

## Phase 4: Testing & Documentation (2-3 days)

### Task 4.1: Write Integration Tests

**Assignee**: Dev 1 & Dev 2 (pair programming)
**Duration**: 8-10 hours

Create `dagger/tests/test_integration.py`:

```python
"""Integration tests for Dagger auto-fixer."""

import pytest
import json


@pytest.mark.asyncio
async def test_fix_generation():
    """Test that fixes are generated for sample failures."""
    # Load sample failures
    with open("test-data/sample-failures.json") as f:
        failures = json.load(f)

    # Test fix generation (mock AI calls)
    # ... test implementation


@pytest.mark.asyncio
async def test_test_execution():
    """Test that tests run in containers."""
    # ... test implementation


@pytest.mark.asyncio
async def test_confidence_calculation():
    """Test confidence scoring."""
    from src.confidence_scorer import ConfidenceScorer

    scorer = ConfidenceScorer()

    # Test premium model
    result = scorer.calculate_confidence(
        ai_confidence=0.80,
        test_passed=True,
        pattern="missing_await",
        model="gpt-4o",
        fix_complexity=1,
    )

    assert result["confidence"] >= 0.90  # Should boost to 90%+
    assert result["recommendation"] == "CREATE_PR"


# Add more tests...
```

**Deliverable**: Comprehensive test suite

**Acceptance Criteria**:
- [ ] 80%+ code coverage
- [ ] Tests pass locally
- [ ] Tests pass in CI
- [ ] Integration tests verify end-to-end flow

---

### Task 4.2: Write Documentation

**Assignee**: Dev 2
**Duration**: 6-8 hours

Create documentation files:

1. **`dagger/README.md`** - Module overview and quick start
2. **`docs/DAGGER_SETUP.md`** - Detailed setup instructions
3. **`docs/PATTERN_LIBRARY.md`** - Supported patterns and examples
4. **`docs/AUTO_FIX_EXAMPLES.md`** - Real examples from demo repo

**Deliverable**: Complete documentation

**Acceptance Criteria**:
- [ ] README explains purpose and usage
- [ ] Setup guide is step-by-step
- [ ] Pattern library has examples
- [ ] Documentation is clear and accurate

---

### Task 4.3: Create GitHub Workflow

**Assignee**: Dev 1
**Duration**: 4-6 hours

Create `.github/workflows/auto-fix.yml`:

```yaml
name: Auto-Fix Test Failures

on:
  issues:
    types: [opened, labeled]

jobs:
  attempt-auto-fix:
    if: contains(github.event.issue.labels.*.name, 'auto-fix-ready')
    runs-on: ubuntu-latest

    permissions:
      contents: write
      issues: write
      pull-requests: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Download failures JSON
        run: |
          # Extract JSON from issue or download from artifact
          # This depends on how analyzer stores the JSON

      - name: Run Dagger auto-fix
        uses: dagger/dagger-for-github@v6
        with:
          version: "latest"
          verb: call
          module: ./dagger
          args: |
            fix-and-create-pr \
              --repo-dir=. \
              --failures-json-path=failures.json \
              --issue-number=${{ github.event.issue.number }} \
              --github-token=env:GITHUB_TOKEN \
              --ai-model=${{ vars.AI_MODEL || 'gpt-4o-mini' }} \
              --min-confidence=0.75
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
```

**Deliverable**: Working GitHub Actions workflow

**Acceptance Criteria**:
- [ ] Triggers on `auto-fix-ready` label
- [ ] Runs Dagger module successfully
- [ ] Creates PR when fixes succeed
- [ ] Handles errors gracefully

---

## Testing Locally

### Setup Test Environment

```bash
# 1. Clone demo repo
git clone https://github.com/decision-crafters/playwright-failure-analyzer-demo.git
cd playwright-failure-analyzer-demo

# 2. Install dependencies
npm install
cd dagger
pip install -e .

# 3. Set environment variables
export OPENROUTER_API_KEY="sk-or-v1-..."  # pragma: allowlist secret
export GITHUB_TOKEN="ghp_..."  # pragma: allowlist secret
export GITHUB_REPOSITORY="decision-crafters/playwright-failure-analyzer-demo"
```

### Run Dagger Module Locally

```bash
# Test basic functionality
dagger call hello

# Test with sample data
dagger call attempt-fix \
  --repo-dir=.. \
  --failures-json-path=test-data/sample-failures.json \
  --ai-model=gpt-4o-mini \
  --min-confidence=0.70

# Test PR creation (dry-run)
dagger call fix-and-create-pr \
  --repo-dir=.. \
  --failures-json-path=test-data/sample-failures.json \
  --issue-number=1 \
  --github-token=env:GITHUB_TOKEN \
  --ai-model=gpt-4o-mini
```

### Validate Results

```bash
# Check generated fixes
cat output.json | jq '.fixes'

# Verify tests pass with fixes
cd ..
git checkout autofix/issue-1-selector-timeout
npm test
```

---

## Deployment

### Pre-Deployment Checklist

- [ ] All tests pass
- [ ] Documentation complete
- [ ] GitHub workflow tested
- [ ] Secrets configured in repo
- [ ] Team trained on usage

### Deploy to Demo Repo

```bash
# 1. Create PR with Dagger module
git checkout -b feature/dagger-auto-fix
git add dagger/ .github/workflows/auto-fix.yml docs/
git commit -m "feat: Add Dagger auto-fix module"
git push origin feature/dagger-auto-fix

# 2. Create PR and get review

# 3. Merge to main

# 4. Test with intentional failure
# Trigger a test failure and verify auto-fix workflow runs
```

---

## Troubleshooting

### Issue: Dagger module not found

**Solution**:
```bash
cd dagger
dagger init --sdk=python
```

### Issue: AI API calls failing

**Solution**:
```bash
# Verify API key is set
echo $OPENROUTER_API_KEY

# Test with curl
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

### Issue: Tests not running in container

**Solution**:
```bash
# Verify Playwright image
docker pull mcr.microsoft.com/playwright:v1.40.0-jammy

# Test manually
docker run -it mcr.microsoft.com/playwright:v1.40.0-jammy npx playwright --version
```

---

## Success Metrics

Track these to measure success:

- **Fix Success Rate**: % of auto-fixes that work
- **Time Saved**: Hours saved per week
- **Pattern Coverage**: # of patterns supported
- **Confidence Accuracy**: Correlation between confidence and success
- **Developer Satisfaction**: Survey results

---

## Next Steps After Implementation

1. **Monitor**: Watch success rates for 2-4 weeks
2. **Iterate**: Add more patterns based on failures
3. **Optimize**: Improve confidence scoring
4. **Scale**: Handle more failures concurrently
5. **Share**: Write blog post, share learnings

---

## Resources

- [Dagger Documentation](https://docs.dagger.io)
- [Dagger LLM Features](https://docs.dagger.io/features/llm)
- [Playwright Failure Analyzer](https://github.com/decision-crafters/playwright-failure-analyzer)
- [Auto-Fix Prompt Templates](./AUTOFIX_PROMPT_TEMPLATES.md)
- [Integration Guide](./AUTOFIX_INTEGRATION_GUIDE.md)

---

**Questions?**
- Open issue in [playwright-failure-analyzer](https://github.com/decision-crafters/playwright-failure-analyzer/issues)
- Tag `@tosinakinosho` for clarifications

**Ready to build?** Start with [Phase 1: Setup](#phase-1-setup-1-2-days)! 🚀
