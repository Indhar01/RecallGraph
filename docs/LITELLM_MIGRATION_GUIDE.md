# LiteLLM Migration Guide

## Overview

MemoGraph now supports **LiteLLM**, a unified interface for 100+ LLM providers. This guide helps you migrate from the old provider-specific adapters to the new unified LiteLLM adapter.

## Why Migrate?

### Old Approach (Provider-Specific Adapters)
- ❌ Separate adapter for each provider
- ❌ Different APIs and configurations
- ❌ ~150 lines of adapter code to maintain
- ❌ Manual retry/fallback logic
- ❌ No built-in cost tracking

### New Approach (LiteLLM Unified Adapter)
- ✅ **One adapter for 100+ providers**
- ✅ **Consistent API across all providers**
- ✅ **~30 lines total** - 80% less code
- ✅ **Built-in retries, fallbacks, cost tracking**
- ✅ **Easy provider switching** - just change model name
- ✅ **Active maintenance** from LiteLLM team

---

## Installation

### Option 1: Install LiteLLM only
```bash
pip install memograph[litellm]
```

### Option 2: Install with other dependencies
```bash
pip install memograph[litellm,embeddings]
```

### Option 3: Install everything
```bash
pip install memograph[all]
```

---

## Migration Examples

### Example 1: Claude (Anthropic)

**Before (Old Adapter):**
```python
from memograph.adapters.llm.claude import ClaudeLLMClient, ClaudeLLMConfig

# Initialize
client = ClaudeLLMClient(api_key="sk-ant-...")
config = ClaudeLLMConfig(
    model="claude-3-5-sonnet-20240620",
    max_tokens=1024,
    temperature=0.1
)

# Generate
response = client.generate("Hello", config)
```

**After (LiteLLM):**
```python
from memograph.adapters.llm.litellm_adapter import LiteLLMClient, LiteLLMConfig

# Initialize
config = LiteLLMConfig(
    model="claude-3-5-sonnet-20240620",
    max_tokens=1024,
    temperature=0.1
)
client = LiteLLMClient(config)

# Generate (same API!)
response = client.generate("Hello")
```

### Example 2: Ollama (Local)

**Before (Old Adapter):**
```python
from memograph.adapters.llm.ollama import OllamaLLMClient, OllamaLLMConfig

# Initialize
client = OllamaLLMClient(base_url="http://localhost:11434")
config = OllamaLLMConfig(
    model="llama3.1:8b",
    max_tokens=512,
    temperature=0.1
)

# Generate
response = client.generate("Hello", config)
```

**After (LiteLLM):**
```python
from memograph.adapters.llm.litellm_adapter import LiteLLMClient, LiteLLMConfig

# Initialize - just add "ollama/" prefix
config = LiteLLMConfig(
    model="ollama/llama3.1:8b",  # <- Add "ollama/" prefix
    api_base="http://localhost:11434",
    max_tokens=512,
    temperature=0.1
)
client = LiteLLMClient(config)

# Generate (same API!)
response = client.generate("Hello")
```

### Example 3: With MemoGraph SmartAutoOrganizer

**Before:**
```python
from memograph import MemoryKernel
from memograph.adapters.llm.claude import ClaudeLLMClient, ClaudeLLMConfig
from memograph.core.extractor import SmartAutoOrganizer

# Different setup for each provider
claude_client = ClaudeLLMClient(api_key="...")
claude_config = ClaudeLLMConfig(model="claude-3-5-sonnet-20240620")

organizer = SmartAutoOrganizer(claude_client, claude_config)
```

**After:**
```python
from memograph import MemoryKernel
from memograph.adapters.llm.litellm_adapter import LiteLLMClient, LiteLLMConfig
from memograph.core.extractor import SmartAutoOrganizer

# Same setup for all providers - just change model name!
config = LiteLLMConfig(model="claude-3-5-sonnet-20240620")
# Or: config = LiteLLMConfig(model="gpt-4")
# Or: config = LiteLLMConfig(model="ollama/llama3.1:8b")

client = LiteLLMClient(config)
organizer = SmartAutoOrganizer(client, config)
```

---

## Quick Reference: Model Names

LiteLLM uses standardized model identifiers:

### OpenAI
```python
"gpt-4-turbo-preview"
"gpt-4"
"gpt-3.5-turbo"
```

### Anthropic (Claude)
```python
"claude-3-5-sonnet-20240620"
"claude-3-opus-20240229"
"claude-3-sonnet-20240229"
```

### Ollama (Local)
```python
"ollama/llama3.1:8b"      # <- Add "ollama/" prefix
"ollama/mistral"
"ollama/codellama"
```

### Google
```python
"gemini/gemini-pro"
"gemini/gemini-1.5-pro"
```

### Azure OpenAI
```python
"azure/gpt-4"
"azure/gpt-35-turbo"
```

### Cohere
```python
"command-r-plus"
"command-r"
```

---

## API Key Configuration

### Environment Variables (Recommended)

LiteLLM automatically reads from standard environment variables:

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# Google
export GEMINI_API_KEY="..."

# Cohere
export COHERE_API_KEY="..."

# No key needed for Ollama (local)
```

### Explicit Configuration

You can also pass API keys directly:

```python
config = LiteLLMConfig(
    model="gpt-4",
    api_key="sk-...",  # <- Explicit API key
)
```

---

## New Features Available

### 1. Automatic Fallbacks

Try multiple models automatically:

```python
client = LiteLLMClient(LiteLLMConfig(model="gpt-4"))

response = client.generate_with_fallback(
    "Hello",
    fallback_models=["gpt-3.5-turbo", "claude-3-sonnet-20240229"]
)
# Tries: gpt-4 → gpt-3.5-turbo → claude-3-sonnet
```

### 2. Streaming Responses

```python
client = LiteLLMClient(LiteLLMConfig(model="gpt-4"))

for chunk in client.stream_generate("Write a story"):
    print(chunk, end="", flush=True)
```

### 3. Async Support

```python
client = LiteLLMClient(LiteLLMConfig(model="gpt-4"))

response = await client.generate_async("Hello")
```

### 4. Cost Tracking

```python
import litellm

response = litellm.completion(model="gpt-4", messages=[...])
cost = litellm.completion_cost(response)
print(f"Cost: ${cost:.4f}")
```

---

## Comparison Table

| Feature | Old Adapters | LiteLLM |
|---------|-------------|---------|
| **Providers Supported** | 3 (OpenAI, Anthropic, Ollama) | 100+ |
| **Lines of Code** | ~150 | ~30 |
| **Unified API** | ❌ No | ✅ Yes |
| **Automatic Retries** | ❌ Manual | ✅ Built-in |
| **Fallback Support** | ❌ Manual | ✅ Built-in |
| **Cost Tracking** | ❌ No | ✅ Built-in |
| **Streaming** | ⚠️ Limited | ✅ Full support |
| **Async** | ⚠️ Limited | ✅ Full support |
| **Maintenance** | Manual | Active (LiteLLM team) |

---

## Migration Checklist

- [ ] Install LiteLLM: `pip install memograph[litellm]`
- [ ] Update imports: `from memograph.adapters.llm.litellm_adapter import ...`
- [ ] Update model names (add prefixes for Ollama: `ollama/model-name`)
- [ ] Set API keys as environment variables
- [ ] Test with your existing code
- [ ] (Optional) Add fallback models for reliability
- [ ] (Optional) Enable async for better performance

---

## Common Issues & Solutions

### Issue 1: "litellm not found"

**Solution:**
```bash
pip install memograph[litellm]
# or
pip install litellm
```

### Issue 2: Ollama connection fails

**Solution:**
- Make sure Ollama is running: `ollama serve`
- Use model prefix: `ollama/llama3.1:8b` (not just `llama3.1:8b`)
- Set correct base URL if not default:
  ```python
  config = LiteLLMConfig(
      model="ollama/llama3.1:8b",
      api_base="http://localhost:11434"
  )
  ```

### Issue 3: API key errors

**Solution:**
- Set environment variables: `export OPENAI_API_KEY="sk-..."`
- Or pass explicitly:
  ```python
  config = LiteLLMConfig(model="gpt-4", api_key="sk-...")
  ```

### Issue 4: "Model not found"

**Solution:**
- Check model name spelling
- For Ollama, add `ollama/` prefix
- For Azure, add `azure/` prefix
- For Gemini, add `gemini/` prefix

---

## Testing the Migration

Run the example file to test your migration:

```bash
python examples/litellm_usage.py
```

This will:
1. Test basic usage with multiple providers
2. Show convenience functions
3. Demonstrate MemoGraph integration
4. Showcase advanced features (fallbacks, streaming, async)

---

## Backward Compatibility

**Good news:** The old adapters (`claude.py`, `ollama.py`) are still available for backward compatibility. You can migrate at your own pace.

**Deprecation timeline:**
- **v0.1.x**: Both old and new adapters available
- **v0.2.x**: Old adapters marked as deprecated (warnings shown)
- **v1.0.0**: Old adapters may be removed

---

## Need Help?

- **Documentation**: See [`LLM_ABSTRACTION_LAYER.md`](../LLM_ABSTRACTION_LAYER.md)
- **Examples**: See [`examples/litellm_usage.py`](../examples/litellm_usage.py)
- **Issues**: [GitHub Issues](https://github.com/Indhar01/MemoGraph/issues)
- **LiteLLM Docs**: https://docs.litellm.ai/

---

## Summary

**Migration is simple:**

1. Install: `pip install memograph[litellm]`
2. Change import: `from memograph.adapters.llm.litellm_adapter import LiteLLMClient, LiteLLMConfig`
3. Update model names (add prefixes where needed)
4. Done! Same API for all 100+ providers

**Benefits:**
- ✅ 80% less code
- ✅ 100+ providers supported
- ✅ Built-in features (retries, fallbacks, cost tracking)
- ✅ Easy provider switching
- ✅ Better maintained

**Happy migrating! 🚀**
