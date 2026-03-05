
# core/extractor.py
import json
import re
from datetime import datetime
from typing import Any, Protocol

from .entity import (
    ActionItemEntity,
    DecisionEntity,
    EntityNode,
    ExtractionResult,
    IdeaEntity,
    OrganizationEntity,
    PersonEntity,
    QuestionEntity,
    RecurringThemeEntity,
    ReferenceEntity,
    RiskEntity,
    SentimentEntity,
    TimelineEntity,
    TopicEntity,
)
from .enums import EntityType, ParticipantRole, PriorityLevel, SentimentType, StatusType
from .node import MemoryNode


class LLMAdapter(Protocol):
    """Protocol for LLM adapters used in extraction."""

    def generate(self, prompt: str, config: Any) -> str:
        """Generate text from a prompt."""
        ...


EXTRACTION_PROMPT_TEMPLATE = """
You are an advanced memory organization AI. Analyze the following memory and extract structured information.

**Memory Content:**
Title: {title}
Type: {memory_type}
Content:
{content}

**Task:**
Extract and structure the following information from the memory in JSON format:

1. **Main Topics** - The primary subject(s) discussed (1-3 topics)
2. **Subtopics** - Secondary or nested concepts (0-5 subtopics)
3. **People** - Individuals mentioned with their roles (organizer, participant, decision_maker, etc.)
4. **Organizations** - Companies, teams, or departments mentioned
5. **Action Items** - Tasks with assignee, deadline, priority (critical/high/medium/low)
6. **Decisions** - Explicit decisions made, who made them, and why
7. **Questions** - Open/unresolved questions
8. **Sentiment** - Overall tone (positive, negative, neutral, tense, productive, chaotic, collaborative, urgent)
9. **Timeline** - Dates, deadlines, or events mentioned
10. **References** - URLs, documents, tools, or external resources
11. **Ideas** - Brainstormed or proposed ideas
12. **Risks** - Potential problems, blockers, or concerns identified
13. **Recurring Themes** - Themes that might connect to other memories

**Output Format (JSON):**
{{
  "topics": [
    {{"name": "Topic Name", "description": "Brief description", "confidence": 0.9}}
  ],
  "subtopics": [
    {{"name": "Subtopic", "description": "Details", "parent_topic": "Topic Name"}}
  ],
  "people": [
    {{"name": "Person Name", "role": "participant|organizer|decision_maker", "organization": "Org Name or null"}}
  ],
  "organizations": [
    {{"name": "Org Name", "department": "Department or null"}}
  ],
  "action_items": [
    {{
      "description": "Task description",
      "assignee": "Person name or null",
      "deadline": "ISO date or null",
      "priority": "critical|high|medium|low",
      "status": "open|in_progress|completed|blocked"
    }}
  ],
  "decisions": [
    {{
      "description": "Decision made",
      "decision_maker": "Person or null",
      "rationale": "Why this was decided"
    }}
  ],
  "questions": [
    {{
      "question": "The question text",
      "asked_by": "Person or null",
      "status": "unresolved|resolved"
    }}
  ],
  "sentiment": {{
    "type": "positive|negative|neutral|tense|productive|chaotic|collaborative|urgent",
    "intensity": 0.7,
    "description": "Brief explanation"
  }},
  "timeline": [
    {{
      "description": "Event description",
      "date": "ISO date or null",
      "event_type": "deadline|milestone|meeting|general"
    }}
  ],
  "references": [
    {{
      "name": "Reference name",
      "url": "URL or null",
      "type": "url|document|tool|api"
    }}
  ],
  "ideas": [
    {{
      "description": "Idea description",
      "category": "Category or null",
      "feasibility": "high|medium|low|null"
    }}
  ],
  "risks": [
    {{
      "description": "Risk description",
      "priority": "critical|high|medium|low",
      "impact": "Potential impact",
      "mitigation": "Mitigation strategy or null"
    }}
  ],
  "recurring_themes": [
    {{
      "theme": "Theme name",
      "description": "Why this is a recurring theme"
    }}
  ]
}}

**Important:**
- Extract ONLY information explicitly mentioned or strongly implied
- Use null for missing information
- Be conservative with confidence scores
- If a section has no relevant information, return an empty array []
- Ensure all JSON is valid and properly formatted

Return ONLY the JSON object, no additional text.
"""


class SmartAutoOrganizer:
    """
    Smart Auto-Organization Engine that extracts rich structured information
    from memories using LLM analysis.
    """

    def __init__(self, llm_client: LLMAdapter, llm_config: Any = None):
        """
        Initialize the organizer with an LLM client.

        Args:
            llm_client: An LLM adapter (ClaudeLLMClient, OllamaLLMClient, etc.)
            llm_config: Configuration object for the LLM
        """
        self.llm_client = llm_client
        self.llm_config = llm_config

    def extract(self, memory: MemoryNode) -> ExtractionResult:
        """
        Extract structured entities from a memory node.

        Args:
            memory: The memory node to analyze

        Returns:
            ExtractionResult containing all extracted entities
        """
        # Construct the prompt
        prompt = EXTRACTION_PROMPT_TEMPLATE.format(
            title=memory.title,
            memory_type=memory.memory_type.value,
            content=memory.content,
        )

        # Generate extraction using LLM
        try:
            response = self.llm_client.generate(prompt, self.llm_config)
            extraction_data = self._parse_llm_response(response)
        except Exception as e:
            # If extraction fails, return empty result
            print(f"Extraction failed for {memory.id}: {e}")
            return ExtractionResult(memory_id=memory.id)

        # Convert JSON data to entity objects
        result = self._create_extraction_result(memory.id, extraction_data)
        return result

    def _parse_llm_response(self, response: str) -> dict[str, Any]:
        """Parse the LLM response to extract JSON."""
        # Try to find JSON in the response
        # Sometimes LLMs wrap JSON in markdown code blocks
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find raw JSON
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            json_str = json_match.group(0) if json_match else response

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {e}")
            print(f"Response: {response[:500]}...")
            return {}

    def _create_extraction_result(
        self, memory_id: str, data: dict[str, Any]
    ) -> ExtractionResult:
        """Convert parsed JSON data into entity objects."""
        result = ExtractionResult(memory_id=memory_id)

        # Extract topics
        for topic_data in data.get("topics", []):
            topic = TopicEntity(
                id=f"{memory_id}:topic:{self._slugify(topic_data['name'])}",
                entity_type=EntityType.TOPIC,
                name=topic_data["name"],
                description=topic_data.get("description", ""),
                source_memory_id=memory_id,
                confidence=topic_data.get("confidence", 1.0),
            )
            result.topics.append(topic)

        # Extract subtopics
        for subtopic_data in data.get("subtopics", []):
            subtopic = EntityNode(
                id=f"{memory_id}:subtopic:{self._slugify(subtopic_data['name'])}",
                entity_type=EntityType.SUBTOPIC,
                name=subtopic_data["name"],
                description=subtopic_data.get("description", ""),
                source_memory_id=memory_id,
            )
            subtopic.metadata["parent_topic"] = subtopic_data.get("parent_topic")
            result.subtopics.append(subtopic)

        # Extract people
        for person_data in data.get("people", []):
            role = self._parse_enum(person_data.get("role"), ParticipantRole, ParticipantRole.PARTICIPANT)
            person = PersonEntity(
                id=f"{memory_id}:person:{self._slugify(person_data['name'])}",
                entity_type=EntityType.PERSON,
                name=person_data["name"],
                description=f"Participant in {memory_id}",
                source_memory_id=memory_id,
                role=role,
            )
            person.metadata["organization"] = person_data.get("organization")
            result.people.append(person)

        # Extract organizations
        for org_data in data.get("organizations", []):
            org = OrganizationEntity(
                id=f"{memory_id}:org:{self._slugify(org_data['name'])}",
                entity_type=EntityType.ORGANIZATION,
                name=org_data["name"],
                description=f"Organization mentioned in {memory_id}",
                source_memory_id=memory_id,
            )
            org.metadata["department"] = org_data.get("department")
            result.organizations.append(org)

        # Extract action items
        for action_data in data.get("action_items", []):
            priority = self._parse_enum(action_data.get("priority"), PriorityLevel, PriorityLevel.MEDIUM)
            status = self._parse_enum(action_data.get("status"), StatusType, StatusType.OPEN)
            deadline = self._parse_date(action_data.get("deadline"))

            action = ActionItemEntity(
                id=f"{memory_id}:action:{self._slugify(action_data['description'][:50])}",
                entity_type=EntityType.ACTION_ITEM,
                name=action_data["description"][:100],
                description=action_data["description"],
                source_memory_id=memory_id,
                assignee=action_data.get("assignee"),
                deadline=deadline,
                priority=priority,
                status=status,
            )
            result.action_items.append(action)

        # Extract decisions
        for decision_data in data.get("decisions", []):
            decision = DecisionEntity(
                id=f"{memory_id}:decision:{self._slugify(decision_data['description'][:50])}",
                entity_type=EntityType.DECISION,
                name=decision_data["description"][:100],
                description=decision_data["description"],
                source_memory_id=memory_id,
                decision_maker=decision_data.get("decision_maker"),
                rationale=decision_data.get("rationale"),
            )
            result.decisions.append(decision)

        # Extract questions
        for question_data in data.get("questions", []):
            status = self._parse_enum(question_data.get("status"), StatusType, StatusType.UNRESOLVED)
            question = QuestionEntity(
                id=f"{memory_id}:question:{self._slugify(question_data['question'][:50])}",
                entity_type=EntityType.QUESTION,
                name=question_data["question"][:100],
                description=question_data["question"],
                source_memory_id=memory_id,
                status=status,
                asked_by=question_data.get("asked_by"),
            )
            result.questions.append(question)

        # Extract sentiment
        sentiment_data = data.get("sentiment", {})
        if sentiment_data and sentiment_data.get("type"):
            sentiment_type = self._parse_enum(sentiment_data.get("type"), SentimentType, SentimentType.NEUTRAL)
            sentiment = SentimentEntity(
                id=f"{memory_id}:sentiment",
                entity_type=EntityType.SENTIMENT,
                name=f"Sentiment: {sentiment_type.value}",
                description=sentiment_data.get("description", ""),
                source_memory_id=memory_id,
                sentiment_type=sentiment_type,
                intensity=float(sentiment_data.get("intensity", 0.5)),
            )
            result.sentiments.append(sentiment)

        # Extract timeline events
        for timeline_data in data.get("timeline", []):
            event_date = self._parse_date(timeline_data.get("date"))
            timeline = TimelineEntity(
                id=f"{memory_id}:timeline:{self._slugify(timeline_data['description'][:50])}",
                entity_type=EntityType.TIMELINE,
                name=timeline_data["description"][:100],
                description=timeline_data["description"],
                source_memory_id=memory_id,
                event_date=event_date,
                event_type=timeline_data.get("event_type", "general"),
            )
            result.timeline_events.append(timeline)

        # Extract references
        for ref_data in data.get("references", []):
            reference = ReferenceEntity(
                id=f"{memory_id}:ref:{self._slugify(ref_data['name'][:50])}",
                entity_type=EntityType.REFERENCE,
                name=ref_data["name"],
                description=ref_data.get("description", ""),
                source_memory_id=memory_id,
                url=ref_data.get("url"),
                reference_type=ref_data.get("type", "general"),
            )
            result.references.append(reference)

        # Extract ideas
        for idea_data in data.get("ideas", []):
            idea = IdeaEntity(
                id=f"{memory_id}:idea:{self._slugify(idea_data['description'][:50])}",
                entity_type=EntityType.IDEA,
                name=idea_data["description"][:100],
                description=idea_data["description"],
                source_memory_id=memory_id,
                category=idea_data.get("category"),
                feasibility=idea_data.get("feasibility"),
            )
            result.ideas.append(idea)

        # Extract risks
        for risk_data in data.get("risks", []):
            priority = self._parse_enum(risk_data.get("priority"), PriorityLevel, PriorityLevel.MEDIUM)
            risk = RiskEntity(
                id=f"{memory_id}:risk:{self._slugify(risk_data['description'][:50])}",
                entity_type=EntityType.RISK,
                name=risk_data["description"][:100],
                description=risk_data["description"],
                source_memory_id=memory_id,
                priority=priority,
                impact=risk_data.get("impact"),
                mitigation=risk_data.get("mitigation"),
            )
            result.risks.append(risk)

        # Extract recurring themes
        for theme_data in data.get("recurring_themes", []):
            theme = RecurringThemeEntity(
                id=f"{memory_id}:theme:{self._slugify(theme_data['theme'])}",
                entity_type=EntityType.RECURRING_THEME,
                name=theme_data["theme"],
                description=theme_data.get("description", ""),
                source_memory_id=memory_id,
            )
            result.recurring_themes.append(theme)

        return result

    @staticmethod
    def _slugify(text: str) -> str:
        """Convert text to a slug suitable for IDs."""
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
        return slug or "unnamed"

    @staticmethod
    def _parse_enum(value: str | None, enum_class: type, default):
        """Parse a string value into an enum, with fallback to default."""
        if not value:
            return default
        try:
            # Handle both "low" and "LOW" formats
            normalized = value.upper() if hasattr(enum_class, value.upper()) else value.lower()
            return enum_class[normalized.upper()] if hasattr(enum_class, normalized.upper()) else enum_class(normalized)
        except (KeyError, ValueError):
            return default

    @staticmethod
    def _parse_date(date_str: str | None) -> datetime | None:
        """Parse an ISO date string into a datetime object."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None
