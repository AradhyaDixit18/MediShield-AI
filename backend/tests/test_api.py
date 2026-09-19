"""Basic API tests. Run:  cd backend && pytest -q"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["status"] == "success"


def test_health():
    r = client.get("/health")
    assert r.json()["models_loaded"] == 3


def test_list_diseases():
    r = client.get("/api/diseases")
    ids = {d["id"] for d in r.json()["diseases"]}
    assert ids == {"diabetes", "heart", "stroke"}


def test_schema_has_fields():
    r = client.get("/api/diseases/diabetes/schema")
    assert r.status_code == 200
    assert len(r.json()["fields"]) == 8


def test_predict_high_and_low_diabetes():
    high = client.post("/api/predict/diabetes", json={"features": {
        "Pregnancies": 6, "Glucose": 190, "BloodPressure": 92, "SkinThickness": 35,
        "Insulin": 250, "BMI": 38.5, "DiabetesPedigreeFunction": 0.9, "Age": 54}}).json()
    low = client.post("/api/predict/diabetes", json={"features": {
        "Pregnancies": 1, "Glucose": 85, "BloodPressure": 66, "SkinThickness": 20,
        "Insulin": 90, "BMI": 22.0, "DiabetesPedigreeFunction": 0.2, "Age": 22}}).json()
    assert high["risk_percent"] > low["risk_percent"]
    assert 0 <= high["risk_percent"] <= 100
    assert len(high["top_factors"]) > 0
    assert len(high["recommendations"]) > 0


def test_predict_heart_high_risk_is_high():
    r = client.post("/api/predict/heart", json={"features": {
        "age": 63, "sex": 1, "cp": 0, "trestbps": 145, "chol": 270, "fbs": 1,
        "restecg": 0, "thalach": 109, "exang": 1, "oldpeak": 2.4, "slope": 2,
        "ca": 2, "thal": 3}}).json()
    assert r["risk_percent"] > 50  # disease-present profile should read high


def test_unknown_disease_404():
    assert client.get("/api/diseases/cancer/schema").status_code == 404


def test_report_parsing_from_text():
    from app.services.report import analyze_text
    text = (
        "Fasting Glucose 142 mg/dL 70 - 99\n"
        "HbA1c 6.8 % 4.0 - 5.6\n"
        "Total Cholesterol 236 mg/dL 0 - 200\n"
        "HDL Cholesterol 38 mg/dL 40 - 60\n"
        "Hemoglobin 14.6 g/dL 13.0 - 17.0\n"
        "Vitamin D 18 ng/mL 30 - 100\n"
    )
    d = analyze_text(text)
    names = {r["name"] for r in d["results"]}
    assert "Total Cholesterol" in names and "HDL Cholesterol" in names
    # total cholesterol must not be confused with HDL's value
    tc = next(r for r in d["results"] if r["name"] == "Total Cholesterol")
    assert tc["value"] == 236.0 and tc["status"] == "High"
    hb = next(r for r in d["results"] if r["name"] == "Hemoglobin")
    assert hb["status"] == "Normal"
    assert d["counts"]["abnormal"] >= 4
    assert "diabetes" in d["related_assessments"]
