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
