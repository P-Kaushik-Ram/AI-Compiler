"""API routes for the System Design compiler stage."""
from fastapi import APIRouter

from app.models.intent import IntentIR
from app.models.system_design import SystemDesign
from app.services.system_design import SystemDesignService

router = APIRouter(tags=["system-design"])
_service = SystemDesignService()


@router.post("/system-design", response_model=SystemDesign)
def generate_system_design(intent_ir: IntentIR) -> SystemDesign:
    """Generate a SystemDesign from the given IntentIR."""
    return _service.build(intent_ir)
