"""Quick automated test for new CLI commands."""

import subprocess
import sys
import os
import json
from pathlib import Path

os.chdir(Path(__file__).parent)

def run(cmd):
    """Run command and return success status."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

print("🧪 Quick Test Suite for New CLI Commands\n")

# Test 1: batch-create (dry-run)
print("1️⃣ Testing batch-create (dry-run)...")
success, out, err = run("python -m memograph --vault test_vault batch-create test_data/sample_memories.json --dry-run")
if success and "DRY RUN" in out:
    print("   ✅ batch-create dry-run works")
else:
    print(f"   ❌ batch-create dry-run failed: {err}")

# Test 2: batch-create (actual)
print("2️⃣ Testing batch-create (actual)...")
success, out, err = run("python -m memograph --vault test_vault batch-create test_data/sample_memories.json --auto-ingest")
if success and "Created:" in out:
    print("   ✅ batch-create works")
else:
    print(f"   ❌ batch-create failed: {err}")

# Test 3: list
print("3️⃣ Testing list...")
success, out, err = run("python -m memograph --vault test_vault list")
if success:
    print("   ✅ list works")
else:
    print(f"   ❌ list failed: {err}")

# Test 4: stats
print("4️⃣ Testing stats...")
success, out, err = run("python -m memograph --vault test_vault stats")
if success and "Total Memories:" in out:
    print("   ✅ stats works")
else:
    print(f"   ❌ stats failed: {err}")

# Test 5: export
print("5️⃣ Testing export...")
success, out, err = run("python -m memograph --vault test_vault export --output test_export.json --format json")
if success and Path("test_export.json").exists():
    print("   ✅ export works")
    Path("test_export.json").unlink()  # cleanup
else:
    print(f"   ❌ export failed: {err}")

# Test 6: backup
print("6️⃣ Testing backup...")
Path("test_backups").mkdir(exist_ok=True)
success, out, err = run("python -m memograph --vault test_vault backup --destination test_backups")
if success and "Backup created:" in out:
    print("   ✅ backup works")
else:
    print(f"   ❌ backup failed: {err}")

# Test 7: config set/get
print("7️⃣ Testing config...")
success1, _, _ = run("python -m memograph config set test_key test_value")
success2, out, _ = run("python -m memograph config get test_key")
if success1 and success2 and "test_value" in out:
    print("   ✅ config works")
else:
    print("   ❌ config failed")

# Test 8: batch-update (dry-run)
print("8️⃣ Testing batch-update...")
success, out, err = run("python -m memograph --vault test_vault batch-update --filter-tags python --set-salience 0.95 --dry-run")
if success and "DRY RUN" in out:
    print("   ✅ batch-update works")
else:
    print(f"   ❌ batch-update failed: {err}")

# Test 9: batch-delete (dry-run)
print("9️⃣ Testing batch-delete...")
success, out, err = run("python -m memograph --vault test_vault batch-delete --filter-tags nonexistent --dry-run")
if success:
    print("   ✅ batch-delete works")
else:
    print(f"   ❌ batch-delete failed: {err}")

# Test 10: import-backup
print("🔟 Testing import-backup...")
if Path("test_backups").exists():
    backups = list(Path("test_backups").glob("*.zip"))
    if backups:
        Path("test_vault_restore").mkdir(exist_ok=True)
        success, out, err = run(f"python -m memograph --vault test_vault_restore import-backup {backups[0]}")
        if success and "Imported:" in out:
            print("   ✅ import-backup works")
        else:
            print(f"   ❌ import-backup failed: {err}")
    else:
        print("   ⚠️ No backup file to test import")
else:
    print("   ⚠️ No backup directory")

print("\n" + "="*50)
print("✅ All basic tests completed!")
print("\nFor detailed testing, see: test_data/MANUAL_TEST_GUIDE.md")
print("For cleanup, run: python -c \"import shutil; shutil.rmtree('test_vault', ignore_errors=True); shutil.rmtree('test_vault_restore', ignore_errors=True); shutil.rmtree('test_backups', ignore_errors=True)\"")
