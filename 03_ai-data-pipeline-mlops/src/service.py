from __future__ import annotations

from pathlib import Path
import statistics
import time
from collections import deque

import joblib
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "artifacts" / "model.joblib"

app = FastAPI(title="AI4I Predictive Maintenance Service", version="0.2.0")
_bundle = None
_request_count = 0
_error_count = 0
_latency_ms = deque(maxlen=10000)


class PredictionRequest(BaseModel):
    type: str
    air_temperature_k: float = Field(gt=0)
    process_temperature_k: float = Field(gt=0)
    rotational_speed_rpm: float = Field(gt=0)
    torque_nm: float = Field(ge=0)
    tool_wear_min: float = Field(ge=0)

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in {"L", "M", "H"}:
            raise ValueError("type must be L, M, or H")
        return v


def get_bundle():
    global _bundle
    if _bundle is None:
        if not MODEL_PATH.exists():
            raise RuntimeError("model artifact missing; run src/pipeline.py first")
        _bundle = joblib.load(MODEL_PATH)
    return _bundle


@app.middleware("http")
async def request_metrics(request: Request, call_next):
    global _request_count, _error_count
    t0 = time.perf_counter()
    _request_count += 1
    try:
        response = await call_next(request)
        if response.status_code >= 400:
            _error_count += 1
        return response
    except Exception:
        _error_count += 1
        raise
    finally:
        _latency_ms.append((time.perf_counter() - t0) * 1000)


@app.get("/health")
def health():
    version = None
    if MODEL_PATH.exists():
        try:
            version = get_bundle().get("model_version", "unknown")
        except Exception:
            version = "unreadable"
    return {"status": "ok", "model_ready": MODEL_PATH.exists(), "version": version or "0.2.0"}


@app.get("/v1/model-info")
def model_info():
    bundle = get_bundle()
    return {
        "model_version": bundle.get("model_version", "unknown"),
        "threshold": float(bundle["threshold"]),
        "features": list(bundle["features"]),
    }


@app.post("/v1/predict")
def predict(req: PredictionRequest):
    try:
        import pandas as pd
        bundle = get_bundle()
        row = pd.DataFrame([{
            "Type": req.type,
            "Air temperature [K]": req.air_temperature_k,
            "Process temperature [K]": req.process_temperature_k,
            "Rotational speed [rpm]": req.rotational_speed_rpm,
            "Torque [Nm]": req.torque_nm,
            "Tool wear [min]": req.tool_wear_min,
        }])
        p = float(bundle["model"].predict_proba(row)[:, 1][0])
        threshold = float(bundle["threshold"])
        return {
            "model_version": bundle.get("model_version", "unknown"),
            "failure_probability": p,
            "prediction": int(p >= threshold),
            "threshold": threshold,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/metrics-summary")
def metrics_summary():
    values = list(_latency_ms)
    def pct(q: float) -> float:
        if not values:
            return 0.0
        arr = sorted(values)
        idx = min(len(arr)-1, max(0, int(round(q*(len(arr)-1)))))
        return float(arr[idx])
    return {
        "request_count": _request_count,
        "error_count": _error_count,
        "error_rate": _error_count / _request_count if _request_count else 0.0,
        "mean_latency_ms": float(statistics.mean(values)) if values else 0.0,
        "p95_latency_ms": pct(0.95),
        "p99_latency_ms": pct(0.99),
        "window_size": len(values),
    }
