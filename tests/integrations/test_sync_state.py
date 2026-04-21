"""Tests for Obsidian sync state management."""

import json
import pytest
from pathlib import Path
from datetime import datetime
from memograph.integrations.obsidian.sync_state import SyncState


@pytest.fixture
def temp_state_file(tmp_path):
    """Create a temporary state file path."""
    return tmp_path / ".sync_state.json"


@pytest.fixture
def sync_state(temp_state_file):
    """Create a SyncState instance with temporary file (using JSON mode)."""
    return SyncState(temp_state_file, use_sqlite=False)


class TestSyncStateInitialization:
    """Test SyncState initialization and loading."""

    def test_init_creates_default_state(self, sync_state):
        """Test that initialization creates default state."""
        assert sync_state.state["last_sync"] is None
        assert sync_state.state["file_hashes"] == {}
        assert sync_state.state["conflicts"] == []

    def test_load_nonexistent_file_returns_default(self, temp_state_file):
        """Test loading from nonexistent file returns default state."""
        state = SyncState(temp_state_file, use_sqlite=False)
        assert state.state == {"last_sync": None, "file_hashes": {}, "conflicts": []}

    def test_load_existing_file(self, temp_state_file):
        """Test loading from existing state file."""
        # Create a state file
        test_data = {
            "last_sync": "2024-01-01T00:00:00",
            "file_hashes": {
                "test.md": {"hash": "abc123", "timestamp": "2024-01-01T00:00:00"}
            },
            "conflicts": [],
        }
        temp_state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_state_file, "w") as f:
            json.dump(test_data, f)

        # Load and verify
        state = SyncState(temp_state_file, use_sqlite=False)
        assert state.state["last_sync"] == "2024-01-01T00:00:00"
        assert "test.md" in state.state["file_hashes"]

    def test_load_corrupted_file_returns_default(self, temp_state_file):
        """Test loading corrupted file returns default state."""
        # Create corrupted file
        temp_state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_state_file, "w") as f:
            f.write("invalid json {")

        # Should return default state
        state = SyncState(temp_state_file, use_sqlite=False)
        assert state.state == {"last_sync": None, "file_hashes": {}, "conflicts": []}


class TestSyncStatePersistence:
    """Test state persistence across restarts."""

    def test_save_state_creates_file(self, sync_state, temp_state_file):
        """Test that save_state creates the file."""
        sync_state.save_state()
        assert temp_state_file.exists()

    def test_save_state_creates_directories(self, tmp_path):
        """Test that save_state creates parent directories."""
        nested_path = tmp_path / "nested" / "dir" / "state.json"
        state = SyncState(nested_path, use_sqlite=False)
        state.save_state()
        assert nested_path.exists()

    def test_state_persists_across_instances(self, temp_state_file):
        """Test that state persists across multiple instances."""
        # Create and modify state
        state1 = SyncState(temp_state_file, use_sqlite=False)
        state1.update_file_hash("test.md", "hash123")

        # Load in new instance
        state2 = SyncState(temp_state_file, use_sqlite=False)
        assert state2.get_file_hash("test.md") == "hash123"

    def test_save_state_writes_valid_json(self, sync_state, temp_state_file):
        """Test that saved state is valid JSON."""
        sync_state.update_file_hash("test.md", "hash123")

        # Read and parse JSON
        with open(temp_state_file, "r") as f:
            data = json.load(f)

        assert "file_hashes" in data
        assert "last_sync" in data
        assert "conflicts" in data


class TestFileHashTracking:
    """Test file hash tracking functionality."""

    def test_update_file_hash(self, sync_state):
        """Test updating file hash."""
        sync_state.update_file_hash("test.md", "abc123")

        assert "test.md" in sync_state.state["file_hashes"]
        assert sync_state.state["file_hashes"]["test.md"]["hash"] == "abc123"
        assert "timestamp" in sync_state.state["file_hashes"]["test.md"]

    def test_update_file_hash_includes_timestamp(self, sync_state):
        """Test that updating hash includes timestamp."""
        before = datetime.now()
        sync_state.update_file_hash("test.md", "abc123")
        after = datetime.now()

        timestamp_str = sync_state.state["file_hashes"]["test.md"]["timestamp"]
        timestamp = datetime.fromisoformat(timestamp_str)

        assert before <= timestamp <= after

    def test_get_file_hash_existing_file(self, sync_state):
        """Test getting hash for existing file."""
        sync_state.update_file_hash("test.md", "abc123")
        assert sync_state.get_file_hash("test.md") == "abc123"

    def test_get_file_hash_nonexistent_file(self, sync_state):
        """Test getting hash for nonexistent file returns None."""
        assert sync_state.get_file_hash("nonexistent.md") is None

    def test_get_file_timestamp(self, sync_state):
        """Test getting timestamp for file."""
        sync_state.update_file_hash("test.md", "abc123")
        timestamp = sync_state.get_file_timestamp("test.md")

        assert timestamp is not None
        # Verify it's a valid ISO timestamp
        datetime.fromisoformat(timestamp)

    def test_get_file_timestamp_nonexistent(self, sync_state):
        """Test getting timestamp for nonexistent file."""
        assert sync_state.get_file_timestamp("nonexistent.md") is None

    def test_update_existing_file_hash(self, sync_state):
        """Test updating hash for already tracked file."""
        sync_state.update_file_hash("test.md", "hash1")
        sync_state.update_file_hash("test.md", "hash2")

        assert sync_state.get_file_hash("test.md") == "hash2"

    def test_has_file_changed_new_file(self, sync_state):
        """Test has_file_changed for untracked file."""
        assert sync_state.has_file_changed("new.md", "hash123") is True

    def test_has_file_changed_same_hash(self, sync_state):
        """Test has_file_changed with same hash."""
        sync_state.update_file_hash("test.md", "hash123")
        assert sync_state.has_file_changed("test.md", "hash123") is False

    def test_has_file_changed_different_hash(self, sync_state):
        """Test has_file_changed with different hash."""
        sync_state.update_file_hash("test.md", "hash1")
        assert sync_state.has_file_changed("test.md", "hash2") is True


class TestSyncTimestamp:
    """Test sync timestamp tracking."""

    def test_mark_synced_updates_timestamp(self, sync_state):
        """Test that mark_synced updates last_sync."""
        before = datetime.now()
        sync_state.mark_synced()
        after = datetime.now()

        last_sync = sync_state.get_last_sync()
        assert last_sync is not None
        assert before <= last_sync <= after

    def test_mark_synced_multiple_times(self, sync_state):
        """Test calling mark_synced multiple times."""
        sync_state.mark_synced()
        first_sync = sync_state.get_last_sync()

        # Small delay to ensure different timestamp
        import time

        time.sleep(0.01)

        sync_state.mark_synced()
        second_sync = sync_state.get_last_sync()

        assert second_sync > first_sync

    def test_get_last_sync_never_synced(self, sync_state):
        """Test get_last_sync when never synced."""
        assert sync_state.get_last_sync() is None

    def test_get_last_sync_returns_datetime(self, sync_state):
        """Test that get_last_sync returns datetime object."""
        sync_state.mark_synced()
        last_sync = sync_state.get_last_sync()

        assert isinstance(last_sync, datetime)


class TestConflictManagement:
    """Test conflict logging and resolution."""

    def test_add_conflict(self, sync_state):
        """Test adding a conflict."""
        sync_state.add_conflict("test.md", "Content mismatch")

        conflicts = sync_state.get_conflicts()
        assert len(conflicts) == 1
        assert conflicts[0]["file_path"] == "test.md"
        assert conflicts[0]["reason"] == "Content mismatch"
        assert "timestamp" in conflicts[0]

    def test_add_multiple_conflicts(self, sync_state):
        """Test adding multiple conflicts."""
        sync_state.add_conflict("file1.md", "Reason 1")
        sync_state.add_conflict("file2.md", "Reason 2")

        conflicts = sync_state.get_conflicts()
        assert len(conflicts) == 2

    def test_get_conflicts_returns_copy(self, sync_state):
        """Test that get_conflicts returns a copy."""
        sync_state.add_conflict("test.md", "Conflict")

        conflicts1 = sync_state.get_conflicts()
        conflicts2 = sync_state.get_conflicts()

        # Modify one copy
        conflicts1.append({"test": "data"})

        # Original should be unchanged
        assert len(conflicts2) == 1
        assert len(sync_state.get_conflicts()) == 1

    def test_resolve_conflict_existing(self, sync_state):
        """Test resolving an existing conflict."""
        sync_state.add_conflict("test.md", "Conflict")

        result = sync_state.resolve_conflict("test.md")

        assert result is True
        assert len(sync_state.get_conflicts()) == 0

    def test_resolve_conflict_nonexistent(self, sync_state):
        """Test resolving nonexistent conflict."""
        result = sync_state.resolve_conflict("nonexistent.md")
        assert result is False

    def test_resolve_conflict_multiple(self, sync_state):
        """Test resolving one of multiple conflicts."""
        sync_state.add_conflict("file1.md", "Conflict 1")
        sync_state.add_conflict("file2.md", "Conflict 2")

        sync_state.resolve_conflict("file1.md")

        conflicts = sync_state.get_conflicts()
        assert len(conflicts) == 1
        assert conflicts[0]["file_path"] == "file2.md"

    def test_clear_conflicts_empty(self, sync_state):
        """Test clearing conflicts when none exist."""
        count = sync_state.clear_conflicts()
        assert count == 0

    def test_clear_conflicts_with_conflicts(self, sync_state):
        """Test clearing multiple conflicts."""
        sync_state.add_conflict("file1.md", "Conflict 1")
        sync_state.add_conflict("file2.md", "Conflict 2")

        count = sync_state.clear_conflicts()

        assert count == 2
        assert len(sync_state.get_conflicts()) == 0


class TestFileManagement:
    """Test file tracking management."""

    def test_remove_file_existing(self, sync_state):
        """Test removing tracked file."""
        sync_state.update_file_hash("test.md", "hash123")

        result = sync_state.remove_file("test.md")

        assert result is True
        assert sync_state.get_file_hash("test.md") is None

    def test_remove_file_nonexistent(self, sync_state):
        """Test removing untracked file."""
        result = sync_state.remove_file("nonexistent.md")
        assert result is False

    def test_get_tracked_files_empty(self, sync_state):
        """Test getting tracked files when none exist."""
        assert sync_state.get_tracked_files() == []

    def test_get_tracked_files_multiple(self, sync_state):
        """Test getting multiple tracked files."""
        sync_state.update_file_hash("file1.md", "hash1")
        sync_state.update_file_hash("file2.md", "hash2")
        sync_state.update_file_hash("file3.md", "hash3")

        tracked = sync_state.get_tracked_files()

        assert len(tracked) == 3
        assert "file1.md" in tracked
        assert "file2.md" in tracked
        assert "file3.md" in tracked

    def test_reset_state(self, sync_state):
        """Test resetting state to default."""
        # Add some data
        sync_state.update_file_hash("test.md", "hash123")
        sync_state.mark_synced()
        sync_state.add_conflict("test.md", "Conflict")

        # Reset
        sync_state.reset_state()

        # Verify everything is cleared
        assert sync_state.state["last_sync"] is None
        assert sync_state.state["file_hashes"] == {}
        assert sync_state.state["conflicts"] == []

    def test_reset_state_persists(self, sync_state, temp_state_file):
        """Test that reset state is saved to file."""
        sync_state.update_file_hash("test.md", "hash123")
        sync_state.reset_state()

        # Load in new instance
        new_state = SyncState(temp_state_file, use_sqlite=False)
        assert new_state.state["file_hashes"] == {}


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_file_path(self, sync_state):
        """Test handling empty file path."""
        sync_state.update_file_hash("", "hash123")
        assert sync_state.get_file_hash("") == "hash123"

    def test_unicode_file_paths(self, sync_state):
        """Test handling Unicode characters in file paths."""
        unicode_path = "тест/文件.md"
        sync_state.update_file_hash(unicode_path, "hash123")
        assert sync_state.get_file_hash(unicode_path) == "hash123"

    def test_very_long_file_path(self, sync_state):
        """Test handling very long file paths."""
        long_path = "a" * 1000 + ".md"
        sync_state.update_file_hash(long_path, "hash123")
        assert sync_state.get_file_hash(long_path) == "hash123"

    def test_special_characters_in_path(self, sync_state):
        """Test handling special characters in file paths."""
        special_path = "test/file with spaces & symbols!.md"
        sync_state.update_file_hash(special_path, "hash123")
        assert sync_state.get_file_hash(special_path) == "hash123"

    def test_empty_hash_value(self, sync_state):
        """Test handling empty hash value."""
        sync_state.update_file_hash("test.md", "")
        assert sync_state.get_file_hash("test.md") == ""

    def test_concurrent_modifications(self, sync_state):
        """Test multiple modifications in sequence."""
        # Simulate rapid updates
        for i in range(100):
            sync_state.update_file_hash(f"file{i}.md", f"hash{i}")

        # Verify all are tracked
        assert len(sync_state.get_tracked_files()) == 100
        assert sync_state.get_file_hash("file50.md") == "hash50"
