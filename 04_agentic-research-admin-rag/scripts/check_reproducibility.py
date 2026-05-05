from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from evaluate import evaluate

OUT=ROOT/"artifacts"/"evaluation_reproducibility.json"

def canonical_hash(obj):
    s=json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False)
    return hashlib.sha256(s.encode()).hexdigest().upper()

a=evaluate()
ha=canonical_hash(a)
b=evaluate()
hb=canonical_hash(b)
result={"runs":2,"run1_sha256":ha,"run2_sha256":hb,"identical":ha==hb}
OUT.write_text(json.dumps(result,indent=2),encoding="utf-8")
if not result["identical"]:
    raise SystemExit("EVALUATION_REPRODUCIBILITY_FAIL")
print("EVALUATION_REPRODUCIBILITY_PASS")
print(json.dumps(result,indent=2))
