"""API routes for the Validation & Repair compiler stage."""
from fastapi import APIRouter

from app.models.validation import ValidationReport
from app.schemas.validation import ValidationRequest
from app.services.validation import ValidationService

router = APIRouter(tags=["validation"])
_service = ValidationService()


@router.post("/validate", response_model=ValidationReport)
def validate_pipeline(request: ValidationRequest) -> ValidationReport:
    """Validate cross-stage consistency between the given IntentIR, SystemDesign, and DataSchema."""
    return _service.validate(request.intent_ir, request.system_design, request.data_schema)
