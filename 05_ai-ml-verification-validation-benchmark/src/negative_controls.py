from __future__ import annotations

import csv
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SUT=ROOT.parent/"03_ai-data-pipeline-mlops"
PRED=SUT/"artifacts"/"test_predictions.csv"
MANIFEST=SUT/"artifacts"/"model_manifest.json"
OUT=ROOT/"artifacts"/"negative_controls.json"
REQUIRED={"UDI","Machine failure","failure_probability","prediction"}


def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):
            h.update(b)
    return h.hexdigest().upper()


def validate_prediction_file(path: Path, expected_hash: str | None=None) -> dict:
    if expected_hash is not None and sha256(path)!=expected_hash:
        return {"valid":False,"reason":"hash_mismatch"}
    try:
        with open(path,newline="",encoding="utf-8") as f:
            rows=list(csv.DictReader(f))
    except Exception as e:
        return {"valid":False,"reason":"read_error"}
    if not rows:
        return {"valid":False,"reason":"empty"}
    if not REQUIRED.issubset(set(rows[0])):
        return {"valid":False,"reason":"missing_required_column"}
    if len(rows)!=1500:
        return {"valid":False,"reason":"row_count"}
    try:
        for r in rows:
            int(r["UDI"]); y=int(r["Machine failure"]); p=float(r["failure_probability"]); pred=int(r["prediction"])
            if y not in (0,1) or pred not in (0,1):
                return {"valid":False,"reason":"nonbinary_label_or_prediction"}
            if not (0.0<=p<=1.0):
                return {"valid":False,"reason":"probability_out_of_range"}
    except Exception:
        return {"valid":False,"reason":"non_numeric_value"}
    return {"valid":True,"reason":"ok"}


def _read_rows(path):
    with open(path,newline="",encoding="utf-8") as f:
        rows=list(csv.DictReader(f)); fields=list(rows[0])
    return fields,rows


def _write_rows(path,fields,rows):
    with open(path,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)


def run():
    expected=json.loads(MANIFEST.read_text())["predictions_sha256"]
    baseline=validate_prediction_file(PRED,expected)
    cases=[]
    with tempfile.TemporaryDirectory() as td:
        td=Path(td)
        fields,rows=_read_rows(PRED)

        p=td/"hash_modified.csv"; rr=[dict(x) for x in rows]
        rr[0]["failure_probability"]=str(min(0.999,float(rr[0]["failure_probability"])+0.001))
        _write_rows(p,fields,rr)
        v=validate_prediction_file(p,expected)
        cases.append({"case":"modified_probability_hash","detected":not v["valid"],"reason":v["reason"]})

        p=td/"missing_column.csv"
        fields2=[x for x in fields if x!="failure_probability"]
        rr=[{k:v for k,v in x.items() if k in fields2} for x in rows]
        _write_rows(p,fields2,rr)
        v=validate_prediction_file(p,None)
        cases.append({"case":"missing_probability_column","detected":not v["valid"],"reason":v["reason"]})

        p=td/"out_of_range.csv"; rr=[dict(x) for x in rows]
        rr[0]["failure_probability"]="1.5"
        _write_rows(p,fields,rr)
        v=validate_prediction_file(p,None)
        cases.append({"case":"probability_1p5","detected":not v["valid"],"reason":v["reason"]})

        p=td/"nonnumeric.csv"; rr=[dict(x) for x in rows]
        rr[0]["failure_probability"]="not-a-number"
        _write_rows(p,fields,rr)
        v=validate_prediction_file(p,None)
        cases.append({"case":"nonnumeric_probability","detected":not v["valid"],"reason":v["reason"]})

    result={
        "baseline_valid":baseline["valid"],
        "cases":cases,
        "detected":sum(x["detected"] for x in cases),
        "total":len(cases),
        "all_negative_controls_detected":all(x["detected"] for x in cases),
    }
    OUT.write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))
    return result

if __name__=="__main__":
    run()
