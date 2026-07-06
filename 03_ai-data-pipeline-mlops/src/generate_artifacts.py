from pathlib import Path
import json
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/"artifacts"
FIG=ROOT/"figures"
FIG.mkdir(exist_ok=True)

metrics=json.loads((ART/"model_metrics.json").read_text())
baseline=json.loads((ART/"baseline_benchmark.json").read_text())
monitor=json.loads((ART/"monitoring_snapshot.json").read_text())

# Performance vs weak baseline
names=["ROC AUC","Average precision","Brier score"]
rf=[metrics["test"]["roc_auc"],metrics["test"]["average_precision"],metrics["test"]["brier"]]
bl=[baseline["roc_auc"],baseline["average_precision"],baseline["brier"]]

fig,ax=plt.subplots(figsize=(7.2,4.6))
x=range(len(names))
w=0.35
ax.bar([i-w/2 for i in x],rf,width=w,label="Random forest")
ax.bar([i+w/2 for i in x],bl,width=w,label="Constant baseline")
ax.set_xticks(list(x),names)
ax.set_ylabel("Metric value")
ax.set_title("Frozen-test model evidence vs non-discriminating baseline")
ax.grid(axis="y",alpha=.25)
ax.legend()
fig.tight_layout()
fig.savefig(FIG/"model_vs_baseline.svg")
fig.savefig(FIG/"model_vs_baseline.png",dpi=180)
plt.close(fig)

# Drift
psi=monitor["numeric_psi"]
fig,ax=plt.subplots(figsize=(7.6,4.8))
labels=[k.replace(" [K]"," K").replace(" [rpm]","").replace(" [Nm]","").replace(" [min]","") for k in psi]
vals=list(psi.values())
ax.barh(labels,vals)
ax.axvline(0.25,linestyle="--",linewidth=1,label="Project alert threshold")
ax.set_xlabel("Population Stability Index")
ax.set_title("Chronological train-to-test feature drift")
ax.grid(axis="x",alpha=.25)
ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig(FIG/"feature_drift_psi.svg")
fig.savefig(FIG/"feature_drift_psi.png",dpi=180)
plt.close(fig)

# Architecture SVG: deliberately simple recruiter-readable system view.
svg="""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="520" viewBox="0 0 1200 520">
<style>
text { font-family: Arial, sans-serif; fill: #111; }
.title { font-size: 28px; font-weight: 700; }
.box { fill: white; stroke: #333; stroke-width: 2; rx: 12; }
.h { font-size: 18px; font-weight: 700; }
.s { font-size: 14px; }
.arrow { stroke: #333; stroke-width: 2.2; fill: none; marker-end: url(#a); }
</style>
<defs><marker id="a" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#333"/></marker></defs>
<text x="40" y="45" class="title">AI Data Pipeline &amp; MLOps Deployment — Evidence Architecture</text>
<rect x="40" y="100" width="190" height="95" class="box"/><text x="60" y="130" class="h">UCI AI4I</text><text x="60" y="155" class="s">CC BY 4.0</text><text x="60" y="178" class="s">10,000 synthetic rows</text>
<rect x="285" y="100" width="210" height="95" class="box"/><text x="305" y="130" class="h">Ingest + QA</text><text x="305" y="155" class="s">SHA-256, schema, leakage</text><text x="305" y="178" class="s">UDI 70/15/15 split</text>
<rect x="550" y="100" width="210" height="95" class="box"/><text x="570" y="130" class="h">Train + Validate</text><text x="570" y="155" class="s">RF 100 trees</text><text x="570" y="178" class="s">validation threshold</text>
<rect x="815" y="100" width="210" height="95" class="box"/><text x="835" y="130" class="h">Versioned Release</text><text x="835" y="155" class="s">model + metrics + hashes</text><text x="835" y="178" class="s">clean rebuild + rollback</text>
<rect x="815" y="300" width="210" height="105" class="box"/><text x="835" y="332" class="h">FastAPI + Docker</text><text x="835" y="357" class="s">health, predict, model-info</text><text x="835" y="380" class="s">request/error/latency</text>
<rect x="550" y="300" width="210" height="105" class="box"/><text x="570" y="332" class="h">Monitoring</text><text x="570" y="357" class="s">PSI + type shift</text><text x="570" y="380" class="s">drift ALERT retained</text>
<rect x="285" y="300" width="210" height="105" class="box"/><text x="305" y="332" class="h">Validation</text><text x="305" y="357" class="s">11/11 pytest</text><text x="305" y="380" class="s">idempotency + smoke tests</text>
<path d="M230 148 L285 148" class="arrow"/><path d="M495 148 L550 148" class="arrow"/><path d="M760 148 L815 148" class="arrow"/>
<path d="M920 195 L920 300" class="arrow"/><path d="M815 352 L760 352" class="arrow"/><path d="M550 352 L495 352" class="arrow"/>
<text x="40" y="470" class="s">Boundary: local/containerized portfolio implementation. No Kubernetes, cloud-scale, factory deployment, or production business-impact claim.</text>
</svg>"""
(FIG/"mlops_architecture.svg").write_text(svg,encoding="utf-8")
print("generated", [p.name for p in FIG.iterdir() if p.is_file()])
