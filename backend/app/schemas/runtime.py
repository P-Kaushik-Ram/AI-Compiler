"""Request schema for the Runtime compilation API."""
from pydantic import BaseModel


class CompileRequest(BaseModel):
    """The payload accepted by POST /compile."""

    prompt: str
