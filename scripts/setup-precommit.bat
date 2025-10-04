@echo off
REM Pre-commit Hooks Setup Script for Windows
REM Playwright Failure Analyzer
REM
REM This script installs and configures pre-commit hooks with security-first approach
REM Author: Tosin Akinosho
REM Usage: scripts\setup-precommit.bat

setlocal enabledelayedexpansion

echo.
echo ================================================================
echo   Pre-commit Hooks Setup - Security First
echo   Playwright Failure Analyzer
echo ================================================================
echo.

REM Check if Python is installed
echo [1/8] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [X] Python is not installed!
    echo Please install Python 3.9 or higher from https://www.python.org/
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION% detected
echo.

REM Check if in git repository
echo [2/8] Checking Git repository...
git rev-parse --git-dir >nul 2>&1
if errorlevel 1 (
    echo [X] Not a git repository!
    echo Please run this script from the root of the repository.
    pause
    exit /b 1
)
echo [OK] Git repository detected
echo.

REM Install pre-commit
echo [3/8] Installing pre-commit...
python -m pip install --user pre-commit
if errorlevel 1 (
    echo [X] Failed to install pre-commit
    pause
    exit /b 1
)
echo [OK] pre-commit installed
echo.

REM Install Python development tools
echo [4/8] Installing Python development tools...
echo Installing black, isort, flake8, mypy, bandit, detect-secrets...
python -m pip install --user black isort flake8 mypy bandit detect-secrets
if errorlevel 1 (
    echo [X] Failed to install Python tools
    pause
    exit /b 1
)
echo [OK] All Python tools installed
echo.

REM Install git hooks
echo [5/8] Installing git hooks...
pre-commit install
if errorlevel 1 (
    echo [X] Failed to install pre-commit hook
    pause
    exit /b 1
)
pre-commit install --hook-type commit-msg
if errorlevel 1 (
    echo [X] Failed to install commit-msg hook
    pause
    exit /b 1
)
echo [OK] Git hooks installed
echo.

REM Initialize secrets baseline
echo [6/8] Initializing secrets baseline...
if exist .secrets.baseline (
    echo [i] Secrets baseline already exists
    detect-secrets scan --baseline .secrets.baseline --exclude-files ".*\.lock$" >nul 2>&1
    echo [OK] Secrets baseline updated
) else (
    echo [i] Creating new secrets baseline...
    detect-secrets scan --baseline .secrets.baseline --exclude-files ".*\.lock$" >nul 2>&1
    echo [OK] Secrets baseline created
)
echo.

REM Check for additional tools
echo [7/8] Checking additional dependencies...
where gitleaks >nul 2>&1
if errorlevel 1 (
    echo [!] gitleaks not installed (highly recommended for security)
    echo To install: See https://github.com/gitleaks/gitleaks#installation
) else (
    echo [OK] gitleaks detected
)
echo.

REM Run initial checks
echo [8/8] Running initial pre-commit checks...
echo This may take a few minutes on first run...
echo.
pre-commit run --all-files
if errorlevel 1 (
    echo.
    echo [!] Some pre-commit checks failed
    echo This is normal for the first run. Common issues:
    echo   - Code formatting (auto-fixable with: black src/ tests/)
    echo   - Import sorting (auto-fixable with: isort src/ tests/)
    echo   - Trailing whitespace (auto-fixed automatically)
    echo.
    echo To fix auto-fixable issues, run:
    echo   pre-commit run --all-files
    echo.
    echo Then stage and commit the changes:
    echo   git add .
    echo   git commit -m "style: apply pre-commit auto-fixes"
) else (
    echo.
    echo [OK] All pre-commit checks passed!
)
echo.

echo ================================================================
echo   Setup Complete!
echo ================================================================
echo.
echo Security Hooks Enabled:
echo   * detect-secrets  - Prevents API keys, passwords, tokens
echo   * gitleaks        - Scans for 100+ secret patterns
echo   * check-workflows - Validates GitHub Actions
echo   * bandit          - Python security linting
echo.
echo Code Quality Hooks Enabled:
echo   * black           - Code formatting [AUTO-FIX]
echo   * isort           - Import sorting [AUTO-FIX]
echo   * flake8          - Linting
echo   * mypy            - Type checking
echo.
echo Useful Commands:
echo   Run hooks manually:      pre-commit run --all-files
echo   Auto-fix formatting:     black src/ tests/ ^&^& isort src/ tests/
echo   Update hooks:            pre-commit autoupdate
echo   See quick reference:     type .pre-commit-quick-reference.md
echo.
echo Documentation:
echo   Quick Reference: .pre-commit-quick-reference.md
echo   Full Guide:      docs\PRE_COMMIT_SETUP.md
echo   Contributing:    CONTRIBUTING.md
echo.
echo You're all set! Happy coding!
echo.
pause
