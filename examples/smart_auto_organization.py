"""
Smart Auto-Organization Engine Example

This example demonstrates how to use MemoGraph's Smart Auto-Organization Engine
to automatically extract structured information from memories.

The engine extracts:
- Topics and subtopics
- People with their roles
- Organizations/teams
- Action items with assignees and deadlines
- Decisions made
- Open questions
- Sentiment/tone
- Timeline events
- External references
- Ideas brainstormed
- Risks and blockers
- Recurring themes
"""

import os
from pathlib import Path

from memograph import EntityType, MemoryKernel, MemoryType
from memograph.adapters.llm.claude import ClaudeLLMClient, ClaudeLLMConfig

# Or use Ollama:
# from memograph.adapters.llm.ollama import OllamaLLMClient, OllamaLLMConfig


def main():
    # Setup: Create a temporary vault for this example
    vault_path = Path("./temp_vault_auto_org")
    vault_path.mkdir(exist_ok=True)

    # Initialize LLM client (using Claude in this example)
    # Make sure you have ANTHROPIC_API_KEY set in your environment
    llm_client = ClaudeLLMClient()
    llm_config = ClaudeLLMConfig(
        model="claude-sonnet-4",
        max_tokens=2048,
        temperature=0.1,
    )

    # Initialize Memory Kernel with auto-extraction enabled
    print("📚 Initializing Memory Kernel with Smart Auto-Organization...")
    kernel = MemoryKernel(
        vault_path=str(vault_path),
        llm_client=llm_client,
        llm_config=llm_config,
        auto_extract=True,  # Enable automatic extraction
    )

    # Create a sample meeting memory
    print("\n✍️  Creating a sample meeting memory...")
    kernel.remember(
        title="Q1 Product Planning Meeting",
        content="""
        Meeting with Sarah Johnson (Product Manager) and Alex Chen (Tech Lead) from the 
        Engineering team.
        
        We discussed the new analytics dashboard feature for our SaaS platform. Sarah wants 
        to launch by March 15th to align with the marketing campaign.
        
        **Decisions Made:**
        - We'll use React and D3.js for the frontend visualization
        - Alex will lead the technical implementation
        - We'll use PostgreSQL for storing analytics data
        
        **Action Items:**
        - Alex to create technical design document (due Feb 28th) - HIGH PRIORITY
        - Sarah to prepare go-to-market materials (due March 1st)
        - John to set up CI/CD pipeline (due March 5th)
        - Everyone to review security requirements
        
        **Open Questions:**
        - Do we need real-time updates or is near-real-time sufficient?
        - What's the total budget allocated for this project?
        - Should we include mobile responsive design in v1?
        
        The meeting was very productive overall. There's some concern about the aggressive 
        timeline, but the team is excited about the feature.
        
        **References:**
        - Figma designs: https://figma.com/file/xyz123
        - API documentation: https://api.example.com/docs/analytics
        - Competitor analysis: https://docs.google.com/spreadsheets/abc
        
        **Ideas Discussed:**
        - Could add AI-powered insights and anomaly detection (high feasibility)
        - Mobile app version might be valuable for executives (medium feasibility)
        - Integration with Slack for notifications (low effort, high value)
        - Custom dashboard builder for enterprise clients
        
        **Risks Identified:**
        - Timeline is very aggressive given current team capacity (HIGH PRIORITY)
        - D3.js learning curve might slow down initial development (MEDIUM)
        - Third-party API rate limits could be an issue (MEDIUM)
        
        **Recurring Themes:**
        This continues the pattern we've seen across Q4 projects - aggressive timelines 
        with resource constraints. We need to address staffing in the next planning cycle.
        """,
        memory_type=MemoryType.EPISODIC,
        tags=["meeting", "product", "engineering", "q1-2024"],
    )

    # Ingest memories with auto-extraction
    print("\n🔄 Ingesting memories and extracting entities...")
    stats = kernel.ingest(auto_extract=True)
    
    print(f"\n📊 Ingestion Statistics:")
    print(f"   - Memories indexed: {stats['indexed']}")
    print(f"   - Total memories: {stats['total']}")
    print(f"   - Entities extracted: {stats['entities_extracted']}")

    # Retrieve all memories
    memories = kernel.graph.all_nodes()
    if not memories:
        print("\n⚠️  No memories found!")
        return

    memory = memories[0]
    print(f"\n📝 Analyzing memory: '{memory.title}'")

    # Get entities for this memory
    entities = kernel.get_entities(memory_id=memory.id)
    print(f"\n🎯 Total entities extracted: {len(entities)}")

    # Get entities by type
    topics = kernel.get_entities(memory_id=memory.id, entity_type=EntityType.TOPIC)
    people = kernel.get_entities(memory_id=memory.id, entity_type=EntityType.PERSON)
    actions = kernel.get_entities(memory_id=memory.id, entity_type=EntityType.ACTION_ITEM)
    decisions = kernel.get_entities(memory_id=memory.id, entity_type=EntityType.DECISION)
    questions = kernel.get_entities(memory_id=memory.id, entity_type=EntityType.QUESTION)
    risks = kernel.get_entities(memory_id=memory.id, entity_type=EntityType.RISK)
    ideas = kernel.get_entities(memory_id=memory.id, entity_type=EntityType.IDEA)
    refs = kernel.get_entities(memory_id=memory.id, entity_type=EntityType.REFERENCE)
    
    # Display extracted topics
    if topics:
        print(f"\n📌 Topics ({len(topics)}):")
        for topic in topics:
            print(f"   - {topic.name}: {topic.description}")
            print(f"     Confidence: {topic.confidence:.2f}")

    # Display extracted people
    if people:
        print(f"\n👥 People ({len(people)}):")
        for person in people:
            role = person.metadata.get('role', 'unknown')
            org = person.metadata.get('organization', 'N/A')
            print(f"   - {person.name} ({role})")
            print(f"     Organization: {org}")

    # Display action items
    if actions:
        print(f"\n✅ Action Items ({len(actions)}):")
        for action in actions:
            assignee = action.metadata.get('assignee', 'Unassigned')
            deadline = action.metadata.get('deadline', 'No deadline')
            priority = action.metadata.get('priority', 'medium')
            print(f"   - [{priority.upper()}] {action.description[:60]}...")
            print(f"     Assignee: {assignee}, Deadline: {deadline}")

    # Display decisions
    if decisions:
        print(f"\n🎯 Decisions ({len(decisions)}):")
        for decision in decisions:
            maker = decision.metadata.get('decision_maker', 'Team')
            print(f"   - {decision.description}")
            print(f"     Decision maker: {maker}")

    # Display open questions
    if questions:
        print(f"\n❓ Open Questions ({len(questions)}):")
        for q in questions:
            status = q.metadata.get('status', 'unresolved')
            print(f"   - [{status.upper()}] {q.description}")

    # Display risks
    if risks:
        print(f"\n⚠️  Risks ({len(risks)}):")
        for risk in risks:
            priority = risk.metadata.get('priority', 'medium')
            mitigation = risk.metadata.get('mitigation', 'None')
            print(f"   - [{priority.upper()}] {risk.description}")
            print(f"     Mitigation: {mitigation}")

    # Display ideas
    if ideas:
        print(f"\n💡 Ideas ({len(ideas)}):")
        for idea in ideas:
            feasibility = idea.metadata.get('feasibility', 'unknown')
            print(f"   - {idea.description[:60]}... (Feasibility: {feasibility})")

    # Display references
    if refs:
        print(f"\n🔗 References ({len(refs)}):")
        for ref in refs:
            url = ref.metadata.get('url', 'N/A')
            print(f"   - {ref.name}: {url}")

    # Demonstrate manual extraction for a specific memory
    print("\n\n🔍 Manual Extraction Example:")
    print("   You can also manually extract from a specific memory...")
    
    extraction_stats = kernel.extract_from_memory(memory.id)
    print(f"   Extraction complete!")
    print(f"   - Topics: {extraction_stats['topics']}")
    print(f"   - People: {extraction_stats['people']}")
    print(f"   - Action Items: {extraction_stats['action_items']}")
    print(f"   - Decisions: {extraction_stats['decisions']}")
    print(f"   - Questions: {extraction_stats['questions']}")
    print(f"   - Risks: {extraction_stats['risks']}")

    print("\n✨ Smart Auto-Organization complete!")
    print(f"\n💾 Vault location: {vault_path}")


if __name__ == "__main__":
    # Check if API key is set
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️  Warning: ANTHROPIC_API_KEY not set. Set it to use Claude.")
        print("   export ANTHROPIC_API_KEY='your-api-key'")
        print("\n   Alternatively, use Ollama by modifying the example.")
    else:
        main()