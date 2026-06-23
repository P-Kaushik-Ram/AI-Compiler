"""Pydantic models for the Intent Extraction stage's Intermediate Representation (IR)."""
from typing import Literal

from pydantic import BaseModel, Field

DomainType = Literal[
    "crm",
    "ecommerce",
    "healthcare",
    "education",
    "finance",
    "logistics",
    "social",
    "productivity",
    "general",
    "other",
]

StatusType = Literal["complete", "needs_clarification", "rejected"]


class Attribute(BaseModel):
    """A single field belonging to an extracted entity."""

    name: str
    type_hint: str
    is_optional: bool
    source_phrase: str | None = None


class Entity(BaseModel):
    """A domain noun (e.g. User, Order) that the requested system must represent."""

    name: str
    description: str
    attributes: list[Attribute] = Field(default_factory=list)
    confidence: float


class Relationship(BaseModel):
    """A conceptual (non-schema) semantic relationship between two entities."""

    from_entity: str
    to_entity: str
    relationship_type: Literal["owns", "has_many", "has_one", "belongs_to", "associated_with"]
    description: str
    source_phrase: str | None = None


class Action(BaseModel):
    """An operation the requested system must support."""

    name: str
    target_entity: str | None = None
    description: str
    confidence: float


class UserStory(BaseModel):
    """A goal a specific actor wants the system to satisfy, with a priority."""

    actor: str
    goal: str
    priority: Literal["must_have", "should_have", "nice_to_have"]
    related_action: str | None = None


class FunctionalRequirement(BaseModel):
    """A business rule or behavior the system must implement."""

    description: str
    related_entity: str | None = None
    related_action: str | None = None
    source_phrase: str | None = None


class NonFunctionalRequirement(BaseModel):
    """A quality attribute (performance, auth posture, compliance, etc.) the system must satisfy."""

    category: Literal[
        "performance", "scalability", "availability", "auth", "compliance", "usability", "other"
    ]
    description: str
    source_phrase: str | None = None


class Integration(BaseModel):
    """A third-party system or service the prompt explicitly references."""

    name: str
    purpose: str


class RiskFlag(BaseModel):
    """A signal that a prompt touches a sensitive area requiring special downstream handling."""

    category: Literal[
        "compliance", "payments", "medical_data", "legal", "security", "high_ambiguity", "other"
    ]
    description: str
    severity: Literal["low", "medium", "high", "critical"]
    source_phrase: str | None = None
    recommended_handling: str | None = None


class Ambiguity(BaseModel):
    """An unresolved point in the prompt that may require clarification from the user."""

    question: str
    related_field: str | None = None
    severity: Literal["blocking", "advisory"]


class Assumption(BaseModel):
    """A default the extractor applied in the absence of explicit information."""

    description: str
    rationale: str
    affected_field: str | None = None


class IntentIR(BaseModel):
    """The complete Intermediate Representation produced by the Intent Extraction stage."""

    intent_id: str
    version: str
    domain: DomainType
    primary_intent: str
    domain_summary: str
    entities: list[Entity] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)
    actions: list[Action] = Field(default_factory=list)
    user_stories: list[UserStory] = Field(default_factory=list)
    functional_requirements: list[FunctionalRequirement] = Field(default_factory=list)
    non_functional_requirements: list[NonFunctionalRequirement] = Field(default_factory=list)
    integrations: list[Integration] = Field(default_factory=list)
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    ambiguities: list[Ambiguity] = Field(default_factory=list)
    assumptions: list[Assumption] = Field(default_factory=list)
    confidence: float
    status: StatusType
    raw_prompt: str
