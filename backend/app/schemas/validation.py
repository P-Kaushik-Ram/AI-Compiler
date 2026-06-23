"""Request schema for the Validation & Repair API."""
from pydantic import BaseModel

from app.models.data_schema import DataSchema
from app.models.intent import IntentIR
from app.models.system_design import SystemDesign


class ValidationRequest(BaseModel):
    """The payload accepted by POST /validate."""

    intent_ir: IntentIR
    system_design: SystemDesign
    data_schema: DataSchema
