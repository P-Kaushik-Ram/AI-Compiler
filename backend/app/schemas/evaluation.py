"""Request schema for the Evaluation Framework API."""
from pydantic import BaseModel, Field

from app.models.evaluation import DatasetCase


class EvaluationRequest(BaseModel):
    """The payload accepted by POST /evaluate: a named batch of dataset cases to benchmark."""

    dataset_name: str = "api-request"
    cases: list[DatasetCase] = Field(default_factory=list)
