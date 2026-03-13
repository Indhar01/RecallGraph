"""
GAM (Graph Attention Memory) Scorer

Lightweight graph attention scoring without neural networks.
Pure Python implementation that combines multiple signals into relevance scores.

Scoring Formula:
    score = α·relationship + β·co_access + γ·recency + δ·salience

Where:
    - relationship: Graph distance-based weighting (wikilinks, backlinks)
    - co_access: Frequency of memories accessed together
    - recency: Time-based decay (newer = higher score)
    - salience: Existing importance score (0.0-1.0)
"""

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .access_tracker import AccessTracker
    from .graph import VaultGraph
    from .node import MemoryNode


@dataclass
class GAMConfig:
    """
    Configuration for GAM scoring weights.

    All weights should sum to 1.0 for normalized scoring.

    Attributes:
        relationship_weight: Weight for graph relationship score (0.0-1.0)
        co_access_weight: Weight for co-access frequency score (0.0-1.0)
        recency_weight: Weight for temporal recency score (0.0-1.0)
        salience_weight: Weight for memory importance score (0.0-1.0)
        recency_decay_days: Half-life for exponential decay (in days)
        max_graph_distance: Maximum graph hops to consider
    """

    relationship_weight: float = 0.3
    co_access_weight: float = 0.2
    recency_weight: float = 0.2
    salience_weight: float = 0.3
    recency_decay_days: float = 30.0
    max_graph_distance: int = 3

    def __post_init__(self):
        """Validate weights sum to 1.0"""
        total = (
            self.relationship_weight
            + self.co_access_weight
            + self.recency_weight
            + self.salience_weight
        )
        if not math.isclose(total, 1.0, rel_tol=1e-5):
            raise ValueError(
                f"GAM weights must sum to 1.0, got {total}. "
                f"Adjust relationship_weight={self.relationship_weight}, "
                f"co_access_weight={self.co_access_weight}, "
                f"recency_weight={self.recency_weight}, "
                f"salience_weight={self.salience_weight}"
            )


class GAMScorer:
    """
    Graph Attention Memory scorer for relevance ranking.

    This scorer combines multiple signals to rank memory nodes:
    1. Relationship strength (graph structure)
    2. Co-access patterns (memories used together)
    3. Temporal recency (time-based decay)
    4. Salience (importance score)

    Example:
        >>> config = GAMConfig(
        ...     relationship_weight=0.4,
        ...     recency_weight=0.3,
        ...     salience_weight=0.3
        ... )
        >>> scorer = GAMScorer(config)
        >>> score = scorer.compute_score(node, query_context, graph, access_tracker)
    """

    def __init__(self, config: GAMConfig | None = None):
        """
        Initialize GAM scorer.

        Args:
            config: GAM configuration. If None, uses default weights.
        """
        self.config = config or GAMConfig()

    def compute_score(
        self,
        node: "MemoryNode",
        query_context: dict,
        graph: "VaultGraph",
        access_tracker: "AccessTracker | None" = None,
    ) -> float:
        """
        Compute GAM score for a memory node.

        Args:
            node: Memory node to score
            query_context: Context dict with keys:
                - 'seed_ids': list[str] - IDs of seed nodes from query
                - 'query': str - original query string
            graph: Vault graph for relationship scoring
            access_tracker: Optional access tracker for co-access scoring

        Returns:
            GAM score (0.0-1.0), higher = more relevant
        """
        # Component scores (all normalized to 0.0-1.0)
        relationship_score = self._compute_relationship_score(
            node, query_context.get("seed_ids", []), graph
        )

        co_access_score = self._compute_co_access_score(
            node, query_context.get("seed_ids", []), access_tracker
        )

        recency_score = self._compute_recency_score(node)

        salience_score = node.salience  # Already 0.0-1.0

        # Weighted combination
        final_score = (
            self.config.relationship_weight * relationship_score
            + self.config.co_access_weight * co_access_score
            + self.config.recency_weight * recency_score
            + self.config.salience_weight * salience_score
        )

        return final_score

    def _compute_relationship_score(
        self,
        node: "MemoryNode",
        seed_ids: list[str],
        graph: "VaultGraph",
    ) -> float:
        """
        Compute relationship score based on graph structure.

        Score decreases exponentially with graph distance from seed nodes.

        Args:
            node: Node to score
            seed_ids: IDs of seed nodes (starting points)
            graph: Vault graph

        Returns:
            Relationship score (0.0-1.0)
        """
        if not seed_ids:
            return 0.5  # Neutral score if no seeds

        # If node is itself a seed, max score
        if node.id in seed_ids:
            return 1.0

        # Find minimum graph distance to any seed
        min_distance = self._find_min_graph_distance(node.id, seed_ids, graph)

        if min_distance is None or min_distance > self.config.max_graph_distance:
            return 0.1  # Distant or unconnected nodes get low score

        # Exponential decay: score = exp(-distance/2)
        # distance=0: score=1.0
        # distance=1: score=0.61
        # distance=2: score=0.37
        # distance=3: score=0.22
        score = math.exp(-min_distance / 2.0)

        return score

    def _find_min_graph_distance(
        self,
        target_id: str,
        seed_ids: list[str],
        graph: "VaultGraph",
    ) -> int | None:
        """
        Find minimum graph distance from target to any seed node using BFS.

        Args:
            target_id: ID of target node
            seed_ids: IDs of seed nodes
            graph: Vault graph

        Returns:
            Minimum distance (hops), or None if not reachable
        """
        from collections import deque

        # BFS from target to find nearest seed
        visited = {target_id}
        queue = deque([(target_id, 0)])

        while queue:
            current_id, distance = queue.popleft()

            # Check if we reached a seed
            if current_id in seed_ids:
                return distance

            # Stop if beyond max distance
            if distance >= self.config.max_graph_distance:
                continue

            # Get current node
            current_node = graph.get(current_id)
            if not current_node:
                continue

            # Explore neighbors (links + backlinks)
            neighbors = set(current_node.links) | set(current_node.backlinks)

            for neighbor_id in neighbors:
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, distance + 1))

        return None  # Not reachable within max distance

    def _compute_co_access_score(
        self,
        node: "MemoryNode",
        seed_ids: list[str],
        access_tracker: "AccessTracker | None",
    ) -> float:
        """
        Compute co-access score based on historical access patterns.

        Memories frequently accessed together with seeds get higher scores.

        Args:
            node: Node to score
            seed_ids: IDs of seed nodes
            access_tracker: Access tracker (None if not available)

        Returns:
            Co-access score (0.0-1.0)
        """
        if not access_tracker or not seed_ids:
            return 0.5  # Neutral if no data

        # Get co-access counts with each seed
        co_access_counts = []
        for seed_id in seed_ids:
            count = access_tracker.get_co_access_score(node.id, seed_id)
            co_access_counts.append(count)

        if not co_access_counts:
            return 0.5

        # Use max co-access count (strongest relationship)
        max_count = max(co_access_counts)

        # Normalize using sigmoid-like function
        # count=0: score=0.5
        # count=5: score=0.82
        # count=10: score=0.92
        # count=20: score=0.97
        score = 1.0 / (1.0 + math.exp(-0.3 * (max_count - 5)))

        return score

    def _compute_recency_score(self, node: "MemoryNode") -> float:
        """
        Compute recency score based on time since last access or creation.

        Uses exponential decay with configurable half-life.

        Args:
            node: Node to score

        Returns:
            Recency score (0.0-1.0)
        """
        # Use last_accessed if available, otherwise created_at
        reference_time = node.last_accessed or node.created_at

        # Calculate age in days
        now = datetime.now(timezone.utc)
        age_seconds = (now - reference_time).total_seconds()
        age_days = age_seconds / (24 * 3600)

        # Exponential decay: score = exp(-age / half_life)
        # age=0: score=1.0 (just accessed)
        # age=half_life: score=0.5
        # age=2*half_life: score=0.25
        half_life = self.config.recency_decay_days
        score = math.exp(-age_days / half_life)

        return score

    def explain_score(
        self,
        node: "MemoryNode",
        query_context: dict,
        graph: "VaultGraph",
        access_tracker: "AccessTracker | None" = None,
    ) -> dict:
        """
        Explain the GAM score breakdown for debugging/analysis.

        Returns dict with component scores and final score.

        Example:
            >>> explanation = scorer.explain_score(node, context, graph, tracker)
            >>> print(f"Final: {explanation['final_score']:.3f}")
            >>> print(f"  Relationship: {explanation['relationship_score']:.3f}")
            >>> print(f"  Co-access: {explanation['co_access_score']:.3f}")
            >>> print(f"  Recency: {explanation['recency_score']:.3f}")
            >>> print(f"  Salience: {explanation['salience_score']:.3f}")
        """
        relationship_score = self._compute_relationship_score(
            node, query_context.get("seed_ids", []), graph
        )
        co_access_score = self._compute_co_access_score(
            node, query_context.get("seed_ids", []), access_tracker
        )
        recency_score = self._compute_recency_score(node)
        salience_score = node.salience

        final_score = (
            self.config.relationship_weight * relationship_score
            + self.config.co_access_weight * co_access_score
            + self.config.recency_weight * recency_score
            + self.config.salience_weight * salience_score
        )

        return {
            "node_id": node.id,
            "node_title": node.title,
            "final_score": final_score,
            "components": {
                "relationship": {
                    "score": relationship_score,
                    "weight": self.config.relationship_weight,
                    "contribution": self.config.relationship_weight * relationship_score,
                },
                "co_access": {
                    "score": co_access_score,
                    "weight": self.config.co_access_weight,
                    "contribution": self.config.co_access_weight * co_access_score,
                },
                "recency": {
                    "score": recency_score,
                    "weight": self.config.recency_weight,
                    "contribution": self.config.recency_weight * recency_score,
                },
                "salience": {
                    "score": salience_score,
                    "weight": self.config.salience_weight,
                    "contribution": self.config.salience_weight * salience_score,
                },
            },
        }


# Convenience function for quick scoring
def score_memory(
    node: "MemoryNode",
    query_context: dict,
    graph: "VaultGraph",
    config: GAMConfig | None = None,
) -> float:
    """
    Convenience function to score a single memory node.

    Example:
        >>> score = score_memory(node, {"seed_ids": ["id1", "id2"]}, graph)
    """
    scorer = GAMScorer(config)
    return scorer.compute_score(node, query_context, graph)
