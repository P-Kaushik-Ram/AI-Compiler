"""FastAPI application entrypoint."""
from fastapi import FastAPI

from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
