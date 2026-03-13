# MemoGraph Testing & Real-World Validation Strategy

**Date**: 2026-03-08
**Purpose**: Comprehensive guide to test and validate MemoGraph in real-world use cases

---

## 📋 Table of Contents

1. [Current State Analysis](#current-state-analysis)
2. [Testing Strategy Overview](#testing-strategy-overview)
3. [Real-World Validation Scenarios](#real-world-validation-scenarios)
4. [Unit Testing](#unit-testing)
5. [Integration Testing](#integration-testing)
6. [End-to-End Testing](#end-to-end-testing)
7. [Performance Testing](#performance-testing)
8. [Manual Validation Workflows](#manual-validation-workflows)
9. [Production Readiness Checklist](#production-readiness-checklist)
10. [Continuous Integration Setup](#continuous-integration-setup)

---

## Current State Analysis

### ✅ What Exists

**Test Files**:
- [`tests/conftest.py`](tests/conftest.py:1) - Pytest fixtures and configuration
- [`tests/test_kernel.py`](tests/test_kernel.py:1) - Core kernel functionality tests
- [`tests/test_embeddings.py`](tests/test_embeddings.py:1) - Embedding adapter tests
- [`tests/test_parser.py`](tests/test_parser.py:1) - Markdown parsing tests
- [`tests/test_indexer.py`](tests/test_indexer.py:1) - File indexing tests
- [`tests/test_extractor.py`](tests/test_extractor.py:1) - Entity extraction tests
- [`tests/test_assistant.py`](tests/test_assistant.py:1) - Assistant integration tests

**Test Coverage**:
- ✅ Basic unit tests for core components
- ✅ Mock embedding adapter for testing
- ✅ Fixtures for temp vaults and test data
- ✅ Some integration tests

### ❌ What's Missing for Real-World Validation

1. **No End-to-End Tests** with actual LLM providers (OpenAI, Claude, Ollama)
2. **No Real-World Scenarios** (chatbot conversations, RAG systems)
3. **No Performance Benchmarks** (load testing, stress testing)
4. **No Concurrent Usage Tests** (async operations, race conditions)
5. **No Production Testing Guides** (deployment validation, monitoring)
6. **No Integration Tests** with actual services (FastAPI, LangChain)
7. **No Manual Testing Checklists** for real-world validation

---

## Testing Strategy Overview

### Testing Pyramid

```
                    ┌──────────────┐
                    │   Manual     │  <-- Real user testing
                    │  Validation  │      Production monitoring
                    └──────────────┘
                  ┌──────────────────┐
                  │   End-to-End     │  <-- Full system with real LLMs
                  │     Tests        │      User journey scenarios
                  └──────────────────┘
              ┌────────────────────────┐
              │   Integration Tests    │  <-- Multiple components
              │   (Real Services)      │      API endpoints, frameworks
              └────────────────────────┘
          ┌──────────────────────────────┐
          │      Unit Tests              │  <-- Individual functions
          │   (Mocks & Fixtures)         │      Fast, isolated
          └──────────────────────────────┘
```

### Test Categories

| Category | Purpose | Tools | Frequency |
|----------|---------|-------|-----------|
| Unit Tests | Test individual functions | pytest, unittest | Every commit |
| Integration Tests | Test component interactions | pytest, real services | Every PR |
| End-to-End Tests | Test complete user flows | pytest, real LLMs | Daily/Weekly |
| Performance Tests | Test speed & scalability | pytest-benchmark, locust | Weekly |
| Manual Testing | Validate real-world usage | Checklist, monitoring | Before release |

---

## Real-World Validation Scenarios

### Scenario 1: Chatbot with Memory

**Use Case**: Build a chatbot that remembers user preferences and conversation history

**Test Implementation**:
```python
# tests/realworld/test_chatbot_scenario.py
import pytest
from memograph import MemoryKernel, MemoryType

def test_chatbot_conversation_flow(temp_vault):
    """Test a realistic chatbot conversation with memory."""
    kernel = MemoryKernel(str(temp_vault))

    # Session 1: User introduces themselves
    kernel.remember(
        title="User Profile - John",
        content="My name is John. I'm a Python developer interested in AI.",
        memory_type=MemoryType.FACT,
        tags=["user-profile", "john"],
        salience=0.9
    )

    # Session 2: User asks a question
    kernel.remember(
        title="Conversation 2024-03-08",
        content="User asked: How do I build a chatbot with memory?",
        memory_type=MemoryType.EPISODIC,
        tags=["conversation", "john", "chatbot"],
        salience=0.7
    )

    # Session 3: User returns later - retrieve context
    kernel.ingest()

    # Chatbot should remember who John is
    context = kernel.context_window(
        query="Who am I and what do I like?",
        tags=["user-profile", "john"],
        top_k=3
    )

    # Validate context includes user info
    assert "John" in context
    assert "Python developer" in context or "Python" in context

    # Chatbot should remember previous conversation
    prev_context = kernel.context_window(
        query="What did we talk about before?",
        tags=["conversation", "john"],
        top_k=3
    )

    assert "chatbot" in prev_context.lower()

# Run with: pytest tests/realworld/test_chatbot_scenario.py -v
```

**Expected Behavior**:
- ✅ User profile is stored and retrieved
- ✅ Conversation history is maintained
- ✅ Context is relevant to the query
- ✅ Information persists across sessions

---

### Scenario 2: RAG System (Document Q&A)

**Test Implementation**:
```python
# tests/realworld/test_rag_scenario.py
import pytest
from memograph import MemoryKernel, MemoryType

def test_rag_document_qa_system(temp_vault):
    """Test a realistic RAG system for document Q&A."""
    kernel = MemoryKernel(str(temp_vault))

    # Load knowledge base documents
    documents = [
        {
            "title": "Python Best Practices",
            "content": "Always use type hints in Python. Use list comprehensions. Follow PEP 8.",
            "tags": ["python", "best-practices"],
            "salience": 0.8
        },
        {
            "title": "FastAPI Guide",
            "content": "FastAPI is a modern async web framework for Python with type validation.",
            "tags": ["python", "fastapi", "web"],
            "salience": 0.8
        },
        {
            "title": "Database Design",
            "content": "Use indexes for queries. Normalize data. Use foreign keys.",
            "tags": ["database", "design"],
            "salience": 0.8
        }
    ]

    # Bulk load documents
    paths, errors = kernel.remember_many([
        {**doc, "memory_type": MemoryType.SEMANTIC} for doc in documents
    ])

    assert len(paths) == 3
    assert len(errors) == 0

    # Ingest and build index
    stats = kernel.ingest()
    assert stats["total"] == 3

    # Test queries
    test_cases = [
        ("What are Python best practices?", ["type hints", "PEP 8"]),
        ("Tell me about FastAPI", ["FastAPI", "async"]),
        ("How to design databases?", ["indexes", "normalize"])
    ]

    for query, expected_keywords in test_cases:
        context = kernel.context_window(query=query, top_k=2, token_limit=500)

        # At least one keyword should be present
        found = any(kw in context or kw.lower() in context.lower()
                   for kw in expected_keywords)
        assert found, f"Expected keywords {expected_keywords} not found for '{query}'"

# Run with: pytest tests/realworld/test_rag_scenario.py -v
```

---

### Scenario 3: Concurrent Async Operations

**Test Implementation**:
```python
# tests/realworld/test_async_concurrent.py
import pytest
import asyncio
from memograph import MemoryKernel, MemoryType

@pytest.mark.asyncio
async def test_concurrent_async_operations(temp_vault):
    """Test concurrent async operations don't cause issues."""
    kernel = MemoryKernel(str(temp_vault))

    # Create multiple memories concurrently
    tasks = []
    for i in range(10):
        task = kernel.remember_async(
            title=f"Memory {i}",
            content=f"Content for memory number {i}",
            memory_type=MemoryType.FACT,
            tags=["concurrent-test"],
            salience=0.5 + (i * 0.05)
        )
        tasks.append(task)

    # Wait for all to complete
    paths = await asyncio.gather(*tasks)
    assert len(paths) == 10

    # Ingest asynchronously
    stats = await kernel.ingest_async()
    assert stats["total"] == 10

    # Concurrent retrievals
    query_tasks = [
        kernel.retrieve_nodes_async(f"memory {i}", top_k=5)
        for i in range(5)
    ]

    results = await asyncio.gather(*query_tasks)
    assert len(results) == 5

    # Each result should have nodes
    for result in results:
        assert len(result) > 0

# Run with: pytest tests/realworld/test_async_concurrent.py -v
```

---

## Integration Testing

### With Real LLM Providers

**Setup**: Create integration tests controlled by environment variables

```python
# tests/integration/test_llm_integration.py
import os
import pytest
from memograph import MemoryKernel

# Skip if API keys not available
pytestmark = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set"
)

def test_openai_embedding_integration(temp_vault):
    """Test integration with OpenAI embeddings."""
    from memograph.adapters.embeddings.openai import OpenAIEmbeddingAdapter

    adapter = OpenAIEmbeddingAdapter(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="text-embedding-3-small"
    )

    kernel = MemoryKernel(str(temp_vault), embedding_adapter=adapter)

    # Create memory
    kernel.remember(
        title="Test with Real Embeddings",
        content="This is a test using real OpenAI embeddings API.",
        salience=0.8
    )

    # Ingest (will call OpenAI API)
    stats = kernel.ingest()
    assert stats["total"] == 1

    # Retrieve with semantic search
    nodes = kernel.retrieve_nodes("test embeddings", top_k=1)
    assert len(nodes) == 1
    assert nodes[0].embedding is not None
    assert len(nodes[0].embedding) > 0

# Run with: OPENAI_API_KEY=your_key pytest tests/integration/ -v
```

### With FastAPI

```python
# tests/integration/test_fastapi_integration.py
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from memograph import MemoryKernel, MemoryType

def test_fastapi_endpoint_integration(temp_vault):
    """Test MemoGraph in a FastAPI application."""
    app = FastAPI()
    kernel = MemoryKernel(str(temp_vault))

    @app.post("/memories/")
    async def create_memory(title: str, content: str):
        path = await kernel.remember_async(
            title=title,
            content=content,
            memory_type=MemoryType.FACT
        )
        return {"path": path}

    @app.get("/search/")
    async def search(q: str):
        await kernel.ingest_async()
        nodes = await kernel.retrieve_nodes_async(q, top_k=5)
        return {"results": [n.to_dict() for n in nodes]}

    # Test the API
    client = TestClient(app)

    # Create memory via API
    response = client.post(
        "/memories/",
        params={"title": "Test API", "content": "Testing FastAPI integration"}
    )
    assert response.status_code == 200
    assert "path" in response.json()

    # Search via API
    response = client.get("/search/", params={"q": "testing"})
    assert response.status_code == 200
    assert "results" in response.json()
    assert len(response.json()["results"]) > 0
```

---

## End-to-End Testing

### Complete User Journey

```python
# tests/e2e/test_complete_user_journey.py
import pytest
from memograph import MemoryKernel, MemoryType

def test_complete_chatbot_user_journey(temp_vault):
    """
    Test complete user journey from setup to conversation.

    Simulates:
    1. System initialization
    2. User onboarding
    3. Multiple conversations
    4. Context retrieval
    5. Memory management
    """
    # Step 1: Initialize system
    kernel = MemoryKernel(str(temp_vault))

    # Step 2: User onboarding
    kernel.remember(
        title="User Onboarding - Alice",
        content="User Alice prefers technical depth, Python examples, and async patterns.",
        memory_type=MemoryType.FACT,
        tags=["user-alice", "preferences", "onboarding"],
        salience=1.0
    )

    # Step 3: First conversation
    conversation_1 = [
        "How do I build a REST API?",
        "What's the best framework?",
        "Show me an example"
    ]

    for i, msg in enumerate(conversation_1):
        kernel.remember(
            title=f"Conv1-Turn{i+1}",
            content=f"User: {msg}",
            memory_type=MemoryType.EPISODIC,
            tags=["user-alice", "conv-1", "api"],
            salience=0.7
        )

    # Step 4: Second conversation (different topic)
    kernel.remember(
        title="Conv2-DatabaseQuestion",
        content="User asked about PostgreSQL vs MySQL for their project",
        memory_type=MemoryType.EPIS
