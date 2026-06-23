"""API routes for the Intent Extraction compiler stage."""
from fastapi import APIRouter

from app.models.intent import IntentIR
from app.schemas.intent import IntentExtractionRequest
from app.services.intent_extraction import IntentExtractionService

router = APIRouter(prefix="/intent", tags=["intent"])
_service = IntentExtractionService()


@router.post("/extract", response_model=IntentIR)
def extract_intent(request: IntentExtractionRequest) -> IntentIR:
    """Extract a structured IntentIR from the given raw natural-language prompt."""
    return _service.extract(request.prompt)
