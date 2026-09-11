"""Regions, health centers and priority ranking endpoints."""

from fastapi import APIRouter, Depends

from .. import database
from ..db_conn import get_db
from ..schemas import HealthCenterOut, RegionOut

router = APIRouter(prefix="/api", tags=["regions"])


@router.get("/regions", response_model=list[RegionOut])
def list_regions(conn=Depends(get_db)):
    return [dict(r) for r in database.get_regions(conn)]


@router.get("/regions/priority")
def priority_ranking(conn=Depends(get_db)):
    """Regions ranked by priority score for the latest assessment date."""
    rows = conn.execute(
        """SELECT r.id, r.name, r.latitude, r.longitude, r.population,
                  ra.assessment_date, ra.severity, ra.severity_score,
                  ra.priority_score, ra.factors,
                  p.outbreak_probability, p.risk_category
           FROM regions r
           JOIN risk_assessments ra ON ra.region_id = r.id
           JOIN predictions p ON p.region_id = r.id
                AND p.prediction_date = ra.assessment_date
                AND p.model_name = 'Random Forest (serving)'
           ORDER BY ra.priority_score DESC, r.name""",
    ).fetchall()
    return [dict(r) for r in rows]


@router.get("/regions/{region_id}", response_model=RegionOut)
def get_region(region_id: int, conn=Depends(get_db)):
    return dict(database.region_row(conn, region_id))


@router.get("/health-centers", response_model=list[HealthCenterOut])
def list_health_centers(conn=Depends(get_db)):
    return [dict(r) for r in database.get_health_centers(conn)]