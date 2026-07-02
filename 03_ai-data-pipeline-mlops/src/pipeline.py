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
    validate_frame(df)
    return df


def split_frame(df: pd.DataFrame):
    train = df[df["UDI"] <= 7000].copy()
    val = df[(df["UDI"] >= 7001) & (df["UDI"] <= 8500)].copy()
    test = df[df["UDI"] >= 8501].copy()
    if (len(train), len(val), len(test)) != (7000, 1500, 1500):
        raise ValueError("frozen UDI split sizes were not reproduced")
    return train, val, test


def build_model() -> Pipeline:
    prep = ColumnTransformer(
        [
            ("num", StandardScaler(), NUMERIC),
            ("type", OneHotEncoder(handle_unknown="error"), ["Type"]),
        ]
    )
    clf = RandomForestClassifier(
        n_estimators=100,
        class_weight="balanced",
        min_samples_leaf=2,
        random_state=42,
        n_jobs=1,
    )
    return Pipeline([("prep", prep), ("clf", clf)])


def select_threshold(y_true: pd.Series, probs: np.ndarray) -> tuple[float, float]:
    candidates = np.linspace(0.05, 0.95, 181)
    scores = np.array([f1_score(y_true, probs >= t, zero_division=0) for t in candidates])
    idx = int(np.argmax(scores))
    return float(candidates[idx]), float(scores[idx])


def population_stability_index(train: pd.Series, test: pd.Series, bins: int = 10) -> float:
    edges = np.unique(np.quantile(train.to_numpy(dtype=float), np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        return 0.0
    edges[0] = -np.inf
    edges[-1] = np.inf
    tr = pd.cut(train, bins=edges, include_lowest=True).value_counts(sort=False, normalize=True).to_numpy()
    te = pd.cut(test, bins=edges, include_lowest=True).value_counts(sort=False, normalize=True).to_numpy()
    eps = 1e-6
    tr = np.clip(tr, eps, None)
    te = np.clip(te, eps, None)
    return float(np.sum((te - tr) * np.log(te / tr)))


def evaluate(model: Pipeline, frame: pd.DataFrame, threshold: float) -> tuple[dict, pd.DataFrame, dict]:
    X = frame[FEATURES]
    y = frame[TARGET].astype(int)
    t0 = time.perf_counter()
    probs = model.predict_proba(X)[:, 1]
    elapsed = time.perf_counter() - t0
    pred = (probs >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    metrics = {
        "rows": int(len(frame)),
        "failures": int(y.sum()),
        "prevalence": float(y.mean()),
        "threshold": float(threshold),
        "roc_auc": float(roc_auc_score(y, probs)),
        "average_precision": float(average_precision_score(y, probs)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "f1": float(f1_score(y, pred, zero_division=0)),
        "brier": float(brier_score_loss(y, probs)),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }
    runtime = {
        "batch_rows": int(len(frame)),
        "batch_latency_ms": float(elapsed * 1000),
        "mean_latency_ms_per_row": float(elapsed * 1000 / len(frame)),
        "note": "environment-specific runtime observation; excluded from deterministic evidence hash",
    }
    out = frame[["UDI", TARGET]].copy()
    out["failure_probability"] = probs
    out["prediction"] = pred
    return metrics, out, runtime


def train_and_evaluate(raw_csv: Path = RAW_CSV):
    df = load_source(raw_csv)
    train, val, test = split_frame(df)
    model = build_model()
    model.fit(train[FEATURES], train[TARGET])
    val_probs = model.predict_proba(val[FEATURES])[:, 1]
    threshold, val_f1 = select_threshold(val[TARGET], val_probs)
    test_metrics, predictions, runtime = evaluate(model, test, threshold)
    psi = {c: population_stability_index(train[c], test[c]) for c in NUMERIC}
    metrics = {
        "model_version": MODEL_VERSION,
        "source_rows": int(len(df)),
        "source_sha256": sha256(raw_csv),
        "split_rows": {"train": len(train), "validation": len(val), "test": len(test)},
        "split_failure_prevalence": {
            "train": float(train[TARGET].mean()),
            "validation": float(val[TARGET].mean()),
            "test": float(test[TARGET].mean()),
        },
        "validation_threshold": threshold,
        "validation_f1_at_threshold": val_f1,
        "test": test_metrics,
        "numeric_feature_psi_train_vs_test": psi,
        "max_numeric_psi": float(max(psi.values())),
        "model": "RandomForestClassifier(n_estimators=100,class_weight=balanced,min_samples_leaf=2,random_state=42,n_jobs=1)",
        "leakage_fields_excluded": ["UDI", "Product ID", "TWF", "HDF", "PWF", "OSF", "RNF"],
    }
    return model, threshold, predictions, metrics, runtime


def run_pipeline(raw_csv: Path = RAW_CSV) -> dict:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    model, threshold, predictions, metrics, runtime = train_and_evaluate(raw_csv)

    joblib.dump({"model": model, "threshold": threshold, "features": FEATURES, "model_version": MODEL_VERSION}, MODEL_PATH)
    predictions.to_csv(PREDICTIONS_PATH, index=False, float_format="%.12g")
    METRICS_PATH.write_text(json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8")
    RUNTIME_PATH.write_text(json.dumps(runtime, indent=2, sort_keys=True), encoding="utf-8")

    # Backward-compatible aggregate output. Runtime is intentionally not used in the deterministic manifest.
    results = dict(metrics)
    results["runtime_observation"] = runtime
    RESULTS_PATH.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")

    model_manifest = {
        "model_version": MODEL_VERSION,
        "source_sha256": metrics["source_sha256"],
        "feature_names": FEATURES,
        "threshold": threshold,
        "model_sha256": sha256(MODEL_PATH),
        "metrics_sha256": sha256(METRICS_PATH),
        "predictions_sha256": sha256(PREDICTIONS_PATH),
    }
    MANIFEST_PATH.write_text(json.dumps(model_manifest, indent=2, sort_keys=True), encoding="utf-8")

    code_paths = [ROOT / "src" / "pipeline.py", ROOT / "src" / "service.py"]
    pipeline_manifest = {
        "pipeline_version": MODEL_VERSION,
        "source_sha256": metrics["source_sha256"],
        "model_sha256": model_manifest["model_sha256"],
        "metrics_sha256": model_manifest["metrics_sha256"],
        "predictions_sha256": model_manifest["predictions_sha256"],
        "code_sha256": {p.name: sha256(p) for p in code_paths if p.exists()},
        "python_version": platform.python_version(),
        "sklearn_version": sklearn.__version__,
        "deterministic_evidence_hash": canonical_json_hash({
            "source_sha256": metrics["source_sha256"],
            "model_sha256": model_manifest["model_sha256"],
            "metrics_sha256": model_manifest["metrics_sha256"],
            "predictions_sha256": model_manifest["predictions_sha256"],
            "threshold": threshold,
        }),
    }
    PIPELINE_MANIFEST_PATH.write_text(json.dumps(pipeline_manifest, indent=2, sort_keys=True), encoding="utf-8")
    return results


if __name__ == "__main__":
    print(json.dumps(run_pipeline(), indent=2))
