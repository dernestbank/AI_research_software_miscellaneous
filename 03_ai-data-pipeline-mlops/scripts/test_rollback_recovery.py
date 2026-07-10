from __future__ import annotations

import json
import shutil
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import joblib
import pandas as pd
import pipeline
import service

live = pipeline.MODEL_PATH
release = ROOT / "releases" / pipeline.MODEL_VERSION / "model.joblib"
out = ROOT / "artifacts" / "rollback_recovery_test.json"
backup = live.read_bytes()
failure_detected = False
recovery_success = False
recovered_probability = None

try:
    live.write_bytes(b"intentionally-corrupted-model-artifact")
    service._bundle = None
    try:
        service.get_bundle()
    except Exception:
        failure_detected = True

    shutil.copy2(release, live)
    service._bundle = None
    bundle = service.get_bundle()
    row = pd.DataFrame([{
        "Type": "L",
        "Air temperature [K]": 300.0,
        "Process temperature [K]": 310.0,
        "Rotational speed [rpm]": 1500.0,
        "Torque [Nm]": 40.0,
        "Tool wear [min]": 100.0,
    }])
    recovered_probability = float(bundle["model"].predict_proba(row)[:, 1][0])
    recovery_success = (
        bundle.get("model_version") == pipeline.MODEL_VERSION
        and 0.0 <= recovered_probability <= 1.0
        and pipeline.sha256(live) == pipeline.sha256(release)
    )
finally:
    live.write_bytes(backup)
    service._bundle = None

result = {
    "failure_detected_on_corrupt_live_model": failure_detected,
    "restored_from_verified_release": recovery_success,
    "release_version": pipeline.MODEL_VERSION,
    "recovered_probability_sample": recovered_probability,
    "live_model_hash_restored": pipeline.sha256(live),
    "release_model_hash": pipeline.sha256(release),
}
out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
if not (failure_detected and recovery_success and result["live_model_hash_restored"] == result["release_model_hash"]):
    raise SystemExit("ROLLBACK_RECOVERY_FAIL")
print("ROLLBACK_RECOVERY_PASS")
print(json.dumps(result, indent=2))
