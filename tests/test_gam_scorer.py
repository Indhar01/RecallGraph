"""
Unit tests for GAM scorer.
"""

import math
from datetime import datetime, timedelta, timezone

import pytest

from memograph.core.access_tracker import AccessTracker
from memograph.core.enums import MemoryType
from memograph.core.gam_scorer import GAMConfig, GAMScorer
from memograph.core.graph import VaultGraph
from memograph.core.node import MemoryNode


@pytest.fixture
def basic_config():
    """Default GAM configuration."""
    return GAMConfig()


@pytest.fixture
def custom_config():
    """Custom GAM configuration."""
    return GAMConfig(
        relationship_weight=0.4,
        recency_weight=0.3,
        salience_weight=0.3,
        co_access_weight=0.0,
    )


@pytest.fixture
def sample_graph():
    """Create a sample graph for testing."""
    graph = VaultGraph()

    # Create nodes
    node1 = MemoryNode(
        id="node1",
        title="Node 1",
        content="Content 1",
        memory_type=MemoryType.SEMANTIC,
        salience=0.8,
        created_at=datetime.now(timezone.utc) - timedelta(days=10),
        last_accessed=datetime.now(timezone.utc) - timedelta(days=5),
    )

    node2 = MemoryNode(
        id="node2",
        title="Node 2",
        content="Content 2 with [[Node 1]] link",
        memory_type=MemoryType.SEMANTIC,
        salience=0.6,
        links=["node1"],
        created_at=datetime.now(timezone.utc) - timedelta(days=20),
        last_accessed=datetime.now(timezone.utc) - timedelta(days=2),
    )

    node3 = MemoryNode(
        id="node3",
        title="Node 3",
        content="Content 3 with [[Node 2]] link",
        memory_type=MemoryType.SEMANTIC,
        salience=0.5,
        links=["node2"],
        created_at=datetime.now(timezone.utc) - timedelta(days=30),
        last_accessed=datetime.now(timezone.utc) - timedelta(days=1),
    )

    graph.add_node(node1)
    graph.add_node(node2)
    graph.add_node(node3)
    graph.build_backlinks()

    return graph


class TestGAMConfig:
    """Test GAM configuration."""

    def test_default_config(self):
        """Test default configuration."""
        config = GAMConfig()

        assert config.relationship_weight == 0.3
        assert config.co_access_weight == 0.2
        assert config.recency_weight == 0.2
        assert config.salience_weight == 0.3
        assert config.recency_decay_days == 30.0
        assert config.max_graph_distance == 3

    def test_custom_config(self):
        """Test custom configuration."""
        config = GAMConfig(
            relationship_weight=0.4,
            recency_weight=0.3,
            salience_weight=0.3,
            co_access_weight=0.0,
        )

        assert config.relationship_weight == 0.4
        assert config.recency_weight == 0.3
        assert config.salience_weight == 0.3
        assert config.co_access_weight == 0.0

    def test_weights_must_sum_to_one(self):
        """Test that weights must sum to 1.0."""
        with pytest.raises(ValueError, match="must sum to 1.0"):
            GAMConfig(
                relationship_weight=0.5,
                recency_weight=0.3,
                salience_weight=0.3,
                co_access_weight=0.0,  # Sum = 1.1
            )


class TestGAMScorer:
    """Test GAM scorer."""

    def test_scorer_initialization(self, basic_config):
        """Test scorer initialization."""
        scorer = GAMScorer(basic_config)
        assert scorer.config == basic_config

    def test_relationship_score_same_node(self, basic_config, sample_graph):
        """Test relationship score for same node."""
        scorer = GAMScorer(basic_config)
        node = sample_graph.get("node1")

        # Node itself should have max score
        score = scorer._compute_relationship_score(node, ["node1"], sample_graph)
        assert score == 1.0

    def test_relationship_score_direct_link(self, basic_config, sample_graph):
        """Test relationship score for directly linked nodes."""
        scorer = GAMScorer(basic_config)
        node2 = sample_graph.get("node2")

        # node2 links to node1 (distance=1)
        score = scorer._compute_relationship_score(node2, ["node1"], sample_graph)
        expected = math.exp(-1 / 2.0)  # ~0.61
        assert abs(score - expected) < 0.01

    def test_relationship_score_no_seeds(self, basic_config, sample_graph):
        """Test relationship score with no seed nodes."""
        scorer = GAMScorer(basic_config)
        node = sample_graph.get("node1")

        # No seeds = neutral score
        score = scorer._compute_relationship_score(node, [], sample_graph)
        assert score == 0.5

    def test_recency_score_just_accessed(self, basic_config):
        """Test recency score for just-accessed node."""
        scorer = GAMScorer(basic_config)
        node = MemoryNode(
            id="test",
            title="Test",
            content="Test",
            memory_type=MemoryType.FACT,
            salience=0.5,
            created_at=datetime.now(timezone.utc),
            last_accessed=datetime.now(timezone.utc),
        )

        score = scorer._compute_recency_score(node)
        assert score > 0.99  # Should be ~1.0

    def test_recency_score_old_memory(self, basic_config):
        """Test recency score for old memory."""
        scorer = GAMScorer(basic_config)
        node = MemoryNode(
            id="test",
            title="Test",
            content="Test",
            memory_type=MemoryType.FACT,
            salience=0.5,
            created_at=datetime.now(timezone.utc) - timedelta(days=90),
            last_accessed=datetime.now(timezone.utc) - timedelta(days=90),
        )

        score = scorer._compute_recency_score(node)
        # 90 days with 30-day half-life = 3 half-lives = 0.5^3 = 0.125
        expected = math.exp(-90 / 30.0)
        assert abs(score - expected) < 0.01

    def test_co_access_score_no_tracker(self, basic_config, sample_graph):
        """Test co-access score without tracker."""
        scorer = GAMScorer(basic_config)
        node = sample_graph.get("node1")

        # No tracker = neutral score
        score = scorer._compute_co_access_score(node, ["node2"], None)
        assert score == 0.5

    def test_co_access_score_with_tracker(self, basic_config, sample_graph):
        """Test co-access score with tracker."""
        scorer = GAMScorer(basic_config)
        tracker = AccessTracker()
        node1 = sample_graph.get("node1")
        node2 = sample_graph.get("node2")

        # Record some co-accesses (need more for score > 0.5)
        for i in range(10):
            tracker.record_access(f"query{i}", [node1, node2])

        score = scorer._compute_co_access_score(node1, ["node2"], tracker)
        # 10 co-accesses should give score > 0.5
        assert score > 0.5

    def test_compute_score(self, basic_config, sample_graph):
        """Test complete score computation."""
        scorer = GAMScorer(basic_config)
        node = sample_graph.get("node1")

        query_context = {"query": "test", "seed_ids": ["node1"]}

        score = scorer.compute_score(node, query_context, sample_graph)

        # Score should be between 0 and 1
        assert 0.0 <= score <= 1.0

        # For same node with high salience, score should be high
        assert score > 0.7

    def test_explain_score(self, basic_config, sample_graph):
        """Test score explanation."""
        scorer = GAMScorer(basic_config)
        node = sample_graph.get("node1")

        query_context = {"query": "test", "seed_ids": ["node1"]}

        explanation = scorer.explain_score(node, query_context, sample_graph)

        assert "node_id" in explanation
        assert "final_score" in explanation
        assert "components" in explanation

        comps = explanation["components"]
        assert "relationship" in comps
        assert "co_access" in comps
        assert "recency" in comps
        assert "salience" in comps

        # Each component should have score, weight, contribution
        for comp in comps.values():
            assert "score" in comp
            assert "weight" in comp
            assert "contribution" in comp


class TestGraphDistance:
    """Test graph distance calculations."""

    def test_find_min_distance_same_node(self, basic_config, sample_graph):
        """Test distance to same node."""
        scorer = GAMScorer(basic_config)

        distance = scorer._find_min_graph_distance("node1", ["node1"], sample_graph)
        assert distance == 0

    def test_find_min_distance_direct_link(self, basic_config, sample_graph):
        """Test distance through direct link."""
        scorer = GAMScorer(basic_config)

        # node2 links to node1
        distance = scorer._find_min_graph_distance("node2", ["node1"], sample_graph)
        assert distance == 1

    def test_find_min_distance_two_hops(self, basic_config, sample_graph):
        """Test distance through two hops."""
        scorer = GAMScorer(basic_config)

        # node3 -> node2 -> node1
        distance = scorer._find_min_graph_distance("node3", ["node1"], sample_graph)
        assert distance == 2

    def test_find_min_distance_unreachable(self, basic_config):
        """Test distance to unreachable node."""
        scorer = GAMScorer(basic_config)
        graph = VaultGraph()

        # Create disconnected nodes
        node1 = MemoryNode(
            id="node1", title="Node 1", content="Content", memory_type=MemoryType.FACT, salience=0.5
        )
        node2 = MemoryNode(
            id="node2", title="Node 2", content="Content", memory_type=MemoryType.FACT, salience=0.5
        )

        graph.add_node(node1)
        graph.add_node(node2)

        distance = scorer._find_min_graph_distance("node2", ["node1"], graph)
        assert distance is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
