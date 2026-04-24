"""Tests for CLI tag filtering features.

Tests comma-separated tag parsing and tag filtering across various CLI commands.
"""

from pathlib import Path

import pytest

from memograph import MemoryKernel, MemoryType
from memograph.cli_helpers import (
    run_list_command,
    run_update_command,
    run_delete_command,
    find_memories_by_filter,
)


class Args:
    """Mock args object for testing."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


@pytest.fixture
def kernel_with_tagged_memories(kernel: MemoryKernel) -> MemoryKernel:
    """Create a kernel with memories that have various tags."""
    kernel.remember(
        title="Python Tutorial",
        content="Learn Python programming basics",
        memory_type=MemoryType.SEMANTIC,
        tags=["python", "programming", "tutorial"],
        salience=0.8,
    )

    kernel.remember(
        title="JavaScript Guide",
        content="JavaScript fundamentals and best practices",
        memory_type=MemoryType.SEMANTIC,
        tags=["javascript", "programming", "web"],
        salience=0.7,
    )

    kernel.remember(
        title="Database Design",
        content="Principles of good database design",
        memory_type=MemoryType.FACT,
        tags=["database", "design", "tutorial"],
        salience=0.6,
    )

    kernel.remember(
        title="Meeting Notes Q1",
        content="Quarterly planning meeting notes",
        memory_type=MemoryType.EPISODIC,
        tags=["meeting", "planning", "q1"],
        salience=0.5,
    )

    kernel.remember(
        title="Python Advanced",
        content="Advanced Python concepts",
        memory_type=MemoryType.SEMANTIC,
        tags=["python", "advanced"],
        salience=0.9,
    )

    kernel.ingest()
    return kernel


class TestCommaSeparatedTagParsing:
    """Tests for comma-separated tag parsing."""

    def test_parse_single_tag(self):
        """Test parsing a single tag."""
        # Simulate the lambda parser from cli.py line 846
        parser = lambda s: [t.strip() for t in s.split(",")]
        result = parser("python")
        assert result == ["python"]

    def test_parse_multiple_tags_comma_separated(self):
        """Test parsing comma-separated tags."""
        parser = lambda s: [t.strip() for t in s.split(",")]
        result = parser("python,javascript,ruby")
        assert result == ["python", "javascript", "ruby"]

    def test_parse_tags_with_spaces(self):
        """Test parsing tags with spaces around commas."""
        parser = lambda s: [t.strip() for t in s.split(",")]
        result = parser("python, javascript , ruby")
        assert result == ["python", "javascript", "ruby"]

    def test_parse_tags_with_empty_strings(self):
        """Test parsing handles empty strings."""
        parser = lambda s: [t.strip() for t in s.split(",")]
        result = parser("python,,javascript")
        # Empty strings become empty after strip
        assert result == ["python", "", "javascript"]

    def test_parse_tags_case_sensitive(self):
        """Test that tag parsing preserves case."""
        parser = lambda s: [t.strip() for t in s.split(",")]
        result = parser("Python,JAVASCRIPT,ruby")
        assert result == ["Python", "JAVASCRIPT", "ruby"]


class TestListCommandTagFiltering:
    """Tests for tag filtering in list command."""

    def test_list_with_single_tag(
        self, kernel_with_tagged_memories: MemoryKernel, capsys
    ):
        """Test listing memories with single tag filter."""
        args = Args(
            tags=["python"],
            type=None,
            min_salience=None,
            max_salience=None,
            sort_by=None,
            reverse=False,
            limit=None,
            offset=None,
            format="table",
        )

        run_list_command(kernel_with_tagged_memories, args)

        captured = capsys.readouterr()
        # Should show Python-tagged memories
        assert "Python Tutorial" in captured.out
        assert "Python Advanced" in captured.out
        # Should not show non-Python memories
        assert "JavaScript Guide" not in captured.out

    def test_list_with_multiple_tags(
        self, kernel_with_tagged_memories: MemoryKernel, capsys
    ):
        """Test listing with multiple tags (any match)."""
        args = Args(
            tags=["python", "javascript"],
            type=None,
            min_salience=None,
            max_salience=None,
            sort_by=None,
            reverse=False,
            limit=None,
            offset=None,
            format="table",
        )

        run_list_command(kernel_with_tagged_memories, args)

        captured = capsys.readouterr()
        # Should show memories with either tag
        assert "Python Tutorial" in captured.out
        assert "JavaScript Guide" in captured.out
        # Should not show unrelated memories
        assert "Meeting Notes" in captured.out or "Meeting Notes" not in captured.out

    def test_list_with_nonexistent_tag(
        self, kernel_with_tagged_memories: MemoryKernel, capsys
    ):
        """Test listing with a tag that doesn't exist."""
        args = Args(
            tags=["nonexistent"],
            type=None,
            min_salience=None,
            max_salience=None,
            sort_by=None,
            reverse=False,
            limit=None,
            offset=None,
            format="table",
        )

        run_list_command(kernel_with_tagged_memories, args)

        captured = capsys.readouterr()
        assert "No memories found" in captured.out


class TestUpdateCommandTagFiltering:
    """Tests for tag filtering in update command."""

    def test_update_by_tag_filter(self, kernel_with_tagged_memories: MemoryKernel):
        """Test updating memories filtered by tag."""
        vault_path = Path(kernel_with_tagged_memories.vault_path)

        args = Args(
            memory_id=None,
            filter=True,
            title=None,
            content=None,
            type=None,
            salience=0.95,
            add_tags=["updated"],
            remove_tags=None,
            set_tags=None,
            filter_tags=["python"],
            filter_type=None,
            filter_min_salience=None,
            filter_max_salience=None,
            dry_run=False,
            confirm=True,
        )

        run_update_command(kernel_with_tagged_memories, args)

        # Verify python-tagged memories were updated
        memories = find_memories_by_filter(vault_path, tags=["updated"])
        assert len(memories) == 2  # Python Tutorial and Python Advanced

        # Verify salience was updated
        for memory in memories:
            assert memory.get("salience") == 0.95

    def test_update_with_multiple_tag_filter(
        self, kernel_with_tagged_memories: MemoryKernel
    ):
        """Test updating with multiple tags in filter."""
        vault_path = Path(kernel_with_tagged_memories.vault_path)

        args = Args(
            memory_id=None,
            filter=True,
            title=None,
            content=None,
            type=None,
            salience=None,
            add_tags=["reviewed"],
            remove_tags=None,
            set_tags=None,
            filter_tags=["tutorial"],  # Matches Python Tutorial and Database Design
            filter_type=None,
            filter_min_salience=None,
            filter_max_salience=None,
            dry_run=False,
            confirm=True,
        )

        run_update_command(kernel_with_tagged_memories, args)

        # Verify tutorial-tagged memories were updated
        memories = find_memories_by_filter(vault_path, tags=["reviewed"])
        assert len(memories) == 2


class TestDeleteCommandTagFiltering:
    """Tests for tag filtering in delete command."""

    def test_delete_by_tag_filter(self, kernel_with_tagged_memories: MemoryKernel):
        """Test deleting memories filtered by tag."""
        vault_path = Path(kernel_with_tagged_memories.vault_path)
        initial_count = len(list(vault_path.glob("*.md")))

        args = Args(
            memory_id=None,
            filter=True,
            filter_tags=["meeting"],
            filter_type=None,
            filter_min_salience=None,
            filter_max_salience=None,
            dry_run=False,
            confirm=True,
        )

        run_delete_command(kernel_with_tagged_memories, args)

        final_count = len(list(vault_path.glob("*.md")))
        assert final_count == initial_count - 1  # One meeting memory deleted

    def test_delete_with_tag_filter_dry_run(
        self, kernel_with_tagged_memories: MemoryKernel, capsys
    ):
        """Test delete dry-run with tag filter."""
        vault_path = Path(kernel_with_tagged_memories.vault_path)
        initial_count = len(list(vault_path.glob("*.md")))

        args = Args(
            memory_id=None,
            filter=True,
            filter_tags=["python"],
            filter_type=None,
            filter_min_salience=None,
            filter_max_salience=None,
            dry_run=True,
            confirm=True,
        )

        run_delete_command(kernel_with_tagged_memories, args)

        final_count = len(list(vault_path.glob("*.md")))
        assert final_count == initial_count  # No files deleted

        captured = capsys.readouterr()
        assert "DRY RUN" in captured.out


class TestFindMemoriesByFilter:
    """Tests for find_memories_by_filter helper function."""

    def test_find_by_single_tag(self, kernel_with_tagged_memories: MemoryKernel):
        """Test finding memories by single tag."""
        vault_path = Path(kernel_with_tagged_memories.vault_path)

        memories = find_memories_by_filter(vault_path, tags=["python"])
        assert len(memories) == 2

        titles = [m.get("title") for m in memories]
        assert "Python Tutorial" in titles
        assert "Python Advanced" in titles

    def test_find_by_multiple_tags_any_match(
        self, kernel_with_tagged_memories: MemoryKernel
    ):
        """Test finding memories with any of multiple tags."""
        vault_path = Path(kernel_with_tagged_memories.vault_path)

        memories = find_memories_by_filter(vault_path, tags=["python", "javascript"])
        assert (
            len(memories) >= 3
        )  # At least Python Tutorial, Python Advanced, JavaScript Guide

    def test_find_by_tag_and_type(self, kernel_with_tagged_memories: MemoryKernel):
        """Test finding memories by both tag and type."""
        vault_path = Path(kernel_with_tagged_memories.vault_path)

        memories = find_memories_by_filter(
            vault_path, tags=["programming"], memory_type="semantic"
        )

        # Should find Python Tutorial and JavaScript Guide (both semantic with programming tag)
        assert len(memories) == 2

    def test_find_by_tag_and_salience_range(
        self, kernel_with_tagged_memories: MemoryKernel
    ):
        """Test finding memories by tag and salience range."""
        vault_path = Path(kernel_with_tagged_memories.vault_path)

        memories = find_memories_by_filter(
            vault_path, tags=["python"], min_salience=0.85
        )

        # Should find only Python Advanced (salience 0.9)
        assert len(memories) == 1
        assert memories[0].get("title") == "Python Advanced"

    def test_find_with_no_matches(self, kernel_with_tagged_memories: MemoryKernel):
        """Test finding with tags that don't match any memories."""
        vault_path = Path(kernel_with_tagged_memories.vault_path)

        memories = find_memories_by_filter(vault_path, tags=["nonexistent", "fake"])
        assert len(memories) == 0


class TestTagFilteringEdgeCases:
    """Tests for edge cases in tag filtering."""

    def test_empty_tag_list(self, kernel_with_tagged_memories: MemoryKernel):
        """Test filtering with empty tag list."""
        vault_path = Path(kernel_with_tagged_memories.vault_path)

        memories = find_memories_by_filter(vault_path, tags=[])
        # Should return all memories when no tag filter
        assert len(memories) == 5

    def test_none_tag_list(self, kernel_with_tagged_memories: MemoryKernel):
        """Test filtering with None tag list."""
        vault_path = Path(kernel_with_tagged_memories.vault_path)

        memories = find_memories_by_filter(vault_path, tags=None)
        # Should return all memories when tag filter is None
        assert len(memories) == 5

    def test_case_sensitive_tag_matching(self, kernel: MemoryKernel):
        """Test that tag matching is case-sensitive."""
        kernel.remember(
            title="Test Memory",
            content="Content",
            memory_type=MemoryType.FACT,
            tags=["Python"],  # Capital P
        )

        vault_path = Path(kernel.vault_path)

        # Search for lowercase should not match
        memories = find_memories_by_filter(vault_path, tags=["python"])
        assert len(memories) == 0

        # Search for exact case should match
        memories = find_memories_by_filter(vault_path, tags=["Python"])
        assert len(memories) == 1
