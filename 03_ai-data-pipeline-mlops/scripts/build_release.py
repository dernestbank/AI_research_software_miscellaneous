from __future__ import annotations

import json
import shutil
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import pipeline

VERSION = pipeline.MODEL_VERSION
RELEASE = ROOT / "releases" / VERSION
RELEASE.mkdir(parents=True, exist_ok=True)

sources = [
    pipeline.MODEL_PATH,
    pipeline.MANIFEST_PATH,
    pipeline.PIPELINE_MANIFEST_PATH,
    pipeline.METRICS_PATH,
    ROOT / "requirements.txt",
]
for src in sources:
    if not src.exists():
        raise SystemExit(f"missing release input: {src}")
    shutil.copy2(src, RELEASE / src.name)

manifest = {
    "release_version": VERSION,
    "files": {p.name: pipeline.sha256(p) for p in sorted(RELEASE.iterdir()) if p.is_file() and p.name != "release_manifest.json"},
}
(RELEASE / "release_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
print("RELEASE_BUILD_PASS")
print(json.dumps(manifest, indent=2))
