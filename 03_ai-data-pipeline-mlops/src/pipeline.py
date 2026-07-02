from __future__ import annotations

import hashlib
import json
import platform
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = ROOT / "data" / "raw" / "uci" / "ai4i2020.csv"
ARTIFACTS = ROOT / "artifacts"
MODEL_PATH = ARTIFACTS / "model.joblib"
RESULTS_PATH = ARTIFACTS / "results.json"
METRICS_PATH = ARTIFACTS / "model_metrics.json"
RUNTIME_PATH = ARTIFACTS / "runtime_metrics.json"
PREDICTIONS_PATH = ARTIFACTS / "test_predictions.csv"
MANIFEST_PATH = ARTIFACTS / "model_manifest.json"
PIPELINE_MANIFEST_PATH = ARTIFACTS / "pipeline_manifest.json"

MODEL_VERSION = "0.2.0"
FEATURES = [
    "Type",
    "Air temperature [K]",
    "Process temperature [K]",
    "Rotational speed [rpm]",
    "Torque [Nm]",
    "Tool wear [min]",
]
NUMERIC = FEATURES[1:]
TARGET = "Machine failure"
REQUIRED = [
    "UDI",
    "Product ID",
    *FEATURES,
    TARGET,
    "TWF",
    "HDF",
    "PWF",
    "OSF",
    "RNF",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def canonical_json_hash(data: dict) -> str:
    payload = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest().upper()


def validate_frame(df: pd.DataFrame, require_authoritative_size: bool = True) -> None:
    missing_cols = [c for c in REQUIRED if c not in df.columns]
    if missing_cols:
        raise ValueError(f"missing required columns: {missing_cols}")
    if require_authoritative_size and len(df) != 10000:
        raise ValueError(f"expected 10000 rows, got {len(df)}")
    if df[FEATURES + [TARGET]].isna().any().any():
        raise ValueError("missing value in predictor or target")
    if not df["UDI"].is_unique:
        raise ValueError("UDI must be unique")
    if not df["UDI"].is_monotonic_increasing:
        raise ValueError("UDI must be monotonically increasing")
    if not set(df[TARGET].unique()).issubset({0, 1}):
        raise ValueError("target must be binary 0/1")
    if not set(df["Type"].unique()).issubset({"L", "M", "H"}):
        raise ValueError("Type contains unsupported category")
    if not np.isfinite(df[NUMERIC].to_numpy(dtype=float)).all():
        raise ValueError("numeric predictors must be finite")


def validate_inference_frame(df: pd.DataFrame) -> None:
    missing = [c for c in FEATURES if c not in df.columns]
    if missing:
        raise ValueError(f"missing inference features: {missing}")
    if df[FEATURES].isna().any().any():
        raise ValueError("missing value in inference features")
    if not set(df["Type"].unique()).issubset({"L", "M", "H"}):
        raise ValueError("Type contains unsupported category")
    if not np.isfinite(df[NUMERIC].to_numpy(dtype=float)).all():
        raise ValueError("numeric inference features must be finite")


def load_source(path: Path = RAW_CSV) -> pd.DataFrame:
    df = pd.read_csv(path)
