from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline import (
    ARTIFACTS,
    FEATURES,
    NUMERIC,
    RAW_CSV,
    TARGET,
    load_source,
    population_stability_index,
    split_frame,
    validate_inference_frame,
)

MONITOR_PATH = ARTIFACTS / "monitoring_snapshot.json"


def categorical_total_variation(reference: pd.Series, current: pd.Series) -> float:
