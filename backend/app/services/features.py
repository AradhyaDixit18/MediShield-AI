"""Shared, data-driven feature transformation.

This module is the SINGLE SOURCE OF TRUTH for turning a raw record (the values a
user enters in the UI) into the numeric matrix the model expects. It is imported
by BOTH the training script and the inference API so the two can never drift.

A `spec` (stored in each model's meta.json) fully describes the transform:

spec = {
    "numeric_fields": [
        {"name": "Glucose", "median": 117.0, "zero_is_missing": True},
        ...
    ],
    "categorical_fields": [
        {"name": "smoking_status", "categories": ["Unknown", "formerly smoked", ...]},
        ...
    ],
}

The processed column order is:
    [numeric fields in order]  +  [f"{cat}={value}" for each category of each cat field]
"""
from __future__ import annotations

from typing import Any
import numpy as np


def processed_columns(spec: dict) -> list[str]:
    cols: list[str] = [f["name"] for f in spec["numeric_fields"]]
    for f in spec["categorical_fields"]:
        for cat in f["categories"]:
            cols.append(f"{f['name']}={cat}")
    return cols


def field_index_map(spec: dict) -> dict[str, list[int]]:
    """Map each original field name -> the processed column indices it owns.

    Numeric fields own exactly one column; a categorical field owns its whole
    one-hot group (so SHAP values can be summed back to a single field).
    """
    mapping: dict[str, list[int]] = {}
    i = 0
    for f in spec["numeric_fields"]:
        mapping[f["name"]] = [i]
        i += 1
    for f in spec["categorical_fields"]:
        idxs = []
        for _ in f["categories"]:
            idxs.append(i)
            i += 1
        mapping[f["name"]] = idxs
    return mapping


def _to_float(value: Any) -> float:
    if value is None:
        return np.nan
    if isinstance(value, str):
        v = value.strip()
        if v == "" or v.upper() in {"N/A", "NA", "NAN", "NONE"}:
            return np.nan
        try:
            return float(v)
        except ValueError:
            return np.nan
    try:
        return float(value)
    except (TypeError, ValueError):
        return np.nan


def transform_records(records: list[dict], spec: dict) -> np.ndarray:
    """Transform a list of raw record dicts into a numeric matrix."""
    rows = []
    for rec in records:
        row: list[float] = []
        # numeric
        for f in spec["numeric_fields"]:
            val = _to_float(rec.get(f["name"]))
            if f.get("zero_is_missing") and val == 0:
                val = np.nan
            if np.isnan(val):
                val = float(f["median"])
            row.append(val)
        # categorical one-hot
        for f in spec["categorical_fields"]:
            raw = rec.get(f["name"])
            raw = "" if raw is None else str(raw).strip()
            for cat in f["categories"]:
                row.append(1.0 if raw == str(cat) else 0.0)
        rows.append(row)
    return np.asarray(rows, dtype=float)
