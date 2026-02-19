# GitHub Actions Workflows

This directory contains automated CI/CD workflows for the PySetItUp project.

## Workflows

### 1. CI Workflow (`ci.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

**Jobs:**

#### Lint & Format Check
- Runs `ruff format --check` to verify code formatting
- Runs `ruff check` for linting issues
- Runs `mypy` for type checking (non-blocking)

#### Test Suite
- Runs tests on Python 3.10, 3.11, and 3.12
- Generates coverage reports
- Uploads coverage to Codecov

#### Integration Tests
- Only runs on pull requests
- Requires Homebrew installation
- Runs integration tests (non-blocking)

#### Build Package
- Builds Python package distribution
- Validates package with `twine check`
- Uploads build artifacts

#### Security Scan
- Runs `safety` to check for vulnerable dependencies
- Runs `bandit` for security issues in code
- Non-blocking (warnings only)

### 2. PR Checks Workflow (`pr-checks.yml`)

**Triggers:**
- Pull request opened, synchronized, or reopened

**Jobs:**

#### PR Title Check
- Enforces conventional commit format
- Valid types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `ci`
- Subject must start with uppercase letter

#### PR Size Check
- Automatically labels PR by size:
  - `size/XS`: < 100 changes
  - `size/S`: < 300 changes
  - `size/M`: < 500 changes
  - `size/L`: < 1000 changes
  - `size/XL`: > 1000 changes
- Warns if PR is too large

#### Automated Code Review
- Checks for new TODO/FIXME comments
- Detects debug statements (print, console.log, debugger, pdb)
- Identifies large file changes

#### Test Coverage Report
- Generates coverage report
- Posts coverage comment on PR
- Minimum thresholds:
  - Green: 70%+
  - Orange: 50-70%
  - Red: < 50%

### 3. Release Workflow (`release.yml`)

**Triggers:**
- Push of version tags (e.g., `v1.0.0`)

**Jobs:**

#### Build and Release
- Builds distribution packages
- Creates GitHub release with auto-generated notes
- Publishes to PyPI (requires `PYPI_API_TOKEN` secret)

## Required Secrets

To use all workflow features, configure these secrets in your repository:

### Optional Secrets

- `CODECOV_TOKEN` - For uploading coverage reports to Codecov
- `PYPI_API_TOKEN` - For publishing releases to PyPI

### Setting Up Secrets

1. Go to repository Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add the required secrets

## Running Workflows Locally

### Format Check
```bash
ruff format --check .
```

### Linting
```bash
ruff check .
```

### Type Checking
```bash
mypy pysetitup
```

### Tests
```bash
pytest tests/unit/ -v --cov=pysetitup
```

### Build Package
```bash
python -m build
```

## Workflow Status Badges

Add these to your README.md:

```markdown
![CI](https://github.com/YOUR_USERNAME/pysetitup/workflows/CI/badge.svg)
![Tests](https://github.com/YOUR_USERNAME/pysetitup/workflows/Tests/badge.svg)
[![codecov](https://codecov.io/gh/YOUR_USERNAME/pysetitup/branch/main/graph/badge.svg)](https://codecov.io/gh/YOUR_USERNAME/pysetitup)
```

## Troubleshooting

### Failed Format Check
```bash
# Auto-fix formatting issues
ruff format .
```

### Failed Linting
```bash
# Auto-fix linting issues where possible
ruff check --fix .
```

### Failed Tests
```bash
# Run specific failing test
pytest tests/unit/path/to/test.py::test_name -v
```

### Build Errors
```bash
# Clean build artifacts
rm -rf dist/ build/ *.egg-info
python -m build
```

## Continuous Deployment

The release workflow automatically:
1. Creates a GitHub release with changelog
2. Uploads distribution files to GitHub
3. Publishes to PyPI (if tag is pushed and secrets are configured)

To create a release:
```bash
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```
