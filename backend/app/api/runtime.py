"""API routes for the Runtime compiler stage."""
from fastapi import APIRouter

from app.models.runtime import CompilationResult
from app.schemas.runtime import CompileRequest
from app.services.runtime import RuntimeService

router = APIRouter(tags=["runtime"])
_service = RuntimeService()


@router.post("/compile", response_model=CompilationResult)
def compile_prompt(request: CompileRequest) -> CompilationResult:
    """Run the full compiler pipeline for the given prompt and return the CompilationResult."""
    return _service.run(prompt=request.prompt)
