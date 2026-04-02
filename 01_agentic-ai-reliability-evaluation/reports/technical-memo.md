# Technical Memo — Agentic AI Reliability & Evaluation Harness

## Objective
Build a reproducible, reviewer-readable harness for evaluating agent orchestration behavior across two synthetic workflows: research administration and engineering MCP tool use. The artifact targets tool selection, argument correctness, citation/grounding behavior, approval boundaries, adversarial cases, regression detection, and trace-level failure classification.

## Scope and evidence boundary
The benchmark contains 24 project-authored synthetic cases (12 research-administration, 12 engineering-MCP) spanning normal, edge, adversarial, and failure/approval classes. No private records or production systems are used. This MVP evaluates deterministic reference traces and the evaluator itself. It does **not** claim measured reliability of a live LLM, production healthcare validation, formal AI safety certification, or autonomous deployment readiness.

## Method
Each case freezes an expected tool, exact expected arguments, whether a citation is required, the expected synthetic document ID when applicable, and whether a potentially irreversible action must be rejected or routed for approval. The scorer reports tool-selection accuracy, argument accuracy, citation accuracy, unsafe-action block rate, task-completion rate, latency/token fixture fields, failure categories, and class-level completion.

Two deterministic policies exercise the harness. `baseline_trace` is intentionally weak and contains known routing, schema, citation, prompt-injection-style, and approval-boundary failures. `guarded_trace` is a known-good regression fixture generated from the benchmark contract. Its perfect score is therefore a scorer/regression-fixture result and must not be interpreted as real model accuracy.

The failure taxonomy currently includes `wrong_tool`, `invalid_arguments`, `citation_failure`, and `unsafe_action_not_blocked`. A six-case manual adjudication sample checks whether the scorer agrees with human interpretation of representative known-good and known-bad traces.

## Validated results
A clean Windows execution generated artifacts and pytest reported 7/7 passing tests.

| Metric | Intentionally weak baseline | Guarded reference fixture |
|---|---:|---:|
| Tool-selection accuracy | 58.33% | 100.00% |
| Exact argument accuracy | 50.00% | 100.00% |
| Citation accuracy | 87.50% | 100.00% |
| Unsafe-action block rate | 75.00% | 100.00% |
| Task-completion rate | 37.50% | 100.00% |

The baseline generated 10 wrong-tool detections, 2 invalid-argument detections, 3 citation failures, and 6 unsafe-action failures. A 2,000-draw fixed-seed case bootstrap estimated a mean guarded-minus-baseline completion difference of 62.81 percentage points, with a case-resampling 2.5–97.5 percentile range of 45.83–83.33 percentage points. This interval describes sensitivity to this finite synthetic case set only.

## Failure / negative testing
Validation deliberately checks malformed tool arguments and unknown tools, verifies that intentionally corrupted baseline traces are detected, checks all six unsafe cases under the guarded reference fixture, verifies adversarial-case completion, and verifies bootstrap reproducibility. The baseline's failures are preserved as evidence that the evaluator is not simply returning a pass for every trace.

## Design provenance
NIST AI RMF 1.0 and the NIST Generative AI Profile are used as high-level TEVV/risk-management framing. MCP tool specifications inform schema/tool-call and human-in-the-loop expectations. OWASP GenAI/LLM guidance informs adversarial prompt-injection and excessive-agency case design. These sources are design references, not sources of benchmark performance data.

## Limitations
The benchmark is small, synthetic, and hand-authored. The guarded fixture is derived from expected outputs, so its 100% score validates scoring/regression plumbing rather than model intelligence. Latency and token fields are deterministic fixture metadata, not API measurements. No real retrieval model, agent SDK, commercial model, or live MCP server is scored in this MVP. A future extension should add frozen live-model traces across model/prompt versions while preserving the same evidence contract.

## Recruiter interpretation
The defensible claim is that this project implements a reproducible agent-evaluation harness with frozen cases, trace scoring, schema/citation/safety gates, adversarial cases, failure taxonomy, regression comparison, bootstrap sensitivity analysis, manual adjudication, tests, and a scorecard. The project does not support claims of 100% LLM reliability.
