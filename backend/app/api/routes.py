"""API routes for MediShield AI."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile, File

from app.core.config import LLM_API_KEY
from app.schemas.prediction import PredictRequest, PredictResponse
from app.services.model_registry import get_registry
from app.services.predict import predict
from app.services import report as report_service

router = APIRouter()

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


@router.get("/diseases")
def list_diseases():
    """List available disease models with their metrics."""
    return {"diseases": get_registry().list_diseases()}


@router.get("/diseases/{disease}/schema")
def disease_schema(disease: str):
    """Return the form field schema + metrics for one disease (drives the UI form)."""
    try:
        m = get_registry().get(disease)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown disease '{disease}'")
    return {
        "id": m.name,
        "title": m.title,
        "positive_label": m.positive_label,
        "fields": m.fields,
        "metrics": m.metrics,
    }


@router.post("/predict/{disease}", response_model=PredictResponse)
def predict_disease(disease: str, body: PredictRequest):
    """Run a risk prediction with SHAP explanation and recommendations."""
    try:
        m = get_registry().get(disease)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown disease '{disease}'")
    if not body.features:
        raise HTTPException(status_code=422, detail="No features provided")
    try:
        return predict(m, body.features)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")


@router.post("/report/analyze")
async def analyze_report(file: UploadFile = File(...)):
    """Analyze an uploaded medical/lab report (PDF or image) and return a
    plain-language breakdown of detected values against reference ranges."""
    data = await file.read()
    if not data:
        raise HTTPException(status_code=422, detail="Empty file.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 10 MB).")
    try:
        return report_service.analyze(data, file.filename or "", file.content_type or "")
    except report_service.ReportError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Report analysis failed: {e}")


@router.get("/capabilities")
def capabilities():
    """Report which optional features are active (e.g. LLM copilot)."""
    return {
        "copilot_enabled": bool(LLM_API_KEY),
        "features": {
            "risk_prediction": True,
            "explainability": True,
            "recommendations": True,
            "report_analysis": True,
            "copilot": bool(LLM_API_KEY),
        },
    }
