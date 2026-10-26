"""Model, dataset and alert endpoints."""

import csv
import json
import os

from fastapi import APIRouter, Depends

from .. import config
from ..db_conn import get_db
from ..services.alerts import build_alerts

router = APIRouter(prefix="/api", tags=["model", "dataset"])


def _read_json(path: str):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _read_csv_rows(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


@router.get("/model-performance")
def model_performance():
    metrics = _read_json(os.path.join(config.MODEL_ARTIFACTS_DIR, "metrics.json")) or {}
    metadata = _read_json(os.path.join(config.MODEL_ARTIFACTS_DIR, "metadata.json")) or {}
    importance = _read_csv_rows(os.path.join(config.MODEL_ARTIFACTS_DIR, "feature_importance.csv"))
    figures = []
    if os.path.isdir(config.MODEL_FIGURES_DIR):
        for name in sorted(os.listdir(config.MODEL_FIGURES_DIR)):
            if name.endswith(".png"):
                figures.append(f"/static/figures/{name}")
    return {
        "metrics": metrics,
        "metadata": metadata,
        "feature_importance": importance,
        "figures": figures,
        "label_methodology": config.LABEL_METHODOLOGY,
        "severity_methodology": config.SEVERITY_METHODOLOGY,
        "priority_methodology": config.PRIORITY_METHODOLOGY,
        "explainability_methodology": config.EXPLAINABILITY_METHODOLOGY,
        "risk_bands": config.RISK_BANDS,
    }


@router.get("/dataset-info")
def dataset_info(conn=Depends(get_db)):
    obs_row = conn.execute(
        "SELECT COUNT(*) AS n, COUNT(DISTINCT region_id) AS regions, "
        "MIN(date) AS first, MAX(date) AS last FROM disease_observations"
    ).fetchone()
    total_cases = conn.execute(
        "SELECT SUM(reported_cases) AS t FROM disease_observations"
    ).fetchone()["t"]
    return {
        "disease": config.DISEASE,
        "demo_data_disclaimer": config.DEMO_DATA_DISCLAIMER,
        "label_methodology": config.LABEL_METHODOLOGY,
        "observations": obs_row["n"],
        "regions": obs_row["regions"],
        "date_range": {"first": obs_row["first"], "last": obs_row["last"]},
        "total_cases": total_cases,
        "source_files": [
            "data/dengue_data.csv",
            "data/regions.csv",
            "data/health_centers.csv",
            "data/roads.json",
        ],
        "synthetic_notice": (
            "All data in this prototype is taken from respective portals."
        ),
    }


@router.get("/alerts")
def alerts(conn=Depends(get_db)):
    rows = conn.execute(
        """SELECT r.name, p.outbreak_probability, ra.severity
           FROM predictions p
           JOIN regions r ON r.id = p.region_id
           LEFT JOIN risk_assessments ra ON ra.region_id = p.region_id
                AND ra.assessment_date = p.prediction_date
           WHERE p.model_name = 'Random Forest (serving)'""",
    ).fetchall()
    items = []
    for row in rows:
        items.extend(build_alerts(row["name"], row["outbreak_probability"], row["severity"] or "LOW"))
    ordering = {"critical": 0, "high": 1}
    items.sort(key=lambda a: (ordering.get(a["level"], 9), -a["probability"]))
    return items