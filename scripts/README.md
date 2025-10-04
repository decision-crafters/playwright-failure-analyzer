# Setup Scripts

This directory contains setup and utility scripts for the Playwright Failure Analyzer project.

## 🔐 Pre-commit Hooks Setup

We provide **three versions** of the pre-commit setup script for maximum compatibility:

### Option 1: Bash Script (Linux/macOS) - Recommended

```bash
./scripts/setup-precommit.sh
```

**Features:**
- ✅ Colorful output with emoji indicators
- ✅ Step-by-step progress tracking
- ✅ Automatic dependency installation
- ✅ Comprehensive error checking
- ✅ Initial verification run

**Requirements:**
- Bash shell (default on Linux/macOS)
- Python 3.9+
- Git

---

### Option 2: Python Script (Cross-platform) - Most Portable

```bash
python scripts/setup-precommit.py
# or
python3 scripts/setup-precommit.py
```

**Features:**
- ✅ Works on Linux, macOS, and Windows
- ✅ No bash required
- ✅ Colorful output (Windows 10+ compatible)
- ✅ Same functionality as bash script
- ✅ Pure Python implementation

**Requirements:**
- Python 3.9+
- Git

---

### Option 3: Batch Script (Windows) - Windows Native

```cmd
scripts\setup-precommit.bat
```

**Features:**
- ✅ Native Windows batch script
- ✅ Works in cmd.exe and PowerShell
- ✅ No bash or Python required for execution
- ✅ Step-by-step progress

**Requirements:**
- Windows OS
- Python 3.9+ (must be installed separately)
- Git

---

## 📋 What These Scripts Do

All three scripts perform the same setup tasks:

1. **✓ Check prerequisites** - Verify Git, Python, and pip are installed
2. **✓ Install pre-commit** - Install the pre-commit framework
3. **✓ Install Python tools** - Install black, isort, flake8, mypy, bandit, detect-secrets
4. **✓ Configure git hooks** - Install pre-commit and commit-msg hooks
5. **✓ Initialize secrets baseline** - Create .secrets.baseline for detect-secrets
6. **✓ Check optional tools** - Verify gitleaks and markdownlint installation
7. **✓ Run initial checks** - Execute pre-commit on all files to verify setup
8. **✓ Display summary** - Show installed hooks and next steps

## 🚀 Quick Start Guide

### First Time Setup

**Choose your script based on your OS:**

```bash
# Linux/macOS
./scripts/setup-precommit.sh

# Windows (PowerShell or cmd)
scripts\setup-precommit.bat

# Any OS (using Python)
python scripts/setup-precommit.py
```

### After Setup

Once setup is complete, pre-commit hooks run automatically on every commit:

```bash
# Make your changes
vim src/my_feature.py

# Stage and commit (hooks run automatically)
git add .
git commit -m "feat: add new feature"

# If hooks fail, fix issues and try again
```

## 🔍 Troubleshooting

### Script won't execute (Permission Denied)

**Linux/macOS:**
```bash
chmod +x scripts/setup-precommit.sh
./scripts/setup-precommit.sh
```

**Use Python version instead:**
```bash
python scripts/setup-precommit.py
```

### Python not found

**Install Python:**
- **macOS:** `brew install python3`
- **Linux:** `sudo apt-get install python3 python3-pip` (Ubuntu/Debian)
- **Windows:** Download from https://www.python.org/downloads/

### pip not found

**Install pip:**
```bash
# Linux
sudo apt-get install python3-pip

# macOS
python3 -m ensurepip --upgrade

# Windows
python -m ensurepip --upgrade
```

### Hooks fail on first run

This is **normal**! First-time runs often detect formatting issues. Fix them:

```bash
# Auto-fix formatting issues
black src/ tests/
isort src/ tests/

# Run hooks again
pre-commit run --all-files

# Commit the fixes
git add .
git commit -m "style: apply pre-commit auto-fixes"
```

### gitleaks not installed warning

**Install gitleaks (optional but recommended):**

```bash
# macOS
brew install gitleaks

# Linux (using binary)
wget https://github.com/gitleaks/gitleaks/releases/download/v8.18.2/gitleaks_8.18.2_linux_x64.tar.gz
tar -xzf gitleaks_8.18.2_linux_x64.tar.gz
sudo mv gitleaks /usr/local/bin/

# Windows
# Download from https://github.com/gitleaks/gitleaks/releases
```

## 📚 Additional Resources

- **Quick Reference:** [`../.pre-commit-quick-reference.md`](../.pre-commit-quick-reference.md)
- **Full Setup Guide:** [`../docs/PRE_COMMIT_SETUP.md`](../docs/PRE_COMMIT_SETUP.md)
- **Implementation Summary:** [`../PRE_COMMIT_IMPLEMENTATION_SUMMARY.md`](../PRE_COMMIT_IMPLEMENTATION_SUMMARY.md)

## 🤝 Contributing

If you improve these scripts or add new ones, please:

1. Test on multiple platforms (Linux, macOS, Windows)
2. Update this README
3. Follow the existing code style
4. Add error handling
5. Include helpful output messages

## 💡 Tips

- **Run setup-precommit.sh from repository root** for best results
- **Use Python version for CI/CD** environments (most portable)
- **Batch script is faster on Windows** than Git Bash
- **All scripts create the same configuration**

---

**Need help?** See [docs/PRE_COMMIT_SETUP.md](../docs/PRE_COMMIT_SETUP.md) for comprehensive troubleshooting.
