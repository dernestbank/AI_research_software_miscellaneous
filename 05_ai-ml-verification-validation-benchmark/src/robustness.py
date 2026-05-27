from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, precision_score, recall_score, f1_score

ROOT=Path(__file__).resolve().parents[1]
SUT=ROOT.parent/"03_ai-data-pipeline-mlops"
ART=SUT/"artifacts"
RAW=SUT/"data"/"raw"/"uci"/"ai4i2020.csv"
OUT=ROOT/"artifacts"/"robustness_report.json"

NOISE_SIGMA={
    "Air temperature [K]":0.2,
    "Process temperature [K]":0.2,
    "Rotational speed [rpm]":20.0,
    "Torque [Nm]":0.5,
    "Tool wear [min]":1.0,
}
SEEDS=[20260829,7,42,101,999]


def class_metrics(y,pred,prob):
    return {
        "precision":float(precision_score(y,pred,zero_division=0)),
        "recall":float(recall_score(y,pred,zero_division=0)),
        "f1":float(f1_score(y,pred,zero_division=0)),
        "brier":float(brier_score_loss(y,prob)),
        "positives":int(np.sum(y)),
        "predicted_positives":int(np.sum(pred)),
    }


def run():
    bundle=joblib.load(ART/"model.joblib")
    model=bundle["model"]; threshold=float(bundle["threshold"]); features=list(bundle["features"])
    df=pd.read_csv(RAW)
    test=df[df["UDI"]>=8501].copy().sort_values("UDI")
    frozen=pd.read_csv(ART/"test_predictions.csv").sort_values("UDI")
    if list(test["UDI"])!=list(frozen["UDI"]):
        raise ValueError("raw test rows do not align with frozen predictions")
    y=test["Machine failure"].to_numpy(int)
    base_prob=frozen["failure_probability"].to_numpy(float)
    base_pred=frozen["prediction"].to_numpy(int)
    base=class_metrics(y,base_pred,base_prob)

    bounds={c:(float(df[c].min()),float(df[c].max())) for c in NOISE_SIGMA}
    noise_runs=[]
    for seed in SEEDS:
        rng=np.random.default_rng(seed)
        x=test[features].copy()
        for c,sigma in NOISE_SIGMA.items():
            x[c]=np.clip(x[c].to_numpy(float)+rng.normal(0,sigma,len(x)),bounds[c][0],bounds[c][1])
        prob=model.predict_proba(x)[:,1]
        pred=(prob>=threshold).astype(int)
        m=class_metrics(y,pred,prob)
        m.update({
            "seed":seed,
            "probability_mae_vs_frozen":float(np.mean(np.abs(prob-base_prob))),
            "probability_max_abs_delta":float(np.max(np.abs(prob-base_prob))),
            "prediction_flips":int(np.sum(pred!=base_pred)),
            "prediction_flip_rate":float(np.mean(pred!=base_pred)),
            "recall_drop_vs_frozen":float(base["recall"]-m["recall"]),
        })
        noise_runs.append(m)

    subgroup={}
    for typ,g in test.groupby("Type",sort=True):
        idx=g.index.to_numpy()-test.index.min()
        # Safer positional alignment by UDI map.
        positions=[int(np.where(test["UDI"].to_numpy()==u)[0][0]) for u in g["UDI"]]
        yy=y[positions]; pp=base_prob[positions]; pred=base_pred[positions]
        subgroup[str(typ)]={
            "rows":len(positions),
            **class_metrics(yy,pred,pp),
        }

    edge_indices=set()
    for c in NOISE_SIGMA:
        edge_indices.add(int(df[c].idxmin()))
        edge_indices.add(int(df[c].idxmax()))
    edges=df.loc[sorted(edge_indices),["UDI","Type",*NOISE_SIGMA.keys()]].copy()
    edge_prob=model.predict_proba(edges[features])[:,1]
    edge_valid=bool(np.isfinite(edge_prob).all() and ((edge_prob>=0)&(edge_prob<=1)).all())
    edge_rows=[{"UDI":int(u),"failure_probability":float(p)} for u,p in zip(edges["UDI"],edge_prob)]

    result={
        "sut_version":bundle.get("model_version"),
        "threshold":threshold,
        "noise_scenario":{"sigma":NOISE_SIGMA,"seeds":SEEDS,"clip_bounds":"observed full-source min/max","classification":"project stress scenario, not calibrated sensor error"},
        "frozen_metrics":base,
        "noise_runs":noise_runs,
        "worst_prediction_flip_rate":float(max(r["prediction_flip_rate"] for r in noise_runs)),
        "worst_recall_drop":float(max(r["recall_drop_vs_frozen"] for r in noise_runs)),
        "noise_gate_flip_rate_pass":max(r["prediction_flip_rate"] for r in noise_runs)<=0.05,
        "noise_gate_recall_drop_pass":max(r["recall_drop_vs_frozen"] for r in noise_runs)<=0.10,
        "subgroup_by_type":subgroup,
        "edge_rows_checked":len(edge_rows),
        "edge_probability_valid":edge_valid,
        "edge_rows":edge_rows,
        "limitations":[
            "Noise scales are project-defined stress values, not sensor specifications.",
            "Subgroup Type metrics use a synthetic benchmark and small positive counts; no fairness claim.",
            "Observed-source extrema do not prove behavior outside the source range."
        ]
    }
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k not in ("noise_runs","subgroup_by_type","edge_rows","limitations")},indent=2))
    print("subgroups",json.dumps(subgroup,indent=2))
    return result

if __name__=="__main__":
    run()
