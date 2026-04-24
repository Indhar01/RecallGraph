"""End-to-end integration tests for Obsidian-MemoGraph bidirectional sync.

This test suite covers complete workflows from file creation through sync to retrieval,
testing the full integration stack.

Test Coverage:
- Complete bidirectional sync workflows
- Multi-file sync scenarios
- Nested directory structures
- Round-trip data integrity
- Real-world usage patterns
- Integration between parser, sync, kernel, and graph components
"""

import pytest
from pathlib import Path
import shutil

from memograph.integrations.obsidian.sync import ObsidianSync
from memograph.integrations.obsidian.conflict_resolver import ConflictStrategy


@pytest.fixture
def integration_vault(tmp_path):
    """Create a temporary vault structure for integration testing."""
    vault = tmp_path / "integration_vault"
    vault.mkdir()

    # Create subdirectories
    (vault / "projects").mkdir()
    (vault / "notes").mkdir()
    (vault / "archive").mkdir()

    return vault


@pytest.fixture
def memograph_vault(tmp_path):
    """Create a temporary MemoGraph vault."""
    vault = tmp_path / "memograph_vault"
    vault.mkdir()
    return vault


@pytest.fixture
def sync_engine(integration_vault, memograph_vault):
    """Create a sync engine for integration tests."""
    return ObsidianSync(
        vault_path=integration_vault,
        memograph_vault=memograph_vault,
        conflict_strategy=ConflictStrategy.NEWEST_WINS,
    )


@pytest.fixture
def fixture_path():
    """Get the path to test fixtures."""
    return Path(__file__).parent / "fixtures"


class TestCompleteE2EWorkflow:
    """Test complete end-to-end workflows."""

    @pytest.mark.asyncio
    async def test_create_sync_retrieve_workflow(
        self, sync_engine, integration_vault, fixture_path
    ):
        """Test complete workflow: create file -> sync -> retrieve from graph."""
        # Step 1: Create a file in Obsidian vault
        note_path = integration_vault / "workflow_test.md"
        shutil.copy(fixture_path / "simple_note.md", note_path)

        # Step 2: Sync from Obsidian to MemoGraph
        pull_stats = await sync_engine.pull_from_obsidian()
        assert pull_stats["count"] == 1
        assert pull_stats["conflicts"] == 0

        # Step 3: Ingest into graph
        sync_engine.kernel.ingest()

        # Step 4: Retrieve and verify data
        nodes = list(sync_engine.kernel.graph.all_nodes())
        assert len(nodes) == 1
        assert nodes[0].title == "Simple Note"
        assert "simple note for testing" in nodes[0].content.lower()
        assert "test" in nodes[0].tags
        assert "simple" in nodes[0].tags

        # Step 5: Verify metadata preservation
        assert nodes[0].frontmatter.get("meta", {}).get("source") == "obsidian"
        assert "obsidian_path" in nodes[0].frontmatter.get("meta", {})

    @pytest.mark.asyncio
    async def test_modify_sync_verify_workflow(
        self, sync_engine, integration_vault, fixture_path
    ):
        """Test workflow: create -> sync -> modify -> sync -> verify changes."""
        # Step 1: Create and initial sync
        note_path = integration_vault / "modify_test.md"
        shutil.copy(fixture_path / "simple_note.md", note_path)
        await sync_engine.pull_from_obsidian()
        sync_engine.kernel.ingest()

        # Step 2: Modify the file
        note_path.write_text(
            "---\ntitle: Modified Note\ntags: [test, modified]\n---\n\n"
            "# Modified Note\n\nThis content has been modified.",
            encoding="utf-8",
        )

        # Step 3: Sync again
        pull_stats = await sync_engine.pull_from_obsidian()
        assert pull_stats["count"] == 1  # Should detect the change

        # Step 4: Ingest and verify
        sync_engine.kernel.ingest()
        nodes = list(sync_engine.kernel.graph.all_nodes())

        # Should have the updated content
        modified_node = [n for n in nodes if n.title == "Modified Note"]
        assert len(modified_node) == 1
        assert "modified" in modified_node[0].content.lower()
        assert "modified" in modified_node[0].tags

    @pytest.mark.asyncio
    async def test_bidirectional_round_trip(
        self, sync_engine, integration_vault, memograph_vault
    ):
        """Test complete round trip: Obsidian -> MemoGraph -> Obsidian."""
        # Step 1: Create file in Obsidian
        obs_note = integration_vault / "roundtrip.md"
        obs_note.write_text(
            "---\ntitle: Round Trip\ntags: [roundtrip]\n---\n\n"
            "# Round Trip\n\nOriginal content",
            encoding="utf-8",
        )

        # Step 2: Pull to MemoGraph
        await sync_engine.pull_from_obsidian()
        sync_engine.kernel.ingest()

        # Step 3: Delete Obsidian file
        obs_note.unlink()
        assert not obs_note.exists()

        # Step 4: Push back to Obsidian
        await sync_engine.push_to_obsidian()

        # Step 5: Verify file restored
        assert obs_note.exists()
        content = obs_note.read_text(encoding="utf-8")
        assert "Round Trip" in content
        assert "Original content" in content


class TestMultiFileSync:
    """Test syncing multiple files in various scenarios."""

    @pytest.mark.asyncio
    async def test_sync_multiple_files_at_once(
        self, sync_engine, integration_vault, fixture_path
    ):
        """Test syncing multiple files in a single operation."""
        # Create multiple files
        files_created = []
        for i in range(5):
            note_path = integration_vault / f"multi_{i}.md"
            note_path.write_text(
                f"---\ntitle: Multi File {i}\ntags: [test, multi]\n---\n\n"
                f"# Multi File {i}\n\nContent {i}",
                encoding="utf-8",
            )
            files_created.append(note_path)

        # Sync all at once
        stats = await sync_engine.pull_from_obsidian()
        assert stats["count"] == 5

        # Verify all in graph
        sync_engine.kernel.ingest()
        nodes = list(sync_engine.kernel.graph.all_nodes())
        assert len(nodes) == 5

        # Verify each file
        titles = [n.title for n in nodes]
        for i in range(5):
            assert f"Multi File {i}" in titles

    @pytest.mark.asyncio
    async def test_sync_nested_directory_structure(
        self, sync_engine, integration_vault
    ):
        """Test syncing files in nested directory structures."""
        # Create nested structure
        projects_dir = integration_vault / "projects"
        notes_dir = integration_vault / "notes"

        # Create files in different directories
        (projects_dir / "project1.md").write_text(
            "---\ntitle: Project 1\n---\n\n# Project 1", encoding="utf-8"
        )
        (projects_dir / "project2.md").write_text(
            "---\ntitle: Project 2\n---\n\n# Project 2", encoding="utf-8"
        )
        (notes_dir / "note1.md").write_text(
            "---\ntitle: Note 1\n---\n\n# Note 1", encoding="utf-8"
        )

        # Sync all
        stats = await sync_engine.pull_from_obsidian()
        assert stats["count"] == 3

        # Verify paths preserved
        sync_engine.kernel.ingest()
        nodes = list(sync_engine.kernel.graph.all_nodes())

        # Check that Obsidian paths reflect directory structure
        paths = [n.frontmatter.get("meta", {}).get("obsidian_path", "") for n in nodes]
        assert any("projects" in p for p in paths)
        assert any("notes" in p for p in paths)

    @pytest.mark.asyncio
    async def test_selective_file_sync(self, sync_engine, integration_vault):
        """Test syncing only specific files."""
        # Create multiple files
        files = []
        for i in range(10):
            note_path = integration_vault / f"selective_{i}.md"
            note_path.write_text(
                f"---\ntitle: Selective {i}\n---\n\n# Content {i}", encoding="utf-8"
            )
            files.append(note_path)

        # Sync only first 5 files
        selected_files = files[:5]
        stats = await sync_engine.batch_sync(
            file_paths=selected_files, direction="pull"
        )

        assert stats["pulled"] == 5
        assert stats["processed"] == 5

        # Verify only selected files in graph
        sync_engine.kernel.ingest()
        nodes = list(sync_engine.kernel.graph.all_nodes())
        assert len(nodes) == 5


class TestNestedDirectorySync:
    """Test syncing with complex nested directory structures."""

    @pytest.mark.asyncio
    async def test_deep_nesting(self, sync_engine, integration_vault):
        """Test syncing deeply nested directories."""
        # Create deep nesting: vault/a/b/c/d/note.md
        deep_path = integration_vault / "a" / "b" / "c" / "d"
        deep_path.mkdir(parents=True)

        note = deep_path / "deep_note.md"
        note.write_text(
            "---\ntitle: Deep Note\n---\n\n# Deep Note\n\nDeeply nested",
            encoding="utf-8",
        )

        # Sync
        stats = await sync_engine.pull_from_obsidian()
        assert stats["count"] == 1

        # Push back and verify path preserved
        await sync_engine.push_to_obsidian()
        assert note.exists()

    @pytest.mark.asyncio
    async def test_preserve_directory_structure_on_push(
        self, sync_engine, integration_vault
    ):
        """Test that directory structure is preserved when pushing."""
        # Create note with specific path
        project_path = integration_vault / "projects" / "2026" / "Q1"
        project_path.mkdir(parents=True)

        note_path = project_path / "project_plan.md"
        note_path.write_text(
            "---\ntitle: Project Plan\n---\n\n# Project Plan", encoding="utf-8"
        )

        # Pull and then delete
        await sync_engine.pull_from_obsidian()
        sync_engine.kernel.ingest()
        note_path.unlink()

        # Push back
        await sync_engine.push_to_obsidian()

        # Verify recreated in correct location
        assert note_path.exists()
        assert project_path.exists()


class TestRealWorldPatterns:
    """Test real-world usage patterns."""

    @pytest.mark.asyncio
    async def test_daily_notes_pattern(self, sync_engine, integration_vault):
        """Test syncing daily notes pattern (date-based filenames)."""
        # Create daily notes
        for day in range(1, 8):  # One week
            date = f"2026-01-{day:02d}"
            note = integration_vault / f"{date}.md"
            note.write_text(
                f"---\ntitle: Daily Note {date}\ntags: [daily]\n---\n\n"
                f"# {date}\n\nDaily notes for {date}",
                encoding="utf-8",
            )

        # Sync all
        stats = await sync_engine.pull_from_obsidian()
        assert stats["count"] == 7

        # Verify all daily notes in graph
        sync_engine.kernel.ingest()
        nodes = list(sync_engine.kernel.graph.all_nodes())
        assert len(nodes) == 7

        # Check temporal ordering preserved
        titles = sorted([n.title for n in nodes])
        assert "2026-01-01" in titles[0]
        assert "2026-01-07" in titles[-1]

    @pytest.mark.asyncio
    async def test_linked_notes_pattern(
        self, sync_engine, integration_vault, fixture_path
    ):
        """Test syncing notes with wikilinks."""
        # Create note with links
        note_with_links = integration_vault / "linked.md"
        shutil.copy(fixture_path / "complex_note.md", note_with_links)

        # Create linked note
        linked_note = integration_vault / "another note.md"
        linked_note.write_text(
            "---\ntitle: Another Note\n---\n\n# Another Note\n\nLinked content",
            encoding="utf-8",
        )

        # Sync both
        stats = await sync_engine.pull_from_obsidian()
        assert stats["count"] >= 2

        # Verify wikilinks extracted
        sync_engine.kernel.ingest()
        nodes = list(sync_engine.kernel.graph.all_nodes())

        # Find the complex note
        complex_nodes = [n for n in nodes if "Complex Note" in n.title]
        assert len(complex_nodes) == 1

        # Check wikilinks in content
        assert "[[" in complex_nodes[0].content

    @pytest.mark.asyncio
    async def test_archive_workflow(self, sync_engine, integration_vault):
        """Test archiving workflow (move to archive folder)."""
        # Create note
        active_note = integration_vault / "active.md"
        active_note.write_text(
            "---\ntitle: Active Note\n---\n\n# Active Note", encoding="utf-8"
        )

        # Initial sync
        await sync_engine.pull_from_obsidian()
        sync_engine.kernel.ingest()

        # Move to archive
        archive_dir = integration_vault / "archive"
        archive_dir.mkdir(exist_ok=True)
        archived_note = archive_dir / "active.md"
        active_note.rename(archived_note)

        # Sync again
        _stats = await sync_engine.pull_from_obsidian()

        # Verify note tracked in new location
        sync_engine.kernel.ingest()
        nodes = list(sync_engine.kernel.graph.all_nodes())
        archived_nodes = [n for n in nodes if "Active Note" in n.title]
        assert len(archived_nodes) == 1
        assert "archive" in archived_nodes[0].frontmatter.get("meta", {}).get(
            "obsidian_path", ""
        )


class TestDataIntegrity:
    """Test data integrity through sync operations."""

    @pytest.mark.asyncio
    async def test_unicode_content_preservation(self, sync_engine, integration_vault):
        """Test that unicode content is preserved through sync."""
        # Create note with unicode
        unicode_note = integration_vault / "unicode.md"
        unicode_note.write_text(
            "---\ntitle: Unicode Test\n---\n\n"
            "# Unicode Test\n\n"
            "Chinese: 测试\n"
            "Japanese: テスト\n"
            "Emoji: 🚀 📝 ✅\n"
            "Math: ∑ ∫ π",
            encoding="utf-8",
        )

        # Sync and verify
        await sync_engine.pull_from_obsidian()
        sync_engine.kernel.ingest()

        nodes = list(sync_engine.kernel.graph.all_nodes())
        assert len(nodes) == 1

        content = nodes[0].content
        assert "测试" in content
        assert "テスト" in content
        assert "🚀" in content
        assert "∑" in content

    @pytest.mark.asyncio
    async def test_special_characters_in_filenames(
        self, sync_engine, integration_vault
    ):
        """Test handling of special characters in filenames."""
        # Create files with special characters
        special_files = [
            "note with spaces.md",
            "note-with-dashes.md",
            "note_with_underscores.md",
            "note.with.dots.md",
        ]

        for filename in special_files:
            note = integration_vault / filename
            note.write_text(
                f"---\ntitle: {filename}\n---\n\n# {filename}", encoding="utf-8"
            )

        # Sync all
        stats = await sync_engine.pull_from_obsidian()
        assert stats["count"] == len(special_files)

        # Verify all synced correctly
        sync_engine.kernel.ingest()
        nodes = list(sync_engine.kernel.graph.all_nodes())
        assert len(nodes) == len(special_files)

    @pytest.mark.asyncio
    async def test_large_file_content(self, sync_engine, integration_vault):
        """Test syncing file with large content."""
        # Create large note
        large_content = "# Large Note\n\n" + ("Lorem ipsum dolor sit amet. " * 1000)
        large_note = integration_vault / "large.md"
        large_note.write_text(
            f"---\ntitle: Large Note\n---\n\n{large_content}", encoding="utf-8"
        )

        # Sync
        stats = await sync_engine.pull_from_obsidian()
        assert stats["count"] == 1

        # Verify content preserved
        sync_engine.kernel.ingest()
        nodes = list(sync_engine.kernel.graph.all_nodes())
        assert len(nodes) == 1
        assert len(nodes[0].content) > 10000  # Should be large


class TestSyncConsistency:
    """Test sync consistency and idempotency."""

    @pytest.mark.asyncio
    async def test_repeated_sync_idempotent(
        self, sync_engine, integration_vault, fixture_path
    ):
        """Test that repeated syncs are idempotent."""
        # Create file
        note = integration_vault / "idempotent.md"
        shutil.copy(fixture_path / "simple_note.md", note)

        # Sync multiple times
        stats1 = await sync_engine.pull_from_obsidian()
        stats2 = await sync_engine.pull_from_obsidian()
        stats3 = await sync_engine.pull_from_obsidian()

        # First sync should process file
        assert stats1["count"] == 1

        # Subsequent syncs should skip unchanged file
        assert stats2["count"] == 0
        assert stats3["count"] == 0

    @pytest.mark.asyncio
    async def test_sync_after_manual_changes(self, sync_engine, integration_vault):
        """Test sync behavior after manual changes in both systems."""
        # Create and sync note
        note = integration_vault / "manual.md"
        note.write_text("---\ntitle: Manual Test\n---\n\n# Original", encoding="utf-8")
        await sync_engine.pull_from_obsidian()
        sync_engine.kernel.ingest()

        # Modify in Obsidian
        note.write_text(
            "---\ntitle: Manual Test Modified\n---\n\n# Modified in Obsidian",
            encoding="utf-8",
        )

        # Sync should detect change
        stats = await sync_engine.pull_from_obsidian()
        assert stats["count"] == 1

        # Verify updated content
        sync_engine.kernel.ingest()
        nodes = list(sync_engine.kernel.graph.all_nodes())
        modified_nodes = [n for n in nodes if "Modified" in n.title]
        assert len(modified_nodes) == 1


class TestConcurrentOperations:
    """Test handling of concurrent operations."""

    @pytest.mark.asyncio
    async def test_concurrent_file_creation(self, sync_engine, integration_vault):
        """Test syncing when multiple files are created simultaneously."""
        import asyncio

        # Create multiple files "simultaneously"
        async def create_file(i):
            note = integration_vault / f"concurrent_{i}.md"
            note.write_text(
                f"---\ntitle: Concurrent {i}\n---\n\n# File {i}", encoding="utf-8"
            )
            await asyncio.sleep(0.01)  # Small delay

        # Create 10 files concurrently
        await asyncio.gather(*[create_file(i) for i in range(10)])

        # Sync all
        stats = await sync_engine.batch_sync(direction="pull")
        assert stats["pulled"] == 10

        # Verify all in graph
        sync_engine.kernel.ingest()
        nodes = list(sync_engine.kernel.graph.all_nodes())
        assert len(nodes) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
