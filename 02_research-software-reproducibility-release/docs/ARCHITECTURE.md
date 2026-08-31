# Architecture

`h2bop-repro` is intentionally small and auditable.

1. `data/dwsim_green_h2_benchmark.json` is an immutable copied fixture from the validated DWSIM-MCP project.
2. `src/h2bop_repro/core.py` performs schema checks, relative-duty reconciliation, mass-balance checks, monotonicity checks and negative-case physics rejection.
3. `src/h2bop_repro/cli.py` exposes the validator as `python -m h2bop_repro.cli` and as the installed `h2bop-repro` console script when the environment exposes its Scripts/bin directory.
4. `tests/test_core.py` covers nominal and failure behavior.
5. `scripts/reproduce.ps1` builds and installs the wheel into a clean venv before validating the fixture.
6. `.github/workflows/ci.yml` defines the intended CI quality gate; no claim is made that hosted CI has run because the repository is not published.

The package contains no network calls, secrets, employer data or mutable external data dependencies.
