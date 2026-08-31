---
title: "Agentic AI Reliability & Evaluation Harness"
type: research-project
status: planned
created: 2026-08-28
updated: 2026-08-28
tags: [research, reproducibility]
---
# Detailed Plan

## Phase 0 — Scope
- [ ] Define the exact decision/question and minimum credible scope.
- [ ] Populate references/SOURCES.md with source/date/license/use.
- [ ] Define data classes, units, assumptions, exclusions and validation criteria.
- [ ] Record important software/package versions.

## Phase 1 — Core build
- [ ] Define two benchmark workflows: one synthetic research-administration agent and one engineering-domain MCP agent
- [ ] Create a frozen evaluation set with normal, edge, adversarial and failure cases
- [ ] Measure retrieval quality and grounded/citation behavior where RAG is used
- [ ] Validate tool selection, tool arguments, schema compliance and task completion
- [ ] Track latency, cost/token use and failure categories
- [ ] Add prompt/model/version regression tests and explicit acceptance thresholds
- [ ] Create trace-level failure taxonomy and a small manual-adjudication sample
- [ ] Add CI quality gate and summary scorecard

## Phase 2 — Validation
- [ ] Add independent benchmark/reconciliation where possible.
- [ ] Add negative/failure tests.
- [ ] Check reproducibility from clean inputs.
- [ ] Record uncertainty and limitations.

## Phase 3 — Results and communication
- [ ] Create one high-signal figure/dashboard/architecture view.
- [ ] Write reports/technical-memo.md.
- [ ] Populate EVIDENCE.md with exact metrics.
- [ ] Write concise and detailed technical summaries.

## Phase 4 — Publication
- [ ] Remove secrets/private paths/restricted data.
- [ ] Verify clean setup and tests.
- [ ] Publish only after evidence gate passes.
