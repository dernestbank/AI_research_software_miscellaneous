# User Tutorial

## Purpose
Validate the frozen Green-H2 compressor benchmark without requiring DWSIM at runtime. The package checks whether a previously validated DWSIM result set still satisfies explicit engineering and reproducibility gates.

## Development run
```powershell
python -m pytest tests -q
python -m h2bop_repro.cli data/dwsim_green_h2_benchmark.json --json
```

## Clean reproduction
```powershell
powershell -ExecutionPolicy Bypass -File scripts/reproduce.ps1
```
The script creates a fresh `.repro-venv`, builds the wheel, installs it, reruns tests and invokes the installed module on the frozen fixture.

## Interpretation
A passing result requires four valid scenarios, <=5% DWSIM-vs-independent duty difference, mass-balance closure, monotonic duty scaling, and rejection of the solver-success/physics-failure control.

## Boundary
This package validates a frozen benchmark. It does not rerun DWSIM and does not claim a full hydrogen facility design.
