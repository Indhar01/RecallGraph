"""
Example: Using LinkSuggester for wikilink suggestions.

This example demonstrates:
- Creating a LinkSuggester instance
- Getting link suggestions for content
- Understanding semantic, keyword, and graph-based matching
- Detecting bidirectional link opportunities
- Recording feedback to improve suggestions

Requirements:
- A vault with multiple notes already ingested
- Optional: Embeddings for semantic suggestions
"""

import asyncio
from pathlib import Path
from memograph import MemoryKernel
from memograph.ai import LinkSuggester


async def main():
    # Initialize the memory kernel with your vault
    vault_path = "./my_vault"  # Change this to your vault path
    kernel = MemoryKernel(vault_path)
    
    print("🔗 LinkSuggester Example")
    print("=" * 50)
    
    # Ingest notes if vault exists
    if Path(vault_path).exists():
        print(f"\n📚 Ingesting notes from {vault_path}...")
        await kernel.ingest(vault_path)
        print(f"✅ Ingested {len(kernel.memories)} notes")
    else:
        print(f"\n⚠️  Vault not found: {vault_path}")
        print("Creating sample notes for demonstration...")
        
        # Create interconnected sample notes
        await kernel.remember(
            content="Deep learning is a subset of machine learning that uses neural networks with multiple layers. It has revolutionized AI applications.",
            title="Deep Learning Basics",
            tags=["deep-learning", "ai", "neural-networks"],
            memory_type="semantic"
        )
        
        await kernel.remember(
            content="Neural networks are inspired by biological neurons. They consist of layers of interconnected nodes that process information.",
            title="Neural Networks",
            tags=["neural-networks", "ai"],
            memory_type="semantic"
        )
        
        await kernel.remember(
            content="Machine learning algorithms enable computers to learn from data without explicit programming. Supervised and unsupervised learning are key paradigms.",
            title="Machine Learning Overview",
            tags=["machine-learning", "ai"],
            memory_type="semantic"
        )
        
        await kernel.remember(
            content="Transformers have become the dominant architecture in NLP. They use attention mechanisms to process sequential data effectively.",
            title="Transformer Architecture",
            tags=["transformers", "nlp", "deep-learning"],
            memory_type="semantic"
        )
        
        await kernel.remember(
            content="Natural Language Processing (NLP) deals with the interaction between computers and human language. Deep learning has greatly advanced NLP capabilities.",
            title="NLP Fundamentals",
            tags=["nlp", "ai", "machine-learning"],
            memory_type="semantic"
        )
        
        print("✅ Created 5 sample notes")
    
    # Create a LinkSuggester instance
    print("\n🔗 Creating LinkSuggester...")
    suggester = LinkSuggester(
        kernel=kernel,
        min_confidence=0.3,      # Accept suggestions with >30% confidence
        max_suggestions=10        # Show up to 10 suggestions
    )
    
    # Example 1: Basic link suggestions
    print("\n" + "=" * 50)
    print("Example 1: Basic Link Suggestions")
    print("=" * 50)
    
    content = """
    Attention mechanisms are the key innovation in transformers.
    Unlike recurrent neural networks, transformers can process
    entire sequences in parallel. This makes them ideal for
    natural language processing tasks and has led to models
    like GPT and BERT.
    """
    
    title = "Introduction to Attention Mechanisms"
    existing_links = []  # No links yet
    
    print(f"\n📝 Content: {content.strip()[:100]}...")
    print(f"📄 Title: {title}")
    print(f"🔗 Existing links: {existing_links if existing_links else 'None'}")
    
    suggestions = await suggester.suggest_links(
        content=content,
        title=title,
        existing_links=existing_links
    )
    
    print(f"\n💡 Found {len(suggestions)} link suggestions:")
    for i, suggestion in enumerate(suggestions, 1):
        bidirectional = "↔️" if suggestion.is_bidirectional else "→"
        print(f"\n{i}. {bidirectional} [[{suggestion.target_title}]]")
        print(f"   Confidence: {suggestion.confidence:.2%}")
        print(f"   Reason: {suggestion.reason}")
        if suggestion.is_bidirectional:
            print(f"   ⚡ Bidirectional opportunity!")
    
    # Example 2: Understanding suggestion types
    print("\n" + "=" * 50)
    print("Example 2: Suggestion Types")
    print("=" * 50)
    
    print("\n📊 LinkSuggester uses three types of matching:")
    print("\n1. Semantic Matching:")
    print("   - Uses embeddings to find semantically similar notes")
    print("   - Example: 'deep learning' → 'Neural Networks'")
    
    print("\n2. Keyword Matching:")
    print("   - Matches keywords in content with note titles")
    print("   - Example: Content mentions 'transformers' → 'Transformer Architecture'")
    
    print("\n3. Graph-Based Matching:")
    print("   - Finds connections through 2-hop graph traversal")
    print("   - Example: Both link to 'Machine Learning' → might be related")
    
    # Example 3: Filtering by confidence
    print("\n" + "=" * 50)
    print("Example 3: Confidence Filtering")
    print("=" * 50)
    
    print("\n🎯 Filtering suggestions by confidence level:")
    
    high_confidence = [s for s in suggestions if s.confidence >= 0.7]
    medium_confidence = [s for s in suggestions if 0.5 <= s.confidence < 0.7]
    low_confidence = [s for s in suggestions if 0.3 <= s.confidence < 0.5]
    
    print(f"\n   High confidence (≥0.7): {len(high_confidence)} suggestions")
    for s in high_confidence[:3]:
        print(f"      → [[{s.target_title}]] ({s.confidence:.2%})")
    
    print(f"\n   Medium confidence (0.5-0.7): {len(medium_confidence)} suggestions")
    for s in medium_confidence[:3]:
        print(f"      → [[{s.target_title}]] ({s.confidence:.2%})")
    
    print(f"\n   Low confidence (0.3-0.5): {len(low_confidence)} suggestions")
    for s in low_confidence[:3]:
        print(f"      → [[{s.target_title}]] ({s.confidence:.2%})")
    
    # Example 4: Bidirectional links
    print("\n" + "=" * 50)
    print("Example 4: Bidirectional Link Opportunities")
    print("=" * 50)
    
    bidirectional_suggestions = [s for s in suggestions if s.is_bidirectional]
    
    print(f"\n🔄 Found {len(bidirectional_suggestions)} bidirectional opportunities:")
    print("\nBidirectional links strengthen your knowledge graph!")
    
    for suggestion in bidirectional_suggestions[:3]:
        print(f"\n   ↔️  {title} ⟷ {suggestion.target_title}")
        print(f"      Confidence: {suggestion.confidence:.2%}")
        print(f"      Reason: {suggestion.reason}")
    
    # Example 5: Recording feedback
    print("\n" + "=" * 50)
    print("Example 5: Recording Feedback")
    print("=" * 50)
    
    print("\n📊 Recording feedback to improve future suggestions...")
    
    # Accept high-confidence suggestions
    if len(high_confidence) > 0:
        accepted_link = high_confidence[0].target_title
        suggester.record_feedback(accepted_link, accepted=True)
        print(f"✅ Accepted: [[{accepted_link}]]")
    
    # Reject low-confidence suggestion
    if len(low_confidence) > 0:
        rejected_link = low_confidence[0].target_title
        suggester.record_feedback(rejected_link, accepted=False)
        print(f"❌ Rejected: [[{rejected_link}]]")
    
    # View statistics
    stats = suggester.get_link_stats()
    print(f"\n📈 Link Statistics:")
    print(f"   Total suggestions made: {stats['total_suggestions']}")
    print(f"   Accepted: {stats['accepted']}")
    print(f"   Rejected: {stats['rejected']}")
    print(f"   Acceptance rate: {stats['acceptance_rate']:.1%}")
    
    # Example 6: Configuration options
    print("\n" + "=" * 50)
    print("Example 6: Configuration Options")
    print("=" * 50)
    
    print("\n⚙️  Different configuration options:")
    
    # High-quality links only
    strict_suggester = LinkSuggester(
        kernel=kernel,
        min_confidence=0.7,      # Only high-confidence links
        max_suggestions=5         # Top 5 only
    )
    print("\n   Strict Suggester (min_confidence=0.7, max_suggestions=5)")
    strict_suggestions = await strict_suggester.suggest_links(content, title, existing_links)
    print(f"   → Found {len(strict_suggestions)} high-quality links")
    
    # Exploratory mode
    exploratory_suggester = LinkSuggester(
        kernel=kernel,
        min_confidence=0.2,      # Lower threshold
        max_suggestions=20        # More suggestions
    )
    print("\n   Exploratory Suggester (min_confidence=0.2, max_suggestions=20)")
    exploratory_suggestions = await exploratory_suggester.suggest_links(content, title, existing_links)
    print(f"   → Found {len(exploratory_suggestions)} potential links")
    
    # Example 7: Best practices
    print("\n" + "=" * 50)
    print("Example 7: Best Practices")
    print("=" * 50)
    
    print("\n💡 Best Practices for LinkSuggester:")
    print("   1. Start with high-confidence suggestions (>0.6)")
    print("   2. Prioritize bidirectional link opportunities")
    print("   3. Provide existing_links to avoid duplicate suggestions")
    print("   4. Record feedback to improve future suggestions")
    print("   5. Use embeddings for better semantic matching")
    print("   6. Review suggestions in context of your knowledge graph")
    print("   7. Focus on links that add meaningful connections")
    
    print("\n" + "=" * 50)
    print("✅ LinkSuggester example complete!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())