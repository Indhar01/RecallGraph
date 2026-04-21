"""Tests for Obsidian conflict resolution.

Tests cover:
- All conflict strategies (OBSIDIAN_WINS, MEMOGRAPH_WINS, NEWEST_WINS, MANUAL)
- Conflict detection
- Edge cases (empty content, identical timestamps, None values)
- Conflict marker creation
- Hash content functionality
"""

from memograph.integrations.obsidian.conflict_resolver import (
    ConflictResolver,
    ConflictStrategy,
)


class TestConflictStrategy:
    """Test ConflictStrategy enum."""

    def test_strategy_values(self):
        """Test that all strategy values are defined."""
        assert ConflictStrategy.OBSIDIAN_WINS.value == "obsidian_wins"
        assert ConflictStrategy.MEMOGRAPH_WINS.value == "memograph_wins"
        assert ConflictStrategy.NEWEST_WINS.value == "newest_wins"
        assert ConflictStrategy.MANUAL.value == "manual"


class TestConflictDetection:
    """Test conflict detection functionality."""

    def test_detect_conflict_different_content(self):
        """Test conflict detection with different content."""
        resolver = ConflictResolver()

        obsidian_version = {"content": "Version A", "modified": 1000}
        memograph_version = {"content": "Version B", "modified": 2000}

        assert resolver.detect_conflict(obsidian_version, memograph_version) is True

    def test_no_conflict_same_content(self):
        """Test no conflict with same content."""
        resolver = ConflictResolver()

        obsidian_version = {"content": "Same content", "modified": 1000}
        memograph_version = {"content": "Same content", "modified": 2000}

        assert resolver.detect_conflict(obsidian_version, memograph_version) is False

    def test_detect_conflict_empty_content(self):
        """Test conflict detection with empty content."""
        resolver = ConflictResolver()

        # Both empty - no conflict
        obsidian_version = {"content": ""}
        memograph_version = {"content": ""}
        assert resolver.detect_conflict(obsidian_version, memograph_version) is False

        # One empty, one not - conflict
        obsidian_version = {"content": "Content"}
        memograph_version = {"content": ""}
        assert resolver.detect_conflict(obsidian_version, memograph_version) is True

    def test_detect_conflict_missing_content_key(self):
        """Test conflict detection with missing content key."""
        resolver = ConflictResolver()

        # Both missing content key - no conflict
        obsidian_version = {"title": "Test"}
        memograph_version = {"title": "Test"}
        assert resolver.detect_conflict(obsidian_version, memograph_version) is False

        # One missing, one present - conflict
        obsidian_version = {"content": "Content"}
        memograph_version = {"title": "Test"}
        assert resolver.detect_conflict(obsidian_version, memograph_version) is True


class TestObsidianWinsStrategy:
    """Test OBSIDIAN_WINS conflict resolution strategy."""

    def test_obsidian_wins_basic(self):
        """Test that Obsidian version wins."""
        resolver = ConflictResolver(strategy=ConflictStrategy.OBSIDIAN_WINS)

        obsidian_version = {"content": "Obsidian content", "modified": 1000}
        memograph_version = {"content": "MemoGraph content", "modified": 2000}

        result = resolver.resolve(obsidian_version, memograph_version)
        assert result == obsidian_version
        assert result["content"] == "Obsidian content"

    def test_obsidian_wins_newer_memograph(self):
        """Test Obsidian wins even when MemoGraph is newer."""
        resolver = ConflictResolver(strategy=ConflictStrategy.OBSIDIAN_WINS)

        obsidian_version = {"content": "Old Obsidian", "modified": 1000}
        memograph_version = {"content": "New MemoGraph", "modified": 3000}

        result = resolver.resolve(obsidian_version, memograph_version)
        assert result == obsidian_version


class TestMemographWinsStrategy:
    """Test MEMOGRAPH_WINS conflict resolution strategy."""

    def test_memograph_wins_basic(self):
        """Test that MemoGraph version wins."""
        resolver = ConflictResolver(strategy=ConflictStrategy.MEMOGRAPH_WINS)

        obsidian_version = {"content": "Obsidian content", "modified": 2000}
        memograph_version = {"content": "MemoGraph content", "modified": 1000}

        result = resolver.resolve(obsidian_version, memograph_version)
        assert result == memograph_version
        assert result["content"] == "MemoGraph content"

    def test_memograph_wins_newer_obsidian(self):
        """Test MemoGraph wins even when Obsidian is newer."""
        resolver = ConflictResolver(strategy=ConflictStrategy.MEMOGRAPH_WINS)

        obsidian_version = {"content": "New Obsidian", "modified": 3000}
        memograph_version = {"content": "Old MemoGraph", "modified": 1000}

        result = resolver.resolve(obsidian_version, memograph_version)
        assert result == memograph_version


class TestNewestWinsStrategy:
    """Test NEWEST_WINS conflict resolution strategy."""

    def test_newest_wins_obsidian_newer(self):
        """Test newest wins when Obsidian is newer."""
        resolver = ConflictResolver(strategy=ConflictStrategy.NEWEST_WINS)

        obsidian_version = {"content": "New Obsidian", "modified": 3000}
        memograph_version = {"content": "Old MemoGraph", "modified": 1000}

        result = resolver.resolve(obsidian_version, memograph_version)
        assert result == obsidian_version
        assert result["content"] == "New Obsidian"

    def test_newest_wins_memograph_newer(self):
        """Test newest wins when MemoGraph is newer."""
        resolver = ConflictResolver(strategy=ConflictStrategy.NEWEST_WINS)

        obsidian_version = {"content": "Old Obsidian", "modified": 1000}
        memograph_version = {"content": "New MemoGraph", "modified": 3000}

        result = resolver.resolve(obsidian_version, memograph_version)
        assert result == memograph_version
        assert result["content"] == "New MemoGraph"

    def test_newest_wins_identical_timestamps(self):
        """Test newest wins with identical timestamps (edge case)."""
        resolver = ConflictResolver(strategy=ConflictStrategy.NEWEST_WINS)

        obsidian_version = {"content": "Obsidian", "modified": 2000}
        memograph_version = {"content": "MemoGraph", "modified": 2000}

        # Should prefer Obsidian when timestamps are identical
        result = resolver.resolve(obsidian_version, memograph_version)
        assert result == obsidian_version

    def test_newest_wins_missing_timestamps(self):
        """Test newest wins with missing timestamps."""
        resolver = ConflictResolver(strategy=ConflictStrategy.NEWEST_WINS)

        obsidian_version = {"content": "Obsidian"}
        memograph_version = {"content": "MemoGraph"}

        # Should prefer Obsidian when both timestamps missing (both default to 0)
        result = resolver.resolve(obsidian_version, memograph_version)
        assert result == obsidian_version


class TestManualStrategy:
    """Test MANUAL conflict resolution strategy."""

    def test_manual_creates_conflict_marker(self):
        """Test that manual strategy creates conflict markers."""
        resolver = ConflictResolver(strategy=ConflictStrategy.MANUAL)

        obsidian_version = {
            "content": "Obsidian content",
            "title": "Test Note",
            "modified": 1000,
        }
        memograph_version = {"content": "MemoGraph content", "modified": 2000}

        result = resolver.resolve(obsidian_version, memograph_version)

        # Check conflict marker format
        assert "<<<<<<< Obsidian Version" in result["content"]
        assert "Obsidian content" in result["content"]
        assert "=======" in result["content"]
        assert "MemoGraph content" in result["content"]
        assert ">>>>>>> MemoGraph Version" in result["content"]

        # Check conflict flag
        assert result["conflict"] is True

        # Check other fields preserved
        assert result["title"] == "Test Note"
        assert result["modified"] == 1000

    def test_manual_empty_content(self):
        """Test manual strategy with empty content."""
        resolver = ConflictResolver(strategy=ConflictStrategy.MANUAL)

        obsidian_version = {"content": ""}
        memograph_version = {"content": "MemoGraph content"}

        result = resolver.resolve(obsidian_version, memograph_version)

        assert "<<<<<<< Obsidian Version" in result["content"]
        assert "=======" in result["content"]
        assert "MemoGraph content" in result["content"]
        assert ">>>>>>> MemoGraph Version" in result["content"]
        assert result["conflict"] is True


class TestConflictMarkerCreation:
    """Test conflict marker creation."""

    def test_create_conflict_marker_basic(self):
        """Test basic conflict marker creation."""
        resolver = ConflictResolver()

        version1 = {"content": "Version 1 content", "title": "Test", "tags": ["tag1"]}
        version2 = {"content": "Version 2 content", "tags": ["tag2"]}

        result = resolver.create_conflict_marker(version1, version2)

        # Check marker structure
        assert "<<<<<<< Obsidian Version" in result["content"]
        assert "Version 1 content" in result["content"]
        assert "=======" in result["content"]
        assert "Version 2 content" in result["content"]
        assert ">>>>>>> MemoGraph Version" in result["content"]

        # Check metadata preserved from version1
        assert result["title"] == "Test"
        assert result["tags"] == ["tag1"]
        assert result["conflict"] is True

    def test_create_conflict_marker_missing_content(self):
        """Test conflict marker with missing content."""
        resolver = ConflictResolver()

        version1 = {"title": "Test"}
        version2 = {"content": "Content"}

        result = resolver.create_conflict_marker(version1, version2)

        assert "<<<<<<< Obsidian Version" in result["content"]
        assert "=======" in result["content"]
        assert "Content" in result["content"]
        assert ">>>>>>> MemoGraph Version" in result["content"]


class TestHashContent:
    """Test content hashing functionality."""

    def test_hash_content_basic(self):
        """Test basic content hashing."""
        resolver = ConflictResolver()

        content = "Test content"
        hash1 = resolver.hash_content(content)
        hash2 = resolver.hash_content(content)

        # Same content should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 32  # MD5 hash length

    def test_hash_content_different(self):
        """Test that different content produces different hashes."""
        resolver = ConflictResolver()

        hash1 = resolver.hash_content("Content A")
        hash2 = resolver.hash_content("Content B")

        assert hash1 != hash2

    def test_hash_content_empty(self):
        """Test hashing empty content."""
        resolver = ConflictResolver()

        hash_empty = resolver.hash_content("")

        # Empty string should produce consistent hash
        assert hash_empty == resolver.hash_content("")
        assert len(hash_empty) == 32

    def test_hash_content_unicode(self):
        """Test hashing unicode content."""
        resolver = ConflictResolver()

        content = "Test 测试 テスト"
        hash1 = resolver.hash_content(content)

        # Should handle unicode properly
        assert len(hash1) == 32
        assert hash1 == resolver.hash_content(content)


class TestDefaultBehavior:
    """Test default initialization and behavior."""

    def test_default_strategy(self):
        """Test that default strategy is NEWEST_WINS."""
        resolver = ConflictResolver()

        assert resolver.strategy == ConflictStrategy.NEWEST_WINS

    def test_strategy_initialization(self):
        """Test strategy can be set during initialization."""
        resolver = ConflictResolver(strategy=ConflictStrategy.OBSIDIAN_WINS)

        assert resolver.strategy == ConflictStrategy.OBSIDIAN_WINS


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_resolve_with_none_values(self):
        """Test resolution with None values in data."""
        resolver = ConflictResolver()

        obsidian_version = {"content": "Content", "title": None, "modified": 1000}
        memograph_version = {"content": "Content", "modified": 2000}

        # Should not raise error
        result = resolver.resolve(obsidian_version, memograph_version)
        assert result is not None

    def test_detect_conflict_with_special_characters(self):
        """Test conflict detection with special characters."""
        resolver = ConflictResolver()

        obsidian_version = {"content": "Content with [[wikilinks]] and #tags"}
        memograph_version = {"content": "Content with [[different]] and #tags"}

        assert resolver.detect_conflict(obsidian_version, memograph_version) is True

    def test_large_content_hashing(self):
        """Test hashing large content."""
        resolver = ConflictResolver()

        # Create large content
        large_content = "Lorem ipsum " * 10000
        hash_value = resolver.hash_content(large_content)

        # Should handle large content without error
        assert len(hash_value) == 32
        assert hash_value == resolver.hash_content(large_content)
