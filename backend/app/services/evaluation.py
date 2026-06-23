"""The Evaluation Framework's batch-execution service.

This is NOT a compiler stage: it has no IR and never participates in compilation. It measures
the compiler's behavior across many prompts by consuming ``RuntimeService`` exclusively — it
never imports or calls ``IntentExtractionService``, ``SystemDesignService``,
``SchemaGenerationService``, or ``ValidationService`` directly. That constraint guarantees this
framework only ever observes behavior a real caller (e.g. the ``/compile`` endpoint) would also
see, and stays fully decoupled from internal refactors of the four compiler stages.

Every method here processes one dataset case at a time: a ``CompilationResult`` is read for its
metrics and then allowed to go out of scope immediately (never stored on ``self`` or appended to
any list), and every ``EvaluationReport`` is yielded the instant it is built. Combined with the
fixed-size ``StreamingAggregator``, this keeps memory usage O(1) with respect to dataset size.
"""
import uuid
from collections import Counter
from pathlib import Path
from typing import Iterator, TextIO

from app.models.evaluation import CaseExpectation, DatasetCase, DatasetError, EvaluationReport, StageMetric
from app.models.runtime import CompilationResult
from app.services.evaluation_aggregator import StreamingAggregator
from app.services.evaluation_dataset import open_dataset_file
from app.services.evaluation_dataset import iter_dataset_cases as _iter_dataset_cases
from app.services.runtime import RUNTIME_VERSION, RuntimeService

REPORT_VERSION = "1.0"


class EvaluationService:
    """Streams a dataset of prompts through RuntimeService and reports per-case and aggregate results."""

    def __init__(self, runtime_service: RuntimeService | None = None) -> None:
        """Construct the service, defaulting to a fresh RuntimeService if none is injected."""
        self._runtime_service = runtime_service or RuntimeService()

    def evaluate_case(self, case: DatasetCase) -> EvaluationReport:
        """Compile one dataset case's prompt via RuntimeService and reduce it to an EvaluationReport.

        The CompilationResult returned by RuntimeService is read only for the metrics folded into
        the report below; it is a local variable that is never retained beyond this method call.
        """
        result = self._runtime_service.run(prompt=case.prompt)
        return self._build_report(case, result)

    def run_benchmark(
        self, dataset: Iterator[DatasetCase | DatasetError], dataset_name: str
    ) -> tuple[Iterator[EvaluationReport], StreamingAggregator]:
        """Start streaming a dataset through the compiler. Returns a lazy report generator paired
        with the StreamingAggregator it feeds; nothing in ``dataset`` is read until the generator
        is iterated, and the aggregator's size never grows with how many items it processes.
        """
        aggregator = StreamingAggregator(dataset_name=dataset_name, compiler_version=RUNTIME_VERSION)
        return self._drive(dataset, aggregator), aggregator

    def run_benchmark_from_path(
        self, path: str | Path, dataset_name: str
    ) -> tuple[Iterator[EvaluationReport], StreamingAggregator]:
        """Stream a JSONL dataset file through the compiler, handling an unopenable file gracefully.

        If the file cannot be opened at all, the returned aggregator is pre-flagged so that
        ``finalize()`` immediately produces a BenchmarkResult with ``status="failed_to_load"``,
        rather than raising out of this method.
        """
        aggregator = StreamingAggregator(dataset_name=dataset_name, compiler_version=RUNTIME_VERSION)
        try:
            file_handle = open_dataset_file(path)
        except OSError as exc:
            aggregator.mark_failed_to_load(f"Could not open dataset file '{path}': {exc}")
            return iter(()), aggregator

        return self._drive_and_close(file_handle, aggregator), aggregator

    def _drive_and_close(self, file_handle: TextIO, aggregator: StreamingAggregator) -> Iterator[EvaluationReport]:
        """Stream an already-open dataset file through the compiler, closing it once exhausted."""
        try:
            yield from self._drive(_iter_dataset_cases(file_handle), aggregator)
        finally:
            file_handle.close()

    def _drive(
        self, dataset: Iterator[DatasetCase | DatasetError], aggregator: StreamingAggregator
    ) -> Iterator[EvaluationReport]:
        """Process one dataset item at a time: route DatasetErrors to the aggregator, compile
        DatasetCases, fold each resulting EvaluationReport into the aggregator, and yield it.
        """
        for item in dataset:
            if isinstance(item, DatasetError):
                aggregator.record_dataset_error(item)
                continue
            report = self.evaluate_case(item)
            aggregator.update(report)
            yield report

    def _build_report(self, case: DatasetCase, result: CompilationResult) -> EvaluationReport:
        """Reduce one CompilationResult to a lightweight EvaluationReport, extracting metrics only."""
        stage_metrics = [
            StageMetric(
                stage_name=summary.stage_name,
                status=summary.status,
                duration_ms=summary.duration_ms,
                confidence=summary.confidence,
            )
            for summary in result.stage_summaries
        ]

        validation_finding_counts: dict[str, int] = {}
        if result.validation_report is not None:
            validation_finding_counts = dict(Counter(finding.severity for finding in result.validation_report.findings))

        failure_category = self._determine_failure_category(result)
        passed, notes = self._determine_passed(case.expectation, result)

        return EvaluationReport(
            evaluation_id=str(uuid.uuid4()),
            version=REPORT_VERSION,
            case_id=case.case_id,
            prompt=case.prompt,
            category=case.category,
            compilation_id=result.compilation_id,
            overall_status=result.overall_status,
            final_decision=result.final_decision,
            stage_metrics=stage_metrics,
            validation_finding_counts=validation_finding_counts,
            failure_category=failure_category,
            passed=passed,
            notes=notes,
            total_duration_ms=result.total_duration_ms,
        )

    def _determine_failure_category(self, result: CompilationResult) -> str | None:
        """Classify a non-success CompilationResult by reading off where the cascade first broke."""
        if result.overall_status in ("succeeded", "succeeded_with_warnings"):
            return None
        if result.overall_status == "errored":
            return "infrastructure_error"
        if result.intent_ir is None or result.intent_ir.status != "complete":
            return "intent_ambiguous"
        if result.system_design is None or result.system_design.status != "complete":
            return "design_inconsistent"
        if result.data_schema is None or result.data_schema.status != "complete":
            return "schema_inconsistent"
        return "validation_failed"

    def _determine_passed(
        self, expectation: CaseExpectation | None, result: CompilationResult
    ) -> tuple[bool | None, str | None]:
        """Evaluate a dataset case's declared expectation (if any) against its CompilationResult."""
        if expectation is None:
            return None, None

        notes: list[str] = []
        if expectation.expect_halt:
            passed: bool | None = result.overall_status == "halted"
        elif expectation.expected_overall_status is not None:
            passed = result.overall_status == expectation.expected_overall_status
        else:
            return None, None

        if expectation.expected_domain is not None:
            actual_domain = result.intent_ir.domain if result.intent_ir is not None else None
            if actual_domain != expectation.expected_domain:
                passed = False
                notes.append(f"expected domain '{expectation.expected_domain}', got '{actual_domain}'")

        if expectation.expected_min_confidence is not None:
            overall_confidence = self._overall_confidence(result)
            if overall_confidence is None or overall_confidence < expectation.expected_min_confidence:
                passed = False
                notes.append(
                    f"expected confidence >= {expectation.expected_min_confidence}, got {overall_confidence}"
                )

        return passed, "; ".join(notes) or None

    def _overall_confidence(self, result: CompilationResult) -> float | None:
        """Return the most authoritative confidence value available on a CompilationResult."""
        if result.validation_report is not None:
            return result.validation_report.confidence
        if result.stage_summaries:
            return result.stage_summaries[-1].confidence
        return None
