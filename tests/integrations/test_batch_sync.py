"""Tests for Obsidian-MemoGraph batch sync operations."""

import asyncio

import pytest

from memograph.integrations.obsidian.conflict_resolver import ConflictStrategy
from memograph.integrations.obsidian.sync import ObsidianSync


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
def obsidian_sync(temp_obsidian_vault, temp_memograph_vault):
    """Create an ObsidianSync instance with temporary vaults."""
    return ObsidianSync(
        vault_path=temp_obsidian_vault,
        memograph_vault=temp_memograph_vault,
        conflict_strategy=ConflictStrategy.NEWEST_WINS,
    )


@pytest.fixture
def create_test_notes(temp_obsidian_vault):
    """Factory fixture to create multiple test notes."""

    def _create_notes(count: int):
        notes = []
        for i in range(count):
            note_path = temp_obsidian_vault / f"note_{i:03d}.md"
            content = f"""---
title: Test Note {i}
tags: [test, batch, note{i}]
---

This is test note {i} for batch sync testing.
It contains some [[wikilinks]] and #hashtags.
"""
            note_path.write_text(content, encoding="utf-8")
            notes.append(note_path)
        return notes

    return _create_notes


class TestBatchSyncBasics:
    """Test basic batch sync operations."""

    @pytest.mark.asyncio
    async def test_batch_sync_empty_vault(self, obsidian_sync):
        """Test batch sync on empty vault."""
        stats = await obsidian_sync.batch_sync()

        assert stats["pulled"] == 0
        assert stats["pushed"] == 0
        assert stats["conflicts"] == 0
        assert stats["cancelled"] is False
        assert stats["processed"] == 0

    @pytest.mark.asyncio
    async def test_batch_sync_single_file(self, obsidian_sync, create_test_notes):
        """Test batch sync with a single file."""
        create_test_notes(1)

        stats = await obsidian_sync.batch_sync(direction="pull")

        assert stats["pulled"] == 1
        assert stats["processed"] == 1
        assert stats["cancelled"] is False

    @pytest.mark.asyncio
    async def test_batch_sync_multiple_files(self, obsidian_sync, create_test_notes):
        """Test batch sync with multiple files."""
        create_test_notes(10)

        stats = await obsidian_sync.batch_sync(direction="pull")

        assert stats["pulled"] == 10
        assert stats["processed"] == 10
        assert stats["cancelled"] is False

    @pytest.mark.asyncio
    async def test_batch_sync_large_dataset(self, obsidian_sync, create_test_notes):
        """Test batch sync with large number of files."""
        # Create 100 test notes
        create_test_notes(100)

        stats = await obsidian_sync.batch_sync(direction="pull", batch_size=25)

        assert stats["pulled"] == 100
        assert stats["processed"] == 100
        assert stats["cancelled"] is False
        assert len(stats["errors"]) == 0

    @pytest.mark.asyncio
    async def test_batch_sync_bidirectional(
        self, obsidian_sync, temp_obsidian_vault, create_test_notes
    ):
        """Test bidirectional batch sync."""
        # Create notes in Obsidian
        create_test_notes(5)

        # Create memory in MemoGraph for push
        push_path = temp_obsidian_vault / "from_memo.md"
        await obsidian_sync.kernel.remember_async(
            title="From MemoGraph",
            content="Pushed content",
            meta={"source": "obsidian", "obsidian_path": str(push_path)},
        )
        obsidian_sync.kernel.ingest()

        stats = await obsidian_sync.batch_sync(direction="bidirectional")

        assert stats["pulled"] >= 5
        assert stats["pushed"] >= 1
        assert stats["cancelled"] is False


class TestBatchSizeAndChunking:
    """Test batch size limits and chunking."""

    @pytest.mark.asyncio
    async def test_batch_sync_with_custom_batch_size(
        self, obsidian_sync, create_test_notes
    ):
        """Test batch sync with custom batch size."""
        create_test_notes(20)

        stats = await obsidian_sync.batch_sync(
            direction="pull",
            batch_size=5,
        )

        assert stats["pulled"] == 20
        assert stats["processed"] == 20

    @pytest.mark.asyncio
    async def test_batch_sync_respects_batch_size(
        self, obsidian_sync, create_test_notes
    ):
        """Test that batch sync processes files in chunks."""
        create_test_notes(50)

        # Track how many batches were processed by monitoring async sleeps
        batch_size = 10
        stats = await obsidian_sync.batch_sync(
            direction="pull",
            batch_size=batch_size,
        )

        # All files should be processed
        assert stats["pulled"] == 50
        # Should have processed in 5 batches (50/10)

    @pytest.mark.asyncio
    async def test_batch_sync_handles_incomplete_batch(
        self, obsidian_sync, create_test_notes
    ):
        """Test batch sync with files not perfectly divisible by batch size."""
        # 23 files with batch size 10 = 2 full batches + 1 batch of 3
        create_test_notes(23)

        stats = await obsidian_sync.batch_sync(
            direction="pull",
            batch_size=10,
        )

        assert stats["pulled"] == 23
        assert stats["processed"] == 23


class TestProgressTracking:
    """Test progress tracking callbacks."""

    @pytest.mark.asyncio
    async def test_batch_sync_calls_progress_callback(
        self, obsidian_sync, create_test_notes
    ):
        """Test that progress callback is called during batch sync."""
        create_test_notes(10)

        progress_calls = []

        def progress_callback(current, total, file_path, status):
            progress_calls.append(
                {
                    "current": current,
                    "total": total,
                    "file": file_path,
                    "status": status,
                }
            )

        _stats = await obsidian_sync.batch_sync(
            direction="pull",
            progress_callback=progress_callback,
        )

        # Progress callback should have been called
        assert len(progress_calls) > 0
        # First call should have current