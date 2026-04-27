#!/usr/bin/env python3
"""
MemoGraph Indexing Diagnostic Script

Run this to diagnose why memories show as "indexed: 0, skipped: N"
and to verify embedding configuration.
"""

import sys
from pathlib import Path


def run_diagnostics(vault_path: str = "./vault"):
    """Run comprehensive diagnostics on MemoGraph indexing."""

    print("=" * 60)
    print("MemoGraph Indexing Diagnostics")
    print("=" * 60)
    print()

    # Import MemoGraph
    try:
        from memograph import MemoryKernel
    except ImportError:
        print("❌ ERROR: MemoGraph not installed")
        print("   Install with: pip install memograph")
        return 1

    # Initialize kernel
    print(f"📂 Vault path: {vault_path}")
    kernel = MemoryKernel(vault_path=vault_path)

    vault_path_obj = Path(vault_path)
    if not vault_path_obj.exists():
        print(f"❌ Vault does not exist: {vault_path_obj}")
        return 1

    print(f"✅ Vault exists: {vault_path_obj.absolute()}")
    print()

    # Check embedding adapter
    print("-" * 60)
    print("EMBEDDING CONFIGURATION")
    print("-" * 60)

    has_embeddings = kernel.embedding_adapter is not None

    if has_embeddings:
        print(
            f"✅ Embedding adapter configured: {type(kernel.embedding_adapter).__name__}"
        )
    else:
        print("❌ NO EMBEDDING ADAPTER CONFIGURED")
        print()
        print("   This is the ROOT CAUSE of semantic search not working!")
        print()
        print("   📖 Solution: Configure an embedding adapter")
        print("      See INDEXING_TROUBLESHOOTING.md for setup instructions")
        print()
        print("   Quick fix - Install sentence-transformers:")
        print("      pip install memograph[embeddings]")
        print()
        print("   Then initialize kernel with embeddings:")
        print(
            "      from memograph.adapters.embeddings.sentence_transformers import SentenceTransformerEmbeddings"
        )
        print("      embeddings = SentenceTransformerEmbeddings()")
        print(
            "      kernel = MemoryKernel(vault_path='./vault', embedding_adapter=embeddings)"
        )
        print()

    # Check ingest stats
    print("-" * 60)
    print("INGEST STATISTICS")
    print("-" * 60)

    try:
        stats = kernel.ingest()
        print("✅ Ingest completed")
        print(f"   • Indexed: {stats['indexed']} (new or changed files)")
        print(f"   • Skipped: {stats['skipped']} (unchanged files from cache)")
        print(f"   • Total: {stats['total']} (total memories in graph)")
        print()

        if stats["indexed"] == 0 and stats["total"] > 0:
            print("ℹ️  NOTE: 'indexed: 0' means all files loaded from cache")
            print("   This is NORMAL and EFFICIENT for unchanged files")
            print()
            if not has_embeddings:
                print("   ⚠️  However, without embedding adapter, no embeddings exist")
                print("   After configuring embeddings, run: kernel.ingest(force=True)")
                print()
    except Exception as e:
        print(f"❌ Ingest failed: {e}")
        return 1

    # Check memory files
    print("-" * 60)
    print("MEMORY FILES")
    print("-" * 60)

    md_files = list(vault_path_obj.glob("*.md"))
    non_cache_files = [f for f in md_files if not f.name.startswith(".memograph")]

    print(f"✅ Found {len(non_cache_files)} memory files:")
    for md_file in non_cache_files[:10]:  # Show first 10
        size_kb = md_file.stat().st_size / 1024
        print(f"   • {md_file.name} ({size_kb:.1f} KB)")

    if len(non_cache_files) > 10:
        print(f"   ... and {len(non_cache_files) - 10} more")
    print()

    # Check embeddings in graph
    print("-" * 60)
    print("EMBEDDING STATUS")
    print("-" * 60)

    nodes_with_embeddings = 0
    total_nodes = 0

    for node in kernel.graph.all_nodes():
        total_nodes += 1
        if node.embedding is not None:
            nodes_with_embeddings += 1

    if total_nodes == 0:
        print("ℹ️  No memories in graph yet")
    else:
        print(f"Memories with embeddings: {nodes_with_embeddings}/{total_nodes}")
        print()

        if nodes_with_embeddings == 0:
            print("❌ NO EMBEDDINGS FOUND")
            print()
            print("   This confirms semantic/vector search will NOT work")
            print()
            print("   Solution:")
            print("   1. Configure embedding adapter (see above)")
            print("   2. Force re-index: kernel.ingest(force=True)")
            print()
        elif nodes_with_embeddings < total_nodes:
            print("⚠️  PARTIAL EMBEDDINGS")
            print(
                f"   {total_nodes - nodes_with_embeddings} memories missing embeddings"
            )
            print("   Run kernel.ingest(force=True) to regenerate all")
            print()
        else:
            print("✅ All memories have embeddings - semantic search ready!")
            print()

    # Check cache files
    print("-" * 60)
    print("CACHE FILES")
    print("-" * 60)

    cache_files = {
        ".memograph_cache.json": "File modification times",
        ".memograph_graph.json": "Cached graph structure",
        ".memograph_embeddings.json": "Cached embedding vectors",
    }

    for cache_file, description in cache_files.items():
        cache_path = vault_path_obj / cache_file
        if cache_path.exists():
            size_kb = cache_path.stat().st_size / 1024
            print(f"✅ {cache_file}")
            print(f"   {description}")
            print(f"   Size: {size_kb:.1f} KB")
        else:
            status = "⚠️ " if cache_file == ".memograph_embeddings.json" else "ℹ️ "
            print(f"{status} {cache_file} - NOT FOUND")
            if cache_file == ".memograph_embeddings.json" and not has_embeddings:
                print("   (Expected - no embedding adapter configured)")
    print()

    # Final summary
    print("=" * 60)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 60)
    print()

    if not has_embeddings:
        print("🔴 ISSUE IDENTIFIED: No embedding adapter configured")
        print()
        print("   Your memories are saved ✅")
        print("   But semantic search won't work ❌")
        print()
        print("   📖 Read INDEXING_TROUBLESHOOTING.md for detailed setup")
        print()
        print("   Quick start:")
        print("   1. pip install memograph[embeddings]")
        print("   2. Use kernel with embeddings (see troubleshooting guide)")
        print("   3. Run kernel.ingest(force=True)")
        print()
        return 1
    elif nodes_with_embeddings == 0 and total_nodes > 0:
        print("🟡 ISSUE: Embedding adapter configured but no embeddings generated")
        print()
        print("   Solution: Force re-index to generate embeddings")
        print("   Run: kernel.ingest(force=True)")
        print()
        return 1
    elif nodes_with_embeddings < total_nodes:
        print("🟡 WARNING: Some memories missing embeddings")
        print()
        print("   Solution: Force re-index")
        print("   Run: kernel.ingest(force=True)")
        print()
        return 0
    else:
        print("🟢 ALL CHECKS PASSED")
        print()
        print("   ✅ Embedding adapter configured")
        print("   ✅ All memories have embeddings")
        print("   ✅ Semantic search should work")
        print()
        print("   You can now use:")
        print("   • kernel.search('your query')")
        print("   • kernel.retrieve_nodes('your query')")
        print("   • kernel.context_window('your query')")
        print()
        return 0


if __name__ == "__main__":
    vault_path = sys.argv[1] if len(sys.argv) > 1 else "./vault"
    sys.exit(run_diagnostics(vault_path))
