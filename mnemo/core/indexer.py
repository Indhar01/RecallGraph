# core/indexer.py
import json
from pathlib import Path
from .parser import parse_file
from .graph import VaultGraph

CACHE_FILE = ".mnemo_cache.json"

class VaultIndexer:
    def __init__(self, vault_root: Path):
        self.root = vault_root
        self.cache_path = vault_root / CACHE_FILE
        self._mtime_cache: dict[str, float] = self._load_cache()

    def _load_cache(self) -> dict[str, float]:
        if self.cache_path.exists():
            try:
                return json.loads(self.cache_path.read_text())
            except json.JSONDecodeError:
                return {}
        return {}

    def _save_cache(self, mtimes: dict[str, float]):
        self.cache_path.write_text(json.dumps(mtimes))
        self._mtime_cache = mtimes

    def index(self, graph: VaultGraph, force=False) -> tuple[int, int]:
        """Returns (indexed, skipped) counts."""
        new_mtimes = {}
        indexed = skipped = 0

        if not self.root.exists():
            self.root.mkdir(parents=True, exist_ok=True)

        for md_file in self.root.rglob("*.md"):
            if md_file.name == CACHE_FILE:
                continue
            rel = md_file.relative_to(self.root).as_posix()
            mtime = md_file.stat().st_mtime
            new_mtimes[rel] = mtime

            unchanged = (not force and self._mtime_cache.get(rel) == mtime)
            if unchanged:
                skipped += 1
            node = parse_file(md_file, self.root)
            graph.add_node(node)
            if not unchanged:
                indexed += 1

        graph.build_backlinks()
        self._save_cache(new_mtimes)
        return indexed, skipped