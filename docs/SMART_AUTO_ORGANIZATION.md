# Smart Auto-Organization Engine

The Smart Auto-Organization Engine is MemoGraph's powerful feature that automatically extracts structured information from your memories using Large Language Models (LLMs). When you ingest a memory, the engine analyzes its content and creates a rich graph of entities, relationships, and metadata.

## 🎯 Overview

The Smart Auto-Organization Engine transforms unstructured memory content (like meeting notes, documents, or conversations) into a structured knowledge graph with:

- **📌 Topics & Subtopics** - Main subjects and nested concepts
- **👥 People** - Participants with their roles (organizer, decision-maker, etc.)
- **🏢 Organizations** - Companies, teams, and departments
- **✅ Action Items** - Tasks with assignees, deadlines, and priorities
- **🎯 Decisions** - Explicit decisions made, who made them, and rationale
- **❓ Questions** - Open or unresolved items flagged for follow-up
- **😊 Sentiment** - Tone analysis (productive, tense, collaborative, etc.)
- **📅 Timeline** - Dates, deadlines, milestones, and events
- **🔗 References** - URLs, documents, tools, and APIs mentioned
- **💡 Ideas** - Brainstormed concepts with feasibility ratings
- **⚠️ Risks** - Potential problems, blockers, and mitigation strategies
- **🔁 Recurring Themes** - Patterns across multiple memories

## 🚀 Quick Start

### Basic Usage

```python
from memograph import MemoryKernel
from memograph.adapters.llm.claude import ClaudeLLMClient, ClaudeLLMConfig

# Initialize LLM client
llm_client = ClaudeLLMClient()
llm_config = ClaudeLLMConfig(model="claude-sonnet-4")

# Create kernel with auto-extraction enabled
kernel = MemoryKernel(
    vault_path="./my_vault",
    llm_client=llm_client,
    llm_config=llm_config,
    auto_extract=True  # Enable automatic extraction
)

# Create a memory
kernel.remember(
    title="Team Meeting",
    content="Meeting with Sarah and John. We decided to use React...",
    tags=["meeting", "engineering"]
)

# Ingest and extract
stats = kernel.ingest(auto_extract=True)
print(f"Extracted {stats['entities_extracted']} entities")
```

### Retrieving Extracted Entities

```python
from memograph import EntityType

# Get all entities for a memory
entities = kernel.get_entities(memory_id="team-meeting")

# Get specific entity types
topics = kernel.get_entities(entity_type=EntityType.TOPIC)
people = kernel.get_entities(entity_type=EntityType.PERSON)
actions = kernel.get_entities(entity_type=EntityType.ACTION_ITEM)
decisions = kernel.get_entities(entity_type=EntityType.DECISION)
```

### Manual Extraction

You can manually trigger extraction for a specific memory:

```python
# Extract from a specific memory
result = kernel.extract_from_memory("team-meeting")

print(f"Topics: {result['topics']}")
print(f"People: {result['people']}")
print(f"Action Items: {result['action_items']}")
```

## 🔧 Configuration

### LLM Providers

The engine supports multiple LLM providers:

#### Claude (Anthropic)

```python
from memograph.adapters.llm.claude import ClaudeLLMClient, ClaudeLLMConfig

llm_client = ClaudeLLMClient(api_key="your-key")
llm_config = ClaudeLLMConfig(
    model="claude-sonnet-4",
    max_tokens=2048,
    temperature=0.1  # Lower = more deterministic
)
```

#### Ollama (Local)

```python
from memograph.adapters.llm.ollama import OllamaLLMClient, OllamaLLMConfig

llm_client = OllamaLLMClient(base_url="http://localhost:11434")
llm_config = OllamaLLMConfig(
    model="llama3.1:8b",
    max_tokens=2048,
    temperature=0.1
)
```

### Extraction Options

```python
kernel = MemoryKernel(
    vault_path="./vault",
    llm_client=llm_client,
    llm_config=llm_config,
    auto_extract=True  # Enable/disable auto-extraction globally
)

# Override per-ingestion
kernel.ingest(auto_extract=False)  # Skip extraction this time
```

## 📊 Entity Types

### Topics (`EntityType.TOPIC`)

Main subjects discussed in the memory.

```python
topic = TopicEntity(
    name="Analytics Dashboard",
    description="New data visualization feature",
    confidence=0.9  # 0.0-1.0
)
```

### People (`EntityType.PERSON`)

Individuals mentioned with their roles.

**Roles:**
- `ORGANIZER` - Meeting/event organizer
- `DECISION_MAKER` - Makes key decisions
- `PARTICIPANT` - General participant
- `CONTRIBUTOR` - Active contributor
- `NOTE_TAKER` - Takes notes
- `OBSERVER` - Passive observer

```python
person = PersonEntity(
    name="Sarah Johnson",
    role=ParticipantRole.ORGANIZER,
    organization="Product Team"
)
```

### Action Items (`EntityType.ACTION_ITEM`)

Tasks with metadata.

**Priority Levels:** `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`  
**Status:** `OPEN`, `IN_PROGRESS`, `COMPLETED`, `BLOCKED`

```python
action = ActionItemEntity(
    description="Create technical design document",
    assignee="John",
    deadline=datetime(2024, 3, 1),
    priority=PriorityLevel.HIGH,
    status=StatusType.OPEN
)
```

### Decisions (`EntityType.DECISION`)

Explicit decisions made.

```python
decision = DecisionEntity(
    description="Use React for frontend",
    decision_maker="Tech Lead",
    rationale="Team expertise and ecosystem"
)
```

### Questions (`EntityType.QUESTION`)

Open or unresolved items.

```python
question = QuestionEntity(
    question="Do we need real-time updates?",
    status=StatusType.UNRESOLVED,
    asked_by="Sarah"
)
```

### Sentiment (`EntityType.SENTIMENT`)

Overall tone of the memory.

**Types:** `POSITIVE`, `NEGATIVE`, `NEUTRAL`, `TENSE`, `PRODUCTIVE`, `CHAOTIC`, `COLLABORATIVE`, `URGENT`

```python
sentiment = SentimentEntity(
    sentiment_type=SentimentType.PRODUCTIVE,
    intensity=0.7,  # 0.0-1.0
    description="Meeting was productive with some concerns"
)
```

### Risks (`EntityType.RISK`)

Potential problems or blockers.

```python
risk = RiskEntity(
    description="Timeline is aggressive",
    priority=PriorityLevel.HIGH,
    impact="May delay launch",
    mitigation="Add buffer time"
)
```

## 🏗️ Architecture

The Smart Auto-Organization Engine consists of:

1. **SmartAutoOrganizer** - Main extraction engine
2. **Extraction Prompt** - Carefully crafted prompt for LLM
3. **Entity Parsers** - Convert LLM JSON to entity objects
4. **Graph Integration** - Store entities in the knowledge graph

### Extraction Flow

```
Memory → LLM Analysis → JSON Response → Entity Objects → Knowledge Graph
```

### Data Model

```
Memory (1) ─────→ ExtractionResult (1)
                         │
                         ├─→ Topics (0..n)
                         ├─→ People (0..n)
                         ├─→ Action Items (0..n)
                         ├─→ Decisions (0..n)
                         └─→ ... (other entities)
```

## 💡 Best Practices

### 1. Write Descriptive Memory Content

The engine works best with well-structured content:

```markdown
✅ Good:
Meeting with Sarah (Product Manager) and John (Tech Lead).
We decided to use React for the dashboard.
Action: John to create design doc by March 1st.

❌ Less Effective:
Met with team. Discussed stuff. Will follow up.
```

### 2. Use Appropriate Memory Types

- `EPISODIC` - Events, meetings, conversations
- `SEMANTIC` - Concepts, definitions, knowledge
- `FACT` - Specific facts or data points
- `PROCEDURAL` - How-to information

### 3. Enable Selective Extraction

For large vaults, you might want to:

```python
# Extract only for important memories
kernel = MemoryKernel(vault_path="./vault", auto_extract=False)
kernel.ingest()  # No extraction

# Manual extraction for specific memories
kernel.extract_from_memory("important-meeting")
```

### 4. Monitor Extraction Quality

Review extracted entities periodically:

```python
entities = kernel.get_entities()
for entity in entities:
    print(f"{entity.entity_type}: {entity.name} (confidence: {entity.confidence})")
```

### 5. Leverage Entity Relationships

Entities are linked to their source memories:

```python
# Get all entities from a memory
entities = kernel.get_entities_for_memory("team-meeting-2024")

# Find related memories through entities
person_entities = kernel.get_entities(entity_type=EntityType.PERSON)
for person in person_entities:
    print(f"{person.name} mentioned in: {person.source_memory_id}")
```

## 🔍 Advanced Usage

### Custom Extraction

You can create your own extraction logic:

```python
from memograph.core.extractor import SmartAutoOrganizer

organizer = SmartAutoOrganizer(llm_client, llm_config)
result = organizer.extract(memory_node)

# Access specific entity types
for topic in result.topics:
    print(f"Topic: {topic.name}")
    
for action in result.action_items:
    print(f"Action: {action.description}")
    print(f"  Assignee: {action.assignee}")
    print(f"  Deadline: {action.deadline}")
```

### Filtering Entities

```python
# Get high-priority action items
actions = kernel.get_entities(entity_type=EntityType.ACTION_ITEM)
high_priority = [a for a in actions if a.priority == PriorityLevel.HIGH]

# Get unresolved questions
questions = kernel.get_entities(entity_type=EntityType.QUESTION)
open_questions = [q for q in questions if q.status == StatusType.UNRESOLVED]

# Get recent risks
risks = kernel.get_entities(entity_type=EntityType.RISK)
critical_risks = [r for r in risks if r.priority == PriorityLevel.CRITICAL]
```

### Entity Metadata

All entities have a `metadata` dictionary for additional information:

```python
person = kernel.get_entity("person-sarah-johnson")
print(person.metadata["organization"])  # "Product Team"
print(person.metadata["role"])  # "organizer"

action = kernel.get_entity("action-design-doc")
print(action.metadata["deadline"])  # "2024-03-01T00:00:00"
print(action.metadata["priority"])  # "high"
```

## 🎨 Use Cases

### 1. Meeting Notes Management

Automatically extract:
- Attendees and their roles
- Decisions made
- Action items with owners
- Open questions

### 2. Project Documentation

Extract:
- Key stakeholders
- Technical decisions and rationale
- Risks and mitigation strategies
- Timeline and milestones

### 3. Knowledge Base Organization

Identify:
- Main topics and subtopics
- Related documents and resources
- Recurring themes across content
- Ideas and innovations

### 4. Task Tracking

Track:
- All action items across memories
- Assignees and deadlines
- Priority levels
- Status updates

## 🐛 Troubleshooting

### No Entities Extracted

**Possible causes:**
1. LLM client not configured correctly
2. Memory content too short or vague
3. JSON parsing error

**Solutions:**
```python
# Check extraction result
result = kernel.extract_from_memory("memory-id")
print(result)  # Should show entity counts

# Enable verbose mode (check console for errors)
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Low Extraction Quality

**Tips:**
- Use more detailed memory content
- Include explicit sections (Decisions, Actions, etc.)
- Adjust LLM temperature (lower = more consistent)
- Try a different/larger model

### Performance Considerations

- Extraction uses LLM API calls (costs money/time)
- Consider extracting only for important memories
- Use local LLMs (Ollama) for cost-free extraction
- Cache results (automatic in MemoGraph)

## 📚 API Reference

### MemoryKernel

```python
kernel = MemoryKernel(
    vault_path: str,
    embedding_adapter=None,
    llm_client=None,
    llm_config=None,
    auto_extract: bool = False
)

# Methods
kernel.ingest(force=False, auto_extract=None) -> dict
kernel.extract_from_memory(memory_id: str) -> dict
kernel.get_entities(memory_id=None, entity_type=None) -> list[EntityNode]
```

### SmartAutoOrganizer

```python
from memograph.core.extractor import SmartAutoOrganizer

organizer = SmartAutoOrganizer(llm_client, llm_config)
result = organizer.extract(memory_node) -> ExtractionResult
```

### Entity Types

All available in `memograph.core.enums`:
- `EntityType` - Entity classification
- `SentimentType` - Sentiment categories
- `ParticipantRole` - People roles
- `PriorityLevel` - Priority levels
- `StatusType` - Status categories

## 🤝 Contributing

Want to improve the extraction engine? Contributions welcome!

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

## 📄 License

MemoGraph is licensed under the MIT License. See [LICENSE](../LICENSE) for details.