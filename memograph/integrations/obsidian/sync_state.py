"""Sync state management for Obsidian integration."""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List, Any


class SyncState:
    """Track sync state between Obsidian and MemoGraph.

    Uses SQLite for efficient indexing and querying of file metadata.
    Falls back to JSON for backwards compatibility.
    """

    def __init__(self, state_file: Path, use_sqlite: bool = True):
        """Initialize sync state manager.

        Args:
            state_file: Path to the state file (JSON or SQLite database)
            use_sqlite: Whether to use SQLite (True) or JSON (False)
        """
        self.state_file = Path(state_file)
        self.use_sqlite = use_sqlite

        if use_sqlite:
            # Use SQLite database
            self.db_path = self.state_file.with_suffix(".db")
            self._init_sqlite_db()
            self.state = None  # Not used with SQLite
        else:
            # Use JSON file (legacy)
            self.db_path = None
            self.state = self.load_state()

    def _init_sqlite_db(self) -> None:
        """Initialize SQLite database schema."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Create tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_hashes (
                file_path TEXT PRIMARY KEY,
                hash TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                size INTEGER,
                modified REAL
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_file_timestamp
            ON file_hashes(timestamp)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_file_modified
            ON file_hashes(modified)
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conflicts (
                file_path TEXT NOT NULL,
                reason TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_conflict_timestamp
            ON conflicts(timestamp)
        """)

        conn.commit()
        conn.close()

    def _get_connection(self) -> sqlite3.Connection:
        """Get SQLite connection."""
        if not self.use_sqlite:
            raise RuntimeError("SQLite not enabled")
        return sqlite3.connect(str(self.db_path))

    def load_state(self) -> Dict[str, Any]:
        """Load sync state from file.

        Returns:
            Dictionary containing sync state with:
            - last_sync: ISO timestamp of last successful sync
            - file_hashes: Dict mapping file paths to hash metadata
            - conflicts: List of unresolved conflicts
        """
        if self.use_sqlite:
            # Not used for SQLite mode
            return self._default_state()

        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                # Return default state if file is corrupted
                print(f"Warning: Failed to load sync state: {e}. Using default state.")
                return self._default_state()
        return self._default_state()

    def _default_state(self) -> Dict[str, Any]:
        """Get default empty sync state.

        Returns:
            Default state dictionary
        """
        return {"last_sync": None, "file_hashes": {}, "conflicts": []}

    def save_state(self) -> None:
        """Save sync state to file.

        Creates parent directories if they don't exist.
        """
        if self.use_sqlite:
            # SQLite writes are immediate, no need to save
            return

        # Ensure parent directory exists
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        # Write state to file
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2, default=str)

    def update_file_hash(
        self, file_path: str, hash_value: str, size: int = 0, modified: float = 0.0
    ) -> None:
        """Update hash for a file.

        Args:
            file_path: Path to the file (relative or absolute)
            hash_value: MD5 or other hash of file content
            size: File size in bytes
            modified: File modification timestamp
        """
        if self.use_sqlite:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO file_hashes
                (file_path, hash, timestamp, size, modified)
                VALUES (?, ?, ?, ?, ?)
            """,
                (file_path, hash_value, datetime.now().isoformat(), size, modified),
            )
            conn.commit()
            conn.close()
        else:
            self.state["file_hashes"][file_path] = {
                "hash": hash_value,
                "timestamp": datetime.now().isoformat(),
                "size": size,
                "modified": modified,
            }
            self.save_state()

    def get_file_hash(self, file_path: str) -> Optional[str]:
        """Get stored hash for a file.

        Args:
            file_path: Path to the file

        Returns:
            Hash value if file is tracked, None otherwise
        """
        if self.use_sqlite:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT hash FROM file_hashes WHERE file_path = ?", (file_path,)
            )
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None
        else:
            file_data = self.state["file_hashes"].get(file_path, {})
            return file_data.get("hash")

    def get_file_timestamp(self, file_path: str) -> Optional[str]:
        """Get timestamp when file was last synced.

        Args:
            file_path: Path to the file

        Returns:
            ISO timestamp string if file is tracked, None otherwise
        """
        if self.use_sqlite:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT timestamp FROM file_hashes WHERE file_path = ?", (file_path,)
            )
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None
        else:
            file_data = self.state["file_hashes"].get(file_path, {})
            return file_data.get("timestamp")

    def mark_synced(self) -> None:
        """Mark successful sync operation.

        Updates the last_sync timestamp to current time.
        """
        timestamp = datetime.now().isoformat()
        if self.use_sqlite:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO sync_metadata (key, value)
                VALUES ('last_sync', ?)
            """,
                (timestamp,),
            )
            conn.commit()
            conn.close()
        else:
            self.state["last_sync"] = timestamp
            self.save_state()

    def get_last_sync(self) -> Optional[datetime]:
        """Get timestamp of last successful sync.

        Returns:
            Datetime object of last sync, None if never synced
        """
        if self.use_sqlite:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM sync_metadata WHERE key = 'last_sync'")
            result = cursor.fetchone()
            conn.close()
            if result:
                return datetime.fromisoformat(result[0])
            return None
        else:
            if self.state["last_sync"]:
                return datetime.fromisoformat(self.state["last_sync"])
            return None

    def add_conflict(self, file_path: str, reason: str) -> None:
        """Add a conflict to the conflict list.

        Args:
            file_path: Path to the conflicting file
            reason: Description of the conflict
        """
        timestamp = datetime.now().isoformat()
        if self.use_sqlite:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO conflicts (file_path, reason, timestamp)
                VALUES (?, ?, ?)
            """,
                (file_path, reason, timestamp),
            )
            conn.commit()
            conn.close()
        else:
            conflict = {
                "file_path": file_path,
                "reason": reason,
                "timestamp": timestamp,
            }
            self.state["conflicts"].append(conflict)
            self.save_state()

    def get_conflicts(self) -> List[Dict[str, Any]]:
        """Get list of unresolved conflicts.

        Returns:
            List of conflict dictionaries
        """
        if self.use_sqlite:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT file_path, reason, timestamp FROM conflicts ORDER BY timestamp DESC"
            )
            results = cursor.fetchall()
            conn.close()
            return [
                {"file_path": row[0], "reason": row[1], "timestamp": row[2]}
                for row in results
            ]
        else:
            return self.state["conflicts"].copy()

    def resolve_conflict(self, file_path: str) -> bool:
        """Remove a conflict from the list.

        Args:
            file_path: Path to the file whose conflict is resolved

        Returns:
            True if conflict was found and removed, False otherwise
        """
        if self.use_sqlite:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM conflicts WHERE file_path = ?", (file_path,))
            affected = cursor.rowcount
            conn.commit()
            conn.close()
            return affected > 0
        else:
            original_length = len(self.state["conflicts"])
            self.state["conflicts"] = [
                c for c in self.state["conflicts"] if c["file_path"] != file_path
            ]

            if len(self.state["conflicts"]) < original_length:
                self.save_state()
                return True
            return False

    def clear_conflicts(self) -> int:
        """Clear all conflicts.

        Returns:
            Number of conflicts cleared
        """
        if self.use_sqlite:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM conflicts")
            count = cursor.fetchone()[0]
            cursor.execute("DELETE FROM conflicts")
            conn.commit()
            conn.close()
            return count
        else:
            count = len(self.state["conflicts"])
            self.state["conflicts"] = []
            if count > 0:
                self.save_state()
            return count

    def remove_file(self, file_path: str) -> bool:
        """Remove a file from tracking.

        Args:
            file_path: Path to the file to untrack

        Returns:
            True if file was tracked and removed, False otherwise
        """
        if self.use_sqlite:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM file_hashes WHERE file_path = ?", (file_path,))
            affected = cursor.rowcount
            conn.commit()
            conn.close()
            return affected > 0
        else:
            if file_path in self.state["file_hashes"]:
                del self.state["file_hashes"][file_path]
                self.save_state()
                return True
            return False

    def get_tracked_files(self) -> List[str]:
        """Get list of all tracked file paths.

        Returns:
            List of file path strings
        """
        if self.use_sqlite:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT file_path FROM file_hashes")
            results = cursor.fetchall()
            conn.close()
            return [row[0] for row in results]
        else:
            return list(self.state["file_hashes"].keys())

    def has_file_changed(self, file_path: str, current_hash: str) -> bool:
        """Check if a file has changed since last sync.

        Args:
            file_path: Path to the file
            current_hash: Current hash of file content

        Returns:
            True if file has changed or is not tracked, False otherwise
        """
        stored_hash = self.get_file_hash(file_path)
        if stored_hash is None:
            return True  # File is not tracked, so consider it changed
        return stored_hash != current_hash

    def reset_state(self) -> None:
        """Reset state to default empty state.

        Useful for testing or recovering from errors.
        """
        if self.use_sqlite:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM file_hashes")
            cursor.execute("DELETE FROM conflicts")
            cursor.execute("DELETE FROM sync_metadata")
            conn.commit()
            conn.close()
        else:
            self.state = self._default_state()
            self.save_state()

    def get_files_by_modified_range(self, start: float, end: float) -> List[str]:
        """Get files modified within a time range (SQLite only).

        Args:
            start: Start timestamp
            end: End timestamp

        Returns:
            List of file paths
        """
        if not self.use_sqlite:
            raise NotImplementedError("Only available with SQLite")

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT file_path FROM file_hashes
            WHERE modified >= ? AND modified <= ?
            ORDER BY modified DESC
        """,
            (start, end),
        )
        results = cursor.fetchall()
        conn.close()
        return [row[0] for row in results]

    def get_statistics(self) -> Dict[str, Any]:
        """Get sync state statistics (SQLite only).

        Returns:
            Dictionary with statistics
        """
        if not self.use_sqlite:
            return {
                "tracked_files": len(self.state["file_hashes"]),
                "conflicts": len(self.state["conflicts"]),
                "last_sync": self.state["last_sync"],
            }

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM file_hashes")
        tracked_files = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM conflicts")
        conflicts = cursor.fetchone()[0]

        cursor.execute("SELECT value FROM sync_metadata WHERE key = 'last_sync'")
        result = cursor.fetchone()
        last_sync = result[0] if result else None

        cursor.execute("SELECT SUM(size) FROM file_hashes")
        total_size_result = cursor.fetchone()
        total_size = (
            total_size_result[0] if total_size_result and total_size_result[0] else 0
        )

        conn.close()

        return {
            "tracked_files": tracked_files,
            "conflicts": conflicts,
            "last_sync": last_sync,
            "total_size_bytes": total_size,
        }

    def create_checkpoint(self) -> Dict[str, Any]:
        """Create a checkpoint of the current state for rollback.

        Returns:
            Dictionary containing the current state snapshot
        """
        if self.use_sqlite:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Get all file hashes
            cursor.execute(
                "SELECT file_path, hash, timestamp, size, modified FROM file_hashes"
            )
            file_hashes = cursor.fetchall()

            # Get all conflicts
            cursor.execute("SELECT file_path, reason, timestamp FROM conflicts")
            conflicts = cursor.fetchall()

            # Get metadata
            cursor.execute("SELECT key, value FROM sync_metadata")
            metadata = cursor.fetchall()

            conn.close()

            return {
                "file_hashes": file_hashes,
                "conflicts": conflicts,
                "metadata": metadata,
                "checkpoint_time": datetime.now().isoformat(),
            }
        else:
            # For JSON mode, return a deep copy
            import copy

            return {
                "state": copy.deepcopy(self.state),
                "checkpoint_time": datetime.now().isoformat(),
            }

    def restore_checkpoint(self, checkpoint: Dict[str, Any]) -> None:
        """Restore state from a checkpoint.

        Args:
            checkpoint: Checkpoint dictionary created by create_checkpoint()
        """
        if self.use_sqlite:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Clear existing data
            cursor.execute("DELETE FROM file_hashes")
            cursor.execute("DELETE FROM conflicts")
            cursor.execute("DELETE FROM sync_metadata")

            # Restore file hashes
            for row in checkpoint["file_hashes"]:
                cursor.execute(
                    """
                    INSERT INTO file_hashes (file_path, hash, timestamp, size, modified)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    row,
                )

            # Restore conflicts
            for row in checkpoint["conflicts"]:
                cursor.execute(
                    """
                    INSERT INTO conflicts (file_path, reason, timestamp)
                    VALUES (?, ?, ?)
                """,
                    row,
                )

            # Restore metadata
            for row in checkpoint["metadata"]:
                cursor.execute(
                    """
                    INSERT INTO sync_metadata (key, value)
                    VALUES (?, ?)
                """,
                    row,
                )

            conn.commit()
            conn.close()
        else:
            # For JSON mode, restore state and save
            self.state = checkpoint["state"]
            self.save_state()
