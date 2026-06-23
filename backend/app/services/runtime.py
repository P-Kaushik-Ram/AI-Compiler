"""Deterministic orchestration for the Runtime compiler stage.

This module contains no compiler logic of its own. It only sequences the four existing
services (``IntentExtractionService``, ``SystemDesignService``, ``SchemaGenerationService``,
``ValidationService``), times each call, and assembles their outputs into one terminal
``CompilationResult``. It never re-implements a decision any of those services already make;
``ValidationReport.pipeline_decision`` is treated as the single terminal arbiter of success.
"""
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Callable, TypeVar

from app.models.data_schema import DataSchema
from app.models.intent import IntentIR
from app.models.runtime import CompilationResult, StageSummary
from app.models.system_design import SystemDesign
from app.models.validation import ValidationReport
from app.services.intent_extraction import IntentExtractionService
from app.services.schema_generation import SchemaGenerationService
from app.services.system_design import SystemDesignService
from app.services.validation import ValidationService

RUNTIME_VERSION = "1.0"

logger = logging.getLogger(__name__)

T = TypeVar("T")

_VALIDATION_STATUS_TO_OVERALL_STATUS = {
    "passed": "succeeded",
    "passed_with_warnings": "succeeded_with_warnings",
    "failed": "halted",
}


class RuntimeConfigurationError(ValueError):
    """Raised when the combination of inputs given to RuntimeService.run cannot form a valid pipeline."""


class RuntimeService:
    """Orchestrates Intent Extraction, System Design, Schema Generation, and Validation in sequence."""

    def run(
        self,
        prompt: str | None = None,
        intent_ir: IntentIR | None = None,
        system_design: SystemDesign | None = None,
        data_schema: DataSchema | None = None,
    ) -> CompilationResult:
        """Run the full pipeline from the earliest unresolved stage through Validation.

        Any of ``intent_ir``, ``system_design``, or ``data_schema`` may be pre-supplied to skip
        the stage that would otherwise produce it (resumable execution). Validation always runs,
        since it is what produces the terminal decision. This method never raises: any failure,
        whether a configuration problem or an unexpected exception from a stage, is captured and
        returned as a CompilationResult with ``overall_status="errored"`` instead.
        """
        try:
            self._validate_starting_point(prompt, intent_ir, system_design, data_schema)
        except RuntimeConfigurationError as exc:
            return self._build_configuration_error_result(exc)

        compilation_id = str(uuid.uuid4())
        started_at = datetime.now(timezone.utc)
        start_perf = time.perf_counter()
        summaries: list[StageSummary] = []

        try:
            if intent_ir is None:
                intent_ir, duration_ms = self._run_stage(
                    "intent_extraction", compilation_id, lambda: IntentExtractionService().extract(prompt)
                )
                summaries.append(self._summarize_intent(intent_ir, duration_ms))
            else:
                summaries.append(self._skipped_summary("intent_extraction"))

            if system_design is None:
                system_design, duration_ms = self._run_stage(
                    "system_design", compilation_id, lambda: SystemDesignService().build(intent_ir)
                )
                summaries.append(self._summarize_design(system_design, duration_ms))
            else:
                summaries.append(self._skipped_summary("system_design"))

            if data_schema is None:
                data_schema, duration_ms = self._run_stage(
                    "schema_generation",
                    compilation_id,
                    lambda: SchemaGenerationService().generate(intent_ir, system_design),
                )
                summaries.append(self._summarize_schema(data_schema, duration_ms))
            else:
                summaries.append(self._skipped_summary("schema_generation"))

            validation_report, duration_ms = self._run_stage(
                "validation",
                compilation_id,
                lambda: ValidationService().validate(intent_ir, system_design, data_schema),
            )
            summaries.append(self._summarize_validation(validation_report, duration_ms))
        except Exception as exc:  # noqa: BLE001 - any stage failure must become data, never propagate
            return self._build_stage_error_result(
                compilation_id, started_at, start_perf, summaries, exc, intent_ir, system_design, data_schema
            )

        return self._build_terminal_result(
            compilation_id, started_at, start_perf, summaries, intent_ir, system_design, data_schema, validation_report
        )

    def _validate_starting_point(
        self,
        prompt: str | None,
        intent_ir: IntentIR | None,
        system_design: SystemDesign | None,
        data_schema: DataSchema | None,
    ) -> None:
        """Ensure the given inputs describe a runnable pipeline before any stage is executed."""
        if intent_ir is None and prompt is None:
            raise RuntimeConfigurationError("Either 'prompt' or 'intent_ir' must be provided.")
        if system_design is not None and intent_ir is None:
            raise RuntimeConfigurationError("Cannot supply 'system_design' without 'intent_ir'.")
        if data_schema is not None and (intent_ir is None or system_design is None):
            raise RuntimeConfigurationError("Cannot supply 'data_schema' without both 'intent_ir' and 'system_design'.")

    def _run_stage(self, stage_label: str, compilation_id: str, fn: Callable[[], T]) -> tuple[T, float]:
        """Execute one stage, logging its start/finish and returning its result with its duration in ms."""
        logger.info("compilation_id=%s stage=%s event=starting", compilation_id, stage_label)
        start = time.perf_counter()
        result = fn()
        duration_ms = round((time.perf_counter() - start) * 1000, 3)
        logger.info("compilation_id=%s stage=%s event=finished duration_ms=%s", compilation_id, stage_label, duration_ms)
        return result, duration_ms

    def _skipped_summary(self, stage_name: str) -> StageSummary:
        """Build the summary recorded for a stage that was skipped because its output was pre-supplied."""
        return StageSummary(
            stage_name=stage_name,  # type: ignore[arg-type]
            status="skipped",
            duration_ms=0.0,
            confidence=None,
            summary="Pre-supplied artifact; stage not executed.",
        )

    def _summarize_intent(self, intent_ir: IntentIR, duration_ms: float) -> StageSummary:
        """Build the StageSummary for a completed Intent Extraction run."""
        return StageSummary(
            stage_name="intent_extraction",
            status=intent_ir.status,
            duration_ms=duration_ms,
            confidence=intent_ir.confidence,
            summary=f"{len(intent_ir.entities)} entities, {len(intent_ir.relationships)} relationships, "
            f"{len(intent_ir.actions)} actions",
        )

    def _summarize_design(self, system_design: SystemDesign, duration_ms: float) -> StageSummary:
        """Build the StageSummary for a completed System Design run."""
        return StageSummary(
            stage_name="system_design",
            status=system_design.status,
            duration_ms=duration_ms,
            confidence=system_design.confidence,
            summary=f"{len(system_design.modules)} modules, {len(system_design.capabilities)} capabilities, "
            f"{len(system_design.module_dependencies)} dependencies",
        )

    def _summarize_schema(self, data_schema: DataSchema, duration_ms: float) -> StageSummary:
        """Build the StageSummary for a completed Schema Generation run."""
        return StageSummary(
            stage_name="schema_generation",
            status=data_schema.status,
            duration_ms=duration_ms,
            confidence=data_schema.confidence,
            summary=f"{len(data_schema.entities)} entities, {len(data_schema.relationships)} relationships, "
            f"{len(data_schema.constraints)} constraints",
        )

    def _summarize_validation(self, validation_report: ValidationReport, duration_ms: float) -> StageSummary:
        """Build the StageSummary for a completed Validation run."""
        return StageSummary(
            stage_name="validation",
            status=validation_report.status,
            duration_ms=duration_ms,
            confidence=validation_report.confidence,
            summary=f"{len(validation_report.findings)} findings; {validation_report.pipeline_decision}",
        )

    def _build_configuration_error_result(self, exc: RuntimeConfigurationError) -> CompilationResult:
        """Build the CompilationResult returned when the inputs cannot form a runnable pipeline."""
        now = datetime.now(timezone.utc)
        logger.error("compilation_id=unassigned event=configuration_error message=%s", exc)
        return CompilationResult(
            compilation_id=str(uuid.uuid4()),
            version=RUNTIME_VERSION,
            started_at=now,
            completed_at=now,
            total_duration_ms=0.0,
            overall_status="errored",
            final_decision="not_reached",
            stage_summaries=[],
            error=f"Invalid pipeline configuration: {exc}",
        )

    def _build_stage_error_result(
        self,
        compilation_id: str,
        started_at: datetime,
        start_perf: float,
        summaries: list[StageSummary],
        exc: Exception,
        intent_ir: IntentIR | None,
        system_design: SystemDesign | None,
        data_schema: DataSchema | None,
    ) -> CompilationResult:
        """Build the CompilationResult returned when a stage raises an unexpected exception."""
        completed_at = datetime.now(timezone.utc)
        total_duration_ms = round((time.perf_counter() - start_perf) * 1000, 3)
        failed_stage = self._next_stage_name(summaries)
        logger.error(
            "compilation_id=%s stage=%s event=error message=%s", compilation_id, failed_stage, exc
        )
        summaries.append(
            StageSummary(
                stage_name=failed_stage,  # type: ignore[arg-type]
                status="error",
                duration_ms=0.0,
                confidence=None,
                summary=str(exc),
            )
        )
        return CompilationResult(
            compilation_id=compilation_id,
            version=RUNTIME_VERSION,
            started_at=started_at,
            completed_at=completed_at,
            total_duration_ms=total_duration_ms,
            overall_status="errored",
            final_decision="not_reached",
            stage_summaries=summaries,
            intent_ir=intent_ir,
            system_design=system_design,
            data_schema=data_schema,
            validation_report=None,
            error=f"{failed_stage} failed: {exc}",
        )

    def _next_stage_name(self, summaries: list[StageSummary]) -> StageName:
        """Infer which stage was executing when a failure occurred, from how many summaries exist so far."""
        stage_order: list[StageName] = ["intent_extraction", "system_design", "schema_generation", "validation"]
        return stage_order[len(summaries)]

    def _build_terminal_result(
        self,
        compilation_id: str,
        started_at: datetime,
        start_perf: float,
        summaries: list[StageSummary],
        intent_ir: IntentIR,
        system_design: SystemDesign,
        data_schema: DataSchema,
        validation_report: ValidationReport,
    ) -> CompilationResult:
        """Build the successful (or halted-but-well-formed) CompilationResult after all stages ran."""
        completed_at = datetime.now(timezone.utc)
        total_duration_ms = round((time.perf_counter() - start_perf) * 1000, 3)
        overall_status = _VALIDATION_STATUS_TO_OVERALL_STATUS[validation_report.status]
        logger.info(
            "compilation_id=%s event=compilation_finished overall_status=%s final_decision=%s total_duration_ms=%s",
            compilation_id,
            overall_status,
            validation_report.pipeline_decision,
            total_duration_ms,
        )
        return CompilationResult(
            compilation_id=compilation_id,
            version=RUNTIME_VERSION,
            started_at=started_at,
            completed_at=completed_at,
            total_duration_ms=total_duration_ms,
            overall_status=overall_status,  # type: ignore[arg-type]
            final_decision=validation_report.pipeline_decision,
            stage_summaries=summaries,
            intent_ir=intent_ir,
            system_design=system_design,
            data_schema=data_schema,
            validation_report=validation_report,
            error=None,
        )
