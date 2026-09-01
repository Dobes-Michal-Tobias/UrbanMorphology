"""Classification metrics used consistently across all model training in
this project (see principles.md): F1, precision, recall, AUPRC.

Binary classification is the default case. For multiclass, pass
`average="macro"` (or "weighted") — AUPRC then needs one-vs-rest scores,
see `multiclass_average_precision`.
"""

import numpy as np
from sklearn.metrics import average_precision_score, f1_score, precision_score, recall_score


def classification_metrics(y_true, y_pred, y_score, average: str = "binary") -> dict:
    """y_score: predicted probability/score of the positive class."""
    return {
        "f1": f1_score(y_true, y_pred, average=average),
        "precision": precision_score(y_true, y_pred, average=average),
        "recall": recall_score(y_true, y_pred, average=average),
        "auprc": average_precision_score(y_true, y_score),
    }


def multiclass_average_precision(y_true, y_score: np.ndarray, average: str = "macro") -> float:
    """y_score: shape (n_samples, n_classes) of per-class probabilities."""
    y_true_onehot = np.eye(y_score.shape[1])[y_true]
    return average_precision_score(y_true_onehot, y_score, average=average)
