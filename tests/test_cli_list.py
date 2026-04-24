"""Tests for CLI list command.

Tests filtering, sorting, pagination, and output formats.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from memograph.cli import main
from memograph.core.enums import MemoryType


@pytest.fixture
def test_vault_with_memories(tmp_path):
    """Create test vault with diverse memories."""
    vault = tmp_path / "vault"
    vault.mkdir()
    
    # Create test memories with varied attributes
    memories = [
        {
            "id": "mem-001",
            "title": "Python Basics",
            "content": "Introduction to Python programming",
            "memory_type": "semantic",
            "salience": 0.9,
            "tags": ["python", "programming", "basics"],
            "created_at": "2024-01-01T10:00:00Z"
        },
        {
            "id": "mem-002",
            "title": "Docker Tutorial",
            "content": "Container basics and best practices",
            "memory_type": "procedural",
            "salience": 0.7,
            "tags": ["docker", "devops", "containers"],
            "created_at": "2024-01-02T10:00:00Z"
        },
        {
            "id": "mem-003",
            "title": "Team Meeting Notes",
            "content": "Discussed Q1 goals and objectives",
            "memory_type": "episodic",
            "salience": 0.5,
            "tags": ["meeting", "planning", "team"],
            "created_at": "2024-01-03T10:00:00Z"
        },
        {
            "id": "mem-004",
            "title": "API Design Patterns",
            "content": "REST and GraphQL comparison",
            "memory_type": "semantic",
            "salience": 0.8,
            "tags": ["api", "design", "architecture"],
            "created_at": "2024-01-04T10:00:00Z"
        },
        {
            "id": "mem-005",
            "title": "Quick Note",
            "content": "Remember to update docs",
            "memory_type": "fact",
            "salience": 0.3,
            "tags": ["todo", "documentation"],
            "created_at": "2024-01-05T10:00:00Z"
        },
        {
            "id": "mem-006",
            "title": "Machine Learning Intro",
            "content": "Basic ML concepts and algorithms",
            "memory_type": "semantic",
            "salience": 0.85,
            "tags": ["ml", "ai", "python"],
            "created_at": "2024-01-06T10:00:00Z"
        },
        {
            "id": "mem-007",
            "title": "Database Optimization",
            "content": "Query optimization techniques",
            "memory_type": "procedural",
            "salience": 0.75,
            "tags": ["database", "performance", "sql"],
            "created_at": "2024-01-07T10:00:00Z"
        },
        {
            "id": "mem-008",
            "title": "Conference Notes",
            "content": "Key takeaways from tech conference",
            "memory_type": "episodic",
            "salience": 0.6,
            "tags": ["conference", "learning", "networking"],
            "created_at": "2024-01-08T10:00:00Z"
        }
    ]
    
    for mem in memories:
        file_path = vault / f"{mem['id']}.md"
        content = f"""---
id: {mem['id']}
title: {mem['title']}
memory_type: {mem['memory_type']}
salience: {mem['salience']}
tags: {mem['tags']}
created_at: {mem['created_at']}
---

{mem['content']}
"""
        file_path.write_text(content, encoding="utf-8")
    
    return vault


class TestListBasic:
    """Test basic list functionality."""
    
    def test_list_all_memories(self, test_vault_with_memories, capsys):
        """Test listing all memories."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_memories),
            "list"
        ]):
            main()
        
        output = capsys.readouterr().out
        # Should show all 8 memories
        assert "mem-001" in output
        assert "mem-008" in output
        assert "Python Basics" in output
    
    def test_list_shows_table_format(self, test_vault_with_memories, capsys):
        """Test default table format."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_memories),
            "list"
        ]):
            main()
        
        output = capsys.readouterr().out
        # Should have table headers
        assert "ID" in output
        assert "Title" in output
        assert "Type" in output
        assert "Salience" in output
        assert "Tags" in output
    
    def test_list_empty_vault(self, tmp_path, capsys):
        """Test listing empty vault."""
        vault = tmp_path / "empty_vault"
        vault.mkdir()
        
        with patch("sys.argv", [
            "memograph",
            "--vault", str(vault),
            "list"
        ]):
            main()
        
        output = capsys.readouterr().out
        assert "No memories found" in output


class TestListFiltering:
    """Test filtering functionality."""
    
    def test_filter_by_single_tag(self, test_vault_with_memories, capsys):
        """Test filtering by single tag."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_memories),
            "list", "--tags", "python"
        ]):
            main()
        
        output = capsys.readouterr().out
        assert "mem-001" in output  # Python Basics
        assert "mem-006" in output  # Machine Learning Intro
        assert "mem-002" not in output  # Docker Tutorial
    
    def test_filter_by_multiple_tags(self, test_vault_with_memories, capsys):
        """Test filtering by multiple tags (any match)."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_memories),
            "list", "--tags", "python", "docker"
        ]):
            main()
        
        output = capsys.readouterr().out
        assert "mem-001" in output  # Has python tag
        assert "mem-002" in output  # Has docker tag
        assert "mem-006" in output  # Has python tag
    
    def test_filter_by_type(self, test_vault_with_memories, capsys):
        """Test filtering by memory type."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_memories),
            "list", "--type", "semantic"
        ]):
            main()
        
        output = capsys.readouterr().out
        assert "mem-001" in output  # semantic
        assert "mem-004" in output  # semantic
        assert "mem-006" in output  # semantic
        assert "mem-002" not in output  # procedural
        assert "mem-003" not in output  # episodic
    
    def test_filter_by_min_salience(self, test_vault_with_memories, capsys):
        """Test filtering by minimum salience."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_memories),
            "list", "--min-salience", "0.8"
        ]):
            main()
        
        output = capsys.readouterr().out
        assert "mem-001" in output  # 0.9
        assert "mem-004" in output  # 0.8
        assert "mem-006" in output  # 0.85
        assert "mem-002" not in output  # 0.7
        assert "mem-005" not in output  # 0.3
    
    def test_filter_by_max_salience(self, test_vault_with_memories, capsys):
        """Test filtering by maximum salience."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_memories),
            "list", "--max-salience", "0.5"
        ]):
            main()
        
        output = capsys.readouterr().out
        assert "mem-003" in output  # 0.5
        assert "mem-005" in output  # 0.3
        assert "mem-001" not in output  # 0.9
    
    def test_filter_by_salience_range(self, test_vault_with_memories, capsys):
        """Test filtering by salience range."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_memories),
            "list",
            "--min-salience", "0.7",
            "--max-salience", "0.8"
        ]):
            main()
        
        output = capsys.readouterr().out
        assert "mem-002" in output  # 0.7
        assert "mem-004" in output  # 0.8
        assert "mem-007" in output  # 0.75
        assert "mem-001" not in output  # 0.9 (too high)
        assert "mem-005" not in output  # 0.3 (too low)
    
    def test_filter_combined(self, test_vault_with_memories, capsys):
        """Test combining multiple filters."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_memories),
            "list",
            "--type", "semantic",
            "--min-salience", "0.8"
        ]):
            main()
        
        output = capsys.readouterr().out
        assert "mem-001" in output  # semantic, 0.9
        assert "mem-004" in output  # semantic, 0.8
        assert "mem-006" in output  # semantic, 0.85
        assert "mem-002" not in output  # procedural
        assert "mem-005" not in output  # fact, low salience


class TestListSorting:
    """Test sorting functionality."""
    
    def test_sort_by_title(self, test_vault_with_memories, capsys):
        """Test sorting by title."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_memories),
            "list", "--sort-by", "title", "--format", "ids"
        ]):
            main()
        
        output = capsys.readouterr().out
        lines = [line for line in output.strip().split('\n') if line]
        # Should be alphabetically sorted
        assert lines[0] == "mem-004"  # API Design Patterns
        assert lines[1] == "mem-008"  # Conference Notes
    
    def test_sort_by_salience(self, test_vault_with_memories, capsys):
        """Test sorting by salience."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_memories),
            "list", "--sort-by", "salience", "--format", "ids"
        ]):
            main()
        
        output = capsys.readouterr().out
        lines = [line for line in output.strip().split('\n') if line]
        # Should be sorted by salience (ascending)
        assert lines[0] == "mem-005"  # 0.3
        assert lines[-1] == "mem-001"  # 0.9
    
    def test_sort_by_salience_reverse(self, test_vault_with_memories, capsys):
        """Test sorting by salience in descending order."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_memories),
            "list",
            "--sort-by", "salience",
            "--reverse",
            "--format", "ids"
        ]):
            main()
        
        output = capsys.readouterr().out
        lines = [line for line in output.strip().split('\n') if line]
        # Should be sorted by salience (descending)
        assert lines[0] == "mem-001"  # 0.9
        assert lines[-1] == "mem-005"  # 0.3
    
    def test_sort_by_type(self, test_vault_with_memories, capsys):
        """Test sorting by memory type."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_memories),
            "list", "--sort-by", "type", "--format", "ids"
        ]):
            main()
        
        output = capsys.readouterr().out
        # Should group by type
        assert "mem-003" in output  # episodic
        assert "mem-008" in output  # episodic


class TestListPagination:
    """Test pagination functionality."""
    
    def test_limit_results(self, test_vault_with_memories, capsys):
        """Test limiting number of results."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_memories),
            "list", "--limit", "3", "--format", "ids"
        ]):
            main()
        
        output = capsys.readouterr().out
        lines = [line for line in output.strip().split('\n') if line]
        assert len(lines) == 3
    
    def test_offset_results(self, test_vault_with_memories, capsys):
        """Test offsetting results."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_memories),
            "list",
            "--sort-by", "salience",
            "--limit", "2",
            "--offset", "2",
            "--format", "ids"
        ]):
            main()
        
        output = capsys.readouterr().out
        lines = [line for line in output.strip().split('\n') if line]
        # Should skip first 2 and show next 2
        assert len(lines) == 2
        assert "mem-005" not in output  # First (0.3)
        assert "mem-003" not in output  # Second (0.5)
    
    def test_pagination_combined(self, test_vault_with_memories, capsys):
        """Test limit and offset together."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_memories),
            "list",
            "--sort-by", "title",
            "--limit", "3",
            "--offset", "1",
            "--format", "ids"
        ]):
            main()
        
        output = capsys.readouterr().out
        lines = [line for line in output.strip().split('\n') if line]
        assert len(lines) == 3


class TestListOutputFormats:
    """Test different output formats."""
    
    def test_table_format(self, test_vault_with_memories, capsys):
        """Test table output format."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_memories),
            "list", "--format", "table", "--limit", "2"
        ]):
            main()
        
        output = capsys.readouterr().out
        # Should have table structure
        assert "|" in output
        assert "ID" in output
        assert "Title" in output
        assert "---" in output  # Separator line
    
    def test_json_format(self, test_vault_with_memories, capsys):
        """Test JSON output format."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_memories),
            "list", "--format", "json", "--limit", "2"
        ]):
            main()
        
        output = capsys.readouterr().out
        # Should be valid JSON
        assert output.strip().startswith("[")
        assert output.strip().endswith("]")
        assert '"id"' in output
        assert '"title"' in output
        assert '"memory_type"' in output
    
    def test_csv_format(self, test_vault_with_memories, capsys):
        """Test CSV output format."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_memories),
            "list", "--format", "csv", "--limit", "2"
        ]):
            main()
        
        output = capsys.readouterr().out
        lines = output.strip().split('\n')
        # Should have CSV header
        assert "id,title,memory_type,salience,tags" in lines[0]
        # Should have quoted values
        assert '"' in output
    
    def test_ids_format(self, test_vault_with_memories, capsys):
        """Test IDs-only output format."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_memories),
            "list", "--format", "ids", "--limit", "3"
        ]):
            main()
        
        output = capsys.readouterr().out
        lines = [line for line in output.strip().split('\n') if line]
        # Should only have IDs
        assert all(line.startswith("mem-") for line in lines)
        assert len(lines) == 3


class TestListIntegration:
    """Integration tests combining multiple features."""
    
    def test_filter_sort_paginate(self, test_vault_with_memories, capsys):
        """Test combining filter, sort, and pagination."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_memories),
            "list",
            "--type", "semantic",
            "--sort-by", "salience",
            "--reverse",
            "--limit", "2",
            "--format", "ids"
        ]):
            main()
        
        output = capsys.readouterr().out
        lines = [line for line in output.strip().split('\n') if line]
        # Should show top 2 semantic memories by salience
        assert len(lines) == 2
        assert "mem-001" in lines  # 0.9
        assert "mem-006" in lines  # 0.85
    
    def test_complex_filter_json_output(self, test_vault_with_memories, capsys):
        """Test complex filtering with JSON output."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_memories),
            "list",
            "--tags", "python",
            "--min-salience", "0.8",
            "--format", "json"
        ]):
            main()
        
        output = capsys.readouterr().out
        # Should be valid JSON with filtered results
        assert '"id": "mem-001"' in output or '"id":"mem-001"' in output
        assert '"id": "mem-006"' in output or '"id":"mem-006"' in output
    
    def test_all_features_combined(self, test_vault_with_memories, capsys):
        """Test all features together."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_memories),
            "list",
            "--tags", "python", "api",
            "--min-salience", "0.7",
            "--sort-by", "salience",
            "--reverse",
            "--limit", "5",
            "--format", "table"
        ]):
            main()
        
        output = capsys.readouterr().out
        # Should execute without error and show results
        assert "ID" in output
        assert "Title" in output


class TestListErrorHandling:
    """Test error handling."""
    
    def test_invalid_sort_field(self, test_vault_with_memories):
        """Test handling of invalid sort field."""
        # This should be caught by argparse
        with pytest.raises(SystemExit):
            with patch("sys.argv", [
                "memograph",
                "--vault", str(test_vault_with_memories),
                "list", "--sort-by", "invalid"
            ]):
                main()
    
    def test_invalid_format(self, test_vault_with_memories):
        """Test handling of invalid format."""
        # This should be caught by argparse
        with pytest.raises(SystemExit):
            with patch("sys.argv", [
                "memograph",
                "--vault", str(test_vault_with_memories),
                "list", "--format", "invalid"
            ]):
                main()
    
    def test_negative_limit(self, test_vault_with_memories, capsys):
        """Test handling of negative limit."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_memories),
            "list", "--limit", "-1"
        ]):
            # Should handle gracefully (show no results or all)
            main()
        
        output = capsys.readouterr().out
        # Should not crash
        assert output is not None
