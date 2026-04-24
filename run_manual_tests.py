"""
Manual test runner for new CLI commands.
Run this script to test all new commands step by step.
"""

import subprocess
import sys
import os
from pathlib import Path

# Ensure we're in the right directory
os.chdir(Path(__file__).parent)

def run_command(cmd, description):
    """Run a command and display results."""
    print(f"\n{'='*60}")
    print(f"TEST: {description}")
    print(f"CMD:  {cmd}")
    print('='*60)
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        print(f"Exit Code: {result.returncode}")
        
        if result.returncode == 0:
            print("✅ SUCCESS")
        else:
            print("❌ FAILED")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("⏱️ TIMEOUT")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    """Run all manual tests."""
    
    print("="*60)
    print("MemoGraph CLI - Manual Test Suite")
    print("="*60)
    
    tests = [
        # Test 1: Verify commands are registered
        (
            "python -m memograph --help",
            "Verify all commands are in help"
        ),
        
        # Test 2: batch-create (dry-run)
        (
            "python -m memograph --vault test_vault batch-create test_data/sample_memories.json --dry-run",
            "Batch create from JSON (dry-run)"
        ),
        
        # Test 3: batch-create (actual)
        (
            "python -m memograph --vault test_vault batch-create test_data/sample_memories.json --auto-ingest",
            "Batch create from JSON (actual)"
        ),
        
        # Test 4: list memories
        (
            "python -m memograph --vault test_vault list",
            "List all memories"
        ),
        
        # Test 5: stats
        (
            "python -m memograph --vault test_vault stats",
            "Show vault statistics"
        ),
        
        # Test 6: export to JSON
        (
            "python -m memograph --vault test_vault export --output test_export.json --format json",
            "Export vault to JSON"
        ),
        
        # Test 7: config set
        (
            "python -m memograph config set test_key test_value",
            "Set config value"
        ),
        
        # Test 8: config get
        (
            "python -m memograph config get test_key",
            "Get config value"
        ),
        
        # Test 9: config list
        (
            "python -m memograph config list",
            "List all config"
        ),
    ]
    
    results = []
    for cmd, desc in tests:
        success = run_command(cmd, desc)
        results.append((desc, success))
        
        # Pause between tests
        input("\nPress Enter to continue to next test...")
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for desc, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {desc}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")

if __name__ == "__main__":
    main()
