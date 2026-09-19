"""Rule-based, evidence-informed preventive recommendations.

These are general preventive-health suggestions derived from the entered values
and the model's top risk drivers. They are NOT a diagnosis or medical advice.
No LLM/API key required.
"""
from __future__ import annotations

from typing import Any


def _f(rec: dict, key: str, default: float = 0.0) -> float:
    try:
        return float(rec.get(key))
    except (TypeError, ValueError):
        return default


def _rec(category: str, title: str, detail: str, severity: str = "info") -> dict:
    return {"category": category, "title": title, "detail": detail, "severity": severity}


def diabetes(rec: dict) -> list[dict]:
    out: list[dict] = []
    glucose, bmi, age = _f(rec, "Glucose"), _f(rec, "BMI"), _f(rec, "Age")
    bp, insulin = _f(rec, "BloodPressure"), _f(rec, "Insulin")
    if glucose >= 140:
        out.append(_rec("Blood Sugar", "Monitor blood glucose", "Your glucose reading is high. Consider an HbA1c test and reduce refined sugar and simple carbohydrates.", "high"))
    elif glucose >= 110:
        out.append(_rec("Blood Sugar", "Watch carbohydrate intake", "Glucose is in the pre-diabetic range. Favor whole grains, fiber, and low-glycemic foods.", "medium"))
    if bmi >= 30:
        out.append(_rec("Weight", "Work toward a healthy weight", "A BMI above 30 raises diabetes risk. A 5–7% weight reduction meaningfully lowers risk.", "high"))
    elif bmi >= 25:
        out.append(_rec("Weight", "Maintain an active routine", "BMI is slightly elevated. Aim for 150 minutes of moderate activity per week.", "medium"))
    if bp >= 90:
        out.append(_rec("Blood Pressure", "Manage blood pressure", "Elevated diastolic pressure often accompanies metabolic risk. Reduce sodium and monitor regularly.", "medium"))
    if insulin and insulin >= 200:
        out.append(_rec("Metabolic", "Discuss insulin resistance", "High serum insulin may indicate insulin resistance. A clinician can advise on screening.", "medium"))
    if age >= 45:
        out.append(_rec("Screening", "Regular screening", "Age is a non-modifiable factor. Routine metabolic screening is recommended from age 45.", "info"))
    out.append(_rec("Lifestyle", "Movement and diet", "Regular exercise, a fiber-rich diet, and limiting sugary drinks are the strongest preventive levers.", "info"))
    return out


def heart(rec: dict) -> list[dict]:
    out: list[dict] = []
    chol, bp, age = _f(rec, "chol"), _f(rec, "trestbps"), _f(rec, "age")
    thalach, oldpeak = _f(rec, "thalach"), _f(rec, "oldpeak")
    fbs, exang = _f(rec, "fbs"), _f(rec, "exang")
    if chol >= 240:
        out.append(_rec("Cholesterol", "Lower cholesterol", "Cholesterol is high. Reduce saturated fat, add soluble fiber, and discuss a lipid panel with your doctor.", "high"))
    elif chol >= 200:
        out.append(_rec("Cholesterol", "Borderline cholesterol", "Cholesterol is borderline-high. Diet changes and activity can bring it down.", "medium"))
    if bp >= 140:
        out.append(_rec("Blood Pressure", "Address high blood pressure", "Resting BP is in the hypertensive range. Reduce sodium, manage stress, and monitor consistently.", "high"))
    elif bp >= 130:
        out.append(_rec("Blood Pressure", "Elevated blood pressure", "BP is elevated. Lifestyle changes now can prevent progression to hypertension.", "medium"))
    if oldpeak >= 2:
        out.append(_rec("Cardiac", "Follow up on ECG findings", "Notable ST depression can indicate reduced blood flow. A cardiology follow-up is advisable.", "high"))
    if exang >= 1:
        out.append(_rec("Symptoms", "Exercise-induced chest pain", "Angina during exertion warrants clinical evaluation before intense activity.", "high"))
    if thalach and thalach < 100:
        out.append(_rec("Fitness", "Improve cardiovascular fitness", "A low peak heart rate can reflect low fitness. Build aerobic capacity gradually.", "medium"))
    if fbs >= 1:
        out.append(_rec("Blood Sugar", "Manage fasting glucose", "Elevated fasting blood sugar compounds cardiac risk. Address diet and screening.", "medium"))
    if age >= 55:
        out.append(_rec("Screening", "Routine cardiac screening", "Age increases baseline risk. Discuss periodic cardiac risk assessment.", "info"))
    out.append(_rec("Lifestyle", "Heart-healthy habits", "A Mediterranean-style diet, no smoking, and regular aerobic exercise are core protective factors.", "info"))
    return out


def stroke(rec: dict) -> list[dict]:
    out: list[dict] = []
    glucose, bmi, age = _f(rec, "avg_glucose_level"), _f(rec, "bmi"), _f(rec, "age")
    htn, hd = _f(rec, "hypertension"), _f(rec, "heart_disease")
    smoking = str(rec.get("smoking_status", "")).strip()
    if htn >= 1:
        out.append(_rec("Blood Pressure", "Control hypertension", "Hypertension is the leading modifiable stroke risk factor. Consistent BP control is critical.", "high"))
    if hd >= 1:
        out.append(_rec("Cardiac", "Manage heart disease", "Existing heart disease raises stroke risk. Keep up cardiology follow-up and medication adherence.", "high"))
    if glucose >= 140:
        out.append(_rec("Blood Sugar", "Manage blood glucose", "High average glucose contributes to vascular damage. Screen for and manage diabetes.", "high"))
    if smoking == "smokes":
        out.append(_rec("Smoking", "Quit smoking", "Smoking sharply increases stroke risk. Cessation support meaningfully lowers it within years.", "high"))
    elif smoking == "formerly smoked":
        out.append(_rec("Smoking", "Stay smoke-free", "Remaining smoke-free continues to reduce your residual risk over time.", "info"))
    if bmi >= 30:
        out.append(_rec("Weight", "Work toward a healthy weight", "Obesity is linked to higher stroke risk through blood pressure and metabolic effects.", "medium"))
    if age >= 60:
        out.append(_rec("Screening", "Vascular health checks", "Age raises baseline risk. Regular vascular and blood-pressure checks are recommended.", "info"))
    out.append(_rec("Lifestyle", "Reduce vascular risk", "Regular activity, a low-sodium diet, limited alcohol, and blood-pressure control are the strongest levers.", "info"))
    return out


_DISPATCH = {"diabetes": diabetes, "heart": heart, "stroke": stroke}


def recommend(disease: str, rec: dict) -> list[dict]:
    fn = _DISPATCH.get(disease)
    return fn(rec) if fn else []
