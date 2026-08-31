param(
  [string]$Python = "python"
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Venv = Join-Path $Root ".repro-venv"
if (Test-Path $Venv) { Remove-Item -Recurse -Force $Venv }
& $Python -m venv $Venv
$Py = Join-Path $Venv "Scripts\python.exe"
& $Py -m pip install --upgrade pip
& $Py -m pip install build pytest
& $Py -m build $Root
$Wheel = Get-ChildItem (Join-Path $Root "dist\h2bop_repro-0.1.0-py3-none-any.whl") | Select-Object -First 1
& $Py -m pip install --force-reinstall $Wheel.FullName
& $Py -m pytest (Join-Path $Root "tests") -q
& $Py -m h2bop_repro.cli (Join-Path $Root "data\dwsim_green_h2_benchmark.json") --json
if ($LASTEXITCODE -ne 0) { throw "Reproduction failed with exit code $LASTEXITCODE" }
Write-Host "REPRODUCTION_PASS"
