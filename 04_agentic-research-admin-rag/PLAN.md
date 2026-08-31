# Detailed Plan

## Phase 0 - Scope and architecture
- [ ] Define exact user, problem, and bounded workflow.
- [ ] Populate references/SOURCES.md with datasets, framework documentation, benchmark references, and licenses.
- [ ] Freeze minimum viable architecture.
- [ ] Define schemas, privacy/security assumptions, and evaluation metrics before implementation.
- [ ] Record runtime, package, model, and API versions.

## Phase 1 - Core implementation
- [ ] Create a public/synthetic research-administration knowledge corpus
- [ ] Implement hybrid retrieval with citations and source metadata
- [ ] Add tool-use for deadline lookup, checklist generation, policy lookup, and document comparison
- [ ] Implement multi-step agent workflows with explicit state and tool traces
- [ ] Create evaluation sets for retrieval, groundedness, tool correctness, safety and refusal behavior
- [ ] Add permission simulation and audit logging
- [ ] Expose a small API and demo UI or CLI
- [ ] Document failure cases and unsupported actions

## Phase 2 - Validation
- [ ] Add deterministic unit and integration tests.
- [ ] Add at least one intentional failure or adversarial test.
- [ ] Establish quantitative evaluation appropriate to the system.
- [ ] Verify clean-environment reproducibility.
- [ ] Record unresolved limitations.

## Phase 3 - Summary evidence
- [ ] Create architecture diagram.
- [ ] Create one 60-second demo path.
- [ ] Create concise evaluation/results table.
- [ ] Write reports/technical-memo.md.
- [ ] Populate EVIDENCE.md with exact metrics only.

## Phase 4 - Technical synthesis
- [ ] Write a concise results summary.
- [ ] Write a detailed methods-and-limitations summary.
- [ ] Record 2-3 validated findings backed by artifacts.
- [ ] Record technical capabilities that are actually implemented.
- [ ] Record open architecture, evaluation, and failure-mode questions for follow-up.

## Phase 5 - Publication
- [ ] Remove secrets, private paths, and restricted data.
- [ ] Add install/run/test instructions.
- [ ] Run tests from a clean environment.
- [ ] Publish only after the evidence gate passes.

## Promotion gate
- [ ] Working implementation
- [ ] Validation/evaluation completed
- [ ] Failure cases documented
- [ ] Summary artifact
- [ ] Technical memo
- [ ] Evidence boundary preserved: Use public or synthetic research-administration data only. Do not claim HIPAA/clinical production compliance or institutional deployment.

