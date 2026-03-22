"""MCP Server implementation for MemoGraph.

This module provides an MCP (Model Context Protocol) server that exposes
MemoGraph functionality as tools that can be used by any MCP-compatible
AI client (Claude Desktop, Cline, etc.).
"""

import logging
import os
from pathlib import Path
from typing import Any

from ..core.enums import MemoryType
from ..core.kernel import MemoryKernel
from .autonomous_hooks import AutonomousHooks

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MemoGraphMCPServer:
    """MCP server for MemoGraph vault operations.

    Exposes MemoGraph functionality as MCP tools that can be called by
    AI assistants like Claude Desktop, Cline, etc.

    Example:
        >>> server = MemoGraphMCPServer(vault_path="~/my-vault")
        >>> await server.run()
    """

    def __init__(
        self,
        vault_path: str,
        llm_provider: str | None = None,
        llm_model: str | None = None,
    ):
        """Initialize MCP server with MemoGraph kernel.

        Args:
            vault_path: Path to the MemoGraph vault
            llm_provider: LLM provider to use (ollama or claude). Optional - if not
                         provided, query_with_context will return context for the
                         client's LLM to use instead of generating answers.
            llm_model: Specific model name (optional)
        """
        self.vault_path = Path(vault_path).expanduser()
        self.kernel = MemoryKernel(str(self.vault_path))
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        
        # Initialize autonomous hooks (can be enabled/disabled via configuration)
        self.autonomous_hooks = AutonomousHooks(self)
        
        # Check if autonomous mode is enabled via environment variable
        auto_mode = os.environ.get("MEMOGRAPH_AUTONOMOUS_MODE", "false").lower() == "true"
        if auto_mode:
            self.autonomous_hooks.auto_search_enabled = True
            self.autonomous_hooks.auto_save_responses = True
            logger.info("Autonomous mode enabled via MEMOGRAPH_AUTONOMOUS_MODE")

        if llm_provider:
            logger.info(
                f"Initialized MemoGraph MCP server with vault: {self.vault_path}, provider: {llm_provider}"
            )
        else:
            logger.info(
                f"Initialized MemoGraph MCP server with vault: {self.vault_path} (no LLM provider - client will handle answers)"
            )

    def _add_vault_context(self, response: dict[str, Any]) -> dict[str, Any]:
        """Add vault context information to any response.

        This helper ensures that AI assistants always know which vault is being used,
        reducing confusion and unnecessary clarification questions.

        Args:
            response: Original response dictionary

        Returns:
            Response with vault_context added
        """
        response["vault_context"] = {
            "path": str(self.vault_path),
            "name": self.vault_path.name,
        }
        return response

    def get_server_info(self) -> dict[str, Any]:
        """Get server configuration and metadata.

        This provides comprehensive information about the MCP server instance,
        including vault configuration and capabilities.

        Returns:
            Dictionary with server metadata
        """
        return {
            "name": "MemoGraph MCP Server",
            "version": "1.0.0",
            "vault": {
                "path": str(self.vault_path),
                "name": self.vault_path.name,
                "absolute_path": str(self.vault_path.resolve()),
            },
            "llm": {
                "provider": self.llm_provider or "client-managed",
                "model": self.llm_model or "not specified",
            },
            "capabilities": {
                "answer_generation": self.llm_provider is not None,
                "context_retrieval": True,
                "graph_traversal": True,
                "embeddings": False,
            },
        }

    async def get_vault_info(self) -> dict[str, Any]:
        """Get information about the currently configured vault.

        Returns essential information about the vault being used by this
        MCP server instance. Use this when you need to confirm vault location.

        Returns:
            Dictionary with vault configuration details
        """
        try:
            return {
                "success": True,
                "vault": {
                    "path": str(self.vault_path),
                    "name": self.vault_path.name,
                    "exists": self.vault_path.exists(),
                    "absolute_path": str(self.vault_path.resolve()),
                },
                "llm_config": {
                    "provider": self.llm_provider or "none (client-managed)",
                    "model": self.llm_model or "not specified",
                },
                "message": f"Currently using vault: {self.vault_path.name} at {self.vault_path}",
            }
        except Exception as e:
            logger.error(f"Error getting vault info: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def search_vault(
        self,
        query: str,
        tags: list[str] | None = None,
        top_k: int = 8,
        depth: int = 2,
        memory_type: str | None = None,
    ) -> dict[str, Any]:
        """Search memories in the vault.

        Args:
            query: Search query string
            tags: Optional list of tags to filter by
            top_k: Maximum number of results to return
            depth: Graph traversal depth
            memory_type: Optional memory type filter

        Returns:
            Dictionary with search results
        """
        try:
            # Retrieve nodes
            results = self.kernel.retrieve_nodes(
                query=query,
                tags=tags,
                depth=depth,
                top_k=top_k,
            )

            # Filter by memory type if specified
            if memory_type:
                try:
                    mem_type = MemoryType(memory_type)
                    results = [n for n in results if n.memory_type == mem_type]
                except ValueError:
                    pass

            # Format results
            formatted_results = [
                {
                    "id": node.id,
                    "title": node.title,
                    "content": node.content[:500] + "..."
                    if len(node.content) > 500
                    else node.content,
                    "memory_type": node.memory_type.value,
                    "tags": node.tags,
                    "salience": node.salience,
                    "created_at": node.created_at.isoformat() if node.created_at else None,
                }
                for node in results
            ]

            return self._add_vault_context({
                "success": True,
                "count": len(formatted_results),
                "results": formatted_results,
            })

        except Exception as e:
            logger.error(f"Error searching vault: {e}")
            return self._add_vault_context({
                "success": False,
                "error": str(e),
                "results": [],
            })

    async def create_memory(
        self,
        title: str,
        content: str,
        memory_type: str = "semantic",
        tags: list[str] | None = None,
        salience: float = 0.7,
    ) -> dict[str, Any]:
        """Create a new memory in the vault.

        Args:
            title: Memory title
            content: Memory content
            memory_type: Type of memory (episodic, semantic, procedural, fact)
            tags: Optional list of tags
            salience: Importance score (0.0-1.0)

        Returns:
            Dictionary with creation result
        """
        try:
            # Create memory
            path = self.kernel.remember(
                title=title,
                content=content,
                memory_type=MemoryType(memory_type),
                tags=tags or [],
                salience=salience,
            )

            return self._add_vault_context({
                "success": True,
                "message": f"Created memory: {title}",
                "path": path,
                "title": title,
            })

        except Exception as e:
            logger.error(f"Error creating memory: {e}")
            return self._add_vault_context({
                "success": False,
                "error": str(e),
            })

    async def query_with_context(
        self,
        question: str,
        tags: list[str] | None = None,
        top_k: int = 8,
        provider: str | None = None,
        model: str | None = None,
        generate_answer: bool = True,
    ) -> dict[str, Any]:
        """Ask a question with vault context.

        Args:
            question: Question to ask
            tags: Optional tag filter
            top_k: Number of memories to use as context
            provider: LLM provider override
            model: Model name override
            generate_answer: If True and LLM available, generate answer.
                           If False, return context for client to use.

        Returns:
            Dictionary with answer (if LLM available) or context (for client to use)
        """
        try:
            from ..core.assistant import build_answer_prompt, retrieve_cited_context, run_answer

            # Get context from vault (core functionality - no LLM needed)
            context, sources = retrieve_cited_context(
                kernel=self.kernel,
                query=question,
                tags=tags,
                top_k=top_k,
            )

            # Format sources
            formatted_sources = [
                {
                    "id": src.source_id,
                    "title": src.title,
                    "memory_type": src.memory_type,
                    "tags": src.tags,
                }
                for src in sources
            ]

            # Determine effective provider
            effective_provider = provider or self.llm_provider

            # If LLM provider configured and answer generation requested, generate answer
            if effective_provider and generate_answer:
                prompt = build_answer_prompt(context=context, query=question)
                model = model or self.llm_model

                answer = run_answer(
                    provider=effective_provider,
                    prompt=prompt,
                    model=model,
                    stream=False,  # No streaming for MCP
                )

                return self._add_vault_context({
                    "success": True,
                    "answer": answer,
                    "sources": formatted_sources,
                    "question": question,
                    "mode": "generated",
                })

            # Otherwise, return context for client's LLM to use
            else:
                return self._add_vault_context({
                    "success": True,
                    "context": context,
                    "sources": formatted_sources,
                    "question": question,
                    "mode": "context_only",
                    "message": "Use the provided context to answer the question. The context includes relevant memories from the vault with source citations [S1], [S2], etc.",
                })

        except Exception as e:
            logger.error(f"Error querying with context: {e}")
            return self._add_vault_context({
                "success": False,
                "error": str(e),
            })

    async def get_vault_stats(self) -> dict[str, Any]:
        """Get statistics about the vault.

        Returns:
            Dictionary with vault statistics
        """
        try:
            # Ingest to get stats
            stats = self.kernel.ingest(force=False)

            # Get additional info
            all_nodes = self.kernel.graph.all_nodes()

            # Count by type
            type_counts: dict[str, int] = {}
            for node in all_nodes:
                type_name = node.memory_type.value
                type_counts[type_name] = type_counts.get(type_name, 0) + 1

            # Get all tags
            all_tags = set()
            for node in all_nodes:
                all_tags.update(node.tags)

            return self._add_vault_context({
                "success": True,
                "vault_path": str(self.vault_path),
                "total_memories": stats["total"],
                "indexed": stats["indexed"],
                "skipped": stats["skipped"],
                "by_type": type_counts,
                "total_tags": len(all_tags),
                "tags": sorted(all_tags),
            })

        except Exception as e:
            logger.error(f"Error getting vault stats: {e}")
            return self._add_vault_context({
                "success": False,
                "error": str(e),
            })

    async def list_memories(
        self,
        limit: int = 20,
        memory_type: str | None = None,
        tags: list[str] | None = None,
        sort_by: str = "created",
    ) -> dict[str, Any]:
        """List memories with optional filters.

        Args:
            limit: Maximum number of memories to return
            memory_type: Filter by memory type
            tags: Filter by tags
            sort_by: Sort by field (created, salience, title)

        Returns:
            Dictionary with list of memories
        """
        try:
            # Get all nodes
            nodes = self.kernel.graph.all_nodes()

            # Apply filters
            if memory_type:
                try:
                    mem_type = MemoryType(memory_type)
                    nodes = [n for n in nodes if n.memory_type == mem_type]
                except ValueError:
                    pass

            if tags:
                nodes = [n for n in nodes if any(tag in n.tags for tag in tags)]

            # Sort
            if sort_by == "created":
                nodes.sort(key=lambda n: n.created_at or "", reverse=True)
            elif sort_by == "salience":
                nodes.sort(key=lambda n: n.salience, reverse=True)
            elif sort_by == "title":
                nodes.sort(key=lambda n: n.title)

            # Limit
            nodes = nodes[:limit]

            # Format
            formatted = [
                {
                    "id": node.id,
                    "title": node.title,
                    "memory_type": node.memory_type.value,
                    "tags": node.tags,
                    "salience": node.salience,
                    "created_at": node.created_at.isoformat() if node.created_at else None,
                    "preview": node.content[:200] + "..."
                    if len(node.content) > 200
                    else node.content,
                }
                for node in nodes
            ]

            return self._add_vault_context({
                "success": True,
                "count": len(formatted),
                "memories": formatted,
            })

        except Exception as e:
            logger.error(f"Error listing memories: {e}")
            return self._add_vault_context({
                "success": False,
                "error": str(e),
                "memories": [],
            })

    async def get_memory(self, memory_id: str) -> dict[str, Any]:
        """Get full content of a specific memory.

        Args:
            memory_id: ID of the memory to retrieve

        Returns:
            Dictionary with memory details
        """
        try:
            node = self.kernel.graph.get(memory_id)

            if not node:
                return self._add_vault_context({
                    "success": False,
                    "error": f"Memory not found: {memory_id}",
                })

            return self._add_vault_context({
                "success": True,
                "memory": {
                    "id": node.id,
                    "title": node.title,
                    "content": node.content,
                    "memory_type": node.memory_type.value,
                    "tags": node.tags,
                    "links": node.links,
                    "backlinks": node.backlinks,
                    "salience": node.salience,
                    "created_at": node.created_at.isoformat() if node.created_at else None,
                    "modified_at": node.modified_at.isoformat() if node.modified_at else None,
                },
            })

        except Exception as e:
            logger.error(f"Error getting memory: {e}")
            return self._add_vault_context({
                "success": False,
                "error": str(e),
            })

    async def import_document(
        self,
        file_path: str,
        tags: list[str] | None = None,
        memory_type: str = "episodic",
        salience: float = 0.7,
    ) -> dict[str, Any]:
        """Import a document (TXT, PDF, DOCX) into the vault.

        Args:
            file_path: Path to the document to import
            tags: Optional tags to add
            memory_type: Memory type for imported document
            salience: Importance score

        Returns:
            Dictionary with import result
        """
        try:
            from ..importers.documents import DocumentImporter

            importer = DocumentImporter(str(self.vault_path))

            success, message = importer.import_file(
                file_path=file_path,
                memory_type=memory_type,
                salience=salience,
                tags=tags or [],
                overwrite=False,
            )

            return self._add_vault_context({
                "success": success,
                "message": message,
            })

        except Exception as e:
            logger.error(f"Error importing document: {e}")
            return self._add_vault_context({
                "success": False,
                "error": str(e),
            })

    async def delete_memory(self, memory_id: str) -> dict[str, Any]:
        """Delete a memory from the vault.

        Args:
            memory_id: ID of the memory to delete

        Returns:
            Dictionary with deletion result
        """
        try:
            # Find the memory file
            memory_path = None
            for md_file in self.vault_path.rglob("*.md"):
                if md_file.stem == memory_id or md_file.stem.startswith(f"{memory_id}-"):
                    memory_path = md_file
                    break

            if not memory_path or not memory_path.exists():
                return self._add_vault_context({
                    "success": False,
                    "error": f"Memory not found: {memory_id}",
                })

            # Get memory info before deletion
            node = self.kernel.graph.get(memory_id)
            title = node.title if node else memory_id

            # Delete the file
            memory_path.unlink()

            # Remove from graph
            if node:
                self.kernel.graph._nodes.pop(memory_id, None)

            logger.info(f"Deleted memory: {memory_id}")

            return self._add_vault_context({
                "success": True,
                "message": f"Deleted memory: {title}",
                "memory_id": memory_id,
            })

        except Exception as e:
            logger.error(f"Error deleting memory: {e}")
            return self._add_vault_context({
                "success": False,
                "error": str(e),
            })

    async def update_memory(
        self,
        memory_id: str,
        title: str | None = None,
        content: str | None = None,
        tags: list[str] | None = None,
        salience: float | None = None,
        append_content: bool = False,
    ) -> dict[str, Any]:
        """Update an existing memory.

        Args:
            memory_id: ID of the memory to update
            title: New title (optional)
            content: New content (optional)
            tags: New tags - replaces existing (optional)
            salience: New salience score (optional)
            append_content: If True, append content instead of replacing

        Returns:
            Dictionary with update result
        """
        try:
            import re
            from datetime import datetime, timezone

            import yaml

            # Find the memory file
            memory_path = None
            for md_file in self.vault_path.rglob("*.md"):
                if md_file.stem == memory_id or md_file.stem.startswith(f"{memory_id}-"):
                    memory_path = md_file
                    break

            if not memory_path or not memory_path.exists():
                return {
                    "success": False,
                    "error": f"Memory not found: {memory_id}",
                }

            # Read existing content
            file_content = memory_path.read_text(encoding="utf-8")

            # Parse frontmatter
            if file_content.startswith("---\n"):
                parts = file_content.split("---\n", 2)
                if len(parts) >= 3:
                    frontmatter_str = parts[1]
                    body = parts[2].strip()
                    frontmatter = yaml.safe_load(frontmatter_str)
                else:
                    return {"success": False, "error": "Invalid frontmatter format"}
            else:
                return {"success": False, "error": "No frontmatter found"}

            # Update frontmatter
            if title:
                frontmatter["title"] = title
            if salience is not None:
                if not 0.0 <= salience <= 1.0:
                    return {"success": False, "error": "Salience must be between 0.0 and 1.0"}
                frontmatter["salience"] = salience
            frontmatter["modified"] = datetime.now(timezone.utc).isoformat()

            # Update content
            if content:
                # Remove old tags from body first
                body = re.sub(r"\n\n#[\w\s#]+$", "", body).strip()
                body = f"{body}\n\n{content}" if append_content else content

            # Update tags
            if tags:
                # Remove old tag line
                body = re.sub(r"\n\n#[\w\s#]+$", "", body).strip()
                tags_line = " ".join(f"#{tag}" for tag in tags)
                body = f"{body}\n\n{tags_line}"

            # Write back
            new_frontmatter = (
                "---\n" + yaml.safe_dump(frontmatter, sort_keys=False).strip() + "\n---\n\n"
            )
            memory_path.write_text(new_frontmatter + body + "\n", encoding="utf-8")

            logger.info(f"Updated memory: {memory_id}")

            return self._add_vault_context({
                "success": True,
                "message": f"Updated memory: {frontmatter['title']}",
                "memory_id": memory_id,
            })

        except Exception as e:
            logger.error(f"Error updating memory: {e}")
            return self._add_vault_context({
                "success": False,
                "error": str(e),
            })

    async def list_available_tools(self) -> dict[str, Any]:
        """List all available MCP tools with descriptions.

        Returns:
            Dictionary with list of available tools
        """
        try:
            tools_info = []
            for tool in self.get_tools_schema():
                tools_info.append(
                    {
                        "name": tool["name"],
                        "description": tool["description"],
                        "required_params": tool["inputSchema"].get("required", []),
                    }
                )

            return {
                "success": True,
                "total_tools": len(tools_info),
                "tools": tools_info,
                "categories": {
                    "search": ["search_vault", "query_with_context"],
                    "create": ["create_memory", "import_document"],
                    "read": ["get_memory", "list_memories"],
                    "update": ["update_memory"],
                    "delete": ["delete_memory"],
                    "analytics": ["get_vault_info", "get_vault_stats"],
                    "discovery": ["list_available_tools"],
                    "autonomous": ["auto_hook_query", "auto_hook_response", "configure_autonomous_mode", "get_autonomous_config"],
                },
            }
        except Exception as e:
            logger.error(f"Error listing tools: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    # ==================== Autonomous Hooks Methods ====================

    async def auto_hook_query(
        self,
        user_query: str,
        conversation_id: str | None = None,
        auto_search: bool | None = None,
        auto_save_query: bool | None = None,
    ) -> dict[str, Any]:
        """Autonomous hook for every user query.
        
        Automatically searches vault and optionally saves the query.
        
        Args:
            user_query: The user's query/question
            conversation_id: Optional conversation ID for tracking
            auto_search: Override auto_search setting
            auto_save_query: Override auto_save_queries setting
        
        Returns:
            Dictionary with context, sources, and actions performed
        """
        return await self.autonomous_hooks.auto_hook_query(
            user_query=user_query,
            conversation_id=conversation_id,
            auto_search=auto_search,
            auto_save_query=auto_save_query,
        )

    async def auto_hook_response(
        self,
        user_query: str,
        ai_response: str,
        sources_used: list[dict[str, Any]] | None = None,
        conversation_id: str | None = None,
        auto_save: bool | None = None,
    ) -> dict[str, Any]:
        """Autonomous hook after AI responds.
        
        Saves the complete interaction as a memory.
        
        Args:
            user_query: Original user query
            ai_response: AI's response
            sources_used: List of source memories that were used
            conversation_id: Optional conversation ID
            auto_save: Override auto_save_responses setting
        
        Returns:
            Dictionary with save result
        """
        return await self.autonomous_hooks.auto_hook_response(
            user_query=user_query,
            ai_response=ai_response,
            sources_used=sources_used,
            conversation_id=conversation_id,
            auto_save=auto_save,
        )

    async def configure_autonomous_mode(
        self,
        auto_search: bool | None = None,
        auto_save_queries: bool | None = None,
        auto_save_responses: bool | None = None,
        min_query_length: int | None = None,
    ) -> dict[str, Any]:
        """Configure autonomous hooks settings.
        
        Args:
            auto_search: Enable/disable auto-search
            auto_save_queries: Enable/disable saving queries
            auto_save_responses: Enable/disable saving responses
            min_query_length: Minimum query length to process
        
        Returns:
            Dictionary with updated configuration
        """
        return await self.autonomous_hooks.configure(
            auto_search=auto_search,
            auto_save_queries=auto_save_queries,
            auto_save_responses=auto_save_responses,
            min_query_length=min_query_length,
        )

    async def get_autonomous_config(self) -> dict[str, Any]:
        """Get current autonomous hooks configuration.
        
        Returns:
            Dictionary with current settings and recommendations
        """
        return self.autonomous_hooks.get_configuration()

    def get_tools_schema(self) -> list[dict[str, Any]]:
        """Get MCP tools schema for registration.

        Returns:
            List of tool schemas
        """
        return [
            {
                "name": "search_vault",
                "description": "Search memories in the MemoGraph vault using semantic or keyword search",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query string",
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional tags to filter by",
                        },
                        "top_k": {
                            "type": "number",
                            "description": "Maximum number of results (default: 8)",
                            "default": 8,
                        },
                        "memory_type": {
                            "type": "string",
                            "enum": ["episodic", "semantic", "procedural", "fact"],
                            "description": "Optional memory type filter",
                        },
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "create_memory",
                "description": "Create a new memory in the MemoGraph vault",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Memory title",
                        },
                        "content": {
                            "type": "string",
                            "description": "Memory content",
                        },
                        "memory_type": {
                            "type": "string",
                            "enum": ["episodic", "semantic", "procedural", "fact"],
                            "description": "Type of memory",
                            "default": "semantic",
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional tags",
                        },
                        "salience": {
                            "type": "number",
                            "description": "Importance score 0.0-1.0",
                            "default": 0.7,
                        },
                    },
                    "required": ["title", "content"],
                },
            },
            {
                "name": "query_with_context",
                "description": "Retrieve relevant context from the vault for a question. If LLM provider is configured, can optionally generate an answer. Otherwise, returns context for the client's LLM to use.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "Question to ask",
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional tag filter",
                        },
                        "top_k": {
                            "type": "number",
                            "description": "Number of memories to use as context",
                            "default": 8,
                        },
                        "generate_answer": {
                            "type": "boolean",
                            "description": "If true and LLM configured, generate answer. If false, return context only.",
                            "default": True,
                        },
                    },
                    "required": ["question"],
                },
            },
            {
                "name": "get_vault_info",
                "description": "Get information about the currently configured MemoGraph vault (path, name, configuration). Use this when you need to know which vault is being used.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "get_vault_stats",
                "description": "Get statistics about the currently configured MemoGraph vault (memory counts, types, tags)",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "list_memories",
                "description": "List memories with optional filters",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "number",
                            "description": "Maximum number to return",
                            "default": 20,
                        },
                        "memory_type": {
                            "type": "string",
                            "enum": ["episodic", "semantic", "procedural", "fact"],
                            "description": "Filter by type",
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by tags",
                        },
                        "sort_by": {
                            "type": "string",
                            "enum": ["created", "salience", "title"],
                            "description": "Sort by field",
                            "default": "created",
                        },
                    },
                },
            },
            {
                "name": "get_memory",
                "description": "Get full content of a specific memory by ID",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "memory_id": {
                            "type": "string",
                            "description": "Memory ID",
                        },
                    },
                    "required": ["memory_id"],
                },
            },
            {
                "name": "import_document",
                "description": "Import a document (TXT, PDF, DOCX) into the vault",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to document",
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional tags",
                        },
                        "memory_type": {
                            "type": "string",
                            "enum": ["episodic", "semantic", "procedural", "fact"],
                            "default": "episodic",
                        },
                        "salience": {
                            "type": "number",
                            "default": 0.7,
                        },
                    },
                    "required": ["file_path"],
                },
            },
            {
                "name": "delete_memory",
                "description": "Delete a memory from the vault by ID",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "memory_id": {
                            "type": "string",
                            "description": "Memory ID to delete",
                        },
                    },
                    "required": ["memory_id"],
                },
            },
            {
                "name": "update_memory",
                "description": "Update an existing memory's title, content, tags, or salience",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "memory_id": {
                            "type": "string",
                            "description": "Memory ID to update",
                        },
                        "title": {
                            "type": "string",
                            "description": "New title (optional)",
                        },
                        "content": {
                            "type": "string",
                            "description": "New content (optional)",
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "New tags - replaces existing (optional)",
                        },
                        "salience": {
                            "type": "number",
                            "description": "New salience score (0.0-1.0)",
                            "minimum": 0.0,
                            "maximum": 1.0,
                        },
                        "append_content": {
                            "type": "boolean",
                            "description": "If true, append content instead of replacing",
                            "default": False,
                        },
                    },
                    "required": ["memory_id"],
                },
            },
            {
                "name": "list_available_tools",
                "description": "List all available MCP tools with their descriptions and categories",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "auto_hook_query",
                "description": "Autonomous hook for user queries - automatically searches vault and provides context. Call this at the START of every user interaction to get relevant context automatically.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_query": {
                            "type": "string",
                            "description": "The user's query/question",
                        },
                        "conversation_id": {
                            "type": "string",
                            "description": "Optional conversation ID for tracking (optional)",
                        },
                        "auto_search": {
                            "type": "boolean",
                            "description": "Override auto_search setting (optional)",
                        },
                        "auto_save_query": {
                            "type": "boolean",
                            "description": "Override auto_save_queries setting (optional)",
                        },
                    },
                    "required": ["user_query"],
                },
            },
            {
                "name": "auto_hook_response",
                "description": "Autonomous hook for AI responses - saves the complete interaction. Call this at the END of every user interaction to save the conversation automatically.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_query": {
                            "type": "string",
                            "description": "Original user query",
                        },
                        "ai_response": {
                            "type": "string",
                            "description": "AI's response to the query",
                        },
                        "sources_used": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "title": {"type": "string"},
                                },
                            },
                            "description": "List of source memories that were used (optional)",
                        },
                        "conversation_id": {
                            "type": "string",
                            "description": "Optional conversation ID (optional)",
                        },
                        "auto_save": {
                            "type": "boolean",
                            "description": "Override auto_save_responses setting (optional)",
                        },
                    },
                    "required": ["user_query", "ai_response"],
                },
            },
            {
                "name": "configure_autonomous_mode",
                "description": "Configure autonomous hooks behavior (enable/disable auto-search, auto-save, etc.)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "auto_search": {
                            "type": "boolean",
                            "description": "Enable/disable automatic vault search on every query",
                        },
                        "auto_save_queries": {
                            "type": "boolean",
                            "description": "Enable/disable saving every query (usually disabled to avoid noise)",
                        },
                        "auto_save_responses": {
                            "type": "boolean",
                            "description": "Enable/disable saving complete interactions (recommended: enabled)",
                        },
                        "min_query_length": {
                            "type": "number",
                            "description": "Minimum query length to process (default: 10)",
                        },
                    },
                },
            },
            {
                "name": "get_autonomous_config",
                "description": "Get current autonomous hooks configuration and recommendations",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
        ]
