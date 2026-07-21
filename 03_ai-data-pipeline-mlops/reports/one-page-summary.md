# One-Page Evidence Summary — AI Data Pipeline & MLOps Deployment

## Scope
Local/containerized predictive-maintenance MLOps evidence using the public **synthetic** UCI AI4I 2020 benchmark.

## Pipeline
UCI source -> SHA/schema/leakage validation -> deterministic UDI train/validation/test split -> random-forest training -> validation-selected threshold -> frozen test evaluation -> deterministic manifests -> FastAPI -> Docker -> monitoring/release/rollback.

## Test model
- Test rows: 1,500
- Failures: 29
- ROC AUC: 0.931644
- Average precision: 0.697250
- Precision: 0.666667
- Recall: 0.620690
- F1: 0.642857
- Brier: 0.0104762

Weak constant reference:
- ROC AUC 0.500
- Average precision 0.019333
- Brier 0.019375

## Reproducibility
- Exact UCI ZIP + CSV SHA-256 verified.
- Two unchanged runs reproduce model, metrics, predictions and overall evidence hashes.
- Clean-artifact rebuild reproduces expected hashes.
- Deterministic evidence hash: `76E75E7E...93FAC7`.

## Monitoring
Frozen test split triggers project drift ALERT:
- Air temperature PSI: 7.50217
- Process temperature PSI: 2.97234
- Type distribution total variation: 0.01376

## Deployment / recovery
- FastAPI v0.2.0.
- Docker image: `sha256:262fb2ca...9539213`.
- Valid prediction succeeds.
- Invalid Type returns 422 and is counted by middleware.
- Versioned 0.2.0 release verifies all hashes.
- Controlled corrupt-model rollback drill: PASSED.

## Validation
- 11/11 pytest checks passed.
- Local eight-stage workflow: PASSED.
- 3 recruiter SVGs parse successfully.
- GitHub Actions workflow defined locally; remote CI run not claimed.

## Boundary
No real-factory deployment, Kubernetes, cloud scale, enterprise MLOps, causal prediction, managed model registry or production business-impact claim.
