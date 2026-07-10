from pathlib import Path
import sys

import pandas as pd
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pipeline
from service import PredictionRequest, predict, health

checks = []

def check(name, condition):
    if not condition:
        raise AssertionError(name)
    checks.append(name)

result = pipeline.run_pipeline()
check("authoritative_rows", result["source_rows"] == 10000)
check("frozen_split", result["split_rows"] == {"train": 7000, "validation": 1500, "test": 1500})
check("test_discrimination", result["test"]["roc_auc"] >= 0.70 and result["test"]["average_precision"] > result["test"]["prevalence"])
check("test_failure_detection", result["test"]["confusion_matrix"]["tp"] > 0 and result["test"]["recall"] >= 0.50)

frame = pipeline.load_source()
broken = frame.drop(columns=["Torque [Nm]"])
try:
    pipeline.validate_frame(broken)
    raise AssertionError("missing_column_rejection")
except ValueError:
    checks.append("missing_column_rejection")

broken = frame.copy()
broken.loc[0, pipeline.TARGET] = 2
try:
    pipeline.validate_frame(broken)
    raise AssertionError("invalid_target_rejection")
except ValueError:
    checks.append("invalid_target_rejection")

try:
    PredictionRequest(type="X", air_temperature_k=300, process_temperature_k=310, rotational_speed_rpm=1500, torque_nm=40, tool_wear_min=100)
    raise AssertionError("api_schema_rejection")
except ValidationError:
    checks.append("api_schema_rejection")

req = PredictionRequest(type="L", air_temperature_k=300, process_temperature_k=310, rotational_speed_rpm=1500, torque_nm=40, tool_wear_min=100)
response = predict(req)
check("api_prediction", 0.0 <= response["failure_probability"] <= 1.0 and response["model_version"] == "0.1.0")
check("api_health", health()["model_ready"] is True)

print(f"VALIDATION_PASS {len(checks)}/{len(checks)}")
for name in checks:
    print(name)
