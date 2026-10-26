"""Shared configuration for the ML pipeline and the serving backend.

Keeping every threshold in one place guarantees that training (`ml/train.py`)
and serving (`backend/`) use EXACTLY the same definitions, avoiding
train/serve skew.

All definitions here are demonstration choices for an academic prototype.
They are deliberately NOT presented as official epidemiological definitions.
"""

import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data")

DENGUE_DATA_CSV = os.path.join(DATA_DIR, "dengue_data.csv")
REGIONS_CSV = os.path.join(DATA_DIR, "regions.csv")
HEALTH_CENTERS_CSV = os.path.join(DATA_DIR, "health_centers.csv")
ROADS_JSON = os.path.join(DATA_DIR, "roads.json")

ARTIFACTS_DIR = os.environ.get(
    "ML_ARTIFACTS_DIR", os.path.join(REPO_ROOT, "ml", "artifacts")
)
FIGURES_DIR = os.environ.get(
    "ML_FIGURES_DIR", os.path.join(REPO_ROOT, "ml", "figures")
)

DISEASE = "Dengue"


# ── High-incidence-event label ─────────────────────────────────────────────
# The prototype uses a PROJECT-DEFINED high-incidence event as a proxy for
# outbreak risk. This is NOT an official epidemiological outbreak definition.
LABEL_COLUMN = "high_incidence_event"

LABEL_CONFIG = {
    # Weekly growth rate (vs average of the previous `growth_baseline_weeks`
    # weeks) that counts as a rapid increase.
    "growth_threshold": 0.25,
    # Weeks averaged to form the growth baseline.
    "growth_baseline_weeks": 4,
    # `cases` must be at least `case_multiplier` x the trailing regional
    # baseline to count as a high-incidence event.
    "case_multiplier": 1.5,
    # Trailing weeks used for the regional case baseline.
    "baseline_window_weeks": 8,
}

LABEL_METHODOLOGY = (
    "A region-week is labelled as a high-incidence event when (1) the weekly "
    "case growth rate (current cases vs the average of the previous "
    f"{LABEL_CONFIG['growth_baseline_weeks']} weeks) exceeds "
    f"{LABEL_CONFIG['growth_threshold']:.0%}, AND (2) weekly cases reach at "
    f"least {LABEL_CONFIG['case_multiplier']}x the trailing "
    f"{LABEL_CONFIG['baseline_window_weeks']}-week regional baseline. "
    "The model is trained to predict this event ONE WEEK IN ADVANCE: the "
    "label at week t is the high-incidence event at week t+1, and the "
    "features at week t use only information available up to week t. "
    "This project-defined high-incidence event is used as a PROXY for "
    "outbreak risk. It is NOT an official epidemiological outbreak definition."
)

# Prediction horizon: how many weeks in advance the model tries to flag an
# event. Features use only information up to week t; the label is the event
# at week t + horizon.
PREDICT_HORIZON_WEEKS = 1


# ── Risk probability bands ─────────────────────────────────────────────────
RISK_BANDS = [
    {"label": "Low", "min": 0, "max": 29, "color": "#16a34a"},
    {"label": "Moderate", "min": 30, "max": 49, "color": "#eab308"},
    {"label": "High", "min": 50, "max": 69, "color": "#f97316"},
    {"label": "Very High", "min": 70, "max": 100, "color": "#dc2626"},
]


# ── Severity classification ────────────────────────────────────────────────
SEVERITY_CONFIG = {
    # Weights applied to normalized sub-scores (each 0-1).
    "weights": {
        "probability_score": 0.25,   # from model probability
        "cases_score": 0.20,         # current cases vs regional max
        "growth_score": 0.20,        # weekly growth rate
        "death_score": 0.15,         # recent deaths
        "spread_score": 0.20,        # geographic spread (share of nearby regions at risk)
    },
    "bands": [
        {"label": "LOW", "max": 0.30},
        {"label": "MODERATE", "max": 0.55},
        {"label": "HIGH", "max": 0.80},
        {"label": "CRITICAL", "max": 1.00},
    ],
}

SEVERITY_METHODOLOGY = (
    "Severity is a project-defined weighted score (0-1) combining the model "
    "outbreak probability, current case load relative to the regional "
    "maximum, weekly case growth, recent deaths, and geographic spread "
    "(share of neighboring regions with High/Very High risk). Bands map the "
    "score to LOW / MODERATE / HIGH / CRITICAL. This is an academic "
    "demonstration, NOT a medically authoritative severity classification."
)


# ── Priority scoring ───────────────────────────────────────────────────────
PRIORITY_CONFIG = {
    "weights": {
        "probability": 0.50,   # model outbreak probability (0-1)
        "severity": 0.30,      # severity band weight (0-1)
        "population": 0.20,    # population factor (0-1, log scaled)
    },
}

SEVERITY_BAND_WEIGHTS = {"LOW": 0.10, "MODERATE": 0.35, "HIGH": 0.70, "CRITICAL": 1.00}

PRIORITY_METHODOLOGY = (
    "priority_score (%) = 100 x (0.50 x probability + 0.30 x severity_weight + "
    "0.20 x population_factor). Severity weight: LOW=0.10, MODERATE=0.35, "
    "HIGH=0.70, CRITICAL=1.00. Population factor is the region population "
    "log-scaled to 0-1. A demonstration formula for ranking resource allocation."
)

EXPLAINABILITY_METHODOLOGY = (
    "Feature attribution is computed by a perturbation sensitivity analysis: "
    "each feature is increased by one standard deviation (of the training "
    "sample) while all other features stay fixed, and the resulting change in "
    "predicted outbreak probability is reported (in percentage points). "
    "This is a demonstration-grade explanation, NOT a rigorous "
    "SHAP-style attribution."
)


# ── Training split ─────────────────────────────────────────────────────────
TRAIN_CONFIG = {
    "test_ratio": 0.20,   # last 20% of weeks per region are held out
    "random_state": 42,
    "rf_n_estimators": 200,
    "rf_max_depth": 10,
    "rf_min_samples_leaf": 3,
    "lr_max_iter": 5000,
}

WARMUP_WEEKS = 6  # rows before the first warmup window start are dropped


def risk_category(probability) -> str:
    """Map a probability (0-100) to a risk-band label."""
    probability = max(0.0, min(100.0, float(probability)))
    for band in RISK_BANDS:
        if band["min"] <= probability <= band["max"]:
            return band["label"]
    return RISK_BANDS[-1]["label"]


def severity_band(score: float) -> str:
    """Map a severity score (0-1) to a severity band label."""
    score = max(0.0, min(1.0, score))
    for band in SEVERITY_CONFIG["bands"]:
        if score <= band["max"]:
            return band["label"]
    return "CRITICAL"