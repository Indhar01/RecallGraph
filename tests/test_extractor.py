"""Tests for the Smart Auto-Organization Engine."""

import json

import pytest

from memograph.core.entity import (
    ActionItemEntity,
    DecisionEntity,
    EntityType,
    PersonEntity,
    QuestionEntity,
    TopicEntity,
)
from memograph.core.enums import (
    MemoryType,
    ParticipantRole,
    PriorityLevel,
    SentimentType,
    StatusType,
)
from memograph.core.extractor import SmartAutoOrganizer
from memograph.core.node import MemoryNode


class MockLLMClient:
    """Mock LLM client for testing."""

    def __init__(self, response: str | dict):
        """Initialize with a predefined response."""
        if isinstance(response, dict):
            self.response = json.dumps(response)
        else:
            self.response = response

    def generate(self, prompt: str, config=None) -> str:
        """Return the predefined response."""
        return self.response


class MockLLMConfig:
    """Mock LLM config for testing."""

    model = "test-model"
    max_tokens = 1024
    temperature = 0.1


@pytest.fixture
def sample_memory():
    """Create a sample memory node for testing."""
    return MemoryNode(
        id="test-meeting-2024",
        title="Product Planning Meeting",
        content="""
        Meeting with Sarah (product manager) and John (tech lead) from Engineering team.

        We discussed the new analytics dashboard feature. Sarah wants to launch by March 15th.

        Decisions:
        - We'll use React for the frontend
        - John will lead the implementation

        Action items:
        - John to create technical design doc (due March 1st)
        - Sarah to prepare marketing materials

        Open questions:
        - Do we need real-time updates?
        - What's the budget for this project?

        The meeting was productive overall. Some concerns about the tight timeline.

        References:
        - Figma design: https://figma.com/design/123
        - API docs: https://api.example.com/docs

        Ideas:
        - Could add AI-powered insights
        - Mobile app version might be valuable

        Risks:
        - Timeline is aggressive
        - Team capacity might be an issue
        """,
        memory_type=MemoryType.EPISODIC,
        tags=["meeting", "product", "engineering"],
    )


@pytest.fixture
def extraction_response():
    """Sample extraction response from LLM."""
    return {
        "topics": [
            {
                "name": "Analytics Dashboard",
                "description": "New feature for data visualization",
                "confidence": 0.9,
            }
        ],
        "subtopics": [
            {
                "name": "Frontend Technology",
                "description": "Choice of React framework",
                "parent_topic": "Analytics Dashboard",
            }
        ],
        "people": [
            {"name": "Sarah", "role": "organizer", "organization": "Product Team"},
            {"name": "John", "role": "decision_maker", "organization": "Engineering"},
        ],
        "organizations": [{"name": "Engineering team", "department": "Engineering"}],
        "action_items": [
            {
                "description": "Create technical design doc",
                "assignee": "John",
                "deadline": "2024-03-01T00:00:00",
                "priority": "high",
                "status": "open",
            },
            {
                "description": "Prepare marketing materials",
                "assignee": "Sarah",
                "deadline": None,
                "priority": "medium",
                "status": "open",
            },
        ],
        "decisions": [
            {
                "description": "Use React for the frontend",
                "decision_maker": "John",
                "rationale": "Team expertise and ecosystem",
            }
        ],
        "questions": [
            {"question": "Do we need real-time updates?", "asked_by": None, "status": "unresolved"},
            {"question": "What's the budget?", "asked_by": None, "status": "unresolved"},
        ],
        "sentiment": {
            "type": "productive",
            "intensity": 0.7,
            "description": "Meeting was productive with some concerns",
        },
        "timeline": [
            {
                "description": "Feature launch date",
                "date": "2024-03-15T00:00:00",
                "event_type": "deadline",
            }
        ],
        "references": [
            {"name": "Figma design", "url": "https://figma.com/design/123", "type": "url"},
            {"name": "API docs", "url": "https://api.example.com/docs", "type": "url"},
        ],
        "ideas": [
            {
                "description": "AI-powered insights",
                "category": "feature",
                "feasibility": "medium",
            },
            {
                "description": "Mobile app version",
                "category": "platform",
                "feasibility": "high",
            },
        ],
        "risks": [
            {
                "description": "Timeline is aggressive",
                "priority": "high",
                "impact": "May delay launch",
                "mitigation": "Add buffer time",
            },
            {
                "description": "Team capacity issue",
                "priority": "medium",
                "impact": "Quality concerns",
                "mitigation": "Hire contractor",
            },
        ],
        "recurring_themes": [
            {"theme": "Timeline pressure", "description": "Common concern across projects"}
        ],
    }


def test_extractor_initialization():
    """Test that the extractor can be initialized."""
    mock_client = MockLLMClient(response="{}")
    organizer = SmartAutoOrganizer(mock_client, MockLLMConfig())
    assert organizer.llm_client is not None
    assert organizer.llm_config is not None


def test_extract_basic(sample_memory, extraction_response):
    """Test basic extraction from a memory."""
    mock_client = MockLLMClient(response=extraction_response)
    organizer = SmartAutoOrganizer(mock_client, MockLLMConfig())

    result = organizer.extract(sample_memory)

    assert result.memory_id == "test-meeting-2024"
    assert result.entity_count() > 0


def test_extract_topics(sample_memory, extraction_response):
    """Test topic extraction."""
    mock_client = MockLLMClient(response=extraction_response)
    organizer = SmartAutoOrganizer(mock_client, MockLLMConfig())

    result = organizer.extract(sample_memory)

    assert len(result.topics) == 1
    topic = result.topics[0]
    assert isinstance(topic, TopicEntity)
    assert topic.name == "Analytics Dashboard"
    assert topic.entity_type == EntityType.TOPIC
    assert topic.source_memory_id == "test-meeting-2024"
    assert 0.0 <= topic.confidence <= 1.0


def test_extract_people(sample_memory, extraction_response):
    """Test people extraction."""
    mock_client = MockLLMClient(response=extraction_response)
    organizer = SmartAutoOrganizer(mock_client, MockLLMConfig())

    result = organizer.extract(sample_memory)

    assert len(result.people) == 2
    sarah = next(p for p in result.people if p.name == "Sarah")
    john = next(p for p in result.people if p.name == "John")

    assert isinstance(sarah, PersonEntity)
    assert sarah.role == ParticipantRole.ORGANIZER
    assert sarah.metadata["organization"] == "Product Team"

    assert isinstance(john, PersonEntity)
    assert john.role == ParticipantRole.DECISION_MAKER


def test_extract_action_items(sample_memory, extraction_response):
    """Test action item extraction."""
    mock_client = MockLLMClient(response=extraction_response)
    organizer = SmartAutoOrganizer(mock_client, MockLLMConfig())

    result = organizer.extract(sample_memory)

    assert len(result.action_items) == 2

    design_doc = next(a for a in result.action_items if "design doc" in a.description)
    assert isinstance(design_doc, ActionItemEntity)
    assert design_doc.assignee == "John"
    assert design_doc.priority == PriorityLevel.HIGH
    assert design_doc.status == StatusType.OPEN
    assert design_doc.deadline is not None


def test_extract_decisions(sample_memory, extraction_response):
    """Test decision extraction."""
    mock_client = MockLLMClient(response=extraction_response)
    organizer = SmartAutoOrganizer(mock_client, MockLLMConfig())

    result = organizer.extract(sample_memory)

    assert len(result.decisions) == 1
    decision = result.decisions[0]
    assert isinstance(decision, DecisionEntity)
    assert "React" in decision.description
    assert decision.decision_maker == "John"
    assert decision.rationale is not None


def test_extract_questions(sample_memory, extraction_response):
    """Test question extraction."""
    mock_client = MockLLMClient(response=extraction_response)
    organizer = SmartAutoOrganizer(mock_client, MockLLMConfig())

    result = organizer.extract(sample_memory)

    assert len(result.questions) == 2
    question = result.questions[0]
    assert isinstance(question, QuestionEntity)
    assert question.status == StatusType.UNRESOLVED


def test_extract_sentiment(sample_memory, extraction_response):
    """Test sentiment extraction."""
    mock_client = MockLLMClient(response=extraction_response)
    organizer = SmartAutoOrganizer(mock_client, MockLLMConfig())

    result = organizer.extract(sample_memory)

    assert len(result.sentiments) == 1
    sentiment = result.sentiments[0]
    assert sentiment.sentiment_type == SentimentType.PRODUCTIVE
    assert 0.0 <= sentiment.intensity <= 1.0


def test_extract_timeline(sample_memory, extraction_response):
    """Test timeline extraction."""
    mock_client = MockLLMClient(response=extraction_response)
    organizer = SmartAutoOrganizer(mock_client, MockLLMConfig())

    result = organizer.extract(sample_memory)

    assert len(result.timeline_events) == 1
    timeline = result.timeline_events[0]
    assert timeline.event_type == "deadline"
    assert timeline.event_date is not None


def test_extract_references(sample_memory, extraction_response):
    """Test reference extraction."""
    mock_client = MockLLMClient(response=extraction_response)
    organizer = SmartAutoOrganizer(mock_client, MockLLMConfig())

    result = organizer.extract(sample_memory)

    assert len(result.references) == 2
    figma_ref = next(r for r in result.references if "Figma" in r.name)
    assert figma_ref.url == "https://figma.com/design/123"
    assert figma_ref.reference_type == "url"


def test_extract_ideas(sample_memory, extraction_response):
    """Test idea extraction."""
    mock_client = MockLLMClient(response=extraction_response)
    organizer = SmartAutoOrganizer(mock_client, MockLLMConfig())

    result = organizer.extract(sample_memory)

    assert len(result.ideas) == 2
    ai_idea = next(i for i in result.ideas if "AI-powered" in i.description)
    assert ai_idea.category == "feature"
    assert ai_idea.feasibility == "medium"


def test_extract_risks(sample_memory, extraction_response):
    """Test risk extraction."""
    mock_client = MockLLMClient(response=extraction_response)
    organizer = SmartAutoOrganizer(mock_client, MockLLMConfig())

    result = organizer.extract(sample_memory)

    assert len(result.risks) == 2
    timeline_risk = next(r for r in result.risks if "Timeline" in r.description)
    assert timeline_risk.priority == PriorityLevel.HIGH
    assert timeline_risk.impact is not None
    assert timeline_risk.mitigation is not None


def test_extract_recurring_themes(sample_memory, extraction_response):
    """Test recurring theme extraction."""
    mock_client = MockLLMClient(response=extraction_response)
    organizer = SmartAutoOrganizer(mock_client, MockLLMConfig())

    result = organizer.extract(sample_memory)

    assert len(result.recurring_themes) == 1
    theme = result.recurring_themes[0]
    assert "Timeline pressure" in theme.name


def test_parse_json_in_markdown(sample_memory):
    """Test parsing JSON wrapped in markdown code blocks."""
    json_data = {"topics": [], "subtopics": [], "people": []}
    markdown_response = f"```json\n{json.dumps(json_data)}\n```"

    mock_client = MockLLMClient(response=markdown_response)
    organizer = SmartAutoOrganizer(mock_client, MockLLMConfig())

    result = organizer.extract(sample_memory)
    assert result.memory_id == sample_memory.id


def test_extract_with_empty_sections(sample_memory):
    """Test extraction when some sections are empty."""
    minimal_response = {
        "topics": [{"name": "Test Topic", "description": "Test", "confidence": 1.0}],
        "subtopics": [],
        "people": [],
        "organizations": [],
        "action_items": [],
        "decisions": [],
        "questions": [],
        "sentiment": {},
        "timeline": [],
        "references": [],
        "ideas": [],
        "risks": [],
        "recurring_themes": [],
    }

    mock_client = MockLLMClient(response=minimal_response)
    organizer = SmartAutoOrganizer(mock_client, MockLLMConfig())

    result = organizer.extract(sample_memory)
    assert len(result.topics) == 1
    assert len(result.people) == 0
    assert len(result.action_items) == 0


def test_extract_with_invalid_json(sample_memory):
    """Test handling of invalid JSON response."""
    mock_client = MockLLMClient(response="This is not JSON")
    organizer = SmartAutoOrganizer(mock_client, MockLLMConfig())

    result = organizer.extract(sample_memory)
    # Should return empty result on error
    assert result.memory_id == sample_memory.id
    assert result.entity_count() == 0


def test_extract_with_exception(sample_memory):
    """Test handling of extraction exceptions."""

    class FailingLLMClient:
        def generate(self, prompt, config):
            raise RuntimeError("LLM service unavailable")

    organizer = SmartAutoOrganizer(FailingLLMClient(), MockLLMConfig())

    result = organizer.extract(sample_memory)
    # Should return empty result on exception
    assert result.memory_id == sample_memory.id
    assert result.entity_count() == 0
