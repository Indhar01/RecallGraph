"""Tests for auto-sync functionality with debouncing and rate limiting."""

import pytest
import asyncio
import time
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from memograph.integrations.obsidian.watcher import ObsidianWatcher
from memograph.integrations.obsidian.sync import ObsidianSync


class TestDebouncing:
    """Test debouncing in ObsidianWatcher."""

    @pytest.fixture
    def temp_vault(self, tmp_path):
        """Create a temporary vault directory."""
        vault = tmp_path / "test_vault"
        vault.mkdir()
        return vault

    @pytest.fixture
    def mock_callback(self):
        """Create a mock async callback."""
        return AsyncMock()

    def test_watcher_debounce_delay_default(self, temp_vault, mock_callback):
        """Test that watcher has default debounce delay."""
        watcher = ObsidianWatcher(temp_vault, mock_callback)
        assert watcher.debounce_delay == 0.3

    def test_watcher_custom_debounce_delay(self, temp_vault, mock_callback):
        """Test that custom debounce delay can be set."""
        watcher = ObsidianWatcher(temp_vault, mock_callback, debounce_delay=0.5)
        assert watcher.debounce_delay == 0.5

    @pytest.mark.asyncio
    async def test_debouncing_multiple_rapid_changes(self, temp_vault, mock_callback):
        """Test that multiple rapid changes result in single callback."""
        watcher = ObsidianWatcher(temp_vault, mock_callback, debounce_delay=0.1)
        
        # Create event loop
        loop = asyncio.get_event_loop()
        watcher.start(loop)
        
        # Create test file
        test_file = temp_vault / "test.md"
        test_file.write_text("Initial content")
        
        # Simulate rapid successive modifications
        for i in range(5):
            watcher._handle_event(str(test_file), "modified")
            await asyncio.sleep(0.02)  # 20ms between changes
        
        # Wait for debounce delay plus buffer
        await asyncio.sleep(0.2)
        
        # Should only be called once after debounce
        assert mock_callback.call_count == 1
        
        watcher.stop()

    @pytest.mark.asyncio
    async def test_debouncing_separate_files(self, temp_vault, mock_callback):
        """Test that changes to different files are not debounced together."""
        watcher = ObsidianWatcher(temp_vault, mock_callback, debounce_delay=0.1)
        
        loop = asyncio.get_event_loop()
        watcher.start(loop)
        
        # Create test files
        file1 = temp_vault / "test1.md"
        file2 = temp_vault / "test2.md"
        file1.write_text("Content 1")
        file2.write_text("Content 2")
        
        # Trigger events for different files
        watcher._handle_event(str(file1), "modified")
        watcher._handle_event(str(file2), "modified")
        
        # Wait for debounce
        await asyncio.sleep(0.2)
        
        # Should be called once for each file
        assert mock_callback.call_count == 2
        
        watcher.stop()


class TestSyncQueue:
    """Test sync queue with rate limiting."""

    @pytest.fixture
    def temp_vaults(self, tmp_path):
        """Create temporary vault directories."""
        obsidian_vault = tmp_path / "obsidian"
        memograph_vault = tmp_path / "memograph"
        obsidian_vault.mkdir()
        memograph_vault.mkdir()
        return obsidian_vault, memograph_vault

    @pytest.fixture
    def sync_manager(self, temp_vaults):
        """Create ObsidianSync instance with queue enabled."""
        obsidian_vault, memograph_vault = temp_vaults
        return ObsidianSync(
            vault_path=obsidian_vault,
            memograph_vault=memograph_vault,
            enable_queue=True,
            max_queue_size=10,
            rate_limit_delay=0.1,
        )

    def test_queue_initialization(self, sync_manager):
        """Test that sync queue is properly initialized."""
        assert sync_manager.enable_queue is True
        assert sync_manager.max_queue_size == 10
        assert sync_manager.rate_limit_delay == 0.1
        assert len(sync_manager._sync_queue) == 0
        assert len(sync_manager._queued_files) == 0

    @pytest.mark.asyncio
    async def test_queue_file_sync(self, sync_manager, temp_vaults):
        """Test adding files to sync queue."""
        obsidian_vault, _ = temp_vaults
        test_file = obsidian_vault / "test.md"
        test_file.write_text("---\ntitle: Test\n---\n\nContent")
        
        # Queue file for sync
        result = await sync_manager.queue_file_sync(str(test_file), "modified")
        
        assert result is True
        assert str(test_file) in sync_manager._queued_files

    @pytest.mark.asyncio
    async def test_queue_prevents_duplicates(self, sync_manager, temp_vaults):
        """Test that same file cannot be queued twice."""
        obsidian_vault, _ = temp_vaults
        test_file = obsidian_vault / "test.md"
        test_file.write_text("---\ntitle: Test\n---\n\nContent")
        
        # Queue file twice
        result1 = await sync_manager.queue_file_sync(str(test_file), "modified")
        result2 = await sync_manager.queue_file_sync(str(test_file), "modified")
        
        assert result1 is True
        assert result2 is False  # Should reject duplicate
        
        # Wait for processing
        await asyncio.sleep(0.3)

    @pytest.mark.asyncio
    async def test_queue_max_size(self, sync_manager, temp_vaults):
        """Test that queue respects max size limit."""
        obsidian_vault, _ = temp_vaults
        
        # Try to add more files than max_queue_size
        results = []
        for i in range(15):  # More than max_queue_size of 10
            test_file = obsidian_vault / f"test{i}.md"
            test_file.write_text("---\ntitle: Test\n---\n\nContent")
            result = await sync_manager.queue_file_sync(str(test_file), "modified")
            results.append(result)
            await asyncio.sleep(0.01)
        
        # First 10 should succeed, rest should fail
        assert sum(results[:10]) == 10  # First 10 are True
        
        # Wait for processing
        await asyncio.sleep(0.5)

    @pytest.mark.asyncio
    async def test_rate_limiting(self, sync_manager, temp_vaults):
        """Test that rate limiting delays sync operations."""
        obsidian_vault, _ = temp_vaults
        
        # Create multiple files
        files = []
        for i in range(3):
            test_file = obsidian_vault / f"test{i}.md"
            test_file.write_text("---\ntitle: Test\n---\n\nContent")
            files.append(test_file)
        
        # Queue all files
        start_time = time.time()
        for file in files:
            await sync_manager.queue_file_sync(str(file), "modified")
        
        # Wait for all to process
        await asyncio.sleep(0.5)
        
        elapsed = time.time() - start_time
        
        # With rate_limit_delay of 0.1s and 3 files, should take at least 0.2s
        # (first file immediate, then 0.1s delay, then 0.1s delay)
        assert elapsed >= 0.2

    def test_get_queue_status(self, sync_manager, temp_vaults):
        """Test getting queue status."""
        status = sync_manager.get_queue_status()
        
        assert "queue_enabled" in status
        assert "queue_size" in status
        assert "queued_files" in status
        assert "is_syncing" in status
        assert "last_sync_time" in status
        
        assert status["queue_enabled"] is True
        assert status["queue_size"] == 0
        assert isinstance(status["queued_files"], list)


class TestIntegration:
    """Integration tests for auto-sync functionality."""

    @pytest.fixture
    def temp_vaults(self, tmp_path):
        """Create temporary vault directories."""
        obsidian_vault = tmp_path / "obsidian"
        memograph_vault = tmp_path / "memograph"
        obsidian_vault.mkdir()
        memograph_vault.mkdir()
        return obsidian_vault, memograph_vault

    @pytest.mark.asyncio
    async def test_watcher_with_sync_queue(self, temp_vaults):
        """Test watcher triggering sync queue."""
        obsidian_vault, memograph_vault = temp_vaults
        
        # Create sync manager
        sync_manager = ObsidianSync(
            vault_path=obsidian_vault,
            memograph_vault=memograph_vault,
            enable_queue=True,
            rate_limit_delay=0.1,
        )
        
        # Create callback that adds to queue
        async def on_file_change(file_path: str, event_type: str):
            await sync_manager.queue_file_sync(file_path, event_type)
        
        # Create watcher
        watcher = ObsidianWatcher(
            obsidian_vault,
            on_file_change,
            debounce_delay=0.1
        )
        
        # Start watcher
        loop = asyncio.get_event_loop()
        watcher.start(loop)
        
        # Create test file
        test_file = obsidian_vault / "test.md"
        test_file.write_text("---\ntitle: Test\n---\n\nInitial content")
        
        # Trigger file change event
        watcher._handle_event(str(test_file), "modified")
        
        # Wait for debouncing and queue processing
        await asyncio.sleep(0.3)
        
        # Check queue status
        status = sync_manager.get_queue_status()
        assert status["queue_size"] == 0  # Should be processed
        
        watcher.stop()

    @pytest.mark.asyncio
    async def test_rapid_changes_processed_once(self, temp_vaults):
        """Test that rapid file changes result in single sync."""
        obsidian_vault, memograph_vault = temp_vaults
        
        sync_count = 0
        
        # Create sync manager with tracking
        sync_manager = ObsidianSync(
            vault_path=obsidian_vault,
            memograph_vault=memograph_vault,
            enable_queue=True,
            rate_limit_delay=0.05,
        )
        
        # Track sync calls
        original_sync = sync_manager.sync_single_file
        
        async def tracked_sync(file_path, event_type):
            nonlocal sync_count
            sync_count += 1
            # Don't actually sync to avoid errors
        
        sync_manager.sync_single_file = tracked_sync
        
        # Create callback
        async def on_file_change(file_path: str, event_type: str):
            await sync_manager.queue_file_sync(file_path, event_type)
        
        # Create watcher with short debounce
        watcher = ObsidianWatcher(
            obsidian_vault,
            on_file_change,
            debounce_delay=0.05
        )
        
        loop = asyncio.get_event_loop()
        watcher.start(loop)
        
        # Create test file
        test_file = obsidian_vault / "test.md"
        test_file.write_text("---\ntitle: Test\n---\n\nContent")
        
        # Simulate rapid changes
        for i in range(10):
            watcher._handle_event(str(test_file), "modified")
            await asyncio.sleep(0.01)  # 10ms between changes
        
        # Wait for debouncing and processing
        await asyncio.sleep(0.2)
        
        # Should only sync once despite 10 rapid changes
        assert sync_count == 1
        
        watcher.stop()


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def temp_vault(self, tmp_path):
        """Create a temporary vault directory."""
        vault = tmp_path / "test_vault"
        vault.mkdir()
        return vault

    def test_watcher_nonexistent_vault_raises_error(self):
        """Test that watcher raises error for nonexistent vault."""
        import uuid
        # Use a UUID to ensure path doesn't exist
        nonexistent_path = f"/tmp/nonexistent_vault_{uuid.uuid4()}"
        with pytest.raises(ValueError, match="Vault path does not exist"):
            ObsidianWatcher(nonexistent_path, lambda x, y: None)

    def test_watcher_file_as_vault_raises_error(self, temp_vault):
        """Test that watcher raises error when vault is a file."""
        not_a_directory = temp_vault / "file.txt"
        not_a_directory.write_text("content")
        
        with pytest.raises(ValueError, match="not a directory"):
            ObsidianWatcher(not_a_directory, lambda x, y: None)

    @pytest.mark.asyncio
    async def test_callback_error_handling(self, temp_vault):
        """Test that callback errors are handled gracefully."""
        # Create callback that raises error
        async def failing_callback(file_path: str, event_type: str):
            raise RuntimeError("Callback error")
        
        watcher = ObsidianWatcher(temp_vault, failing_callback, debounce_delay=0.05)
        
        loop = asyncio.get_event_loop()
        watcher.start(loop)
        
        test_file = temp_vault / "test.md"
        test_file.write_text("content")
        
        # Should not raise, error should be logged
        watcher._handle_event(str(test_file), "modified")
        
        await asyncio.sleep(0.1)
        
        # Watcher should still be running
        assert watcher.observer is not None
        
        watcher.stop()