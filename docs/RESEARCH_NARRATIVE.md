# Research Development Narrative

Six-month arc (March–August 2026) for the AI & Research Software portfolio track. Dates align with git history; claims in `EVIDENCE.md` files remain gated on validation.

## Phase 1 — Evaluation foundations (March 2026)

**Project 01 — Agentic AI Reliability & Evaluation Harness**

- Defined benchmark cases spanning research-administration tool use, citation requirements, and privilege boundaries.
- Built a deterministic evaluation harness (not an LLM) to score expected traces, schema validity, and failure modes.
- Ran first benchmark pass; produced case-level scores and a reliability scorecard figure.
- Drafted technical memo and manual adjudication notes for ambiguous cases.

## Phase 2 — RAG copilot for research administration (April–May 2026)

**Project 04 — Agentic Research Administration RAG**

- Assembled a synthetic public corpus and evaluation set for grant-administration scenarios.
- Implemented retrieval, agent routing, admin tools, and a copilot orchestration layer.
- Logged tool traces, failed evaluation runs, and reproducibility checks.
- Documented architecture and limitations in the technical memo.

## Phase 3 — Verification & validation benchmark (May–June 2026)

**Project 05 — AI/ML V&V Benchmark**

- Designed validation matrix covering robustness probes and negative controls.
- Implemented agent-style V&V checks and orchestrated verification reports.
- Published artifact bundle (matrix CSV/JSON, robustness and clean-environment reports).
- Added release-gate demo figure for recruiter walkthrough.

## Phase 4 — Reproducibility and MLOps (June–July 2026)

**Project 02 — Research Software Reproducibility Release**

- Packaged a minimal reproducible CLI/library (`h2bop_repro`) with pinned workflow.
- Added tests and a reproducibility summary figure.

**Project 03 — AI Data Pipeline & MLOps**

- Built sklearn-based training pipeline on public UCI AI4I 2020 data (labeled synthetic/portfolio use).
- Added monitoring snapshots, idempotency checks, rollback tests, and release manifests.
- Produced architecture, drift, and model-vs-baseline figures.

## Phase 5 — Forward portfolio (July–August 2026)

**Projects 06–09** — Architecture and evidence design only:

| Project | Focus |
|---------|--------|
| 06 Secure RAG & Agent Red-Team Lab | Attack taxonomy and evaluation design |
| 07 University Operations AI Automation | Workflow boundaries and tool permissions |
| 08 ML/LLM Observability & Governance | Drift metrics and governance dashboard spec |
| 09 Learning Analytics & Student Success | Synthetic analytics product scoping |

## Evidence discipline

- Synthetic and public inputs are labeled in `SOURCE_SPEC.md` and data READMEs.
- Failed runs are preserved in artifacts where applicable.
- Resume-ready claims require passing each project's evidence gate — see per-project `STATUS.md`.
