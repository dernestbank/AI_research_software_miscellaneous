# Formal V&V Test Plan

## Purpose
Evaluate two already-built portfolio systems with independent, requirement-based checks:
1. Primary ML SUT: AI4I predictive-maintenance MLOps release 0.2.0.
2. Secondary agent SUT: research-administration RAG/tool-use copilot.

The V&V harness may pass even if a SUT receives HOLD. A HOLD is an expected valid outcome when a release requirement fails.

## Evidence boundary
This is portfolio TEVV evidence only. It is not certification, formal third-party validation, DoD verification authority, regulated qualification, or safety-critical approval.

## ML SUT requirements
| ID | Requirement | Criterion | Rationale |
|---|---|---|---|
| ML-001 | Prediction artifact identity | SHA-256 equals frozen manifest | detect wrong/corrupt artifact |
| ML-002 | Confusion matrix reconciliation | exact TN/FP/FN/TP match | independent metric reconstruction |
| ML-003 | Recall floor | >= 0.60 | project release criterion for rare failures |
| ML-004 | Brier ceiling | <= 0.02 | probability-quality gate |
| ML-005 | Probability range | every p in [0,1] | output validity |
| ML-006 | Missing/nonfinite monitor cells | both zero | data-quality release gate |
| ML-007 | Distribution shift | max numeric PSI < 0.25 | project drift rule; not universal |
| ML-008 | Calibration | 10-bin ECE <= 0.03 | project calibration rule |
| ML-009 | Modest-noise robustness | worst prediction-flip rate <= 5% | stability under bounded sensor perturbation |
| ML-010 | Modest-noise recall stability | worst recall drop <= 0.10 absolute | avoid large sensitivity in positive detection |
| ML-011 | Edge-row output validity | finite probabilities in [0,1] | model should handle observed-source extrema |

### Modest sensor-noise scenario
Five deterministic seeds. Independent zero-mean Gaussian perturbations:
- air temperature: sigma 0.2 K;
- process temperature: sigma 0.2 K;
- rotational speed: sigma 20 rpm;
- torque: sigma 0.5 Nm;
- tool wear: sigma 1 minute.

Perturbed values are clipped to the observed 10,000-row source min/max. This is a project stress scenario, not a calibrated sensor-error distribution.

## Negative controls
The harness must reject:
- a prediction file with one modified probability when checked against the frozen SHA-256;
- a prediction file missing a required column;
- any probability outside [0,1];
- malformed/non-numeric probability values.

## Threshold sensitivity
Report precision/recall/F1 at thresholds 0.30, 0.35, and 0.40. Do not select a new release threshold from the frozen test set.

## Subgroup analysis
Report Type L/M/H:
- row count;
- positive count;
- precision;
- recall;
- F1;
- Brier.

No fairness/parity claim is made because the synthetic dataset and subgroup positive counts are limited.

## Agent SUT requirements
| ID | Requirement | Criterion |
|---|---|---|
| AG-001 | Frozen retrieval top-1 | >= 0.90 |
| AG-002 | Retrieval hit@3 | == 1.00 |
| AG-003 | MRR@3 | >= 0.90 |
| AG-004 | Unsafe external-action refusal | == 1.00 |
| AG-005 | Evaluation artifact reproducibility | recorded deterministic hash available |

These checks consume the sibling project's primary frozen evaluation artifact. Supplemental experiments are not mixed into this requirement matrix.

## Harness acceptance
The **V&V project evidence gate** passes when:
- automated tests for the V&V harness pass;
- negative controls are detected;
- robustness/subgroup/calibration analyses execute reproducibly;
- SUT requirement results are reported without suppressing failures;
- clean-environment reproduction passes;
- recruiter report/artifact and technical memo are complete.

The ML SUT release disposition is independent and remains HOLD if any required ML release criterion fails.
