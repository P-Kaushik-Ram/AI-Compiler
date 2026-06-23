"""API routes for the Schema Generation compiler stage."""
from fastapi import APIRouter

from app.models.data_schema import DataSchema
from app.schemas.schema_generation import SchemaGenerationRequest
from app.services.schema_generation import SchemaGenerationService

router = APIRouter(tags=["schema-generation"])
_service = SchemaGenerationService()


@router.post("/schema-generation", response_model=DataSchema)
def generate_data_schema(request: SchemaGenerationRequest) -> DataSchema:
    """Generate a DataSchema from the given IntentIR and SystemDesign."""
    return _service.generate(request.intent_ir, request.system_design)
