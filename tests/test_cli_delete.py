"""Tests for CLI delete command.

Tests single memory deletion, bulk deletion, filtering, and safety features.
"""

from unittest.mock import patch

import pytest

from memograph.cli import main


@pytest.fixture
def test_vault_with_memories(tmp_path):
    """Create test vault with sample memories."""
    vault = tmp_path / "vault"
    vault.mkdir()

    # Create test memories
    memories = [
        {
            "id": "test-001",
            "title": "Python Tips",
            "content": "Use list comprehensions for better performance",
            "memory_type": "semantic",
            "salience": 0.7,
            "tags": ["python", "programming"],
        },
        {
            "id": "test-002",
            "title": "Docker Guide",
            "content": "Container basics and best practices",
            "memory_type": "procedural",
            "salience": 0.6,
            "tags": ["docker", "devops"],
        },
        {
            "id": "test-003",
            "title": "Meeting Notes",
            "content": "Discussed Q3 goals and objectives",
            "memory_type": "episodic",
            "salience": 0.5,
            "tags": ["meeting", "planning"],
        },
        {
            "id": "test-004",
            "title": "Old Documentation",
            "content": "Outdated information",
            "memory_type": "semantic",
            "salience": 0.3,
            "tags": ["deprecated", "old"],
        },
        {
            "id": "test-005",
            "title": "Temporary Note",
            "content": "Can be deleted",
            "memory_type": "fact",
            "salience": 0.2,
            "tags": ["temp", "delete-me"],
        },
    ]

    for mem in memories:
        file_path = vault / f"{mem['id']}.md"
        content = f"""---
id: {mem['id']}
title: {mem['title']}
memory_type: {mem['memory_type']}
salience: {mem['salience']}
tags: {mem['tags']}
---

{mem['content']}
"""
        file_path.write_text(content, encoding="utf-8")

    return vault


class TestDeleteSingleMemory:
    """Test deleting a single memory by ID."""

    def test_delete_single_memory(self, test_vault_with_memories, capsys):
        """Test deleting a single memory."""
        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "delete",
                "test-005",
                "--confirm",
            ],
        ):
            main()

        output = capsys.readouterr().out
        assert "Deleted memory: test-005" in output

        # Verify file was deleted
        file_path = test_vault_with_memories / "test-005.md"
        assert not file_path.exists()

    def test_delete_shows_memory_info(self, test_vault_with_memories, capsys):
        """Test that delete shows memory information before deletion."""
        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "delete",
                "test-001",
                "--confirm",
            ],
        ):
            main()

        output = capsys.readouterr().out
        assert "Memory to Delete" in output
        assert "test-001" in output
        assert "Python Tips" in output

    def test_delete_nonexistent_memory(self, test_vault_with_memories, capsys):
        """Test deleting non-existent memory."""
        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "delete",
                "nonexistent-id",
                "--confirm",
            ],
        ):
            main()

        output = capsys.readouterr().out
        assert "not found" in output.lower()

    def test_delete_updates_graph(self, test_vault_with_memories, capsys):
        """Test that graph is updated after deletion."""
        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "delete",
                "test-005",
                "--confirm",
            ],
        ):
            main()

        output = capsys.readouterr().out
        assert "Graph updated" in output


class TestDeleteBulk:
    """Test bulk deletion with filters."""

    def test_delete_by_tag_filter(self, test_vault_with_memories, capsys):
        """Test deleting memories by tag filter."""
        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "delete",
                "--filter",
                "--filter-tags",
                "temp",
                "--confirm",
            ],
        ):
            main()

        output = capsys.readouterr().out
        assert "Deleted: 1" in output

        # Verify file was deleted
        file_path = test_vault_with_memories / "test-005.md"
        assert not file_path.exists()

    def test_delete_by_type_filter(self, test_vault_with_memories, capsys):
        """Test deleting memories by type filter."""
        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "delete",
                "--filter",
                "--filter-type",
                "semantic",
                "--confirm",
            ],
        ):
            main()

        output = capsys.readouterr().out
        assert "Deleted: 2" in output  # test-001 and test-004

        # Verify files were deleted
        assert not (test_vault_with_memories / "test-001.md").exists()
        assert not (test_vault_with_memories / "test-004.md").exists()

        # Verify other files still exist
        assert (test_vault_with_memories / "test-002.md").exists()
        assert (test_vault_with_memories / "test-003.md").exists()

    def test_delete_by_salience_filter(self, test_vault_with_memories, capsys):
        """Test deleting memories by salience filter."""
        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "delete",
                "--filter",
                "--filter-max-salience",
                "0.3",
                "--confirm",
            ],
        ):
            main()

        output = capsys.readouterr().out
        assert "Deleted: 2" in output  # test-004 and test-005

    def test_delete_multiple_filters(self, test_vault_with_memories, capsys):
        """Test deleting with multiple filter criteria."""
        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "delete",
                "--filter",
                "--filter-type",
                "semantic",
                "--filter-max-salience",
                "0.5",
                "--confirm",
            ],
        ):
            main()

        output = capsys.readouterr().out
        assert "Deleted: 1" in output  # Only test-004 matches both filters

    def test_delete_no_matches(self, test_vault_with_memories, capsys):
        """Test bulk delete with no matching memories."""
        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "delete",
                "--filter",
                "--filter-tags",
                "nonexistent-tag",
                "--confirm",
            ],
        ):
            main()

        output = capsys.readouterr().out
        assert "No memories match" in output

    def test_delete_shows_preview(self, test_vault_with_memories, capsys):
        """Test that bulk delete shows preview of memories to delete."""
        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "delete",
                "--filter",
                "--filter-tags",
                "deprecated",
                "--confirm",
            ],
        ):
            main()

        output = capsys.readouterr().out
        assert "Found 1 matching memories" in output
        assert "test-004" in output


class TestDeleteSafety:
    """Test safety features (dry-run, confirmation)."""

    def test_dry_run_no_deletion(self, test_vault_with_memories, capsys):
        """Test dry-run mode doesn't delete files."""
        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "delete",
                "test-005",
                "--dry-run",
            ],
        ):
            main()

        output = capsys.readouterr().out
        assert "DRY RUN" in output

        # Verify file wasn't deleted
        file_path = test_vault_with_memories / "test-005.md"
        assert file_path.exists()

    def test_dry_run_bulk_deletion(self, test_vault_with_memories, capsys):
        """Test dry-run for bulk deletion."""
        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "delete",
                "--filter",
                "--filter-type",
                "semantic",
                "--dry-run",
            ],
        ):
            main()

        output = capsys.readouterr().out
        assert "DRY RUN" in output

        # Verify files weren't deleted
        assert (test_vault_with_memories / "test-001.md").exists()
        assert (test_vault_with_memories / "test-004.md").exists()

    def test_confirmation_required(self, test_vault_with_memories, capsys, monkeypatch):
        """Test confirmation prompt is shown."""
        # Simulate user declining
        monkeypatch.setattr("builtins.input", lambda _: "n")

        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "delete",
                "test-005",
            ],
        ):
            main()

        output = capsys.readouterr().out
        assert "cancelled" in output.lower()

        # Verify file wasn't deleted
        file_path = test_vault_with_memories / "test-005.md"
        assert file_path.exists()

    def test_confirmation_warning(self, test_vault_with_memories, capsys):
        """Test that confirmation shows warning message."""
        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "delete",
                "test-005",
                "--confirm",
            ],
        ):
            main()

        output = capsys.readouterr().out
        # Should show warning in the output
        assert "test-005" in output

    def test_confirm_flag_skips_prompt(self, test_vault_with_memories, capsys):
        """Test --confirm flag skips confirmation prompt."""
        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "delete",
                "test-005",
                "--confirm",
            ],
        ):
            main()

        output = capsys.readouterr().out
        assert "Deleted memory" in output

        # Verify file was deleted
        file_path = test_vault_with_memories / "test-005.md"
        assert not file_path.exists()

    def test_bulk_confirmation_shows_count(
        self, test_vault_with_memories, capsys, monkeypatch
    ):
        """Test bulk deletion confirmation shows count."""
        # Simulate user declining
        monkeypatch.setattr("builtins.input", lambda _: "n")

        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "delete",
                "--filter",
                "--filter-type",
                "semantic",
            ],
        ):
            main()

        output = capsys.readouterr().out
        assert (
            "Found 2 matching memories" in output
        )  # Should show count in confirmation


class TestDeleteIntegration:
    """Integration tests with kernel."""

    def test_graph_updated_after_delete(self, test_vault_with_memories, capsys):
        """Test that graph is re-ingested after deletion."""
        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "delete",
                "test-005",
                "--confirm",
            ],
        ):
            main()

        output = capsys.readouterr().out
        assert "Graph updated" in output

    def test_bulk_delete_graph_updated(self, test_vault_with_memories, capsys):
        """Test graph update after bulk deletion."""
        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "delete",
                "--filter",
                "--filter-tags",
                "temp",
                "--confirm",
            ],
        ):
            main()

        output = capsys.readouterr().out
        assert "Graph updated" in output

    def test_delete_preserves_other_files(self, test_vault_with_memories, capsys):
        """Test that deletion only removes targeted files."""
        # Count files before
        files_before = list(test_vault_with_memories.glob("*.md"))

        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "delete",
                "test-005",
                "--confirm",
            ],
        ):
            main()

        # Count files after
        files_after = list(test_vault_with_memories.glob("*.md"))

        # Should have exactly one less file
        assert len(files_after) == len(files_before) - 1

        # Verify specific files still exist
        assert (test_vault_with_memories / "test-001.md").exists()
        assert (test_vault_with_memories / "test-002.md").exists()
        assert (test_vault_with_memories / "test-003.md").exists()
        assert (test_vault_with_memories / "test-004.md").exists()


class TestDeleteErrorHandling:
    """Test error handling in delete operations."""

    def test_delete_handles_read_error(self, test_vault_with_memories, capsys):
        """Test handling of file read errors."""
        # Create a file with invalid format
        bad_file = test_vault_with_memories / "bad-file.md"
        bad_file.write_text("Invalid content without frontmatter")

        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "delete",
                "--filter",
                "--filter-tags",
                "any",
                "--confirm",
            ],
        ):
            # Should not crash, just skip invalid files
            main()

        output = capsys.readouterr().out
        # Should complete without error
        assert "Deletion Summary" in output or "No memories match" in output
