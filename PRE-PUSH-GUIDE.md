# Pre-Push Checklist Guide

## 🚀 Quick Start

Before every `git push`, simply run:

```powershell
.\pre-push.ps1
```

If all checks pass, you'll see:
```
🎉 All checks passed! Safe to push.
```

Then you can safely push:
```powershell
git push
```

---

## 🔍 What It Checks

The script runs three essential checks:

1. **Syntax Check** - Ensures no Python syntax errors
2. **Tests** - Runs all unit tests with pytest
3. **Pre-commit Hooks** - Runs linting, formatting, and other quality checks

---

## ❌ If Checks Fail

### Syntax Errors
```powershell
# See detailed syntax errors
python -m compileall memograph/
```

### Test Failures
```powershell
# See detailed test output
pytest -v

# Run specific test
pytest tests/test_kernel.py -v
```

### Pre-commit Issues
```powershell
# Review what changed
git status
git diff

# If pre-commit auto-fixed files, stage and commit them
git add -u
git commit -m "style: Auto-format code"
```

---

## 🎯 Workflow

```
1. Write code
2. Save changes
3. Run: .\pre-push.ps1
4. If pass → git push
5. If fail → fix issues → go to step 3
```

---

## 💡 Pro Tips

### Create an Alias
Add to your PowerShell profile:
```powershell
function Check { .\pre-push.ps1 }
```
Now just type: `Check`

### Skip in Emergency (Not Recommended)
```powershell
git push --no-verify  # Skips hooks
```

### First Time Setup
```powershell
# Install pre-commit hooks
pre-commit install

# Test the script
.\pre-push.ps1
```

---

## 📞 Need Help?

If the script doesn't work:
1. Ensure Python is installed: `python --version`
2. Ensure pytest is installed: `pytest --version`
3. Ensure pre-commit is installed: `pre-commit --version`

Install missing tools:
```powershell
pip install pytest pre-commit
```

---

## 🔧 Customize

Edit `pre-push.ps1` to add/remove checks based on your needs.

The script is in your project root directory.
