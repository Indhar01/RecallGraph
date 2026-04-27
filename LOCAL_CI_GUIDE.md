# Local CI Verification Guide

## Problem Statement

**Issue**: Pre-commit hooks pass locally but CI workflow fails in PR checks.

**Root Causes**:
1. Pre-commit hooks **auto-fix** issues (`--fix` flag), while CI only **checks** for issues
2. Pre-commit doesn't run **tests**, while CI runs comprehensive test suites
3. Pre-commit runs on **changed files**, while CI checks the **entire codebase**
4. Different tool configurations between local and CI environments

## Solution Overview

This guide provides multiple approaches to verify your code locally before pushing, ensuring it will pass CI checks.

---

## Quick Start: Run All CI Checks Locally

### Option 1: Use the Local CI Script (Recommended)

```powershell
# Run all CI checks (lint + tests)
.\scripts\run_ci_locally.ps1

# Run only linting checks
.\scripts\run_ci_locally.ps1 -LintOnly

# Run only tests
.\scripts\run_ci_locally.ps1 -TestOnly

# Skip stress tests (faster)
.\scripts\run_ci_locally.ps1 -SkipStress
```

### Option 2: Manual Commands

```powershell
# 1. Run ruff linter (CHECK mode - like CI)
ruff check .

# 2. Run ruff formatter check (CHECK mode - like CI)
ruff format --check .

# 3. Run mypy type checking
mypy memograph/ --config-file=pyproject.toml

# 4. Run tests with coverage
pytest --ignore=tests/stress/ --cov=memograph --cov-report=term

# 5. Check coverage threshold
coverage report --fail-under=40
```

---

## Understanding the Differences

### Pre-commit Hooks vs CI Workflow

| Aspect | Pre-commit Hooks | CI Workflow |
|--------|------------------|-------------|
| **Ruff Linter** | `ruff --fix` (auto-fixes) | `ruff check .` (only checks) |
| **Ruff Formatter** | `ruff format` (applies) | `ruff format --check` (only checks) |
| **Mypy** | Checks memograph/ | Checks memograph/ |
| **Tests** | ❌ Not run | ✅ Full test suite |
| **Coverage** | ❌ Not checked | ✅ Checked (40% threshold) |
| **Scope** | Changed files | Entire codebase |

### Why Pre-commit Passes but CI Fails

1. **Auto-fix masks issues**: Pre-commit fixes issues automatically, so you never see them. CI only checks and fails if issues exist.

2. **No test execution**: Pre-commit doesn't run tests. Your code might have:
   - Failing unit tests
   - Broken integration tests
   - Coverage below threshold
   - Performance regressions

3. **Incomplete checks**: Pre-commit might miss issues in files you didn't change but that are affected by your changes.

---

## Recommended Workflow

### Before Every Commit

```powershell
# 1. Let pre-commit auto-fix issues
git add .
pre-commit run --all-files

# 2. Review the changes pre-commit made
git diff

# 3. Commit if satisfied
git commit -m "Your commit message"
```

### Before Every Push

```powershell
# Run full CI checks locally
.\scripts\run_ci_locally.ps1

# If all checks pass, push
git push
```

### Alternative: Use Pre-push Hook (Automatic)

```powershell
# Set up automatic pre-push checks
.\scripts\setup_pre_push_hook.ps1

# Now every 'git push' will automatically run CI checks
git push  # Automatically runs checks before pushing
```

---

## Detailed Check Explanations

### 1. Ruff Linter Check

**What it does**: Checks code for style issues, bugs, and anti-patterns

```powershell
# CI command (check only)
ruff check .

# Pre-commit command (auto-fix)
ruff check --fix .
```

**Common failures**:
- Unused imports (F401)
- Undefined names (F821)
- Line too long (E501) - though handled by formatter
- Unused variables (F841)

### 2. Ruff Formatter Check

**What it does**: Ensures code is properly formatted

```powershell
# CI command (check only)
ruff format --check .

# Pre-commit command (apply formatting)
ruff format .
```

**Common failures**:
- Inconsistent indentation
- Missing/extra blank lines
- Inconsistent quote styles

### 3. Mypy Type Checking

**What it does**: Validates type annotations

```powershell
mypy memograph/ --config-file=pyproject.toml
```

**Common failures**:
- Missing type annotations
- Type mismatches
- Invalid type usage

**Note**: Many modules have `ignore_errors = true` in pyproject.toml, so mypy failures are often non-blocking.

### 4. Test Suite

**What it does**: Runs all unit, integration, and performance tests

```powershell
# Run all tests (excluding stress tests)
pytest --ignore=tests/stress/ --cov=memograph --cov-report=term

# Run specific test categories
pytest tests/test_kernel.py -v
pytest tests/integration_suite/ -v
```

**Common failures**:
- Broken functionality
- API changes without updating tests
- Missing test coverage
- Performance regressions

### 5. Coverage Check

**What it does**: Ensures code coverage meets minimum threshold (40%)

```powershell
coverage report --fail-under=40
```

**Common failures**:
- New code without tests
- Deleted tests without updating coverage

---

## CI Workflow Jobs Explained

The CI workflow runs multiple jobs in parallel:

### 1. **lint** Job
- Runs ruff linter (check mode)
- Runs ruff formatter (check mode)
- Runs mypy type checking
- **Fast**: ~1-2 minutes

### 2. **test** Job
- Runs on multiple OS (Ubuntu, Windows, macOS)
- Tests Python 3.10, 3.11, 3.12
- Runs full test suite with coverage
- **Slow**: ~5-10 minutes per matrix combination

### 3. **test-enhanced** Job
- Tests enhanced modules specifically
- Validates cache, validation, graph enhancements
- **Medium**: ~3-5 minutes

### 4. **performance** Job
- Runs performance regression tests
- Benchmarks critical operations
- **Medium**: ~3-5 minutes
- **Note**: `continue-on-error: true` (non-blocking)

### 5. **integration** Job
- Tests backward compatibility
- Tests cache integration
- Tests validation integration
- **Medium**: ~3-5 minutes

### 6. **pre-commit** Job
- Runs pre-commit hooks on all files
- **Fast**: ~1-2 minutes
- **Note**: `continue-on-error: true` (non-blocking)

### 7. **quality-gates** Job
- Final quality check
- Runs after all other jobs
- Generates coverage report
- **Fast**: ~2-3 minutes

---

## Troubleshooting

### "Ruff check passes locally but fails in CI"

**Cause**: You're running `ruff check --fix` locally (auto-fixes), but CI runs `ruff check .` (check only)

**Solution**:
```powershell
# Run in check mode (like CI)
ruff check .

# If issues found, fix them
ruff check --fix .

# Verify again
ruff check .
```

### "Tests pass locally but fail in CI"

**Possible causes**:
1. **Environment differences**: CI uses clean environment
2. **Missing dependencies**: Check `pyproject.toml` [dev] dependencies
3. **OS-specific issues**: CI tests on Linux, Windows, macOS
4. **Timing issues**: CI might be slower/faster than local

**Solution**:
```powershell
# Recreate clean environment
python -m venv .venv-test
.\.venv-test\Scripts\Activate.ps1
pip install -e ".[dev,all]"

# Run tests
pytest --ignore=tests/stress/ --cov=memograph
```

### "Coverage fails in CI but not locally"

**Cause**: Different files being tested or coverage configuration

**Solution**:
```powershell
# Run coverage exactly like CI
pytest --ignore=tests/stress/ --cov=memograph --cov-report=term
coverage report --fail-under=40

# Check which files are missing coverage
coverage report --show-missing
```

### "Mypy passes locally but fails in CI"

**Cause**: Different mypy versions or configuration

**Solution**:
```powershell
# Update mypy
pip install --upgrade mypy

# Run mypy exactly like CI
mypy memograph/ --config-file=pyproject.toml

# Check mypy version
mypy --version
```

---

## Best Practices

### 1. Run Checks Before Committing
```powershell
# Quick pre-commit check
pre-commit run --all-files
```

### 2. Run Full CI Before Pushing
```powershell
# Comprehensive check
.\scripts\run_ci_locally.ps1
```

### 3. Use Pre-push Hook for Automation
```powershell
# One-time setup
.\scripts\setup_pre_push_hook.ps1

# Now automatic on every push
git push
```

### 4. Fix Issues Incrementally
- Don't accumulate issues
- Fix linting issues immediately
- Write tests as you code
- Run checks frequently

### 5. Understand CI Feedback
- Read CI logs carefully
- Identify which job failed
- Reproduce locally
- Fix and verify

---

## Quick Reference

### Essential Commands

```powershell
# Full CI simulation
.\scripts\run_ci_locally.ps1

# Lint only
ruff check .
ruff format --check .
mypy memograph/ --config-file=pyproject.toml

# Test only
pytest --ignore=tests/stress/ --cov=memograph

# Coverage check
coverage report --fail-under=40

# Pre-commit
pre-commit run --all-files
```

### File Locations

- **CI Workflow**: `.github/workflows/ci.yml`
- **Pre-commit Config**: `.pre-commit-config.yaml`
- **Pytest Config**: `pyproject.toml` → `[tool.pytest.ini_options]`
- **Ruff Config**: `pyproject.toml` → `[tool.ruff]`
- **Mypy Config**: `pyproject.toml` → `[tool.mypy]`
- **Coverage Config**: `pyproject.toml` → `[tool.coverage]`

---

## Testing Multiple Python Versions Locally

### Understanding CI's Multi-Version Testing

**What CI Does:**
- Tests on **3 operating systems**: Ubuntu (Linux), Windows, macOS
- Tests on **3 Python versions**: 3.10, 3.11, 3.12
- Runs **9 combinations** in parallel (3 OS × 3 Python versions)

**What Local Script Does:**
- Tests on **your current OS only** (e.g., Windows)
- Tests on **your current Python version only** (e.g., 3.10)
- Catches ~95% of issues, but OS/version-specific issues may still appear in CI

### Testing Multiple Python Versions Locally

#### Option 1: Using pyenv (Recommended for Linux/macOS)

```bash
# Install pyenv (if not already installed)
curl https://pyenv.run | bash

# Install multiple Python versions
pyenv install 3.10.13
pyenv install 3.11.8
pyenv install 3.12.2

# Test with Python 3.10
pyenv shell 3.10.13
python -m venv .venv-310
.venv-310\Scripts\Activate.ps1  # Windows
source .venv-310/bin/activate   # Linux/macOS
pip install -e ".[dev,all]"
.\scripts\run_ci_locally.ps1

# Test with Python 3.11
pyenv shell 3.11.8
python -m venv .venv-311
.venv-311\Scripts\Activate.ps1
pip install -e ".[dev,all]"
.\scripts\run_ci_locally.ps1

# Test with Python 3.12
pyenv shell 3.12.2
python -m venv .venv-312
.venv-312\Scripts\Activate.ps1
pip install -e ".[dev,all]"
.\scripts\run_ci_locally.ps1
```

#### Option 2: Using py launcher (Windows)

```powershell
# List installed Python versions
py --list

# Test with Python 3.10
py -3.10 -m venv .venv-310
.\.venv-310\Scripts\Activate.ps1
pip install -e ".[dev,all]"
.\scripts\run_ci_locally.ps1

# Test with Python 3.11
py -3.11 -m venv .venv-311
.\.venv-311\Scripts\Activate.ps1
pip install -e ".[dev,all]"
.\scripts\run_ci_locally.ps1

# Test with Python 3.12
py -3.12 -m venv .venv-312
.\.venv-312\Scripts\Activate.ps1
pip install -e ".[dev,all]"
.\scripts\run_ci_locally.ps1
```

#### Option 3: Using tox (Automated Multi-Version Testing)

Create `tox.ini` in project root:

```ini
[tox]
envlist = py310,py311,py312
skipsdist = False

[testenv]
deps =
    -e.[dev,all]
commands =
    ruff check .
    ruff format --check .
    mypy memograph/ --config-file=pyproject.toml
    pytest --ignore=tests/stress/ --cov=memograph
```

Then run:

```powershell
# Install tox
pip install tox

# Test all Python versions
tox

# Test specific version
tox -e py310
tox -e py311
tox -e py312
```

#### Option 4: Manual Script for Multiple Versions

Create `scripts/test_all_python_versions.ps1`:

```powershell
#!/usr/bin/env pwsh
$pythonVersions = @("3.10", "3.11", "3.12")
$failed = @()

foreach ($version in $pythonVersions) {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "Testing Python $version" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan

    $pythonCmd = "py -$version"

    # Check if version is available
    $available = & $pythonCmd --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Python $version not installed, skipping..." -ForegroundColor Yellow
        continue
    }

    # Create virtual environment
    $venvPath = ".venv-$($version.Replace('.', ''))"
    & $pythonCmd -m venv $venvPath

    # Activate and test
    & "$venvPath\Scripts\Activate.ps1"
    pip install -e ".[dev,all]" -q

    .\scripts\run_ci_locally.ps1 -Fast

    if ($LASTEXITCODE -ne 0) {
        $failed += $version
    }

    deactivate
}

if ($failed.Count -gt 0) {
    Write-Host "`nFailed on Python versions: $($failed -join ', ')" -ForegroundColor Red
    exit 1
} else {
    Write-Host "`nAll Python versions passed!" -ForegroundColor Green
    exit 0
}
```

### Testing on Different Operating Systems

#### Option 1: Using Docker (Test Linux locally)

Create `Dockerfile.test`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY . .

RUN pip install -e ".[dev,all]"

CMD ["pytest", "--ignore=tests/stress/", "--cov=memograph"]
```

Run tests in Linux container:

```powershell
# Build image
docker build -f Dockerfile.test -t memograph-test .

# Run tests
docker run --rm memograph-test

# Run with different Python versions
docker build -f Dockerfile.test --build-arg PYTHON_VERSION=3.11 -t memograph-test-311 .
docker run --rm memograph-test-311
```

#### Option 2: Using GitHub Actions Locally (act)

```powershell
# Install act (GitHub Actions local runner)
# Windows: choco install act-cli
# macOS: brew install act
# Linux: curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run CI workflow locally
act -j test

# Run specific job
act -j lint
act -j test-enhanced
```

### Practical Recommendations

**For Most Developers:**
1. ✅ Run `.\scripts\run_ci_locally.ps1` on your current Python version
2. ✅ Let CI test other OS/Python combinations
3. ✅ Only test multiple versions locally if you're changing core functionality

**For Critical Changes:**
1. Test with at least Python 3.10 and 3.12 (min and max supported)
2. Use tox for automated multi-version testing
3. Consider Docker for Linux testing if on Windows

**For Release Managers:**
1. Test all Python versions (3.10, 3.11, 3.12)
2. Test on at least 2 operating systems
3. Run full test suite (not just fast mode)

### Common Multi-Version Issues

**Import Compatibility:**
```python
# Python 3.10+ only
from typing import TypeAlias  # ❌ Fails on 3.9

# Compatible with 3.9+
from typing_extensions import TypeAlias  # ✅ Works everywhere
```

**Syntax Changes:**
```python
# Python 3.10+ only
match value:  # ❌ Fails on 3.9
    case 1: ...

# Compatible approach
if value == 1:  # ✅ Works everywhere
    ...
```

**Library Version Differences:**
- Some dependencies may behave differently across Python versions
- Always test with the minimum supported version (3.10)

## Summary

**The Problem**: Pre-commit auto-fixes issues and doesn't run tests, while CI only checks and runs comprehensive tests.

**The Solution**: Run CI checks locally before pushing using the provided script or manual commands.

**The Workflow**:
1. **Commit**: Let pre-commit auto-fix issues
2. **Before Push**: Run `.\scripts\run_ci_locally.ps1`
3. **Push**: Only if all checks pass

**OS/Version Testing**:
- Local script tests **your current OS and Python version only**
- CI tests **3 OS × 3 Python versions = 9 combinations**
- For critical changes, test multiple Python versions locally using tox or manual scripts
- Most issues are caught by single-version testing; let CI handle the rest

**The Result**: No more surprises in CI! 🎉
