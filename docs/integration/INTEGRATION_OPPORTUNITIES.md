# Integration Opportunities: Learning from Graphiti, Mem0, and Letta

## Overview

This document identifies specific features and approaches from Graphiti, Mem0, and Letta that can enhance MemoGraph, either through:
1. **Direct Integration**: Using their packages as dependencies
2. **Inspired Implementation**: Learning from their approach and implementing in MemoGraph
3. **Hybrid Approach**: Combining both strategies

---

## 1. Features from Graphiti (getzep/graphiti)

### 1.1 Temporal Features ⭐ HIGH PRIORITY

**What to Learn:**
- Timestamp-based memory retrieval
- Time-decay algorithms for memory relevance
- Temporal relationship tracking (entity X knew Y at time T)

**Integration Strategy:**
```python
# Direct integration approach
pip install graphiti

# Use Graphiti's temporal engine alongside MemoGraph
from graphiti import TemporalGraph
from memograph import MemoryKernel

class TemporalMemoryKernel(MemoryKernel):
    def __init__(self, vault_path):
        super().__init__(vault_path)
        self.temporal_graph = TemporalGraph()

    def remember_with_time(self, content, timestamp, **kwargs):
        # Store in MemoGraph (markdown)
        node = self.remember(content, **kwargs)
        # Track temporal relationships in Graphiti
        self.temporal_graph.add_event(node.id, timestamp, content)
        return node

    def recall_at_time(self, query, timestamp):
        # Query what was known at specific time
        return self.temporal_graph.query_at_time(query, timestamp)
```

**Inspired Implementation:**
Add temporal fields to MemoGraph's YAML frontmatter:
```yaml
---
title: "Meeting Notes"
created: 2024-03-08T10:00:00Z
last_accessed: 2024-03-08T18:00:00Z
access_count: 15
decay_factor: 0.95
temporal_relevance: 0.87
---
```

**Benefits:**
- Time-aware retrieval ("What did we discuss last week?")
- Memory aging and decay
- Historical context ("What did we know before X happened?")

### 1.2 Advanced Entity Relationship Tracking

**What to Learn:**
- Entity resolution (same person, different mentions)
- Relationship strength over time
- Entity disambiguation

**Integration Strategy:**
```python
# Direct integration
from graphiti import EntityResolver

class EnhancedExtractor(EntityExtractor):
    def __init__(self):
        super().__init__()
        self.resolver = EntityResolver()

    def extract_entities(self, content):
        entities = super().extract_entities(content)
        # Use Graphiti's resolution
        resolved = self.resolver.resolve(entities)
        return resolved
```

**Inspired Implementation:**
Enhance MemoGraph's entity tracking:
```python
# memograph/core/entity.py
class Entity:
    def __init__(self, name, entity_type):
        self.name = name
        self.entity_type = entity_type
        self.aliases = set()  # Alternative names
        self.canonical_id = None  # Resolved identity
        self.mentions = []  # All mentions
        self.confidence = 1.0
```

**Benefits:**
- Better entity deduplication
- Track entities across different mentions
- Relationship strength scoring

### 1.3 Graph Query Language

**What to Learn:**
- Declarative graph queries
- Path finding algorithms
- Subgraph extraction

**Inspired Implementation:**
```python
# memograph/core/query.py
class GraphQuery:
    """Inspired by Graphiti's query system"""

    def path_between(self, entity_a, entity_b, max_depth=3):
        """Find paths connecting two entities"""
        pass

    def subgraph_around(self, entity, radius=2):
        """Extract subgraph centered on entity"""
        pass

    def temporal_path(self, entity, start_time, end_time):
        """Path through entity's timeline"""
        pass
```

---

## 2. Features from Mem0 (mem0ai/mem0)

### 2.1 Memory Hierarchy (Multi-Level Memory) ⭐ HIGH PRIORITY

**What to Learn:**
- User-level memories (persistent across sessions)
- Session-level memories (temporary)
- Agent-level memories (persona-specific)

**Direct Integration:**
```python
# Can use Mem0's memory client directly
pip install mem0ai

from mem0 import Memory
from memograph import MemoryKernel

class HierarchicalMemoryKernel(MemoryKernel):
    def __init__(self, vault_path):
        super().__init__(vault_path)
        # Use Mem0 for session/agent level
        self.mem0 = Memory()

    def remember(self, content, scope="persistent", **kwargs):
        if scope == "persistent":
            # Store in MemoGraph markdown
            return super().remember(content, **kwargs)
        else:
            # Store in Mem0 (temporary)
            return self.mem0.add(content, user_id=kwargs.get('user_id'))

    def context_window(self, query, include_session=True):
        # Combine MemoGraph persistent + Mem0 session
        persistent = super().context_window(query)
        if include_session:
            session = self.mem0.search(query)
            return self._merge_contexts(persistent, session)
        return persistent
```

**Inspired Implementation:**
Add scope field to MemoGraph:
```yaml
---
title: "Quick Note"
memory_scope: session  # persistent, session, or agent
expires_at: 2024-03-09T00:00:00Z
session_id: abc-123
---
```

**Benefits:**
- Separate permanent knowledge from temporary context
- Session-specific information doesn't pollute permanent vault
- Agent personas with separate memory spaces

### 2.2 Adaptive Learning & Personalization

**What to Learn:**
- User preference tracking
- Adaptive ranking based on user behavior
- Personalized retrieval

**Direct Integration:**
```python
from mem0 import Memory

class AdaptiveKernel(MemoryKernel):
    def __init__(self, vault_path, user_id):
        super().__init__(vault_path)
        self.mem0_client = Memory()
        self.user_id = user_id

    def learn_preference(self, query, selected_memory, feedback):
        """Learn from user's memory selection"""
        self.mem0_client.add(
            f"User prefers {selected_memory.title} for queries about {query}",
            user_id=self.user_id,
            metadata={"type": "preference", "feedback": feedback}
        )

    def personalized_retrieve(self, query):
        # Get base results
        results = self.retrieve_nodes(query)
        # Get user preferences from Mem0
        preferences = self.mem0_client.get_all(user_id=self.user_id)
        # Re-rank based on preferences
        return self._rerank_with_preferences(results, preferences)
```

**Benefits:**
- Learns from user behavior
- Improves retrieval over time
- Personalized results per user

### 2.3 Memory APIs & REST Interface

**What to Learn:**
- RESTful API design
- Memory CRUD operations
- Webhook integration

**Inspired Implementation:**
```python
# memograph/api/server.py
from fastapi import FastAPI
from memograph import MemoryKernel

app = FastAPI()
kernel = MemoryKernel("~/vault")

@app.post("/memories")
async def create_memory(content: str, tags: List[str]):
    return kernel.remember(content=content, tags=tags)

@app.get("/memories/search")
async def search_memories(query: str, top_k: int = 10):
    return kernel.context_window(query=query, top_k=top_k)

@app.put("/memories/{memory_id}")
async def update_memory(memory_id: str, content: str):
    return kernel.update_memory(memory_id, content)
```

**Benefits:**
- Remote access to memory system
- Integration with web applications
- Webhook support for real-time updates

### 2.4 Vector Store Abstraction

**What to Learn:**
- Unified interface for multiple vector stores
- Easy switching between providers
- Optimized batch operations

**Direct Integration:**
```python
# Use Mem0's vector store abstraction
from mem0.vector_stores import VectorStore
from memograph.adapters.embeddings.base import BaseEmbedding

class Mem0VectorAdapter:
    def __init__(self, provider="qdrant"):
        self.vector_store = VectorStore.get(provider)

    def add_embeddings(self, embeddings, metadata):
        self.vector_store.add(embeddings, metadata)

    def search(self, query_embedding, top_k=10):
        return self.vector_store.search(query_embedding, top_k)
```

**Benefits:**
- Support multiple vector databases
- Easier migration between providers
- Battle-tested abstractions

---

## 3. Features from Letta (letta-ai/letta)

### 3.1 Virtual Context Management ⭐ HIGH PRIORITY

**What to Learn:**
- Context window management beyond token limits
- Memory paging and swapping
- Core vs archival memory distinction

**Integration Strategy:**
```python
pip install letta

from letta import MemoryManager
from memograph import MemoryKernel

class VirtualContextKernel(MemoryKernel):
    def __init__(self, vault_path, context_limit=4096):
        super().__init__(vault_path)
        self.memory_manager = MemoryManager(context_limit)
        self.core_memory = []  # Always in context
        self.archival_memory = []  # Retrieved as needed

    def build_context(self, query, max_tokens=4096):
        """Build context that fits within token limit"""
        # Always include core memory
        context = self.core_memory
        remaining_tokens = max_tokens - self._count_tokens(context)

        # Retrieve relevant archival memory
        candidates = self.retrieve_nodes(query, top_k=50)

        # Use Letta's paging algorithm to fit best memories
        selected = self.memory_manager.select_memories(
            candidates,
            remaining_tokens
        )

        return context + selected

    def promote_to_core(self, memory_id):
        """Move frequently accessed memory to core"""
        memory = self.get_memory(memory_id)
        self.core_memory.append(memory)
        if len(self.core_memory) > self.core_limit:
            # Demote least important
            self._demote_from_core()
```

**Inspired Implementation:**
Add memory tiers to MemoGraph:
```yaml
---
title: "Important Fact"
memory_tier: core  # core, active, archival
access_frequency: 150
last_accessed: 2024-03-08T18:00:00Z
importance_score: 0.95
---
```

**Benefits:**
- Handle conversations longer than context window
- Automatic memory management
- Performance optimization through tiering

### 3.2 Self-Editing Memory

**What to Learn:**
- Allow LLM to modify its own memory
- Memory consolidation and summarization
- Automatic memory cleanup

**Inspired Implementation:**
```python
# memograph/core/self_editor.py
class SelfEditingMemory:
    def __init__(self, kernel, llm_client):
        self.kernel = kernel
        self.llm = llm_client

    async def consolidate_memories(self, topic, memories):
        """LLM consolidates related memories"""
        prompt = f"""
        Consolidate these {len(memories)} memories about {topic}:
        {self._format_memories(memories)}

        Create a single, comprehensive memory that captures all important information.
        """

        consolidated = await self.llm.generate(prompt)

        # Create new consolidated memory
        new_memory = self.kernel.remember(
            title=f"Consolidated: {topic}",
            content=consolidated,
            replaces=[m.id for m in memories]
        )

        # Optionally archive old memories
        for memory in memories:
            memory.archived = True

        return new_memory

    async def refine_memory(self, memory_id, new_information):
        """LLM updates existing memory with new info"""
        memory = self.kernel.get_memory(memory_id)

        prompt = f"""
        Update this memory with new information:

        Current memory:
        {memory.content}

        New information:
        {new_information}

        Provide updated memory content.
        """

        updated = await self.llm.generate(prompt)
        self.kernel.update_memory(memory_id, updated)
```

**Benefits:**
- Memories improve over time
- Reduce redundancy
- Automatic knowledge organization

### 3.3 Function Calling / Tool Use Integration

**What to Learn:**
- Memory operations as function calls
- Tool-use patterns for memory management
- Agent action logging

**Inspired Implementation:**
```python
# memograph/tools/memory_tools.py
class MemoryTools:
    """Expose memory operations as LLM tools"""

    @staticmethod
    def get_tool_definitions():
        return [
            {
                "name": "search_memory",
                "description": "Search memories for relevant information",
                "parameters": {
                    "query": {"type": "string"},
                    "tags": {"type": "array"},
                    "top_k": {"type": "integer", "default": 10}
                }
            },
            {
                "name": "save_memory",
                "description": "Save new information to memory",
                "parameters": {
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "tags": {"type": "array"},
                    "memory_type": {"type": "string"}
                }
            },
            {
                "name": "update_memory",
                "description": "Update existing memory",
                "parameters": {
                    "memory_id": {"type": "string"},
                    "new_content": {"type": "string"}
                }
            }
        ]

    def execute_tool(self, tool_name, parameters):
        kernel = MemoryKernel(self.vault_path)

        if tool_name == "search_memory":
            return kernel.context_window(**parameters)
        elif tool_name == "save_memory":
            return kernel.remember(**parameters)
        elif tool_name == "update_memory":
            return kernel.update_memory(**parameters)
```

**Benefits:**
- LLM can manage its own memory
- Better integration with agent frameworks
- Automatic memory operations

### 3.4 Agent State Persistence

**What to Learn:**
- Persistent agent state across sessions
- Agent personality and behavior patterns
- Long-running agent conversations

**Direct Integration:**
```python
from letta import Agent
from memograph import
