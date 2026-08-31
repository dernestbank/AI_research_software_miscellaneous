# Technical Memo — AI Data Pipeline & MLOps Deployment

**Date:** 2026-08-29
**Evidence status:** VALIDATED
**Boundary:** Local/containerized MLOps research implementation on a public synthetic benchmark. No factory deployment, cloud-scale, Kubernetes, or enterprise production claim.

## Executive summary
A reproducible predictive-maintenance ML service was built around the UCI AI4I 2020 dataset. The project verifies the official source by SHA-256, enforces schema and leakage controls, uses a deterministic UDI-ordered train/validation/test split, trains and versions a small random-forest classifier, exposes a versioned FastAPI inference service, containerizes the service, records request/error/latency metrics, monitors feature drift, verifies deterministic reruns, packages a versioned release, and exercises rollback recovery.

The authoritative source contains 10,000 rows and 339 machine-failure labels. The frozen test split contains 1,500 rows and 29 failures. The selected 100-tree random forest achieves ROC AUC 0.931644, average precision 0.697250, precision 0.666667, recall 0.620690, F1 0.642857 and Brier score 0.0104762. A non-discriminating constant-prevalence reference produces ROC AUC 0.500, average precision 0.019333 and Brier 0.019375.

## 1. Source and data contract
Primary source:
- UCI AI4I 2020 Predictive Maintenance Dataset, DOI 10.24432/C5HS5C.
- CC BY 4.0.
- UCI describes the data as synthetic but designed to reflect predictive-maintenance data encountered in industry.

Verified immutable inputs:
- official ZIP SHA-256: `F601F14294BCF190F9D720676B7F0AEA46A26CDE9AB8EBC7B4F8174D9D26B252`;
- extracted CSV SHA-256: `DC6630CD9B1F0F853922FAD78A1B6436570D3F1EC863F1DD5C4340AC56BC8A8E`;
- 10,000 rows;
- 14 required columns;
- 339 Machine failure positives.

The fetch script uses the current official UCI static attachment and rejects either ZIP or CSV hash mismatch.

## 2. Leakage and split design
Predictors:
- Type;
- air temperature;
- process temperature;
- rotational speed;
- torque;
- tool wear.

Excluded:
- UDI and Product ID identifiers;
- TWF, HDF, PWF, OSF and RNF failure-mode outcome fields.

The primary split is deterministic and ordered by UDI:
- train: 1-7000;
- validation: 7001-8500;
- test: 8501-10000.

This is intentionally not a random split. It exposes real distribution differences in the synthetic source sequence instead of averaging them away.

## 3. Model selection
An earlier balanced logistic-regression baseline under the same split achieved ROC AUC about 0.9015 but only 31.0% recall and F1 0.375. It was retained as a rejected experiment rather than promoted.

The selected model is:
- RandomForestClassifier;
- 100 trees;
- class_weight=balanced;
- min_samples_leaf=2;
- random_state=42;
- n_jobs=1 for stable evidence generation.

Threshold selection is performed only on the validation split by maximum F1. The frozen threshold is 0.35.

### Frozen test metrics
| Metric | Value |
|---|---:|
| Rows | 1,500 |
| Failures | 29 |
| Prevalence | 1.9333% |
| ROC AUC | 0.931644 |
| Average precision | 0.697250 |
| Precision | 0.666667 |
| Recall | 0.620690 |
| F1 | 0.642857 |
| Brier score | 0.0104762 |
| TN / FP / FN / TP | 1462 / 9 / 11 / 18 |

### Weak reference
Constant training-prevalence probability:
- ROC AUC: 0.500;
- average precision: 0.019333;
- Brier: 0.019375.

The selected model materially improves discrimination, ranking precision and probability error relative to this weak reference.

## 4. Deterministic MLOps evidence
Environment-specific latency is written separately from deterministic model evidence.

Two unchanged pipeline runs reproduced identical:
- source hash;
- serialized model hash;
- deterministic metrics hash;
- test-predictions hash;
- overall evidence hash.

Current deterministic evidence hash:
`76E75E7E792FF3AF90CAE5CBBA409F487E8FAC4A3133A2AF022B3830EB93FAC7`.

A clean-artifact rebuild, after deleting generated model/metric/prediction/manifests, reproduced the same expected hashes.

## 5. Local orchestration
`scripts/run_workflow.py` executes a bounded dependency order:
1. source fetch/hash verification;
2. weak baseline;
3. model train/version;
4. drift monitoring;
5. two-run idempotency;
6. pytest;
7. release build;
8. release verification.

The executed workflow completed all eight tasks successfully. Fetching is the only task with automatic retry because network retrieval may be transient. Deterministic validation/model failures are not blindly retried.

This is local Python orchestration; no Airflow, Prefect or cloud orchestrator claim is made.

## 6. API and container deployment
FastAPI v0.2.0 endpoints:
- `GET /health`;
- `GET /v1/model-info`;
- `POST /v1/predict`;
- `GET /metrics-summary`.

Middleware tracks:
- request count;
- HTTP error count/rate;
- mean latency;
- p95 latency;
- p99 latency;
- bounded request-latency window.

Docker image:
`sha256:262fb2ca5b9f3f3a40ddcaf6bee4c3e58351cb00ea01b09977152c2fb9539213`.

Final local container smoke test:
- health: OK;
- model_ready: true;
- model version: 0.2.0;
- valid prediction: HTTP success;
- deliberately invalid Type: HTTP 422;
- middleware recorded the intentional error.

Observed smoke-test latency is environment/startup-specific and is not a production SLA.

## 7. Drift monitoring
A batch monitor compares current features against the training reference using:
- numeric Population Stability Index;
- categorical Type total-variation distance;
- missing/non-finite feature counts.

Project alert rule:
- PSI >= 0.25; or
- Type total variation >= 0.10.

Frozen test split result: **ALERT**.

Largest shifts:
- Air temperature PSI: 7.50217;
- Process temperature PSI: 2.97234.

The high drift is retained and documented. The pipeline does not automatically retrain on drift.

## 8. Release and recovery
Versioned local release:
`releases/0.2.0/`.

Release manifest verifies:
- model.joblib;
- model_manifest.json;
- model_metrics.json;
- pipeline_manifest.json;
- requirements.txt.

Rollback drill:
1. deliberately corrupted the live model artifact;
2. confirmed model load failure;
3. restored model only from the verified 0.2.0 release;
4. confirmed inference recovery;
5. confirmed restored live model SHA-256 equals the release SHA-256.

Rollback/recovery test: PASSED.

## 9. Testing and CI
Refactored pytest trains once per session instead of once per test.

Final local test result:
- **11/11 passed in 5.32 s** in the direct validation run;
- the local orchestration run also reports 11/11 passed.

This closes the earlier >30 s connector timeout.

A GitHub Actions workflow is defined to:
- install pinned dependencies;
- run benchmark;
- run monitoring;
- run idempotency;
- run pytest;
- build the Docker image.

No remote GitHub Actions execution is claimed because the repository has not been published/run remotely.

## 10. Reproducible environment
Pinned key dependencies:
- Python 3.13;
- NumPy 2.4.1;
- pandas 3.0.0;
- SciPy 1.16.3;
- scikit-learn 1.8.0;
- joblib 1.5.3;
- FastAPI 0.128.0;
- Pydantic 2.11.7;
- Uvicorn 0.35.0;
- httpx 0.28.1;
- pytest 9.0.2.

## 11. Limitations
- Source data are synthetic, not measured factory telemetry.
- Chronological split is a scenario stress test, not a production temporal validation protocol.
- The model is not calibrated or validated for real equipment.
- No causal failure prediction claim.
- No automated retraining.
- No cloud, Kubernetes, warehouse, feature-store or managed registry implementation.
- Local release versioning is filesystem/hash based, not MLflow or a managed model registry.
- CI workflow is defined but has not run on a remote repository.
- API latency observations are local and not an SLA.

## 12. Evidence artifacts
- `artifacts/model_metrics.json`
- `artifacts/pipeline_manifest.json`
- `artifacts/idempotency_check.json`
- `artifacts/clean_rebuild_check.json`
- `artifacts/monitoring_snapshot.json`
- `artifacts/baseline_benchmark.json`
- `artifacts/docker_smoke_final.json`
- `artifacts/release_verification.json`
- `artifacts/rollback_recovery_test.json`
- `artifacts/workflow_run.json`
- `artifacts/pytest_final.txt`
- `figures/mlops_architecture.svg`
- `figures/model_vs_baseline.svg`
- `figures/feature_drift_psi.svg`
- `docs/RUNBOOK.md`
