"""FastAPI application entrypoint."""
from fastapi import FastAPI

from app.api.intent import router as intent_router
from app.api.system_design import router as system_design_router
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)
app.include_router(intent_router)
app.include_router(system_design_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
