# pre-push.ps1
# Pre-Push Validation Script for MemoGraph
# Run this before every push: .\pre-push.ps1

Write-Host "`n🚀 Pre-Push Checks Starting...`n" -ForegroundColor Cyan

# Step 1: Syntax Check
Write-Host "1️⃣ Checking Python syntax..." -ForegroundColor Yellow
python -m compileall -q memograph/
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Syntax errors found! Fix them and try again." -ForegroundColor Red
    Write-Host "   Run: python -m compileall memograph/ (without -q) to see details`n" -ForegroundColor Gray
    exit 1
}
Write-Host "✅ Syntax check passed`n" -ForegroundColor Green

# Step 2: Run Tests
Write-Host "2️⃣ Running tests..." -ForegroundColor Yellow
pytest -q
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Tests failed! Fix failing tests and try again." -ForegroundColor Red
    Write-Host "   Run: pytest -v for detailed output`n" -ForegroundColor Gray
    exit 1
}
Write-Host "✅ All tests passed`n" -ForegroundColor Green

# Step 3: Pre-commit Hooks
Write-Host "3️⃣ Running pre-commit hooks..." -ForegroundColor Yellow
pre-commit run --all-files
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Pre-commit hooks made changes or found issues." -ForegroundColor Yellow
    Write-Host "   Review the changes, then stage and commit them." -ForegroundColor Gray
    Write-Host "   Run: git status to see what changed`n" -ForegroundColor Gray
    exit 1
}
Write-Host "✅ Pre-commit hooks passed`n" -ForegroundColor Green

# All checks passed
Write-Host "═══════════════════════════════════════════" -ForegroundColor Green
Write-Host "  🎉 All checks passed! Safe to push." -ForegroundColor Green
Write-Host "═══════════════════════════════════════════" -ForegroundColor Green
Write-Host "`nYou can now run: git push`n" -ForegroundColor Cyan

exit 0
