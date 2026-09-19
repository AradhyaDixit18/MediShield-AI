"""API routes for MediShield AI."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile, File

from app.core.config import LLM_API_KEY
from app.schemas.prediction import PredictRequest, PredictResponse
from app.services.model_registry import get_registry
from app.services.predict import predict
from app.services import report as report_service
from app.services import oral as oral_service

router = APIRouter()

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB

ORAL_SUMMARY = {
    "id": "oral",
    "title": oral_service.TITLE,
    "kind": "guideline",
    "metrics": {"basis": "WHO Oral Health & ADA risk factors"},
    "n_fields": len(oral_service.FIELDS),
}


@router.get("/diseases")
def list_diseases():
    """List available disease models with their metrics."""
    return {"diseases": get_registry().list_diseases() + [ORAL_SUMMARY]}


@router.get("/diseases/{disease}/schema")
def disease_schema(disease: str):
    """Return the form field schema + metrics for one disease (drives the UI form)."""
    if disease == "oral":
        return {
            "id": "oral",
            "title": oral_service.TITLE,
            "positive_label": oral_service.POSITIVE_LABEL,
            "fields": oral_service.FIELDS,
            "metrics": {"basis": "WHO Oral Health & ADA risk factors"},
            "kind": "guideline",
        }
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


@router.post("/predict/{disease}")
def predict_disease(disease: str, body: PredictRequest):
    """Run a risk prediction/screening with explanation and recommendations."""
    if not body.features:
        raise HTTPException(status_code=422, detail="No features provided")
    if disease == "oral":
        try:
            return oral_service.assess(body.features)
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=f"Screening failed: {e}")
    try:
        m = get_registry().get(disease)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown disease '{disease}'")
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


@router.post("/report/analyze-text")
def analyze_report_text(body: dict):
    """Analyze already-extracted report text (e.g. OCR done in the browser).
    Lightweight: no OCR or file rendering on the server."""
    text = (body or {}).get("text", "")
    if not isinstance(text, str) or not text.strip():
        raise HTTPException(status_code=422, detail="No text provided")
    method = (body.get("method") if isinstance(body, dict) else None) or "client"
    try:
        return report_service.analyze_text(text, str(method))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")


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
