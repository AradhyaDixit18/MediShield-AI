"""Oral & Dental Health risk screening (guideline-based, transparent scoring).

Oral disease affects an estimated 3.5 billion people worldwide and is largely
preventable, yet access to screening is deeply unequal. This module gives a fast,
explainable self-check built from established risk factors (WHO Oral Health and
ADA guidance): diet, hygiene, dental-visit history, tobacco, dry mouth, and
symptoms. It is a screening aid and triage nudge, NOT a diagnosis, and it is
clearly labeled as guideline-based rather than a trained ML model.

Output matches the ML predict() shape so it renders in the same UI.
"""
from __future__ import annotations

from typing import Any

TITLE = "Oral & Dental Health"
POSITIVE_LABEL = "Elevated oral-health risk"

# Each field: name, label, type, options/points. Points are signed:
# positive = raises risk, negative = protective.
FIELDS: list[dict] = [
    {"name": "age", "label": "Age", "type": "number", "min": 1, "max": 120, "step": 1,
     "unit": "years", "default": 30, "help": "Age in years"},
    {"name": "sugar_frequency", "label": "Sugary foods/drinks per day", "type": "select", "default": "1-2",
     "help": "How often you consume sugary snacks or drinks",
     "options": [
         {"value": "0", "label": "Rarely / none"},
         {"value": "1-2", "label": "1–2 times"},
         {"value": "3-4", "label": "3–4 times"},
         {"value": "5+", "label": "5 or more"}]},
    {"name": "brushing", "label": "Brushing", "type": "select", "default": "twice",
     "help": "How often you brush your teeth",
     "options": [
         {"value": "twice", "label": "Twice a day or more"},
         {"value": "once", "label": "Once a day"},
         {"value": "less", "label": "Less than daily"}]},
    {"name": "flossing", "label": "Flossing / interdental cleaning", "type": "select", "default": "sometimes",
     "help": "How often you clean between teeth",
     "options": [
         {"value": "daily", "label": "Daily"},
         {"value": "sometimes", "label": "Sometimes"},
         {"value": "never", "label": "Never"}]},
    {"name": "last_dentist", "label": "Last dental visit", "type": "select", "default": "6-12",
     "help": "When you last saw a dentist",
     "options": [
         {"value": "<6", "label": "Within 6 months"},
         {"value": "6-12", "label": "6–12 months ago"},
         {"value": "1-2y", "label": "1–2 years ago"},
         {"value": ">2y", "label": "Over 2 years ago"},
         {"value": "never", "label": "Never"}]},
    {"name": "bleeding_gums", "label": "Bleeding gums", "type": "toggle", "default": 0,
     "help": "Do your gums bleed when brushing or flossing"},
    {"name": "tooth_pain", "label": "Tooth pain or sensitivity", "type": "toggle", "default": 0,
     "help": "Ongoing toothache or sensitivity to hot/cold/sweet"},
    {"name": "visible_cavity", "label": "Visible cavity or hole", "type": "toggle", "default": 0,
     "help": "A visible hole, dark spot, or broken tooth"},
    {"name": "dry_mouth", "label": "Frequent dry mouth", "type": "toggle", "default": 0,
     "help": "Persistent dry mouth reduces natural protection"},
    {"name": "tobacco", "label": "Tobacco use", "type": "toggle", "default": 0,
     "help": "Smoking or chewing tobacco"},
    {"name": "diabetes", "label": "Diabetes", "type": "toggle", "default": 0,
     "help": "Diabetes raises the risk of gum disease"},
]

# Points per answer (signed).
_SELECT_POINTS = {
    "sugar_frequency": {"0": -2, "1-2": 0, "3-4": 3, "5+": 5},
    "brushing": {"twice": -3, "once": 0, "less": 4},
    "flossing": {"daily": -2, "sometimes": 0, "never": 2},
    "last_dentist": {"<6": -3, "6-12": 0, "1-2y": 2, ">2y": 4, "never": 5},
}
_TOGGLE_POINTS = {
    "bleeding_gums": 4, "tooth_pain": 4, "visible_cavity": 6,
    "dry_mouth": 2, "tobacco": 5, "diabetes": 3,
}

_LABELS = {f["name"]: f for f in FIELDS}


def _band(pct: float) -> str:
    if pct < 25:
        return "Low"
    if pct < 50:
        return "Moderate"
    if pct < 75:
        return "High"
    return "Very high"


def _display(field: dict, raw: Any) -> str:
    if field["type"] == "toggle":
        return "Yes" if str(raw) in ("1", "1.0", "True", "true", "yes", "Yes") else "No"
    if field["type"] == "select":
        for o in field.get("options", []):
            if str(o["value"]) == str(raw):
                return str(o["label"])
    unit = field.get("unit", "")
    return f"{raw}{(' ' + unit) if unit else ''}".strip()


def _min_max() -> tuple[float, float]:
    lo = hi = 0.0
    for name, pts in _SELECT_POINTS.items():
        lo += min(pts.values())
        hi += max(pts.values())
    for name, p in _TOGGLE_POINTS.items():
        hi += p  # min is 0 (answer "No")
    # age contribution range
    lo += 0
    hi += 4
    return lo, hi


def assess(record: dict) -> dict[str, Any]:
    factors = []

    # selects
    for name, pts in _SELECT_POINTS.items():
        val = str(record.get(name, _LABELS[name]["default"]))
        p = pts.get(val, 0)
        factors.append((name, float(p)))
    # toggles
    for name, p in _TOGGLE_POINTS.items():
        on = str(record.get(name, 0)) in ("1", "1.0", "True", "true", "yes", "Yes")
        factors.append((name, float(p if on else 0)))
    # age
    try:
        age = float(record.get("age", 30))
    except (TypeError, ValueError):
        age = 30.0
    age_pts = 4.0 if age >= 60 else 2.0 if age >= 40 else 0.0
    factors.append(("age", age_pts))

    score = sum(p for _, p in factors)
    lo, hi = _min_max()
    pct = max(0.0, min(100.0, 100.0 * (score - lo) / (hi - lo)))
    band = _band(pct)

    total_abs = sum(abs(p) for _, p in factors) or 1.0
    out_factors = []
    for name, p in factors:
        field = _LABELS[name]
        out_factors.append({
            "field": name, "label": field["label"],
            "value": _display(field, record.get(name, field.get("default"))),
            "contribution": round(p, 3),
            "direction": "increases" if p > 0 else "decreases",
            "impact_pct": round(100.0 * abs(p) / total_abs, 1),
        })
    out_factors.sort(key=lambda x: abs(x["contribution"]), reverse=True)

    return {
        "disease": "oral",
        "title": TITLE,
        "kind": "guideline",
        "probability": round(pct / 100, 4),
        "risk_percent": round(pct, 1),
        "band": band,
        "positive_label": POSITIVE_LABEL,
        "top_factors": [f for f in out_factors if f["contribution"] != 0][:6] or out_factors[:6],
        "all_factors": out_factors,
        "triage": _triage(band, record),
        "recommendations": _recommend(record, band),
        "model_metrics": {"basis": "WHO Oral Health & ADA risk factors", "kind": "guideline"},
        "disclaimer": (
            "This is a guideline-based screening aid, not a dental diagnosis. It cannot replace an examination "
            "by a dentist. If you have pain, swelling, or bleeding that concerns you, see a dental professional."
        ),
    }


def _triage(band: str, rec: dict) -> str:
    def on(k):
        return str(rec.get(k, 0)) in ("1", "1.0", "True", "true", "yes", "Yes")
    if on("visible_cavity") or on("tooth_pain"):
        return "Book a dental appointment soon (within about 2 weeks). Pain or a visible cavity should be examined."
    if band in ("High", "Very high") or on("bleeding_gums"):
        return "Schedule a dental check-up in the next month. Several risk factors are present."
    return "A routine dental check-up every 6 months is enough based on what you entered."


def _recommend(rec: dict, band: str) -> list[dict]:
    def on(k):
        return str(rec.get(k, 0)) in ("1", "1.0", "True", "true", "yes", "Yes")
    out = []
    r = lambda c, t, d, s="info": out.append({"category": c, "title": t, "detail": d, "severity": s})

    r("Triage", "Next dental visit", _triage(band, rec), "high" if band in ("High", "Very high") else "info")
    sugar = str(rec.get("sugar_frequency", ""))
    if sugar in ("3-4", "5+"):
        r("Diet", "Cut back on sugar frequency", "It is how often, not just how much, sugar you consume that drives decay. Limit sugary snacks and drinks between meals.", "high")
    if str(rec.get("brushing")) in ("once", "less"):
        r("Hygiene", "Brush twice daily with fluoride", "Brush for two minutes, twice a day, with fluoride toothpaste, and avoid rinsing heavily afterward.", "medium")
    if str(rec.get("flossing")) in ("sometimes", "never"):
        r("Hygiene", "Clean between your teeth daily", "Floss or use interdental brushes once a day to reach where a toothbrush cannot.", "medium")
    if on("bleeding_gums"):
        r("Gums", "Address bleeding gums", "Bleeding gums are an early sign of gum disease and are usually reversible with better cleaning and a dental cleaning.", "high")
    if on("tobacco"):
        r("Tobacco", "Stop tobacco use", "Tobacco is a leading cause of gum disease and oral cancer. Quitting sharply lowers your risk.", "high")
    if on("dry_mouth"):
        r("Saliva", "Manage dry mouth", "Saliva protects teeth. Stay hydrated, and ask a dentist about causes if it persists.", "medium")
    if str(rec.get("last_dentist")) in (">2y", "never"):
        r("Screening", "Establish regular dental care", "Regular check-ups catch problems early, when they are cheaper and easier to treat.", "medium")
    r("Prevention", "Everyday protection", "Fluoride toothpaste, limiting sugary snacking, cleaning between teeth, and regular check-ups are the core of prevention.", "info")
    return out
