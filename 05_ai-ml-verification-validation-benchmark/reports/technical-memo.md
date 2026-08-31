# Technical Memo — AI/ML Verification & Validation Benchmark

**Date:** 2026-08-29
**Harness evidence status:** VALIDATED
**ML SUT disposition:** HOLD
**Agent SUT disposition:** PASS

## Executive summary
This project independently verifies two frozen sibling systems without modifying them: an AI4I predictive-maintenance ML release v0.2.0 and a research-administration RAG/tool-use copilot. The harness checks artifact identity, independently rebuilds metrics, evaluates calibration, threshold sensitivity, bounded-noise robustness, observed-range edge cases, subgroup behavior, corruption controls, and explicit release requirements.

The key result is intentionally not an all-green model release. The ML SUT passes 10 of 11 requirements but remains on HOLD because max numeric PSI is 7.50217 against a project-defined release rule of <0.25. The agent SUT passes 5/5 bounded frozen requirements. The V&V harness itself passes 7/7 automated tests in both the working environment and a fresh Python 3.13.5 virtual environment, and detects all 4/4 corrupted prediction-artifact controls.

## ML system under test
Source system: sibling project `03_ai-data-pipeline-mlops`, release 0.2.0. Upstream UCI AI4I benchmark is explicitly synthetic and CC BY 4.0.

Frozen 1,500-row prediction reconciliation:
- TN 1462, FP 9, FN 11, TP 18;
- precision 0.666667;
- recall 0.620690;
- F1 0.642857;
- Brier 0.0104762;
- 10-bin ECE 0.0110035.

## Requirement result
The ML SUT passes artifact identity, confusion reconciliation, recall, Brier, output probability bounds, monitoring missing/nonfinite checks, calibration, bounded-noise prediction stability, bounded-noise recall stability, and observed-extreme output validity.

It fails one release gate:
- max numeric PSI = 7.50217;
- frozen project criterion = <0.25;
- disposition = HOLD.

The failed drift requirement is not suppressed or bypassed.

## Robustness and edge cases
Five deterministic modest-noise runs perturb temperature, rotational speed, torque and tool wear within observed source bounds. The scenario is a project stress test, not a calibrated sensor-error model.

Observed worst cases:
- prediction flip rate = 0.005333, below 0.05 gate;
- absolute recall drop = 0.034483, below 0.10 gate;
- 9 observed-extreme source rows returned finite probabilities within [0,1].

Subgroup slices are reported but not interpreted as fairness evidence. Type H has zero positive test examples and Type M only four positives.

## Threshold analysis
At thresholds 0.30 / 0.35 / 0.40:
- precision = 0.6452 / 0.6667 / 0.8095;
- recall = 0.6897 / 0.6207 / 0.5862;
- F1 = 0.6667 / 0.6429 / 0.6800.

No new threshold is selected from the frozen test set. Any future threshold change should be based on validation data and operational error costs.

## Negative controls
The harness deliberately corrupts the frozen prediction artifact four ways and detects all four:
1. modified probability causing hash mismatch;
2. missing required probability column;
3. probability outside [0,1];
4. non-numeric probability.

The unmodified frozen artifact passes validation.

## Agent system under test
The sibling research-admin copilot frozen evaluation passes 5/5 project requirements:
- top-1 retrieval = 0.9167;
- hit@3 = 1.0000;
- MRR@3 = 0.9583;
- unsafe external-action refusal = 1.0000;
- evaluation artifact is present and SHA-256 hashable.

This PASS is bounded regression evidence on a small project-authored evaluation set, not a production or institutional certification claim.

## Reproducibility
Working-environment pytest: 7/7 passed.

Fresh environment:
- Python 3.13.5;
- NumPy 2.4.1;
- pandas 3.0.0;
- SciPy 1.16.3;
- scikit-learn 1.8.0;
- joblib 1.5.3;
- pytest 9.0.2;
- 7/7 tests passed.

A prior pytest launch hit a connector 502 before a result was returned. That execution failure was not interpreted as a pass; a subsequent direct rerun completed successfully.

## Recommendation matrix
- **ML drift:** release-blocking. Keep HOLD and investigate shifted feature distributions and data representativeness before retraining/re-release.
- **ML threshold:** analytical only. Do not retune on the test set.
- **ML subgroup:** limitation. Do not make parity/fairness claims from sparse synthetic slices.
- **Agent:** scoped PASS. Expand corpus and evaluation diversity before broader reliability claims.

## Evidence boundary
This is a research V&V/TEVV harness. It is not formal third-party certification, DoD verification authority, regulated qualification, safety-critical approval, or production release authority.
