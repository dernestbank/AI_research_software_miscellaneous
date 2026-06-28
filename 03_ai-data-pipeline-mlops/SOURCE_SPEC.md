# SOURCE_SPEC — AI Data Pipeline + MLOps Deployment

## Decision / use case
Build a bounded predictive-maintenance ML service that ingests the public UCI AI4I 2020 dataset, validates its schema, trains a small interpretable binary classifier for `Machine failure`, versions the resulting model/metrics, exposes prediction and health endpoints, and records data-quality/drift/failure behavior.

The project demonstrates MLOps mechanics; it is not an industrial production system and the source dataset itself is synthetic.

## Primary structured source
- **AI4I 2020 Predictive Maintenance Dataset**, UCI Machine Learning Repository.
- DOI: `10.24432/C5HS5C`.
- 10,000 rows; UCI describes the dataset as synthetic but designed to reflect predictive-maintenance data encountered in industry.
- License: CC BY 4.0.
- Downloaded 2026-08-29 from the official UCI static dataset attachment.
- Raw ZIP SHA-256: `F601F14294BCF190F9D720676B7F0AEA46A26CDE9AB8EBC7B4F8174D9D26B252`.
- Raw inputs remain unchanged under `data/raw/`.

## Features and leakage policy
Allowed predictors:
- `Type` (categorical)
- `Air temperature [K]`
- `Process temperature [K]`
- `Rotational speed [rpm]`
- `Torque [Nm]`
- `Tool wear [min]`

Target: `Machine failure`.

Excluded from prediction:
- `UDI`, `Product ID` — identifiers.
- `TWF`, `HDF`, `PWF`, `OSF`, `RNF` — failure-mode outcome fields that would leak target-generation information.

## Frozen split
Rows are ordered by UDI to make split/reproduction deterministic:
- Train: UDI 1–7000.
- Validation: UDI 7001–8500.
- Test: UDI 8501–10000.
No random resampling is used for the primary split.

## Data-quality contract
- Exactly 10,000 rows in the authoritative raw CSV.
- Required 14 columns present.
- No missing values in required predictors/target.
- UDI unique and strictly increasing after source-order load.
- Target values restricted to {0,1}.
- Type restricted to {L,M,H}.
- Numeric predictors finite.

## Model / evaluation contract
- Preprocessing: standardize numeric predictors; one-hot encode `Type`.
- Classifier: logistic regression with balanced class weights; deterministic solver configuration.
- Classification threshold selected on validation data by maximum F1, then frozen before test evaluation.
- Report test ROC AUC, average precision (PR AUC), precision, recall, F1, Brier score, confusion matrix and latency sample.
- Report class prevalence for all splits so imbalanced-label performance is not obscured.
- Report a simple feature-distribution drift diagnostic between train and test; it is a monitoring signal, not proof of operational drift.

## Failure/negative tests
Reject missing required columns, missing predictor values, invalid target labels and unknown product type. API must reject malformed payloads. Rerunning the batch pipeline on unchanged raw input must be deterministic for metrics/model manifest.

## Evidence boundary
No claims of real factory deployment, cloud scale, Kubernetes, enterprise orchestration, causal prediction, generalization beyond this synthetic benchmark, or production business impact.
