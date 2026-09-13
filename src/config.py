"""Central place for paths, constants and environment variables.

Import this from notebooks/other modules instead of hardcoding paths:

    from src.config import DATA_RAW, DATA_PROCESSED, REPORTS_FIGURES

Add project-specific constants (random seed, label names, API model ids...)
here as the project grows.
"""

from pathlib import Path
import sys

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "modules"))
from dataviz_style.chartstyle import (  # noqa: E402
    PRIMARY_COLOR, ACCENT_COLOR, NEUTRAL_COLOR, INK_COLOR, MUTED_COLOR,
    CATEGORICAL_PALETTE,
)

load_dotenv(PROJECT_ROOT / ".env")

DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW = DATA_DIR / "raw"
DATA_INTERIM = DATA_DIR / "interim"
DATA_PROCESSED = DATA_DIR / "processed"
DATA_EXTERNAL = DATA_DIR / "external"

MODELS_DIR = PROJECT_ROOT / "models"

REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_FIGURES = REPORTS_DIR / "figures"

for _dir in (DATA_RAW, DATA_INTERIM, DATA_PROCESSED, DATA_EXTERNAL, MODELS_DIR, REPORTS_FIGURES):
    _dir.mkdir(parents=True, exist_ok=True)

RANDOM_SEED = 42
