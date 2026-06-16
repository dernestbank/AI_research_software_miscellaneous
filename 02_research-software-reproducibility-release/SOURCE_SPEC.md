# SOURCE_SPEC — Research Software Reproducibility Release

## Scientific fixture
This project packages an immutable copy of the already validated Green-H2 compressor reconciliation from `01_Process_Engineering/09_dwsim-mcp`. It does not rerun or reinterpret DWSIM as a new scientific result.

## Inputs
- `data/dwsim_green_h2_benchmark.json` — copied benchmark fixture derived from the validated DWSIM-MCP evidence package.
- Four valid production-scale scenarios: 750, 1500, 3000 and 6000 kg H2/day.
- One deliberately invalid solver-success compressor case retained as a negative physics control.

## Provenance
Upstream simulation evidence was generated with DWSIM 10.2.3 and the official DWSIM 10.2 MCP image. Independent compressor-duty reconciliation used public NIST Chemistry WebBook gaseous-H2 Shomate coefficients. Full upstream provenance remains in `01_Process_Engineering/09_dwsim-mcp/references/SOURCES.md` and `EVIDENCE.md`.

## Data classes
- Public reference data: NIST hydrogen heat-capacity coefficients used upstream.
- Third-party software outputs: DWSIM simulation values used upstream.
- Local validated evidence: copied benchmark fixture in this package.
- Synthetic/test data: malformed or modified fixtures used only by negative tests.

## Units
- Hydrogen production: kg/day
- Compressor duty: kW
- Mass-balance error: kg/s
- Pressure: bar

## Acceptance criteria
1. Four valid scenarios are present.
2. Each valid scenario reports solver success, zero recorded warnings, absolute mass-balance error <=1e-9 kg/s and positive compressor duty.
3. DWSIM-vs-independent duty difference is <=5% for each valid scenario.
4. Compressor duty increases monotonically with production rate.
5. The preserved negative case must be rejected by a physics gate even if solver success is true.
6. The package must reproduce these checks after installation in a fresh isolated environment.

## Exclusions
- No claim of full electrolyzer-plant simulation.
- No claim of external adoption, package downloads, production deployment or community maintenance.
- No claim that this package generated the upstream DWSIM results.
