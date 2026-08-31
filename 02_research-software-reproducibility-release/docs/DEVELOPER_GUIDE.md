# Developer Guide

Preserve the benchmark fixture unless provenance and upstream evidence are intentionally versioned. Add a test for each behavior change. Never relax a physics or reconciliation gate solely to make a fixture pass.

Before a release candidate, run the test suite, build the wheel, install it into a clean environment, and run the benchmark CLI. Update `pyproject.toml`, `CHANGELOG.md`, and `CITATION.cff` when versioning changes. Record wheel hashes and changed validation results. External publication requires explicit authorization.
