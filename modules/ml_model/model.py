"""OOP wrapper around scikit-learn-style estimators.

Subclass `BaseModel` per algorithm/backend so notebooks always call the same
`fit` / `predict` / `predict_proba` / `evaluate` interface, regardless of
whether the underlying model is scikit-learn, XGBoost, or a hand-rolled
PyTorch module.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from .metrics import classification_metrics


class BaseModel(ABC):
    """Common interface every concrete model wrapper must implement."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def fit(self, X, y) -> "BaseModel":
        ...

    @abstractmethod
    def predict(self, X) -> np.ndarray:
        ...

    @abstractmethod
    def predict_proba(self, X) -> np.ndarray:
        """Return probability of the positive class, shape (n_samples,)."""
        ...

    def evaluate(self, X, y) -> dict:
        y_pred = self.predict(X)
        y_score = self.predict_proba(X)
        return classification_metrics(y, y_pred, y_score)

    def save(self, path: Path) -> None:
        joblib.dump(self, Path(path))

    @classmethod
    def load(cls, path: Path) -> "BaseModel":
        return joblib.load(Path(path))


class SklearnModel(BaseModel):
    """Wraps any scikit-learn-compatible estimator (fit/predict/predict_proba)."""

    def __init__(self, estimator: Any, name: str | None = None):
        super().__init__(name or estimator.__class__.__name__)
        self.estimator = estimator

    def fit(self, X, y) -> "SklearnModel":
        self.estimator.fit(X, y)
        return self

    def predict(self, X) -> np.ndarray:
        return self.estimator.predict(X)

    def predict_proba(self, X) -> np.ndarray:
        return self.estimator.predict_proba(X)[:, 1]
