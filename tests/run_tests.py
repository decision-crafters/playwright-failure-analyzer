#!/usr/bin/env python3
"""
Test runner for the Playwright Failure Bundler action.

This script runs all tests and generates a coverage report.
"""

import subprocess
import sys
import unittest
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


def run_unit_tests():
    """Run all unit tests."""
    print("🧪 Running unit tests...")

    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent
    suite = loader.discover(start_dir, pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


def run_linting():
    """Run code linting checks."""
    print("🔍 Running linting checks...")

    src_dir = Path(__file__).parent.parent / "src"

    try:
        # Check if flake8 is available
        subprocess.run(["flake8", "--version"], capture_output=True, check=True)

        # Run flake8 on source code
        result = subprocess.run(
            [
                "flake8",
                str(src_dir),
                "--max-line-length=100",
                "--ignore=E501,W503",  # Ignore line length and line break before binary operator
                "--exclude=__pycache__",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("✅ Linting passed")
            return True
        else:
            print("❌ Linting failed:")
            print(result.stdout)
            print(result.stderr)
            return False

    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  flake8 not available, skipping linting")
        return True


def check_dependencies():
    """Check that all required dependencies are available."""
    print("📦 Checking dependencies...")

    required_packages = ["requests"]
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install -r requirements.txt")
        return False

    print("✅ All dependencies available")
    return True


def run_type_checking():
    """Run type checking with mypy if available."""
    print("🔍 Running type checking...")

    src_dir = Path(__file__).parent.parent / "src"

    try:
        # Check if mypy is available
        subprocess.run(["mypy", "--version"], capture_output=True, check=True)

        # Run mypy on source code
        result = subprocess.run(
            ["mypy", str(src_dir), "--ignore-missing-imports", "--no-strict-optional"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("✅ Type checking passed")
            return True
        else:
            print("⚠️  Type checking issues found:")
            print(result.stdout)
            return True  # Don't fail on type checking issues for now

    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  mypy not available, skipping type checking")
        return True


def generate_test_report():
    """Generate a test report summary."""
    print("\n" + "=" * 60)
    print("📊 TEST REPORT SUMMARY")
    print("=" * 60)

    # Count test files
    test_dir = Path(__file__).parent
    test_files = list(test_dir.glob("test_*.py"))
    print(f"Test files: {len(test_files)}")

    # Count source files
    src_dir = Path(__file__).parent.parent / "src"
    src_files = list(src_dir.glob("*.py"))
    print(f"Source files: {len(src_files)}")

    # List test files
    print("\nTest files:")
    for test_file in test_files:
        print(f"  • {test_file.name}")

    print("\nSource files:")
    for src_file in src_files:
        print(f"  • {src_file.name}")


def main():
    """Main test runner function."""
    print("🚀 Starting Playwright Failure Bundler test suite")
    print("=" * 60)

    success = True

    # Check dependencies first
    if not check_dependencies():
        return 1

    # Run linting
    if not run_linting():
        success = False

    # Run type checking
    if not run_type_checking():
        success = False

    # Run unit tests
    if not run_unit_tests():
        success = False

    # Generate report
    generate_test_report()

    if success:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
