"""Prediction orchestration: risk score + SHAP explanation + recommendations."""
from __future__ import annotations

from typing import Any

import numpy as np

from app.services.features import transform_records
from app.services.model_registry import DiseaseModel
from app.services.recommend import recommend


def _display_value(field: dict, raw: Any) -> str:
    if field["type"] in ("select", "toggle"):
        if field["type"] == "toggle":
            return "Yes" if str(raw) in ("1", "1.0", "True", "true", "yes", "Yes") else "No"
        for opt in field.get("options", []):
            if str(opt["value"]) == str(raw):
                return str(opt["label"])
    unit = field.get("unit", "")
    return f"{raw}{(' ' + unit) if unit else ''}".strip()


def _band(times: float) -> str:
    if times < 1.0:
        return "Below average"
    if times < 2.0:
        return "Moderate"
    if times < 4.0:
        return "High"
    return "Very high"


def predict(model: DiseaseModel, record: dict) -> dict:
    X = transform_records([record], model.spec)
    proba = float(model.predict_proba(X)[0])
    sv, base = model.shap_values(X)
    sv = sv[0]  # (n_cols,)

    fields_by_name = {f["name"]: f for f in model.fields}
    factors = []
    for fname, idxs in model.field_index_map.items():
        contribution = float(np.sum([sv[i] for i in idxs]))
        field = fields_by_name.get(fname, {"name": fname, "label": fname, "type": "number"})
        factors.append({
            "field": fname,
            "label": field.get("label", fname),
            "value": _display_value(field, record.get(fname)),
            "contribution": round(contribution, 4),
            "direction": "increases" if contribution > 0 else "decreases",
        })
    factors.sort(key=lambda x: abs(x["contribution"]), reverse=True)

    base_rate = float(model.metrics.get("prevalence", model.meta.get("base_rate", 0.1))) or 0.1
    times = proba / base_rate
    total_abs = sum(abs(f["contribution"]) for f in factors) or 1.0
    for f in factors:
        f["impact_pct"] = round(100.0 * abs(f["contribution"]) / total_abs, 1)

    return {
        "disease": model.name,
        "title": model.title,
        "probability": round(proba, 4),
        "risk_percent": round(proba * 100, 1),
        "base_rate": round(base_rate, 4),
        "times_average": round(times, 2),
        "band": _band(times),
        "positive_label": model.positive_label,
        "top_factors": factors[:6],
        "all_factors": factors,
        "recommendations": recommend(model.name, record),
        "model_metrics": model.metrics,
        "disclaimer": (
            "MediShield AI provides preventive-health insight for educational purposes only. "
            "It is not a medical diagnosis. Consult a qualified healthcare professional for medical advice."
        ),
    }
