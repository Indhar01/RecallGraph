"""Pydantic schemas for MemoGraph REST API.

These schemas define the request and response shapes
for all REST API endpoints.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ==================== Request Schemas ====================


class SaveMemoryRequest(BaseModel):
    """Request schema for saving a new memory."""

    title: str = Field(..., description="Memory title", min_length=1)
    content: str = Field(..., description="Memory content", min_length=1)
    memory_type: str = Field(
        default="semantic",
        description="Memory type: episodic, semantic, procedural, fact",
    )
    tags: list[str] = Field(default_factory=list, description="List of tags")
    salience: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Importance score between 0.0 and 1.0",
    )
    meta: dict[str, Any] | None = Field(
        default=None, description="Optional arbitrary metadata"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Python Tips",
                "content": "Always use list comprehensions when possible.",
                "memory_type": "semantic",
                "tags": ["python", "programming"],
                "salience": 0.8,
            }
        }
    }


class UpdateMemoryRequest(BaseModel):
    """Request schema for updating an existing memory."""

    title: str | None = Field(default=None, description="New title (optional)")
    content: str | None = Field(default=None, description="New content (optional)")
    tags: list[str] | None = Field(
        default=None, description="New tags - replaces existing (optional)"
    )
    salience: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="New salience score (optional)",
    )
    append_content: bool = Field(
        default=False,
        description="If true, append content instead of replacing",
    )


class SearchRequest(BaseModel):
    """Request schema for searching memories."""

    query: str = Field(..., description="Search query string", min_length=1)
    tags: list[str] | None = Field(default=None, description="Filter by tags")
    memory_type: str | None = Field(default=None, description="Filter by memory type")
    top_k: int = Field(default=8, ge=1, le=100, description="Maximum results to return")
    depth: int = Field(default=2, ge=0, le=5, description="Graph traversal depth")

    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "python best practices",
                "tags": ["programming"],
                "top_k": 5,
            }
        }
    }


class ContextRequest(BaseModel):
    """Request schema for building context window."""

    query: str = Field(..., description="Query to build context for", min_length=1)
    tags: list[str] | None = Field(default=None, description="Filter by tags")
    top_k: int = Field(default=8, ge=1, le=50, description="Number of memories to use")
    depth: int = Field(default=2, ge=0, le=5, description="Graph traversal depth")
    token_limit: int = Field(
        default=2048,
        ge=100,
        le=32000,
        description="Maximum tokens in context",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "machine learning basics",
                "top_k": 5,
                "token_limit": 1024,
            }
        }
    }


class BulkCreateRequest(BaseModel):
    """Request schema for bulk creating memories."""

    memories: list[SaveMemoryRequest] = Field(
        ..., description="List of memories to create", min_length=1
    )
    continue_on_error: bool = Field(
        default=True,
        description="Continue even if some memories fail to create",
    )


# ==================== Response Schemas ====================


class MemoryResponse(BaseModel):
    """Response schema for a single memory."""

    id: str
    title: str
    content: str
    memory_type: str
    tags: list[str]
    salience: float
    created_at: str | None = None
    modified_at: str | None = None
    links: list[str] = Field(default_factory=list)
    backlinks: list[str] = Field(default_factory=list)


class MemoryPreviewResponse(BaseModel):
    """Response schema for memory preview (truncated content)."""

    id: str
    title: str
    preview: str
    memory_type: str
    tags: list