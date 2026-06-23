"""Request schema for the Schema Generation API."""
from pydantic import BaseModel

from app.models.intent import IntentIR
from app.models.system_design import SystemDesign


class SchemaGenerationRequest(BaseModel):
    """The payload accepted by POST /schema-generation."""

    intent_ir: IntentIR
    system_design: SystemDesign
