# Integration Recommendations: Key Features to Adopt from Graphiti, Mem0, and Letta

## Executive Summary

Based on analysis of three leading LLM memory systems, here are the **most valuable features** to integrate into MemoGraph, ordered by priority and implementation difficulty.

---

## 🔥 HIGH PRIORITY: Quick Wins (1-2 weeks)

### 1. Temporal Features (From Graphiti)

**What:** Add timestamp tracking and time-decay algorithms for memory relevance.

**Why:** Enables "What did we discuss last week?" queries and makes recent memories more relevant.

**Implementation Options:**

**Option A - Direct Integration:**
```bash
pip install graphiti
```
```python
from graphiti import TemporalGraph
from memograph import MemoryKernel

class TemporalMemoryKernel(MemoryKernel):
    def __init__(self, vault_path):
        super().__init__(vault_path)
        self.temporal = TemporalGraph()

    def remember_with_time(self, content, timestamp=None, **kwargs):
        node = super().remember(content, **kwargs)
        self.temporal.add_event(node.id, timestamp or datetime.now(), content)
        return node
```

**Option B - Inspired (Recommended):**
Enhance YAML frontmatter:
```yaml
---
title: "Meeting Notes"
created: 2024-03-08T10:00:00Z
last_accessed: 2024-03-08T18:00:00Z
access_count: 15
temporal_relevance: 0.87  # Calculated: salience * decay_factor
---
```

**Files to Modify:**
- `memograph/core/node.py` - Add temporal fields
- `memograph/core/retriever.py` - Add time-based scoring
- `memograph/core/parser.py` - Parse temporal metadata

---

### 2. REST API (From Mem0)

**What:** Add FastAPI-based REST endpoints for remote memory access.

**Why:** Enables web apps, mobile apps, and services to use MemoGraph remotely.

**Implementation:**
```bash
pip install fastapi uvicorn pydantic
```

```python
# memograph/api/server.py
from fastapi import FastAPI
from memograph import MemoryKernel

app = FastAPI(title="MemoGraph API")
kernel = MemoryKernel("~/vault")

@app.post("/api/v1/memories")
async def create_memory(title: str, content: str, tags: list[str] = []):
    return kernel.remember(title=title, content=content, tags=tags)

@app.get("/api/v1/memories/search")
async def search(q: str, top_k: int = 10):
    return kernel.context_window(query=q, top_k=top_k)
```

**Usage:**
```bash
# Start server
python -m memograph.api.server

# Or via CLI
memograph --vault ~/vault serve --port 8000
```

**Files to Create:**
- `memograph/api/__init__.py`
- `memograph/api/server.py`
- `memograph/api/models.py` (Pydantic models)

---

### 3. Memory Hierarchy - Session vs Persistent (From Mem0)

**What:** Separate temporary session memories from permanent knowledge.

**Why:** Prevents temporary context from polluting permanent vault.

**Implementation Option A - Direct Integration:**
```bash
pip install mem0ai
```

```python
from mem0 import Memory as Mem0
from memograph import MemoryKernel

class HybridMemory:
    def __init__(self, vault_path):
        self.persistent = MemoryKernel(vault_path)  # Permanent -> Markdown
        self.session = Mem0()  # Temporary -> Mem0

    def remember(self, content, scope="persistent", **kwargs):
        if scope == "persistent":
            return self.persistent.remember(content, **kwargs)
        else:
            return self.session.add(content, user_id=kwargs.get('user_id'))
```

**Implementation Option B - Inspired (Recommended):**
Add in-memory session cache:
```python
# memograph/core/hierarchy.py
class SessionMemory:
    def __init__(self, kernel):
        self.kernel = kernel
        self.sessions = {}  # session_id -> list of memories

    def remember_session(self, content, session_id, **kwargs):
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        memory = {"content": content, "timestamp": datetime.now(), **kwargs}
        self.sessions[session_id].append(memory)
        return memory

    def clear_session(self, session_id):
        """Clear expired session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
```

---

## ⭐ MEDIUM PRIORITY: Enhanced Capabilities (2-4 weeks)

### 4. Virtual Context Management (From Letta)

**What:** Smart context window management that fits within token limits.

**Why:** Handle conversations longer than context window, optimize token usage.

**Implementation:**
```bash
pip install tiktoken
```

```python
# memograph/features/context_manager.py
import tiktoken

class VirtualContextManager:
    def __init__(self, kernel, max_tokens=4096):
        self.kernel = kernel
        self.max_tokens = max_tokens
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        self.core_memory = []  # Always included

    def build_context(self, query, system_prompt=""):
        budget = self.max_tokens
        parts = []

        # 1. System prompt
        if system_prompt:
            parts.append(system_prompt)
            budget -= self._count_tokens(system_prompt)

        # 2. Core memories
        core_text = self._format(self.core_memory)
        parts.append(core_text)
        budget -= self._count_tokens(core_text)

        # 3. Retrieve and fit archival memories
        candidates = self.kernel.retrieve_nodes(query, top_k=50)
        selected = self._fit_to_budget(candidates, budget)
        parts.append(self._format(selected))

        return "\n\n".join(parts)
```

**Files to Create:**
- `memograph/features/context_manager.py`
- Update `memograph/cli.py` to use virtual context

---

### 5. Self-Editing Memory (From Letta)

**What:** Allow LLM to consolidate and refine its own memories.

**Why:** Reduce redundancy, improve memory quality over time.

**Implementation:**
```python
# memograph/features/self_editing.py
class SelfEditingMemory:
    def __init__(self, kernel, llm_client):
        self.kernel = kernel
        self.llm = llm_client

    async def consolidate_topic(self, topic):
        """Merge multiple memories about same topic"""
        memories = self.kernel.retrieve_nodes(topic, top_k=20)

        if len(memories) < 3:
            return None

        prompt = f"""Consolidate these {len(memories)} memories about {topic} into one comprehensive memory:
        {self._format_memories(memories)}
        """

        consolidated = await self.llm.generate(prompt)

        # Create consolidated memory
        new = self.kernel.remember(
            title=f"Consolidated: {topic}",
            content=consolidated,
            tags=["consolidated"] + memories[0].tags
        )

        # Archive old memories
        for m in memories:
            self.kernel.update_metadata(m.id, {"archived": True, "replaced_by": new.id})

        return new
```

**Files to Create:**
- `memograph/features/self_editing.py`
- Add CLI command: `memograph consolidate --topic "project planning"`

---

### 6. Enhanced Entity Resolution (From Graphiti)

**What:** Better entity deduplication and relationship tracking.

**Why:** "John", "John Smith", and "John S." should be recognized as same person.

**Implementation Options:**

**Option A - Use Graphiti:**
```python
from graphiti import EntityResolver

class EnhancedExtractor(EntityExtractor):
    def __init__(self):
        super().__init__()
        self.resolver = EntityResolver()

    def extract_entities(self, content):
        entities = super().extract_entities(content)
        return self.resolver.resolve(entities)
```

**Option B - Implement Simple Resolution:**
```python
# memograph/core/entity_resolution.py
class EntityResolver:
    def __init__(self):
        self.canonical_names = {}  # alias -> canonical
        self.entity_aliases = {}   # canonical -> [aliases]

    def resolve(self, entity_name):
        """Get canonical name for entity"""
        return self.canonical_names.get(entity_name, entity_name)

    def merge_entities(self, entity1, entity2):
        """Merge two entities"""
        canonical = entity1
        alias = entity2
        self.canonical_names[alias] = canonical
        if canonical not in self.entity_aliases:
            self.entity_aliases[canonical] = []
        self.entity_aliases[canonical].append(alias)
```

---

## 🚀 ADVANCED: Future Enhancements (4+ weeks)

### 7. Full Letta Agent Integration

**What:** Use MemoGraph as memory backend for Letta agents.

**Why:** Combine Letta's agent framework with MemoGraph's markdown storage.

**Implementation:**
```bash
pip install letta
```

```python
# memograph/integrations/letta.py
from letta import Agent, create_client
from memograph import MemoryKernel

class LettaMemoryBackend:
    def __init__(self, vault_path, agent_id):
        self.kernel = MemoryKernel(vault_path)
        self.agent_id = agent_id
        self.client = create_client()
        self.agent = self.client.create_agent(
            name=agent_id,
            memory=self
        )

    def core_memory_append(self, key, value):
        self.kernel.remember(
            title=f"Core: {key}",
            content=value,
            tags=["core-memory", self.agent_id],
            memory_tier="core"
        )

    def archival_memory_search(self, query, top_k=10):
        return self.kernel.retrieve_nodes(
            query,
            tags=[self.agent_id],
            top_k=top_k
        )
```

---

### 8. Adaptive Learning from User Behavior

**What:** Learn which memories users find most helpful and adapt ranking.

**Why:** Personalized retrieval that improves over time.

**Implementation:**
```python
# memograph/features/adaptive.py
class AdaptiveLearning:
    def __init__(self, kernel):
        self.kernel = kernel
        self.feedback_db = {}  # memory_id -> feedback score

    def record_selection(self, query, selected_memory_id):
        """User selected this memory for this query"""
        if selected_memory_id not in self.feedback_db:
            self.feedback_db[selected_memory_id] = {'helpful_count': 0}
        self.feedback_db[selected_memory_id]['helpful_count'] += 1

    def personalized_rank(self, memories):
        """Re-rank based on learned preferences"""
        for memory in memories:
            feedback = self.feedback_db.get(memory.id, {})
            boost = feedback.get('helpful_count', 0) * 0.1
            memory.score += boost
        return sorted(memories, key=lambda m: m.score, reverse=True)
```

---

## 📦 Recommended Packages to Add

### Direct Dependencies
```toml
# pyproject.toml
[project.optional-dependencies]
api = [
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
    "pydantic>=2.0.0"
]
temporal = [
    "graphiti>=0.1.0"  # If using direct integration
]
session = [
    "mem0ai>=0.1.0"  # If using direct integration
]
agents = [
    "letta>=0.1.0"  # If using direct integration
]
context = [
    "tiktoken>=0.5.0"
]
all-integrations = [
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
    "pydantic>=2.0.0",
    "tiktoken>=0.5.0",
    "graphiti>=0.1.0",
    "mem0ai>=0.1.0",
    "letta>=0.1.0"
]
```

---

## 🎯 Recommended Implementation Order

### Sprint 1 (Week 1-2): Foundation
1. ✅ Add temporal fields to YAML frontmatter
2. ✅ Implement time-decay scoring in retriever
3. ✅ Add REST API with FastAPI
4. ✅ Add session memory support (in-memory)

### Sprint 2 (Week 3-4): Enhancement
5. ✅ Implement virtual context manager
6. ✅ Add basic entity resolution
7. ✅ Create self-editing memory features
8. ✅ Add adaptive learning tracking

### Sprint 3 (Week 5-6): Integration
9. ✅ Integrate Mem0 for session management (optional)
10. ✅ Integrate Graphiti for temporal queries (optional)
11. ✅ Add Letta agent backend support
12. ✅ Create integration examples

---

## 💡 Architecture Decisions

### When to Use Direct Integration vs Inspired Implementation

**Use Direct Integration (pip install) when:**
- Feature is complex and well-tested in their library
- You want to leverage their optimizations
- Community support and updates are valuable
- Examples: Mem0 for session management, Tiktoken for tokenization

**Use Inspired Implementation (write your own) when:**
- Feature is simple enough to implement
- You want full control over behavior
- You want to maintain markdown-first philosophy
- Dependency would add significant bloat
- Examples: Temporal scoring, entity resolution basics

### Hybrid Approach (Recommended)

**Core MemoGraph**: Keep markdown-first, file-based, lightweight
- Temporal features (inspired)
- Session memory (inspired)
- Entity resolution (inspired)
- Virtual context (inspired)

**Optional Integrations**: Via plugins/adapters
- Mem0 adapter for advanced session management
- Graphiti adapter for complex temporal queries
- Letta adapter for agent frameworks

This keeps MemoGraph lightweight by default while offering power-user integrations.

---

## 📝 Example Usage After Integration

```python
from memograph import MemoryKernel
from memograph.features import VirtualContextManager, SessionMemory
from memograph.api import create_api_server

# Initialize with enhanced features
kernel = MemoryKernel("~/vault")
context_mgr = VirtualContextManager(kernel, max_tokens=4096)
session_mgr = SessionMemory(kernel)

# Use temporal queries
recent = kernel.retrieve_nodes(
    query="project decisions",
    since
