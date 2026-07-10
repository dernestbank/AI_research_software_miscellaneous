from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pipeline
import service
from monitoring import monitor_batch


@pytest.fixture(scope="session")
def trained_result():
    return pipeline.run_pipeline()


@pytest.fixture(scope="session")
def source_df():
    return pipeline.load_source()


def test_authoritative_source_contract(source_df):
    assert len(source_df) == 10000
    assert int(source_df[pipeline.TARGET].sum()) == 339
    assert pipeline.sha256(pipeline.RAW_CSV) == "DC6630CD9B1F0F853922FAD78A1B6436570D3F1EC863F1DD5C4340AC56BC8A8E"


def test_frozen_split(source_df):
    train, val, test = pipeline.split_frame(source_df)
    assert (len(train), len(val), len(test)) == (7000, 1500, 1500)
    assert train["UDI"].max() == 7000
    assert val["UDI"].min() == 7001 and val["UDI"].max() == 8500
    assert test["UDI"].min() == 8501


def test_missing_column_rejected(source_df):
    df = source_df.drop(columns=["Torque [Nm]"])
    with pytest.raises(ValueError, match="missing required columns"):
        pipeline.validate_frame(df)


def test_missing_value_rejected(source_df):
    df = source_df.copy()
    df.loc[0, "Torque [Nm]"] = np.nan
    with pytest.raises(ValueError, match="missing value"):
        pipeline.validate_frame(df)


def test_invalid_target_rejected(source_df):
    df = source_df.copy()
    df.loc[0, pipeline.TARGET] = 2
    with pytest.raises(ValueError, match="target must be binary"):
        pipeline.validate_frame(df)


def test_unknown_type_rejected(source_df):
    df = source_df.copy()
    df.loc[0, "Type"] = "X"
    with pytest.raises(ValueError, match="unsupported category"):
        pipeline.validate_frame(df)


def test_pipeline_outputs_and_metrics(trained_result):
    result = trained_result
    assert result["source_rows"] == 10000
    assert result["test"]["roc_auc"] >= 0.90
    assert result["test"]["average_precision"] > result["test"]["prevalence"] * 10
    assert result["test"]["recall"] >= 0.50
    assert result["test"]["f1"] >= 0.60
    assert pipeline.MODEL_PATH.exists()
    assert pipeline.METRICS_PATH.exists()
    assert pipeline.PIPELINE_MANIFEST_PATH.exists()


def test_model_beats_constant_baseline(trained_result):
    baseline = json.loads((ROOT / "artifacts" / "baseline_benchmark.json").read_text())
    assert trained_result["test"]["roc_auc"] > baseline["roc_auc"] + 0.30
    assert trained_result["test"]["average_precision"] > baseline["average_precision"] * 20
    assert trained_result["test"]["brier"] < baseline["brier"]


def test_monitoring_detects_chronological_shift(source_df):
    train, _, test = pipeline.split_frame(source_df)
    snap = monitor_batch(train[pipeline.FEATURES], test[pipeline.FEATURES])
    assert snap["status"] == "ALERT"
    assert snap["max_numeric_psi"] > 0.25
    assert snap["max_numeric_psi_feature"] == "Air temperature [K]"
    assert snap["missing_feature_cells"] == 0


def test_api_health_prediction_validation_and_metrics(trained_result):
    service._bundle = None
    client = TestClient(service.app)

    h = client.get("/health")
    assert h.status_code == 200 and h.json()["model_ready"] is True
    assert h.json()["version"] == pipeline.MODEL_VERSION

    info = client.get("/v1/model-info")
    assert info.status_code == 200
    assert info.json()["model_version"] == pipeline.MODEL_VERSION
    assert info.json()["features"] == pipeline.FEATURES

    good = client.post("/v1/predict", json={
        "type": "L",
        "air_temperature_k": 300.0,
        "process_temperature_k": 310.0,
        "rotational_speed_rpm": 1500,
        "torque_nm": 40,
        "tool_wear_min": 100,
    })
    assert good.status_code == 200
    assert 0 <= good.json()["failure_probability"] <= 1

    bad = client.post("/v1/predict", json={
        "type": "X",
        "air_temperature_k": 300.0,
        "process_temperature_k": 310.0,
        "rotational_speed_rpm": 1500,
        "torque_nm": 40,
        "tool_wear_min": 100,
    })
    assert bad.status_code == 422

    metrics = client.get("/metrics-summary")
    assert metrics.status_code == 200
    m = metrics.json()
    assert m["request_count"] >= 5
    assert m["error_count"] >= 1
    assert 0 < m["error_rate"] < 1
    assert m["p95_latency_ms"] >= 0


def test_idempotency_artifact_passed():
    p = ROOT / "artifacts" / "idempotency_check.json"
    assert p.exists()
    d = json.loads(p.read_text())
    assert d["all_deterministic_hashes_match"] is True
    assert all(d["checks"].values())
