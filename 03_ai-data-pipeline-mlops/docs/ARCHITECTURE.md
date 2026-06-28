# Architecture

```text
UCI AI4I CC BY 4.0
        |
        v
hash-verifying fetch
        |
        v
schema + leakage checks
        |
        v
UDI 70/15/15 split
        |
        +-------> drift monitor (train vs current)
        |
        v
RandomForest training
        |
        v
validation threshold selection
        |
        v
frozen test evaluation
        |
        +-------> deterministic manifests + release bundle
        |
        v
FastAPI v0.2.0
  |       |       |
health  predict  metrics
        |
        v
Docker smoke test
```

## Evidence boundaries
- UCI data are synthetic predictive-maintenance records, not factory telemetry.
- Batch training is local and deterministic; no remote orchestrator or managed cloud platform is claimed.
- GitHub Actions workflow is defined locally; no remote CI execution is claimed until a repository run exists.
- Docker inference smoke testing is local.
