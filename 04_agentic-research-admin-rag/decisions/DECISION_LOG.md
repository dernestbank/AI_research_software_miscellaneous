# Decision Log

## 2026-08-29 — Freeze bounded deterministic architecture
Selected a lightweight deterministic retrieval/tool-use copilot instead of a live-LLM dependency so evidence is reproducible and attributable. Public NSF/NIH guidance is paraphrased; internal-office policies are synthetic.

## 2026-08-29 — Permission model
Read-only policy lookup, checklist generation, deadline lookup, and document comparison are allowed. Submission, email, deletion, and permission changes require explicit approval and remain simulated even after approval in this portfolio implementation.

## 2026-08-29 — Evaluation contract
Frozen evaluation: 12 retrieval cases plus 6 unsafe-action requests. Metrics are top-1 accuracy, hit@3, MRR@3, and unsafe-action refusal rate. These metrics describe only this bounded corpus and benchmark.

## 2026-08-29 — Artifact validation failure retained
The first architecture SVG generated through the file writer failed XML parsing. It was not accepted. The SVG was rewritten as plain UTF-8 and subsequently parsed successfully.
