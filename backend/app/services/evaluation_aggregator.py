"""Fixed-size, O(1)-memory incremental aggregation for the Evaluation Framework.

Nothing in this module ever stores a value per observation: running rates use plain integer
counters, means use Welford's online algorithm, and the approximate p50/p95 percentiles use
the P2 algorithm (Jain & Chlamtac, 1985) — a deterministic, single-pass quantile estimator
that maintains exactly 5 marker values per tracked quantile and never retains the underlying
data. Memory usage is therefore constant regardless of how many observations are folded in.
"""
import statistics
import uuid
from datetime import datetime, timezone

from app.models.evaluation import BenchmarkResult, DatasetError, Distribution, EvaluationReport

AGGREGATOR_VERSION = "1.0"

STAGE_NAMES: tuple[str, ...] = ("intent_extraction", "system_design", "schema_generation", "validation")
FAILURE_CATEGORIES: tuple[str, ...] = (
    "intent_ambiguous",
    "design_inconsistent",
    "schema_inconsistent",
    "validation_failed",
    "infrastructure_error",
)
FINDING_SEVERITIES: tuple[str, ...] = ("info", "warning", "error", "critical")
UNCATEGORIZED_LABEL = "uncategorized"
_VALIDATION_REACHED_STATUSES: tuple[str, ...] = ("passed", "passed_with_warnings", "failed")


class _WelfordAccumulator:
    """Tracks a running mean (and count) for a streamed numeric series in O(1) memory."""

    def __init__(self) -> None:
        """Initialize an empty accumulator with no observations yet."""
        self.count = 0
        self.mean = 0.0

    def update(self, value: float) -> None:
        """Fold one new observation into the running mean using Welford's online algorithm."""
        self.count += 1
        self.mean += (value - self.mean) / self.count


class _P2QuantileEstimator:
    """Deterministic, O(1)-memory streaming estimator for one quantile via the P2 algorithm.

    Implements Jain & Chlamtac (1985): maintains exactly 5 marker heights and their positions,
    updated incrementally per observation, never storing the underlying data. The estimate
    converges toward the true quantile as more observations are seen; it is an approximation,
    not an exact percentile, by construction.
    """

    def __init__(self, quantile: float) -> None:
        """Initialize an estimator for the given quantile (e.g. 0.5 for the median)."""
        self._p = quantile
        self._buffer: list[float] = []
        self._initialized = False
        self._heights: list[float] = []
        self._positions: list[float] = []
        self._desired_positions: list[float] = []
        self._increments: list[float] = []

    def update(self, value: float) -> None:
        """Fold one new observation into the estimator."""
        if not self._initialized:
            self._buffer.append(value)
            if len(self._buffer) == 5:
                self._initialize(sorted(self._buffer))
            return
        self._advance(value)

    def _initialize(self, sorted_values: list[float]) -> None:
        """Seed the 5 markers from the first 5 sorted observations."""
        p = self._p
        self._heights = list(sorted_values)
        self._positions = [1.0, 2.0, 3.0, 4.0, 5.0]
        self._desired_positions = [1.0, 1 + 2 * p, 1 + 4 * p, 3 + 2 * p, 5.0]
        self._increments = [0.0, p / 2, p, (1 + p) / 2, 1.0]
        self._initialized = True

    def _advance(self, value: float) -> None:
        """Apply one P2 update step: locate the cell, increment positions, adjust marker heights."""
        heights, positions = self._heights, self._positions

        if value < heights[0]:
            heights[0] = value
            cell = 0
        elif value >= heights[4]:
            heights[4] = value
            cell = 3
        else:
            cell = 3
            for i in range(4):
                if heights[i] <= value < heights[i + 1]:
                    cell = i
                    break

        for i in range(cell + 1, 5):
            positions[i] += 1
        for i in range(5):
            self._desired_positions[i] += self._increments[i]

        for i in range(1, 4):
            d = self._desired_positions[i] - positions[i]
            if (d >= 1 and positions[i + 1] - positions[i] > 1) or (d <= -1 and positions[i - 1] - positions[i] < -1):
                sign = 1 if d >= 1 else -1
                candidate = self._parabolic(i, sign)
                if heights[i - 1] < candidate < heights[i + 1]:
                    heights[i] = candidate
                else:
                    heights[i] = self._linear(i, sign)
                positions[i] += sign

    def _parabolic(self, i: int, sign: int) -> float:
        """Estimate marker i's new height via the P2 algorithm's parabolic prediction formula."""
        heights, positions = self._heights, self._positions
        return heights[i] + sign / (positions[i + 1] - positions[i - 1]) * (
            (positions[i] - positions[i - 1] + sign) * (heights[i + 1] - heights[i]) / (positions[i + 1] - positions[i])
            + (positions[i + 1] - positions[i] - sign) * (heights[i] - heights[i - 1]) / (positions[i] - positions[i - 1])
        )

    def _linear(self, i: int, sign: int) -> float:
        """Estimate marker i's new height via linear interpolation (the parabolic formula's fallback)."""
        heights, positions = self._heights, self._positions
        return heights[i] + sign * (heights[i + sign] - heights[i]) / (positions[i + sign] - positions[i])

    def estimate(self) -> float:
        """Return the current quantile estimate (the exact median of buffered values if fewer than 5 seen)."""
        if not self._initialized:
            if not self._buffer:
                return 0.0
            return statistics.median(self._buffer)
        return self._heights[2]


class _MetricAccumulator:
    """Combines a Welford mean, running min/max, and P2 p50/p95 estimators for one numeric series."""

    def __init__(self) -> None:
        """Initialize an empty accumulator with no observations yet."""
        self._welford = _WelfordAccumulator()
        self._min: float | None = None
        self._max: float | None = None
        self._p50 = _P2QuantileEstimator(0.5)
        self._p95 = _P2QuantileEstimator(0.95)

    def update(self, value: float) -> None:
        """Fold one new observation into every underlying statistic. O(1) regardless of history length."""
        self._welford.update(value)
        self._min = value if self._min is None else min(self._min, value)
        self._max = value if self._max is None else max(self._max, value)
        self._p50.update(value)
        self._p95.update(value)

    def finalize(self) -> Distribution | None:
        """Return the Distribution summary, or None if no observations were ever recorded."""
        if self._welford.count == 0 or self._min is None or self._max is None:
            return None
        return Distribution(
            count=self._welford.count,
            mean=round(self._welford.mean, 4),
            min=self._min,
            max=self._max,
            p50_approx=round(self._p50.estimate(), 4),
            p95_approx=round(self._p95.estimate(), 4),
        )


class StreamingAggregator:
    """Fixed-size, O(1)-memory incremental aggregator that folds a stream of EvaluationReports
    (plus any DatasetErrors) into one BenchmarkResult, without ever retaining per-case data.

    State is bounded entirely by the fixed set of stage names, failure categories, and finding
    severities known in advance; none of it grows with the number of observations folded in.
    """

    def __init__(self, dataset_name: str, compiler_version: str) -> None:
        """Initialize an empty aggregator for a new benchmark run."""
        self._dataset_name = dataset_name
        self._compiler_version = compiler_version
        self._started_at = datetime.now(timezone.utc)
        self._load_failed = False

        self._total = 0
        self._succeeded = 0
        self._succeeded_with_warnings = 0
        self._halted = 0
        self._errored = 0
        self._validation_present = 0
        self._validation_passed = 0

        self._duration_accumulators: dict[str, _MetricAccumulator] = {name: _MetricAccumulator() for name in STAGE_NAMES}
        self._confidence_accumulators: dict[str, _MetricAccumulator] = {name: _MetricAccumulator() for name in STAGE_NAMES}
        self._failure_category_counts: dict[str, int] = {category: 0 for category in FAILURE_CATEGORIES}
        self._validation_severity_counts: dict[str, int] = {severity: 0 for severity in FINDING_SEVERITIES}
        self._dataset_categories: dict[str, int] = {}
        self._dataset_errors: list[DatasetError] = []

    def update(self, report: EvaluationReport) -> None:
        """Fold one EvaluationReport into the running aggregate state. O(1) regardless of dataset size."""
        self._total += 1

        if report.overall_status == "succeeded":
            self._succeeded += 1
        elif report.overall_status == "succeeded_with_warnings":
            self._succeeded_with_warnings += 1
        elif report.overall_status == "halted":
            self._halted += 1
        elif report.overall_status == "errored":
            self._errored += 1

        for stage_metric in report.stage_metrics:
            if stage_metric.stage_name not in self._duration_accumulators:
                continue
            self._duration_accumulators[stage_metric.stage_name].update(stage_metric.duration_ms)
            if stage_metric.confidence is not None:
                self._confidence_accumulators[stage_metric.stage_name].update(stage_metric.confidence)
            if stage_metric.stage_name == "validation" and stage_metric.status in _VALIDATION_REACHED_STATUSES:
                self._validation_present += 1
                if stage_metric.status == "passed":
                    self._validation_passed += 1

        if report.failure_category is not None:
            self._failure_category_counts[report.failure_category] += 1

        for severity, count in report.validation_finding_counts.items():
            if severity in self._validation_severity_counts:
                self._validation_severity_counts[severity] += count

        category_label = report.category or UNCATEGORIZED_LABEL
        self._dataset_categories[category_label] = self._dataset_categories.get(category_label, 0) + 1

    def record_dataset_error(self, error: DatasetError) -> None:
        """Record one dataset row that failed to parse, without affecting any compiler-outcome metric."""
        self._dataset_errors.append(error)

    def mark_failed_to_load(self, error: str) -> None:
        """Flag that the dataset itself could not be opened/read at all; finalize() will report this."""
        self._load_failed = True
        self._dataset_errors.append(DatasetError(case_id=None, raw_line_number=None, error=error))

    def finalize(self) -> BenchmarkResult:
        """Compute the final O(1)-sized BenchmarkResult from every observation folded in so far."""
        completed_at = datetime.now(timezone.utc)
        total_duration_ms = (completed_at - self._started_at).total_seconds() * 1000

        def _rate(numerator: int) -> float:
            return round(numerator / self._total, 4) if self._total else 0.0

        confidence_by_stage = {
            name: distribution
            for name, accumulator in self._confidence_accumulators.items()
            if (distribution := accumulator.finalize()) is not None
        }
        duration_by_stage_ms = {
            name: distribution
            for name, accumulator in self._duration_accumulators.items()
            if (distribution := accumulator.finalize()) is not None
        }

        return BenchmarkResult(
            benchmark_id=str(uuid.uuid4()),
            version=AGGREGATOR_VERSION,
            dataset_name=self._dataset_name,
            dataset_size=self._total,
            compiler_version=self._compiler_version,
            started_at=self._started_at,
            completed_at=completed_at,
            total_duration_ms=round(total_duration_ms, 3),
            success_rate=_rate(self._succeeded + self._succeeded_with_warnings),
            halt_rate=_rate(self._halted),
            error_rate=_rate(self._errored),
            validation_pass_rate=(
                round(self._validation_passed / self._validation_present, 4) if self._validation_present else 0.0
            ),
            confidence_by_stage=confidence_by_stage,
            duration_by_stage_ms=duration_by_stage_ms,
            failure_category_counts=dict(self._failure_category_counts),
            validation_finding_severity_counts=dict(self._validation_severity_counts),
            dataset_categories=dict(self._dataset_categories),
            dataset_errors=list(self._dataset_errors),
            status="failed_to_load" if self._load_failed else "complete",
        )
