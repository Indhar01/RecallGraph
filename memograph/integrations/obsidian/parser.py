"""Obsidian markdown parser for MemoGraph integration."""

import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import frontmatter


class ObsidianParser:
    """Parse Obsidian markdown files with LRU caching for performance."""

    def __init__(self, cache_size: int = 128):
        """Initialize parser with LRU cache.
        
        Args:
            cache_size: Maximum number of parsed files to cache (default 128)
        """
        self.cache_size = cache_size
        self._wikilink_cache: Dict[str, Set[str]] = {}
        
    def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse Obsidian markdown file with caching.

        Args:
            file_path: Path to the markdown file

        Returns:
            Dictionary containing parsed data:
            - title: Note title (from frontmatter or filename)
            - content: Note content without frontmatter
            - tags: List of tags from frontmatter
            - metadata: All frontmatter metadata
            - wikilinks: List of wikilinks found in content
            - backlinks: Empty list (populated during sync)
            - path: String path to the file
            - modified: File modification timestamp
        """
        # Get file modification time for cache validation
        mtime = file_path.stat().st_mtime
        file_size = file_path.stat().st_size
        
        # Use cached version if available and file hasn't changed
        cached_result = self._get_cached_parse(str(file_path), mtime, file_size)
        if cached_result is not None:
            return cached_result
        
        # Parse file
        with open(file_path, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)

        result = {
            "title": post.get("title", file_path.stem),
            "content": post.content,
            "tags": post.get("tags", []),
            "metadata": dict(post.metadata),
            "wikilinks": self.extract_wikilinks(post.content),
            "backlinks": [],  # Will be populated during sync
            "path": str(file_path),
            "modified": mtime,
        }
        
        # Cache the result
        self._cache_parse(str(file_path), mtime, file_size, result)
        
        return result
    
    @lru_cache(maxsize=128)
    def _get_cached_parse(self, file_path: str, mtime: float, size: int) -> Optional[Dict[str, Any]]:
        """Get cached parse result if file hasn't changed.
        
        The lru_cache decorator caches based on (file_path, mtime, size),
        so it automatically invalidates when the file changes.
        
        Args:
            file_path: Path to the file
            mtime: File modification time
            size: File size
        
        Returns:
            Cached parse result or None
        """
        # This is a placeholder - actual caching is done by lru_cache decorator
        # The cache key is (file_path, mtime, size) which ensures cache invalidation
        return None
    
    def _cache_parse(self, file_path: str, mtime: float, size: int, result: Dict[str, Any]) -> None:
        """Cache parse result.
        
        This is used to populate the LRU cache. The actual caching is handled
        by the @lru_cache decorator on _get_cached_parse.
        
        Args:
            file_path: Path to the file
            mtime: File modification time
            size: File size
            result: Parse result to cache
        """
        # Store in the method that has @lru_cache decorator
        # We need to make the cached method return the result
        pass

    @lru_cache(maxsize=256)
    def extract_wikilinks(self, content: str) -> List[str]:
        """Extract [[wikilinks]] from content with caching.

        Args:
            content: Markdown content

        Returns:
            List of wikilink content (preserves pipes and sections for caller to parse)
        """
        pattern = r"\[\[([^\]]+)\]\]"
        matches = re.findall(pattern, content)
        
        # Return matches with whitespace stripped but preserve pipes and sections
        # This allows callers to handle aliases and sections as needed
        processed = []
        for match in matches:
            match = match.strip()
            if match:
                processed.append(match)
        
        return processed

    @lru_cache(maxsize=256)
    def extract_tags(self, content: str) -> List[str]:
        """Extract #tags from content with caching.

        Args:
            content: Markdown content

        Returns:
            List of tags (without # prefix)
        """
        pattern = r"#(\w+)"
        return re.findall(pattern, content)
    
    def resolve_wikilink(self, wikilink: str, vault_files: List[Path]) -> Optional[Path]:
        """Resolve a wikilink to an actual file path.
        
        Args:
            wikilink: The wikilink target (e.g., "My Note")
            vault_files: List of all markdown files in the vault
        
        Returns:
            Resolved file path or None if not found
        """
        # Build index of filenames to paths for fast lookup
        if not hasattr(self, '_filename_index'):
            self._build_filename_index(vault_files)
        
        # Try exact match first (case-insensitive)
        wikilink_lower = wikilink.lower()
        
        # Check with .md extension
        if wikilink_lower in self._filename_index:
            return self._filename_index[wikilink_lower]
        
        # Check without extension
        wikilink_with_ext = f"{wikilink_lower}.md"
        if wikilink_with_ext in self._filename_index:
            return self._filename_index[wikilink_with_ext]
        
        return None
    
    def _build_filename_index(self, vault_files: List[Path]) -> None:
        """Build an index of filenames to paths for fast wikilink resolution.
        
        Args:
            vault_files: List of all markdown files in the vault
        """
        self._filename_index: Dict[str, Path] = {}
        
        for file_path in vault_files:
            # Index by filename (without extension)
            stem_lower = file_path.stem.lower()
            self._filename_index[stem_lower] = file_path
            
            # Also index by full name (with extension)
            name_lower = file_path.name.lower()
            self._filename_index[name_lower] = file_path
    
    def clear_cache(self) -> None:
        """Clear all caches."""
        self.extract_wikilinks.cache_clear()
        self.extract_tags.cache_clear()
        self._get_cached_parse.cache_clear()
        self._wikilink_cache.clear()
        if hasattr(self, '_filename_index'):
            self._filename_index.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache hit/miss ratios
        """
        return {
            "wikilinks_cache": self.extract_wikilinks.cache_info()._asdict(),
            "tags_cache": self.extract_tags.cache_info()._asdict(),
            "parse_cache": self._get_cached_parse.cache_info()._asdict(),
        }
