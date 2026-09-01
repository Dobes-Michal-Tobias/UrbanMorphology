# module: ml_model

Optional module — copy this whole folder into `src/` (or `src/ml_model/`) of a
project that trains a classifier/model and needs a reusable OOP structure
plus a training loop that follows the project's logging conventions.

## Contents

- `model.py` — `BaseModel` abstract wrapper around a scikit-learn-style
  estimator (`fit`/`predict`/`predict_proba`), so notebooks call
  `model.fit(X, y)` / `model.evaluate(X, y)` instead of juggling raw
  estimator objects. Subclass it per algorithm (`LogisticRegressionModel`,
  `RandomForestModel`, ...) or swap the backend for PyTorch by reimplementing
  `fit`/`predict_proba`.
- `metrics.py` — `classification_metrics()` returning F1, precision, recall,
  AUPRC (per this project's convention — see `principles.md`).
- `train_loop.py` — example training/evaluation loop: progress bar,
  incremental CSV logging via `src/io_utils.append_row_csv`, and a results
  plot via `src/viz.py`.

## How to pull just this module

```bash
git clone --no-checkout https://github.com/<you>/research-template.git tmp_template
cd tmp_template
git sparse-checkout init --cone
git sparse-checkout set modules/ml_model
git checkout
# copy modules/ml_model/* into your project's src/
```

## Usage sketch

```python
from ml_model.model import SklearnModel
from ml_model.train_loop import train_and_log
from sklearn.ensemble import RandomForestClassifier

model = SklearnModel(RandomForestClassifier(random_state=RANDOM_SEED))
results = train_and_log(model, X_train, y_train, X_val, y_val, run_name="rf_baseline")
```
