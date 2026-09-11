"""Backend configuration.

Settings resolve from environment variables (with sensible demo defaults)
and reuse the same threshold definitions as `ml/config.py` to guarantee the
served predictions use identical methodology to training.
"""

import os

from ml import config as ml_config
from ml.config import (
    EXPLAINABILITY_METHODOLOGY,
    LABEL_METHODOLOGY,
    PRIORITY_METHODOLOGY,
    SEVERITY_METHODOLOGY,
    risk_category,
    severity_band,
)
from ml.features import FEATURE_COLUMNS

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(BACKEND_DIR)

DEMO_MODE = os.environ.get("DEMO_MODE", "true").lower() == "true"
API_HOST = os.environ.get("API_HOST", "127.0.0.1")
API_PORT = int(os.environ.get("API_PORT", "8000"))

DATABASE_PATH = os.environ.get("DATABASE_PATH", os.path.join(BACKEND_DIR, "demo.db"))
MODEL_ARTIFACTS_DIR = os.environ.get("ML_ARTIFACTS_DIR", ml_config.ARTIFACTS_DIR)
MODEL_FIGURES_DIR = os.environ.get("ML_FIGURES_DIR", ml_config.FIGURES_DIR)

# Thresholds reused from the ML config (single source of truth).
RISK_BANDS = ml_config.RISK_BANDS
SEVERITY_CONFIG = ml_config.SEVERITY_CONFIG
PRIORITY_CONFIG = ml_config.PRIORITY_CONFIG
SEVERITY_BAND_WEIGHTS = ml_config.SEVERITY_BAND_WEIGHTS
LABEL_CONFIG = ml_config.LABEL_CONFIG
PREDICT_HORIZON_WEEKS = ml_config.PREDICT_HORIZON_WEEKS
DISEASE = ml_config.DISEASE
DEMO_DATA_DISCLAIMER = ml_config.DEMO_DATA_DISCLAIMER

# Response-planner rules (severity/risk -> recommended actions).
# Each action may carry a template reason populated with live values later.
RESPONSE_RULES = [
    {
        "id": "low-s1",
        "min_severity": "LOW",
        "action": "Continue routine surveillance",
        "reason_template": "Low predicted risk ({risk}%) - maintaining routine surveillance.",
    },
    {
        "id": "low-s2",
        "min_severity": "LOW",
        "action": "Monitor environmental conditions",
        "reason_template": "Environmental monitoring is routine during low-risk periods.",
    },
    {
        "id": "mod-s1",
        "min_severity": "MODERATE",
        "action": "Increase monitoring frequency",
        "reason_template": "Moderate predicted risk ({risk}%) warrants more frequent monitoring.",
    },
    {
        "id": "mod-s2",
        "min_severity": "MODERATE",
        "action": "Inspect potential breeding areas",
        "reason_template": "Alert conditions ({risk}% risk) may support Aedes breeding; inspect stagnant water sites.",
    },
    {
        "id": "mod-s3",
        "min_severity": "MODERATE",
        "action": "Increase public awareness",
        "reason_template": "Moderate risk ({risk}%) - raise community awareness to reduce transmission.",
    },
    {
        "id": "high-s1",
        "min_severity": "HIGH",
        "action": "Deploy additional health workers",
        "reason_template": "High predicted risk ({risk}%) with elevated severity ({severity}) requires extra field staff.",
    },
    {
        "id": "high-s2",
        "min_severity": "HIGH",
        "action": "Prioritize testing and surveillance",
        "reason_template": "Cases are rising ({growth}% weekly growth) - prioritize testing capacity.",
    },
    {
        "id": "high-s3",
        "min_severity": "HIGH",
        "action": "Inspect high-risk locations",
        "reason_template": "High predicted risk ({risk}%) - focus on high-risk wards and breeding hotspots.",
    },
    {
        "id": "high-s4",
        "min_severity": "HIGH",
        "action": "Monitor neighboring regions",
        "reason_template": "High regional incidence ({cases} weekly cases) may spread to nearby areas.",
    },
    {
        "id": "crit-s1",
        "min_severity": "CRITICAL",
        "action": "Immediate field response",
        "reason_template": "CRITICAL severity ({severity}, {risk}% risk) - initiate immediate field response.",
    },
    {
        "id": "crit-s2",
        "min_severity": "CRITICAL",
        "action": "Prioritize health-worker deployment",
        "reason_template": "CRITICAL situation ({risk}% probability, {cases} cases) - prioritize deployment.",
    },
    {
        "id": "crit-s3",
        "min_severity": "CRITICAL",
        "action": "Coordinate emergency response resources",
        "reason_template": "CRITICAL severity with {deaths} recent deaths requires coordinated emergency resources.",
    },
    {
        "id": "crit-s4",
        "min_severity": "CRITICAL",
        "action": "Increase surveillance and testing across all wards",
        "reason_template": "CRITICAL severity - expand surveillance and testing across all wards.",
    },
]


def should_demo_watermark() -> bool:
    return DEMO_MODE