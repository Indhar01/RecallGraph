"""Performance metrics tracking for Obsidian integration."""

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import contextmanager


@dataclass
class OperationMetrics:
    """Metrics for a single operation."""
    
    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    files_processed: int = 0
    bytes_processed: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    errors: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def complete(self) -> None:
        """Mark operation as complete and calculate duration."""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "operation": self.operation_name,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "end_time": datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "files_processed": self.files_processed,
            "bytes_processed": self.bytes_processed,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "errors": self.errors,
            "throughput_files_per_sec": self._calculate_throughput_files() if self.duration_ms else 0,
            "throughput_mb_per_sec": self._calculate_throughput_mb() if self.duration_ms else 0,
            "metadata": self.metadata,
        }
    
    def _calculate_throughput_files(self) -> float:
        """Calculate files processed per second."""
        if not self.duration_ms or self.duration_ms == 0:
            return 0.0
        return (self.files_processed / self.duration_ms) * 1000
    
    def _calculate_throughput_mb(self) -> float:
        """Calculate MB processed per second."""
        if not self.duration_ms or self.duration_ms == 0:
            return 0.0
        mb_processed = self.bytes_processed / (1024 * 1024)
        return (mb_processed / self.duration_ms) * 1000


class PerformanceTracker:
    """Track performance metrics for sync operations."""
    
    def __init__(self):
        """Initialize performance tracker."""
        self.operations: List[OperationMetrics] = []
        self.current_operation: Optional[OperationMetrics] = None
        self._operation_counts: Dict[str, int] = {}
    
    @contextmanager
    def track_operation(self, operation_name: str, **metadata):
        """Context manager to track an operation.
        
        Args:
            operation_name: Name of the operation
            **meta Additional metadata to store
        
        Usage:
            with tracker.track_operation("sync_pull", direction="pull"):
                # Do sync work
                tracker.record_file_processed(1024)
        """
        metrics = OperationMetrics(
            operation_name=operation_name,
            start_time=time.time(),
            metadata=metadata,
        )
        self.current_operation = metrics
        
        try:
            yield metrics
        except Exception as e:
            metrics.errors += 1
            metrics.metadata["error"] = str(e)
            raise
        finally:
            metrics.complete()
            self.operations.append(metrics)
            self.current_operation = None
            self._operation_counts[operation_name] = self._operation_counts.get(operation_name, 0) + 1
    
    def record_file_processed(self, size_bytes: int = 0) -> None:
        """Record that a file was processed.
        
        Args:
            size_bytes: Size of the file in bytes
        """
        if self.current_operation:
            self.current_operation.files_processed += 1
            self.current_operation.bytes_processed += size_bytes
    
    def record_cache_hit(self) -> None:
        """Record a cache hit."""
        if self.current_operation:
            self.current_operation.cache_hits += 1
    
    def record_cache_miss(self) -> None:
        """Record a cache miss."""
        if self.current_operation:
            self.current_operation.cache_misses += 1
    
    def record_error(self) -> None:
        """Record an error."""
        if self.current_operation:
            self.current_operation.errors += 1
    
    def get_recent_operations(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get most recent operations.
        
        Args:
            count: Number of recent operations to return
        
        Returns:
            List of operation metrics as dictionaries
        """
        return [op.to_dict() for op in self.operations[-count:]]
    
    def get_operation_summary(self, operation_name: Optional[str] = None) -> Dict[str, Any]:
        """Get summary statistics for operations.
        
        Args:
            operation_name: Filter by operation name, or None for all
        
        Returns:
            Dictionary with summary statistics
        """
        if operation_name:
            ops = [op for op in self.operations if op.operation_name == operation_name]
        else:
            ops = self.operations
        
        if not ops:
            return {
                "operation_name": operation_name or "all",
                "count": 0,
                "total_files": 0,
                "total_bytes": 0,
                "total_errors": 0,
                "avg_duration_ms": 0,
                "min_duration_ms": 0,
                "max_duration_ms": 0,
            }
        
        durations = [op.duration_ms for op in ops if op.duration_ms]
        
        return {
            "operation_name": operation_name or "all",
            "count": len(ops),
            "total_files": sum(op.files_processed for op in ops),
            "total_bytes": sum(op.bytes_processed for op in ops),
            "total_errors": sum(op.errors for op in ops),
            "total_cache_hits": sum(op.cache_hits for op in ops),
            "total_cache_misses": sum(op.cache_misses for op in ops),
            "cache_hit_rate": self._calculate_cache_hit_rate(ops),
            "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
            "min_duration_ms": min(durations) if durations else 0,
            "max_duration_ms": max(durations) if durations else 0,
            "avg_files_per_operation": sum(op.files_processed for op in ops) / len(ops),
            "avg_throughput_files_per_sec": self._calculate_avg_throughput_files(ops),
            "avg_throughput_mb_per_sec": self._calculate_avg_throughput_mb(ops),
        }
    
    def _calculate_cache_hit_rate(self, operations: List[OperationMetrics]) -> float:
        """Calculate cache hit rate as percentage.
        
        Args:
            operations: List of operations to analyze
        
        Returns:
            Cache hit rate as percentage (0-100)
        """
        total_hits = sum(op.cache_hits for op in operations)
        total_misses = sum(op.cache_misses for op in operations)
        total_accesses = total_hits + total_misses
        
        if total_accesses == 0:
            return 0.0
        
        return (total_hits / total_accesses) * 100
    
    def _calculate_avg_throughput_files(self, operations: List[OperationMetrics]) -> float:
        """Calculate average files per second throughput.
        
        Args:
            operations: List of operations to analyze
        
        Returns:
            Average files per second
        """
        throughputs = [op._calculate_throughput_files() for op in operations if op.duration_ms]
        return sum(throughputs) / len(throughputs) if throughputs else 0.0
    
    def _calculate_avg_throughput_mb(self, operations: List[OperationMetrics]) -> float:
        """Calculate average MB per second throughput.
        
        Args:
            operations: List of operations to analyze
        
        Returns:
            Average MB per second
        """
        throughputs = [op._calculate_throughput_mb() for op in operations if op.duration_ms]
        return sum(throughputs) / len(throughputs) if throughputs else 0.0
    
    def get_all_operation_names(self) -> List[str]:
        """Get list of all operation names tracked.
        
        Returns:
            List of unique operation names
        """
        return list(self._operation_counts.keys())
    
    def clear(self) -> None:
        """Clear all tracked metrics."""
        self.operations.clear()
        self._operation_counts.clear()
        self.current_operation = None
    
    def export_metrics(self) -> Dict[str, Any]:
        """Export all metrics for analysis.
        
        Returns:
            Dictionary with complete metrics data
        """
        return {
            "total_operations": len(self.operations),
            "operation_types": self._operation_counts.copy(),
            "summary": self.get_operation_summary(),
            "operation_summaries": {
                name: self.get_operation_summary(name)
                for name in self.get_all_operation_names()
            },
            "recent_operations": self.get_recent_operations(20),
        }


# Global instance for easy access
_global_tracker: Optional[PerformanceTracker] = None


def get_tracker() -> PerformanceTracker:
    """Get the global performance tracker instance.
    
    Returns:
        Global PerformanceTracker instance
    """
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = PerformanceTracker()
    return _global_tracker


def reset_tracker() -> None:
    """Reset the global performance tracker."""
    global _global_tracker
    _global_tracker = PerformanceTracker()