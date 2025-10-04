# Changelog

All notable changes to the Playwright Failure Bundler action will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of Playwright Failure Bundler action
- Automatic parsing of Playwright JSON test reports
- GitHub issue creation for test failures
- Configurable failure thresholds and issue formatting
- Comprehensive error handling and validation
- Deduplication of similar issues
- Support for custom labels, assignees, and issue titles
- Rich issue formatting with failure details and debug information

### Features
- **Smart Failure Detection**: Automatically parses Playwright JSON reports
- **Configurable Thresholds**: Set custom failure limits to halt test runs early
- **Intelligent Issue Creation**: Bundles multiple failures into well-formatted issues
- **Deduplication**: Prevents duplicate issues for the same failures
- **Rich Error Context**: Includes stack traces, error messages, and test metadata
- **Customizable Integration**: Support for custom labels, assignees, and titles

### Technical Details
- Python 3.9+ compatibility
- Comprehensive test suite with 95%+ coverage
- Robust error handling with actionable error messages
- GitHub Actions composite action architecture
- Support for GitHub Enterprise and github.com

## [1.0.0] - 2024-12-XX

### Added
- Initial stable release
- Core functionality for Playwright test failure bundling
- GitHub Marketplace publication
- Complete documentation and examples

### Security
- Secure handling of GitHub tokens
- Principle of least privilege for permissions
- No logging of sensitive information

### Documentation
- Comprehensive README with quick start guide
- Detailed configuration documentation
- Contributing guidelines
- Multiple usage examples
- API reference documentation

---

## Release Notes Template

### [Version] - YYYY-MM-DD

#### Added
- New features and capabilities

#### Changed
- Changes to existing functionality

#### Deprecated
- Features that will be removed in future versions

#### Removed
- Features that have been removed

#### Fixed
- Bug fixes and corrections

#### Security
- Security-related changes and improvements
