# Decision Log

## 2026-08-29 — System under test
Use the already evidence-gated AI4I MLOps model v0.2.0 from sibling project #3 as the V&V system under test. This avoids creating another model and keeps the project focused on verification, independent metric reconciliation, robustness and release gating.

## 2026-08-29 — Release rule
A V&V harness can pass while the evaluated model is held. Requirements include artifact identity, confusion reconciliation, recall >=0.60, Brier <=0.02, probability bounds, no missing/nonfinite monitor cells, and a project-defined max PSI <0.25 release criterion.

## 2026-08-29 — Preserved implementation failure
First `verify.py` run failed with FileNotFoundError because the sibling project path resolved one parent too high. The failure was preserved; only the path expression was corrected before rerun.

## 2026-08-29 — Current model disposition
Independent recomputation reconciled TN/FP/FN/TP = 1462/9/11/18, precision 0.6667, recall 0.62069, F1 0.642857 and Brier 0.0104762. Six of seven current requirements pass. The release decision is HOLD solely because max numeric PSI = 7.50217 exceeds the project-defined <0.25 drift gate.

## 2026-08-29 — Harness promotion while preserving SUT HOLD
Completed the full requirement matrix after robustness, calibration, edge-case, subgroup and corruption-control execution. ML SUT passes 10/11 requirements but remains HOLD because max numeric PSI 7.50217 exceeds the frozen project rule <0.25. Agent SUT passes 5/5. The harness itself passes 7/7 pytest checks in both working and fresh Python 3.13.5 environments. The failed drift gate is retained as the primary release-blocking finding rather than bypassed.

## 2026-08-29 — Connector failure handling
An initial pytest launch returned HTTP 502 without an execution result. No pass was inferred. A direct rerun completed 7/7, and a separately created fresh virtual environment also completed 7/7. This preserves execution provenance and avoids treating transport failure as test success.
