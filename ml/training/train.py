"""Train MediShield AI risk models (diabetes, heart disease, stroke).

Produces, per disease, in backend/app/artifacts/:
  <disease>_model.json    XGBoost model (portable JSON booster)
  <disease>_meta.json     feature spec + UI metadata + metrics + column order

Run:  python ml/training/train.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score
from xgboost import XGBClassifier

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.features import transform_records, processed_columns, field_index_map  # noqa: E402

DATA = ROOT / "ml" / "data"
ARTIFACTS = ROOT / "backend" / "app" / "artifacts"
ARTIFACTS.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Per-disease configuration. `fields` drives BOTH the model and the UI forms.
# type: "number" | "select" | "toggle"
# ---------------------------------------------------------------------------
CONFIGS = {
    "diabetes": {
        "title": "Diabetes Risk",
        "csv": "diabetes.csv",
        "target": "Outcome",
        "positive_label": "Likely diabetic",
        "fields": [
            {"name": "Pregnancies", "label": "Pregnancies", "type": "number", "min": 0, "max": 17, "step": 1, "unit": "", "default": 1, "help": "Number of times pregnant"},
            {"name": "Glucose", "label": "Glucose", "type": "number", "min": 40, "max": 300, "step": 1, "unit": "mg/dL", "default": 117, "zero_is_missing": True, "help": "Plasma glucose concentration (oral glucose tolerance test)"},
            {"name": "BloodPressure", "label": "Blood Pressure", "type": "number", "min": 30, "max": 180, "step": 1, "unit": "mm Hg", "default": 72, "zero_is_missing": True, "help": "Diastolic blood pressure"},
            {"name": "SkinThickness", "label": "Skin Thickness", "type": "number", "min": 0, "max": 100, "step": 1, "unit": "mm", "default": 23, "zero_is_missing": True, "help": "Triceps skinfold thickness"},
            {"name": "Insulin", "label": "Insulin", "type": "number", "min": 0, "max": 900, "step": 1, "unit": "mu U/ml", "default": 30, "zero_is_missing": True, "help": "2-hour serum insulin"},
            {"name": "BMI", "label": "BMI", "type": "number", "min": 10, "max": 70, "step": 0.1, "unit": "kg/m²", "default": 32, "zero_is_missing": True, "help": "Body mass index"},
            {"name": "DiabetesPedigreeFunction", "label": "Pedigree Function", "type": "number", "min": 0.05, "max": 2.5, "step": 0.01, "unit": "", "default": 0.37, "help": "Diabetes likelihood based on family history"},
            {"name": "Age", "label": "Age", "type": "number", "min": 1, "max": 120, "step": 1, "unit": "years", "default": 33, "help": "Age in years"},
        ],
    },
    "heart": {
        "title": "Heart Disease Risk",
        "csv": "heart.csv",
        "target": "target",
        "positive_class": 0,  # NOTE: in this UCI CSV, target=0 means disease PRESENT (verified empirically)
        "positive_label": "Heart disease likely",
        "fields": [
            {"name": "age", "label": "Age", "type": "number", "min": 1, "max": 120, "step": 1, "unit": "years", "default": 54, "help": "Age in years"},
            {"name": "sex", "label": "Sex", "type": "select", "default": 1, "options": [{"value": 1, "label": "Male"}, {"value": 0, "label": "Female"}], "help": "Biological sex"},
            {"name": "cp", "label": "Chest Pain Type", "type": "select", "default": 0, "options": [{"value": 0, "label": "Typical angina"}, {"value": 1, "label": "Atypical angina"}, {"value": 2, "label": "Non-anginal pain"}, {"value": 3, "label": "Asymptomatic"}], "help": "Type of chest pain experienced"},
            {"name": "trestbps", "label": "Resting Blood Pressure", "type": "number", "min": 80, "max": 220, "step": 1, "unit": "mm Hg", "default": 131, "help": "Resting blood pressure on admission"},
            {"name": "chol", "label": "Cholesterol", "type": "number", "min": 100, "max": 600, "step": 1, "unit": "mg/dL", "default": 246, "help": "Serum cholesterol"},
            {"name": "fbs", "label": "Fasting Blood Sugar > 120", "type": "toggle", "default": 0, "help": "Is fasting blood sugar greater than 120 mg/dL"},
            {"name": "restecg", "label": "Resting ECG", "type": "select", "default": 1, "options": [{"value": 0, "label": "Normal"}, {"value": 1, "label": "ST-T abnormality"}, {"value": 2, "label": "LV hypertrophy"}], "help": "Resting electrocardiographic result"},
            {"name": "thalach", "label": "Max Heart Rate", "type": "number", "min": 60, "max": 220, "step": 1, "unit": "bpm", "default": 150, "help": "Maximum heart rate achieved"},
            {"name": "exang", "label": "Exercise-Induced Angina", "type": "toggle", "default": 0, "help": "Angina induced by exercise"},
            {"name": "oldpeak", "label": "ST Depression", "type": "number", "min": 0, "max": 7, "step": 0.1, "unit": "", "default": 1.0, "help": "ST depression induced by exercise relative to rest"},
            {"name": "slope", "label": "ST Slope", "type": "select", "default": 1, "options": [{"value": 0, "label": "Upsloping"}, {"value": 1, "label": "Flat"}, {"value": 2, "label": "Downsloping"}], "help": "Slope of the peak exercise ST segment"},
            {"name": "ca", "label": "Major Vessels", "type": "select", "default": 0, "options": [{"value": 0, "label": "0"}, {"value": 1, "label": "1"}, {"value": 2, "label": "2"}, {"value": 3, "label": "3"}, {"value": 4, "label": "4"}], "help": "Number of major vessels colored by fluoroscopy"},
            {"name": "thal", "label": "Thalassemia", "type": "select", "default": 2, "options": [{"value": 0, "label": "Unknown"}, {"value": 1, "label": "Normal"}, {"value": 2, "label": "Fixed defect"}, {"value": 3, "label": "Reversible defect"}], "help": "Thalassemia blood disorder status"},
        ],
    },
    "stroke": {
        "title": "Stroke Risk",
        "csv": "stroke.csv",
        "target": "stroke",
        "positive_label": "Elevated stroke risk",
        "drop": ["id"],
        "fields": [
            {"name": "gender", "label": "Gender", "type": "select", "default": "Female", "categorical": True, "options": [{"value": "Male", "label": "Male"}, {"value": "Female", "label": "Female"}, {"value": "Other", "label": "Other"}], "help": "Gender"},
            {"name": "age", "label": "Age", "type": "number", "min": 1, "max": 120, "step": 1, "unit": "years", "default": 45, "help": "Age in years"},
            {"name": "hypertension", "label": "Hypertension", "type": "toggle", "default": 0, "help": "Diagnosed with hypertension"},
            {"name": "heart_disease", "label": "Heart Disease", "type": "toggle", "default": 0, "help": "Diagnosed with heart disease"},
            {"name": "ever_married", "label": "Ever Married", "type": "select", "default": "Yes", "categorical": True, "options": [{"value": "Yes", "label": "Yes"}, {"value": "No", "label": "No"}], "help": "Has the person ever been married"},
            {"name": "work_type", "label": "Work Type", "type": "select", "default": "Private", "categorical": True, "options": [{"value": "Private", "label": "Private"}, {"value": "Self-employed", "label": "Self-employed"}, {"value": "Govt_job", "label": "Government job"}, {"value": "children", "label": "Children"}, {"value": "Never_worked", "label": "Never worked"}], "help": "Type of employment"},
            {"name": "Residence_type", "label": "Residence Type", "type": "select", "default": "Urban", "categorical": True, "options": [{"value": "Urban", "label": "Urban"}, {"value": "Rural", "label": "Rural"}], "help": "Residence type"},
            {"name": "avg_glucose_level", "label": "Avg Glucose Level", "type": "number", "min": 50, "max": 300, "step": 0.1, "unit": "mg/dL", "default": 106, "help": "Average glucose level in blood"},
            {"name": "bmi", "label": "BMI", "type": "number", "min": 10, "max": 70, "step": 0.1, "unit": "kg/m²", "default": 28.9, "help": "Body mass index"},
            {"name": "smoking_status", "label": "Smoking Status", "type": "select", "default": "never smoked", "categorical": True, "options": [{"value": "never smoked", "label": "Never smoked"}, {"value": "formerly smoked", "label": "Formerly smoked"}, {"value": "smokes", "label": "Smokes"}, {"value": "Unknown", "label": "Unknown"}], "help": "Smoking status"},
        ],
    },
}


def build_spec(cfg: dict, df: pd.DataFrame) -> dict:
    numeric_fields, categorical_fields = [], []
    for f in cfg["fields"]:
        if f.get("categorical"):
            cats = [o["value"] for o in f["options"]]
            categorical_fields.append({"name": f["name"], "categories": cats})
        else:
            col = pd.to_numeric(df[f["name"]], errors="coerce")
            if f.get("zero_is_missing"):
                col = col.replace(0, np.nan)
            median = float(np.nanmedian(col.values))
            numeric_fields.append({"name": f["name"], "median": median, "zero_is_missing": bool(f.get("zero_is_missing", False))})
    return {"numeric_fields": numeric_fields, "categorical_fields": categorical_fields}


def train_one(name: str, cfg: dict) -> dict:
    df = pd.read_csv(DATA / cfg["csv"])
    for c in cfg.get("drop", []):
        if c in df.columns:
            df = df.drop(columns=[c])
    df = df.dropna(subset=[cfg["target"]])
    positive_class = cfg.get("positive_class", 1)
    y = (df[cfg["target"]].astype(int) == positive_class).astype(int).values

    spec = build_spec(cfg, df)
    records = df.to_dict(orient="records")
    X = transform_records(records, spec)
    cols = processed_columns(spec)

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    pos = int(y_tr.sum())
    neg = int(len(y_tr) - pos)
    spw = (neg / pos) if pos else 1.0

    model = XGBClassifier(
        n_estimators=400, max_depth=4, learning_rate=0.05,
        subsample=0.9, colsample_bytree=0.9, min_child_weight=2,
        reg_lambda=1.0, scale_pos_weight=spw, eval_metric="logloss",
        n_jobs=4, random_state=42,
    )
    model.fit(X_tr, y_tr)

    proba = model.predict_proba(X_te)[:, 1]
    pred = (proba >= 0.5).astype(int)
    metrics = {
        "roc_auc": round(float(roc_auc_score(y_te, proba)), 4),
        "accuracy": round(float(accuracy_score(y_te, pred)), 4),
        "f1": round(float(f1_score(y_te, pred)), 4),
        "n_samples": int(len(df)),
        "n_positive": int(y.sum()),
        "prevalence": round(float(y.mean()), 4),
    }

    model.get_booster().feature_names = cols
    model.get_booster().save_model(str(ARTIFACTS / f"{name}_model.json"))

    meta = {
        "name": name,
        "title": cfg["title"],
        "positive_label": cfg["positive_label"],
        "target": cfg["target"],
        "fields": cfg["fields"],
        "spec": spec,
        "processed_columns": cols,
        "field_index_map": field_index_map(spec),
        "metrics": metrics,
        "base_rate": round(float(y.mean()), 4),
    }
    with open(ARTIFACTS / f"{name}_meta.json", "w") as fh:
        json.dump(meta, fh, indent=2)

    print(f"[{name:8}] ROC-AUC={metrics['roc_auc']}  ACC={metrics['accuracy']}  "
          f"F1={metrics['f1']}  n={metrics['n_samples']}  prev={metrics['prevalence']}  cols={len(cols)}")
    return meta


def main():
    index = {}
    for name, cfg in CONFIGS.items():
        meta = train_one(name, cfg)
        index[name] = {"title": meta["title"], "metrics": meta["metrics"], "n_fields": len(meta["fields"])}
    with open(ARTIFACTS / "index.json", "w") as fh:
        json.dump(index, fh, indent=2)
    print("\nSaved artifacts to", ARTIFACTS)


if __name__ == "__main__":
    main()
