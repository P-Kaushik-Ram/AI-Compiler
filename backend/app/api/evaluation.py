"""API routes for the Evaluation Framework."""
from fastapi import APIRouter

from app.models.evaluation import BenchmarkResult
from app.schemas.evaluation import EvaluationRequest
from app.services.evaluation import EvaluationService

router = APIRouter(tags=["evaluation"])


@router.post("/evaluate", response_model=BenchmarkResult)
def evaluate_dataset(request: EvaluationRequest) -> BenchmarkResult:
    """Run a batch of dataset cases through the compiler pipeline and return the aggregate BenchmarkResult.

    Cases are streamed through RuntimeService one at a time; each EvaluationReport is folded into
    the StreamingAggregator and then discarded, so only the O(1)-sized BenchmarkResult is held by
    the time this returns, regardless of how many cases were submitted.
    """
    service = EvaluationService()
    reports, aggregator = service.run_benchmark(iter(request.cases), request.dataset_name)
    for _ in reports:
        pass  # each report has already been folded into `aggregator`; nothing to retain here
    return aggregator.finalize()
