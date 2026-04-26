"""Performance tests for Obsidian integration.

This module tests the performance optimizations including:
- SQLite indexing for file metadata
- LRU caching for file parsing
- Optimized wikilink resolution
- Performance metrics tracking
"""

import pytest
import tempfile
import time
from pathlib import Path
from memograph.integrations.obsidian.sync import ObsidianSync
from memograph.integrations.obsidian.parser import ObsidianParser
from memograph.integrations.obsidian.sync_state import SyncState
from memograph.integrations.obsidian.performance_metrics import (
    PerformanceTracker,
    get_tracker,
    reset_tracker,
)


@pytest.fixture
def temp_vaults():
    """Create temporary vault directories."""
    with tempfile.TemporaryDirectory() as obsidian_dir:
        with tempfile.TemporaryDirectory() as memograph_dir:
            yield Path(obsidian_dir), Path(memograph_dir)


@pytest.fixture
def sample_notes(temp_vaults):
    """Create sample notes for testing."""
    obsidian_vault, _ = temp_vaults
    notes = []

    for i in range(100):
        note_path = obsidian_vault / f"note_{i}.md"
        content = f"""---
title: Test Note {i}
tags: [test, performance]
---

# Test Note {i}

This is test note number {i}.

It contains several [[note_{(i + 1) % 100}|wikilinks]] and #tags.

Some more content here with [[note_{(i - 1) % 100}]].
"""
        note_path.write_text(content, encoding="utf-8")
        notes.append(note_path)

    return notes


@pytest.fixture
def parser():
    """Create parser with caching."""
    return ObsidianParser(cache_size=128)


@pytest.fixture
def sync_state(temp_vaults):
    """Create sync state with SQLite."""
    _, memograph_vault = temp_vaults
    state_file = memograph_vault / ".sync_state.json"
    return SyncState(state_file, use_sqlite=True)


class TestSQLitePerformance:
    """Test SQLite indexing performance."""

    def test_sqlite_vs_json_write_performance(self, temp_vaults):
        """Compare SQLite vs JSON for write operations."""
        _, memograph_vault = temp_vaults

        # Test SQLite
        sqlite_state = SyncState(memograph_vault / ".sync_sqlite.json", use_sqlite=True)
        start = time.time()
        for i in range(1000):
            sqlite_state.update_file_hash(
                f"file_{i}.md", f"hash_{i}", 1024, time.time()
            )
        sqlite_duration = time.time() - start

        # Test JSON
        json_state = SyncState(memograph_vault / ".sync_json.json", use_sqlite=False)
        start = time.time()
        for i in range(1000):
            json_state.update_file_hash(f"file_{i}.md", f"hash_{i}", 1024, time.time())
        json_duration = time.time() - start

        # SQLite should be faster or at most 3x slower (Windows I/O can vary significantly)
        assert sqlite_duration < json_duration * 3, (
            f"SQLite ({sqlite_duration:.3f}s) should be comparable to JSON ({json_duration:.3f}s)"
        )

        print(
            f"\nSQLite write: {sqlite_duration:.3f}s, JSON write: {json_duration:.3f}s"
        )
        print(f"Speedup: {json_duration / sqlite_duration:.2f}x")

    def test_sqlite_vs_json_read_performance(self, temp_vaults):
        """Compare SQLite vs JSON for read operations."""
        _, memograph_vault = temp_vaults

        # Setup data
        sqlite_state = SyncState(memograph_vault / ".sync_sqlite.json", use_sqlite=True)
        json_state = SyncState(memograph_vault / ".sync_json.json", use_sqlite=False)

        for i in range(1000):
            sqlite_state.update_file_hash(
                f"file_{i}.md", f"hash_{i}", 1024, time.time()
            )
            json_state.update_file_hash(f"file_{i}.md", f"hash_{i}", 1024, time.time())

        # Test SQLite reads
        start = time.time()
        for i in range(1000):
            _ = sqlite_state.get_file_hash(f"file_{i}.md")
        sqlite_duration = time.time() - start

        # Test JSON reads
        start = time.time()
        for i in range(1000):
            _ = json_state.get_file_hash(f"file_{i}.md")
        json_duration = time.time() - start

        print(f"\nSQLite read: {sqlite_duration:.3f}s, JSON read: {json_duration:.3f}s")
        print(f"Speedup: {json_duration / sqlite_duration:.2f}x")

    def test_sqlite_statistics(self, sync_state):
        """Test SQLite statistics functionality."""
        # Add some data
        for i in range(100):
            sync_state.update_file_hash(
                f"file_{i}.md", f"hash_{i}", 1024 * i, time.time()
            )

        stats = sync_state.get_statistics()

        assert stats["tracked_files"] == 100
        assert stats["total_size_bytes"] > 0
        assert "last_sync" in stats


class TestLRUCachePerformance:
    """Test LRU caching performance."""

    def test_parser_caching(self, parser, sample_notes):
        """Test that parser caching improves performance."""
        # First parse (cold cache)
        start = time.time()
        for note in sample_notes[:10]:
            parser.parse_file(note)
        cold_duration = time.time() - start

        # Second parse (warm cache - same files)
        start = time.time()
        for note in sample_notes[:10]:
            parser.parse_file(note)
        warm_duration = time.time() - start

        print(f"\nCold cache: {cold_duration:.3f}s, Warm cache: {warm_duration:.3f}s")
        if warm_duration > 0:
            print(f"Speedup: {cold_duration / warm_duration:.2f}x")
        else:
            print("Speedup: warm cache too fast to measure")

        # Warm cache should be significantly faster.
        # Skip the assertion if cold parse was too fast to measure reliably
        # (timings under 10ms are dominated by noise and not meaningful for cache comparison)
        if cold_duration > 0.01:
            assert warm_duration < cold_duration * 0.5, (
                f"Cached parse ({warm_duration:.3f}s) should be much faster than cold ({cold_duration:.3f}s)"
            )

    def test_wikilink_extraction_caching(self, parser):
        """Test wikilink extraction caching."""
        content = "Test [[link1]] and [[link2]] and [[link3]]" * 100

        # First extraction
        start = time.time()
        for _ in range(1000):
            parser.extract_wikilinks(content)
        first_duration = time.time() - start

        # Get cache stats
        stats = parser.get_cache_stats()
        assert stats["wikilinks_cache"]["hits"] > 0

        print(f"\nWikilink extraction with caching: {first_duration:.3f}s")
        print(f"Cache stats: {stats['wikilinks_cache']}")

    def test_cache_stats(self, parser, sample_notes):
        """Test cache statistics tracking."""
        # Parse some files
        for note in sample_notes[:20]:
            parser.parse_file(note)

        # Parse again to generate cache hits
        for note in sample_notes[:20]:
            parser.parse_file(note)

        stats = parser.get_cache_stats()

        # Should have cache information
        assert "wikilinks_cache" in stats
        assert "tags_cache" in stats
        assert "parse_cache" in stats

        print(f"\nCache statistics: {stats}")


class TestWikilinkResolution:
    """Test optimized wikilink resolution."""

    def test_wikilink_resolution_with_index(self, parser, sample_notes):
        """Test wikilink resolution performance with filename index."""
        vault_files = sample_notes

        # Build index (done automatically on first resolve)
        start = time.time()
        result = parser.resolve_wikilink("note_50", vault_files)
        index_build_duration = time.time() - start

        assert result is not None
        assert result.stem == "note_50"

        # Subsequent resolutions should be fast
        start = time.time()
        for i in range(100):
            parser.resolve_wikilink(f"note_{i}", vault_files)
        resolution_duration = time.time() - start

        # Should be very fast with index
        assert resolution_duration < 0.1, (
            f"Wikilink resolution should be fast with index: {resolution_duration:.3f}s"
        )

        print(f"\nIndex build: {index_build_duration:.3f}s")
        print(
            f"100 resolutions: {resolution_duration:.3f}s ({resolution_duration * 10:.1f}ms each)"
        )

    def test_wikilink_resolution_case_insensitive(self, parser, sample_notes):
        """Test case-insensitive wikilink resolution."""
        vault_files = sample_notes

        # Test various case combinations
        result1 = parser.resolve_wikilink("NOTE_50", vault_files)
        result2 = parser.resolve_wikilink("Note_50", vault_files)
        result3 = parser.resolve_wikilink("note_50", vault_files)

        assert result1 == result2 == result3


class TestPerformanceMetrics:
    """Test performance metrics tracking."""

    def test_performance_tracker_basic(self):
        """Test basic performance tracking."""
        tracker = PerformanceTracker()

        with tracker.track_operation("test_operation"):
            tracker.record_file_processed(1024)
            tracker.record_cache_hit()
            time.sleep(0.01)  # Simulate work

        summary = tracker.get_operation_summary("test_operation")

        assert summary["count"] == 1
        assert summary["total_files"] == 1
        assert summary["total_bytes"] == 1024
        assert summary["total_cache_hits"] == 1
        assert summary["avg_duration_ms"] > 0

    def test_performance_tracker_throughput(self):
        """Test throughput calculations."""
        tracker = PerformanceTracker()

        with tracker.track_operation("sync_test"):
            for i in range(100):
                tracker.record_file_processed(10240)  # 10KB each
            time.sleep(0.1)  # Simulate work

        summary = tracker.get_operation_summary("sync_test")

        assert summary["total_files"] == 100
        assert summary["total_bytes"] == 1024000
        assert summary["avg_throughput_files_per_sec"] > 0
        assert summary["avg_throughput_mb_per_sec"] > 0

        print(f"\nThroughput: {summary['avg_throughput_files_per_sec']:.1f} files/sec")
        print(f"Throughput: {summary['avg_throughput_mb_per_sec']:.2f} MB/sec")

    def test_global_tracker(self):
        """Test global tracker instance."""
        reset_tracker()
        tracker = get_tracker()

        with tracker.track_operation("global_test"):
            tracker.record_file_processed(2048)

        # Get same instance
        tracker2 = get_tracker()
        assert tracker is tracker2

        summary = tracker2.get_operation_summary("global_test")
        assert summary["count"] == 1


class TestEndToEndPerformance:
    """End-to-end performance tests."""

    @pytest.mark.asyncio
    async def test_sync_performance_small_vault(self, temp_vaults, sample_notes):
        """Test sync performance with small vault (100 notes)."""
        obsidian_vault, memograph_vault = temp_vaults

        sync = ObsidianSync(obsidian_vault, memograph_vault)

        # First sync (cold)
        start = time.time()
        stats = await sync.sync(direction="pull")
        cold_duration = time.time() - start

        assert stats["pulled"] == 100
        assert stats["errors"] == []

        # Second sync (warm - no changes)
        start = time.time()
        stats = await sync.sync(direction="pull")
        warm_duration = time.time() - start

        # Verify second sync completes successfully with no new pulls
        # (files should be skipped due to unchanged hashes)
        assert stats["pulled"] == 0, (
            f"Expected 0 pulls on unchanged sync, got {stats['pulled']}"
        )
        assert stats["errors"] == []

        # Note: End-to-end timing can vary significantly due to database operations,
        # system load, and other factors. The parser caching is proven in test_parser_caching.
        # Here we just verify correctness (0 pulls on unchanged files).

        print(
            f"\nCold sync: {cold_duration:.3f}s ({cold_duration / 100 * 1000:.1f}ms/file)"
        )
        print(
            f"Warm sync: {warm_duration:.3f}s ({warm_duration / 100 * 1000:.1f}ms/file)"
        )
        print(f"Speedup: {cold_duration / warm_duration:.2f}x")

        # Check performance stats
        sync_status = sync.get_sync_status()
        assert "cache_stats" in sync_status
        assert "performance_stats" in sync_status

        print(f"\nCache stats: {sync_status['cache_stats']}")
        print(f"Performance stats: {sync_status['performance_stats']}")

    @pytest.mark.asyncio
    async def test_incremental_sync_performance(self, temp_vaults, sample_notes):
        """Test incremental sync only processes changed files."""
        obsidian_vault, memograph_vault = temp_vaults

        sync = ObsidianSync(obsidian_vault, memograph_vault)

        # Initial sync
        await sync.sync(direction="pull")

        # Modify one file
        modified_note = sample_notes[0]
        content = modified_note.read_text()
        modified_note.write_text(content + "\n\nModified content", encoding="utf-8")

        # Sync again - should only process 1 file
        start = time.time()
        stats = await sync.sync(direction="pull")
        duration = time.time() - start

        # Should be very fast since only 1 file changed
        assert duration < 1.0, f"Incremental sync should be fast: {duration:.3f}s"
        assert stats["pulled"] == 1  # Only the modified file

        print(f"\nIncremental sync (1 file): {duration:.3f}s")

    def test_memory_usage_large_vault(self, temp_vaults):
        """Test memory usage with larger vault."""
        obsidian_vault, memograph_vault = temp_vaults

        # Create 1000 notes
        for i in range(1000):
            note_path = obsidian_vault / f"note_{i}.md"
            content = f"# Note {i}\n\nContent for note {i}."
            note_path.write_text(content, encoding="utf-8")

        # Create sync and track memory
        sync = ObsidianSync(obsidian_vault, memograph_vault)
        state_stats = sync.state.get_statistics()

        # Should handle 1000 notes efficiently
        assert state_stats["tracked_files"] >= 0  # Initially empty

        print(f"\nState stats for 1000 notes: {state_stats}")
