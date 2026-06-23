"""Request schema for the Intent Extraction API."""
from pydantic import BaseModel


class IntentExtractionRequest(BaseModel):
    """The payload accepted by POST /intent/extract."""

    prompt: str
