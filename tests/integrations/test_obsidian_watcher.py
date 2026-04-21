"""Tests for Obsidian vault file system watcher."""

import pytest
import asyncio
import time
from unittest.mock import MagicMock, AsyncMock
from memograph.integrations.obsidian.watcher import ObsidianWatcher


@pytest.fixture
def vault_path(tmp_path):
    """Create a temporary vault directory."""
    vault = tmp_path / "test_vault"
    vault.mkdir()
    return vault


@pytest.fixture
def mock_callback():
    """Create a mock synchronous callback."""
    return MagicMock()


@pytest.fixture
def mock_async_callback():
    """Create a mock asynchronous callback."""
    return AsyncMock()


class TestObsidianWatcherInitialization:
    """Test watcher initialization."""

    def test_init_with_valid_path(self, vault_path):
        """Test initialization with valid vault path."""
        watcher = ObsidianWatcher(vault_path, lambda p, e: None)
        assert watcher.vault_path == vault_path
        assert watcher.observer is None

    def test_init_with_string_path(self, vault_path):
        """Test initialization with string path."""
        watcher = ObsidianWatcher(str(vault_path), lambda p, e: None)
        assert watcher.vault_path == vault_path

    def test_init_with_nonexistent_path(self, tmp_path):
        """Test initialization with nonexistent path raises error."""
        nonexistent = tmp_path / "nonexistent"
        with pytest.raises(ValueError, match="does not exist"):
            ObsidianWatcher(nonexistent, lambda p, e: None)

    def test_init_with_file_path(self, tmp_path):
        """Test initialization with file path raises error."""
        file_path = tmp_path / "file.txt"
        file_path.touch()
        with pytest.raises(ValueError, match="not a directory"):
            ObsidianWatcher(file_path, lambda p, e: None)


class TestObsidianWatcherOperations:
    """Test watcher start/stop operations."""

    def test_start_watcher(self, vault_path, mock_callback):
        """Test starting the watcher."""
        watcher = ObsidianWatcher(vault_path, mock_callback)
        watcher.start()

        assert watcher.observer is not None
        assert watcher.observer.is_alive()

        watcher.stop()

    def test_stop_watcher(self, vault_path, mock_callback):
        """Test stopping the watcher."""
        watcher = ObsidianWatcher(vault_path, mock_callback)
        watcher.start()
        watcher.stop()

        assert watcher.observer is None

    def test_start_already_running_watcher(self, vault_path, mock_callback):
        """Test starting an already running watcher."""
        watcher = ObsidianWatcher(vault_path, mock_callback)
        watcher.start()

        # Start again should not fail
        watcher.start()

        watcher.stop()

    def test_stop_not_running_watcher(self, vault_path, mock_callback):
        """Test stopping a watcher that isn't running."""
        watcher = ObsidianWatcher(vault_path, mock_callback)
        # Should not fail
        watcher.stop()

    def test_context_manager(self, vault_path, mock_callback):
        """Test using watcher as context manager."""
        with ObsidianWatcher(vault_path, mock_callback) as watcher:
            assert watcher.observer is not None
            assert watcher.observer.is_alive()

        # Observer should be stopped after exiting context
        assert watcher.observer is None


class TestObsidianWatcherFileEvents:
    """Test file event detection."""

    def test_detects_markdown_file_creation(self, vault_path, mock_callback):
        """Test watcher detects markdown file creation."""
        watcher = ObsidianWatcher(vault_path, mock_callback)
        watcher.start()

        # Give watcher time to start
        time.sleep(0.1)

        # Create a markdown file
        test_file = vault_path / "test.md"
        test_file.write_text("# Test Note")

        # Give watcher time to detect and debounce (default debounce is 0.3s)
        time.sleep(0.5)

        watcher.stop()

        # Verify callback was called
        assert mock_callback.called
        call_args = mock_callback.call_args[0]
        assert str(test_file) in call_args[0]
        # On Windows, file creation may trigger 'modified' instead of 'created'
        assert call_args[1] in ("created", "modified")

    def test_detects_markdown_file_modification(self, vault_path, mock_callback):
        """Test watcher detects markdown file modification."""
        # Create file before starting watcher
        test_file = vault_path / "test.md"
        test_file.write_text("# Initial Content")

        watcher = ObsidianWatcher(vault_path, mock_callback)
        watcher.start()

        # Give watcher time to start
        time.sleep(0.1)

        # Modify the file
        test_file.write_text("# Modified Content")

        # Give watcher time to detect and debounce (default debounce is 0.3s)
        time.sleep(0.5)

        watcher.stop()

        # Verify callback was called
        assert mock_callback.called
        call_args = mock_callback.call_args[0]
        assert str(test_file) in call_args[0]
        assert call_args[1] == "modified"

    def test_detects_markdown_file_deletion(self, vault_path, mock_callback):
        """Test watcher detects markdown file deletion."""
        # Create file before starting watcher
        test_file = vault_path / "test.md"
        test_file.write_text("# Test Note")

        watcher = ObsidianWatcher(vault_path, mock_callback)
        watcher.start()

        # Give watcher time to start
        time.sleep(0.1)

        # Delete the file
        test_file.unlink()

        # Give watcher time to detect and debounce (default debounce is 0.3s)
        time.sleep(0.5)

        watcher.stop()

        # Verify callback was called
        assert mock_callback.called
        call_args = mock_callback.call_args[0]
        assert str(test_file) in call_args[0]
        assert call_args[1] == "deleted"

    def test_ignores_non_markdown_files(self, vault_path, mock_callback):
        """Test watcher ignores non-markdown files."""
        watcher = ObsidianWatcher(vault_path, mock_callback)
        watcher.start()

        # Give watcher time to start
        time.sleep(0.1)

        # Create non-markdown files
        (vault_path / "test.txt").write_text("text file")
        (vault_path / "test.pdf").write_text("pdf file")
        (vault_path / "test.json").write_text('{"key": "value"}')

        # Give watcher time to potentially detect (it shouldn't)
        time.sleep(0.2)

        watcher.stop()

        # Verify callback was NOT called
        assert not mock_callback.called

    def test_ignores_directory_events(self, vault_path, mock_callback):
        """Test watcher ignores directory events."""
        watcher = ObsidianWatcher(vault_path, mock_callback)
        watcher.start()

        # Give watcher time to start
        time.sleep(0.1)

        # Create a subdirectory
        (vault_path / "subfolder").mkdir()

        # Give watcher time to potentially detect (it shouldn't)
        time.sleep(0.2)

        watcher.stop()

        # Verify callback was NOT called
        assert not mock_callback.called

    def test_detects_files_in_subdirectories(self, vault_path, mock_callback):
        """Test watcher detects markdown files in subdirectories."""
        # Create subdirectory
        subdir = vault_path / "notes"
        subdir.mkdir()

        watcher = ObsidianWatcher(vault_path, mock_callback)
        watcher.start()

        # Give watcher time to start
        time.sleep(0.1)

        # Create markdown file in subdirectory
        test_file = subdir / "nested.md"
        test_file.write_text("# Nested Note")

        # Give watcher time to detect and debounce (default debounce is 0.3s)
        time.sleep(0.5)

        watcher.stop()

        # Verify callback was called
        assert mock_callback.called
        call_args = mock_callback.call_args[0]
        assert str(test_file) in call_args[0]


class TestObsidianWatcherAsyncCallback:
    """Test watcher with async callbacks."""

    @pytest.mark.asyncio
    async def test_async_callback_on_file_creation(
        self, vault_path, mock_async_callback
    ):
        """Test watcher with async callback on file creation."""
        loop = asyncio.get_event_loop()

        watcher = ObsidianWatcher(vault_path, mock_async_callback)
        watcher.start(loop=loop)

        # Give watcher time to start
        await asyncio.sleep(0.1)

        # Create a markdown file
        test_file = vault_path / "async_test.md"
        test_file.write_text("# Async Test")

        # Give watcher time to detect and process (debounce is 0.3s)
        await asyncio.sleep(0.5)

        watcher.stop()

        # Verify async callback was called
        assert mock_async_callback.called
        call_args = mock_async_callback.call_args[0]
        assert str(test_file) in call_args[0]
        # On Windows, file creation may trigger 'modified' instead of 'created'
        assert call_args[1] in ("created", "modified")


class TestObsidianWatcherEdgeCases:
    """Test edge cases and error handling."""

    def test_callback_exception_handling(self, vault_path):
        """Test watcher handles callback exceptions gracefully."""

        def failing_callback(path, event_type):
            raise ValueError("Callback error")

        watcher = ObsidianWatcher(vault_path, failing_callback)
        watcher.start()

        # Give watcher time to start
        time.sleep(0.1)

        # Create a file that will trigger the failing callback
        test_file = vault_path / "error_test.md"
        test_file.write_text("# Error Test")

        # Give watcher time to process (should not crash)
        time.sleep(0.2)

        # Watcher should still be running
        assert watcher.observer is not None
        assert watcher.observer.is_alive()

        watcher.stop()

    def test_multiple_rapid_events(self, vault_path, mock_callback):
        """Test watcher handles multiple rapid events."""
        watcher = ObsidianWatcher(vault_path, mock_callback)
        watcher.start()

        # Give watcher time to start
        time.sleep(0.1)

        # Create multiple files rapidly
        for i in range(5):
            test_file = vault_path / f"test_{i}.md"
            test_file.write_text(f"# Test Note {i}")

        # Give watcher time to detect all and debounce (default debounce is 0.3s)
        time.sleep(0.6)

        watcher.stop()

        # Verify callback was called multiple times
        assert mock_callback.call_count >= 5

    def test_file_with_special_characters(self, vault_path, mock_callback):
        """Test watcher handles files with special characters in names."""
        watcher = ObsidianWatcher(vault_path, mock_callback)
        watcher.start()

        # Give watcher time to start
        time.sleep(0.1)

        # Create file with special characters
        test_file = vault_path / "test note with spaces & special chars!.md"
        test_file.write_text("# Special Characters")

        # Give watcher time to detect and debounce (default debounce is 0.3s)
        time.sleep(0.5)

        watcher.stop()

        # Verify callback was called
        assert mock_callback.called
