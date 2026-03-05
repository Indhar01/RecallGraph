from enum import Enum


class MemoryType(Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    FACT = "fact"


class EntityType(Enum):
    """Types of entities that can be extracted from memories."""
    TOPIC = "topic"
    SUBTOPIC = "subtopic"
    PERSON = "person"
    ORGANIZATION = "organization"
    ACTION_ITEM = "action_item"
    DECISION = "decision"
    QUESTION = "question"
    SENTIMENT = "sentiment"
    TIMELINE = "timeline"
    REFERENCE = "reference"
    IDEA = "idea"
    RISK = "risk"
    RECURRING_THEME = "recurring_theme"


class SentimentType(Enum):
    """Sentiment/tone classifications."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    TENSE = "tense"
    PRODUCTIVE = "productive"
    CHAOTIC = "chaotic"
    COLLABORATIVE = "collaborative"
    URGENT = "urgent"


class ParticipantRole(Enum):
    """Roles that people can have in a discussion/meeting."""
    ORGANIZER = "organizer"
    NOTE_TAKER = "note_taker"
    DECISION_MAKER = "decision_maker"
    PARTICIPANT = "participant"
    CONTRIBUTOR = "contributor"
    OBSERVER = "observer"


class PriorityLevel(Enum):
    """Priority levels for action items and risks."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class StatusType(Enum):
    """Status for action items and questions."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
