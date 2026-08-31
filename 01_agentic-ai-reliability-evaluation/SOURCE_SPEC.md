# SOURCE_SPEC — Agentic AI Reliability & Evaluation Harness

## Data classes
- `data/benchmark_cases.json`: project-authored synthetic benchmark cases. No private, employer, student, patient, or production data.
- `SYNTHETIC_DOCS` in `src/evaluate.py`: project-authored policy snippets used only to test citation/grounding logic.
- External references: public guidance/specifications used to define evaluation dimensions; they are not benchmark observations.

## Benchmark boundary
The MVP evaluates a deterministic orchestration/evaluation harness, not a live production LLM. Two workflows are represented: synthetic research administration and synthetic engineering MCP tool use. The evaluation set contains 24 frozen cases: normal, edge, adversarial, and failure/approval cases.

## Units / metrics
- Accuracy and completion metrics are fractions over the frozen 24-case benchmark.
- Latency and token fields are deterministic fixture metadata used to exercise reporting; they are NOT measured model/API latency or billing tokens.
- Bootstrap intervals resample benchmark cases and quantify case-set sensitivity only; they do not establish population-level AI reliability.

## Validation criteria
1. Exactly 24 cases, balanced 12/12 across the two workflows.
2. Normal, edge, adversarial, and failure classes present.
3. Guarded reference traces must satisfy expected tool, exact expected arguments, citation requirement, and approval/rejection requirement.
4. Intentionally weak baseline must produce known failures so the evaluator demonstrates detection sensitivity.
5. Missing tool arguments and unknown tools must fail schema validation.
6. Bootstrap comparison must be deterministic under a fixed seed.
7. Summary SVG must be valid XML.

## Exclusions
No healthcare validation, formal AI safety certification, real university records, live grant submission, autonomous external action, or claim of real-model accuracy.
