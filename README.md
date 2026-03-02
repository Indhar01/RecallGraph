# Mnemo Vault

Mnemo Vault is a library for building and interacting with a personal memory vault using LLMs
. It provides a graph-based memory kernel that can ingest Markdown notes and retrieve context for Large Language Models.

## Installation

```bash
pip install mnemo-vault
```

To install with specific LLM provider support:

```bash
pip install mnemo-vault[openai]
pip install mnemo-vault[anthropic]
```


## Python Usage

```python
from mnemo import MemoryKernel, MemoryType

# Initialize the kernel attached to your vault path
kernel = MemoryKernel("~/my-vault")

# Ingest all notes in the vault
stats = kernel.ingest()
print(f"Indexed {stats['indexed']} memories.")

# Programmatically add a new memory
kernel.remember(
    title="Meeting Note",
    content="Decided to use BFS graph traversal for retrieval.",
    memory_type=MemoryType.EPISODIC,
    tags=["#design", "#retrieval"]
)

# Retrieve context for an LLM query
context = kernel.context_window(
    query="how does retrieval work?",
    tags=["retrieval"],
    depth=2,
    top_k=8
)

print(context)
```

## CLI Usage

Mnemo comes with a powerful CLI for managing your vault and chatting with it.

### Ingest
Index your markdown files into the graph database.

```bash
mnemo --vault ~/my-vault ingest
```

### Remember
Quickly add a memory from the command line.

```bash
mnemo --vault ~/my-vault remember \
    --title "Team Sync" \
    --content "Discussed Q3 goals." \
    --tags planning q3
```

### Chat
Start an interactive chat session with your vault context.

```bash
mnemo --vault ~/my-vault ask --chat --provider ollama --model llama3
```

### Diagnostics
Check your environment and connection to LLM providers.

```bash
mnemo --vault ~/my-vault doctor
```

## License

MIT
