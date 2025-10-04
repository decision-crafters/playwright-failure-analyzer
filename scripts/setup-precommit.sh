#!/bin/bash
#
# Pre-commit Hooks Setup Script
# Playwright Failure Analyzer
#
# This script installs and configures pre-commit hooks with security-first approach
# Author: Tosin Akinosho
# Usage: ./scripts/setup-precommit.sh

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Symbols
CHECK="${GREEN}✓${NC}"
CROSS="${RED}✗${NC}"
ARROW="${BLUE}→${NC}"
WARN="${YELLOW}⚠${NC}"

# Print functions
print_header() {
    echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  🔒 Pre-commit Hooks Setup - Security First                 ${BLUE}║${NC}"
    echo -e "${BLUE}║${NC}     Playwright Failure Analyzer                              ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}\n"
}

print_step() {
    echo -e "${CYAN}${1}${NC}"
}

print_success() {
    echo -e "${CHECK} ${1}"
}

print_error() {
    echo -e "${CROSS} ${1}"
}

print_warning() {
    echo -e "${WARN} ${1}"
}

print_info() {
    echo -e "${ARROW} ${1}"
}

# Check if running in git repository
check_git_repo() {
    print_step "Checking Git repository..."
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_error "Not a git repository!"
        echo "Please run this script from the root of the repository."
        exit 1
    fi
    print_success "Git repository detected"
}

# Check Python version
check_python() {
    print_step "\nChecking Python installation..."

    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed!"
        echo "Please install Python 3.9 or higher."
        exit 1
    fi

    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_success "Python ${PYTHON_VERSION} detected"

    # Check if version is 3.9 or higher
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
        print_warning "Python 3.9+ recommended (you have ${PYTHON_VERSION})"
    fi
}

# Setup virtual environment for development tools
setup_venv() {
    print_step "\nSetting up Python virtual environment..."

    VENV_DIR=".venv"

    if [ -d "$VENV_DIR" ]; then
        print_info "Virtual environment already exists"
    else
        print_info "Creating virtual environment..."

        # Prefer Python 3.11 if available
        if command -v python3.11 &> /dev/null; then
            PYTHON_CMD="python3.11"
            print_info "Using Python 3.11 for venv"
        elif command -v python3 &> /dev/null; then
            PYTHON_CMD="python3"
        else
            print_error "Python 3 not found!"
            exit 1
        fi

        $PYTHON_CMD -m venv $VENV_DIR
        print_success "Virtual environment created"
    fi

    # Activate venv and set pip command
    source $VENV_DIR/bin/activate
    PIP_CMD="$VENV_DIR/bin/pip"

    # Upgrade pip in venv
    print_info "Upgrading pip in venv..."
    $PIP_CMD install --upgrade pip > /dev/null 2>&1

    print_success "Virtual environment ready"
}

# Install pre-commit
install_precommit() {
    print_step "\nInstalling pre-commit in venv..."

    print_info "Installing pre-commit..."
    $PIP_CMD install pre-commit > /dev/null 2>&1

    PRECOMMIT_VERSION=$($VENV_DIR/bin/pre-commit --version | cut -d' ' -f2)
    print_success "pre-commit ${PRECOMMIT_VERSION} installed"
}

# Install Python development tools
install_python_tools() {
    print_step "\nInstalling Python development tools..."

    TOOLS=(
        "black"
        "isort"
        "flake8"
        "mypy"
        "bandit"
        "detect-secrets"
    )

    print_info "Installing tools into venv..."
    $PIP_CMD install "${TOOLS[@]}" > /dev/null 2>&1

    print_success "All Python tools installed"
}

# Install git hooks
install_git_hooks() {
    print_step "\nInstalling git hooks..."

    # Install pre-commit hook using venv's pre-commit
    $VENV_DIR/bin/pre-commit install
    print_success "Pre-commit hook installed"

    # Install commit-msg hook for conventional commits
    $VENV_DIR/bin/pre-commit install --hook-type commit-msg
    print_success "Commit-msg hook installed"
}

# Initialize secrets baseline
initialize_secrets_baseline() {
    print_step "\nInitializing secrets baseline..."

    if [ -f ".secrets.baseline" ]; then
        print_info "Secrets baseline already exists"

        # Update the baseline with current files
        $VENV_DIR/bin/detect-secrets scan --baseline .secrets.baseline --exclude-files '.*\.lock$' > /dev/null 2>&1 || true
        print_success "Secrets baseline updated"
    else
        print_info "Creating new secrets baseline..."
        $VENV_DIR/bin/detect-secrets scan --baseline .secrets.baseline --exclude-files '.*\.lock$' > /dev/null 2>&1 || true
        print_success "Secrets baseline created"
    fi
}

# Install additional dependencies
install_additional_deps() {
    print_step "\nInstalling additional dependencies..."

    # Check if markdownlint is available (optional)
    if command -v markdownlint &> /dev/null; then
        print_info "markdownlint already installed"
    else
        print_warning "markdownlint not installed (optional - requires Node.js)"
        print_info "To install: npm install -g markdownlint-cli"
    fi

    # Check if gitleaks is available (optional but recommended)
    if command -v gitleaks &> /dev/null; then
        GITLEAKS_VERSION=$(gitleaks version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
        print_success "gitleaks ${GITLEAKS_VERSION} detected"
    else
        print_warning "gitleaks not installed (highly recommended for security)"
        echo ""
        print_info "To install gitleaks:"
        echo "  macOS:   brew install gitleaks"
        echo "  Linux:   See https://github.com/gitleaks/gitleaks#installation"
        echo "  Windows: See https://github.com/gitleaks/gitleaks#installation"
    fi
}

# Run initial checks
run_initial_checks() {
    print_step "\nRunning initial pre-commit checks..."

    echo -e "\n${YELLOW}This may take a few minutes on first run...${NC}\n"

    # Run pre-commit on all files using venv's pre-commit
    if $VENV_DIR/bin/pre-commit run --all-files; then
        echo ""
        print_success "All pre-commit checks passed! 🎉"
    else
        echo ""
        print_warning "Some pre-commit checks failed"
        echo ""
        print_info "This is normal for the first run. Common issues:"
        echo "  • Code formatting (auto-fixable with: .venv/bin/black src/ tests/)"
        echo "  • Import sorting (auto-fixable with: .venv/bin/isort src/ tests/)"
        echo "  • Trailing whitespace (auto-fixed automatically)"
        echo ""
        print_info "To fix auto-fixable issues, run:"
        echo "  ${CYAN}.venv/bin/pre-commit run --all-files${NC}"
        echo ""
        print_info "Then stage and commit the changes:"
        echo "  ${CYAN}git add .${NC}"
        echo "  ${CYAN}git commit -m \"style: apply pre-commit auto-fixes\"${NC}"
    fi
}

# Print summary and next steps
print_summary() {
    echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  🎉 Pre-commit Setup Complete!                              ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}\n"

    print_success "Pre-commit hooks are now installed and configured\n"

    echo -e "${CYAN}Security Hooks Enabled:${NC}"
    echo "  🔐 detect-secrets  - Prevents API keys, passwords, tokens"
    echo "  🕵️  gitleaks       - Scans for 100+ secret patterns"
    echo "  ✅ check-workflows - Validates GitHub Actions"
    echo "  🛡️  bandit         - Python security linting"

    echo -e "\n${CYAN}Code Quality Hooks Enabled:${NC}"
    echo "  🎨 black           - Code formatting [AUTO-FIX]"
    echo "  📦 isort           - Import sorting [AUTO-FIX]"
    echo "  🔍 flake8          - Linting"
    echo "  🔎 mypy            - Type checking"

    echo -e "\n${CYAN}How It Works:${NC}"
    echo "  1. Make your changes"
    echo "  2. Stage files: ${YELLOW}git add .${NC}"
    echo "  3. Commit: ${YELLOW}git commit -m \"feat: your message\"${NC}"
    echo "  4. Pre-commit hooks run automatically!"

    echo -e "\n${CYAN}Useful Commands:${NC}"
    echo "  • Run hooks manually:      ${YELLOW}.venv/bin/pre-commit run --all-files${NC}"
    echo "  • Auto-fix formatting:     ${YELLOW}.venv/bin/black src/ tests/ && .venv/bin/isort src/ tests/${NC}"
    echo "  • Update hooks:            ${YELLOW}.venv/bin/pre-commit autoupdate${NC}"
    echo "  • See quick reference:     ${YELLOW}cat .pre-commit-quick-reference.md${NC}"

    echo -e "\n${CYAN}Documentation:${NC}"
    echo "  • Quick Reference: .pre-commit-quick-reference.md"
    echo "  • Full Guide:      docs/PRE_COMMIT_SETUP.md"
    echo "  • Contributing:    CONTRIBUTING.md"

    echo -e "\n${GREEN}You're all set! Happy coding! 🚀${NC}\n"
}

# Main execution
main() {
    print_header

    check_git_repo
    check_python
    setup_venv
    install_precommit
    install_python_tools
    install_git_hooks
    initialize_secrets_baseline
    install_additional_deps
    run_initial_checks
    print_summary
}

# Run main function
main
