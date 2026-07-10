from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import pipeline

version = pipeline.MODEL_VERSION
release = ROOT / "releases" / version
manifest = json.loads((release / "release_manifest.json").read_text())
checks = {}
for name, expected in manifest["files"].items():
    p = release / name
    checks[name] = p.exists() and pipeline.sha256(p) == expected

result = {"release_version": version, "checks": checks, "valid": all(checks.values())}
out = ROOT / "artifacts" / "release_verification.json"
out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
if not result["valid"]:
    raise SystemExit("RELEASE_VERIFY_FAIL")
print("RELEASE_VERIFY_PASS")
print(json.dumps(result, indent=2))
