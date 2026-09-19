"""Application configuration."""
from __future__ import annotations

import os
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = APP_DIR / "artifacts"

APP_NAME = "MediShield AI"
APP_VERSION = "1.0.0"

# Comma-separated list of allowed origins. "*" allows all (fine for a public demo).
_origins = os.getenv("CORS_ORIGINS", "*").strip()
CORS_ORIGINS = ["*"] if _origins in ("", "*") else [o.strip() for o in _origins.split(",")]

# Optional LLM key for the (future) copilot layer. Absent = copilot disabled.
LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()
