"""
Unit tests for access tracker.
"""

import tempfile
from pathlib import Path

import pytest

from memograph.core.access_tracker import AccessTracker
from memograph.core.enums import MemoryType
from memograph.core.node import MemoryNode


@pytest.fixture
def sample_nodes():
    """Create sample nodes for testing."""
    return [
        MemoryNode(
            id="node1",
            title="Node 1",
            content="Content 1",
            memory_type=MemoryType.SEMANTIC,
            salience=0.8,
        ),
        MemoryNode(
            id="node2",
            title="Node 2",
            content="Content 2",
            memory_type=MemoryType.SEMANTIC,
            salience=0.6,
        ),
        MemoryNode(
            id="node3",
            title="Node 3",
            content="Content 3",
            memory_type=MemoryType.SEMANTIC,
            salience=0.5,
        ),
    ]


class TestAccessTracker:
    """Test access tracker."""

    def test_initialization(self):
        """Test tracker initialization."""
        tracker = AccessTracker()
        assert tracker.max_history == 1000
        assert tracker.total_queries == 0

    def test_record_access(self, sample_nodes):
        """Test recording access."""
        tracker = AccessTracker()
        tracker.record_access("test query", sample_nodes[:2])

        assert tracker.total_queries == 1
        assert len(tracker.access_history) == 1
        assert tracker.node_access_counts["node1"] == 1
        assert tracker.node_access_counts["node2"] == 1

    def test_co_access_matrix(self, sample_nodes):
        """Test co-access matrix building."""
        tracker = AccessTracker()
        tracker.record_access("query1", sample_nodes[:2])

        assert tracker.get_co_access_score("node1", "node2") == 1
        assert tracker.get_co_access_score("node2", "node1") == 1

    def test_multiple_accesses(self, sample_nodes):
        """Test multiple access recordings."""
        tracker = AccessTracker()

        tracker.record_access("query1", sample_nodes[:2])
        tracker.record_access("query2", sample_nodes[:2])
        tracker.record_access("query3", [sample_nodes[0], sample_nodes[2]])

        assert tracker.total_queries == 3
        assert tracker.node_access_counts["node1"] == 3
        assert tracker.node_access_counts["node2"] == 2
        assert tracker.get_co_access_score("node1", "node2") == 2

    def test_get_most_related(self, sample_nodes):
        """Test getting most related nodes."""
        tracker = AccessTracker()

        tracker.record_access("q1", [sample_nodes[0], sample_nodes[1]])
        tracker.record_access("q2", [sample_nodes[0], sample_nodes[1]])
        tracker.record_access("q3", [sample_nodes[0], sample_nodes[2]])

        related = tracker.get_most_related("node1", top_k=2)

        assert len(related) == 2
        assert related[0][0] == "node2"  # Most related
        assert related[0][1] == 2  # 2 co-accesses

    def test_get_statistics(self, sample_nodes):
        """Test getting statistics."""
        tracker = AccessTracker()

        tracker.record_access("q1", sample_nodes[:2])
        tracker.record_access("q2", sample_nodes[:2])

        stats = tracker.get_statistics()

        assert stats["total_queries"] == 2
        assert stats["nodes_tracked"] == 2
        assert stats["relationships_tracked"] == 1
        assert len(stats["most_accessed_nodes"]) > 0

    def test_persistence(self, sample_nodes):
        """Test save and load."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tracker.json"

            # Create and populate tracker
            tracker1 = AccessTracker()
            tracker1.record_access("query1", sample_nodes[:2])
            tracker1.record_access("query2", sample_nodes[:2])

            # Save
            tracker1.save(path)
            assert path.exists()

            # Load into new tracker
            tracker2 = AccessTracker()
            tracker2.load(path)

            assert tracker2.total_queries == 2
            assert tracker2.node_access_counts["node1"] == 2
            assert tracker2.get_co_access_score("node1", "node2") == 2

    def test_clear_history(self, sample_nodes):
        """Test clearing history."""
        tracker = AccessTracker()
        tracker.record_access("query", sample_nodes[:2])

        assert len(tracker.access_history) == 1

        tracker.clear_history()

        assert len(tracker.access_history) == 0
        assert tracker.node_access_counts["node1"] == 1  # Counts preserved

    def test_reset(self, sample_nodes):
        """Test reset."""
        tracker = AccessTracker()
        tracker.record_access("query", sample_nodes[:2])

        assert tracker.total_queries == 1

        tracker.reset()

        assert tracker.total_queries == 0
        assert len(tracker.access_history) == 0
        assert len(tracker.node_access_counts) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
