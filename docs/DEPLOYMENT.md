# Deployment Guide

This guide covers how to deploy and publish the Playwright Failure Bundler action to GitHub Marketplace and how to set up your own instance.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Publishing to GitHub Marketplace](#publishing-to-github-marketplace)
- [Self-Hosting the Action](#self-hosting-the-action)
- [Version Management](#version-management)
- [Testing Before Release](#testing-before-release)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before deploying the action, ensure you have:

- **GitHub repository** with appropriate permissions
- **Python 3.9+** for local testing
- **Git** configured with your GitHub credentials
- **Understanding** of GitHub Actions and marketplace policies

### Repository Setup

Your repository should have the following structure:

```
playwright-failure-bundler/
├── action.yml                 # Action definition
├── README.md                 # Documentation
├── LICENSE                   # License file
├── requirements.txt          # Python dependencies
├── src/                      # Source code
│   ├── parse_report.py
│   ├── create_issue.py
│   ├── error_handling.py
│   └── utils.py
├── tests/                    # Test suite
├── examples/                 # Usage examples
├── docs/                     # Documentation
└── .github/workflows/        # CI/CD workflows
```

## Publishing to GitHub Marketplace

### Step 1: Prepare for Release

1. **Update version information** in relevant files
2. **Update CHANGELOG.md** with new features and fixes
3. **Run the complete test suite** to ensure everything works
4. **Review documentation** for accuracy and completeness

### Step 2: Create a Release

1. **Tag the release** with semantic versioning:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. **Create a GitHub release** from the tag:
   - Go to your repository on GitHub
   - Click "Releases" → "Create a new release"
   - Select your tag
   - Fill in release notes

### Step 3: Marketplace Submission

1. **Navigate to GitHub Marketplace**:
   - Go to https://github.com/marketplace
   - Click "List an action"

2. **Select your repository** and configure:
   - Choose the repository containing your action
   - Select the release tag
   - Configure marketplace settings

3. **Complete the listing**:
   - Add description and categories
   - Upload logo/icon if desired
   - Review and submit for approval

### Step 4: Marketplace Review

GitHub will review your action for:
- **Security compliance**
- **Functionality verification**
- **Documentation quality**
- **Marketplace guidelines adherence**

The review process typically takes 1-3 business days.

## Self-Hosting the Action

If you prefer to host the action privately or need customizations:

### Option 1: Fork and Customize

1. **Fork the repository**:
   ```bash
   git clone https://github.com/your-org/playwright-failure-bundler.git
   cd playwright-failure-bundler
   ```

2. **Make your customizations**:
   - Modify source code as needed
   - Update configuration options
   - Add custom features

3. **Use in your workflows**:
   ```yaml
   - uses: your-org/playwright-failure-bundler@main
     with:
       github-token: ${{ secrets.GITHUB_TOKEN }}
   ```

### Option 2: Local Action

1. **Copy action files** to your repository:
   ```
   .github/actions/playwright-failure-bundler/
   ├── action.yml
   ├── requirements.txt
   └── src/
   ```

2. **Use as local action**:
   ```yaml
   - uses: ./.github/actions/playwright-failure-bundler
     with:
       github-token: ${{ secrets.GITHUB_TOKEN }}
   ```

### Option 3: Docker Container

1. **Create Dockerfile**:
   ```dockerfile
   FROM python:3.9-slim
   
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   
   COPY src/ ./src/
   COPY action.yml .
   
   ENTRYPOINT ["python", "/app/src/main.py"]
   ```

2. **Build and publish**:
   ```bash
   docker build -t your-org/playwright-failure-bundler .
   docker push your-org/playwright-failure-bundler
   ```

3. **Use in workflows**:
   ```yaml
   - uses: docker://your-org/playwright-failure-bundler:latest
     with:
       github-token: ${{ secrets.GITHUB_TOKEN }}
   ```

## Version Management

### Semantic Versioning

Follow semantic versioning (semver) for releases:

- **MAJOR** (v2.0.0): Breaking changes
- **MINOR** (v1.1.0): New features, backward compatible
- **PATCH** (v1.0.1): Bug fixes, backward compatible

### Version Tags

Maintain multiple tag formats for flexibility:

```bash
# Specific version
git tag v1.2.3

# Major version (for marketplace)
git tag v1

# Latest (optional)
git tag latest

# Push all tags
git push origin --tags
```

### Branch Strategy

Recommended branching strategy:

- **main**: Stable releases only
- **develop**: Integration branch for features
- **feature/***: Individual feature branches
- **hotfix/***: Critical bug fixes

### Release Process

1. **Feature development** on feature branches
2. **Integration testing** on develop branch
3. **Release preparation** and testing
4. **Merge to main** and tag release
5. **Marketplace update** (automatic via CI/CD)

## Testing Before Release

### Local Testing

1. **Run the test suite**:
   ```bash
   python tests/run_tests.py
   ```

2. **Test with real Playwright reports**:
   ```bash
   # Create a test report
   npx playwright test --reporter=json
   
   # Test the parser
   python src/parse_report.py \
     --report-path test-results/results.json \
     --max-failures 3 \
     --output-file /tmp/summary.json
   ```

3. **Test issue creation** (with test repository):
   ```bash
   export GITHUB_TOKEN="your-test-token"
   export GITHUB_REPOSITORY="your-org/test-repo"
   
   python src/create_issue.py \
     --summary-file /tmp/summary.json \
     --issue-title "Test Issue" \
     --issue-labels "test"
   ```

### Integration Testing

1. **Create test workflow** in a separate repository:
   ```yaml
   name: Test Playwright Failure Bundler
   
   on: workflow_dispatch
   
   jobs:
     test:
       runs-on: ubuntu-latest
       permissions:
         issues: write
       steps:
         - uses: actions/checkout@v4
         - uses: your-org/playwright-failure-bundler@test-branch
           with:
             github-token: ${{ secrets.GITHUB_TOKEN }}
             issue-title: "Integration Test"
   ```

2. **Test different scenarios**:
   - Successful test runs (no failures)
   - Single failure
   - Multiple failures
   - Malformed reports
   - Permission errors

### Automated Testing

Set up CI/CD pipeline to test:

1. **Unit tests** on every commit
2. **Integration tests** on pull requests
3. **End-to-end tests** before releases
4. **Security scans** for vulnerabilities

## Troubleshooting

### Common Deployment Issues

#### Issue: Action not found in marketplace

**Causes:**
- Release not properly tagged
- Marketplace submission pending
- Repository visibility issues

**Solutions:**
1. Verify release tag exists and is public
2. Check marketplace submission status
3. Ensure repository is public (for marketplace)

#### Issue: Action fails in workflows

**Causes:**
- Missing dependencies
- Incorrect file paths
- Permission issues

**Solutions:**
1. Test action locally first
2. Check action.yml syntax
3. Verify all required files are included

#### Issue: Marketplace rejection

**Common reasons:**
- Security vulnerabilities
- Incomplete documentation
- Trademark issues
- Policy violations

**Solutions:**
1. Address security findings
2. Improve documentation
3. Review marketplace guidelines
4. Contact GitHub support if needed

### Debugging Deployment

1. **Enable debug logging**:
   ```yaml
   - uses: your-org/playwright-failure-bundler@v1
     with:
       github-token: ${{ secrets.GITHUB_TOKEN }}
     env:
       RUNNER_DEBUG: 1
   ```

2. **Check action logs** in workflow runs

3. **Validate action.yml**:
   ```bash
   # Check YAML syntax
   python -c "import yaml; yaml.safe_load(open('action.yml'))"
   ```

4. **Test dependencies**:
   ```bash
   pip install -r requirements.txt
   python -c "import requests; print('Dependencies OK')"
   ```

### Performance Optimization

1. **Minimize dependencies** in requirements.txt
2. **Use caching** for Python dependencies
3. **Optimize Docker images** if using containers
4. **Profile execution time** and optimize bottlenecks

### Security Considerations

1. **Scan for vulnerabilities**:
   ```bash
   pip install bandit
   bandit -r src/
   ```

2. **Review dependencies** for known issues:
   ```bash
   pip install safety
   safety check
   ```

3. **Follow security best practices**:
   - Never log sensitive information
   - Use minimal required permissions
   - Validate all inputs
   - Handle errors gracefully

## Maintenance

### Regular Updates

1. **Update dependencies** regularly
2. **Monitor security advisories**
3. **Test with new Playwright versions**
4. **Update documentation** as needed

### Community Support

1. **Monitor GitHub issues** for bug reports
2. **Respond to questions** and feature requests
3. **Review pull requests** from contributors
4. **Maintain changelog** and release notes

### Metrics and Analytics

Track action usage and performance:

1. **GitHub insights** for repository activity
2. **Marketplace analytics** for download stats
3. **Issue tracking** for common problems
4. **User feedback** for improvement opportunities

---

For additional support or questions about deployment, please:

- **Check the documentation** in the `docs/` directory
- **Search existing issues** on GitHub
- **Create a new issue** with detailed information
- **Join the discussion** in GitHub Discussions
