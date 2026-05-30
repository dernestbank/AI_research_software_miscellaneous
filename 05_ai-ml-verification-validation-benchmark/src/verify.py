from __future__ import annotations
import csv, hashlib, json, math
from dataclasses import dataclass, asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUT = ROOT.parent / '03_ai-data-pipeline-mlops'
ART = SUT / 'artifacts'

@dataclass
class Check:
    req_id: str
    name: str
    passed: bool
    observed: object
    criterion: str


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest().upper()


def load_rows(path: Path):
    with path.open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def metrics_from_rows(rows):
    y=[int(r['Machine failure']) for r in rows]
    p=[float(r['failure_probability']) for r in rows]
    pred=[int(r['prediction']) for r in rows]
    tn=sum(a==0 and b==0 for a,b in zip(y,pred)); fp=sum(a==0 and b==1 for a,b in zip(y,pred))
    fn=sum(a==1 and b==0 for a,b in zip(y,pred)); tp=sum(a==1 and b==1 for a,b in zip(y,pred))
    precision=tp/(tp+fp) if tp+fp else 0.0; recall=tp/(tp+fn) if tp+fn else 0.0
    f1=2*precision*recall/(precision+recall) if precision+recall else 0.0
    brier=sum((a-b)**2 for a,b in zip(y,p))/len(y)
    return {'rows':len(rows),'tn':tn,'fp':fp,'fn':fn,'tp':tp,'precision':precision,'recall':recall,'f1':f1,'brier':brier}


def ece(rows, bins=10):
    buckets=[[] for _ in range(bins)]
    for r in rows:
        p=float(r['failure_probability']); y=int(r['Machine failure'])
        idx=min(int(p*bins), bins-1); buckets[idx].append((p,y))
    total=len(rows); score=0.0
    for b in buckets:
        if not b: continue
        conf=sum(x[0] for x in b)/len(b); rate=sum(x[1] for x in b)/len(b)
        score += len(b)/total*abs(conf-rate)
    return score

def threshold_sensitivity(rows, thresholds=(0.30,0.35,0.40)):
    out=[]
    for t in thresholds:
        y=[int(r['Machine failure']) for r in rows]
        p=[float(r['failure_probability']) for r in rows]
        pred=[int(v>=t) for v in p]
        tp=sum(a==1 and b==1 for a,b in zip(y,pred)); fp=sum(a==0 and b==1 for a,b in zip(y,pred))
        fn=sum(a==1 and b==0 for a,b in zip(y,pred))
        precision=tp/(tp+fp) if tp+fp else 0.0; recall=tp/(tp+fn) if tp+fn else 0.0
        f1=2*precision*recall/(precision+recall) if precision+recall else 0.0
        out.append({'threshold':t,'precision':precision,'recall':recall,'f1':f1,'tp':tp,'fp':fp,'fn':fn})
    return out


def run():
    manifest=json.loads((ART/'model_manifest.json').read_text())
    metrics=json.loads((ART/'model_metrics.json').read_text())
    monitoring=json.loads((ART/'monitoring_snapshot.json').read_text())
    rows=load_rows(ART/'test_predictions.csv')
    recomputed=metrics_from_rows(rows)
    checks=[]
    checks.append(Check('REQ-001','Prediction artifact identity', sha256(ART/'test_predictions.csv')==manifest['predictions_sha256'], sha256(ART/'test_predictions.csv'), manifest['predictions_sha256']))
    cm=metrics['test']['confusion_matrix']
    checks.append(Check('REQ-002','Confusion matrix reconciles', [recomputed[k] for k in ('tn','fp','fn','tp')]==[cm[k] for k in ('tn','fp','fn','tp')], {k:recomputed[k] for k in ('tn','fp','fn','tp')}, str(cm)))
    checks.append(Check('REQ-003','Recall floor', recomputed['recall']>=0.60, recomputed['recall'], '>=0.60'))
    checks.append(Check('REQ-004','Brier ceiling', recomputed['brier']<=0.02, recomputed['brier'], '<=0.02'))
    checks.append(Check('REQ-005','Probability range', all(0<=float(r['failure_probability'])<=1 for r in rows), 'all 1500 rows checked', '[0,1]'))
    checks.append(Check('REQ-006','Missing/nonfinite monitor cells', monitoring['missing_feature_cells']==0 and monitoring['nonfinite_numeric_cells']==0, {'missing':monitoring['missing_feature_cells'],'nonfinite':monitoring['nonfinite_numeric_cells']}, 'both zero'))
    checks.append(Check('REQ-007','Distribution-shift release gate', monitoring['max_numeric_psi']<0.25, monitoring['max_numeric_psi'], '<0.25 project rule'))
    result={
      'sut_version':manifest['model_version'], 'requirements':[asdict(c) for c in checks],
      'requirements_passed':sum(c.passed for c in checks), 'requirements_total':len(checks),
      'release_decision':'PASS' if all(c.passed for c in checks) else 'HOLD',
      'recomputed_metrics':recomputed, 'ece_10bin':ece(rows),
      'threshold_sensitivity':threshold_sensitivity(rows),
      'monitoring_status':monitoring['status'], 'max_numeric_psi':monitoring['max_numeric_psi']
    }
    out=ROOT/'artifacts'; out.mkdir(exist_ok=True)
    (out/'vv_report.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('requirements','threshold_sensitivity')},indent=2))
    return result

if __name__=='__main__': run()
