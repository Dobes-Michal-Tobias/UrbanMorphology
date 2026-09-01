"""Example training/evaluation loop following this project's conventions:
progress bar, incremental CSV logging (crash-safe), metrics = F1/precision/
recall/AUPRC, and a results plot saved via src/viz.py.

Assumes this module was copied into a project that has `src/io_utils.py`,
`src/viz.py` and `src/config.py` (the core template modules).
"""

from datetime import datetime, timezone

import pandas as pd

from src.config import MODELS_DIR, REPORTS_DIR
from src.io_utils import append_row_csv, iter_progress
from src.viz import plot_barplot, save_fig, set_style

from .model import BaseModel

RESULTS_CSV = REPORTS_DIR / "training_results.csv"


def train_and_log(
    model: BaseModel,
    X_train,
    y_train,
    X_val,
    y_val,
    run_name: str,
    save_model: bool = True,
) -> dict:
    """Fit `model`, evaluate on validation data, append metrics to
    reports/training_results.csv, and save the model checkpoint.

    For a multi-epoch/iterative model, wrap the fit step itself in
    `iter_progress(range(n_epochs), desc=run_name)` instead of this
    single-bar version.
    """
    for _ in iter_progress([0], desc=f"training {run_name}"):
        model.fit(X_train, y_train)

    metrics = model.evaluate(X_val, y_val)

    row = {
        "run_name": run_name,
        "model": model.name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **metrics,
    }
    append_row_csv(RESULTS_CSV, row)

    if save_model:
        model.save(MODELS_DIR / f"{run_name}.joblib")

    return row


def plot_results(results_csv=RESULTS_CSV, metric: str = "f1"):
    """Bar plot comparing `metric` across all logged runs."""
    set_style()
    df = pd.read_csv(results_csv)
    ax = plot_barplot(df, x="run_name", y=metric, title=f"{metric} by run")
    save_fig(ax.figure, f"training_{metric}_comparison")
    return ax
