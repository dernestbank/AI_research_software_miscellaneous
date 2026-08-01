# Detailed Plan

## Phase 0 - Scope and architecture
- [ ] Define exact user, problem, and bounded workflow.
- [ ] Populate references/SOURCES.md with datasets, framework docs, role signals, and licenses.
- [ ] Freeze minimum viable architecture.
- [ ] Define schemas, privacy/security assumptions, and evaluation metrics before implementation.
- [ ] Record runtime, package, model, and API versions.

## Phase 1 - Core implementation
- [ ] Model a synthetic university service-desk workflow
- [ ] Implement intake classification and routing
- [ ] Add grounded knowledge retrieval with citations
- [ ] Implement safe tool calls against a mock ticketing API
- [ ] Add user roles, permissions and audit trail
- [ ] Create human review for low-confidence or high-risk actions
- [ ] Benchmark routing accuracy and unsupported-action rate
- [ ] Document system architecture and operations

## Phase 2 - Validation
- [ ] Add deterministic unit and integration tests.
- [ ] Add at least one intentional failure or adversarial test.
- [ ] Establish quantitative evaluation appropriate to the system.
- [ ] Verify clean-environment reproducibility.
- [ ] Record unresolved limitations.

## Phase 3 - Recruiter-readable evidence
- [ ] Create architecture diagram.
- [ ] Create one 60-second demo path.
- [ ] Create concise evaluation/results table.
- [ ] Write reports/technical-memo.md.
- [ ] Populate EVIDENCE.md with exact metrics only.

## Phase 4 - ATS and interview packaging
- [ ] Write 30-second project explanation.
- [ ] Write 2-minute technical explanation.
- [ ] Draft 2-3 evidence-backed resume bullets.
- [ ] Record genuinely unlocked ATS keywords.
- [ ] Prepare architecture, evaluation, and failure-mode interview questions.

## Phase 5 - Publication
- [ ] Remove secrets, private paths, and restricted data.
- [ ] Add install/run/test instructions.
- [ ] Run tests from a clean environment.
- [ ] Publish only after the evidence gate passes.

## Promotion gate
- [ ] Working implementation
- [ ] Validation/evaluation completed
- [ ] Failure cases documented
- [ ] Recruiter-readable artifact
- [ ] Technical memo
- [ ] Evidence boundary preserved: Do not claim production integration with real university systems or realized operational savings.

