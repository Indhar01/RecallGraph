"""
Example: Using GapDetector to find knowledge gaps.

This example demonstrates:
- Creating a GapDetector instance
- Detecting different types of knowledge gaps
- Understanding gap severity and types
- Analyzing topic clusters
- Generating learning paths
- Performing comprehensive knowledge base analysis

Requirements:
- A vault with multiple notes already ingested
- Larger vaults (20+ notes) show better gap detection
"""

import asyncio
from pathlib import Path
from memograph import MemoryKernel
from memograph.ai import GapDetector


async def main():
    # Initialize the memory kernel with your vault
    vault_path = "./my_vault"  # Change this to your vault path
    kernel = MemoryKernel(vault_path)
    
    print("🔍 GapDetector Example")
    print("=" * 50)
    
    # Ingest notes if vault exists
    if Path(vault_path).exists():
        print(f"\n📚 Ingesting notes from {vault_path}...")
        await kernel.ingest(vault_path)
        print(f"✅ Ingested {len(kernel.memories)} notes")
    else:
        print(f"\n⚠️  Vault not found: {vault_path}")
        print("Creating sample notes for demonstration...")
        
        # Create sample notes with intentional gaps
        await kernel.remember(
            content="Machine learning is a subset of AI that enables computers to learn from data.",
            title="Machine Learning",
            tags=["machine-learning", "ai"],
            memory_type="semantic"
        )
        
        await kernel.remember(
            content="Deep learning uses neural networks with multiple layers. It has revolutionized computer vision and NLP.",
            title="Deep Learning",
            tags=["deep-learning", "ai", "neural-networks"],
            memory_type="semantic"
        )
        
        await kernel.remember(
            content="Supervised learning uses labeled data. Common algorithms include decision trees and SVM.",
            title="Supervised Learning",
            tags=["supervised-learning", "machine-learning"],
            memory_type="semantic"
        )
        
        await kernel.remember(
            content="Reinforcement learning agents learn by interacting with environments. Key concepts include rewards and policies.",
            title="Reinforcement Learning",
            tags=["reinforcement-learning", "machine-learning"],
            memory_type="semantic"
        )
        
        # Isolated note
        await kernel.remember(
            content="Quantum computing uses quantum mechanics principles for computation.",
            title="Quantum Computing Basics",
            tags=["quantum-computing"],
            memory_type="semantic"
        )
        
        # Note that mentions topics without dedicated notes
        await kernel.remember(
            content="Neural networks consist of layers. CNNs are great for images, RNNs for sequences, and Transformers dominate NLP.",
            title="Neural Network Architectures",
            tags=["neural-networks", "deep-learning"],
            memory_type="semantic"
        )
        
        print("✅ Created 6 sample notes with intentional gaps")
    
    # Create a GapDetector instance
    print("\n🔍 Creating GapDetector...")
    detector = GapDetector(
        kernel=kernel,
        min_severity=0.3         # Detect gaps with >30% severity
    )
    
    # Example 1: Basic gap detection
    print("\n" + "=" * 50)
    print("Example 1: Detecting Knowledge Gaps")
    print("=" * 50)
    
    print("\n🔍 Analyzing vault for knowledge gaps...")
    gaps = await detector.detect_gaps(min_severity=0.3)
    
    print(f"\n💡 Found {len(gaps)} knowledge gaps:")
    
    # Group by gap type
    gaps_by_type = {}
    for gap in gaps:
        if gap.gap_type not in gaps_by_type:
            gaps_by_type[gap.gap_type] = []
        gaps_by_type[gap.gap_type].append(gap)
    
    for gap_type, type_gaps in gaps_by_type.items():
        print(f"\n📊 {gap_type.replace('_', ' ').title()} ({len(type_gaps)})")
        for gap in type_gaps[:3]:  # Show top 3 per type
            severity_emoji = "🔴" if gap.severity >= 0.7 else "🟡" if gap.severity >= 0.5 else "🟢"
            print(f"\n   {severity_emoji} {gap.topic}")
            print(f"      Severity: {gap.severity:.2%}")
            print(f"      Evidence: {gap.evidence}")
            print(f"      Suggestion: {gap.suggestion}")
    
    # Example 2: Understanding gap types
    print("\n" + "=" * 50)
    print("Example 2: Understanding Gap Types")
    print("=" * 50)
    
    print("\n📚 GapDetector identifies four types of gaps:")
    
    print("\n1. Missing Topics:")
    print("   - Topics mentioned in notes but not covered in detail")
    print("   - Example: 'CNNs' mentioned but no dedicated note exists")
    
    print("\n2. Weak Coverage:")
    print("   - Topics with minimal content")
    print("   - Example: Only one short note about an important topic")
    
    print("\n3. Isolated Notes:")
    print("   - Notes with few or no connections")
    print("   - Example: Note with 0 backlinks and 0 outgoing links")
    
    print("\n4. Missing Links:")
    print("   - Related notes that should be connected")
    print("   - Example: 'Deep Learning' and 'Neural Networks' don't link")
    
    # Example 3: Filtering by severity
    print("\n" + "=" * 50)
    print("Example 3: Filtering by Severity")
    print("=" * 50)
    
    critical_gaps = [g for g in gaps if g.severity >= 0.7]
    important_gaps = [g for g in gaps if 0.5 <= g.severity < 0.7]
    minor_gaps = [g for g in gaps if 0.3 <= g.severity < 0.5]
    
    print(f"\n🎯 Gap distribution by severity:")
    print(f"\n   🔴 Critical (≥0.7): {len(critical_gaps)} gaps")
    for gap in critical_gaps[:2]:
        print(f"      → {gap.topic} ({gap.severity:.2%})")
    
    print(f"\n   🟡 Important (0.5-0.7): {len(important_gaps)} gaps")
    for gap in important_gaps[:2]:
        print(f"      → {gap.topic} ({gap.severity:.2%})")
    
    print(f"\n   🟢 Minor (0.3-0.5): {len(minor_gaps)} gaps")
    for gap in minor_gaps[:2]:
        print(f"      → {gap.topic} ({gap.severity:.2%})")
    
    # Example 4: Comprehensive knowledge base analysis
    print("\n" + "=" * 50)
    print("Example 4: Comprehensive Analysis")
    print("=" * 50)
    
    print("\n📊 Performing comprehensive knowledge base analysis...")
    analysis = await detector.analyze_knowledge_base()
    
    print(f"\n📈 Knowledge Base Statistics:")
    print(f"   Total notes: {analysis['total_notes']}")
    print(f"   Total gaps: {len(analysis['gaps'])}")
    print(f"   Average note length: {analysis.get('avg_note_length', 0):.0f} chars")
    print(f"   Topic clusters: {len(analysis['topic_clusters'])}")
    print(f"   Isolated notes: {analysis['isolated_notes']}")
    
    # Example 5: Topic clustering
    print("\n" + "=" * 50)
    print("Example 5: Topic Clusters")
    print("=" * 50)
    
    print("\n🗂️  Topic Clusters:")
    
    for i, cluster in enumerate(analysis['topic_clusters'][:5], 1):
        print(f"\n{i}. Cluster: {cluster.topic}")
        print(f"   Notes: {len(cluster.notes)}")
        print(f"   Density: {cluster.density:.2%}")
        print(f"   Coverage: {cluster.coverage:.2%}")
        print(f"   Keywords: {', '.join(cluster.keywords[:5])}")
        
        if cluster.density < 0.3:
            print(f"   ⚠️  Low density - consider adding more connections")
        if cluster.coverage < 0.5:
            print(f"   ⚠️  Weak coverage - consider expanding content")
    
    # Example 6: Learning paths
    print("\n" + "=" * 50)
    print("Example 6: Learning Paths")
    print("=" * 50)
    
    print("\n🎓 Suggested Learning Paths:")
    
    for i, path in enumerate(analysis['learning_paths'][:3], 1):
        print(f"\n{i}. Goal: {path.goal}")
        print(f"   Prerequisites: {', '.join(path.prerequisites) if path.prerequisites else 'None'}")
        print(f"   Steps:")
        for j, step in enumerate(path.steps, 1):
            print(f"      {j}. {step}")
        print(f"   Estimated time: {path.estimated_hours} hours")
        print(f"   Difficulty: {path.difficulty}")
    
    # Example 7: Recording feedback
    print("\n" + "=" * 50)
    print("Example 7: Recording Feedback")
    print("=" * 50)
    
    print("\n📊 Recording feedback on gap suggestions...")
    
    if len(gaps) > 0:
        # Accept a gap
        accepted_gap = gaps[0]
        detector.record_feedback(accepted_gap.topic, accepted=True)
        print(f"✅ Accepted gap: '{accepted_gap.topic}'")
        print(f"   Action: Will create note about this topic")
    
    if len(gaps) > 1:
        # Reject a gap
        rejected_gap = gaps[1]
        detector.record_feedback(rejected_gap.topic, accepted=False)
        print(f"❌ Rejected gap: '{rejected_gap.topic}'")
        print(f"   Reason: Not relevant to my knowledge base focus")
    
    # Example 8: Best practices
    print("\n" + "=" * 50)
    print("Example 8: Best Practices")
    print("=" * 50)
    
    print("\n💡 Best Practices for GapDetector:")
    print("   1. Focus on critical gaps (≥0.7) first")
    print("   2. Use topic clusters to identify knowledge domains")
    print("   3. Follow learning paths for structured improvement")
    print("   4. Address isolated notes by adding connections")
    print("   5. Re-run analysis periodically as your vault grows")
    print("   6. Combine with LinkSuggester to fix missing links")
    print("   7. Use weak coverage as a guide for expanding notes")
    print("   8. Don't try to fix all gaps at once - prioritize")
    
    # Example 9: Configuration options
    print("\n" + "=" * 50)
    print("Example 9: Configuration Options")
    print("=" * 50)
    
    print("\n⚙️  Different configuration options:")
    
    # Strict detection (only critical gaps)
    strict_detector = GapDetector(kernel=kernel, min_severity=0.7)
    strict_gaps = await strict_detector.detect_gaps()
    print(f"\n   Strict Detector (min_severity=0.7)")
    print(f"   → Found {len(strict_gaps)} critical gaps only")
    
    # Permissive detection (all gaps)
    permissive_detector = GapDetector(kernel=kernel, min_severity=0.1)
    permissive_gaps = await permissive_detector.detect_gaps()
    print(f"\n   Permissive Detector (min_severity=0.1)")
    print(f"   → Found {len(permissive_gaps)} gaps total")
    
    print("\n" + "=" * 50)
    print("✅ GapDetector example complete!")
    print("=" * 50)
    
    print("\n💡 Next steps:")
    print("   1. Review critical gaps and plan which to address")
    print("   2. Create notes for missing topics")
    print("   3. Expand notes with weak coverage")
    print("   4. Connect isolated notes")
    print("   5. Run analysis again to track progress")


if __name__ == "__main__":
    asyncio.run(main())