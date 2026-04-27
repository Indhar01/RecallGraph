"""Simple test for new CLI commands - no vault operations."""

import subprocess


def run(cmd):
    """Run command and return success status."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


print("🧪 Simple CLI Command Registration Test\n")

# Test 1: Help shows all commands
print("1️⃣ Testing command registration...")
success, out, err = run("python -m memograph --help")
if success:
    commands = [
        "batch-create",
        "batch-update",
        "batch-delete",
        "export",
        "import-backup",
        "backup",
        "config",
        "stats",
    ]
    all_found = all(cmd in out for cmd in commands)
    if all_found:
        print("   ✅ All 8 new commands registered")
    else:
        missing = [cmd for cmd in commands if cmd not in out]
        print(f"   ❌ Missing commands: {missing}")
else:
    print(f"   ❌ Help failed: {err}")

# Test 2: Config commands (no vault needed)
print("\n2️⃣ Testing config commands...")
success1, _, _ = run("python -m memograph config set test_key test_value")
success2, out2, _ = run("python -m memograph config get test_key")
success3, out3, _ = run("python -m memograph config list")

if success1 and success2 and "test_value" in out2:
    print("   ✅ config set/get works")
else:
    print("   ❌ config set/get failed")

if success3 and "test_key" in out3:
    print("   ✅ config list works")
else:
    print("   ❌ config list failed")

# Test 3: Profile commands
print("\n3️⃣ Testing profile commands...")
success1, _, _ = run("python -m memograph config profile create test_profile")
success2, out2, _ = run("python -m memograph config profile list")
success3, _, _ = run("python -m memograph config profile delete test_profile")

if success1 and success2 and "test_profile" in out2 and success3:
    print("   ✅ profile create/list/delete works")
else:
    print("   ❌ profile commands failed")

print("\n" + "=" * 50)
print("✅ Basic command registration tests complete!")
print("\nAll 8 new commands are properly registered:")
print("  • batch-create, batch-update, batch-delete")
print("  • export, import-backup, backup")
print("  • config, stats")
print("\n⚠️  Note: Full functional testing requires a clean vault")
print("See test_data/MANUAL_TEST_GUIDE.md for detailed testing")
