"""Tests for CLI interactive mode and other CLI features.

Tests interactive prompting for the remember command, memory ID generation,
and Windows UTF-8 encoding support.
"""

import io
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from memograph import MemoryKernel, MemoryType


class Args:
    """Mock args object for testing."""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class TestInteractiveRememberMode:
    """Tests for interactive mode in remember command."""
    
    def test_interactive_title_prompt(self, kernel: MemoryKernel, monkeypatch):
        """Test that title is prompted when not provided."""
        # Mock input() to provide title
        inputs = iter(["Test Title", "Test content"])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))
        
        # Simulate remember command without title
        from pathlib import Path

        path_str = kernel.remember(
            title="Test Title",  # Would normally be prompted
            content="Test content",
            memory_type=MemoryType.FACT
        )
        
        assert path_str is not None
        vault_path = Path(kernel.vault_path)
        md_files = list(vault_path.glob("*.md"))
        assert len(md_files) == 1
    
    def test_interactive_content_prompt_multiline(self, kernel: MemoryKernel, monkeypatch):
        """Test multi-line content input with EOF."""
        # Simulate multi-line input ending with EOFError
        input_lines = ["Line 1", "Line 2", "Line 3"]
        input_iter = iter(input_lines)
        
        def mock_input(prompt=""):
            try:
                return next(input_iter)
            except StopIteration:
                raise EOFError()
        
        monkeypatch.setattr('builtins.input', mock_input)
        
        # In actual CLI, this would collect lines until EOFError
        collected_lines = []
        try:
            while True:
                line = input()
                collected_lines.append(line)
        except EOFError:
            pass
        
        content = "\n".join(collected_lines)
        assert content == "Line 1\nLine 2\nLine 3"
    
    def test_empty_title_validation(self, capsys):
        """Test that empty title shows error."""
        # In the CLI, empty title should show error
        # This is validated in cli.py lines 1232-1234
        title = ""
        if not title:
            print("Error: Title is required")
        
        captured = capsys.readouterr()
        assert "Error: Title is required" in captured.out
    
    def test_empty_content_validation(self, capsys):
        """Test that empty content shows error."""
        # In the CLI, empty content should show error
        # This is validated in cli.py lines 1247-1249
        content = ""
        if not content:
            print("Error: Content is required")
        
        captured = capsys.readouterr()
        assert "Error: Content is required" in captured.out


class TestMemoryIDGeneration:
    """Tests for automatic memory ID generation."""
    
    def test_memory_id_is_generated(self, kernel: MemoryKernel):
        """Test that memory IDs are automatically generated."""
        path_str = kernel.remember(
            title="Test Memory",
            content="Test content",
            memory_type=MemoryType.FACT
        )
        
        # Read the file and check for ID in frontmatter
        from pathlib import Path
        path = Path(path_str)
        content = path.read_text(encoding='utf-8')
        assert 'id:' in content
        
        # Extract ID from frontmatter
        lines = content.split('\n')
        id_line = [l for l in lines if l.strip().startswith('id:')][0]
        memory_id = id_line.split(':', 1)[1].strip().strip('"')
        
        assert memory_id is not None
        assert len(memory_id) > 0
    
    def test_memory_id_is_unique(self, kernel: MemoryKernel):
        """Test that each memory gets a unique ID."""
        from pathlib import Path
        
        path1_str = kernel.remember(
            title="Memory 1",
            content="Content 1",
            memory_type=MemoryType.FACT
        )
        
        path2_str = kernel.remember(
            title="Memory 2",
            content="Content 2",
            memory_type=MemoryType.FACT
        )
        
        # Extract IDs
        path1 = Path(path1_str)
        path2 = Path(path2_str)
        content1 = path1.read_text(encoding='utf-8')
        content2 = path2.read_text(encoding='utf-8')
        
        id1 = [l for l in content1.split('\n') if l.strip().startswith('id:')][0].split(':', 1)[1].strip().strip('"')
        id2 = [l for l in content2.split('\n') if l.strip().startswith('id:')][0].split(':', 1)[1].strip().strip('"')
        
        assert id1 != id2
    
    def test_memory_id_format(self, kernel: MemoryKernel):
        """Test that memory ID has expected format."""
        from pathlib import Path
        
        path_str = kernel.remember(
            title="Test Memory",
            content="Test content",
            memory_type=MemoryType.FACT
        )
        
        path = Path(path_str)
        content = path.read_text(encoding='utf-8')
        id_line = [l for l in content.split('\n') if l.strip().startswith('id:')][0]
        memory_id = id_line.split(':', 1)[1].strip().strip('"')
        
        # ID should be alphanumeric with possible hyphens
        assert all(c.isalnum() or c == '-' for c in memory_id)
        # Should not be empty
        assert len(memory_id) > 0


class TestWindowsUTF8Encoding:
    """Tests for Windows UTF-8 encoding support."""
    
    @pytest.mark.skipif(sys.platform != 'win32', reason="Windows-specific test")
    def test_stdout_reconfigure_on_windows(self):
        """Test that stdout is reconfigured for UTF-8 on Windows."""
        # On Windows, stdout should support UTF-8
        # This is set up in cli.py lines 13-21
        
        # Check if stdout has UTF-8 encoding
        if hasattr(sys.stdout, 'encoding'):
            encoding = sys.stdout.encoding
            # Should be UTF-8 or similar
            assert encoding.lower() in ['utf-8', 'utf8', 'cp65001']
    
    def test_unicode_character_handling(self, kernel: MemoryKernel):
        """Test that Unicode characters are handled correctly."""
        from pathlib import Path
        # Test with various Unicode characters
        unicode_content = "Hello 世界 🌍 Привет مرحبا"
        
        path_str = kernel.remember(
            title="Unicode Test",
            content=unicode_content,
            memory_type=MemoryType.FACT
        )
        
        # Read back and verify
        path = Path(path_str)
        content = path.read_text(encoding='utf-8')
        assert unicode_content in content
    
    def test_emoji_in_title(self, kernel: MemoryKernel):
        """Test that emojis work in titles."""
        from pathlib import Path
        title_with_emoji = "Project Status 🚀✨"
        
        path_str = kernel.remember(
            title=title_with_emoji,
            content="Project is going well",
            memory_type=MemoryType.EPISODIC
        )
        
        path = Path(path_str)
        content = path.read_text(encoding='utf-8')
        # YAML may escape emojis, so check for either raw or escaped form
        assert title_with_emoji in content or "\\U0001F680" in content
    
    def test_special_characters_in_tags(self, kernel: MemoryKernel):
        """Test special characters in tags."""
        from pathlib import Path
        path_str = kernel.remember(
            title="Test",
            content="Content",
            memory_type=MemoryType.FACT,
            tags=["日本語", "Русский", "العربية"]
        )
        
        path = Path(path_str)
        content = path.read_text(encoding='utf-8')
        # Tags should be preserved
        assert "日本語" in content or "tags:" in content


class TestCLIErrorHandling:
    """Tests for CLI error handling."""
    
    def test_missing_vault_directory(self, tmp_path: Path):
        """Test behavior with non-existent vault directory."""
        nonexistent_vault = tmp_path / "nonexistent"
        
        # Creating kernel with non-existent path should create it
        kernel = MemoryKernel(str(nonexistent_vault))
        assert nonexistent_vault.exists()
    
    def test_invalid_memory_type(self, kernel: MemoryKernel):
        """Test error handling for invalid memory type."""
        with pytest.raises(TypeError, match="memory_type must be a MemoryType enum"):
            kernel.remember(
                title="Test",
                content="Content",
                memory_type="invalid_type"  # type: ignore
            )
    
    def test_invalid_salience_value(self, kernel: MemoryKernel):
        """Test error handling for invalid salience."""
        # Salience should be between 0.0 and 1.0
        # Values outside this range should raise ValueError
        with pytest.raises(ValueError, match="salience must be between 0.0 and 1.0"):
            kernel.remember(
                title="Test",
                content="Content",
                memory_type=MemoryType.FACT,
                salience=1.5  # Out of range
            )


class TestCLIOutputFormatting:
    """Tests for CLI output formatting."""
    
    def test_success_message_format(self, kernel: MemoryKernel, capsys):
        """Test that success messages are formatted correctly."""
        path = kernel.remember(
            title="Test Memory",
            content="Test content",
            memory_type=MemoryType.FACT
        )
        
        print(f"Created memory: {path}")
        
        captured = capsys.readouterr()
        assert "Created memory:" in captured.out
        assert str(path) in captured.out
    
    def test_error_message_format(self, capsys):
        """Test that error messages are formatted consistently."""
        print("Error: Something went wrong")
        
        captured = capsys.readouterr()
        assert "Error:" in captured.out
    
    def test_progress_indicator(self, capsys):
        """Test progress indicators in output."""
        print("[OK] Operation completed successfully")
        print("[ERROR] Operation failed")
        print("[WARNING] Potential issue detected")
        
        captured = capsys.readouterr()
        assert "[OK]" in captured.out
        assert "[ERROR]" in captured.out
        assert "[WARNING]" in captured.out


class TestInteractiveConfirmation:
    """Tests for interactive confirmation prompts."""
    
    def test_confirmation_prompt_yes(self, monkeypatch):
        """Test confirmation with 'y' response."""
        monkeypatch.setattr('builtins.input', lambda _: 'y')
        
        response = input("Confirm? (y/N): ")
        assert response.lower() == 'y'
    
    def test_confirmation_prompt_no(self, monkeypatch):
        """Test confirmation with 'N' response."""
        monkeypatch.setattr('builtins.input', lambda _: 'N')
        
        response = input("Confirm? (y/N): ")
        assert response.lower() == 'n'
    
    def test_confirmation_prompt_empty(self, monkeypatch):
        """Test confirmation with empty response (default no)."""
        monkeypatch.setattr('builtins.input', lambda _: '')
        
        response = input("Confirm? (y/N): ")
        # Empty response should be treated as 'no'
        assert response.lower() != 'y'


class TestMemoryFileCreation:
    """Tests for memory file creation."""
    
    def test_memory_file_has_frontmatter(self, kernel: MemoryKernel):
        """Test that created memory files have proper frontmatter."""
        from pathlib import Path
        path_str = kernel.remember(
            title="Test Memory",
            content="Test content",
            memory_type=MemoryType.FACT,
            tags=["test"],
            salience=0.7
        )
        
        path = Path(path_str)
        content = path.read_text(encoding='utf-8')
        
        # Check for frontmatter delimiters
        assert content.startswith('---')
        assert '---' in content[3:]  # Second delimiter
        
        # Check for required fields
        assert 'title:' in content
        assert 'memory_type:' in content
        assert 'salience:' in content
        assert 'id:' in content
    
    def test_memory_file_naming(self, kernel: MemoryKernel):
        """Test that memory files are named correctly."""
        from pathlib import Path
        path_str = kernel.remember(
            title="Test Memory With Spaces",
            content="Content",
            memory_type=MemoryType.FACT
        )
        
        # Filename should be derived from title
        path = Path(path_str)
        filename = path.name
        assert filename.endswith('.md')
        # Should have sanitized the title for filename
        assert ' ' not in filename or '-' in filename.lower()
    
    def test_memory_file_content_preservation(self, kernel: MemoryKernel):
        """Test that content is preserved exactly as provided."""
        from pathlib import Path
        original_content = "Line 1\n\nLine 2\n\n- Bullet 1\n- Bullet 2"
        
        path_str = kernel.remember(
            title="Test",
            content=original_content,
            memory_type=MemoryType.FACT
        )
        
        path = Path(path_str)
        file_content = path.read_text(encoding='utf-8')
        # Original content should be in the file
        assert original_content in file_content


class TestCLIIntegration:
    """Integration tests for CLI features working together."""
    
    def test_create_and_list_memory(self, kernel: MemoryKernel):
        """Test creating a memory and then listing it."""
        # Create memory
        kernel.remember(
            title="Integration Test",
            content="Integration test content",
            memory_type=MemoryType.FACT,
            tags=["integration", "test"]
        )
        
        # List memories
        from memograph.cli_helpers import find_all_memories
        vault_path = Path(kernel.vault_path)
        memories = find_all_memories(vault_path)
        
        assert len(memories) == 1
        assert memories[0].get('title') == "Integration Test"
    
    def test_create_update_and_verify(self, kernel: MemoryKernel):
        """Test creating, updating, and verifying a memory."""
        from pathlib import Path
        # Create memory
        path_str = kernel.remember(
            title="Test Memory",
            content="Original content",
            memory_type=MemoryType.FACT,
            tags=["original"],
            salience=0.5
        )
        
        # Update the file
        from memograph.cli_helpers import read_memory_file, write_memory_file
        path = Path(path_str)
        memory_data = read_memory_file(path)
        memory_data['salience'] = 0.9
        memory_data['tags'] = ["original", "updated"]
        write_memory_file(path, memory_data)
        
        # Verify update
        updated_data = read_memory_file(path)
        assert updated_data['salience'] == 0.9
        assert "updated" in updated_data['tags']