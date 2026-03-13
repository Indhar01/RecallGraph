"""
Example: Using LiteLLM Unified Adapter with MemoGraph

This example demonstrates how to use the LiteLLM adapter to connect to multiple
AI providers (OpenAI, Anthropic, Google, Ollama, etc.) with a unified interface.

Installation:
    pip install memograph[litellm]

Environment Setup:
    export OPENAI_API_KEY="sk-..."
    export ANTHROPIC_API_KEY="sk-ant-..."
    export GEMINI_API_KEY="..."
    # No key needed for Ollama (local)
"""

import asyncio

from memograph import MemoryKernel, MemoryType
from memograph.adapters.llm.litellm_adapter import LiteLLMClient, LiteLLMConfig, create_client
from memograph.core.extractor import SmartAutoOrganizer


def example_1_basic_usage():
    """Example 1: Basic usage with different providers"""
    print("=" * 60)
    print("Example 1: Basic Usage with Different Providers")
    print("=" * 60)

    # OpenAI GPT-4
    print("\n1. Using OpenAI GPT-4:")
    config = LiteLLMConfig(model="gpt-4", max_tokens=100, temperature=0.7)
    client = LiteLLMClient(config)
    response = client.generate("What is machine learning?")
    print(f"Response: {response[:150]}...")

    # Anthropic Claude
    print("\n2. Using Anthropic Claude:")
    config = LiteLLMConfig(model="claude-3-5-sonnet-20240620", max_tokens=100, temperature=0.7)
    client = LiteLLMClient(config)
    response = client.generate("What is machine learning?")
    print(f"Response: {response[:150]}...")

    # Ollama (Local)
    print("\n3. Using Ollama (Local):")
    try:
        config = LiteLLMConfig(
            model="ollama/llama3.1:8b",
            api_base="http://localhost:11434",
            max_tokens=100,
            temperature=0.7,
        )
        client = LiteLLMClient(config)
        response = client.generate("What is machine learning?")
        print(f"Response: {response[:150]}...")
    except Exception as e:
        print(f"Ollama not available: {e}")

    # Google Gemini
    print("\n4. Using Google Gemini:")
    try:
        config = LiteLLMConfig(model="gemini/gemini-pro", max_tokens=100, temperature=0.7)
        client = LiteLLMClient(config)
        response = client.generate("What is machine learning?")
        print(f"Response: {response[:150]}...")
    except Exception as e:
        print(f"Gemini not available (may need API key): {e}")


def example_2_convenience_function():
    """Example 2: Using convenience function for quick setup"""
    print("\n" + "=" * 60)
    print("Example 2: Convenience Function")
    print("=" * 60)

    # Quick setup with create_client()
    client = create_client("gpt-3.5-turbo", temperature=0.5, max_tokens=50)
    response = client.generate("Define artificial intelligence in one sentence.")
    print(f"\nResponse: {response}")


def example_3_with_memograph():
    """Example 3: Using LiteLLM with MemoGraph's Smart Auto-Organizer"""
    print("\n" + "=" * 60)
    print("Example 3: LiteLLM with MemoGraph")
    print("=" * 60)

    # Initialize kernel
    kernel = MemoryKernel("./test_vault")

    # Configure LiteLLM for extraction
    config = LiteLLMConfig(
        model="gpt-3.5-turbo",  # Or "claude-3-5-sonnet-20240620"
        max_tokens=1024,
        temperature=0.1,
    )
    llm_client = LiteLLMClient(config)

    # Create Smart Auto-Organizer with LiteLLM
    organizer = SmartAutoOrganizer(llm_client, config)

    # Add a memory
    memory = kernel.remember(
        title="Team Meeting Notes",
        content="""
        Met with the engineering team today. Discussed the new API design.

        Key decisions:
        - Will use REST architecture
        - Target launch date: March 15, 2024
        - Sarah will lead the backend implementation
        - John raised concerns about scalability

        Action items:
        - Sarah: Draft API specification by Friday
        - John: Research load balancing solutions
        - Team: Review security requirements
        """,
        memory_type=MemoryType.EPISODIC,
        tags=["meeting", "engineering", "api-design"],
    )

    print(f"\nCreated memory: {memory.title}")

    # Extract structured information using LiteLLM
    print("\nExtracting structured information...")
    extraction = organizer.extract(memory)

    # Display extracted entities
    print(f"\nTopics: {[t.name for t in extraction.topics]}")
    print(f"People: {[p.name for p in extraction.people]}")
    print(f"Decisions: {[d.description[:50] + '...' for d in extraction.decisions]}")
    print(f"Action Items: {[a.description[:50] + '...' for a in extraction.action_items]}")


def example_4_fallback():
    """Example 4: Using fallback models"""
    print("\n" + "=" * 60)
    print("Example 4: Automatic Fallbacks")
    print("=" * 60)

    config = LiteLLMConfig(model="gpt-4", max_tokens=50)
    client = LiteLLMClient(config)

    try:
        # Try GPT-4, fallback to GPT-3.5, then Claude
        response = client.generate_with_fallback(
            "Explain quantum computing briefly.",
            fallback_models=["gpt-3.5-turbo", "claude-3-sonnet-20240229"],
        )
        print(f"Response: {response}")
    except Exception as e:
        print(f"All models failed: {e}")


def example_5_streaming():
    """Example 5: Streaming responses"""
    print("\n" + "=" * 60)
    print("Example 5: Streaming Responses")
    print("=" * 60)

    config = LiteLLMConfig(model="gpt-3.5-turbo", max_tokens=100, temperature=0.7)
    client = LiteLLMClient(config)

    print("\nStreaming response:")
    for chunk in client.stream_generate("Write a haiku about programming."):
        print(chunk, end="", flush=True)
    print("\n")


async def example_6_async():
    """Example 6: Async usage for better performance"""
    print("\n" + "=" * 60)
    print("Example 6: Async Usage")
    print("=" * 60)

    config = LiteLLMConfig(model="gpt-3.5-turbo", max_tokens=50)
    client = LiteLLMClient(config)

    # Multiple async requests
    prompts = ["What is Python?", "What is JavaScript?", "What is Go?"]

    print("\nMaking 3 async requests...")
    tasks = [client.generate_async(prompt, config) for prompt in prompts]
    responses = await asyncio.gather(*tasks)

    for prompt, response in zip(prompts, responses):
        print(f"\n{prompt}")
        print(f"Response: {response[:100]}...")


def example_7_all_providers():
    """Example 7: Showcase all supported providers"""
    print("\n" + "=" * 60)
    print("Example 7: All Supported Providers")
    print("=" * 60)

    providers = {
        "OpenAI GPT-4": "gpt-4",
        "OpenAI GPT-3.5": "gpt-3.5-turbo",
        "Claude 3.5 Sonnet": "claude-3-5-sonnet-20240620",
        "Claude 3 Opus": "claude-3-opus-20240229",
        "Gemini Pro": "gemini/gemini-pro",
        "Ollama Llama": "ollama/llama3.1:8b",
        "Cohere Command": "command-r",
    }

    print("\nSupported Providers:")
    for name, model_id in providers.items():
        print(f"  • {name}: {model_id}")

    print("\nTo use any provider, just change the model parameter:")
    print('  client = LiteLLMClient(LiteLLMConfig(model="YOUR_MODEL_HERE"))')


def example_8_comparison():
    """Example 8: Compare old adapters vs LiteLLM"""
    print("\n" + "=" * 60)
    print("Example 8: Old vs New Approach")
    print("=" * 60)

    print("\n🔴 OLD WAY (Multiple Adapters):")
    print("-" * 40)
    print("""
# Different imports
from memograph.adapters.llm.claude import ClaudeLLMClient, ClaudeLLMConfig
from memograph.adapters.llm.ollama import OllamaLLMClient, OllamaLLMConfig

# Different instantiation
claude = ClaudeLLMClient(api_key="...")
ollama = OllamaLLMClient(base_url="http://localhost:11434")

# Different configs
claude_config = ClaudeLLMConfig(model="claude-3-5-sonnet")
ollama_config = OllamaLLMConfig(model="llama3.1:8b")

# Different generate calls
response1 = claude.generate(prompt, claude_config)
response2 = ollama.generate(prompt, ollama_config)
    """)

    print("\n✅ NEW WAY (LiteLLM - Single Adapter):")
    print("-" * 40)
    print("""
# Single import
from memograph.adapters.llm.litellm_adapter import LiteLLMClient, LiteLLMConfig

# Unified instantiation - just change model name!
client = LiteLLMClient(LiteLLMConfig(model="claude-3-5-sonnet-20240620"))
# Or
client = LiteLLMClient(LiteLLMConfig(model="ollama/llama3.1:8b"))
# Or
client = LiteLLMClient(LiteLLMConfig(model="gpt-4"))

# Same generate call for all providers
response = client.generate(prompt)
    """)

    print("\n📊 Benefits:")
    print("  ✅ One adapter for 100+ providers")
    print("  ✅ Consistent interface")
    print("  ✅ Built-in features: retries, fallbacks, cost tracking")
    print("  ✅ Easy to switch providers")
    print("  ✅ Reduced maintenance")


def main():
    """Run all examples"""
    print("\n")
    print("=" * 60)
    print("  LiteLLM Unified Adapter Examples")
    print("=" * 60)

    # Note: Comment out examples that require API keys you don't have

    try:
        # Example 1: Basic usage with different providers
        example_1_basic_usage()

        # Example 2: Convenience function
        example_2_convenience_function()

        # Example 3: With MemoGraph
        # example_3_with_memograph()  # Uncomment to test with actual vault

        # Example 4: Fallbacks
        # example_4_fallback()  # Uncomment to test fallbacks

        # Example 5: Streaming
        # example_5_streaming()  # Uncomment to test streaming

        # Example 6: Async
        # asyncio.run(example_6_async())  # Uncomment to test async

        # Example 7: All providers showcase
        example_7_all_providers()

        # Example 8: Comparison
        example_8_comparison()

        print("\n" + "=" * 60)
        print("✅ Examples completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have:")
        print("  1. Installed litellm: pip install memograph[litellm]")
        print("  2. Set appropriate API keys as environment variables")
        print("  3. Started Ollama if testing local models")


if __name__ == "__main__":
    main()
