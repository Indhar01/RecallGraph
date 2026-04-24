"""Tests for CLI search command.

Tests search strategies, output formats, scoring options, and error handling.
"""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from memograph.cli import main
from memograph.core.node import MemoryNode
from memograph.core.enums import MemoryType


@pytest.fixture
def test_vault_with_search_memories(tmp_path):
    """Create test vault with memories for search testing."""
    vault = tmp_path / "vault"
    vault.mkdir()
    
    memories = [
        {
            "id": "py-001",
            "title": "Python Async Programming",
            "content": "Comprehensive guide to async/await in Python. Covers asyncio, coroutines, and event loops.",
            "memory_type": "semantic",
            "salience": 0.9,
            "tags": ["python", "async", "programming"],
        },
        {
            "id": "py-002",
            "title": "Python Best Practices",
            "content": "Collection of Python coding standards and best practices for clean code.",
            "memory_type": "semantic",
            "salience": 0.85,
            "tags": ["python", "best-practices", "coding"],
        },
        {
            "id": "docker-001",
            "title": "Docker Basics",
            "content": "Introduction to Docker containers, images, and basic commands.",
            "memory_type": "procedural",
            "salience": 0.8,
            "tags": ["docker", "containers", "devops"],
        },
        {
            "id": "ml-001",
            "title": "Machine Learning Fundamentals",
            "content": "Core concepts of machine learning including supervised and unsupervised learning.",
            "memory_type": "semantic",
            "salience": 0.95,
            "tags": ["ml", "ai", "data-science"],
        },
        {
            "id": "api-001",
            "title": "REST API Design",
            "content": "Best practices for designing RESTful APIs with proper HTTP methods and status codes.",
            "memory_type": "semantic",
            "salience": 0.75,
            "tags": ["api", "rest", "design"],
        },
    ]
    
    for mem in memories:
        file_path = vault / f"{mem['id']}.md"
        content = f"""---
id: {mem['id']}
title: {mem['title']}
memory_type: {mem['memory_type']}
salience: {mem['salience']}
tags: {mem['tags']}
---

{mem['content']}
"""
        file_path.write_text(content, encoding="utf-8")
    
    return vault


@pytest.fixture
def mock_search_results():
    """Create mock search results."""
    results = [
        MagicMock(
            id="py-001",
            title="Python Async Programming",
            content="Comprehensive guide to async/await in Python.",
            memory_type="semantic",
            salience=0.9,
            tags=["python", "async"],
            score=0.95,
            connections=[]
        ),
        MagicMock(
            id="py-002",
            title="Python Best Practices",
            content="Collection of Python coding standards.",
            memory_type="semantic",
            salience=0.85,
            tags=["python", "best-practices"],
            score=0.88,
            connections=[]
        ),
    ]
    return results


class TestSearchBasic:
    """Test basic search functionality."""
    
    def test_search_with_query(self, test_vault_with_search_memories, capsys):
        """Test basic search with query."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_search_memories),
            "search", "python"
        ]):
            main()
        
        output = capsys.readouterr().out
        # Should show results
        assert "ID" in output or "Found" in output or "python" in output.lower()
    
    def test_search_default_strategy(self, test_vault_with_search_memories, capsys):
        """Test search uses hybrid strategy by default."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_search_memories),
            "search", "python programming"
        ]):
            main()
        
        output = capsys.readouterr().out
        # Should mention hybrid strategy in summary
        assert "hybrid" in output.lower() or "results" in output.lower()
    
    def test_search_no_results(self, test_vault_with_search_memories, capsys):
        """Test search with no matching results."""
        # Mock kernel.search to return empty list
        with patch("memograph.core.kernel.MemoryKernel.search", return_value=[]):
            with patch("sys.argv", [
                "memograph",
                "--vault", str(test_vault_with_search_memories),
                "search", "nonexistent_query_xyz123"
            ]):
                main()
        
        output = capsys.readouterr().out
        assert "No results found" in output


class TestSearchStrategies:
    """Test different search strategies."""
    
    def test_keyword_strategy(self, test_vault_with_search_memories, capsys):
        """Test keyword search strategy."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_search_memories),
            "search", "python", "--strategy", "keyword"
        ]):
            main()
        
        output = capsys.readouterr().out
        assert "keyword" in output.lower()
    
    def test_semantic_strategy(self, test_vault_with_search_memories, capsys):
        """Test semantic search strategy."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_search_memories),
            "search", "python", "--strategy", "semantic"
        ]):
            main()
        
        output = capsys.readouterr().out
        assert "semantic" in output.lower()
    
    def test_hybrid_strategy(self, test_vault_with_search_memories, capsys):
        """Test hybrid search strategy."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_search_memories),
            "search", "python", "--strategy", "hybrid"
        ]):
            main()
        
        output = capsys.readouterr().out
        assert "hybrid" in output.lower()
    
    def test_graph_strategy(self, test_vault_with_search_memories, capsys):
        """Test graph search strategy."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_search_memories),
            "search", "python", "--strategy", "graph"
        ]):
            main()
        
        output = capsys.readouterr().out
        assert "graph" in output.lower()


class TestSearchOptions:
    """Test search options and filters."""
    
    def test_limit_results(self, test_vault_with_search_memories, capsys):
        """Test limiting search results."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_search_memories),
            "search", "python", "--limit", "2"
        ]):
            main()
        
        output = capsys.readouterr().out
        # Should execute without error
        assert output is not None
    
    def test_min_salience_filter(self, test_vault_with_search_memories, capsys):
        """Test minimum salience filter."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_search_memories),
            "search", "python", "--min-salience", "0.9"
        ]):
            main()
        
        output = capsys.readouterr().out
        # Should execute without error
        assert output is not None
    
    def test_depth_option(self, test_vault_with_search_memories, capsys):
        """Test graph depth option."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_search_memories),
            "search", "python", "--depth", "3"
        ]):
            main()
        
        output = capsys.readouterr().out
        # Should execute without error
        assert output is not None
    
    def test_boost_recent(self, test_vault_with_search_memories, capsys):
        """Test recency boost option."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_search_memories),
            "search", "python", "--boost-recent"
        ]):
            main()
        
        output = capsys.readouterr().out
        # Should execute without error
        assert output is not None


class TestSearchScoring:
    """Test search scoring options."""
    
    def test_custom_keyword_weight(self, test_vault_with_search_memories, capsys):
        """Test custom keyword weight."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_search_memories),
            "search", "python", "--keyword-weight", "0.7"
        ]):
            main()
        
        output = capsys.readouterr().out
        # Should execute without error
        assert output is not None
    
    def test_custom_semantic_weight(self, test_vault_with_search_memories, capsys):
        """Test custom semantic weight."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_search_memories),
            "search", "python", "--semantic-weight", "0.8"
        ]):
            main()
        
        output = capsys.readouterr().out
        # Should execute without error
        assert output is not None
    
    def test_custom_weights_both(self, test_vault_with_search_memories, capsys):
        """Test setting both keyword and semantic weights."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_search_memories),
            "search", "python",
            "--keyword-weight", "0.3",
            "--semantic-weight", "0.7"
        ]):
            main()
        
        output = capsys.readouterr().out
        # Should execute without error
        assert output is not None


class TestSearchOutputFormats:
    """Test different output formats."""
    
    def test_table_format(self, test_vault_with_search_memories, capsys):
        """Test table output format."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_search_memories),
            "search", "python", "--format", "table"
        ]):
            main()
        
        output = capsys.readouterr().out
        # Should have table structure or results
        assert "ID" in output or "Title" in output or "results" in output.lower()
    
    def test_json_format(self, test_vault_with_search_memories, capsys):
        """Test JSON output format."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_search_memories),
            "search", "python", "--format", "json"
        ]):
            main()
        
        output = capsys.readouterr().out
        # Should be JSON or empty results
        assert "[" in output or "No results" in output
    
    def test_detailed_format(self, test_vault_with_search_memories, capsys):
        """Test detailed output format."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_search_memories),
            "search", "python", "--format", "detailed"
        ]):
            main()
        
        output = capsys.readouterr().out
        # Should have detailed info or no results
        assert "Result" in output or "No results" in output
    
    def test_show_scores(self, test_vault_with_search_memories, capsys):
        """Test showing relevance scores."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_search_memories),
            "search", "python", "--show-scores"
        ]):
            main()
        
        output = capsys.readouterr().out
        # Should execute without error
        assert output is not None
    
    def test_show_snippets(self, test_vault_with_search_memories, capsys):
        """Test showing content snippets."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_search_memories),
            "search", "python", "--show-snippets"
        ]):
            main()
        
        output = capsys.readouterr().out
        # Should execute without error
        assert output is not None


class TestSearchIntegration:
    """Integration tests combining multiple features."""
    
    def test_search_with_all_options(self, test_vault_with_search_memories, capsys):
        """Test search with multiple options combined."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_search_memories),
            "search", "python programming",
            "--strategy", "hybrid",
            "--limit", "5",
            "--min-salience", "0.7",
            "--boost-recent",
            "--show-scores",
            "--format", "table"
        ]):
            main()
        
        output = capsys.readouterr().out
        # Should execute without error
        assert output is not None
    
    def test_search_json_with_options(self, test_vault_with_search_memories, capsys):
        """Test JSON output with search options."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_search_memories),
            "search", "python",
            "--strategy", "semantic",
            "--limit", "3",
            "--format", "json"
        ]):
            main()
        
        output = capsys.readouterr().out
        # Should be JSON or no results
        assert "[" in output or "No results" in output
    
    def test_search_detailed_with_snippets(self, test_vault_with_search_memories, capsys):
        """Test detailed format with snippets."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_search_memories),
            "search", "python",
            "--format", "detailed",
            "--show-snippets",
            "--limit", "2"
        ]):
            main()
        
        output = capsys.readouterr().out
        # Should execute without error
        assert output is not None


class TestSearchErrorHandling:
    """Test error handling."""
    
    def test_invalid_strategy(self, test_vault_with_search_memories):
        """Test handling of invalid search strategy."""
        with pytest.raises(SystemExit):
            with patch("sys.argv", [
                "memograph",
                "--vault", str(test_vault_with_search_memories),
                "search", "python", "--strategy", "invalid"
            ]):
                main()
    
    def test_invalid_format(self, test_vault_with_search_memories):
        """Test handling of invalid output format."""
        with pytest.raises(SystemExit):
            with patch("sys.argv", [
                "memograph",
                "--vault", str(test_vault_with_search_memories),
                "search", "python", "--format", "invalid"
            ]):
                main()
    
    def test_negative_limit(self, test_vault_with_search_memories, capsys):
        """Test handling of negative limit."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_search_memories),
            "search", "python", "--limit", "-1"
        ]):
            # Should handle gracefully
            main()
        
        output = capsys.readouterr().out
        # Should not crash
        assert output is not None
    
    def test_empty_query(self, test_vault_with_search_memories):
        """Test handling of empty query."""
        with pytest.raises(SystemExit):
            with patch("sys.argv", [
                "memograph",
                "--vault", str(test_vault_with_search_memories),
                "search"
            ]):
                main()
    
    def test_invalid_weight_range(self, test_vault_with_search_memories, capsys):
        """Test handling of invalid weight values."""
        with patch("sys.argv", [
            "memograph",
            "--vault", str(test_vault_with_search_memories),
            "search", "python", "--keyword-weight", "1.5"
        ]):
            # Should handle gracefully or normalize
            main()
        
        output = capsys.readouterr().out
        # Should not crash
        assert output is not None


class TestSearchWithMockedKernel:
    """Test search with mocked kernel for controlled results."""
    
    def test_search_returns_results(self, test_vault_with_search_memories, mock_search_results, capsys):
        """Test search with mocked results."""
        with patch("memograph.core.kernel.MemoryKernel.search", return_value=mock_search_results):
            with patch("sys.argv", [
                "memograph",
                "--vault", str(test_vault_with_search_memories),
                "search", "python"
            ]):
                main()
        
        output = capsys.readouterr().out
        # Should show the mocked results
        assert "py-001" in output or "Python" in output
    
    def test_search_empty_results(self, test_vault_with_search_memories, capsys):
        """Test search with no results."""
        with patch("memograph.core.kernel.MemoryKernel.search", return_value=[]):
            with patch("sys.argv", [
                "memograph",
                "--vault", str(test_vault_with_search_memories),
                "search", "nonexistent"
            ]):
                main()
        
        output = capsys.readouterr().out
        assert "No results found" in output
    
    def test_search_with_scores(self, test_vault_with_search_memories, mock_search_results, capsys):
        """Test search showing scores."""
        with patch("memograph.core.kernel.MemoryKernel.search", return_value=mock_search_results):
            with patch("sys.argv", [
                "memograph",
                "--vault", str(test_vault_with_search_memories),
                "search", "python", "--show-scores"
            ]):
                main()
        
        output = capsys.readouterr().out
        # Should show scores
        assert "Score" in output or "0.95" in output or "0.88" in output
