import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .compressor import TokenCompressor
from .enums import MemoryType
from .extractor import SmartAutoOrganizer
from .graph import VaultGraph
from .indexer import VaultIndexer
from .node import MemoryNode
from .retriever import HybridRetriever


class MemoryKernel:
    def __init__(
        self,
        vault_path: str,
        embedding_adapter=None,
        llm_client=None,
        llm_config=None,
        auto_extract: bool = False,
    ):
        """
        Initialize the memory kernel.

        Args:
            vault_path: Path to the vault directory
            embedding_adapter: Optional embedding adapter for semantic search
            llm_client: Optional LLM client for auto-extraction
            llm_config: Optional configuration for the LLM
            auto_extract: Whether to automatically extract entities during ingestion
        """
        self.vault_path = Path(vault_path).expanduser()
        self.vault_path.mkdir(parents=True, exist_ok=True)

        self.graph = VaultGraph()
        self.embedding_adapter = embedding_adapter
        self.indexer = VaultIndexer(self.vault_path, embedding_adapter=embedding_adapter)
        self.retriever = HybridRetriever(self.graph, embedding_adapter=embedding_adapter)

        # Auto-extraction setup
        self.auto_extract = auto_extract
        self.llm_client = llm_client
        self.llm_config = llm_config
        self.organizer = None
        if auto_extract and llm_client:
            self.organizer = SmartAutoOrganizer(llm_client, llm_config)

    @staticmethod
    def _normalize_tags(tags: list[str] | None) -> list[str]:
        if not tags:
            return []
        normalized = []
        for tag in tags:
            clean = tag.strip().lstrip("#")
            if clean:
                normalized.append(clean)
        return normalized

    @staticmethod
    def _slugify(text: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
        return slug or datetime.now(timezone.utc).strftime("memory-%Y%m%d-%H%M%S")

    def ingest(self, force: bool = False, auto_extract: bool | None = None) -> dict[str, int]:
        """
        Ingests all memories from the vault.

        Args:
            force: Force re-indexing even if files haven't changed
            auto_extract: Override the default auto_extract setting for this ingestion

        Returns:
            Dictionary with indexing statistics and extraction counts
        """
        self.graph = VaultGraph()
        indexed, skipped = self.indexer.index(self.graph, force=force)
        self.retriever = HybridRetriever(self.graph, embedding_adapter=self.retriever.embeddings)

        # Perform auto-extraction if enabled
        extract_enabled = auto_extract if auto_extract is not None else self.auto_extract
        entities_extracted = 0

        if extract_enabled and self.organizer:
            entities_extracted = self._extract_entities_from_memories()

        total = len(self.graph._nodes)
        return {
            "indexed": indexed,
            "skipped": skipped,
            "total": total,
            "entities_extracted": entities_extracted,
        }

    def _extract_entities_from_memories(self) -> int:
        """
        Extract entities from all memories in the graph.

        Returns:
            Number of entities extracted
        """
        total_entities = 0
        for memory in self.graph.all_nodes():
            try:
                result = self.organizer.extract(memory)
                self.graph.add_extraction_result(result)
                total_entities += result.entity_count()
                print(f"Extracted {result.entity_count()} entities from {memory.id}")
            except Exception as e:
                print(f"Failed to extract from {memory.id}: {e}")

        return total_entities

    def extract_from_memory(self, memory_id: str) -> dict[str, Any]:
        """
        Manually extract entities from a specific memory.

        Args:
            memory_id: ID of the memory to extract from

        Returns:
            Dictionary with extraction results
        """
        if not self.organizer:
            raise RuntimeError(
                "Auto-extraction not enabled. Initialize kernel with llm_client and auto_extract=True"
            )

        memory = self.graph.get(memory_id)
        if not memory:
            raise ValueError(f"Memory {memory_id} not found")

        result = self.organizer.extract(memory)
        self.graph.add_extraction_result(result)

        return {
            "memory_id": memory_id,
            "entities_extracted": result.entity_count(),
            "topics": len(result.topics),
            "people": len(result.people),
            "action_items": len(result.action_items),
            "decisions": len(result.decisions),
            "questions": len(result.questions),
            "risks": len(result.risks),
        }

    def get_entities(self, memory_id: str | None = None, entity_type=None):
        """
        Get extracted entities, optionally filtered by memory or type.

        Args:
            memory_id: Optional memory ID to filter by
            entity_type: Optional EntityType to filter by

        Returns:
            List of entities
        """
        if memory_id:
            entities = self.graph.get_entities_for_memory(memory_id)
        else:
            entities = self.graph.all_entities()

        if entity_type:
            entities = [e for e in entities if e.entity_type == entity_type]

        return entities

    def remember(
        self,
        title: str,
        content: str,
        memory_type: MemoryType = MemoryType.FACT,
        tags: list[str] = None,
    ):
        """
        Creates a new memory.
        """
        normalized_tags = self._normalize_tags(tags)
        slug = self._slugify(title)
        file_path = self.vault_path / f"{slug}.md"

        counter = 2
        while file_path.exists():
            file_path = self.vault_path / f"{slug}-{counter}.md"
            counter += 1

        created_at = datetime.now(timezone.utc).isoformat()
        tags_line = " ".join(f"#{tag}" for tag in normalized_tags)

        payload = {
            "title": title,
            "memory_type": memory_type.value,
            "created": created_at,
            "salience": 1.0,
        }
        frontmatter = "---\n" + yaml.safe_dump(payload, sort_keys=False).strip() + "\n---\n\n"

        body = content.strip()
        if tags_line:
            body = f"{body}\n\n{tags_line}"

        file_path.write_text(frontmatter + body + "\n", encoding="utf-8")
        return str(file_path)

    def context_window(
        self,
        query: str,
        tags: list[str] = None,
        depth: int = 2,
        top_k: int = 8,
        token_limit: int = 2048,
    ) -> str:
        """
        Retrieves relevant context from the memory vault.
        """
        nodes = self.retrieve_nodes(query=query, tags=tags, depth=depth, top_k=top_k)
        compressor = TokenCompressor(token_limit=token_limit)
        return compressor.compress(nodes)

    def retrieve_nodes(
        self,
        query: str,
        tags: list[str] = None,
        depth: int = 2,
        top_k: int = 8,
    ) -> list[MemoryNode]:
        normalized_tags = self._normalize_tags(tags)

        if not self.graph._nodes:
            self.ingest()

        query_words = [w.lower() for w in re.findall(r"\w+", query) if len(w) > 2]
        seed_ids = []
        for node in self.graph._nodes.values():
            haystack = f"{node.title} {node.content}".lower()
            if any(word in haystack for word in query_words):
                seed_ids.append(node.id)

        return self.retriever.retrieve(
            query=query,
            seed_ids=seed_ids,
            tags=normalized_tags,
            depth=depth,
            top_k=top_k,
        )
