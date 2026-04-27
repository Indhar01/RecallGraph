"""
Example: Using AutoTagger for automatic tag suggestions.

This example demonstrates:
- Creating an AutoTagger instance
- Getting tag suggestions for content
- Recording user feedback
- Viewing statistics and acceptance rates
- Best practices for tag management

Requirements:
- A vault with some notes already ingested
- Optional: Embeddings for semantic suggestions
"""

import asyncio
from pathlib import Path
from memograph import MemoryKernel
from memograph.ai import AutoTagger


async def main():
    # Initialize the memory kernel with your vault
    vault_path = "./my_vault"  # Change this to your vault path
    kernel = MemoryKernel(vault_path)

    print("🚀 AutoTagger Example")
    print("=" * 50)

    # Ingest notes if vault exists
    if Path(vault_path).exists():
        print(f"\n📚 Ingesting notes from {vault_path}...")
        await kernel.ingest(vault_path)
        print(f"✅ Ingested {len(kernel.memories)} notes")
    else:
        print(f"\n⚠️  Vault not found: {vault_path}")
        print("Creating sample notes for demonstration...")

        # Create some sample notes for demonstration
        await kernel.remember(
            content="Python is a versatile programming language widely used in data science, machine learning, and web development.",
            title="Introduction to Python",
            tags=["python", "programming"],
            memory_type="semantic",
        )

        await kernel.remember(
            content="Machine learning algorithms can learn patterns from data without being explicitly programmed.",
            title="Machine Learning Basics",
            tags=["machine-learning", "ai", "data-science"],
            memory_type="semantic",
        )

        await kernel.remember(
            content="Neural networks are computing systems inspired by biological neural networks that can learn complex patterns.",
            title="Neural Networks Overview",
            tags=["neural-networks", "deep-learning", "ai"],
            memory_type="semantic",
        )

        print("✅ Created 3 sample notes")

    # Create an AutoTagger instance
    print("\n🏷️  Creating AutoTagger...")
    tagger = AutoTagger(
        kernel=kernel,
        min_confidence=0.3,  # Accept suggestions with >30% confidence
        max_suggestions=5,  # Show up to 5 suggestions
    )

    # Example 1: Basic tag suggestions
    print("\n" + "=" * 50)
    print("Example 1: Basic Tag Suggestions")
    print("=" * 50)

    content = """
    Python is excellent for machine learning and data science.
    Libraries like scikit-learn, TensorFlow, and PyTorch make it easy
    to implement complex algorithms. Deep learning frameworks have
    revolutionized the field of artificial intelligence.
    """

    title = "ML with Python"
    existing_tags = ["python"]  # Already has this tag

    print(f"\n📝 Content: {content.strip()[:100]}...")
    print(f"📄 Title: {title}")
    print(f"🏷️  Existing tags: {existing_tags}")

    suggestions = await tagger.suggest_tags(
        content=content, title=title, existing_tags=existing_tags
    )

    print(f"\n💡 Found {len(suggestions)} tag suggestions:")
    for i, suggestion in enumerate(suggestions, 1):
        print(f"\n{i}. Tag: '{suggestion.tag}'")
        print(f"   Confidence: {suggestion.confidence:.2%}")
        print(f"   Reason: {suggestion.reason}")

    # Example 2: Recording feedback
    print("\n" + "=" * 50)
    print("Example 2: Recording Feedback")
    print("=" * 50)

    print("\n📊 Recording feedback to improve future suggestions...")

    # Accept some suggestions
    if len(suggestions) > 0:
        accepted_tag = suggestions[0].tag
        tagger.record_feedback(accepted_tag, accepted=True)
        print(f"✅ Accepted: '{accepted_tag}'")

    if len(suggestions) > 1:
        rejected_tag = suggestions[1].tag
        tagger.record_feedback(rejected_tag, accepted=False)
        print(f"❌ Rejected: '{rejected_tag}'")

    # Example 3: Viewing statistics
    print("\n" + "=" * 50)
    print("Example 3: Tag Statistics")
    print("=" * 50)

    stats = tagger.get_tag_stats()

    print("\n📈 Tag Statistics:")
    print(f"   Total suggestions made: {stats['total_suggestions']}")
    print(f"   Accepted: {stats['accepted']}")
    print(f"   Rejected: {stats['rejected']}")
    print(f"   Acceptance rate: {stats['acceptance_rate']:.1%}")

    # Example 4: Best practices
    print("\n" + "=" * 50)
    print("Example 4: Best Practices")
    print("=" * 50)

    print("\n💡 Best Practices for AutoTagger:")
    print("   1. Start with lower confidence (0.3) to see more suggestions")
    print("   2. Always provide existing_tags to avoid duplicates")
    print("   3. Record feedback to improve future suggestions")
    print("   4. Use embeddings for better semantic matching")
    print("   5. Review high-confidence suggestions (>0.6) first")

    # Example 5: Configuration options
    print("\n" + "=" * 50)
    print("Example 5: Configuration Options")
    print("=" * 50)

    print("\n⚙️  Different configuration options:")

    # High-confidence, fewer suggestions
    strict_tagger = AutoTagger(
        kernel=kernel,
        min_confidence=0.6,  # Only high-confidence suggestions
        max_suggestions=3,  # Just top 3
    )
    print("\n   Strict Tagger (min_confidence=0.6, max_suggestions=3)")
    strict_suggestions = await strict_tagger.suggest_tags(content, title, existing_tags)
    print(f"   → Found {len(strict_suggestions)} high-confidence suggestions")

    # More permissive
    permissive_tagger = AutoTagger(
        kernel=kernel,
        min_confidence=0.2,  # Lower threshold
        max_suggestions=10,  # More suggestions
    )
    print("\n   Permissive Tagger (min_confidence=0.2, max_suggestions=10)")
    permissive_suggestions = await permissive_tagger.suggest_tags(
        content, title, existing_tags
    )
    print(f"   → Found {len(permissive_suggestions)} suggestions")

    print("\n" + "=" * 50)
    print("✅ AutoTagger example complete!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
