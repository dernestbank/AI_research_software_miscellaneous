from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "workflow_run.json"

TASKS = [
    ("fetch_data", [sys.executable, "scripts/fetch_data.py"], 2),
    ("baseline", [sys.executable, "src/benchmark.py"], 1),
    ("train_version", [sys.executable, "src/pipeline.py"], 1),
    ("monitor", [sys.executable, "src/monitoring.py"], 1),
    ("idempotency", [sys.executable, "scripts/check_idempotency.py"], 1),
    ("tests", [sys.executable, "-m", "pytest", "tests", "-q"], 1),
    ("release_build", [sys.executable, "scripts/build_release.py"], 1),
    ("release_verify", [sys.executable, "scripts/verify_release.py"], 1),
]


def run_task(name: str, cmd: list[str], attempts: int):
    last = None
    for attempt in range(1, attempts + 1):
        t0 = time.perf_counter()
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        elapsed = time.perf_counter() - t0
        last = {
            "name": name,
            "attempt": attempt,
            "max_attempts": attempts,
            "returncode": p.returncode,
            "duration_s": elapsed,
            "stdout_tail": p.stdout[-2000:],
            "stderr_tail": p.stderr[-2000:],
        }
        if p.returncode == 0:
            return last
        if attempt < attempts:
            time.sleep(1.0)
    return last


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stop-after", choices=[t[0] for t in TASKS])
    args = parser.parse_args()

    records = []
    status = "PASSED"
    for name, cmd, attempts in TASKS:
        rec = run_task(name, cmd, attempts)
        records.append(rec)
        if rec["returncode"] != 0:
            status = "FAILED"
            break
        if args.stop_after == name:
            break

    result = {
        "workflow": "local evidence pipeline",
        "status": status,
        "tasks": records,
        "completed_tasks": [r["name"] for r in records if r["returncode"] == 0],
        "boundary": "local Python orchestration; no Airflow/Prefect/cloud orchestrator claim",
    }
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if status == "PASSED" else 1)


if __name__ == "__main__":
    main()
