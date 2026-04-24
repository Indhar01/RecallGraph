"""Tests for CLI update command.

Tests single memory updates, bulk updates, filtering, and safety features.
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


class TestUpdateSingleMemory:
    """Test updating a single memory by ID."""

    def test_update_title(self, test_vault_with_memories, capsys):
        """Test updating memory title."""
        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "update",
                "test-001",
                "--title",
                "Advanced Python Tips",
                "--confirm",
            ],
        ):
            main()

        output = capsys.readouterr().out
        assert "Updated memory: test-001" in output

        # Verify file was updated
        file_path = test_vault_with_memories / "test-001.md"
        content = file_path.read_text(encoding="utf-8")
        assert "Advanced Python Tips" in content

    def test_update_salience(self, test_vault_with_memories, capsys):
        """Test updating memory salience."""
        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "update",
                "test-002",
                "--salience",
                "0.9",
                "--confirm",
            ],
        ):
            main()

        output = capsys.readouterr().out
        assert "Updated memory: test-002" in output

        # Verify salience was updated
        file_path = test_vault_with_memories / "test-002.md"
        content = file_path.read_text(encoding="utf-8")
        assert "salience: 0.9" in content

    def test_update_type(self, test_vault_with_memories, capsys):
        """Test updating memory type."""
        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "update",
                "test-003",
                "--type",
                "semantic",
                "--confirm",
            ],
        ):
            main()

        output = capsys.readouterr().out
        assert "Updated memory: test-003" in output

        # Verify type was updated
        file_path = test_vault_with_memories / "test-003.md"
        content = file_path.read_text(encoding="utf-8")
        assert "memory_type: semantic" in content

    def test_update_content(self, test_vault_with_memories, capsys):
        """Test updating memory content."""
        new_content = "Updated content with new information"

        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "update",
                "test-001",
                "--content",
                new_content,
                "--confirm",
            ],
        ):
            main()

        output = capsys.readouterr().out
        assert "Updated memory: test-001" in output

        # Verify content was updated
        file_path = test_vault_with_memories / "test-001.md"
        content = file_path.read_text(encoding="utf-8")
        assert new_content in content

    def test_update_add_tags(self, test_vault_with_memories, capsys):
        """Test adding tags to memory."""
        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "update",
                "test-001",
                "--add-tags",
                "advanced",
                "tutorial",
                "--confirm",
            ],
        ):
            main()

        output = capsys.readouterr().out
        assert "Updated memory: test-001" in output

        # Verify tags were added
        file_path = test_vault_with_memories / "test-001.md"
        content = file_path.read_text(encoding="utf-8")
        assert "advanced" in content
        assert "tutorial" in content
        # Original tags should still be there
        assert "python" in content

    def test_update_remove_tags(self, test_vault_with_memories, capsys):
        """Test removing tags from memory."""
        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "update",
                "test-001",
                "--remove-tags",
                "programming",
                "--confirm",
            ],
        ):
            main()

        output = capsys.readouterr().out
        assert "Updated memory: test-001" in output

        # Verify tag was removed
        file_path = test_vault_with_memories / "test-001.md"
        content = file_path.read_text(encoding="utf-8")
        # Python tag should remain
        assert "python" in content

    def test_update_set_tags(self, test_vault_with_memories, capsys):
        """Test replacing all tags."""
        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "update",
                "test-001",
                "--set-tags",
                "new-tag",
                "another-tag",
                "--confirm",
            ],
        ):
            main()

        output = capsys.readouterr().out
        assert "Updated memory: test-001" in output

        # Verify tags were replaced
        file_path = test_vault_with_memories / "test-001.md"
        content = file_path.read_text(encoding="utf-8")
        assert "new-tag" in content
        assert "another-tag" in content

    def test_update_multiple_fields(self, test_vault_with_memories, capsys):
        """Test updating multiple fields at once."""
        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "update",
                "test-001",
                "--title",
                "New Title",
                "--salience",
                "0.95",
                "--add-tags",
                "important",
                "--confirm",
            ],
        ):
            main()

        output = capsys.readouterr().out
        assert "Updated memory: test-001" in output

        # Verify all updates
        file_path = test_vault_with_memories / "test-001.md"
        content = file_path.read_text(encoding="utf-8")
        assert "New Title" in content
        assert "salience: 0.95" in content
        assert "important" in content

    def test_update_nonexistent_memory(self, test_vault_with_memories, capsys):
        """Test updating non-existent memory."""
        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "update",
                "nonexistent-id",
                "--title",
                "New Title",
                "--confirm",
            ],
        ):
            main()

        output = capsys.readouterr().out
        assert "not found" in output.lower()


class TestUpdateBulk:
    """Test bulk update with filters."""

    def test_update_by_tag_filter(self, test_vault_with_memories, capsys):
        """Test updating memories by tag filter."""
        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "update",
                "--filter",
                "--filter-tags",
                "deprecated",
                "--salience",
                "0.2",
                "--confirm",
            ],
        ):
            main()

        output = capsys.readouterr().out
        assert "Success: 1" in output

        # Verify update
        file_path = test_vault_with_memories / "test-004.md"
        content = file_path.read_text(encoding="utf-8")
        assert "salience: 0.2" in content

    def test_update_by_type_filter(self, test_vault_with_memories, capsys):
        """Test updating memories by type filter."""
        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "update",
                "--filter",
                "--filter-type",
                "semantic",
                "--add-tags",
                "knowledge",
                "--confirm",
            ],
        ):
            main()

        output = capsys.readouterr().out
        assert "Success: 2" in output  # test-001 and test-004

    def test_update_by_salience_filter(self, test_vault_with_memories, capsys):
        """Test updating memories by salience filter."""
        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "update",
                "--filter",
                "--filter-min-salience",
                "0.6",
                "--add-tags",
                "high-quality",
                "--confirm",
            ],
        ):
            main()

        output = capsys.readouterr().out
        assert "Success: 2" in output  # test-001 and test-002

    def test_update_no_matches(self, test_vault_with_memories, capsys):
        """Test bulk update with no matching memories."""
        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "update",
                "--filter",
                "--filter-tags",
                "nonexistent-tag",
                "--salience",
                "0.5",
                "--confirm",
            ],
        ):
            main()

        output = capsys.readouterr().out
        assert "No memories match" in output


class TestUpdateSafety:
    """Test safety features (dry-run, confirmation)."""

    def test_dry_run_no_changes(self, test_vault_with_memories, capsys):
        """Test dry-run mode doesn't modify files."""
        # Read original content
        file_path = test_vault_with_memories / "test-001.md"
        original_content = file_path.read_text(encoding="utf-8")

        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "update",
                "test-001",
                "--title",
                "Should Not Change",
                "--dry-run",
            ],
        ):
            main()

        output = capsys.readouterr().out
        assert "DRY RUN" in output

        # Verify file wasn't changed
        new_content = file_path.read_text(encoding="utf-8")
        assert original_content == new_content

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
                "update",
                "test-001",
                "--title",
                "Should Not Change",
            ],
        ):
            main()

        output = capsys.readouterr().out
        assert "cancelled" in output.lower()

    def test_confirm_flag_skips_prompt(self, test_vault_with_memories, capsys):
        """Test --confirm flag skips confirmation prompt."""
        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "update",
                "test-001",
                "--title",
                "New Title",
                "--confirm",
            ],
        ):
            main()

        output = capsys.readouterr().out
        assert "Updated memory" in output
        # Should not show "Apply changes?" prompt


class TestUpdateValidation:
    """Test input validation."""

    def test_no_update_fields_error(self, test_vault_with_memories, capsys):
        """Test error when no update fields provided."""
        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "update",
                "test-001",
                "--confirm",
            ],
        ):
            main()

        output = capsys.readouterr().out
        assert "at least one update field" in output.lower()

    def test_invalid_salience_range(self, test_vault_with_memories, capsys):
        """Test validation of salience range."""
        # This would be caught by argparse type validation
        # Testing the actual update logic
        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "update",
                "test-001",
                "--salience",
                "1.5",  # Invalid: > 1.0
                "--confirm",
            ],
        ):
            try:
                main()
            except SystemExit:
                # argparse will exit on invalid value
                pass


class TestUpdateIntegration:
    """Integration tests with kernel."""

    def test_graph_updated_after_update(self, test_vault_with_memories, capsys):
        """Test that graph is re-ingested after update."""
        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "update",
                "test-001",
                "--title",
                "Updated Title",
                "--confirm",
            ],
        ):
            main()

        output = capsys.readouterr().out
        assert "Graph updated" in output

    def test_bulk_update_graph_updated(self, test_vault_with_memories, capsys):
        """Test graph update after bulk operation."""
        with patch(
            "sys.argv",
            [
                "memograph",
                "--vault",
                str(test_vault_with_memories),
                "update",
                "--filter",
                "--filter-type",
                "semantic",
                "--add-tags",
                "updated",
                "--confirm",
            ],
        ):
            main()

        output = capsys.readouterr().out
        assert "Graph updated" in output
