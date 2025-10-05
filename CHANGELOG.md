# Changelog

All notable changes to the Playwright Failure Analyzer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive documentation and examples for GitHub Marketplace release
- Full AI integration testing guide
- Support for OpenRouter and DeepSeek AI providers
- `.env.example` template for configuration

### Changed
- README.md completely rewritten for marketplace readiness
- Updated all repository URLs from placeholders to actual organization

## [1.0.0] - 2025-10-05

### Added
- 🎉 Initial release of Intelligent Playwright Failure Analyzer
- 🤖 AI-powered failure analysis using LiteLLM
  - Support for OpenAI (GPT-4o, GPT-4o-mini)
  - Support for Anthropic (Claude 3.5)
  - Support for OpenRouter (access to 100+ models)
  - Support for DeepSeek (ultra-low cost option)
- 📊 Intelligent test failure parsing
  - Parse Playwright JSON reports
  - Extract detailed failure information
  - Include stack traces and error messages
- 📋 Automated GitHub issue creation
  - Rich Markdown formatting
  - Comprehensive failure details
  - Test metadata and context
  - GitHub workflow information
- 🔄 Smart deduplication
  - Hash-based duplicate detection
  - Prevents duplicate issues for same failures
- ⚙️ Configurable options
  - Custom failure limits
  - Customizable labels and assignees
  - Flexible report paths
  - Optional AI analysis
- 🎨 Beautiful issue formatting
  - Professional Markdown layout
  - Code blocks for stack traces
  - Tables for statistics
  - Emoji indicators for readability
- 🔒 Secure implementation
  - No data storage
  - Runs in GitHub Actions environment
  - Proper token handling
- ⚡ Performance optimized
  - Efficient JSON parsing
  - Minimal dependencies
  - Fast execution
- 🧪 Comprehensive testing
  - 50+ unit and integration tests
  - 5 E2E test scenarios
  - 93% code coverage
  - All tests passing
- 📚 Complete documentation
  - README with quick start
  - AI testing guide
  - Setup scripts for development
  - Contributing guidelines
- 🛠️ Development tools
  - Pre-commit hooks (black, isort, flake8, mypy, bandit)
  - Automated linting and type checking
  - Security scanning (gitleaks, detect-secrets, bandit)
  - Comprehensive CI/CD pipeline

### Security
- ANSI escape code stripping to prevent display issues
- Input validation for all user-provided data
- Secure token handling with proper scoping
- Security scanning integrated into CI/CD
- No hardcoded secrets or credentials

### Performance
- Typical analysis time: <2 seconds (without AI)
- With AI analysis: 5-10 seconds
- Cost with DeepSeek: ~$0.0003 per analysis
- Minimal memory footprint

## [0.9.0] - 2025-10-04 (Pre-release)

### Added
- Beta testing phase
- Core functionality implementation
- Initial AI integration
- Basic documentation

### Fixed
- Multiple linting and type checking issues
- Security warnings from bandit
- Test coverage improvements

## [0.1.0] - 2025-09-15 (Alpha)

### Added
- Initial project structure
- Basic Playwright report parsing
- GitHub issue creation
- Simple deduplication logic

---

## Release Notes

### v1.0.0 - Production Ready! 🎉

This is the first production-ready release of the Intelligent Playwright Failure Analyzer!

**Highlights:**
- ✅ **Fully tested**: 50+ tests, 93% coverage
- ✅ **AI-powered**: Optional intelligent analysis with 4 provider options
- ✅ **Cost-effective**: Ultra-cheap with OpenRouter + DeepSeek (~$0.0003/analysis)
- ✅ **Secure**: Comprehensive security scanning, no vulnerabilities
- ✅ **Well-documented**: Complete guides and examples
- ✅ **Marketplace ready**: Meets all GitHub Marketplace requirements

**Breaking Changes:**
- None (first major release)

**Migration Guide:**
- Not applicable (first release)

**Known Issues:**
- None currently identified

**Upgrade Path:**
- Fresh installation - just add to your workflow!

---

## Versioning Strategy

We follow [Semantic Versioning](https://semver.org/):
- **MAJOR** version (X.0.0): Incompatible API changes
- **MINOR** version (0.X.0): New functionality in a backward-compatible manner
- **PATCH** version (0.0.X): Backward-compatible bug fixes

---

## Support

- 🐛 [Report bugs](https://github.com/decision-crafters/playwright-failure-analyzer/issues/new?template=bug_report.md)
- ✨ [Request features](https://github.com/decision-crafters/playwright-failure-analyzer/issues/new?template=feature_request.md)
- 💬 [Ask questions](https://github.com/decision-crafters/playwright-failure-analyzer/discussions)
- 📖 [Read docs](https://github.com/decision-crafters/playwright-failure-analyzer/tree/main/docs)

---

[Unreleased]: https://github.com/decision-crafters/playwright-failure-analyzer/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/decision-crafters/playwright-failure-analyzer/releases/tag/v1.0.0
[0.9.0]: https://github.com/decision-crafters/playwright-failure-analyzer/releases/tag/v0.9.0
[0.1.0]: https://github.com/decision-crafters/playwright-failure-analyzer/releases/tag/v0.1.0
