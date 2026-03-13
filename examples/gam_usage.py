"""
GAM (Graph Attention Memory) Usage Examples

This example demonstrates how to use MemoGraph's GAM features for
enhanced memory retrieval with attention-based scoring.
"""

from memograph import MemoryKernel, MemoryType
from memograph.core.gam_scorer import GAMConfig


def basic_gam_usage():
    """Basic GAM usage example."""
    print("=" * 60)
    print("Basic GAM Usage")
    print("=" * 60)

    # Enable GAM with default configuration
    kernel = MemoryKernel("./test_vault", use_gam=True)

    # Create some test memories
    kernel.remember(
        title="Python Best Practices",
        content="Use list comprehensions for better performance. Follow PEP 8 style guide.",
        memory_type=MemoryType.SEMANTIC,
        tags=["python", "programming", "best-practices"],
        salience=0.8,
    )

    kernel.remember(
        title="Python Performance Tips",
        content="Use generators for memory efficiency. Profile code before optimizing. [[Python Best Practices]] are important.",
        memory_type=MemoryType.PROCEDURAL,
        tags=["python", "performance"],
        salience=0.7,
    )

    kernel.remember(
        title="Code Review Notes",
        content="Team meeting discussed [[Python Best Practices]]. Need to refactor module X.",
        memory_type=MemoryType.EPISODIC,
        tags=["meeting", "code-review"],
        salience=0.6,
    )

    # Ingest memories
    stats = kernel.ingest()
    print(f"\nIndexed {stats['indexed']} memories")

    # Retrieve with GAM scoring
    print("\nRetrieving memories about 'python best practices'...")
    nodes = kernel.retrieve_nodes("python best practices", top_k=3)

    print(f"\nFound {len(nodes)} memories:")
    for i, node in enumerate(nodes, 1):
        print(f"{i}. {node.title} (salience: {node.salience:.2f})")
        print(f"   Type: {node.memory_type.value}")
        print(f"   Tags: {', '.join(node.tags)}")

    print("\n✅ GAM automatically ranked memories using:")
    print("   - Graph relationships (wikilinks)")
    print("   - Co-access patterns")
    print("   - Recency decay")
    print("   - Salience scores")


def custom_gam_config():
    """Using custom GAM configuration."""
    print("\n" + "=" * 60)
    print("Custom GAM Configuration")
    print("=" * 60)

    # Create custom GAM configuration
    # Prioritize recent memories and relationships
    config = GAMConfig(
        relationship_weight=0.4,  # Strong emphasis on graph connections
        recency_weight=0.3,  # Prioritize recent memories
        salience_weight=0.3,  # Standard importance
        co_access_weight=0.0,  # Disable until we have data
        recency_decay_days=15.0,  # Faster decay (15 days half-life)
    )

    kernel = MemoryKernel("./test_vault", use_gam=True, gam_config=config)
    kernel.ingest()

    print("\nCustom GAM weights:")
    print(f"  Relationship: {config.relationship_weight}")
    print(f"  Recency: {config.recency_weight}")
    print(f"  Salience: {config.salience_weight}")
    print(f"  Co-access: {config.co_access_weight}")
    print(f"  Decay half-life: {config.recency_decay_days} days")

    nodes = kernel.retrieve_nodes("python", top_k=3)
    print(f"\nRetrieved {len(nodes)} memories with custom scoring")


def gam_with_explanation():
    """Explain GAM scoring decisions."""
    print("\n" + "=" * 60)
    print("GAM Score Explanation")
    print("=" * 60)

    kernel = MemoryKernel("./test_vault", use_gam=True)
    kernel.ingest()

    # Get detailed explanation of why memories were ranked
    explanation = kernel.explain_retrieval("python", top_k=3)

    print(f"\nQuery: '{explanation['query']}'")
    print(f"Candidates found: {explanation['candidates_found']}")
    print("\nGAM Configuration:")
    for key, value in explanation["gam_config"].items():
        print(f"  {key}: {value}")

    print("\n" + "-" * 60)
    print("Top Results with Score Breakdown:")
    print("-" * 60)

    for result in explanation["results"]:
        print(f"\n📄 {result['node_title']}")
        print(f"   Final Score: {result['final_score']:.4f}")

        comps = result["components"]
        print("\n   Component Contributions:")
        print(
            f"   - Relationship: {comps['relationship']['score']:.4f} × {comps['relationship']['weight']:.2f} = {comps['relationship']['contribution']:.4f}"
        )
        print(
            f"   - Co-access:    {comps['co_access']['score']:.4f} × {comps['co_access']['weight']:.2f} = {comps['co_access']['contribution']:.4f}"
        )
        print(
            f"   - Recency:      {comps['recency']['score']:.4f} × {comps['recency']['weight']:.2f} = {comps['recency']['contribution']:.4f}"
        )
        print(
            f"   - Salience:     {comps['salience']['score']:.4f} × {comps['salience']['weight']:.2f} = {comps['salience']['contribution']:.4f}"
        )


def gam_access_statistics():
    """View GAM access tracking statistics."""
    print("\n" + "=" * 60)
    print("GAM Access Statistics")
    print("=" * 60)

    kernel = MemoryKernel("./test_vault", use_gam=True)
    kernel.ingest()

    # Perform some queries to build access patterns
    print("\nPerforming queries to build access patterns...")
    kernel.retrieve_nodes("python", top_k=3)
    kernel.retrieve_nodes("best practices", top_k=3)
    kernel.retrieve_nodes("performance", top_k=3)

    # Get statistics
    stats = kernel.get_gam_statistics()

    print("\nAccess Tracking Statistics:")
    print(f"  Total queries: {stats['total_queries']}")
    print(f"  Nodes tracked: {stats['nodes_tracked']}")
    print(f"  Relationships tracked: {stats['relationships_tracked']}")
    print(f"  History size: {stats['history_size']}")

    if stats["most_accessed_nodes"]:
        print("\n  Most Accessed Memories:")
        for node_id, count in stats["most_accessed_nodes"][:5]:
            print(f"    - {node_id}: {count} accesses")


def compare_with_without_gam():
    """Compare retrieval with and without GAM."""
    print("\n" + "=" * 60)
    print("Comparison: With vs Without GAM")
    print("=" * 60)

    # Without GAM (standard hybrid retrieval)
    print("\n1. Standard Retrieval (No GAM):")
    kernel_standard = MemoryKernel("./test_vault", use_gam=False)
    kernel_standard.ingest()

    nodes_standard = kernel_standard.retrieve_nodes("python", top_k=3)
    print("   Results:")
    for i, node in enumerate(nodes_standard, 1):
        print(f"   {i}. {node.title}")

    # With GAM
    print("\n2. GAM-Enhanced Retrieval:")
    kernel_gam = MemoryKernel("./test_vault", use_gam=True)
    kernel_gam.ingest()

    nodes_gam = kernel_gam.retrieve_nodes("python", top_k=3)
    print("   Results:")
    for i, node in enumerate(nodes_gam, 1):
        print(f"   {i}. {node.title}")

    print("\n✨ GAM provides more nuanced ranking by considering:")
    print("   - Temporal relevance (recency decay)")
    print("   - Usage patterns (co-access tracking)")
    print("   - Graph structure (relationship strength)")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("MemoGraph GAM Usage Examples")
    print("=" * 60)

    try:
        basic_gam_usage()
        custom_gam_config()
        gam_with_explanation()
        gam_access_statistics()
        compare_with_without_gam()

        print("\n" + "=" * 60)
        print("✅ All examples completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
