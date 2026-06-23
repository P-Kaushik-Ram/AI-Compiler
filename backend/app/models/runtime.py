"""Pydantic models for the Runtime stage's CompilationResult output."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.models.data_schema import DataSchema
from app.models.intent import IntentIR
from app.models.system_design import SystemDesign
from app.models.validation import ValidationReport

StageName = Literal["intent_extraction", "system_design", "schema_generation", "validation"]
OverallStatus = Literal["succeeded", "succeeded_with_warnings", "halted", "errored"]
FinalDecision = Literal["proceed", "proceed_with_warnings", "halt", "not_reached"]


class StageSummary(BaseModel):
    """A timing and outcome summary for a single stage execution within one compilation run."""

    stage_name: StageName
    status: str
    duration_ms: float
    confidence: float | None = None
    summary: str


class CompilationResult(BaseModel):
    """The complete, terminal record produced by orchestrating all four compiler stages."""

    compilation_id: str
    version: str
    started_at: datetime
    completed_at: datetime
    total_duration_ms: float
    overall_status: OverallStatus
    final_decision: FinalDecision
    stage_summaries: list[StageSummary] = Field(default_factory=list)
    intent_ir: IntentIR | None = None
    system_design: SystemDesign | None = None
    data_schema: DataSchema | None = None
    validation_report: ValidationReport | None = None
    error: str | None = None
