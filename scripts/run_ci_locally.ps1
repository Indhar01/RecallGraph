#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Run CI checks locally before pushing to ensure they pass in GitHub Actions.

.DESCRIPTION
    This script simulates the GitHub Actions CI workflow locally, running the same
    checks that will be executed in the CI pipeline. This helps catch issues before
    pushing and avoids failed PR checks.

.PARAMETER LintOnly
    Run only linting checks (ruff, mypy) without tests.

.PARAMETER TestOnly
    Run only tests without linting checks.

.PARAMETER SkipStress
    Skip stress tests (default behavior, matches CI).

.PARAMETER SkipCoverage
    Skip coverage threshold check.

.PARAMETER Verbose
    Show detailed output from all commands.

.PARAMETER Fast
    Run only essential checks (lint + basic tests).

.EXAMPLE
    .\scripts\run_ci_locally.ps1
    Run all CI checks (default)

.EXAMPLE
    .\scripts\run_ci_locally.ps1 -LintOnly
    Run only linting checks

.EXAMPLE
    .\scripts\run_ci_locally.ps1 -Fast
    Run essential checks quickly

.NOTES
    This script matches the checks in .github/workflows/ci.yml
    Make sure you have all dev dependencies installed: pip install -e ".[dev,all]"
#>

[CmdletBinding()]
param(
    [Parameter(HelpMessage="Run only linting checks")]
    [switch]$LintOnly,

    [Parameter(HelpMessage="Run only tests")]
    [switch]$TestOnly,

    [Parameter(HelpMessage="Skip stress tests (default)")]
    [switch]$SkipStress = $true,

    [Parameter(HelpMessage="Skip coverage threshold check")]
    [switch]$SkipCoverage,

    [Parameter(HelpMessage="Show detailed output")]
    [switch]$ShowDetails,

    [Parameter(HelpMessage="Run only essential checks")]
    [switch]$Fast
)

# Color output functions
function Write-Success {
    param([string]$Message)
    Write-Host "SUCCESS: $Message" -ForegroundColor Green
}

function Write-Failure {
    param([string]$Message)
    Write-Host "FAILED: $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "INFO: $Message" -ForegroundColor Cyan
}

function Write-Warning {
    param([string]$Message)
    Write-Host "WARNING: $Message" -ForegroundColor Yellow
}

function Write-Section {
    param([string]$Message)
    Write-Host "`n=======================================================" -ForegroundColor Blue
    Write-Host "  $Message" -ForegroundColor Blue
    Write-Host "=======================================================`n" -ForegroundColor Blue
}

# Track results
$script:FailedChecks = @()
$script:PassedChecks = @()
$script:SkippedChecks = @()

function Add-Result {
    param(
        [string]$CheckName,
        [bool]$Success,
        [string]$Message = ""
    )

    if ($Success) {
        $script:PassedChecks += $CheckName
        Write-Success "$CheckName passed"
    } else {
        $script:FailedChecks += $CheckName
        Write-Failure "$CheckName failed"
        if ($Message) {
            Write-Host "  $Message" -ForegroundColor Yellow
        }
    }
}

function Add-Skipped {
    param([string]$CheckName)
    $script:SkippedChecks += $CheckName
    Write-Warning "$CheckName skipped"
}

# Check if we're in the project root
if (-not (Test-Path "pyproject.toml")) {
    Write-Failure "Not in project root directory. Please run from the MemoGraph root."
    exit 1
}

# Check if virtual environment is activated
if (-not $env:VIRTUAL_ENV) {
    Write-Warning "Virtual environment not activated. Attempting to activate..."
    if (Test-Path ".venv\Scripts\Activate.ps1") {
        & .\.venv\Scripts\Activate.ps1
        Write-Success "Virtual environment activated"
    } else {
        Write-Failure "Virtual environment not found. Please create one: python -m venv .venv"
        exit 1
    }
}

# Check if dependencies are installed
Write-Info "Checking dependencies..."
$requiredPackages = @("ruff", "mypy", "pytest", "pytest-cov")
$missingPackages = @()

foreach ($package in $requiredPackages) {
    $result = pip show $package 2>$null
    if (-not $result) {
        $missingPackages += $package
    }
}

if ($missingPackages.Count -gt 0) {
    Write-Failure "Missing required packages: $($missingPackages -join ', ')"
    Write-Info "Install with: pip install -e `".[dev,all]`""
    exit 1
}

Write-Success "All required dependencies found"

# Start timing
$startTime = Get-Date

Write-Section "Starting Local CI Checks"
Write-Info "Simulating GitHub Actions CI workflow"
Write-Info "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

# LINTING CHECKS
if (-not $TestOnly) {
    Write-Section "Linting Checks"

    # 1. Ruff Linter
    Write-Info "Running ruff linter (check mode)..."
    $ruffLintOutput = ruff check . 2>&1
    $ruffLintSuccess = $LASTEXITCODE -eq 0

    if ($ShowDetails -or -not $ruffLintSuccess) {
        Write-Host $ruffLintOutput
    }

    Add-Result -CheckName "Ruff Linter" -Success $ruffLintSuccess -Message "Run 'ruff check --fix .' to auto-fix issues"

    # 2. Ruff Formatter
    Write-Info "Running ruff formatter check..."
    $ruffFormatOutput = ruff format --check . 2>&1
    $ruffFormatSuccess = $LASTEXITCODE -eq 0

    if ($ShowDetails -or -not $ruffFormatSuccess) {
        Write-Host $ruffFormatOutput
    }

    Add-Result -CheckName "Ruff Formatter" -Success $ruffFormatSuccess -Message "Run 'ruff format .' to apply formatting"

    # 3. Mypy Type Checking
    Write-Info "Running mypy type checking..."
    $mypyOutput = mypy memograph/ --config-file=pyproject.toml 2>&1
    $mypySuccess = $LASTEXITCODE -eq 0

    if ($ShowDetails -or -not $mypySuccess) {
        Write-Host $mypyOutput
    }

    if ($mypySuccess) {
        Add-Result -CheckName "Mypy" -Success $true
    } else {
        Write-Warning "Mypy found issues (non-blocking in CI)"
        Add-Result -CheckName "Mypy" -Success $true -Message "Type checking issues found but non-blocking"
    }
}

# TEST CHECKS
if (-not $LintOnly) {
    Write-Section "Test Suite"

    if ($Fast) {
        Write-Info "Running essential tests only (fast mode)..."
        $testArgs = @(
            "tests/test_kernel.py",
            "tests/test_graph_enhanced.py",
            "tests/test_cache_enhanced.py",
            "-v"
        )
    } else {
        Write-Info "Running full test suite..."
        $testArgs = @(
            "--ignore=tests/stress/",
            "--cov=memograph",
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-report=xml"
        )

        if ($ShowDetails) {
            $testArgs += "-v"
        }
    }

    $testOutput = pytest @testArgs 2>&1
    $testSuccess = $LASTEXITCODE -eq 0

    if ($ShowDetails -or -not $testSuccess) {
        Write-Host $testOutput
    }

    Add-Result -CheckName "Test Suite" -Success $testSuccess -Message "Check test output above for details"

    # Coverage threshold check
    if (-not $SkipCoverage -and -not $Fast) {
        Write-Info "Checking coverage threshold (40%)..."
        $coverageOutput = coverage report --fail-under=40 2>&1
        $coverageSuccess = $LASTEXITCODE -eq 0

        if ($ShowDetails -or -not $coverageSuccess) {
            Write-Host $coverageOutput
        }

        Add-Result -CheckName "Coverage Threshold" -Success $coverageSuccess -Message "Coverage below 40% threshold"
    } elseif ($Fast) {
        Add-Skipped -CheckName "Coverage Threshold (fast mode)"
    } else {
        Add-Skipped -CheckName "Coverage Threshold (--SkipCoverage)"
    }
}

# ENHANCED MODULE TESTS
if (-not $LintOnly -and -not $Fast) {
    Write-Section "Enhanced Module Tests"

    Write-Info "Running enhanced module tests..."
    $enhancedTests = @(
        "tests/test_cache_enhanced.py",
        "tests/test_validation.py",
        "tests/test_graph_enhanced.py",
        "tests/test_kernel_enhanced.py"
    )

    $enhancedOutput = pytest @enhancedTests -v --cov=memograph.core --cov=memograph.storage --cov-report=term 2>&1
    $enhancedSuccess = $LASTEXITCODE -eq 0

    if ($ShowDetails -or -not $enhancedSuccess) {
        Write-Host $enhancedOutput
    }

    Add-Result -CheckName "Enhanced Modules" -Success $enhancedSuccess
}

# INTEGRATION TESTS
if (-not $LintOnly -and -not $Fast) {
    Write-Section "Integration Tests"

    Write-Info "Running integration tests..."
    $integrationTests = @(
        "tests/test_kernel_enhanced.py::TestBackwardCompatibility",
        "tests/test_kernel_enhanced.py::TestCacheManagement",
        "tests/test_kernel_enhanced.py::TestRememberWithValidation",
        "tests/test_kernel_enhanced.py::TestRetrieveWithCaching"
    )

    $integrationOutput = pytest @integrationTests -v 2>&1
    $integrationSuccess = $LASTEXITCODE -eq 0

    if ($ShowDetails -or -not $integrationSuccess) {
        Write-Host $integrationOutput
    }

    Add-Result -CheckName "Integration Tests" -Success $integrationSuccess
}

# PRE-COMMIT HOOKS
if (-not $TestOnly -and -not $Fast) {
    Write-Section "Pre-commit Hooks"

    Write-Info "Running pre-commit hooks on all files..."
    $precommitOutput = pre-commit run --all-files 2>&1
    $precommitSuccess = $LASTEXITCODE -eq 0

    if ($ShowDetails -or -not $precommitSuccess) {
        Write-Host $precommitOutput
    }

    if ($precommitSuccess) {
        Add-Result -CheckName "Pre-commit Hooks" -Success $true
    } else {
        Write-Warning "Pre-commit hooks found issues (non-blocking in CI)"
        Add-Result -CheckName "Pre-commit Hooks" -Success $true -Message "Pre-commit issues found but non-blocking"
    }
}

# SUMMARY
$endTime = Get-Date
$duration = $endTime - $startTime

Write-Section "Summary"

Write-Host "Duration: $($duration.ToString('mm\:ss'))" -ForegroundColor Cyan
Write-Host ""

if ($script:PassedChecks.Count -gt 0) {
    Write-Host "Passed Checks ($($script:PassedChecks.Count)):" -ForegroundColor Green
    foreach ($check in $script:PassedChecks) {
        Write-Host "  [PASS] $check" -ForegroundColor Green
    }
    Write-Host ""
}

if ($script:SkippedChecks.Count -gt 0) {
    Write-Host "Skipped Checks ($($script:SkippedChecks.Count)):" -ForegroundColor Yellow
    foreach ($check in $script:SkippedChecks) {
        Write-Host "  [SKIP] $check" -ForegroundColor Yellow
    }
    Write-Host ""
}

if ($script:FailedChecks.Count -gt 0) {
    Write-Host "Failed Checks ($($script:FailedChecks.Count)):" -ForegroundColor Red
    foreach ($check in $script:FailedChecks) {
        Write-Host "  [FAIL] $check" -ForegroundColor Red
    }
    Write-Host ""

    Write-Section "CI Checks Failed"
    Write-Failure "Some checks failed. Please fix the issues before pushing."
    Write-Info "Review the output above for details on what failed."
    Write-Info "Common fixes:"
    Write-Host "  - Ruff issues: ruff check --fix ." -ForegroundColor Cyan
    Write-Host "  - Format issues: ruff format ." -ForegroundColor Cyan
    Write-Host "  - Test failures: Review test output and fix code" -ForegroundColor Cyan
    Write-Host "  - Coverage: Add tests for uncovered code" -ForegroundColor Cyan

    exit 1
} else {
    Write-Section "All CI Checks Passed"
    Write-Success "Your code is ready to push. CI should pass in GitHub Actions."
    Write-Info "You can now safely run: git push"

    exit 0
}
