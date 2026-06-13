from fastapi import FastAPI

app = FastAPI(
    title="MediShield AI",
    description="Explainable Preventive Healthcare Intelligence Platform",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "status": "success",
        "message": "MediShield AI Backend Running"
    }