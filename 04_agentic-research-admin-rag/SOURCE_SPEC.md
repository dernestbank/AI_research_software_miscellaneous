# Source Specification

## Public policy sources
- NSF Preparing Your Proposal: official NSF guidance, paraphrased into the bounded corpus; retrieved 2026-08-29.
- NSF Submitting Your Proposal: official NSF submission guidance, paraphrased; retrieved 2026-08-29.
- NSF PAPPG policy page: official NSF policy metadata, paraphrased; retrieved 2026-08-29.
- NIH Submission Policies: official NIH guidance, paraphrased; retrieved 2026-08-29.

## Synthetic sources
- `SYN_ROUTING`: project-authored fictional university research-office routing policy.
- `SYN_SECURITY`: project-authored fictional copilot permission policy.

## Boundary
No clinical, HIPAA, private institutional, sponsor-account, or real proposal data are used. Public web text is paraphrased rather than copied wholesale. Numerical evaluation results come only from the frozen project-authored evaluation set.

## Runtime
Python 3.x standard library; pytest used for validation. No live LLM or external action API is required for the evidence run.
