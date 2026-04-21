"""Tests for Obsidian-MemoGraph bidirectional sync."""

import pytest
from datetime import datetime
from unittest.mock import Mock

from memograph.integrations.obsidian.sync import ObsidianSync
from memograph.integrations.obsidian.conflict_resolver import ConflictStrategy
from memograph.core.enums import MemoryType


@pytest.fixture
def temp_obsidian_vault(tmp_path):
    """Create a temporary Obsidian vault directory."""
    vault = tmp_path / "obsidian_vault"
    vault.mkdir()
    return vault


@pytest.fixture
def temp_memograph_vault(tmp_path):
    """Create a temporary MemoGraph vault directory."""
    vault = tmp_path / "memograph_vault"
    vault.mkdir()
    return vault


@pytest.fixture
def sample_obsidian_note(temp_obsidian_vault):
    """Create a sample Obsidian note."""
    note_path = temp_obsidian_vault / "sample.md"
    content = """---
title: Sample Note
tags: [test, sample]
---

This is a sample note with [[wikilink]] and #hashtag.
"""
    note_path.write_text(content, encoding="utf-8")
    return note_path


@pytest.fixture
def obsidian_sync(temp_obsidian_vault, temp_memograph_vault):
    """Create an ObsidianSync instance with temporary vaults."""
    return ObsidianSync(
        vault_path=temp_obsidian_vault,
        memograph_vault=temp_memograph_vault,
        conflict_strategy=ConflictStrategy.NEWEST_WINS,
    )


class TestObsidianSyncInitialization:
    """Test ObsidianSync initialization."""

    def test_init_creates_vaults(self, tmp_path):
        """Test that initialization creates vault directories."""
        obs_vault = tmp_path / "obs"
        memo_vault = tmp_path / "memo"

        sync = ObsidianSync(obs_vault, memo_vault)

        assert obs_vault.exists()
        assert memo_vault.exists()

    def test_init_sets_attributes(
        self, obsidian_sync, temp_obsidian_vault, temp_memograph_vault
    ):
        """Test that initialization sets correct attributes."""
        assert obsidian_sync.vault_path == temp_obsidian_vault
        assert obsidian_sync.memograph_vault == temp_memograph_vault
        assert obsidian_sync.kernel is not None
        assert obsidian_sync.parser is not None
        assert obsidian_sync.state is not None
        assert obsidian_sync.resolver is not None

    def test_init_with_different_strategies(
        self, temp_obsidian_vault, temp_memograph_vault
    ):
        """Test initialization with different conflict strategies."""
        strategies = [
            ConflictStrategy.OBSIDIAN_WINS,
            ConflictStrategy.MEMOGRAPH_WINS,
            ConflictStrategy.NEWEST_WINS,
            ConflictStrategy.MANUAL,
        ]

        for strategy in strategies:
            sync = ObsidianSync(
                temp_obsidian_vault, temp_memograph_vault, conflict_strategy=strategy
            )
            assert sync.resolver.strategy == strategy

    def test_init_creates_sync_state_file(self, obsidian_sync, temp_memograph_vault):
        """Test that initialization prepares for sync state file."""
        # When using SQLite (default), the state file is a .db file, not .json
        # Trigger state operations to ensure database is initialized
        obsidian_sync.state.mark_synced()

        # Check for SQLite database file (default mode)
        state_file = temp_memograph_vault / ".obsidian_sync_state.db"
        assert state_file.exists()


class TestPullFromObsidian:
    """Test pulling notes from Obsidian to MemoGraph."""

    @pytest.mark.asyncio
    async def test_pull_empty_vault(self, obsidian_sync):
        """Test pulling from empty Obsidian vault."""
        stats = await obsidian_sync.pull_from_obsidian()

        assert stats["count"] == 0
        assert stats["conflicts"] == 0

    @pytest.mark.asyncio
    async def test_pull_single_note(self, obsidian_sync, sample_obsidian_note):
        """Test pulling a single note from Obsidian."""
        stats = await obsidian_sync.pull_from_obsidian()

        assert stats["count"] == 1
        assert stats["conflicts"] == 0

    @pytest.mark.asyncio
    async def test_pull_multiple_notes(self, obsidian_sync, temp_obsidian_vault):
        """Test pulling multiple notes."""
        # Create multiple notes
        for i in range(3):
            note = temp_obsidian_vault / f"note{i}.md"
            note.write_text(
                f"---\ntitle: Note {i}\n---\n\nContent {i}", encoding="utf-8"
            )

        stats = await obsidian_sync.pull_from_obsidian()

        assert stats["count"] == 3

    @pytest.mark.asyncio
    async def test_pull_skips_unchanged_files(
        self, obsidian_sync, sample_obsidian_note
    ):
        """Test that pull skips files that haven't changed."""
        # First pull
        stats1 = await obsidian_sync.pull_from_obsidian()
        assert stats1["count"] == 1

        # Second pull without changes
        stats2 = await obsidian_sync.pull_from_obsidian()
        assert stats2["count"] == 0  # Should skip unchanged file

    @pytest.mark.asyncio
    async def test_pull_detects_file_changes(self, obsidian_sync, sample_obsidian_note):
        """Test that pull detects when files are modified."""
        # First pull
        await obsidian_sync.pull_from_obsidian()

        # Modify the file
        sample_obsidian_note.write_text(
            "---\ntitle: Modified\n---\n\nModified content", encoding="utf-8"
        )

        # Second pull should detect change
        stats = await obsidian_sync.pull_from_obsidian()
        assert stats["count"] == 1

    @pytest.mark.asyncio
    async def test_pull_handles_nested_directories(
        self, obsidian_sync, temp_obsidian_vault
    ):
        """Test pulling notes from nested directories."""
        # Create nested structure
        nested = temp_obsidian_vault / "subdir" / "nested"
        nested.mkdir(parents=True)

        note = nested / "deep.md"
        note.write_text(
            "---\ntitle: Deep Note\n---\n\nNested content", encoding="utf-8"
        )

        stats = await obsidian_sync.pull_from_obsidian()
        assert stats["count"] == 1

    @pytest.mark.asyncio
    async def test_pull_ignores_non_markdown_files(
        self, obsidian_sync, temp_obsidian_vault
    ):
        """Test that pull ignores non-markdown files."""
        # Create non-markdown files
        (temp_obsidian_vault / "image.png").write_bytes(b"fake image")
        (temp_obsidian_vault / "data.json").write_text('{"test": true}')
        (temp_obsidian_vault / "note.md").write_text(
            "---\ntitle: Note\n---\n\nContent", encoding="utf-8"
        )

        stats = await obsidian_sync.pull_from_obsidian()
        assert stats["count"] == 1  # Only the .md file

    @pytest.mark.asyncio
    async def test_pull_stores_obsidian_metadata(
        self, obsidian_sync, sample_obsidian_note
    ):
        """Test that pulled notes store Obsidian metadata."""
        await obsidian_sync.pull_from_obsidian()

        # Check that metadata includes obsidian source
        obsidian_sync.kernel.ingest()
        nodes = list(obsidian_sync.kernel.graph.all_nodes())

        assert len(nodes) > 0
        node = nodes[0]
        assert node.frontmatter.get("meta", {}).get("source") == "obsidian"
        assert "obsidian_path" in node.frontmatter.get("meta", {})


class TestPushToObsidian:
    """Test pushing memories from MemoGraph to Obsidian."""

    @pytest.mark.asyncio
    async def test_push_empty_memograph(self, obsidian_sync):
        """Test pushing when MemoGraph has no Obsidian memories."""
        stats = await obsidian_sync.push_to_obsidian()

        assert stats["count"] == 0
        assert stats["conflicts"] == 0

    @pytest.mark.asyncio
    async def test_push_creates_obsidian_file(self, obsidian_sync, temp_obsidian_vault):
        """Test that push creates files in Obsidian vault."""
        # Create a memory with Obsidian metadata
        obsidian_path = temp_obsidian_vault / "pushed.md"

        await obsidian_sync.kernel.remember_async(
            title="Pushed Note",
            content="This was pushed from MemoGraph",
            tags=["test"],
            meta={"source": "obsidian", "obsidian_path": str(obsidian_path)},
        )

        obsidian_sync.kernel.ingest()
        stats = await obsidian_sync.push_to_obsidian()

        assert stats["count"] == 1
        assert obsidian_path.exists()

    @pytest.mark.asyncio
    async def test_push_updates_existing_file(self, obsidian_sync, temp_obsidian_vault):
        """Test that push updates existing Obsidian files."""
        obsidian_path = temp_obsidian_vault / "existing.md"

        # Create initial file
        obsidian_path.write_text(
            "---\ntitle: Old\n---\n\nOld content", encoding="utf-8"
        )

        # Create updated memory
        await obsidian_sync.kernel.remember_async(
            title="Updated",
            content="New content",
            meta={"source": "obsidian", "obsidian_path": str(obsidian_path)},
        )

        obsidian_sync.kernel.ingest()
        stats = await obsidian_sync.push_to_obsidian()

        assert stats["count"] == 1
        content = obsidian_path.read_text(encoding="utf-8")
        assert "New content" in content

    @pytest.mark.asyncio
    async def test_push_skips_non_obsidian_memories(self, obsidian_sync):
        """Test that push only pushes memories from Obsidian source."""
        # Create memory without Obsidian metadata
        await obsidian_sync.kernel.remember_async(
            title="Regular Memory", content="Not from Obsidian"
        )

        obsidian_sync.kernel.ingest()
        stats = await obsidian_sync.push_to_obsidian()

        assert stats["count"] == 0

    @pytest.mark.asyncio
    async def test_push_creates_nested_directories(
        self, obsidian_sync, temp_obsidian_vault
    ):
        """Test that push creates nested directories as needed."""
        nested_path = temp_obsidian_vault / "deep" / "nested" / "note.md"

        await obsidian_sync.kernel.remember_async(
            title="Deep Note",
            content="Nested content",
            meta={"source": "obsidian", "obsidian_path": str(nested_path)},
        )

        obsidian_sync.kernel.ingest()
        await obsidian_sync.push_to_obsidian()

        assert nested_path.exists()
        assert nested_path.parent.exists()


class TestBidirectionalSync:
    """Test bidirectional sync operations."""

    @pytest.mark.asyncio
    async def test_bidirectional_sync_both_directions(
        self, obsidian_sync, temp_obsidian_vault
    ):
        """Test that bidirectional sync processes both directions."""
        # Create note in Obsidian
        obs_note = temp_obsidian_vault / "from_obs.md"
        obs_note.write_text(
            "---\ntitle: From Obsidian\n---\n\nContent", encoding="utf-8"
        )

        # Create memory in MemoGraph for push
        push_path = temp_obsidian_vault / "from_memo.md"
        await obsidian_sync.kernel.remember_async(
            title="From MemoGraph",
            content="Pushed content",
            meta={"source": "obsidian", "obsidian_path": str(push_path)},
        )
        obsidian_sync.kernel.ingest()

        # Perform bidirectional sync
        stats = await obsidian_sync.sync(direction="bidirectional")

        assert stats["pulled"] >= 1
        assert stats["pushed"] >= 1
        assert push_path.exists()

    @pytest.mark.asyncio
    async def test_sync_pull_only(self, obsidian_sync, sample_obsidian_note):
        """Test sync with pull-only direction."""
        stats = await obsidian_sync.sync(direction="pull")

        assert stats["pulled"] == 1
        assert stats["pushed"] == 0

    @pytest.mark.asyncio
    async def test_sync_push_only(self, obsidian_sync, temp_obsidian_vault):
        """Test sync with push-only direction."""
        # Create memory for push
        push_path = temp_obsidian_vault / "push_only.md"
        await obsidian_sync.kernel.remember_async(
            title="Push Only",
            content="Content",
            meta={"source": "obsidian", "obsidian_path": str(push_path)},
        )
        obsidian_sync.kernel.ingest()

        stats = await obsidian_sync.sync(direction="push")

        assert stats["pulled"] == 0
        assert stats["pushed"] == 1

    @pytest.mark.asyncio
    async def test_sync_marks_completion(self, obsidian_sync, sample_obsidian_note):
        """Test that sync marks successful completion."""
        before_sync = obsidian_sync.state.get_last_sync()

        await obsidian_sync.sync()

        after_sync = obsidian_sync.state.get_last_sync()
        assert after_sync is not None
        if before_sync:
            assert after_sync > before_sync


class TestSyncStateManagement:
    """Test sync state tracking and management."""

    def test_get_sync_status(self, obsidian_sync):
        """Test getting sync status."""
        status = obsidian_sync.get_sync_status()

        assert "last_sync" in status
        assert "tracked_files" in status
        assert "conflicts" in status
        assert isinstance(status["tracked_files"], int)
        assert isinstance(status["conflicts"], list)

    def test_resolve_conflict_manually(self, obsidian_sync):
        """Test manually resolving conflicts."""
        # Add a conflict
        obsidian_sync.state.add_conflict("test.md", "Test conflict")

        # Resolve it
        result = obsidian_sync.resolve_conflict_manually("test.md")

        assert result is True
        assert len(obsidian_sync.state.get_conflicts()) == 0

    def test_clear_all_conflicts(self, obsidian_sync):
        """Test clearing all conflicts."""
        # Add multiple conflicts
        obsidian_sync.state.add_conflict("file1.md", "Conflict 1")
        obsidian_sync.state.add_conflict("file2.md", "Conflict 2")

        # Clear all
        count = obsidian_sync.clear_all_conflicts()

        assert count == 2
        assert len(obsidian_sync.state.get_conflicts()) == 0


class TestHelperMethods:
    """Test helper methods."""

    def test_find_memory_by_path_nonexistent(self, obsidian_sync):
        """Test finding memory by nonexistent Obsidian path."""
        result = obsidian_sync._find_memory_by_path("/nonexistent/path.md")
        assert result is None

    def test_node_to_dict_conversion(self, obsidian_sync):
        """Test converting MemoryNode to dictionary."""
        # Create a mock node
        mock_node = Mock()
        mock_node.title = "Test Title"
        mock_node.content = "Test Content"
        mock_node.tags = {"tag1", "tag2"}
        mock_node.frontmatter = {"key": "value"}
        mock_node.created_at = datetime.now()

        result = obsidian_sync._node_to_dict(mock_node)

        assert result["title"] == "Test Title"
        assert result["content"] == "Test Content"
        assert isinstance(result["tags"], list)
        assert result["metadata"] == {"key": "value"}

    def test_parse_memory_type_valid(self, obsidian_sync):
        """Test parsing valid memory type strings."""
        assert obsidian_sync._parse_memory_type("episodic") == MemoryType.EPISODIC
        assert obsidian_sync._parse_memory_type("semantic") == MemoryType.SEMANTIC
        assert obsidian_sync._parse_memory_type("procedural") == MemoryType.PROCEDURAL
        assert obsidian_sync._parse_memory_type("fact") == MemoryType.FACT

    def test_parse_memory_type_invalid(self, obsidian_sync):
        """Test parsing invalid memory type returns default."""
        assert obsidian_sync._parse_memory_type("invalid") == MemoryType.FACT
        assert obsidian_sync._parse_memory_type(None) == MemoryType.FACT
        assert obsidian_sync._parse_memory_type("") == MemoryType.FACT

    def test_hash_content(self, obsidian_sync):
        """Test content hashing."""
        content1 = "This is test content"
        content2 = "This is test content"
        content3 = "Different content"

        hash1 = obsidian_sync._hash_content(content1)
        hash2 = obsidian_sync._hash_content(content2)
        hash3 = obsidian_sync._hash_content(content3)

        assert hash1 == hash2
        assert hash1 != hash3

    def test_write_obsidian_file(self, obsidian_sync, tmp_path):
        """Test writing Obsidian files."""
        file_path = tmp_path / "test_write.md"

        data = {
            "title": "Test Note",
            "content": "Test content",
            "tags": ["tag1", "tag2"],
            "metadata": {"salience": 0.8, "source": "obsidian"},
        }

        obsidian_sync._write_obsidian_file(file_path, data)

        assert file_path.exists()
        content = file_path.read_text(encoding="utf-8")
        assert "Test Note" in content
        assert "Test content" in content
