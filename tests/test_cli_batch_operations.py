"""Tests for CLI batch operations (batch-create, batch-update, batch-delete)."""

import json
import tempfile
from pathlib import Path

import pytest

from memograph import MemoryKernel, MemoryType
from memograph.cli_batch_helpers import (
    run_batch_create_command,
    run_batch_update_command,
    run_batch_delete_command,
    _load_memories_from_json,
    _load_memories_from_csv,
)


class Args:
    """Mock args object for testing."""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


@pytest.fixture
def batch_json_file(temp_vault: Path) -> Path:
    """Create a test JSON file with batch memories."""
    json_data = {
        "memories": [
            {
                "title": "Batch Memory 1",
                "content": "Content for batch memory 1",
                "memory_type": "fact",
                "tags": ["batch", "test"],
                "salience": 0.6
            },
            {
                "title": "Batch Memory 2",
                "content": "Content for batch memory 2",
                "memory_type": "semantic",
                "tags": ["batch", "important"],
                "salience": 0.8
            },
            {
                "title": "Batch Memory 3",
                "content": "Content for batch memory 3",
                "memory_type": "episodic",
                "tags": ["batch"],
                "salience": 0.5
            }
        ]
    }
    
    json_file = temp_vault / "batch_memories.json"
    json_file.write_text(json.dumps(json_data, indent=2), encoding='utf-8')
    return json_file


@pytest.fixture
def batch_csv_file(temp_vault: Path) -> Path:
    """Create a test CSV file with batch memories."""
    csv_content = """title,content,memory_type,tags,salience
"CSV Memory 1","Content for CSV memory 1","fact","csv;test",0.6
"CSV Memory 2","Content for CSV memory 2","semantic","csv;important",0.8
"CSV Memory 3","Content for CSV memory 3","episodic","csv",0.5"""
    
    csv_file = temp_vault / "batch_memories.csv"
    csv_file.write_text(csv_content, encoding='utf-8')
    return csv_file


class TestBatchCreate:
    """Tests for batch-create command."""
    
    def test_batch_create_from_json(self, kernel: MemoryKernel, batch_json_file: Path):
        """Test creating memories from JSON file."""
        args = Args(
            input_file=str(batch_json_file),
            format='json',
            dry_run=False,
            auto_ingest=False
        )
        
        run_batch_create_command(kernel, args)
        
        # Verify memories were created
        vault_path = Path(kernel.vault_path)
        md_files = list(vault_path.glob("*.md"))
        assert len(md_files) == 3
        
        # Check memory content
        for md_file in md_files:
            content = md_file.read_text(encoding='utf-8')
            assert "batch" in content.lower()
    
    def test_batch_create_from_csv(self, kernel: MemoryKernel, batch_csv_file: Path):
        """Test creating memories from CSV file."""
        args = Args(
            input_file=str(batch_csv_file),
            format='csv',
            dry_run=False,
            auto_ingest=False
        )
        
        run_batch_create_command(kernel, args)
        
        # Verify memories were created
        vault_path = Path(kernel.vault_path)
        md_files = list(vault_path.glob("*.md"))
        assert len(md_files) == 3
    
    def test_batch_create_auto_detect_json(self, kernel: MemoryKernel, batch_json_file: Path):
        """Test auto-detecting JSON format."""
        args = Args(
            input_file=str(batch_json_file),
            format=None,  # Auto-detect
            dry_run=False,
            auto_ingest=False
        )
        
        run_batch_create_command(kernel, args)
        
        vault_path = Path(kernel.vault_path)
        md_files = list(vault_path.glob("*.md"))
        assert len(md_files) == 3
    
    def test_batch_create_dry_run(self, kernel: MemoryKernel, batch_json_file: Path, capsys):
        """Test dry-run mode doesn't create memories."""
        args = Args(
            input_file=str(batch_json_file),
            format='json',
            dry_run=True,
            auto_ingest=False
        )
        
        run_batch_create_command(kernel, args)
        
        # Verify no memories were created
        vault_path = Path(kernel.vault_path)
        md_files = list(vault_path.glob("*.md"))
        assert len(md_files) == 0
        
        # Verify dry-run message was printed
        captured = capsys.readouterr()
        assert "DRY RUN" in captured.out
    
    def test_batch_create_with_auto_ingest(self, kernel: MemoryKernel, batch_json_file: Path):
        """Test batch create with auto-ingest."""
        args = Args(
            input_file=str(batch_json_file),
            format='json',
            dry_run=False,
            auto_ingest=True
        )
        
        run_batch_create_command(kernel, args)
        
        # Verify memories were created and ingested
        vault_path = Path(kernel.vault_path)
        md_files = list(vault_path.glob("*.md"))
        assert len(md_files) == 3
    
    def test_batch_create_file_not_found(self, kernel: MemoryKernel, capsys):
        """Test error handling when file doesn't exist."""
        args = Args(
            input_file="nonexistent.json",
            format='json',
            dry_run=False,
            auto_ingest=False
        )
        
        run_batch_create_command(kernel, args)
        
        captured = capsys.readouterr()
        assert "not found" in captured.out.lower()


class TestBatchUpdate:
    """Tests for batch-update command."""
    
    def test_batch_update_by_filter(self, populated_kernel: MemoryKernel):
        """Test updating memories by filter."""
        args = Args(
            input_file=None,
            filter_tags=["python"],
            filter_type=None,
            set_salience=0.9,
            add_tags=["updated"],
            dry_run=False,
            confirm=True
        )
        
        run_batch_update_command(populated_kernel, args)
        
        # Verify update was applied
        vault_path = Path(populated_kernel.vault_path)
        from memograph.cli_helpers import find_memories_by_filter
        
        updated = find_memories_by_filter(vault_path, tags=["updated"])
        assert len(updated) > 0
        assert all(m.get('salience') == 0.9 for m in updated)
    
    def test_batch_update_dry_run(self, populated_kernel: MemoryKernel, capsys):
        """Test batch update dry-run mode."""
        args = Args(
            input_file=None,
            filter_tags=["python"],
            filter_type=None,
            set_salience=0.9,
            add_tags=["updated"],
            dry_run=True,
            confirm=True
        )
        
        run_batch_update_command(populated_kernel, args)
        
        # Verify no updates were applied
        vault_path = Path(populated_kernel.vault_path)
        from memograph.cli_helpers import find_memories_by_filter
        
        updated = find_memories_by_filter(vault_path, tags=["updated"])
        assert len(updated) == 0
        
        captured = capsys.readouterr()
        assert "DRY RUN" in captured.out
    
    def test_batch_update_no_matches(self, populated_kernel: MemoryKernel, capsys):
        """Test batch update with no matching memories."""
        args = Args(
            input_file=None,
            filter_tags=["nonexistent"],
            filter_type=None,
            set_salience=0.9,
            add_tags=None,
            dry_run=False,
            confirm=True
        )
        
        run_batch_update_command(populated_kernel, args)
        
        captured = capsys.readouterr()
        assert "no memories match" in captured.out.lower()


class TestBatchDelete:
    """Tests for batch-delete command."""
    
    def test_batch_delete_by_filter(self, populated_kernel: MemoryKernel):
        """Test deleting memories by filter."""
        vault_path = Path(populated_kernel.vault_path)
        initial_count = len(list(vault_path.glob("*.md")))
        
        args = Args(
            input_file=None,
            filter_tags=["python"],
            filter_type=None,
            older_than=None,
            dry_run=False,
            confirm=True
        )
        
        run_batch_delete_command(populated_kernel, args)
        
        # Verify memories were deleted
        final_count = len(list(vault_path.glob("*.md")))
        assert final_count < initial_count
    
    def test_batch_delete_dry_run(self, populated_kernel: MemoryKernel, capsys):
        """Test batch delete dry-run mode."""
        vault_path = Path(populated_kernel.vault_path)
        initial_count = len(list(vault_path.glob("*.md")))
        
        args = Args(
            input_file=None,
            filter_tags=["python"],
            filter_type=None,
            older_than=None,
            dry_run=True,
            confirm=True
        )
        
        run_batch_delete_command(populated_kernel, args)
        
        # Verify no files were deleted
        final_count = len(list(vault_path.glob("*.md")))
        assert final_count == initial_count
        
        captured = capsys.readouterr()
        assert "DRY RUN" in captured.out
    
    def test_batch_delete_from_file(self, populated_kernel: MemoryKernel, temp_vault: Path):
        """Test deleting memories from file with IDs."""
        from memograph.cli_helpers import find_all_memories
        
        vault_path = Path(populated_kernel.vault_path)
        memories = find_all_memories(vault_path)
        
        # Create file with memory IDs
        id_file = temp_vault / "delete_ids.txt"
        memory_ids = [m.get('id', '') for m in memories[:1]]
        id_file.write_text('\n'.join(memory_ids), encoding='utf-8')
        
        initial_count = len(list(vault_path.glob("*.md")))
        
        args = Args(
            input_file=str(id_file),
            filter_tags=None,
            filter_type=None,
            older_than=None,
            dry_run=False,
            confirm=True
        )
        
        run_batch_delete_command(populated_kernel, args)
        
        final_count = len(list(vault_path.glob("*.md")))
        assert final_count == initial_count - 1
    
    def test_batch_delete_no_matches(self, populated_kernel: MemoryKernel, capsys):
        """Test batch delete with no matching memories."""
        args = Args(
            input_file=None,
            filter_tags=["nonexistent"],
            filter_type=None,
            older_than=None,
            dry_run=False,
            confirm=True
        )
        
        run_batch_delete_command(populated_kernel, args)
        
        captured = capsys.readouterr()
        assert "no memories match" in captured.out.lower()


class TestLoadMemories:
    """Tests for memory loading utilities."""
    
    def test_load_memories_from_json_list(self, temp_vault: Path):
        """Test loading memories from JSON list format."""
        json_data = [
            {"title": "Memory 1", "content": "Content 1"},
            {"title": "Memory 2", "content": "Content 2"}
        ]
        
        json_file = temp_vault / "test.json"
        json_file.write_text(json.dumps(json_data), encoding='utf-8')
        
        memories = _load_memories_from_json(json_file)
        assert len(memories) == 2
        assert memories[0]['title'] == "Memory 1"
    
    def test_load_memories_from_json_dict(self, temp_vault: Path):
        """Test loading memories from JSON dict format."""
        json_data = {
            "memories": [
                {"title": "Memory 1", "content": "Content 1"},
                {"title": "Memory 2", "content": "Content 2"}
            ]
        }
        
        json_file = temp_vault / "test.json"
        json_file.write_text(json.dumps(json_data), encoding='utf-8')
        
        memories = _load_memories_from_json(json_file)
        assert len(memories) == 2
    
    def test_load_memories_from_csv(self, batch_csv_file: Path):
        """Test loading memories from CSV file."""
        memories = _load_memories_from_csv(batch_csv_file)
        
        assert len(memories) == 3
        assert isinstance(memories[0]['tags'], list)
        assert 'csv' in memories[0]['tags']
        assert isinstance(memories[0]['salience'], float)
    
    def test_load_memories_from_csv_tag_parsing(self, temp_vault: Path):
        """Test CSV tag parsing with semicolons."""
        csv_content = """title,content,memory_type,tags,salience
"Test","Content","fact","tag1;tag2;tag3",0.5"""
        
        csv_file = temp_vault / "test.csv"
        csv_file.write_text(csv_content, encoding='utf-8')
        
        memories = _load_memories_from_csv(csv_file)
        assert len(memories[0]['tags']) == 3
        assert 'tag1' in memories[0]['tags']
        assert 'tag2' in memories[0]['tags']
        assert 'tag3' in memories[0]['tags']


class TestProgressBars:
    """Tests for progress bar functionality."""
    
    def test_batch_create_with_tqdm(self, kernel: MemoryKernel, batch_json_file: Path):
        """Test that tqdm progress bar is used when available."""
        pytest.importorskip("tqdm")
        
        args = Args(
            input_file=str(batch_json_file),
            format='json',
            dry_run=False,
            auto_ingest=False
        )
        
        # Should complete without errors
        run_batch_create_command(kernel, args)
        
        vault_path = Path(kernel.vault_path)
        md_files = list(vault_path.glob("*.md"))
        assert len(md_files) == 3
    
    def test_batch_operations_without_tqdm(self, kernel: MemoryKernel, batch_json_file: Path, monkeypatch):
        """Test batch operations work without tqdm installed."""
        # Mock tqdm import failure
        import sys
        import builtins
        
        real_import = builtins.__import__
        
        def mock_import(name, *args, **kwargs):
            if name == 'tqdm':
                raise ImportError("tqdm not available")
            return real_import(name, *args, **kwargs)
        
        monkeypatch.setattr(builtins, '__import__', mock_import)
        
        args = Args(
            input_file=str(batch_json_file),
            format='json',
            dry_run=False,
            auto_ingest=False
        )
        
        # Should still work without tqdm
        run_batch_create_command(kernel, args)
        
        vault_path = Path(kernel.vault_path)
        md_files = list(vault_path.glob("*.md"))
        assert len(md_files) == 3