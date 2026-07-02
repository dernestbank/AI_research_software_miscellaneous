from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline import (
    ARTIFACTS,
    FEATURES,
    NUMERIC,
    RAW_CSV,
    TARGET,
    load_source,
    population_stability_index,
    split_frame,
    validate_inference_frame,
)

MONITOR_PATH = ARTIFACTS / "monitoring_snapshot.json"


def categorical_total_variation(reference: pd.Series, current: pd.Series) -> float:
    cats = sorted(set(reference.dropna().astype(str)) | set(current.dropna().astype(str)))
    rp = reference.astype(str).value_counts(normalize=True).reindex(cats, fill_value=0.0)
    cp = current.astype(str).value_counts(normalize=True).reindex(cats, fill_value=0.0)
    return float(0.5 * np.abs(rp.to_numpy() - cp.to_numpy()).sum())


def monitor_batch(reference: pd.DataFrame, current: pd.DataFrame) -> dict:
    validate_inference_frame(current)
    psi = {c: population_stability_index(reference[c], current[c]) for c in NUMERIC}
    type_tv = categorical_total_variation(reference["Type"], current["Type"])
    return {
        "rows": int(len(current)),
        "numeric_psi": psi,
        "max_numeric_psi": float(max(psi.values())),
        "max_numeric_psi_feature": max(psi, key=psi.get),
        "type_distribution_total_variation": type_tv,
        "missing_feature_cells": int(current[FEATURES].isna().sum().sum()),
        "nonfinite_numeric_cells": int((~np.isfinite(current[NUMERIC].to_numpy(dtype=float))).sum()),
        "status": "ALERT" if max(psi.values()) >= 0.25 or type_tv >= 0.10 else "OK",
        "threshold_note": "PSI>=0.25 or type total-variation>=0.10 is a project monitoring rule, not a universal production standard",
    }


def source_split_snapshot(raw_csv: Path = RAW_CSV) -> dict:
    df = load_source(raw_csv)
    train, _, test = split_frame(df)
    snap = monitor_batch(train[FEATURES], test[FEATURES])
    snap["reference"] = "UDI 1-7000 training split"
    snap["current"] = "UDI 8501-10000 frozen test split"
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    MONITOR_PATH.write_text(json.dumps(snap, indent=2, sort_keys=True), encoding="utf-8")
    return snap


if __name__ == "__main__":
    print(json.dumps(source_split_snapshot(), indent=2))
