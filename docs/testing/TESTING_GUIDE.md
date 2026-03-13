# MemoGraph Real-World Testing & Validation Guide

**Purpose**: Practical guide to validate MemoGraph works correctly in real-world Python applications

---

## 🚀 Quick Start: Testing Your MemoGraph Integration

### Step 1: Create a Simple Test Script

Create `test_my_memograph.py`:

```python
#!/usr/bin/env python3
"""
Quick validation script for MemoGraph in your application.
Run with: python test_my_memograph.py
"""

from memograph import MemoryKernel, MemoryType
import tempfile
import os

def test_basic_functionality():
    """Test basic MemoGraph operations."""
    print("🧪 Testing MemoGraph Basic Functionality...\n")

    # Create temporary vault
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"✓ Created temporary vault at: {temp_dir}")

        # Initialize kernel
        kernel = MemoryKernel(temp_dir)
        print("✓ Initialized MemoryKernel")

        # Test 1: Create a memory
        print("\n📝 Test 1: Creating memory...")
        path = kernel.remember(
            title="Test Memory",
            content="This is a test memory for validation",
            memory_type=MemoryType.FACT,
            tags=["test", "validation"],
            salience=0.8
        )
        print(f"✓ Memory created at: {path}")
        assert os.path.exists(path), "Memory file not created!"

        # Test 2: Ingest memories
        print("\n📚 Test 2: Ingesting memories...")
        stats = kernel.ingest()
        print(f"✓ Ingested {stats['total']} memories")
        assert stats['total'] == 1, f"Expected 1 memory, got {stats['total']}"

        # Test 3: Retrieve memories
        print("\n🔍 Test 3: Retrieving memories...")
        nodes = kernel.retrieve_nodes(query="test validation", top_k=5)
        print(f"✓ Retrieved {len(nodes)} nodes")
        assert len(nodes) > 0, "No nodes retrieved!"
        assert "Test Memory" in nodes[0].title

        # Test 4: Context window
        print("\n📄 Test 4: Generating context window...")
        context = kernel.context_window(
            query="test memory",
            tags=["test"],
            top_k=3,
            token_limit=512
        )
        print(f"✓ Generated context ({len(context)} chars)")
        assert "Test Memory" in context
        assert len(context) > 0

        print("\n✅ All tests passed! MemoGraph is working correctly.\n")
        return True

if __name__ == "__main__":
    try:
        test_basic_functionality()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
```

### Step 2: Run the Test

```bash
python test_my_memograph.py
```

**Expected Output**:
```
🧪 Testing MemoGraph Basic Functionality...

✓ Created temporary vault at: /tmp/tmpxyz123
✓ Initialized MemoryKernel

📝 Test 1: Creating memory...
✓ Memory created at: /tmp/tmpxyz123/test-memory.md

📚 Test 2: Ingesting memories...
✓ Ingested 1 memories

🔍 Test 3: Retrieving memories...
✓ Retrieved 1 nodes

📄 Test 4: Generating context window...
✓ Generated context (156 chars)

✅ All tests passed! MemoGraph is working correctly.
```

---

## 🎯 Real-World Use Case Testing

### Use Case 1: Chatbot Memory

**Test your chatbot integration:**

```python
# test_chatbot_integration.py
from memograph import MemoryKernel, MemoryType

def test_chatbot_memory():
    """Test chatbot with conversation memory."""
    kernel = MemoryKernel("./chatbot_memory")

    # Simulate user conversation
    print("💬 Testing chatbot conversation memory...\n")

    # User introduces themselves
    kernel.remember(
        title="User Profile - John",
        content="Name: John. Occupation: Software Engineer. Interests: AI, Python",
        memory_type=MemoryType.FACT,
        tags=["user-john", "profile"],
        salience=0.9
    )
    print("✓ Stored user profile")

    # User asks a question
    kernel.remember(
        title="Question about APIs",
        content="User asked: How do I build a RESTful API with FastAPI?",
        memory_type=MemoryType.EPISODIC,
        tags=["user-john", "conversation", "fastapi"],
        salience=0.7
    )
    print("✓ Stored conversation turn")

    # Ingest
    kernel.ingest()

    # Later: Bot needs to recall user info
    context = kernel.context_window(
        query="Who is the user and what do they like?",
        tags=["user-john", "profile"],
        top_k=3
    )

    print(f"\n📋 Retrieved context:\n{context}\n")

    # Verify important info is present
    assert "John" in context
    assert "Software Engineer" in context or "AI" in context
    print("✅ Chatbot memory test passed!\n")

if __name__ == "__main__":
    test_chatbot_memory()
```

---

### Use Case 2: RAG (Document Q&A)

**Test document retrieval:**

```python
# test_rag_system.py
from memograph import MemoryKernel, MemoryType

def test_rag_system():
    """Test RAG system for document Q&A."""
    kernel = MemoryKernel("./rag_documents")

    print("📚 Testing RAG document Q&A system...\n")

    # Load documents
    documents = [
        {
            "title": "Python Async Guide",
            "content": "Python async/await allows non-blocking I/O operations. "
                      "Use asyncio for concurrent tasks. FastAPI is async-first.",
            "tags": ["python", "async", "guide"]
        },
        {
            "title": "Database Best Practices",
            "content": "Always use connection pooling. Index frequently queried columns. "
                      "Use prepared statements to prevent SQL injection.",
            "tags": ["database", "best-practices", "security"]
        },
        {
            "title": "API Design Principles",
            "content": "RESTful APIs should be stateless. Use proper HTTP methods. "
                      "Version your API endpoints. Return appropriate status codes.",
            "tags": ["api", "design", "rest"]
        }
    ]

    # Bulk load
    paths, errors = kernel.remember_many([
        {**doc, "memory_type": MemoryType.SEMANTIC, "salience": 0.8}
        for doc in documents
    ])

    print(f"✓ Loaded {len(paths)} documents")
    kernel.ingest()

    # Test queries
    test_queries = [
        "How do I use async in Python?",
        "What are database security practices?",
        "How should I design REST APIs?"
    ]

    for query in test_queries:
        print(f"\n❓ Query: {query}")
        context = kernel.context_window(query=query, top_k=2, token_limit=300)
        print(f"📄 Answer preview: {context[:150]}...")
        assert len(context) > 0, f"No context for query: {query}"

    print("\n✅ RAG system test passed!\n")

if __name__ == "__main__":
    test_rag_system()
```

---

### Use Case 3: Async FastAPI Integration

**Test async operations in FastAPI:**

```python
# test_fastapi_async.py
import asyncio
from memograph import MemoryKernel, MemoryType

async def test_async_operations():
    """Test async operations for FastAPI integration."""
    kernel = MemoryKernel("./async_test")

    print("⚡ Testing async operations...\n")

    # Test async memory creation
    print("Creating memories asynchronously...")
    tasks = [
        kernel.remember_async(
            title=f"Async Memory {i}",
            content=f"Test content {i}",
            salience=0.5 + (i * 0.1)
        )
        for i in range(5)
    ]

    paths = await asyncio.gather(*tasks)
    print(f"✓ Created {len(paths)} memories asynchronously")

    # Test async ingest
    stats = await kernel.ingest_async()
    print(f"✓ Ingested {stats['total']} memories asynchronously")

    # Test async retrieval
    nodes = await kernel.retrieve_nodes_async("test content", top_k=5)
    print(f"✓ Retrieved {len(nodes)} nodes asynchronously")

    # Test async context window
    context = await kernel.context_window_async("async", top_k=3)
    print(f"✓ Generated context asynchronously ({len(context)} chars)")

    print("\n✅ Async operations test passed!\n")

if __name__ == "__main__":
    asyncio.run(test_async_operations())
```

---

## 🔬 Performance Testing

### Test 1: Measure Retrieval Speed

```python
# test_performance.py
import time
from memograph import MemoryKernel, MemoryType

def test_retrieval_performance():
    """Measure retrieval performance with various data sizes."""
    kernel = MemoryKernel("./perf_test")

    print("⏱️  Testing retrieval performance...\n")

    # Create test data
    sizes = [10, 50, 100, 500]

    for size in sizes:
        print(f"Testing with {size} memories...")

        # Create memories
        for i in range(size):
            kernel.remember(
                title=f"Memory {i}",
                content=f"Content for memory {i} " * 10,
                memory_type=MemoryType.SEMANTIC,
                tags=["performance-test"],
                salience=0.5
            )

        # Ingest
        kernel.ingest()

        # Measure retrieval time
        start = time.time()
        nodes = kernel.retrieve_nodes("memory content", top_k=10)
        elapsed = time.time() - start

        print(f"  ✓ Retrieved {len(nodes)} nodes in {elapsed:.3f}s")

        # Performance threshold: should be < 1 second for 500 memories
        if size <= 500:
            assert elapsed < 1.0, f"Retrieval too slow: {elapsed}s"

    print("\n✅ Performance test passed!\n")

if __name__ == "__main__":
    test_retrieval_performance()
```

### Test 2: Memory Usage

```python
# test_memory_usage.py
import psutil
import os
from memograph import MemoryKernel, MemoryType

def test_memory_usage():
    """Monitor memory usage during operations."""
    process = psutil.Process(os.getpid())

    print("💾 Testing memory usage...\n")

    # Baseline memory
    mem_before = process.memory_info().rss / 1024 / 1024  # MB
    print(f"Baseline memory: {mem_before:.2f} MB")

    kernel = MemoryKernel("./memory_test")

    # Create large dataset
    print("Creating 1000 memories...")
    for i in range(1000):
        kernel.remember(
            title=f"Memory {i}",
            content=f"Test content {i} " * 50,
            salience=0.5
        )

    kernel.ingest()

    # Measure memory after
    mem_after = process.memory_info().rss / 1024 / 1024  # MB
    mem_increase = mem_after - mem_before

    print(f"Memory after 1000 memories: {mem_after:.2f} MB")
    print(f"Memory increase: {mem_increase:.2f} MB")

    # Should not use excessive memory (< 100MB for 1000 memories)
    assert mem_increase < 100, f"Memory usage too high: {mem_increase} MB"

    print("\n✅ Memory usage test passed!\n")

if __name__ == "__main__":
    test_memory_usage()
```

---

## ✅ Production Readiness Checklist

Before deploying MemoGraph in production, verify:

### Functional Testing

- [ ] **Basic Operations**
  - [ ] Create memories with all parameters
  - [ ] Ingest and index memories correctly
  - [ ] Retrieve relevant memories
  - [ ] Generate context windows
  - [ ] Handle empty vaults gracefully

- [ ] **Error Handling**
  - [ ] Invalid inputs raise appropriate errors
  - [ ] Missing API keys fail gracefully
  - [ ] Corrupted files don't crash system
  - [ ] Network errors are handled

- [ ] **Edge Cases**
  - [ ] Empty strings and None values
  - [ ] Very long content (>10,000 chars)
  - [ ] Special characters in titles
  - [ ] Concurrent operations
  - [ ] Large number of memories (>10,000)

### Performance Testing

- [ ] **Speed**
  - [ ] Retrieval < 100ms for 1,000 memories
  - [ ] Ingestion < 5s for 1,000 files
  - [ ] Context generation < 50ms

- [ ] **Resource Usage**
  - [ ] Memory usage stays reasonable
  - [ ] No memory leaks over time
  - [ ] Disk usage is manageable

### Integration Testing

- [ ] **With LLM Providers**
  - [ ] OpenAI integration works
  - [ ] Claude integration works
  - [ ] Ollama integration works (if using)

- [ ] **With Frameworks**
  - [ ] FastAPI async operations work
  - [ ] LangChain integration works (if using)
  - [ ] LlamaIndex integration works (if using)

### Security

- [ ] **Data Safety**
  - [ ] No SQL injection vulnerabilities
  - [ ] File paths are validated
  - [ ] API keys are not logged
  - [ ] User data is isolated (multi-tenant)

---

## 🔄 Continuous Testing Strategy

### Development Workflow

```bash
# 1. Run unit tests on every change
pytest tests/ -v

# 2. Run integration tests before commits
pytest tests/integration/ -v
