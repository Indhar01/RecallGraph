# LLM Abstraction Layer: Using LiteLLM for Unified Provider Support

## Current Situation

MemoGraph currently has separate adapter files for each LLM provider:
- [`memograph/adapters/llm/claude.py`](memograph/adapters/llm/claude.py) - Anthropic Claude
- [`memograph/adapters/llm/ollama.py`](memograph/adapters/llm/ollama.py) - Ollama
- Presumably OpenAI adapter somewhere

**Problems with current approach:**
1. ❌ Need to write and maintain separate adapter for each provider
2. ❌ Duplication of error handling, retry logic, etc.
3. ❌ When adding new provider (Google Gemini, Cohere, etc.), need new adapter
4. ❌ Inconsistent interfaces between adapters

## Solution: LiteLLM

**LiteLLM** is a unified interface that supports 100+ LLM providers with a single API.

### What is LiteLLM?

LiteLLM provides:
- ✅ **Unified API** - Same interface for OpenAI, Anthropic, Ollama, Google, Cohere, etc.
- ✅ **100+ Models** - Supports virtually every major LLM provider
- ✅ **Built-in Features** - Retries, fallbacks, rate limiting, cost tracking
- ✅ **OpenAI-compatible** - Uses OpenAI's API format (familiar to developers)
- ✅ **Streaming Support** - Easy streaming responses
- ✅ **Async Support** - Native async/await

### Supported Providers

- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude 3.5 Sonnet, Claude 3 Opus)
- Google (Gemini Pro, PaLM)
- Ollama (all local models)
- Cohere
- Azure OpenAI
- AWS Bedrock
- Hugging Face
- ...and 90+ more

---

## Comparison: Before vs After

### Before (Current): Multiple Adapters

**File Structure:**
```
memograph/adapters/llm/
├── claude.py       (43 lines)
├── ollama.py       (47 lines)
├── openai.py       (probably 40 lines)
└── base.py         (interface)
```

**Usage:**
```python
# Different imports for each provider
from memograph.adapters.llm.claude import ClaudeLLMClient, ClaudeLLMConfig
from memograph.adapters.llm.ollama import OllamaLLMClient, OllamaLLMConfig

# Different instantiation
claude = ClaudeLLMClient(api_key="...")
ollama = OllamaLLMClient(base_url="http://localhost:11434")

# Different configs
claude_config = ClaudeLLMConfig(model="claude-3-5-sonnet-20240620")
ollama_config = OllamaLLMConfig(model="llama3.1:8b")
```

### After (With LiteLLM): Single Unified Adapter

**File Structure:**
```
memograph/adapters/llm/
├── litellm_adapter.py  (30 lines total!)
└── base.py             (interface)
```

**Usage:**
```python
# Single import
from memograph.adapters.llm.litellm_adapter import LiteLLMClient

# Unified instantiation - just change model name
client = LiteLLMClient()

# All providers use same interface
response = client.generate("Hello", model="claude-3-5-sonnet-20240620")
response = client.generate("Hello", model="gpt-4")
response = client.generate("Hello", model="ollama/llama3.1:8b")
```

---

## Implementation

### Step 1: Install LiteLLM

```bash
pip install litellm
```

### Step 2: Create Unified Adapter

```python
# memograph/adapters/llm/litellm_adapter.py
import os
from dataclasses import dataclass
from typing import Optional
import litellm

@dataclass
class LiteLLMConfig:
    """Unified config for all LLM providers"""
    model: str = "gpt-3.5-turbo"
    max_tokens: int = 1024
    temperature: float = 0.1
    api_key: Optional[str] = None
    api_base: Optional[str] = None

class LiteLLMClient:
    """Unified LLM client supporting 100+ providers via LiteLLM"""

    def __init__(self, config: Optional[LiteLLMConfig] = None):
        self.config = config or LiteLLMConfig()

        # Set API keys from environment if not provided
        if not self.config.api_key:
            # LiteLLM auto-detects from environment:
            # OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.
            pass

        # Configure LiteLLM settings
        litellm.drop_params = True  # Ignore unsupported params
        litellm.set_verbose = False  # Set to True for debugging

    def generate(self, prompt: str, config: Optional[LiteLLMConfig] = None) -> str:
        """Generate text from prompt using any LLM provider"""
        cfg = config or self.config

        try:
            response = litellm.completion(
                model=cfg.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=cfg.max_tokens,
                temperature=cfg.temperature,
                api_key=cfg.api_key,
                api_base=cfg.api_base,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise RuntimeError(f"LLM generation failed: {e}") from e

    async def generate_async(self, prompt: str, config: Optional[LiteLLMConfig] = None) -> str:
        """Async version for better performance"""
        cfg = config or self.config

        try:
            response = await litellm.acompletion(
                model=cfg.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=cfg.max_tokens,
                temperature=cfg.temperature,
                api_key=cfg.api_key,
                api_base=cfg.api_base,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise RuntimeError(f"Async LLM generation failed: {e}") from e
```

### Step 3: Update Extractor to Use LiteLLM

```python
# memograph/core/extractor.py
from memograph.adapters.llm.litellm_adapter import LiteLLMClient, LiteLLMConfig

# Old way (multiple imports):
# from memograph.adapters.llm.claude import ClaudeLLMClient
# from memograph.adapters.llm.ollama import OllamaLLMClient

# New way (single import):
class SmartAutoOrganizer:
    def __init__(self, model: str = "gpt-3.5-turbo"):
        config = LiteLLMConfig(
            model=model,
            max_tokens=1024,
            temperature=0.1
        )
        self.llm_client = LiteLLMClient(config)

    def extract(self, memory):
        # Same as before - just works with any provider!
        response = self.llm_client.generate(prompt, self.llm_client.config)
        # ... rest of extraction logic
```

---

## Usage Examples

### Example 1: OpenAI GPT-4

```python
from memograph import MemoryKernel
from memograph.adapters.llm.litellm_adapter import LiteLLMClient, LiteLLMConfig

# Configure for OpenAI
config = LiteLLMConfig(
    model="gpt-4",
    temperature=0.1,
    max_tokens=1024
)

client = LiteLLMClient(config)
kernel = MemoryKernel("~/vault", llm_client=client)
```

### Example 2: Anthropic Claude

```python
# Just change the model name!
config = LiteLLMConfig(
    model="claude-3-5-sonnet-20240620",
    temperature=0.1,
    max_tokens=1024
)

client = LiteLLMClient(config)
kernel = MemoryKernel("~/vault", llm_client=client)
```

### Example 3: Ollama (Local)

```python
# For Ollama, prefix model with "ollama/"
config = LiteLLMConfig(
    model="ollama/llama3.1:8b",
    api_base="http://localhost:11434",
    temperature=0.1
)

client = LiteLLMClient(config)
kernel = MemoryKernel("~/vault", llm_client=client)
```

### Example 4: Google Gemini

```python
config = LiteLLMConfig(
    model="gemini/gemini-pro",
    temperature=0.1
)

client = LiteLLMClient(config)
kernel = MemoryKernel("~/vault", llm_client=client)
```

### Example 5: Azure OpenAI

```python
config = LiteLLMConfig(
    model="azure/gpt-4",
    api_base="https://your-resource.openai.azure.com",
    api_key="your-azure-key"
)

client = LiteLLMClient(config)
kernel = MemoryKernel("~/vault", llm_client=client)
```

---

## Advanced Features

### Feature 1: Automatic Fallbacks

LiteLLM can automatically fallback to alternative models if primary fails:

```python
from litellm import completion

response = completion(
    model="gpt-4",
    messages=[{"role": "user", "content": prompt}],
    fallbacks=["gpt-3.5-turbo", "claude-3-sonnet-20240229"]
)
```

### Feature 2: Cost Tracking

```python
import litellm

# Enable cost tracking
litellm.success_callback = ["langfuse"]  # or any callback

response = litellm.completion(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)

# Get cost
print(f"Cost: ${litellm.completion_cost(response)}")
```

### Feature 3: Retry Logic

```python
from litellm import completion_with_retries

response = completion_with_retries(
    model="gpt-4",
    messages=[{"role": "user", "content": prompt}],
    num_retries=3,
    timeout=60
)
```

### Feature 4: Rate Limiting

```python
from litellm import Router

# Create router with rate limits
router = Router(
    model_list=[
        {
            "model_name": "gpt-4",
            "litellm_params": {
                "model": "gpt-4",
                "api_key": os.getenv("OPENAI_API_KEY")
            },
            "rpm": 60  # requests per minute
        }
    ]
)

response = router.completion(
    model="gpt-4",
    messages=[{"role": "user", "content": prompt}]
)
```

### Feature 5: Streaming Responses

```python
response = litellm.completion(
    model="gpt-4",
    messages=[{"role": "user", "content": prompt}],
    stream=True
)

for chunk in response:
    print(chunk.choices[0].delta.content, end="")
```

---

## Migration Plan

### Phase 1: Add LiteLLM Adapter (Week 1)

**Tasks:**
1. Install LiteLLM: `pip install litellm`
2. Create `memograph/adapters/llm/litellm_adapter.py`
3. Test with existing providers (Claude, Ollama)
4. Ensure backward compatibility

**Files to Create:**
- `memograph/adapters/llm/litellm_adapter.py`
- `tests/test_litellm_adapter.py`

### Phase 2: Update Core Components (Week 1-2)

**Tasks:**
1. Update `SmartAutoOrganizer` to accept LiteLLM client
2. Update CLI to use LiteLLM
3. Update examples

**Files to Modify:**
- `memograph/core/extractor.py`
- `memograph/core/assistant.py`
- `memograph/cli.py`
- `examples/`

### Phase 3: Deprecate Old Adapters (Week 2-3)

**Tasks:**
1. Mark old adapters as deprecated
2. Add migration guide
3. Update documentation
4. Keep old adapters for backward compatibility (1-2 releases)

**Files to Update:**
- `memograph/adapters/llm/claude.py` (add deprecation warning)
- `memograph/adapters/llm/ollama.py` (add deprecation warning)
- `docs/MIGRATION.md` (create)

### Phase 4: Remove Old Adapters (Future release)

**Tasks:**
1. Remove deprecated adapters
2. Clean up imports
3. Update all documentation

---

## Configuration Examples

### Via Environment Variables

LiteLLM automatically reads from environment:

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# Google
export GEMINI_API_KEY="..."

# Ollama (no key needed)
export OLLAMA_BASE_URL="http://localhost:11434"
```

Then use:
```python
client = LiteLLMClient(LiteLLMConfig(model="gpt-4"))  # Auto-uses OPENAI_API_KEY
client = LiteLLMClient(LiteLLMConfig(model="claude-3-5-sonnet-20240620"))  # Auto-uses ANTHROPIC_API_KEY
```

### Via Config File

```yaml
# config.yaml
llm:
  provider: litellm
  model: gpt-4
  temperature: 0.1
  max_tokens: 1024
  fallbacks:
    - gpt-3.5-
