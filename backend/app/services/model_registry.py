"""Loads trained models + SHAP explainers once at startup and serves them."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import shap
import xgboost as xgb

from app.core.config import ARTIFACTS_DIR


class DiseaseModel:
    def __init__(self, name: str, artifacts_dir: Path):
        with open(artifacts_dir / f"{name}_meta.json") as fh:
            self.meta = json.load(fh)
        self.name = name
        self.title = self.meta["title"]
        self.fields = self.meta["fields"]
        self.spec = self.meta["spec"]
        self.columns = self.meta["processed_columns"]
        self.field_index_map = self.meta["field_index_map"]
        self.metrics = self.meta["metrics"]
        self.positive_label = self.meta["positive_label"]

        self.booster = xgb.Booster()
        self.booster.load_model(str(artifacts_dir / f"{name}_model.json"))
        self.booster.feature_names = self.columns
        self.explainer = shap.TreeExplainer(self.booster)

    def _dmatrix(self, X: np.ndarray) -> xgb.DMatrix:
        return xgb.DMatrix(X, feature_names=self.columns)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self.booster.predict(self._dmatrix(X))

    def shap_values(self, X: np.ndarray):
        sv = self.explainer.shap_values(X)
        base = self.explainer.expected_value
        if isinstance(base, (list, np.ndarray)) and np.ndim(base) > 0:
            base = float(np.ravel(base)[0])
        return np.asarray(sv), float(base)


class Registry:
    def __init__(self, artifacts_dir: Path):
        self.artifacts_dir = artifacts_dir
        with open(artifacts_dir / "index.json") as fh:
            self.index = json.load(fh)
        self.models: dict[str, DiseaseModel] = {
            name: DiseaseModel(name, artifacts_dir) for name in self.index
        }

    def get(self, name: str) -> DiseaseModel:
        if name not in self.models:
            raise KeyError(name)
        return self.models[name]

    def list_diseases(self) -> list[dict]:
        return [
            {
                "id": name,
                "title": m.title,
                "metrics": m.metrics,
                "n_fields": len(m.fields),
            }
            for name, m in self.models.items()
        ]


@lru_cache(maxsize=1)
def get_registry() -> Registry:
    return Registry(ARTIFACTS_DIR)
