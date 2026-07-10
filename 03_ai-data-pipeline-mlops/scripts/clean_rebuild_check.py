from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import pipeline

OUT = ROOT / "artifacts" / "clean_rebuild_check.json"
before = json.loads(pipeline.PIPELINE_MANIFEST_PATH.read_text()) if pipeline.PIPELINE_MANIFEST_PATH.exists() else None

for p in [
    pipeline.MODEL_PATH,
    pipeline.RESULTS_PATH,
    pipeline.METRICS_PATH,
    pipeline.RUNTIME_PATH,
    pipeline.PREDICTIONS_PATH,
    pipeline.MANIFEST_PATH,
    pipeline.PIPELINE_MANIFEST_PATH,
]:
    p.unlink(missing_ok=True)

pipeline.run_pipeline()
after = json.loads(pipeline.PIPELINE_MANIFEST_PATH.read_text())

keys = ["source_sha256", "model_sha256", "metrics_sha256", "predictions_sha256", "deterministic_evidence_hash"]
checks = {k: (before is None or before[k] == after[k]) for k in keys}
result = {
    "generated_from_clean_artifact_state": True,
    "prior_manifest_available": before is not None,
    "checks": checks,
    "all_expected_hashes_reproduced": all(checks.values()),
    "after": {k: after[k] for k in keys},
}
OUT.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
if not result["all_expected_hashes_reproduced"]:
    raise SystemExit("CLEAN_REBUILD_FAIL")
print("CLEAN_REBUILD_PASS")
print(json.dumps(result, indent=2))
