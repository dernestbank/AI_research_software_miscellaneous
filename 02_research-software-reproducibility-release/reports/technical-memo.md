# Technical Memo — Reproducible Green-H2 Compressor Benchmark Release

**Date:** 2026-08-29  
**Artifact:** `h2bop-repro` v0.1.0 local release candidate

## Objective
Package a previously validated Green-H2 balance-of-plant compressor reconciliation as small, installable and auditable research software. The package is a reproducibility/validation layer; it does not rerun DWSIM or create new process-simulation results.

## Scientific fixture
The frozen fixture comes from the completed DWSIM-MCP research project. Four valid 20→200 bar H2 compression cases are retained at 750, 1,500, 3,000 and 6,000 kg H2/day. DWSIM duties are 49.1311, 98.2623, 196.5245 and 393.0491 kW. The independent NIST-Shomate-based estimates are 48.4812, 96.9625, 193.9249 and 387.8499 kW.

## Validation contract
A release candidate passes only when all four valid scenarios are present; solver success and zero recorded warnings are retained; absolute recorded mass-balance error is <=1e-9 kg/s; compressor duty is positive and monotonic with plant scale; DWSIM-versus-independent duty difference is <=5%; and the preserved solver-success/physics-failure case is rejected by the physical-validity gate.

## Reproducibility result
Development tests passed 6/6. A fresh Python 3.13.5 virtual environment was then created. The package was rebuilt as both sdist and wheel, the wheel was installed into that isolated environment, and the same 6/6 tests passed in 0.03 s. Running the installed module on the frozen fixture returned `validation_pass=true`, four passing scenarios, monotonic duty, successful rejection of the negative case and maximum relative duty difference 0.013405116 (1.340512%).

The rebuilt wheel is `h2bop_repro-0.1.0-py3-none-any.whl` with SHA-256 `04E40C045C81F5561FB224539B420E4D48C94B487BB4FCE7ECEF3D79DB24630E`.

## Preserved failures and limitations
The first one-command `scripts/reproduce.ps1` invocation exceeded the Windows MCP 30-second command timeout. Inspection showed that the fresh venv existed but the package had not yet been installed, so that run is recorded as failed rather than inferred successful. The same reproduction steps were then executed individually and passed. An earlier global-user installation also exposed a Windows PATH issue for the `h2bop-repro` console script; `python -m h2bop_repro.cli` remains the environment-independent documented invocation.

The repository is a shared dirty workspace with unrelated changes and an existing merge conflict, so no git tag or commit was created. The release candidate is therefore versioned at the package/artifact level only. The included GitHub Actions workflow is an unexecuted CI definition; no hosted-CI claim is made. No package or repository was published.

## Engineering interpretation
The package demonstrates that the previously validated compressor-duty reconciliation survives packaging and clean installation without changing its engineering acceptance decision. The strongest defensible claim is research-software reproducibility and validation engineering around an evidence-backed benchmark—not new process-model development or external software adoption.
