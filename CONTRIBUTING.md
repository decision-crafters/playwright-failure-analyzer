# Contributing to Playwright Failure Bundler

Thank you for your interest in contributing to the Playwright Failure Bundler! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Release Process](#release-process)

## Code of Conduct

This project adheres to a code of conduct that we expect all contributors to follow. Please be respectful and constructive in all interactions.

### Our Standards

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- GitHub account
- Basic understanding of GitHub Actions

### Development Tools

We recommend using one of these development environments:
- **Windsurf** (preferred)
- **Cursor**
- VS Code with Python extension
- PyCharm

## Development Setup

1. **Fork the repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/playwright-failure-bundler.git
   cd playwright-failure-bundler
   ```

2. **Set up Python environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

3. **Install development tools**
   ```bash
   pip install flake8 mypy pytest pytest-cov black isort
   ```

4. **Install pre-commit hooks** (Security required!)
   ```bash
   # Automated installation (recommended - choose your platform)
   ./scripts/setup-precommit.sh           # Linux/macOS
   scripts\setup-precommit.bat            # Windows
   python scripts/setup-precommit.py      # Any platform

   # OR manual installation
   pip install pre-commit
   pre-commit install
   pre-commit install --hook-type commit-msg
   ```

5. **Verify setup**
   ```bash
   # Test code
   python tests/run_tests.py

   # Test pre-commit hooks
   pre-commit run --all-files
   ```

### Pre-commit Hooks (Required)

This project uses pre-commit hooks to ensure code quality and security **before** code reaches the repository. All contributors must install and use these hooks.

**Security hooks (will block commits):**
- 🔐 **detect-secrets** - Prevents API keys, passwords, tokens
- 🕵️ **gitleaks** - Scans for 100+ secret patterns
- ✅ **check-github-workflows** - Validates GitHub Actions
- 🛡️ **bandit** - Python security linting

**Code quality hooks:**
- 🎨 **black** - Auto-formats code
- 📦 **isort** - Auto-sorts imports
- 🔍 **flake8** - Linting
- 🔎 **mypy** - Type checking

**Quick Reference:**
```bash
# See all available commands
cat .pre-commit-quick-reference.md

# Run hooks manually
pre-commit run --all-files

# Skip hooks (emergency only, not recommended)
git commit --no-verify -m "emergency fix"
```

**Important:** Never skip security hooks (`detect-secrets`, `gitleaks`, `bandit`) without team approval.

📖 **Full documentation:** See [Pre-commit Setup Guide](docs/PRE_COMMIT_SETUP.md)

## Making Changes

### Branch Naming

Use descriptive branch names:
- `feature/add-ai-analysis` - New features
- `fix/handle-empty-reports` - Bug fixes
- `docs/update-configuration-guide` - Documentation updates
- `refactor/improve-error-handling` - Code refactoring

### Code Style

We follow PEP 8 with some modifications:

- **Line length**: 100 characters (not 79)
- **String quotes**: Use double quotes for strings, single quotes for string literals in code
- **Imports**: Use absolute imports, group by standard library, third-party, local

#### Formatting Tools

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Check style
flake8 src/ tests/
```

### Code Structure

```
src/
├── parse_report.py      # Playwright report parsing
├── create_issue.py      # GitHub API integration
├── error_handling.py    # Error handling and validation
└── utils.py            # Utility functions

tests/
├── test_parse_report.py    # Unit tests for report parsing
├── test_create_issue.py    # Unit tests for issue creation
├── test_utils.py          # Unit tests for utilities
├── test_integration.py    # Integration tests
└── run_tests.py          # Test runner
```

### Adding New Features

1. **Create an issue** describing the feature
2. **Write tests first** (TDD approach)
3. **Implement the feature**
4. **Update documentation**
5. **Add examples** if applicable

### Bug Fixes

1. **Create a test** that reproduces the bug
2. **Fix the bug**
3. **Verify the test passes**
4. **Update documentation** if needed

## Testing

### Running Tests

```bash
# Run all tests
python tests/run_tests.py

# Run specific test file
python -m pytest tests/test_parse_report.py -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html
```

### Test Categories

1. **Unit Tests**: Test individual functions and classes
2. **Integration Tests**: Test component interactions
3. **End-to-End Tests**: Test complete workflows

### Writing Tests

- Use descriptive test names: `test_parse_report_with_multiple_failures`
- Include both positive and negative test cases
- Test edge cases and error conditions
- Use mocks for external dependencies (GitHub API, file system)

#### Example Test

```python
def test_parse_report_with_max_failures_limit(self):
    """Test that max_failures parameter limits returned failures."""
    # Arrange
    report_data = self.create_report_with_failures(5)
    parser = PlaywrightReportParser(report_data, self.error_handler)
    
    # Act
    summary = parser.parse_failures(max_failures=3)
    
    # Assert
    self.assertEqual(len(summary.failures), 3)
    self.assertEqual(summary.failed_tests, 5)  # Still reports total
```

### Test Data

- Use realistic test data that matches actual Playwright reports
- Create helper methods for generating test data
- Store complex test data in separate JSON files if needed

## Submitting Changes

### Pull Request Process

1. **Update your fork**
   ```bash
   git checkout main
   git pull upstream main
   git push origin main
   ```

2. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make changes and commit**
   ```bash
   git add .
   git commit -m "Add feature: description of changes"
   ```

4. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create pull request** on GitHub

### Pull Request Guidelines

#### Title Format
- Use imperative mood: "Add AI analysis feature"
- Keep under 50 characters
- Reference issue number: "Fix #123: Handle empty reports"

#### Description Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests pass locally
```

### Commit Messages

Follow conventional commit format:

```
type(scope): description

body (optional)

footer (optional)
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Maintenance tasks

**Examples:**
```
feat(parser): add support for nested test suites
fix(api): handle rate limiting with exponential backoff
docs(readme): update installation instructions
```

## Release Process

### Versioning

We use [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

1. **Update version** in relevant files
2. **Update CHANGELOG.md** with new features and fixes
3. **Run full test suite**
4. **Create release PR**
5. **Tag release** after merge
6. **Publish to GitHub Marketplace**

### Creating a Release

```bash
# Create release branch
git checkout -b release/v1.2.0

# Update version and changelog
# ... make changes ...

# Commit and push
git commit -m "chore: prepare release v1.2.0"
git push origin release/v1.2.0

# Create PR and merge

# Tag release
git tag v1.2.0
git push origin v1.2.0
```

## Documentation

### Types of Documentation

1. **README.md**: Overview and quick start
2. **CONFIGURATION.md**: Detailed configuration guide
3. **API.md**: API reference (if applicable)
4. **Examples/**: Usage examples
5. **Inline comments**: Code documentation

### Documentation Standards

- Use clear, concise language
- Include code examples
- Keep examples up to date
- Use proper Markdown formatting
- Include table of contents for long documents

### Updating Documentation

- Update documentation with code changes
- Add examples for new features
- Keep configuration guide current
- Update README for major changes

## Getting Help

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and general discussion
- **Pull Request Comments**: Code review and feedback

### Asking Questions

When asking for help:
1. **Search existing issues** first
2. **Provide context**: What are you trying to do?
3. **Include details**: Error messages, configuration, environment
4. **Share code**: Minimal reproducible example

### Reporting Bugs

Use the bug report template:
1. **Description**: What happened vs. what was expected
2. **Steps to reproduce**: Minimal steps to trigger the bug
3. **Environment**: OS, Python version, dependencies
4. **Logs**: Error messages and stack traces

## Recognition

Contributors will be recognized in:
- **CONTRIBUTORS.md**: List of all contributors
- **Release notes**: Major contributions highlighted
- **GitHub**: Contributor badges and statistics

Thank you for contributing to make Playwright testing better for everyone! 🎉
