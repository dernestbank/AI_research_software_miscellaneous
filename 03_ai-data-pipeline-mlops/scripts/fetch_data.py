from __future__ import annotations

import hashlib
import shutil
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
ZIP_PATH = RAW / "ai4i2020.zip"
CSV_DIR = RAW / "uci"
CSV_PATH = CSV_DIR / "ai4i2020.csv"

URL = "https://archive.ics.uci.edu/static/public/601/ai4i%2B2020%2Bpredictive%2Bmaintenance%2Bdataset.zip"
EXPECTED_ZIP_SHA256 = "F601F14294BCF190F9D720676B7F0AEA46A26CDE9AB8EBC7B4F8174D9D26B252"
EXPECTED_CSV_SHA256 = "DC6630CD9B1F0F853922FAD78A1B6436570D3F1EC863F1DD5C4340AC56BC8A8E"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


RAW.mkdir(parents=True, exist_ok=True)
CSV_DIR.mkdir(parents=True, exist_ok=True)

if not ZIP_PATH.exists() or sha256(ZIP_PATH) != EXPECTED_ZIP_SHA256:
    tmp = ZIP_PATH.with_suffix(".zip.part")
    with urllib.request.urlopen(URL, timeout=60) as src, tmp.open("wb") as dst:
        shutil.copyfileobj(src, dst)
    if sha256(tmp) != EXPECTED_ZIP_SHA256:
        tmp.unlink(missing_ok=True)
        raise SystemExit("Downloaded ZIP hash mismatch")
    tmp.replace(ZIP_PATH)

with zipfile.ZipFile(ZIP_PATH) as zf:
    names = [n for n in zf.namelist() if n.lower().endswith("ai4i2020.csv")]
    if len(names) != 1:
        raise SystemExit(f"Expected exactly one ai4i2020.csv in archive, found {names}")
    with zf.open(names[0]) as src, CSV_PATH.open("wb") as dst:
        shutil.copyfileobj(src, dst)

if sha256(CSV_PATH) != EXPECTED_CSV_SHA256:
    raise SystemExit("Extracted CSV hash mismatch")

print("FETCH_PASS")
print(f"zip_sha256={sha256(ZIP_PATH)}")
print(f"csv_sha256={sha256(CSV_PATH)}")
