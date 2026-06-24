"""FastAPI application entrypoint."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.evaluation import router as evaluation_router
from app.api.intent import router as intent_router
from app.api.runtime import router as runtime_router
from app.api.schema_generation import router as schema_generation_router
from app.api.system_design import router as system_design_router
from app.api.validation import router as validation_router
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)
origins = [
    "http://localhost:5173",
    "https://ai-compiler-frontend.onrender.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(intent_router)
app.include_router(system_design_router)
app.include_router(schema_generation_router)
app.include_router(validation_router)
app.include_router(runtime_router)
app.include_router(evaluation_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
