# core/entity.py
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .enums import EntityType, ParticipantRole, PriorityLevel, SentimentType, StatusType


@dataclass
class EntityNode:
    """
    Represents an extracted entity from a memory.
    Entities are connected to their source memory and can link to other entities.
    """

    id: str  # Unique identifier for the entity
    entity_type: EntityType
    name: str  # Display name of the entity
    description: str  # Description or content of the entity
    source_memory_id: str  # ID of the memory this was extracted from

    # Relationships
    related_entities: list[str] = field(default_factory=list)  # IDs of related entities
    mentions: list[str] = field(default_factory=list)  # Memory IDs where this entity is mentioned

    # Common metadata
    confidence: float = 1.0  # Extraction confidence (0.0-1.0)
    salience: float = 1.0  # Importance score
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Type-specific metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    # Optional embedding for semantic search
    embedding: list[float] | None = None


@dataclass
class TopicEntity(EntityNode):
    """Main topic of a discussion or memory."""

    def __post_init__(self):
        self.entity_type = EntityType.TOPIC
        self.metadata.setdefault("subtopics", [])


@dataclass
class PersonEntity(EntityNode):
    """Person mentioned in a memory."""

    role: ParticipantRole = ParticipantRole.PARTICIPANT

    def __post_init__(self):
        self.entity_type = EntityType.PERSON
        self.metadata["role"] = self.role.value
        self.metadata.setdefault("organization", None)
        self.metadata.setdefault("email", None)


@dataclass
class OrganizationEntity(EntityNode):
    """Organization, team, or company mentioned."""

    def __post_init__(self):
        self.entity_type = EntityType.ORGANIZATION
        self.metadata.setdefault("department", None)
        self.metadata.setdefault("members", [])


@dataclass
class ActionItemEntity(EntityNode):
    """Action item extracted from a memory."""

    assignee: str | None = None  # Person responsible
    deadline: datetime | None = None
    priority: PriorityLevel = PriorityLevel.MEDIUM
    status: StatusType = StatusType.OPEN

    def __post_init__(self):
        self.entity_type = EntityType.ACTION_ITEM
        self.metadata["assignee"] = self.assignee
        self.metadata["deadline"] = self.deadline.isoformat() if self.deadline else None
        self.metadata["priority"] = self.priority.value
        self.metadata["status"] = self.status.value


@dataclass
class DecisionEntity(EntityNode):
    """Decision made during a discussion."""

    decision_maker: str | None = None  # Person who made the decision
    rationale: str | None = None

    def __post_init__(self):
        self.entity_type = EntityType.DECISION
        self.metadata["decision_maker"] = self.decision_maker
        self.metadata["rationale"] = self.rationale
        self.metadata.setdefault("alternatives_considered", [])


@dataclass
class QuestionEntity(EntityNode):
    """Open question or unresolved item."""

    status: StatusType = StatusType.UNRESOLVED
    asked_by: str | None = None

    def __post_init__(self):
        self.entity_type = EntityType.QUESTION
        self.metadata["status"] = self.status.value
        self.metadata["asked_by"] = self.asked_by
        self.metadata.setdefault("follow_up_required", True)


@dataclass
class SentimentEntity(EntityNode):
    """Sentiment/tone of a discussion."""

    sentiment_type: SentimentType = SentimentType.NEUTRAL
    intensity: float = 0.5  # 0.0-1.0

    def __post_init__(self):
        self.entity_type = EntityType.SENTIMENT
        self.metadata["sentiment_type"] = self.sentiment_type.value
        self.metadata["intensity"] = self.intensity


@dataclass
class TimelineEntity(EntityNode):
    """Timeline event (date, deadline, milestone)."""

    event_date: datetime | None = None
    event_type: str = "general"  # deadline, milestone, meeting, etc.

    def __post_init__(self):
        self.entity_type = EntityType.TIMELINE
        self.metadata["event_date"] = self.event_date.isoformat() if self.event_date else None
        self.metadata["event_type"] = self.event_type


@dataclass
class ReferenceEntity(EntityNode):
    """External reference (URL, document, tool)."""

    url: str | None = None
    reference_type: str = "general"  # url, document, tool, api, etc.

    def __post_init__(self):
        self.entity_type = EntityType.REFERENCE
        self.metadata["url"] = self.url
        self.metadata["reference_type"] = self.reference_type


@dataclass
class IdeaEntity(EntityNode):
    """Idea or brainstormed item."""

    category: str | None = None
    feasibility: str | None = None  # high, medium, low

    def __post_init__(self):
        self.entity_type = EntityType.IDEA
        self.metadata["category"] = self.category
        self.metadata["feasibility"] = self.feasibility
        self.metadata.setdefault("related_ideas", [])


@dataclass
class RiskEntity(EntityNode):
    """Risk or blocker identified."""

    priority: PriorityLevel = PriorityLevel.MEDIUM
    impact: str | None = None  # Description of potential impact
    mitigation: str | None = None  # Mitigation strategy

    def __post_init__(self):
        self.entity_type = EntityType.RISK
        self.metadata["priority"] = self.priority.value
        self.metadata["impact"] = self.impact
        self.metadata["mitigation"] = self.mitigation


@dataclass
class RecurringThemeEntity(EntityNode):
    """Recurring theme across multiple memories."""

    frequency: int = 1  # Number of times this theme appears
    first_occurrence: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_occurrence: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        self.entity_type = EntityType.RECURRING_THEME
        self.metadata["frequency"] = self.frequency
        self.metadata["first_occurrence"] = self.first_occurrence.isoformat()
        self.metadata["last_occurrence"] = self.last_occurrence.isoformat()


@dataclass
class ExtractionResult:
    """Container for all entities extracted from a memory."""

    memory_id: str
    topics: list[TopicEntity] = field(default_factory=list)
    subtopics: list[EntityNode] = field(default_factory=list)
    people: list[PersonEntity] = field(default_factory=list)
    organizations: list[OrganizationEntity] = field(default_factory=list)
    action_items: list[ActionItemEntity] = field(default_factory=list)
    decisions: list[DecisionEntity] = field(default_factory=list)
    questions: list[QuestionEntity] = field(default_factory=list)
    sentiments: list[SentimentEntity] = field(default_factory=list)
    timeline_events: list[TimelineEntity] = field(default_factory=list)
    references: list[ReferenceEntity] = field(default_factory=list)
    ideas: list[IdeaEntity] = field(default_factory=list)
    risks: list[RiskEntity] = field(default_factory=list)
    recurring_themes: list[RecurringThemeEntity] = field(default_factory=list)

    def all_entities(self) -> list[EntityNode]:
        """Return all extracted entities as a flat list."""
        return (
            self.topics
            + self.subtopics
            + self.people
            + self.organizations
            + self.action_items
            + self.decisions
            + self.questions
            + self.sentiments
            + self.timeline_events
            + self.references
            + self.ideas
            + self.risks
            + self.recurring_themes
        )

    def entity_count(self) -> int:
        """Return total number of extracted entities."""
        return len(self.all_entities())
