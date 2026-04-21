"""
Example: Complete AI workflow integrating all features.

This example demonstrates:
- A complete end-to-end workflow using all AI features
- How features work together to enhance knowledge management
- Best practices for using AI features in combination
- Real-world usage pattern from ingestion to analysis

Features used:
- ContentAnalyzer: Analyze note structure
- AutoTagger: Suggest and apply tags
- LinkSuggester: Find and create connections
- GapDetector: Identify and address gaps

Requirements:
- A vault directory (will be created if needed)
"""

import asyncio
from memograph import MemoryKernel
from memograph.ai import ContentAnalyzer, AutoTagger, LinkSuggester, GapDetector


async def main():
    print("🚀 Complete AI Workflow Example")
    print("=" * 70)
    print("\nThis example demonstrates a complete workflow:")
    print("1. Create and ingest notes")
    print("2. Analyze content structure")
    print("3. Suggest and apply tags")
    print("4. Suggest and apply links")
    print("5. Detect and address knowledge gaps")
    print("=" * 70)

    # Step 1: Initialize kernel and create sample vault
    print("\n" + "=" * 70)
    print("STEP 1: Initialize and Create Sample Vault")
    print("=" * 70)

    vault_path = "./demo_vault"
    kernel = MemoryKernel(vault_path)

    print(f"\n📂 Creating sample vault at: {vault_path}")

    # Create a realistic knowledge base about AI/ML
    notes = [
        {
            "title": "Introduction to Machine Learning",
            "content": """
Machine learning is a subset of artificial intelligence that enables computers
to learn from data without being explicitly programmed. It has three main types:
supervised learning, unsupervised learning, and reinforcement learning.

Key concepts include:
- Training data and test data
- Features and labels
- Model evaluation metrics
- Overfitting and underfitting

Machine learning is used in many applications including image recognition,
natural language processing, and recommendation systems.
            """,
            "tags": ["machine-learning", "ai"],
        },
        {
            "title": "Deep Learning Fundamentals",
            "content": """
Deep learning is a subset of machine learning based on artificial neural networks.
It has revolutionized many fields including computer vision and NLP.

Neural networks consist of layers:
- Input layer: receives data
- Hidden layers: process information
- Output layer: produces results

Popular architectures include CNNs for images and RNNs for sequences.
Modern frameworks like TensorFlow and PyTorch make implementation easier.
            """,
            "tags": ["deep-learning", "neural-networks"],
        },
        {
            "title": "Natural Language Processing",
            "content": """
Natural Language Processing (NLP) enables computers to understand and generate
human language. It combines linguistics, computer science, and AI.

Common NLP tasks:
- Text classification
- Named entity recognition
- Machine translation
- Sentiment analysis

Transformers have become the dominant architecture, with models like
BERT, GPT, and T5 achieving state-of-the-art results.
            """,
            "tags": ["nlp", "ai"],
        },
        {
            "title": "Computer Vision Basics",
            "content": """
Computer vision enables machines to interpret and understand visual information
from the world. It's a key component of AI systems.

Applications include:
- Object detection and recognition
- Image segmentation
- Facial recognition
- Autonomous vehicles

Convolutional Neural Networks (CNNs) are the standard architecture for
computer vision tasks.
            """,
            "tags": ["computer-vision", "deep-learning"],
        },
        {
            "title": "Supervised Learning",
            "content": """
Supervised learning uses labeled training data to learn a mapping from
inputs to outputs. It's the most common type of machine learning.

Key algorithms:
- Linear regression
- Logistic regression
- Decision trees
- Support Vector Machines (SVM)
- Random forests

The training process involves minimizing a loss function using
optimization algorithms like gradient descent.
            """,
            "tags": ["supervised-learning", "machine-learning"],
        },
    ]

    # Ingest notes
    for note in notes:
        await kernel.remember(
            content=note["content"],
            title=note["title"],
            tags=note["tags"],
            memory_type="semantic",
        )

    print(f"✅ Created {len(notes)} notes in the vault")

    # Step 2: Analyze content structure
    print("\n" + "=" * 70)
    print("STEP 2: Analyze Content Structure")
    print("=" * 70)

    analyzer = ContentAnalyzer(kernel)

    # Analyze the first note
    note = notes[0]
    print(f"\n📝 Analyzing: {note['title']}")

    structure = analyzer.analyze_structure(note["content"])
    content_type = analyzer.detect_content_type(note["content"])
    keywords = analyzer.extract_keywords(note["content"], max_keywords=5)

    print("\n📊 Structure Analysis:")
    print(f"   Headings: {len(structure['headings'])}")
    print(f"   Lists: {len(structure['lists'])}")
    print(f"   Links: {len(structure['links'])}")
    print(f"   Content type: {content_type}")
    print(f"   Top keywords: {', '.join(keywords[:5])}")

    # Step 3: Suggest and apply tags
    print("\n" + "=" * 70)
    print("STEP 3: Suggest and Apply Tags")
    print("=" * 70)

    tagger = AutoTagger(kernel, min_confidence=0.3, max_suggestions=5)

    # Create a new note that needs tags
    new_note_content = """
Transformers are the dominant architecture in modern NLP. They use attention
mechanisms to process sequential data in parallel, unlike RNNs. This makes
them much faster and more effective.

Key innovations:
- Self-attention mechanism
- Positional encoding
- Multi-head attention

Models like BERT, GPT, and T5 are all based on the transformer architecture.
They have achieved state-of-the-art results across many NLP benchmarks.
    """

    print("\n📝 Analyzing new note about Transformers...")

    tag_suggestions = await tagger.suggest_tags(
        content=new_note_content, title="Transformer Architecture", existing_tags=[]
    )

    print(f"\n💡 Found {len(tag_suggestions)} tag suggestions:")
    for i, suggestion in enumerate(tag_suggestions, 1):
        print(f"   {i}. '{suggestion.tag}' (confidence: {suggestion.confidence:.2%})")
        print(f"      Reason: {suggestion.reason}")

    # Apply high-confidence tags
    applied_tags = [s.tag for s in tag_suggestions if s.confidence >= 0.5]
    print(f"\n✅ Applied {len(applied_tags)} high-confidence tags: {applied_tags}")

    # Record feedback
    for tag in applied_tags:
        tagger.record_feedback(tag, accepted=True)

    # Add the note to kernel with tags
    await kernel.remember(
        content=new_note_content,
        title="Transformer Architecture",
        tags=applied_tags,
        memory_type="semantic",
    )

    # Step 4: Suggest and apply links
    print("\n" + "=" * 70)
    print("STEP 4: Suggest and Apply Links")
    print("=" * 70)

    suggester = LinkSuggester(kernel, min_confidence=0.3, max_suggestions=10)

    print("\n🔗 Finding link suggestions for 'Transformer Architecture'...")

    link_suggestions = await suggester.suggest_links(
        content=new_note_content, title="Transformer Architecture", existing_links=[]
    )

    print(f"\n💡 Found {len(link_suggestions)} link suggestions:")

    high_confidence_links = []
    bidirectional_links = []

    for i, suggestion in enumerate(link_suggestions[:5], 1):
        bidirectional = "↔️" if suggestion.is_bidirectional else "→"
        print(f"   {i}. {bidirectional} [[{suggestion.target_title}]]")
        print(f"      Confidence: {suggestion.confidence:.2%}")
        print(f"      Reason: {suggestion.reason}")

        if suggestion.confidence >= 0.6:
            high_confidence_links.append(suggestion.target_title)
        if suggestion.is_bidirectional:
            bidirectional_links.append(suggestion.target_title)

    print(f"\n✅ Would apply {len(high_confidence_links)} high-confidence links")
    print(f"🔄 {len(bidirectional_links)} bidirectional opportunities found")

    # Record feedback
    for link in high_confidence_links:
        suggester.record_feedback(link, accepted=True)

    # Step 5: Detect and address knowledge gaps
    print("\n" + "=" * 70)
    print("STEP 5: Detect and Address Knowledge Gaps")
    print("=" * 70)

    detector = GapDetector(kernel, min_severity=0.3)

    print("\n🔍 Analyzing knowledge base for gaps...")

    gaps = await detector.detect_gaps(min_severity=0.3)

    print(f"\n💡 Found {len(gaps)} knowledge gaps:")

    # Group by type
    gaps_by_type = {}
    for gap in gaps:
        if gap.gap_type not in gaps_by_type:
            gaps_by_type[gap.gap_type] = []
        gaps_by_type[gap.gap_type].append(gap)

    for gap_type, type_gaps in gaps_by_type.items():
        print(f"\n   📊 {gap_type.replace('_', ' ').title()}: {len(type_gaps)} gaps")
        for gap in type_gaps[:2]:
            severity_emoji = (
                "🔴" if gap.severity >= 0.7 else "🟡" if gap.severity >= 0.5 else "🟢"
            )
            print(f"      {severity_emoji} {gap.topic} (severity: {gap.severity:.2%})")
            print(f"         {gap.suggestion}")

    # Comprehensive analysis
    print("\n📊 Performing comprehensive analysis...")
    analysis = await detector.analyze_knowledge_base()

    print("\n📈 Knowledge Base Summary:")
    print(f"   Total notes: {analysis['total_notes']}")
    print(f"   Topic clusters: {len(analysis['topic_clusters'])}")
    print(f"   Isolated notes: {analysis['isolated_notes']}")
    print(f"   Learning paths: {len(analysis['learning_paths'])}")

    # Show top clusters
    print("\n🗂️  Top Topic Clusters:")
    for cluster in analysis["topic_clusters"][:3]:
        print(f"   - {cluster.topic}: {len(cluster.notes)} notes")
        print(f"     Density: {cluster.density:.2%}, Coverage: {cluster.coverage:.2%}")

    # Show learning paths
    if analysis["learning_paths"]:
        print("\n🎓 Suggested Learning Path:")
        path = analysis["learning_paths"][0]
        print(f"   Goal: {path.goal}")
        print(f"   Steps: {len(path.steps)}")
        print(f"   Estimated time: {path.estimated_hours} hours")

    # Step 6: Summary and recommendations
    print("\n" + "=" * 70)
    print("STEP 6: Summary and Recommendations")
    print("=" * 70)

    # Get statistics from all features
    tag_stats = tagger.get_tag_stats()
    link_stats = suggester.get_link_stats()

    print("\n📊 Workflow Statistics:")
    print("\n   ContentAnalyzer:")
    print(f"   - Analyzed {len(notes)} notes")
    print("   - Extracted structure and keywords")

    print("\n   AutoTagger:")
    print(f"   - Made {tag_stats['total_suggestions']} tag suggestions")
    print(f"   - Applied {len(applied_tags)} tags")
    print(f"   - Acceptance rate: {tag_stats['acceptance_rate']:.1%}")

    print("\n   LinkSuggester:")
    print(f"   - Made {link_stats['total_suggestions']} link suggestions")
    print(f"   - Found {len(high_confidence_links)} high-confidence links")
    print(f"   - Found {len(bidirectional_links)} bidirectional opportunities")

    print("\n   GapDetector:")
    print(f"   - Identified {len(gaps)} knowledge gaps")
    print(f"   - Clustered into {len(analysis['topic_clusters'])} topics")
    print(f"   - Generated {len(analysis['learning_paths'])} learning paths")

    print("\n💡 Recommendations:")
    print(
        f"   1. Address {len([g for g in gaps if g.severity >= 0.7])} critical gaps first"
    )
    print(
        f"   2. Apply {len(high_confidence_links)} suggested links to strengthen graph"
    )
    print(f"   3. Connect {analysis['isolated_notes']} isolated notes")
    print("   4. Follow learning paths to fill knowledge gaps systematically")
    print("   5. Re-run analysis after making changes to track progress")

    print("\n" + "=" * 70)
    print("✅ Complete AI Workflow Example Finished!")
    print("=" * 70)

    print("\n🎯 Next Steps:")
    print("   1. Run this workflow on your own vault")
    print("   2. Review and apply AI suggestions")
    print("   3. Provide feedback to improve future suggestions")
    print("   4. Iterate: add content → analyze → improve → repeat")
    print("   5. Use CLI commands for quicker interactions:")
    print("      - memograph suggest-tags <note>")
    print("      - memograph suggest-links <note>")
    print("      - memograph detect-gaps")
    print("      - memograph analyze-knowledge")


if __name__ == "__main__":
    asyncio.run(main())
