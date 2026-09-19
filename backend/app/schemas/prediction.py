"""Pydantic schemas for the prediction API."""
from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    features: dict[str, Any] = Field(..., description="Raw field values keyed by field name")


class Factor(BaseModel):
    field: str
    label: str
    value: str
    contribution: float
    direction: str
    impact_pct: float


class Recommendation(BaseModel):
    category: str
    title: str
    detail: str
    severity: str


class PredictResponse(BaseModel):
    disease: str
    title: str
    probability: float
    risk_percent: float
    base_rate: float
    times_average: float
    band: str
    positive_label: str
    top_factors: list[Factor]
    all_factors: list[Factor]
    recommendations: list[Recommendation]
    model_metrics: dict[str, Any]
    disclaimer: str
