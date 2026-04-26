"""Bidirectional sync between Obsidian and MemoGraph.

This module provides full bidirectional synchronization between an Obsidian vault
and MemoGraph's memory system, handling conflicts, tracking state, and maintaining
consistency across both systems.
"""

import hashlib
import asyncio
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Callable, Tuple
from datetime import datetime
from collections import deque

from memograph import MemoryKernel
from memograph.core.enums import MemoryType
from .parser import ObsidianParser
from .sync_state import SyncState
from .conflict_resolver import ConflictResolver, ConflictStrategy
from .performance_metrics import get_tracker


# Type alias for progress callback
# Callback receives: (current_index, total_files, current_file_path, status)
ProgressCallback = Callable[[int, int, str, str], None]


class BatchSyncCancelled(Exception):
    """Exception raised when batch sync is cancelled."""

    pass


class ObsidianSync:
    """Bidirectional sync between Obsidian and MemoGraph."""

    def __init__(
        self,
        vault_path: Path,
        memograph_vault: Path,
        conflict_strategy: ConflictStrategy = ConflictStrategy.NEWEST_WINS,
        enable_queue: bool = True,
        max_queue_size: int = 100,
        rate_limit_delay: float = 1.0,
    ):
        """Initialize Obsidian sync manager.

        Args:
            vault_path: Path to the Obsidian vault directory
            memograph_vault: Path to the MemoGraph vault directory
            conflict_strategy: Strategy for resolving sync conflicts
            enable_queue: Enable sync queue for rate limiting
            max_queue_size: Maximum number of files in sync queue
            rate_limit_delay: Minimum delay between sync operations (seconds)
        """
        self.vault_path = Path(vault_path)
        self.memograph_vault = Path(memograph_vault)
        self.kernel = MemoryKernel(str(memograph_vault))
        self.parser = ObsidianParser(cache_size=256)  # Enable LRU caching
        self.state = SyncState(
            memograph_vault / ".obsidian_sync_state.json", use_sqlite=True
        )
        self.resolver = ConflictResolver(conflict_strategy)
        self.perf_tracker = get_tracker()

        # Sync queue configuration
        self.enable_queue = enable_queue
        self.max_queue_size = max_queue_size
        self.rate_limit_delay = rate_limit_delay

        # Sync queue state
        self._sync_queue: deque = deque(maxlen=max_queue_size)
        self._queued_files: Set[str] = set()
        self._queue_lock = asyncio.Lock()
        self._is_syncing = False
        self._last_sync_time = 0.0
        self._queue_processor_task: Optional[asyncio.Task] = None

        # Batch sync state
        self._batch_cancelled = False
        self._current_batch_progress: Dict[str, Any] = {}

        # Error tracking
        self._error_history: List[Dict[str, Any]] = []
        self._error_count = 0
        self._error_rate_limit = (
            10  # Max errors before stopping (lowered for better safety)
        )
        self._last_error_time = 0.0

        # Ensure vault paths exist
        self.vault_path.mkdir(parents=True, exist_ok=True)
        self.memograph_vault.mkdir(parents=True, exist_ok=True)

    def _build_path_index(self) -> Dict[str, Any]:
        """Build an O(1) lookup index of obsidian_path -> MemoryNode.

        Iterates all nodes once and returns a dict for fast lookups.
        Use this instead of calling _find_memory_by_path in a loop.

        Returns:
            Dictionary mapping obsidian_path strings to MemoryNodes
        """
        index = {}
        for node in self.kernel.graph.all_nodes():
            path = node.frontmatter.get("meta", {}).get("obsidian_path")
            if path:
                index[path] = node
        return index

    def _build_title_index(self) -> Dict[str, Any]:
        """Build an O(1) lookup index of title -> MemoryNode for Obsidian memories.

        Iterates all nodes once and returns a dict for fast lookups.
        Use this instead of calling _find_memory_by_title in a loop.

        Returns:
            Dictionary mapping title strings to MemoryNodes (Obsidian source only)
        """
        index = {}
        for node in self.kernel.graph.all_nodes():
            if node.frontmatter.get("meta", {}).get("source") == "obsidian":
                index[node.title] = node
        return index

    async def sync(self, direction: str = "bidirectional") -> Dict[str, Any]:
        """Perform sync operation.

        Args:
            direction: Sync direction - "pull", "push", or "bidirectional"

        Returns:
            Dictionary with sync statistics:
                - pulled: Number of notes pulled from Obsidian
                - pushed: Number of notes pushed to Obsidian
                - conflicts: Number of conflicts encountered
                - errors: List of error messages
                - duration: Duration in seconds
                - timestamp: ISO timestamp of sync completion
        """
        start_time = time.time()
        stats = {"pulled": 0, "pushed": 0, "conflicts": 0, "errors": []}
        self._is_syncing = True

        with self.perf_tracker.track_operation("sync", direction=direction):
            try:
                # Ensure graph is loaded (only if empty)
                if not self.kernel.graph or not list(self.kernel.graph.all_nodes()):
                    self.kernel.ingest()

                if direction in ["pull", "bidirectional"]:
                    try:
                        pull_stats = await self.pull_from_obsidian()
                        stats["pulled"] = pull_stats["count"]
                        stats["conflicts"] += pull_stats["conflicts"]
                        if "errors" in pull_stats and pull_stats["errors"]:
                            stats["errors"].extend(pull_stats["errors"])
                    except (ConnectionError, TimeoutError, ConnectionRefusedError) as e:
                        error_msg = f"Network error during pull: {str(e)}"
                        stats["errors"].append(error_msg)
                        self._record_error(e, transient=True)

                if direction in ["push", "bidirectional"]:
                    try:
                        push_stats = await self.push_to_obsidian()
                        stats["pushed"] = push_stats["count"]
                        stats["conflicts"] += push_stats["conflicts"]
                        if "errors" in push_stats and push_stats["errors"]:
                            stats["errors"].extend(push_stats["errors"])
                    except (ConnectionError, TimeoutError, ConnectionRefusedError) as e:
                        error_msg = f