"""
Access Tracker for Co-access Pattern Monitoring

Tracks which memories are accessed together to identify co-access patterns.
This helps the GAM scorer understand which memories are frequently used
in combination, improving relevance ranking.

Features:
    - Lightweight in-memory tracking
    - Periodic persistence to disk
    - Co-access frequency matrix
    - Query history with timestamps
"""

import json
import logging
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .node import MemoryNode

logger = logging.getLogger("memograph.access_tracker")


class AccessTracker:
    """
    Tracks co-access patterns between memories.

    When memories are retrieved together for a query, this tracker
    records the relationship. Over time, it builds a co-access matrix
    showing which memories are frequently used together.

    Example:
        >>> tracker = AccessTracker()
        >>> tracker.record_access("python tips", [node1, node2, node3])
        >>> score = tracker.get_co_access_score("node1_id", "node2_id")
        >>> print(f"Co-access count: {score}")
    """

    def __init__(self, max_history: int = 1000, persist_path: Path | None = None):
        """
        Initialize access tracker.

        Args:
            max_history: Maximum number of queries to keep in history
            persist_path: Optional path to persist tracker state
        """
        self.max_history = max_history
        self.persist_path = persist_path

        # Co-access matrix: node_id -> node_id -> count
        self.co_access_matrix: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

        # Query history: recent queries with accessed nodes
        self.access_history: deque = deque(maxlen=max_history)

        # Access counts per node
        self.node_access_counts: dict[str, int] = defaultdict(int)

        # Total queries tracked
        self.total_queries = 0

        # Load persisted state if available
        if persist_path and persist_path.exists():
            self.load(persist_path)

    def record_access(
        self,
        query: str,
        nodes: list["MemoryNode"],
        timestamp: datetime | None = None,
    ) -> None:
        """
        Record that these nodes were accessed together for a query.

        Updates:
        1. Co-access matrix (pairwise counts)
        2. Access history (query log)
        3. Individual node access counts

        Args:
            query: The query string
            nodes: List of nodes that were retrieved
            timestamp: Optional timestamp (uses current time if None)
        """
        if not nodes:
            return

        timestamp = timestamp or datetime.now(timezone.utc)
        node_ids = [node.id for node in nodes]

        # Update co-access matrix (pairwise)
        for i, id1 in enumerate(node_ids):
            # Update individual access count
            self.node_access_counts[id1] += 1

            # Update pairwise co-access
            for id2 in node_ids[i + 1 :]:
                self.co_access_matrix[id1][id2] += 1
                self.co_access_matrix[id2][id1] += 1

        # Add to history
        self.access_history.append(
            {"query": query, "nodes": node_ids, "timestamp": timestamp.isoformat()}
        )

        self.total_queries += 1

        logger.debug(f"Recorded access: query='{query}', nodes={len(node_ids)}")

        # Auto-persist if path is set and milestone reached
        if self.persist_path and self.total_queries % 100 == 0:
            self.save(self.persist_path)

    def get_co_access_score(self, node1_id: str, node2_id: str) -> int:
        """
        Get co-access frequency between two nodes.

        Args:
            node1_id: First node ID
            node2_id: Second node ID

        Returns:
            Number of times these nodes were accessed together
        """
        return self.co_access_matrix[node1_id].get(node2_id, 0)

    def get_node_access_count(self, node_id: str) -> int:
        """
        Get total access count for a node.

        Args:
            node_id: Node ID

        Returns:
            Number of times this node was accessed
        """
        return self.node_access_counts.get(node_id, 0)

    def get_most_related(self, node_id: str, top_k: int = 10) -> list[tuple[str, int]]:
        """
        Get nodes most frequently accessed with the given node.

        Args:
            node_id: Node ID to find related nodes for
            top_k: Maximum number of results

        Returns:
            List of (related_node_id, co_access_count) tuples,
            sorted by co-access count descending
        """
        if node_id not in self.co_access_matrix:
            return []

        related = self.co_access_matrix[node_id].items()
        sorted_related = sorted(related, key=lambda x: x[1], reverse=True)

        return sorted_related[:top_k]

    def get_recent_queries(self, limit: int = 10) -> list[dict]:
        """
        Get recent query history.

        Args:
            limit: Maximum number of queries to return

        Returns:
            List of query dicts with keys: query, nodes, timestamp
        """
        return list(self.access_history)[-limit:]

    def clear_history(self) -> None:
        """Clear query history but keep co-access matrix."""
        self.access_history.clear()
        logger.info("Cleared query history")

    def reset(self) -> None:
        """Reset all tracking data."""
        self.co_access_matrix.clear()
        self.access_history.clear()
        self.node_access_counts.clear()
        self.total_queries = 0
        logger.info("Reset access tracker")

    def save(self, path: Path) -> None:
        """
        Persist tracker state to disk.

        Args:
            path: Path to save state file
        """
        try:
            state = {
                "co_access_matrix": {k: dict(v) for k, v in self.co_access_matrix.items()},
                "access_history": list(self.access_history),
                "node_access_counts": dict(self.node_access_counts),
                "total_queries": self.total_queries,
                "saved_at": datetime.now(timezone.utc).isoformat(),
            }

            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)

            logger.info(f"Saved access tracker state to {path}")

        except Exception as e:
            logger.error(f"Failed to save access tracker: {e}")

    def load(self, path: Path) -> None:
        """
        Load tracker state from disk.

        Args:
            path: Path to load state file from
        """
        try:
            with open(path, encoding="utf-8") as f:
                state = json.load(f)

            # Restore co-access matrix
            self.co_access_matrix = defaultdict(
                lambda: defaultdict(int),
                {k: defaultdict(int, v) for k, v in state["co_access_matrix"].items()},
            )

            # Restore history
            history = state.get("access_history", [])
            self.access_history = deque(history, maxlen=self.max_history)

            # Restore access counts
            self.node_access_counts = defaultdict(int, state.get("node_access_counts", {}))

            # Restore query count
            self.total_queries = state.get("total_queries", 0)

            logger.info(f"Loaded access tracker state from {path}")

        except Exception as e:
            logger.error(f"Failed to load access tracker: {e}")

    def get_statistics(self) -> dict:
        """
        Get tracker statistics for debugging/analysis.

        Returns:
            Dict with statistics about tracked data
        """
        num_nodes_tracked = len(self.node_access_counts)
        num_relationships = sum(len(v) for v in self.co_access_matrix.values()) // 2

        most_accessed = []
        if self.node_access_counts:
            sorted_nodes = sorted(self.node_access_counts.items(), key=lambda x: x[1], reverse=True)
            most_accessed = sorted_nodes[:10]

        return {
            "total_queries": self.total_queries,
            "nodes_tracked": num_nodes_tracked,
            "relationships_tracked": num_relationships,
            "history_size": len(self.access_history),
            "most_accessed_nodes": most_accessed,
        }


# Convenience function for quick tracking
def track_access(
    tracker: AccessTracker,
    query: str,
    nodes: list["MemoryNode"],
) -> None:
    """
    Convenience function to track a query access.

    Example:
        >>> tracker = AccessTracker()
        >>> track_access(tracker, "python tips", [node1, node2])
    """
    tracker.record_access(query, nodes)
