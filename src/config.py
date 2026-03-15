"""Application configuration constants."""

from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
VOL_DIR = DATA_DIR / "vols"
PRICE_DIR = DATA_DIR / "prices"
RVOL_DIR = DATA_DIR / "rvols"
SAMPLE_DIR = DATA_DIR / "samples"

DEFAULT_REALIZED_WINDOW = 60
DEFAULT_RETURN_TYPE = "log"
WEIGHT_TOLERANCE_PCT = 0.5
MIN_CONSTITUENTS = 2
EPSILON = 1e-10
