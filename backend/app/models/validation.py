"""Pydantic models for the Validation & Repair stage's ValidationReport output."""
from typing import Literal

from pydantic import BaseModel, Field

ValidationCategory = Literal[
    "missing_entity",
    "orphan_relationship",
    "invalid_reference",
    "duplicate_definition",
    "naming_conflict",
    "risk_propagation_failure",
    "missing_required_field",
    "broken_traceability",
    "cross_stage_inconsistency",
]
Severity = Literal["info", "warning", "error", "critical"]
Stage = Literal["intent", "system_design", "data_schema", "cross_stage"]
PipelineDecision = Literal["proceed", "proceed_with_warnings", "halt"]
ValidationStatus = Literal["passed", "passed_with_warnings", "failed"]


class ValidationFinding(BaseModel):
    """A single reported inconsistency, with its severity and a non-executed recommendation."""

    finding_id: str
    category: ValidationCategory
    severity: Severity
    stage: Stage
    message: str
    related_field: str | None = None
    recommendation: str


class ConsistencySummary(BaseModel):
    """Aggregate counts describing the scope of what was checked and what was already known."""

    entities_checked: int
    relationships_checked: int
    modules_checked: int
    schema_entities_checked: int
    upstream_ambiguities_carried: int
    acknowledged_gaps: int


class ValidationReport(BaseModel):
    """The complete cross-stage consistency report produced by the Validation & Repair stage."""

    validation_id: str
    version: str
    source_intent_id: str
    source_design_id: str
    source_schema_id: str
    findings: list[ValidationFinding] = Field(default_factory=list)
    consistency_summary: ConsistencySummary
    confidence: float
    pipeline_decision: PipelineDecision
    status: ValidationStatus
