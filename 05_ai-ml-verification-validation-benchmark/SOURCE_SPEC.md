# Source Specification

## Primary ML system under test
Evidence-gated AI4I MLOps model from sibling project 03_ai-data-pipeline-mlops, version 0.2.0.

Read-only artifacts:
- artifacts/model.joblib
- artifacts/model_manifest.json
- artifacts/model_metrics.json
- artifacts/monitoring_snapshot.json
- artifacts/test_predictions.csv
- data/raw/uci/ai4i2020.csv

Upstream data provenance: UCI AI4I 2020 Predictive Maintenance Dataset, explicitly synthetic, 10,000 rows, CC BY 4.0, DOI 10.24432/C5HS5C.

## Secondary agent system under test
Completed sibling project 04_agentic-research-admin-rag.

Primary read-only evaluation artifact:
- artifacts/evaluation.json

The V&V project uses the sibling project's promoted frozen evaluation (12 retrieval cases, 6 unsafe-action cases). It does not merge later supplemental experiments into the release matrix.

## Evidence boundary
Portfolio verification and validation only. No formal certification, independent third-party authority, DoD verification authority, safety-critical qualification, production-release authority, or regulated compliance claim.

## Frozen V&V contract
See docs/TEST_PLAN.md. Criteria are explicit before robustness/agent execution. Failed SUT gates are preserved and can legitimately yield HOLD while the V&V harness itself passes.
