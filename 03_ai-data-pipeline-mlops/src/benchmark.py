from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

from pipeline import ARTIFACTS, TARGET, load_source, split_frame

OUT = ARTIFACTS / "baseline_benchmark.json"


def run_baseline() -> dict:
    df = load_source()
    train, _, test = split_frame(df)
    y = test[TARGET].to_numpy(dtype=int)
    p = np.full(len(test), float(train[TARGET].mean()), dtype=float)
    out = {
        "baseline": "constant training-prevalence probability",
        "training_prevalence": float(train[TARGET].mean()),
        "test_prevalence": float(y.mean()),
        "roc_auc": float(roc_auc_score(y, p)),
        "average_precision": float(average_precision_score(y, p)),
        "brier": float(brier_score_loss(y, p)),
        "interpretation": "weak non-discriminating reference only; not a deployable model",
    }
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")
    return out


if __name__ == "__main__":
    print(json.dumps(run_baseline(), indent=2))
