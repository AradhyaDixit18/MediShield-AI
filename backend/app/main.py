"""MediShield AI — FastAPI application entrypoint."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import APP_NAME, APP_VERSION, CORS_ORIGINS
from app.services.model_registry import get_registry


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Load models + SHAP explainers once at boot so the first request is fast.
    get_registry()
    yield


app = FastAPI(
    title=APP_NAME,
    description="Explainable Preventive Healthcare Intelligence Platform",
    version=APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
def root():
    reg = get_registry()
    return {
        "status": "success",
        "message": "MediShield AI Backend Running",
        "version": APP_VERSION,
        "diseases": list(reg.models.keys()),
    }


@app.get("/health")
def health():
    return {"status": "healthy", "models_loaded": len(get_registry().models)}
