# AI Research Software — Repository Guide

Research collection for agentic AI, research software engineering, MLOps, and applied ML validation evidence. Each numbered directory is an independent project with its own scope boundary, validation plan, and evidence gate.

## Layout convention

| Path | Purpose |
|------|---------|
| `About.md` | Problem statement, audience, and boundary |
| `PLAN.md` | Phased build plan and acceptance criteria |
| `SOURCE_SPEC.md` | Data sources, licenses, and input provenance |
| `STATUS.md` | Current milestone checklist (updated as work progresses) |
| `EVIDENCE.md` | Verified claims only — no promotion before validation |
| `src/` | Runnable implementation |
| `tests/` | Automated checks tied to acceptance criteria |
| `data/` | Versioned inputs (public or labeled synthetic) |
| `artifacts/` | Generated run outputs (JSON, CSV, logs) |
| `figures/` or `demo/` | Summary visual summaries |
| `reports/` | Technical memos and adjudication notes |
| `references/` | External sources and version pins |
| `decisions/` | Engineering decision log |

## Build order (recommended)

1. **01** Agentic AI Reliability & Evaluation Harness
2. **04** Agentic Research Administration RAG & Tool-Use Copilot
3. **05** AI/ML Verification & Validation Benchmark
4. **02** Research Software Reproducibility Release
5. **03** AI Data Pipeline & MLOps Deployment
6. **06–09** Planning-phase projects (architecture and evidence design)

## What belongs in git

- Experiment code, evaluation harnesses, benchmark cases
- Reproducible artifacts from validated runs
- Figures derived from those runs
- Technical memos with explicit limitations

## What stays local (see `.gitignore`)

- Virtual environments, caches, and vector DB runtime state
- Secrets and machine-local `.env` files
- Local AI assistant instruction files (`AGENTS.md`, etc.)

## Running an implemented project

Each project with `src/` includes a `README.md` with setup steps. Typical flow:

```bash
cd 01_agentic-ai-reliability-evaluation
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt  # when present
python src/evaluate.py
pytest
```

Re-run validation before citing metrics or `EVIDENCE.md`.
