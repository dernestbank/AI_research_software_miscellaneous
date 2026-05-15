# Technical Memo — Agentic Research Administration RAG & Tool-Use Copilot

## Scope
A bounded, deterministic portfolio prototype for research-administration policy retrieval and read-only workflow assistance. It uses official NSF/NIH guidance paraphrases plus two clearly synthetic internal-policy documents. It is not an institutional deployment, clinical system, HIPAA environment, or live sponsor-submission agent.

## Architecture
`src/copilot.py` implements metadata-preserving hybrid lexical retrieval, cited answer assembly, four read-only tools, an explicit workflow state, and an audit trace. External/privileged actions—submission, email, deletion, and permission changes—are refused without explicit approval and remain simulated even when approved in this demo.

## Evaluation
The frozen evaluation set contains 12 retrieval queries and 6 unsafe-action requests. Results: top-1 retrieval accuracy 91.67%, hit@3 100%, MRR@3 0.9583, unsafe-action refusal 100%. These are deterministic benchmark results on a small project-authored corpus, not general LLM performance claims.

## Validation
Eight unit/integration tests cover NSF/NIH retrieval, citation presence, checklist tool behavior, unknown-tool rejection, submission refusal, adversarial submission wording, and deterministic document comparison. The recruiter architecture SVG is XML-validated. The demo runs three paths: NSF checklist, NIH deadline policy, and a refused submission request.

## Failure modes and limitations
Lexical retrieval is intentionally lightweight and may underperform on semantic paraphrases or larger corpora. Corpus freshness depends on manual source updates. The system does not resolve solicitation-specific requirements unless represented in the corpus. No live LLM, authentication service, institutional RBAC, sponsor API, production logging backend, privacy review, or compliance certification is claimed.

## Reproduction
From the project root: `python -m pytest -q`, `python src/evaluate.py`, and `python demo/run_demo.py`. The core implementation requires only the Python standard library; pytest is needed for the test command.
