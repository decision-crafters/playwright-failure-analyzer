#!/usr/bin/env python3
"""
Pre-commit Hooks Setup Script (Python version)
Playwright Failure Analyzer

This script installs and configures pre-commit hooks with security-first approach
Cross-platform compatible (Linux, macOS, Windows)

Author: Tosin Akinosho
Usage: python scripts/setup-precommit.py
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output"""

    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    CYAN = "\033[0;36m"
    NC = "\033[0m"  # No Color

    @staticmethod
    def supports_color():
        """Check if terminal supports colors"""
        if os.name == "nt":
            # Enable ANSI colors on Windows 10+
            try:
                import ctypes

                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
                return True
            except:
                return False
        return True


# Disable colors on Windows if not supported
if not Colors.supports_color():
    Colors.RED = Colors.GREEN = Colors.YELLOW = Colors.BLUE = Colors.CYAN = Colors.NC = ""


def print_header():
    """Print setup header"""
    print(f"\n{Colors.BLUE}{'='*68}{Colors.NC}")
    print(f"{Colors.BLUE}  🔒 Pre-commit Hooks Setup - Security First{Colors.NC}")
    print(f"{Colors.BLUE}     Playwright Failure Analyzer{Colors.NC}")
    print(f"{Colors.BLUE}{'='*68}{Colors.NC}\n")


def print_step(msg):
    """Print step message"""
    print(f"{Colors.CYAN}{msg}{Colors.NC}")


def print_success(msg):
    """Print success message"""
    print(f"{Colors.GREEN}✓{Colors.NC} {msg}")


def print_error(msg):
    """Print error message"""
    print(f"{Colors.RED}✗{Colors.NC} {msg}")


def print_warning(msg):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠{Colors.NC} {msg}")


def print_info(msg):
    """Print info message"""
    print(f"{Colors.BLUE}→{Colors.NC} {msg}")


def run_command(cmd, check=True, capture_output=False):
    """Run a shell command"""
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
            return result.stdout.strip()
        else:
            subprocess.run(cmd, shell=True, check=check)
            return True
    except subprocess.CalledProcessError as e:
        if check:
            raise
        return False


def check_git_repo():
    """Check if running in a git repository"""
    print_step("Checking Git repository...")
    try:
        run_command("git rev-parse --git-dir", capture_output=True)
        print_success("Git repository detected")
        return True
    except subprocess.CalledProcessError:
        print_error("Not a git repository!")
        print("Please run this script from the root of the repository.")
        return False


def check_python():
    """Check Python version"""
    print_step("\nChecking Python installation...")

    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"

    print_success(f"Python {version_str} detected")

    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print_warning(f"Python 3.9+ recommended (you have {version_str})")

    return True


def check_pip():
    """Check if pip is available"""
    print_step("\nChecking pip installation...")

    if shutil.which("pip") or shutil.which("pip3"):
        print_success("pip detected")
        return True
    else:
        print_error("pip is not installed!")
        print("Please install pip for Python 3.")
        return False


def install_precommit():
    """Install pre-commit"""
    print_step("\nInstalling pre-commit...")

    if shutil.which("pre-commit"):
        try:
            version = run_command("pre-commit --version", capture_output=True)
            print_info(f"pre-commit {version} already installed")
        except:
            print_info("pre-commit already installed")
    else:
        print_info("Installing pre-commit via pip...")
        run_command(f"{sys.executable} -m pip install --user pre-commit")
        print_success("pre-commit installed")

    return True


def install_python_tools():
    """Install Python development tools"""
    print_step("\nInstalling Python development tools...")

    tools = ["black", "isort", "flake8", "mypy", "bandit", "detect-secrets"]

    for tool in tools:
        if shutil.which(tool):
            print_info(f"{tool} already installed")
        else:
            print_info(f"Installing {tool}...")
            run_command(f"{sys.executable} -m pip install --user {tool}")

    print_success("All Python tools installed")
    return True


def install_git_hooks():
    """Install git hooks"""
    print_step("\nInstalling git hooks...")

    # Install pre-commit hook
    run_command("pre-commit install")
    print_success("Pre-commit hook installed")

    # Install commit-msg hook
    run_command("pre-commit install --hook-type commit-msg")
    print_success("Commit-msg hook installed")

    return True


def initialize_secrets_baseline():
    """Initialize secrets baseline"""
    print_step("\nInitializing secrets baseline...")

    baseline_path = Path(".secrets.baseline")

    if baseline_path.exists():
        print_info("Secrets baseline already exists")
        run_command(
            'detect-secrets scan --baseline .secrets.baseline --exclude-files ".*\\.lock$"',
            check=False,
        )
        print_success("Secrets baseline updated")
    else:
        print_info("Creating new secrets baseline...")
        run_command(
            'detect-secrets scan --baseline .secrets.baseline --exclude-files ".*\\.lock$"',
            check=False,
        )
        print_success("Secrets baseline created")

    return True


def check_additional_deps():
    """Check for additional dependencies"""
    print_step("\nChecking additional dependencies...")

    # Check markdownlint
    if shutil.which("markdownlint"):
        print_info("markdownlint already installed")
    else:
        print_warning("markdownlint not installed (optional - requires Node.js)")
        print_info("To install: npm install -g markdownlint-cli")

    # Check gitleaks
    if shutil.which("gitleaks"):
        try:
            version = run_command("gitleaks version", capture_output=True)
            print_success(f"gitleaks detected")
        except:
            print_success("gitleaks detected")
    else:
        print_warning("gitleaks not installed (highly recommended for security)")
        print("")
        print_info("To install gitleaks:")
        print("  macOS:   brew install gitleaks")
        print("  Linux:   See https://github.com/gitleaks/gitleaks#installation")
        print("  Windows: See https://github.com/gitleaks/gitleaks#installation")

    return True


def run_initial_checks():
    """Run initial pre-commit checks"""
    print_step("\nRunning initial pre-commit checks...")
    print(f"\n{Colors.YELLOW}This may take a few minutes on first run...{Colors.NC}\n")

    success = run_command("pre-commit run --all-files", check=False)

    if success:
        print("")
        print_success("All pre-commit checks passed! 🎉")
    else:
        print("")
        print_warning("Some pre-commit checks failed")
        print("")
        print_info("This is normal for the first run. Common issues:")
        print("  • Code formatting (auto-fixable with: black src/ tests/)")
        print("  • Import sorting (auto-fixable with: isort src/ tests/)")
        print("  • Trailing whitespace (auto-fixed automatically)")
        print("")
        print_info("To fix auto-fixable issues, run:")
        print(f"  {Colors.CYAN}pre-commit run --all-files{Colors.NC}")
        print("")
        print_info("Then stage and commit the changes:")
        print(f"  {Colors.CYAN}git add .{Colors.NC}")
        print(f'  {Colors.CYAN}git commit -m "style: apply pre-commit auto-fixes"{Colors.NC}')

    return True


def print_summary():
    """Print summary and next steps"""
    print(f"\n{Colors.BLUE}{'='*68}{Colors.NC}")
    print(f"{Colors.BLUE}  🎉 Pre-commit Setup Complete!{Colors.NC}")
    print(f"{Colors.BLUE}{'='*68}{Colors.NC}\n")

    print_success("Pre-commit hooks are now installed and configured\n")

    print(f"{Colors.CYAN}Security Hooks Enabled:{Colors.NC}")
    print("  🔐 detect-secrets  - Prevents API keys, passwords, tokens")
    print("  🕵️  gitleaks       - Scans for 100+ secret patterns")
    print("  ✅ check-workflows - Validates GitHub Actions")
    print("  🛡️  bandit         - Python security linting")

    print(f"\n{Colors.CYAN}Code Quality Hooks Enabled:{Colors.NC}")
    print("  🎨 black           - Code formatting [AUTO-FIX]")
    print("  📦 isort           - Import sorting [AUTO-FIX]")
    print("  🔍 flake8          - Linting")
    print("  🔎 mypy            - Type checking")

    print(f"\n{Colors.CYAN}How It Works:{Colors.NC}")
    print("  1. Make your changes")
    print(f"  2. Stage files: {Colors.YELLOW}git add .{Colors.NC}")
    print(f'  3. Commit: {Colors.YELLOW}git commit -m "feat: your message"{Colors.NC}')
    print("  4. Pre-commit hooks run automatically!")

    print(f"\n{Colors.CYAN}Useful Commands:{Colors.NC}")
    print(f"  • Run hooks manually:      {Colors.YELLOW}pre-commit run --all-files{Colors.NC}")
    print(
        f"  • Auto-fix formatting:     {Colors.YELLOW}black src/ tests/ && isort src/ tests/{Colors.NC}"
    )
    print(f"  • Update hooks:            {Colors.YELLOW}pre-commit autoupdate{Colors.NC}")
    print(
        f"  • See quick reference:     {Colors.YELLOW}cat .pre-commit-quick-reference.md{Colors.NC}"
    )

    print(f"\n{Colors.CYAN}Documentation:{Colors.NC}")
    print("  • Quick Reference: .pre-commit-quick-reference.md")
    print("  • Full Guide:      docs/PRE_COMMIT_SETUP.md")
    print("  • Contributing:    CONTRIBUTING.md")

    print(f"\n{Colors.GREEN}You're all set! Happy coding! 🚀{Colors.NC}\n")


def main():
    """Main execution"""
    print_header()

    steps = [
        ("Git Repository", check_git_repo),
        ("Python", check_python),
        ("pip", check_pip),
        ("Pre-commit", install_precommit),
        ("Python Tools", install_python_tools),
        ("Git Hooks", install_git_hooks),
        ("Secrets Baseline", initialize_secrets_baseline),
        ("Additional Dependencies", check_additional_deps),
        ("Initial Checks", run_initial_checks),
    ]

    for name, func in steps:
        try:
            if not func():
                print_error(f"\nSetup failed at step: {name}")
                return 1
        except Exception as e:
            print_error(f"\nError during {name}: {str(e)}")
            return 1

    print_summary()
    return 0


if __name__ == "__main__":
    sys.exit(main())
