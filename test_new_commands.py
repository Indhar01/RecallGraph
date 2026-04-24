"""Quick test to verify new CLI commands are registered."""

import sys
from memograph.cli import main

# Capture help output
import io
from contextlib import redirect_stdout

# Test if new commands are in help
sys.argv = ["memograph", "--help"]

try:
    f = io.StringIO()
    with redirect_stdout(f):
        try:
            main()
        except SystemExit:
            pass

    help_output = f.getvalue()

    # Check for new commands
    new_commands = [
        "batch-create",
        "batch-update",
        "batch-delete",
        "export",
        "import-backup",
        "backup",
        "config",
        "stats",
    ]

    print("=== Checking New Commands ===\n")

    all_found = True
    for cmd in new_commands:
        if cmd in help_output:
            print(f"✓ {cmd:20} - Found")
        else:
            print(f"✗ {cmd:20} - NOT FOUND")
            all_found = False

    print("\n" + "=" * 40)
    if all_found:
        print("✅ All 8 new commands registered successfully!")
    else:
        print("❌ Some commands missing from CLI")

    print("\nTotal commands in help:", help_output.count("  {"))

except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
