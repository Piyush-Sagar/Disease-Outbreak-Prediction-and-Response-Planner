"""Response-recommendation endpoint."""

from fastapi import APIRouter, Depends, HTTPException

from .. import database
from ..db_conn import get_db

router = APIRouter(prefix="/api", tags=["recommendations"])


@router.get("/recommendations/{region_id}")
def recommendations_for_region(region_id: int, conn=Depends(get_db)):
    database.region_row(conn, region_id)  # 404 if missing
    rows = conn.execute(
        """SELECT action, reason, source_rule, recommendation_date as date
           FROM response_recommendations
           WHERE region_id = ?
           ORDER BY rowid""",
        (region_id,),
    ).fetchall()
    return [dict(r) for r in rows]


@router.get("/recommendations")
def all_recommendations(conn=Depends(get_db)):
    rows = conn.execute(
        """SELECT r.name AS region, rec.action, rec.reason,
                  rec.recommendation_date AS date
           FROM response_recommendations rec
           JOIN regions r ON r.id = rec.region_id
           ORDER BY rec.recommendation_date DESC, r.name, rec.rowid""",
    ).fetchall()
    return [dict(r) for r in rows]