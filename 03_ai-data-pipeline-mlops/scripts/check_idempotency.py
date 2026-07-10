from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pipeline

OUT = ROOT / "artifacts" / "idempotency_check.json"


def snapshot():
    return json.loads(pipeline.PIPELINE_MANIFEST_PATH.read_text(encoding="utf-8"))


pipeline.run_pipeline()
a = snapshot()
pipeline.run_pipeline()
b = snapshot()

keys = ["source_sha256", "model_sha256", "metrics_sha256", "predictions_sha256", "deterministic_evidence_hash"]
checks = {k: a[k] == b[k] for k in keys}
result = {
    "runs": 2,
    "checks": checks,
    "all_deterministic_hashes_match": all(checks.values()),
    "run1": {k: a[k] for k in keys},
    "run2": {k: b[k] for k in keys},
}
OUT.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
if not result["all_deterministic_hashes_match"]:
    raise SystemExit("IDEMPOTENCY_FAIL")
print("IDEMPOTENCY_PASS")
print(json.dumps(result, indent=2))
