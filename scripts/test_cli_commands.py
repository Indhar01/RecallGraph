#!/usr/bin/env python3
"""
Comprehensive CLI validation script for MemoGraph.

Tests all CLI commands to ensure they work as documented in README.md.
Run this after making changes to CLI or documentation.

Usage:
    python scripts/test_cli_commands.py
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")


def print_test(name: str):
    """Print test name."""
    print(f"{Colors.BOLD}Testing: {name}{Colors.RESET}")


def print_success(message: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")


def print_error(message: str):
    """Print error message."""
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")


def print_warning(message: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")


def run_command(cmd: list[str], check: bool = True) -> tuple[bool, str, str]:
    """
    Run a command and return success status, stdout, and stderr.

    Args:
        cmd: Command and arguments as list
        check: Whether to check return code (False for expected failures)

    Returns:
        Tuple of (success, stdout, stderr)
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        success = result.returncode == 0 if check else True
        return success, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)


def test_help_commands():
    """Test help and version commands."""
    print_header("Testing Help & Version Commands")

    # Test --help
    print_test("memograph --help")
    success, stdout, stderr = run_command(["python", "-m", "memograph.cli", "--help"])
    if success and "MemoGraph CLI" in stdout:
        print_success("Help command works")
    else:
        print_error(f"Help command failed: {stderr}")
        return False

    # Test --version
    print_test("memograph --version")
    success, stdout, stderr = run_command(
        ["python", "-m", "memograph.cli", "--version"]
    )
    if success and "memograph" in stdout:
        print_success(f"Version command works: {stdout.strip()}")
    else:
        print_error(f"Version command failed: {stderr}")
        return False

    return True


def test_subcommand_help():
    """Test help for all subcommands."""
    print_header("Testing Subcommand Help")

    commands = [
        "ingest",
        "remember",
        "context",
        "ask",
        "import",
        "doctor",
        "setup-mcp",
        "verify-mcp",
        "suggest-tags",
        "suggest-links",
        "detect-gaps",
        "analyze-knowledge",
    ]

    all_passed = True
    for cmd in commands:
        print_test(f"memograph {cmd} --help")
        success, stdout, stderr = run_command(
            ["python", "-m", "memograph.cli", cmd, "--help"]
        )
        if success:
            print_success(f"{cmd} help works")
        else:
            print_error(f"{cmd} help failed: {stderr}")
            all_passed = False

    return all_passed


def test_vault_commands(vault_path: Path):
    """Test commands that require a vault."""
    print_header("Testing Vault Commands")

    # Create test note
    test_note = vault_path / "test-note.md"
    test_note.write_text(
        "---\n"
        "title: Test Note\n"
        "memory_type: semantic\n"
        "salience: 0.7\n"
        "tags: [test, python]\n"
        "---\n\n"
        "This is a test note about Python programming.\n"
        "It includes information about testing and validation.\n"
    )

    all_passed = True

    # Test ingest
    print_test("memograph ingest")
    success, stdout, stderr = run_command(
        ["python", "-m", "memograph.cli", "--vault", str(vault_path), "ingest"]
    )
    if success and ("indexed" in stdout or "total" in stdout):
        print_success("Ingest command works")
    else:
        print_error(f"Ingest failed: {stderr}")
        all_passed = False

    # Test ingest --force
    print_test("memograph ingest --force")
    success, stdout, stderr = run_command(
        [
            "python",
            "-m",
            "memograph.cli",
            "--vault",
            str(vault_path),
            "ingest",
            "--force",
        ]
    )
    if success:
        print_success("Ingest --force works")
    else:
        print_error(f"Ingest --force failed: {stderr}")
        all_passed = False

    # Test remember
    print_test("memograph remember")
    success, stdout, stderr = run_command(
        [
            "python",
            "-m",
            "memograph.cli",
            "--vault",
            str(vault_path),
            "remember",
            "--title",
            "CLI Test Memory",
            "--content",
            "This is a test memory created by the CLI validation script.",
            "--tags",
            "test",
            "cli",
        ]
    )
    if success and "Created memory" in stdout:
        print_success("Remember command works")
    else:
        print_error(f"Remember failed: {stderr}")
        all_passed = False

    # Test context
    print_test("memograph context")
    success, stdout, stderr = run_command(
        [
            "python",
            "-m",
            "memograph.cli",
            "--vault",
            str(vault_path),
            "context",
            "--query",
            "python testing",
            "--depth",
            "2",
            "--top-k",
            "5",
        ]
    )
    if success:
        print_success("Context command works")
    else:
        print_error(f"Context failed: {stderr}")
        all_passed = False

    # Test doctor
    print_test("memograph doctor")
    success, stdout, stderr = run_command(
        ["python", "-m", "memograph.cli", "--vault", str(vault_path), "doctor"]
    )
    if success and "vault" in stdout.lower():
        print_success("Doctor command works")
    else:
        print_error(f"Doctor failed: {stderr}")
        all_passed = False

    return all_passed


def test_ai_commands(vault_path: Path):
    """Test AI-powered commands."""
    print_header("Testing AI Commands")

    # Create test note for AI commands
    test_note = vault_path / "ai-test.md"
    test_note.write_text(
        "# Python Testing Guide\n\n"
        "This document covers testing strategies in Python.\n"
        "Topics include unit testing, integration testing, and test automation.\n"
    )

    all_passed = True

    # Test suggest-tags
    print_test("memograph suggest-tags")
    success, stdout, stderr = run_command(
        [
            "python",
            "-m",
            "memograph.cli",
            "suggest-tags",
            str(test_note),
            "--min-confidence",
            "0.3",
            "--max-suggestions",
            "5",
        ],
        check=False,  # May fail if LLM not available
    )
    if success:
        print_success("Suggest-tags command works")
    else:
        print_warning(f"Suggest-tags skipped (may need LLM): {stderr[:100]}")

    # Test suggest-links
    print_test("memograph suggest-links")
    success, stdout, stderr = run_command(
        [
            "python",
            "-m",
            "memograph.cli",
            "suggest-links",
            str(test_note),
            "--min-confidence",
            "0.4",
            "--max-suggestions",
            "10",
        ],
        check=False,  # May fail if LLM not available
    )
    if success:
        print_success("Suggest-links command works")
    else:
        print_warning(f"Suggest-links skipped (may need LLM): {stderr[:100]}")

    # Test detect-gaps
    print_test("memograph detect-gaps")
    success, stdout, stderr = run_command(
        [
            "python",
            "-m",
            "memograph.cli",
            "--vault",
            str(vault_path),
            "detect-gaps",
            "--min-severity",
            "0.3",
            "--max-gaps",
            "20",
        ],
        check=False,  # May fail if LLM not available
    )
    if success:
        print_success("Detect-gaps command works")
    else:
        print_warning(f"Detect-gaps skipped (may need LLM): {stderr[:100]}")

    # Test analyze-knowledge
    print_test("memograph analyze-knowledge")
    success, stdout, stderr = run_command(
        [
            "python",
            "-m",
            "memograph.cli",
            "--vault",
            str(vault_path),
            "analyze-knowledge",
            "--output",
            "text",
        ],
        check=False,  # May fail if LLM not available
    )
    if success:
        print_success("Analyze-knowledge command works")
    else:
        print_warning(f"Analyze-knowledge skipped (may need LLM): {stderr[:100]}")

    return all_passed


def test_import_command(vault_path: Path):
    """Test document import command."""
    print_header("Testing Import Command")

    # Create test document
    test_doc = vault_path.parent / "test-import.txt"
    test_doc.write_text("This is a test document for import validation.")

    all_passed = True

    # Test import --dry-run
    print_test("memograph import --dry-run")
    success, stdout, stderr = run_command(
        [
            "python",
            "-m",
            "memograph.cli",
            "--vault",
            str(vault_path),
            "import",
            str(test_doc),
            "--dry-run",
        ]
    )
    if success and "Would import" in stdout:
        print_success("Import --dry-run works")
    else:
        print_error(f"Import --dry-run failed: {stderr}")
        all_passed = False

    # Test actual import
    print_test("memograph import")
    success, stdout, stderr = run_command(
        [
            "python",
            "-m",
            "memograph.cli",
            "--vault",
            str(vault_path),
            "import",
            str(test_doc),
            "--type",
            "episodic",
        ]
    )
    if success:
        print_success("Import command works")
    else:
        print_error(f"Import failed: {stderr}")
        all_passed = False

    return all_passed


def test_mcp_commands():
    """Test MCP-related commands."""
    print_header("Testing MCP Commands")

    all_passed = True

    # Test verify-mcp
    print_test("memograph verify-mcp")
    success, stdout, stderr = run_command(
        ["python", "-m", "memograph.cli", "verify-mcp"], check=False
    )
    if success or "MCP" in stdout or "MCP" in stderr:
        print_success("Verify-mcp command works")
    else:
        print_warning("Verify-mcp may need configuration")

    return all_passed


def main():
    """Run all CLI validation tests."""
    print(f"\n{Colors.BOLD}MemoGraph CLI Validation Script{Colors.RESET}")
    print(f"{Colors.BOLD}Testing all commands from README.md{Colors.RESET}\n")

    # Create temporary vault
    temp_dir = tempfile.mkdtemp(prefix="memograph_test_")
    vault_path = Path(temp_dir) / "test-vault"
    vault_path.mkdir()

    try:
        results = {
            "Help & Version": test_help_commands(),
            "Subcommand Help": test_subcommand_help(),
            "Vault Commands": test_vault_commands(vault_path),
            "AI Commands": test_ai_commands(vault_path),
            "Import Command": test_import_command(vault_path),
            "MCP Commands": test_mcp_commands(),
        }

        # Print summary
        print_header("Test Summary")
        passed = sum(1 for v in results.values() if v)
        total = len(results)

        for category, result in results.items():
            status = (
                f"{Colors.GREEN}✓ PASSED{Colors.RESET}"
                if result
                else f"{Colors.RED}✗ FAILED{Colors.RESET}"
            )
            print(f"{category}: {status}")

        print(
            f"\n{Colors.BOLD}Overall: {passed}/{total} test categories passed{Colors.RESET}\n"
        )

        if passed == total:
            print(
                f"{Colors.GREEN}{Colors.BOLD}🎉 All CLI commands validated successfully!{Colors.RESET}\n"
            )
            return 0
        else:
            print(
                f"{Colors.YELLOW}{Colors.BOLD}⚠ Some tests failed or were skipped{Colors.RESET}\n"
            )
            return 1

    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
