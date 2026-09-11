"""Prediction and risk-assessment endpoints (read from the persisted pipeline)."""

from fastapi import APIRouter, Depends, HTTPException, Query

from .. import config, database
from ..db_conn import get_db
from ..services.deps import get_model_service
from ..services.explainability import Explainer
from ..schemas import PredictionOut

router = APIRouter(prefix="/api", tags=["predictions"])


@router.get("/predictions", response_model=list[PredictionOut])
def latest_predictions(conn=Depends(get_db)):
    rows = conn.execute(
        """SELECT r.id AS region_id, r.name AS region,
                  p.observation_date, p.prediction_date,
                  p.outbreak_probability AS probability,
                  p.risk_category,
                  ra.severity AS severity_band,
                  ra.severity_score, ra.priority_score
           FROM predictions p
           JOIN regions r ON r.id = p.region_id
           LEFT JOIN risk_assessments ra ON ra.region_id = p.region_id
                AND ra.assessment_date = p.prediction_date
           WHERE p.model_name = 'Random Forest (serving)'
           ORDER BY p.outbreak_probability DESC, r.name""",
    ).fetchall()
    out = []
    for row in rows:
        d = dict(row)
        d["region_name"] = row["region"]
        d["probability_lr"] = _lr_probability(conn, row["region_id"], row["prediction_date"])
        d["risk_category"] = config.risk_category(float(d["probability"]) * 100)
        out.append(d)
    return out


def _lr_probability(conn, region_id: int, prediction_date: str) -> float:
    row = conn.execute(
        """SELECT outbreak_probability FROM predictions
           WHERE region_id = ? AND prediction_date = ?
             AND model_name = 'Logistic Regression (baseline)'""",
        (region_id, prediction_date),
    ).fetchone()
    return row["outbreak_probability"] if row else 0.0


@router.get("/predictions/{region_id}")
def region_prediction_detail(
    region_id: int,
    explain: bool = Query(True, description="include feature-level attributions"),
    conn=Depends(get_db),
    model_service=Depends(get_model_service),
):
    region = database.region_row(conn, region_id)
    row = conn.execute(
        """SELECT p.*, ra.severity, ra.severity_score, ra.priority_score, ra.factors
           FROM predictions p
           LEFT JOIN risk_assessments ra ON ra.region_id = p.region_id
                AND ra.assessment_date = p.prediction_date
           WHERE p.region_id = ? AND p.model_name = 'Random Forest (serving)'
           ORDER BY p.prediction_date DESC LIMIT 1""",
        (region_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="No prediction for this region")

    detail = {
        "region_id": region_id,
        "region_name": region["name"],
        "latitude": region["latitude"],
        "longitude": region["longitude"],
        "population": region["population"],
        "observation_date": row["observation_date"],
        "prediction_date": row["prediction_date"],
        "probability": row["outbreak_probability"],
        "risk_category": row["risk_category"],
        "severity_band": row["severity"],
        "severity_score": row["severity_score"],
        "priority_score": row["priority_score"],
        "severity_factors": (dict(__import__("json").loads(row["factors"])) if row["factors"] else {}),
        "label_methodology": config.LABEL_METHODOLOGY,
        "severity_methodology": config.SEVERITY_METHODOLOGY,
        "priority_methodology": config.PRIORITY_METHODOLOGY,
        "demo_data_disclaimer": config.DEMO_DATA_DISCLAIMER,
    }
    if explain:
        detail["explainability"] = Explainer(model_service).explain(region["name"])
    return detail


@router.get("/risk-assessments")
def risk_assessments(conn=Depends(get_db)):
    rows = conn.execute(
        """SELECT r.id AS region_id, r.name, ra.assessment_date, ra.severity,
                  ra.severity_score, ra.priority_score, ra.factors
           FROM risk_assessments ra JOIN regions r ON r.id = ra.region_id
           ORDER BY ra.priority_score DESC, r.name""",
    ).fetchall()
    return [dict(r) for r in rows]


@router.get("/regions/{region_id}/history")
def region_history(
    region_id: int,
    limit: int = Query(52, ge=8, le=500),
    conn=Depends(get_db),
):
    """Weekly observations for a region (for charts), most recent first."""
    database.region_row(conn, region_id)
    rows = conn.execute(
        """SELECT o.date, o.reported_cases, o.previous_week_cases, o.previous_month_cases,
                  o.deaths, o.temperature, o.rainfall, o.humidity,
                  o.water_accumulation_index
           FROM disease_observations o
           WHERE o.region_id = ?
           ORDER BY o.date DESC LIMIT ?""",
        (region_id, limit),
    ).fetchall()
    out = [dict(r) for r in rows]
    out.reverse()
    return {"region_id": region_id, "history": out}


@router.get("/timeseries/cases")
def cases_timeseries(conn=Depends(get_db)):
    """Aggregate reported cases per week across all regions (national view)."""
    rows = conn.execute(
        """SELECT date, SUM(reported_cases) AS total_cases, SUM(deaths) AS total_deaths
           FROM disease_observations GROUP BY date ORDER BY date""",
    ).fetchall()
    return [dict(r) for r in rows]


@router.get("/dataset-rows")
def dataset_rows(
    limit: int = Query(15, ge=1, le=500),
    conn=Depends(get_db),
):
    """Latest observation rows joined with region name (for the /data page)."""
    rows = conn.execute(
        """SELECT o.date, r.name AS region, o.reported_cases, o.previous_week_cases,
                  o.deaths, o.temperature, o.rainfall, o.humidity,
                  o.water_accumulation_index, o.population_density
           FROM disease_observations o JOIN regions r ON r.id = o.region_id
           ORDER BY o.date DESC, r.name LIMIT ?""",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]