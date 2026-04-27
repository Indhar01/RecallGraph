"""Comprehensive integration tests for conflict resolution scenarios.

This test suite covers real-world conflict scenarios that occur during
bidirectional sync operations, testing all conflict resolution strategies
in integration contexts.

Test Coverage:
- All conflict resolution strategies (OBSIDIAN_WINS, MEMOGRAPH_WINS, NEWEST_WINS, MANUAL)
- Real-world conflict patterns
- Complex multi-file conflicts
- Conflict resolution with UI callbacks
- Conflict history tracking
- Conflict recovery workflows
- Edge cases and boundary conditions
"""

import pytest
from pathlib import Path
import time

from memograph.integrations.obsidian.sync import ObsidianSync
from memograph.integrations.obsidian.conflict_resolver import ConflictStrategy


@pytest.fixture
def obsidian_vault(tmp_path):
    """Create a temporary Obsidian vault."""
    vault = tmp_path / "obsidian_vault"
    vault.mkdir()
    return vault


@pytest.fixture
def memograph_vault(tmp_path):
    """Create a temporary MemoGraph vault."""
    vault = tmp_path / "memograph_vault"
    vault.mkdir()
    return vault


@pytest.fixture
def fixture_path():
    """Get the path to test fixtures."""
    return Path(__file__).parent / "fixtures"


def create_sync_engine(obsidian_vault, memograph_vault, strategy):
    """Create a sync engine with specific conflict strategy."""
    return ObsidianSync(
        vault_path=obsidian_vault,
        memograph_vault=memograph_vault,
        conflict_strategy=strategy,
    )


class TestObsidianWinsStrategy:
    """Test OBSIDIAN_WINS conflict resolution strategy in integration scenarios."""

    @pytest.mark.asyncio
    async def test_obsidian_wins_both_modified(
        self, obsidian_vault, memograph_vault, fixture_path
    ):
        """Test Obsidian wins when both sides modified."""
        sync_engine = create_sync_engine(
            obsidian_vault, memograph_vault, ConflictStrategy.OBSIDIAN_WINS
        )

        # Step 1: Create and sync initial version
        note_path = obsidian_vault / "conflict.md"
        note_path.write_text(
            "---\ntitle: Original\n---\n\n# Original Content", encoding="utf-8"
        )
        await sync_engine.pull_from_obsidian()
        sync_engine.kernel.ingest()

        # Step 2: Modify in Obsidian
        time.sleep(0.1)  # Ensure different timestamps
        note_path.write_text(
            "---\ntitle: Obsidian Version\n---\n\n# Modified in Obsidian",
            encoding="utf-8",
        )

        # Step 3: Modify in MemoGraph
        await sync_engine.kernel.remember_async(
            title="MemoGraph Version",
            content="Modified in MemoGraph",
            meta={"source": "obsidian", "obsidian_path": str(note_path)},
        )
        sync_engine.kernel.ingest()

        # Step 4: Sync - Obsidian should win
        _stats = await sync_engine.sync(direction="bidirectional")

        # Verify Obsidian version preserved
        content = note_path.read_text(encoding="utf-8")
        assert "Obsidian Version" in content
        assert "MemoGraph Version" not in content

    @pytest.mark.asyncio
    async def test_obsidian_wins_with_newer_memograph(
        self, obsidian_vault, memograph_vault
    ):
        """Test Obsidian wins even when MemoGraph is newer."""
        sync_engine = create_sync_engine(
            obsidian_vault, memograph_vault, ConflictStrategy.OBSIDIAN_WINS
        )

        # Create old Obsidian version
        note_path = obsidian_vault / "old_obs.md"
        note_path.write_text("---\ntitle: Old Obsidian\n---\n\n# Old", encoding="utf-8")
        await sync_engine.pull_from_obsidian()
        sync_engine.kernel.ingest()

        # Create newer MemoGraph version
        time.sleep(0.2)
        await sync_engine.kernel.remember_async(
            title="New MemoGraph",
            content="Much newer content",
            meta={"source": "obsidian", "obsidian_path": str(note_path)},
        )
        sync_engine.kernel.ingest()

        # Modify Obsidian (still older timestamp)
        note_path.write_text(
            "---\ntitle: Old Obsidian Modified\n---\n\n# Old Modified", encoding="utf-8"
        )

        # Sync - Obsidian should still win despite being older
        await sync_engine.sync(direction="bidirectional")

        # Verify Obsidian won
        sync_engine.kernel.ingest()
        nodes = list(sync_engine.kernel.graph.all_nodes())
        titles = [n.title for n in nodes]
        assert "Old Obsidian Modified" in titles
        assert "New MemoGraph" not in titles


class TestMemographWinsStrategy:
    """Test MEMOGRAPH_WINS conflict resolution strategy."""

    @pytest.mark.asyncio
    async def test_memograph_wins_both_modified(self, obsidian_vault, memograph_vault):
        """Test MemoGraph wins when both sides modified."""
        sync_engine = create_sync_engine(
            obsidian_vault, memograph_vault, ConflictStrategy.MEMOGRAPH_WINS
        )

        # Create and sync initial
        note_path = obsidian_vault / "memo_wins.md"
        note_path.write_text(
            "---\ntitle: Original\n---\n\n# Original", encoding="utf-8"
        )
        await sync_engine.pull_from_obsidian()
        sync_engine.kernel.ingest()

        # Modify Obsidian
        note_path.write_text(
            "---\ntitle: Obsidian Mod\n---\n\n# Obsidian", encoding="utf-8"
        )

        # Modify MemoGraph
        await sync_engine.kernel.remember_async(
            title="MemoGraph Mod",
            content="MemoGraph content",
            meta={"source": "obsidian", "obsidian_path": str(note_path)},
        )
        sync_engine.kernel.ingest()

        # Sync - MemoGraph should win
        await sync_engine.sync(direction="bidirectional")

        # Verify MemoGraph won (Obsidian file updated)
        content = note_path.read_text(encoding="utf-8")
        assert "MemoGraph Mod" in content
        assert "Obsidian Mod" not in content


class TestNewestWinsStrategy:
    """Test NEWEST_WINS conflict resolution strategy."""

    @pytest.mark.asyncio
    async def test_newest_wins_obsidian_newer(self, obsidian_vault, memograph_vault):
        """Test newest wins when Obsidian is newer."""
        sync_engine = create_sync_engine(
            obsidian_vault, memograph_vault, ConflictStrategy.NEWEST_WINS
        )

        # Create initial
        note_path = obsidian_vault / "newest.md"
        note_path.write_text(
            "---\ntitle: Original\n---\n\n# Original", encoding="utf-8"
        )
        await sync_engine.pull_from_obsidian()
        sync_engine.kernel.ingest()

        # Modify MemoGraph first (older)
        await sync_engine.kernel.remember_async(
            title="MemoGraph Old",
            content="Old modification",
            meta={"source": "obsidian", "obsidian_path": str(note_path)},
        )
        sync_engine.kernel.ingest()

        # Modify Obsidian later (newer)
        time.sleep(0.2)
        note_path.write_text(
            "---\ntitle: Obsidian New\n---\n\n# Newer", encoding="utf-8"
        )

        # Sync - newer Obsidian should win
        await sync_engine.sync(direction="bidirectional")

        # Verify Obsidian (newer) won
        sync_engine.kernel.ingest()
        nodes = list(sync_engine.kernel.graph.all_nodes())
        titles = [n.title for n in nodes]
        assert "Obsidian New" in titles

    @pytest.mark.asyncio
    async def test_newest_wins_memograph_newer(self, obsidian_vault, memograph_vault):
        """Test newest wins when MemoGraph is newer."""
        sync_engine = create_sync_engine(
            obsidian_vault, memograph_vault, ConflictStrategy.NEWEST_WINS
        )

        # Create initial
        note_path = obsidian_vault / "newest2.md"
        note_path.write_text(
            "---\ntitle: Original\n---\n\n# Original", encoding="utf-8"
        )
        await sync_engine.pull_from_obsidian()
        sync_engine.kernel.ingest()

        # Modify Obsidian first (older)
        note_path.write_text(
            "---\ntitle: Obsidian Old\n---\n\n# Older", encoding="utf-8"
        )

        # Modify MemoGraph later (newer)
        time.sleep(0.2)
        await sync_engine.kernel.remember_async(
            title="MemoGraph New",
            content="Newer modification",
            meta={"source": "obsidian", "obsidian_path": str(note_path)},
        )
        sync_engine.kernel.ingest()

        # Sync - newer MemoGraph should win
        await sync_engine.sync(direction="bidirectional")

        # Verify MemoGraph (newer) updated Obsidian
        content = note_path.read_text(encoding="utf-8")
        assert "MemoGraph New" in content


class TestManualStrategy:
    """Test MANUAL conflict resolution strategy."""

    @pytest.mark.asyncio
    async def test_manual_creates_conflict_markers(
        self, obsidian_vault, memograph_vault
    ):
        """Test that manual strategy creates conflict markers."""
        sync_engine = create_sync_engine(
            obsidian_vault, memograph_vault, ConflictStrategy.MANUAL
        )

        # Create and sync
        note_path = obsidian_vault / "manual.md"
        note_path.write_text(
            "---\ntitle: Original\n---\n\n# Original Content", encoding="utf-8"
        )
        await sync_engine.pull_from_obsidian()
        sync_engine.kernel.ingest()

        # Create conflict
        note_path.write_text(
            "---\ntitle: Obsidian Version\n---\n\n# Obsidian Content", encoding="utf-8"
        )

        await sync_engine.kernel.remember_async(
            title="MemoGraph Version",
            content="# MemoGraph Content",
            meta={"source": "obsidian", "obsidian_path": str(note_path)},
        )
        sync_engine.kernel.ingest()

        # Sync - should create conflict markers
        await sync_engine.sync(direction="bidirectional")

        # Verify conflict markers in file
        content = note_path.read_text(encoding="utf-8")
        assert "<<<<<<< Obsidian Version" in content
        assert "=======" in content
        assert ">>>>>>> MemoGraph Version" in content
        assert "Obsidian Content" in content
        assert "MemoGraph Content" in content

    @pytest.mark.asyncio
    async def test_manual_tracks_conflicts(self, obsidian_vault, memograph_vault):
        """Test that manual strategy tracks conflicts."""
        sync_engine = create_sync_engine(
            obsidian_vault, memograph_vault, ConflictStrategy.MANUAL
        )

        # Create conflict scenario
        note_path = obsidian_vault / "tracked.md"
        note_path.write_text(
            "---\ntitle: Original\n---\n\n# Original", encoding="utf-8"
        )
        await sync_engine.pull_from_obsidian()
        sync_engine.kernel.ingest()

        # Modify both sides
        note_path.write_text(
            "---\ntitle: Modified\n---\n\n# Modified", encoding="utf-8"
        )

        await sync_engine.kernel.remember_async(
            title="Also Modified",
            content="Also Modified",
            meta={"source": "obsidian", "obsidian_path": str(note_path)},
        )
        sync_engine.kernel.ingest()

        # Sync
        await sync_engine.sync(direction="bidirectional")

        # Check conflicts tracked
        status = sync_engine.get_sync_status()
        assert len(status["conflicts"]) > 0
        assert any(str(note_path) in conflict for conflict in status["conflicts"])


class TestComplexConflictScenarios:
    """Test complex real-world conflict scenarios."""

    @pytest.mark.asyncio
    async def test_multiple_file_conflicts(self, obsidian_vault, memograph_vault):
        """Test handling multiple conflicting files in one sync."""
        sync_engine = create_sync_engine(
            obsidian_vault, memograph_vault, ConflictStrategy.NEWEST_WINS
        )

        # Create multiple files
        files = []
        for i in range(5):
            note_path = obsidian_vault / f"conflict_{i}.md"
            note_path.write_text(
                f"---\ntitle: File {i}\n---\n\n# Original {i}", encoding="utf-8"
            )
            files.append(note_path)

        # Initial sync
        await sync_engine.pull_from_obsidian()
        sync_engine.kernel.ingest()

        # Create conflicts in all files
        for i, file_path in enumerate(files):
            # Modify in Obsidian
            file_path.write_text(
                f"---\ntitle: Obsidian {i}\n---\n\n# Obsidian {i}", encoding="utf-8"
            )

            # Modify in MemoGraph
            await sync_engine.kernel.remember_async(
                title=f"MemoGraph {i}",
                content=f"# MemoGraph {i}",
                meta={"source": "obsidian", "obsidian_path": str(file_path)},
            )

        sync_engine.kernel.ingest()

        # Sync - should resolve all conflicts
        stats = await sync_engine.sync(direction="bidirectional")

        # All files should be processed (resolved)
        # Bidirectional sync counts conflicts in both directions: 5 files × 2 = 10
        assert stats["conflicts"] == 10

    @pytest.mark.asyncio
    async def test_cascade_conflict_resolution(self, obsidian_vault, memograph_vault):
        """Test conflict resolution in linked notes (cascade effect)."""
        sync_engine = create_sync_engine(
            obsidian_vault, memograph_vault, ConflictStrategy.OBSIDIAN_WINS
        )

        # Create note A linking to note B
        note_a = obsidian_vault / "note_a.md"
        note_a.write_text(
            "---\ntitle: Note A\n---\n\n# Note A\n\nLinks to [[note_b]]",
            encoding="utf-8",
        )

        note_b = obsidian_vault / "note_b.md"
        note_b.write_text(
            "---\ntitle: Note B\n---\n\n# Note B\n\nOriginal content", encoding="utf-8"
        )

        # Initial sync
        await sync_engine.pull_from_obsidian()
        sync_engine.kernel.ingest()

        # Create conflicts in both
        note_a.write_text(
            "---\ntitle: Note A Modified\n---\n\n# A Modified\n\nLinks to [[note_b]]",
            encoding="utf-8",
        )
        note_b.write_text(
            "---\ntitle: Note B Modified\n---\n\n# B Modified", encoding="utf-8"
        )

        # Sync - both should resolve with Obsidian winning
        await sync_engine.sync(direction="bidirectional")

        # Verify both resolved correctly
        assert note_a.exists()
        assert note_b.exists()
        content_a = note_a.read_text(encoding="utf-8")
        content_b = note_b.read_text(encoding="utf-8")
        assert "A Modified" in content_a
        assert "B Modified" in content_b

    @pytest.mark.asyncio
    async def test_conflict_with_deletion(self, obsidian_vault, memograph_vault):
        """Test conflict when file deleted in one location."""
        sync_engine = create_sync_engine(
            obsidian_vault, memograph_vault, ConflictStrategy.OBSIDIAN_WINS
        )

        # Create and sync
        note_path = obsidian_vault / "deleted.md"
        note_path.write_text(
            "---\ntitle: To Delete\n---\n\n# Content", encoding="utf-8"
        )
        await sync_engine.pull_from_obsidian()
        sync_engine.kernel.ingest()

        # Delete in Obsidian
        note_path.unlink()

        # Modify in MemoGraph
        await sync_engine.kernel.remember_async(
            title="Modified After Delete",
            content="Modified content",
            meta={"source": "obsidian", "obsidian_path": str(note_path)},
        )
        sync_engine.kernel.ingest()

        # Sync - deletion should take precedence (Obsidian wins = no file)
        await sync_engine.sync(direction="bidirectional")

        # File should remain deleted
        assert not note_path.exists()


class TestConflictHistoryTracking:
    """Test conflict history tracking functionality."""

    @pytest.mark.asyncio
    async def test_conflict_history_recorded(self, obsidian_vault, memograph_vault):
        """Test that conflicts are recorded in history."""
        sync_engine = create_sync_engine(
            obsidian_vault, memograph_vault, ConflictStrategy.MANUAL
        )

        # Create conflict
        note_path = obsidian_vault / "history.md"
        note_path.write_text(
            "---\ntitle: Original\n---\n\n# Original", encoding="utf-8"
        )
        await sync_engine.pull_from_obsidian()
        sync_engine.kernel.ingest()

        # Modify both
        note_path.write_text(
            "---\ntitle: Modified\n---\n\n# Modified", encoding="utf-8"
        )
        await sync_engine.kernel.remember_async(
            title="Also Modified",
            content="Also Modified",
            meta={"source": "obsidian", "obsidian_path": str(note_path)},
        )
        sync_engine.kernel.ingest()

        # Sync and check history
        await sync_engine.sync(direction="bidirectional")

        # Get conflict history
        history = sync_engine.resolver.get_conflict_history()
        assert len(history) > 0

        # Verify history entry details
        assert any(str(note_path) in entry.get("file_path", "") for entry in history)

    @pytest.mark.asyncio
    async def test_clear_conflict_history(self, obsidian_vault, memograph_vault):
        """Test clearing conflict history."""
        sync_engine = create_sync_engine(
            obsidian_vault, memograph_vault, ConflictStrategy.MANUAL
        )

        # Create and resolve a conflict
        note_path = obsidian_vault / "clearable.md"
        note_path.write_text(
            "---\ntitle: Original\n---\n\n# Original", encoding="utf-8"
        )
        await sync_engine.pull_from_obsidian()
        sync_engine.kernel.ingest()

        note_path.write_text(
            "---\ntitle: Modified\n---\n\n# Modified", encoding="utf-8"
        )
        await sync_engine.kernel.remember_async(
            title="Modified",
            content="Modified",
            meta={"source": "obsidian", "obsidian_path": str(note_path)},
        )
        sync_engine.kernel.ingest()

        await sync_engine.sync(direction="bidirectional")

        # Verify history exists
        history_before = sync_engine.resolver.get_conflict_history()
        assert len(history_before) > 0

        # Clear history
        sync_engine.resolver.clear_conflict_history()

        # Verify history cleared
        history_after = sync_engine.resolver.get_conflict_history()
        assert len(history_after) == 0


class TestConflictRecovery:
    """Test recovery from conflict scenarios."""

    @pytest.mark.asyncio
    async def test_recover_from_manual_conflict(self, obsidian_vault, memograph_vault):
        """Test recovering from manually marked conflict."""
        sync_engine = create_sync_engine(
            obsidian_vault, memograph_vault, ConflictStrategy.MANUAL
        )

        # Create conflict
        note_path = obsidian_vault / "recoverable.md"
        note_path.write_text(
            "---\ntitle: Original\n---\n\n# Original", encoding="utf-8"
        )
        await sync_engine.pull_from_obsidian()
        sync_engine.kernel.ingest()

        note_path.write_text(
            "---\ntitle: Obsidian\n---\n\n# Obsidian", encoding="utf-8"
        )
        await sync_engine.kernel.remember_async(
            title="MemoGraph",
            content="MemoGraph",
            meta={"source": "obsidian", "obsidian_path": str(note_path)},
        )
        sync_engine.kernel.ingest()

        # Sync - creates conflict markers
        await sync_engine.sync(direction="bidirectional")

        # Manually resolve by editing file
        note_path.write_text(
            "---\ntitle: Resolved\n---\n\n# Manually Resolved Content", encoding="utf-8"
        )

        # Resolve conflict manually
        result = sync_engine.resolve_conflict_manually(str(note_path))
        assert result is True

        # Sync again - should accept resolved version
        await sync_engine.pull_from_obsidian()
        sync_engine.kernel.ingest()

        nodes = list(sync_engine.kernel.graph.all_nodes())
        titles = [n.title for n in nodes]
        assert "Resolved" in titles

    @pytest.mark.asyncio
    async def test_batch_conflict_recovery(self, obsidian_vault, memograph_vault):
        """Test recovering from multiple conflicts in batch."""
        sync_engine = create_sync_engine(
            obsidian_vault, memograph_vault, ConflictStrategy.NEWEST_WINS
        )

        # Create multiple conflicting files
        files = []
        for i in range(3):
            note = obsidian_vault / f"batch_conflict_{i}.md"
            note.write_text(
                f"---\ntitle: Original {i}\n---\n\n# Original {i}", encoding="utf-8"
            )
            files.append(note)

        await sync_engine.pull_from_obsidian()
        sync_engine.kernel.ingest()

        # Create conflicts
        for i, file_path in enumerate(files):
            file_path.write_text(
                f"---\ntitle: Obsidian {i}\n---\n\n# Obsidian {i}", encoding="utf-8"
            )
            await sync_engine.kernel.remember_async(
                title=f"MemoGraph {i}",
                content=f"MemoGraph {i}",
                meta={"source": "obsidian", "obsidian_path": str(file_path)},
            )

        sync_engine.kernel.ingest()

        # Batch sync - should resolve all with newest wins
        stats = await sync_engine.batch_sync(direction="bidirectional")

        # Bidirectional sync counts conflicts in both directions: 3 files × 2 = 6
        assert stats["conflicts"] == 6
        # All should be resolved automatically
        assert stats["processed"] >= 3


class TestEdgeCases:
    """Test edge cases and boundary conditions in conflict resolution."""

    @pytest.mark.asyncio
    async def test_conflict_with_identical_content(
        self, obsidian_vault, memograph_vault
    ):
        """Test when both sides have identical content (no real conflict)."""
        sync_engine = create_sync_engine(
            obsidian_vault, memograph_vault, ConflictStrategy.NEWEST_WINS
        )

        # Create file
        note_path = obsidian_vault / "identical.md"
        note_path.write_text(
            "---\ntitle: Same\n---\n\n# Same Content", encoding="utf-8"
        )
        await sync_engine.pull_from_obsidian()
        sync_engine.kernel.ingest()

        # "Modify" both with same content
        note_path.write_text(
            "---\ntitle: Same Modified\n---\n\n# Same Content Modified",
            encoding="utf-8",
        )
        await sync_engine.kernel.remember_async(
            title="Same Modified",
            content="# Same Content Modified",
            meta={"source": "obsidian", "obsidian_path": str(note_path)},
        )
        sync_engine.kernel.ingest()

        # Sync - should not count as conflict
        stats = await sync_engine.sync(direction="bidirectional")

        # No conflict because content is identical
        assert stats["conflicts"] == 0

    @pytest.mark.asyncio
    async def test_conflict_with_empty_content(self, obsidian_vault, memograph_vault):
        """Test conflict when one side has empty content."""
        sync_engine = create_sync_engine(
            obsidian_vault, memograph_vault, ConflictStrategy.OBSIDIAN_WINS
        )

        # Create file
        note_path = obsidian_vault / "empty_conflict.md"
        note_path.write_text(
            "---\ntitle: Original\n---\n\n# Original Content", encoding="utf-8"
        )
        await sync_engine.pull_from_obsidian()
        sync_engine.kernel.ingest()

        # Empty Obsidian version
        note_path.write_text("---\ntitle: Empty\n---\n\n", encoding="utf-8")

        # Non-empty MemoGraph version
        await sync_engine.kernel.remember_async(
            title="Not Empty",
            content="Has content",
            meta={"source": "obsidian", "obsidian_path": str(note_path)},
        )
        sync_engine.kernel.ingest()

        # Sync - Obsidian (empty) should win
        await sync_engine.sync(direction="bidirectional")

        content = note_path.read_text(encoding="utf-8")
        assert "Empty" in content
        assert "Has content" not in content


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
