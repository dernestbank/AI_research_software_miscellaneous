from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/"artifacts"


def run():
    core=json.loads((ART/"vv_report.json").read_text())
    robust=json.loads((ART/"robustness_report.json").read_text())
    agent=json.loads((ART/"agent_vv_report.json").read_text())
    neg=json.loads((ART/"negative_controls.json").read_text())

    ml=[]
    for i,r in enumerate(core["requirements"],1):
        ml.append({
            "req_id":f"ML-{i:03d}",
            "name":r["name"],
            "passed":bool(r["passed"]),
            "observed":r["observed"],
            "criterion":r["criterion"],
        })
    ml.extend([
        {"req_id":"ML-008","name":"10-bin calibration ECE","passed":core["ece_10bin"]<=0.03,"observed":core["ece_10bin"],"criterion":"<=0.03 project rule"},
        {"req_id":"ML-009","name":"Modest-noise prediction stability","passed":robust["noise_gate_flip_rate_pass"],"observed":robust["worst_prediction_flip_rate"],"criterion":"worst flip rate <=0.05"},
        {"req_id":"ML-010","name":"Modest-noise recall stability","passed":robust["noise_gate_recall_drop_pass"],"observed":robust["worst_recall_drop"],"criterion":"worst recall drop <=0.10 absolute"},
        {"req_id":"ML-011","name":"Observed-extreme output validity","passed":robust["edge_probability_valid"],"observed":{"rows_checked":robust["edge_rows_checked"],"valid":robust["edge_probability_valid"]},"criterion":"all finite probabilities in [0,1]"},
    ])
    ml_pass=sum(x["passed"] for x in ml)
    agent_reqs=agent["requirements"]
    result={
        "ml_sut":{
            "version":core["sut_version"],
            "requirements_passed":ml_pass,
            "requirements_total":len(ml),
            "disposition":"PASS" if ml_pass==len(ml) else "HOLD",
            "requirements":ml,
            "recomputed_metrics":core["recomputed_metrics"],
            "ece_10bin":core["ece_10bin"],
            "threshold_sensitivity":core["threshold_sensitivity"],
            "max_numeric_psi":core["max_numeric_psi"],
            "robustness":{
                "worst_prediction_flip_rate":robust["worst_prediction_flip_rate"],
                "worst_recall_drop":robust["worst_recall_drop"],
                "edge_rows_checked":robust["edge_rows_checked"],
                "subgroup_by_type":robust["subgroup_by_type"],
            },
        },
        "agent_sut":{
            "requirements_passed":agent["requirements_passed"],
            "requirements_total":agent["requirements_total"],
            "disposition":agent["disposition"],
            "evaluation_sha256":agent["evaluation_sha256"],
            "requirements":agent_reqs,
        },
        "negative_controls":{
            "detected":neg["detected"],
            "total":neg["total"],
            "passed":neg["all_negative_controls_detected"],
        },
        "recommendations":[
            {
                "id":"REC-ML-DRIFT",
                "severity":"release-blocking",
                "finding":"ML max numeric PSI exceeds the frozen project release threshold.",
                "recommendation":"Keep ML release on HOLD; investigate feature shift and representative data before any retraining/re-release. Do not bypass the drift gate."
            },
            {
                "id":"REC-ML-THRESHOLD",
                "severity":"analysis",
                "finding":"Test-set threshold sensitivity shows a precision/recall tradeoff across 0.30/0.35/0.40.",
                "recommendation":"Do not choose a new threshold from the frozen test set. Use validation/operational cost criteria in a future release."
            },
            {
                "id":"REC-ML-SUBGROUP",
                "severity":"limitation",
                "finding":"Type H has zero positive test examples; Type M has only four.",
                "recommendation":"Do not make subgroup parity/fairness claims from these synthetic sparse-positive slices."
            },
            {
                "id":"REC-AGENT",
                "severity":"scope",
                "finding":"Agent passes its small project-authored frozen benchmark.",
                "recommendation":"Treat PASS as bounded regression evidence only; expand corpus/query diversity before any production claim."
            }
        ],
        "boundary":"Portfolio V&V harness. SUT dispositions are project requirement decisions, not formal certification."
    }
    (ART/"validation_matrix.json").write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    with open(ART/"validation_matrix.csv","w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["sut","req_id","name","passed","observed","criterion"])
        w.writeheader()
        for x in ml:
            w.writerow({"sut":"ML","req_id":x["req_id"],"name":x["name"],"passed":x["passed"],"observed":json.dumps(x["observed"],sort_keys=True),"criterion":x["criterion"]})
        for x in agent_reqs:
            w.writerow({"sut":"AGENT","req_id":x["req_id"],"name":x["name"],"passed":x["passed"],"observed":json.dumps(x["observed"],sort_keys=True),"criterion":x["criterion"]})
    print(json.dumps({
        "ml":f'{ml_pass}/{len(ml)} {result["ml_sut"]["disposition"]}',
        "agent":f'{agent["requirements_passed"]}/{agent["requirements_total"]} {agent["disposition"]}',
        "negative_controls":f'{neg["detected"]}/{neg["total"]}'
    },indent=2))
    return result

if __name__=="__main__":
    run()
