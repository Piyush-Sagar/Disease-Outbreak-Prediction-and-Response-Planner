"""Dashboard summary + alerts."""

from fastapi import APIRouter, Depends

from .. import database
from ..db_conn import get_db
from ..services.alerts import build_alerts

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard/summary")
def dashboard_summary(conn=Depends(get_db)):
    preds = conn.execute(
        """SELECT p.*, r.name, ra.severity FROM predictions p
           JOIN regions r ON r.id = p.region_id
           LEFT JOIN risk_assessments ra ON ra.region_id = p.region_id
                AND ra.assessment_date = p.prediction_date
           WHERE p.model_name = 'Random Forest (serving)'""",
    ).fetchall()
    obs_date = database.latest_observation_date(conn)
    total_cases = conn.execute(
        "SELECT SUM(reported_cases) AS t FROM disease_observations WHERE date = "
        "(SELECT MAX(date) FROM disease_observations)"
    ).fetchone()["t"]
    total_deaths = conn.execute(
        "SELECT SUM(deaths) AS t FROM disease_observations WHERE date = "
        "(SELECT MAX(date) FROM disease_observations)"
    ).fetchone()["t"]
    avg_prob = sum(p["outbreak_probability"] for p in preds) / len(preds) if preds else 0.0
    critical_alerts = []
    for p in preds:
        critical_alerts.extend(build_alerts(p["name"], p["outbreak_probability"], p["severity"] or "LOW"))
    critical_alerts = [a for a in critical_alerts if a["level"] == "critical"]
    return {
        "as_of_date": obs_date,
        "regions_count": len(preds),
        "high_risk_regions": sum(1 for p in preds if p["outbreak_probability"] >= 0.50),
        "critical_regions": sum(1 for p in preds if p["severity"] == "CRITICAL"),
        "latest_week_cases": total_cases,
        "latest_week_deaths": total_deaths,
        "avg_probability": round(avg_prob, 4),
        "alerts_count": len(critical_alerts),
        "demo_data_disclaimer": "DEMO DATA - NOT FOR REAL-WORLD HEALTHCARE DECISIONS",
    }