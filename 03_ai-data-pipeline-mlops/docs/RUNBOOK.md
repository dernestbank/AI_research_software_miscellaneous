# Operations Runbook — AI4I MLOps Service

## Scope
This runbook covers the local/containerized portfolio service only. It does not claim production SRE coverage, cloud deployment, Kubernetes, or enterprise incident response.

## Normal release flow
1. Retrieve/verify source: `python scripts/fetch_data.py`.
2. Run weak baseline: `python src/benchmark.py`.
3. Train/evaluate/version artifacts: `python src/pipeline.py`.
4. Generate monitoring snapshot: `python src/monitoring.py`.
5. Verify deterministic reruns: `python scripts/check_idempotency.py`.
6. Run tests: `python -m pytest tests -q`.
7. Build versioned release: `python scripts/build_release.py`.
8. Verify release hashes: `python scripts/verify_release.py`.
9. Build container: `docker build -t ai4i-mlops:0.2.0 .`.
10. Smoke-test endpoints before replacing any running instance.

## Retry policy
Retry only failures likely to be transient:
- source HTTP/network retrieval;
- container pull/build network dependency retrieval.

Do **not** retry data validation, hash mismatch, schema mismatch, test failure, model-metric failure, or release-manifest failure without diagnosis. These are deterministic blockers.

## Data/schema failure
If source row count, columns, labels, type values, missingness, or hash contract fails:
- stop before training;
- preserve the failing input separately;
- compare source metadata/version;
- update the source contract only with documented rationale;
- rerun all downstream checks.

## Drift alert
Current monitoring rule:
- alert if numeric PSI >= 0.25; or
- Type-distribution total variation >= 0.10.

These thresholds are project rules, not universal standards.

On alert:
1. Do not automatically retrain.
2. Inspect which feature triggered.
3. Compare target prevalence if labels are available.
4. Run model evaluation on the shifted labeled slice.
5. Retrain only if the decision boundary and evidence contract justify it.

The frozen chronological test split currently triggers ALERT because air-temperature PSI is ~7.50.

## API/service failure
Health endpoint:
- `GET /health`
- expected: `status=ok`, `model_ready=true`, version `0.2.0`.

If model artifact is missing or unreadable:
- do not serve predictions;
- restore the last verified release bundle;
- verify its release manifest;
- restart the service;
- rerun health, model-info, valid prediction, invalid-payload, and metrics probes.

## Rollback
Versioned release bundles live under `releases/<version>/`.

Rollback procedure:
1. Stop the current container/process.
2. Verify the target release with `scripts/verify_release.py` or equivalent hash verification.
3. Copy the verified model artifact and manifest from the selected release into `artifacts/`.
4. Rebuild/restart the container with the selected version tag.
5. Run smoke probes.
6. Record the reason and resulting version in the decision/incident log.

Do not roll back to an unverified artifact merely because it is older.

## Monitoring
API middleware tracks:
- request count;
- HTTP error count/rate;
- mean latency;
- p95 latency;
- p99 latency;
- bounded in-memory window size.

Batch monitoring tracks:
- numeric PSI by feature;
- maximum PSI feature;
- Type distribution total variation;
- missing feature cells;
- non-finite numeric cells.

Latency values are environment-specific and excluded from deterministic model evidence hashes.

## Evidence preservation
Keep:
- source hashes;
- model/data/code manifest;
- test output;
- Docker image ID and smoke result;
- clean-rebuild result;
- release verification;
- monitoring snapshot;
- rejected model baseline.

Never replace failed evidence with a later successful run without retaining the failure note.
