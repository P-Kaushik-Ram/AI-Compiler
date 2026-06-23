"""Pydantic models for the System Design stage's SystemDesign output."""
from typing import Literal

from pydantic import BaseModel, Field

ArchitectureStyle = Literal["modular_monolith", "service_oriented", "single_module"]
SystemDesignStatus = Literal["complete", "needs_clarification", "rejected"]


class ModuleRef(BaseModel):
    """A logical subsystem grouping a set of entities and the capabilities that act on them."""

    name: str
    purpose: str
    owned_entities: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    source_fields: list[str] = Field(default_factory=list)


class Capability(BaseModel):
    """A named ability a module exposes, grouping one or more IntentIR actions."""

    name: str
    module: str
    description: str
    related_actions: list[str] = Field(default_factory=list)
    risk_level: Literal["none", "low", "medium", "high", "critical"]


class WorkflowStep(BaseModel):
    """A single ordered step within a Workflow."""

    step_name: str
    capability: str
    depends_on: list[str] = Field(default_factory=list)


class Workflow(BaseModel):
    """An ordered, multi-step process synthesized from sequencing language in the IR."""

    name: str
    trigger: str
    steps: list[WorkflowStep] = Field(default_factory=list)
    outcome: str


class Actor(BaseModel):
    """A role that interacts with the system and the capabilities it can access."""

    name: str
    description: str
    accessible_capabilities: list[str] = Field(default_factory=list)
    source_user_stories: list[str] = Field(default_factory=list)


class ModuleDependency(BaseModel):
    """A directed dependency from one module on another."""

    from_module: str
    to_module: str
    dependency_type: Literal["data", "workflow", "integration"]
    reason: str


class ExternalDependency(BaseModel):
    """A third-party integration from the IR, attached to the module that owns it."""

    name: str
    purpose: str
    owning_module: str


class DesignAmbiguity(BaseModel):
    """An unresolved architectural decision that may require clarification."""

    question: str
    related_field: str | None = None
    severity: Literal["blocking", "advisory"]


class DesignRisk(BaseModel):
    """A risk inherited from the IR, with the modules it affects and its architectural implication."""

    category: Literal[
        "compliance", "payments", "medical_data", "legal", "security", "high_ambiguity", "other"
    ]
    description: str
    severity: Literal["low", "medium", "high", "critical"]
    affected_modules: list[str] = Field(default_factory=list)
    architectural_implication: str


class SystemDesign(BaseModel):
    """The complete logical architecture produced by the System Design stage."""

    design_id: str
    version: str
    source_intent_id: str
    architecture_style: ArchitectureStyle
    modules: list[ModuleRef] = Field(default_factory=list)
    capabilities: list[Capability] = Field(default_factory=list)
    workflows: list[Workflow] = Field(default_factory=list)
    actors: list[Actor] = Field(default_factory=list)
    module_dependencies: list[ModuleDependency] = Field(default_factory=list)
    external_dependencies: list[ExternalDependency] = Field(default_factory=list)
    design_ambiguities: list[DesignAmbiguity] = Field(default_factory=list)
    design_risks: list[DesignRisk] = Field(default_factory=list)
    confidence: float
    status: SystemDesignStatus
