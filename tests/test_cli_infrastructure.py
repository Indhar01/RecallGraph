"""Tests for CLI infrastructure commands (export, backup, config, stats)."""

import gzip
import json
import shutil
import zipfile
from pathlib import Path

import pytest
import yaml

from memograph import MemoryKernel, MemoryType
from memograph.cli_infrastructure_helpers import (
    run_export_command,
    run_import_backup_command,
    run_backup_command,
    run_config_command,
    run_stats_command,
    _export_json,
    _export_csv,
    _export_markdown,
    _export_zip,
    _import_from_json,
    _import_from_zip,
)


class Args:
    """Mock args object for testing."""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


@pytest.fixture
def config_dir(tmp_path: Path) -> Path:
    """Create temporary config directory."""
    config_dir = tmp_path / ".memograph"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


class TestExport:
    """Tests for export command."""
    
    def test_export_json(self, populated_kernel: MemoryKernel, tmp_path: Path):
        """Test exporting vault to JSON format."""
        output_file = tmp_path / "export.json"
        
        args = Args(
            output=str(output_file),
            format='json',
            filter_tags=None,
            compress=False
        )
        
        run_export_command(populated_kernel, args)
        
        assert output_file.exists()
        
        # Verify JSON content
        data = json.loads(output_file.read_text(encoding='utf-8'))
        assert 'memories' in data
        assert len(data['memories']) > 0
        assert 'export_date' in data
        assert 'version' in data
    
    def test_export_json_compressed(self, populated_kernel: MemoryKernel, tmp_path: Path):
        """Test exporting vault to compressed JSON."""
        output_file = tmp_path / "export.json"
        
        args = Args(
            output=str(output_file),
            format='json',
            filter_tags=None,
            compress=True
        )
        
        run_export_command(populated_kernel, args)
        
        # Should create .json.gz file
        compressed_file = output_file.with_suffix('.json.gz')
        assert compressed_file.exists()
        
        # Verify can decompress and read
        with gzip.open(compressed_file, 'rt', encoding='utf-8') as f:
            data = json.load(f)
        assert 'memories' in data
    
    def test_export_csv(self, populated_kernel: MemoryKernel, tmp_path: Path):
        """Test exporting vault to CSV format."""
        output_file = tmp_path / "export.csv"
        
        args = Args(
            output=str(output_file),
            format='csv',
            filter_tags=None,
            compress=False
        )
        
        run_export_command(populated_kernel, args)
        
        assert output_file.exists()
        
        # Verify CSV content
        content = output_file.read_text(encoding='utf-8')
        assert 'id,title,memory_type,salience,tags' in content
        lines = content.strip().split('\n')
        assert len(lines) > 1  # Header + data
    
    def test_export_zip(self, populated_kernel: MemoryKernel, tmp_path: Path):
        """Test exporting vault to ZIP archive."""
        output_file = tmp_path / "export.zip"
        
        args = Args(
            output=str(output_file),
            format='zip',
            filter_tags=None,
            compress=False
        )
        
        run_export_command(populated_kernel, args)
        
        assert output_file.exists()
        
        # Verify ZIP content
        with zipfile.ZipFile(output_file, 'r') as zipf:
            namelist = zipf.namelist()
            assert len(namelist) > 0
            # Should contain .md files
            md_files = [n for n in namelist if n.endswith('.md')]
            assert len(md_files) > 0
    
    def test_export_markdown(self, populated_kernel: MemoryKernel, tmp_path: Path):
        """Test exporting vault to markdown directory."""
        output_dir = tmp_path / "export_md"
        
        args = Args(
            output=str(output_dir),
            format='markdown',
            filter_tags=None,
            compress=False
        )
        
        run_export_command(populated_kernel, args)
        
        assert output_dir.exists()
        assert output_dir.is_dir()
        
        # Verify markdown files were copied
        md_files = list(output_dir.rglob("*.md"))
        assert len(md_files) > 0
    
    def test_export_with_tag_filter(self, populated_kernel: MemoryKernel, tmp_path: Path):
        """Test exporting with tag filter."""
        output_file = tmp_path / "export.json"
        
        args = Args(
            output=str(output_file),
            format='json',
            filter_tags=["python"],
            compress=False
        )
        
        run_export_command(populated_kernel, args)
        
        assert output_file.exists()
        
        data = json.loads(output_file.read_text(encoding='utf-8'))
        # Should only export memories with 'python' tag
        for memory in data['memories']:
            assert 'python' in memory.get('tags', [])
    
    def test_export_empty_vault(self, kernel: MemoryKernel, tmp_path: Path, capsys):
        """Test exporting empty vault."""
        output_file = tmp_path / "export.json"
        
        args = Args(
            output=str(output_file),
            format='json',
            filter_tags=None,
            compress=False
        )
        
        run_export_command(kernel, args)
        
        captured = capsys.readouterr()
        assert "no memories" in captured.out.lower()


class TestImportBackup:
    """Tests for import-backup command."""
    
    def test_import_from_json_backup(self, kernel: MemoryKernel, tmp_path: Path):
        """Test importing from JSON backup."""
        # Create backup file
        backup_data = {
            "memories": [
                {
                    "id": "test-1",
                    "title": "Import Test 1",
                    "content": "Content 1",
                    "memory_type": "fact",
                    "tags": ["imported"],
                    "salience": 0.6
                },
                {
                    "id": "test-2",
                    "title": "Import Test 2",
                    "content": "Content 2",
                    "memory_type": "semantic",
                    "tags": ["imported"],
                    "salience": 0.7
                }
            ]
        }
        
        backup_file = tmp_path / "backup.json"
        backup_file.write_text(json.dumps(backup_data), encoding='utf-8')
        
        args = Args(
            backup_file=str(backup_file),
            merge=True,
            skip_duplicates=False
        )
        
        run_import_backup_command(kernel, args)
        
        # Verify memories were imported
        vault_path = Path(kernel.vault_path)
        md_files = list(vault_path.glob("*.md"))
        assert len(md_files) == 2
    
    def test_import_from_compressed_json(self, kernel: MemoryKernel, tmp_path: Path):
        """Test importing from compressed JSON backup."""
        backup_data = {
            "memories": [
                {
                    "title": "Compressed Import",
                    "content": "Content",
                    "memory_type": "fact",
                    "tags": ["compressed"],
                    "salience": 0.5
                }
            ]
        }
        
        backup_file = tmp_path / "backup.json.gz"
        with gzip.open(backup_file, 'wt', encoding='utf-8') as f:
            json.dump(backup_data, f)
        
        args = Args(
            backup_file=str(backup_file),
            merge=True,
            skip_duplicates=False
        )
        
        run_import_backup_command(kernel, args)
        
        vault_path = Path(kernel.vault_path)
        md_files = list(vault_path.glob("*.md"))
        assert len(md_files) == 1
    
    def test_import_merge_mode(self, populated_kernel: MemoryKernel, tmp_path: Path):
        """Test importing in merge mode (keeps existing)."""
        vault_path = Path(populated_kernel.vault_path)
        initial_count = len(list(vault_path.glob("*.md")))
        
        backup_data = {
            "memories": [
                {
                    "title": "New Memory",
                    "content": "New content",
                    "memory_type": "fact",
                    "tags": ["new"],
                    "salience": 0.5
                }
            ]
        }
        
        backup_file = tmp_path / "backup.json"
        backup_file.write_text(json.dumps(backup_data), encoding='utf-8')
        
        args = Args(
            backup_file=str(backup_file),
            merge=True,
            skip_duplicates=False
        )
        
        run_import_backup_command(populated_kernel, args)
        
        final_count = len(list(vault_path.glob("*.md")))
        assert final_count == initial_count + 1
    
    def test_import_skip_duplicates(self, kernel: MemoryKernel, tmp_path: Path):
        """Test skipping duplicate memories during import."""
        # Create a memory first
        kernel.remember(
            title="Existing Memory",
            content="Existing content",
            memory_type=MemoryType.FACT,
            tags=["existing"]
        )
        
        from memograph.cli_helpers import find_all_memories
        vault_path = Path(kernel.vault_path)
        existing = find_all_memories(vault_path)
        existing_id = existing[0].get('id')
        
        # Try to import memory with same ID
        backup_data = {
            "memories": [
                {
                    "id": existing_id,
                    "title": "Duplicate Memory",
                    "content": "Duplicate content",
                    "memory_type": "fact",
                    "tags": ["duplicate"],
                    "salience": 0.5
                }
            ]
        }
        
        backup_file = tmp_path / "backup.json"
        backup_file.write_text(json.dumps(backup_data), encoding='utf-8')
        
        args = Args(
            backup_file=str(backup_file),
            merge=True,
            skip_duplicates=True
        )
        
        run_import_backup_command(kernel, args)
        
        # Should still have only 1 memory
        final_count = len(list(vault_path.glob("*.md")))
        assert final_count == 1


class TestBackup:
    """Tests for backup command."""
    
    def test_backup_compressed(self, populated_kernel: MemoryKernel, tmp_path: Path):
        """Test creating compressed backup."""
        dest_dir = tmp_path / "backups"
        
        args = Args(
            destination=str(dest_dir),
            compress=True,
            keep=10
        )
        
        run_backup_command(populated_kernel, args)
        
        assert dest_dir.exists()
        
        # Should create a .zip file
        zip_files = list(dest_dir.glob("*.zip"))
        assert len(zip_files) == 1
        
        # Verify ZIP contents
        with zipfile.ZipFile(zip_files[0], 'r') as zipf:
            assert len(zipf.namelist()) > 0
    
    def test_backup_uncompressed(self, populated_kernel: MemoryKernel, tmp_path: Path):
        """Test creating uncompressed backup (directory copy)."""
        dest_dir = tmp_path / "backups"
        
        args = Args(
            destination=str(dest_dir),
            compress=False,
            keep=10
        )
        
        run_backup_command(populated_kernel, args)
        
        assert dest_dir.exists()
        
        # Should create a directory backup
        backup_dirs = [d for d in dest_dir.iterdir() if d.is_dir()]
        assert len(backup_dirs) == 1
        
        # Verify contents
        md_files = list(backup_dirs[0].rglob("*.md"))
        assert len(md_files) > 0
    
    def test_backup_cleanup_old(self, populated_kernel: MemoryKernel, tmp_path: Path):
        """Test cleanup of old backups."""
        dest_dir = tmp_path / "backups"
        dest_dir.mkdir(parents=True)
        
        # Create multiple fake old backups
        vault_name = Path(populated_kernel.vault_path).name
        for i in range(15):
            old_backup = dest_dir / f"{vault_name}_backup_2024010{i:02d}_120000.zip"
            old_backup.write_text("fake backup")
        
        args = Args(
            destination=str(dest_dir),
            compress=True,
            keep=5
        )
        
        run_backup_command(populated_kernel, args)
        
        # Should keep only 5 most recent + the new one
        zip_files = list(dest_dir.glob("*.zip"))
        assert len(zip_files) <= 6  # keep=5 plus the new one


class TestConfig:
    """Tests for config command."""
    
    def test_config_set(self, kernel: MemoryKernel, tmp_path: Path, monkeypatch):
        """Test setting configuration value."""
        config_file = tmp_path / ".memograph" / "config.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        
        args = Args(
            config_command='set',
            key='default_provider',
            value='claude',
            action=None,
            name=None
        )
        
        run_config_command(kernel, args)
        
        # Verify config was saved
        assert config_file.exists()
        config = yaml.safe_load(config_file.read_text())
        assert config['default_provider'] == 'claude'
    
    def test_config_get(self, kernel: MemoryKernel, tmp_path: Path, monkeypatch, capsys):
        """Test getting configuration value."""
        config_file = tmp_path / ".memograph" / "config.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create config with a value
        config = {'default_provider': 'ollama'}
        config_file.write_text(yaml.dump(config), encoding='utf-8')
        
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        
        args = Args(
            config_command='get',
            key='default_provider',
            value=None,
            action=None,
            name=None
        )
        
        run_config_command(kernel, args)
        
        captured = capsys.readouterr()
        assert 'ollama' in captured.out
    
    def test_config_list(self, kernel: MemoryKernel, tmp_path: Path, monkeypatch, capsys):
        """Test listing all configuration."""
        config_file = tmp_path / ".memograph" / "config.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        config = {
            'default_provider': 'ollama',
            'default_vault': '/path/to/vault'
        }
        config_file.write_text(yaml.dump(config), encoding='utf-8')
        
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        
        args = Args(
            config_command='list',
            key=None,
            value=None,
            action=None,
            name=None
        )
        
        run_config_command(kernel, args)
        
        captured = capsys.readouterr()
        assert 'default_provider' in captured.out
        assert 'ollama' in captured.out
    
    def test_config_profile_create(self, kernel: MemoryKernel, tmp_path: Path, monkeypatch):
        """Test creating a configuration profile."""
        config_file = tmp_path / ".memograph" / "config.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        
        args = Args(
            config_command='profile',
            key=None,
            value=None,
            action='create',
            name='test_profile'
        )
        
        run_config_command(kernel, args)
        
        # Verify profile was created
        config = yaml.safe_load(config_file.read_text())
        assert 'profiles' in config
        assert 'test_profile' in config['profiles']
    
    def test_config_profile_use(self, kernel: MemoryKernel, tmp_path: Path, monkeypatch):
        """Test switching to a profile."""
        config_file = tmp_path / ".memograph" / "config.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        config = {
            'profiles': {
                'test_profile': {
                    'vault': '/test/vault',
                    'provider': 'claude'
                }
            }
        }
        config_file.write_text(yaml.dump(config), encoding='utf-8')
        
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        
        args = Args(
            config_command='profile',
            key=None,
            value=None,
            action='use',
            name='test_profile'
        )
        
        run_config_command(kernel, args)
        
        # Verify active profile was set
        config = yaml.safe_load(config_file.read_text())
        assert config['active_profile'] == 'test_profile'


class TestStats:
    """Tests for stats command."""
    
    def test_stats_text_format(self, populated_kernel: MemoryKernel, capsys):
        """Test statistics in text format."""
        args = Args(
            detailed=False,
            format='text'
        )
        
        run_stats_command(populated_kernel, args)
        
        captured = capsys.readouterr()
        assert 'Total Memories' in captured.out
        assert 'Total Tags' in captured.out
        assert 'Average Salience' in captured.out
    
    def test_stats_json_format(self, populated_kernel: MemoryKernel, capsys):
        """Test statistics in JSON format."""
        args = Args(
            detailed=False,
            format='json'
        )
        
        run_stats_command(populated_kernel, args)
        
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        
        assert 'total_memories' in data
        assert 'by_type' in data
        assert 'by_tag' in data
        assert 'salience_avg' in data
        assert 'salience_distribution' in data
    
    def test_stats_detailed(self, populated_kernel: MemoryKernel, capsys):
        """Test detailed statistics output."""
        args = Args(
            detailed=True,
            format='text'
        )
        
        run_stats_command(populated_kernel, args)
        
        captured = capsys.readouterr()
        assert 'Top Tags' in captured.out
    
    def test_stats_empty_vault(self, kernel: MemoryKernel, capsys):
        """Test statistics on empty vault."""
        args = Args(
            detailed=False,
            format='text'
        )
        
        run_stats_command(kernel, args)
        
        captured = capsys.readouterr()
        assert 'no memories' in captured.out.lower()