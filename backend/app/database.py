"""SQLite persistence layer.

Schema + idempotent seed from the generated demo CSVs (`data/*.csv`).

SQLite is used via the standard library to keep the demo dependency-light.
"""

import csv
import os
import sqlite3
from typing import Iterable

from fastapi import HTTPException

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS regions (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    population INTEGER NOT NULL,
    population_density REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS health_centers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    region_id INTEGER REFERENCES regions(id),
    latitude REAL NOT NULL,
    longitude REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS disease_observations (
    id INTEGER PRIMARY KEY,
    region_id INTEGER NOT NULL REFERENCES regions(id),
    date TEXT NOT NULL,
    reported_cases INTEGER NOT NULL,
    previous_week_cases INTEGER,
    previous_month_cases INTEGER,
    deaths INTEGER DEFAULT 0,
    temperature REAL,
    rainfall REAL,
    humidity REAL,
    water_accumulation_index REAL,
    population_density REAL,
    UNIQUE (region_id, date)
);

CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY,
    region_id INTEGER NOT NULL REFERENCES regions(id),
    observation_date TEXT NOT NULL,
    prediction_date TEXT NOT NULL,
    outbreak_probability REAL NOT NULL,
    risk_category TEXT NOT NULL,
    model_name TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (region_id, prediction_date, model_name)
);

CREATE TABLE IF NOT EXISTS risk_assessments (
    id INTEGER PRIMARY KEY,
    region_id INTEGER NOT NULL REFERENCES regions(id),
    assessment_date TEXT NOT NULL,
    severity TEXT NOT NULL,
    severity_score REAL NOT NULL,
    priority_score REAL NOT NULL,
    factors TEXT,
    UNIQUE (region_id, assessment_date)
);

CREATE TABLE IF NOT EXISTS response_recommendations (
    id INTEGER PRIMARY KEY,
    region_id INTEGER NOT NULL REFERENCES regions(id),
    recommendation_date TEXT NOT NULL,
    action TEXT NOT NULL,
    reason TEXT NOT NULL,
    source_rule TEXT,
    UNIQUE (region_id, recommendation_date, action)
);
"""


def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    """Open a connection with row access by column name and FK enforcement."""
    conn = sqlite3.connect(db_path or config.DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: str | None = None) -> None:
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def _read_csv(filename: str) -> list[dict]:
    path = os.path.join(config.REPO_ROOT, "data", filename)
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def seed_database(db_path: str | None = None) -> dict:
    """Idempotently load regions, health centers and observations from CSVs."""
    init_db(db_path)
    conn = get_connection(db_path)
    counts = {"regions": 0, "health_centers": 0, "observations": 0}
    try:
        rows = _read_csv("regions.csv")
        for row in rows:
            cur = conn.execute(
                """INSERT OR IGNORE INTO regions
                   (id, name, latitude, longitude, population, population_density)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    int(row["id"]),
                    row["name"],
                    float(row["latitude"]),
                    float(row["longitude"]),
                    int(row["population"]),
                    float(row["population_density"]),
                ),
            )
            counts["regions"] += cur.rowcount

        rows = _read_csv("health_centers.csv")
        for row in rows:
            cur = conn.execute(
                """INSERT OR IGNORE INTO health_centers
                   (id, name, region_id, latitude, longitude)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    int(row["id"]),
                    row["name"],
                    int(row["region_id"]),
                    float(row["latitude"]),
                    float(row["longitude"]),
                ),
            )
            counts["health_centers"] += cur.rowcount

        name_to_id = {
            r["name"]: r["id"] for r in conn.execute("SELECT id, name FROM regions").fetchall()
        }
        rows = _read_csv("dengue_data.csv")
        for row in rows:
            region_id = name_to_id.get(row["region"])
            if region_id is None:
                continue
            cur = conn.execute(
                """INSERT OR IGNORE INTO disease_observations
                   (region_id, date, reported_cases, previous_week_cases,
                    previous_month_cases, deaths, temperature, rainfall,
                    humidity, water_accumulation_index, population_density)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    int(region_id),
                    row["date"],
                    int(row["reported_cases"]),
                    int(float(row["previous_week_cases"])),
                    int(float(row["previous_month_cases"])),
                    int(row["deaths"]),
                    float(row["temperature"]),
                    float(row["rainfall"]),
                    float(row["humidity"]),
                    float(row["water_accumulation_index"]),
                    float(row["population_density"]),
                ),
            )
            counts["observations"] += cur.rowcount

        conn.commit()
    finally:
        conn.close()
    return counts


def get_regions(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT id, name, latitude, longitude, population, population_density "
        "FROM regions ORDER BY name"
    ).fetchall()


def get_health_centers(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT id, name, region_id, latitude, longitude FROM health_centers ORDER BY name"
    ).fetchall()


def latest_observation_date(conn: sqlite3.Connection) -> str | None:
    row = conn.execute("SELECT MAX(date) AS d FROM disease_observations").fetchone()
    return row["d"] if row else None


def get_observations(
    conn: sqlite3.Connection,
    region_id: int | None = None,
    limit: int | None = None,
) -> list[sqlite3.Row]:
    sql = (
        "SELECT o.*, r.name AS region_name, r.latitude, r.longitude, r.population "
        "FROM disease_observations o JOIN regions r ON r.id = o.region_id"
    )
    params: list = []
    if region_id is not None:
        sql += " WHERE o.region_id = ?"
        params.append(region_id)
    sql += " ORDER BY o.date"
    if limit is not None:
        sql += " LIMIT ?"
        params.append(limit)
    return conn.execute(sql, params).fetchall()


def region_row(conn: sqlite3.Connection, region_id: int) -> sqlite3.Row:
    row = conn.execute(
        "SELECT id, name, latitude, longitude, population, population_density "
        "FROM regions WHERE id = ?",
        (region_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Region {region_id} not found")
    return row


def upsert_prediction(
    conn: sqlite3.Connection,
    region_id: int,
    observation_date: str,
    prediction_date: str,
    probability: float,
    risk_category: str,
    model_name: str,
) -> None:
    conn.execute(
        """INSERT INTO predictions
           (region_id, observation_date, prediction_date, outbreak_probability,
            risk_category, model_name)
           VALUES (?, ?, ?, ?, ?, ?)
           ON CONFLICT (region_id, prediction_date, model_name)
           DO UPDATE SET outbreak_probability = excluded.outbreak_probability,
                         risk_category = excluded.risk_category,
                         observation_date = excluded.observation_date""",
        (region_id, observation_date, prediction_date, probability, risk_category, model_name),
    )


def upsert_risk_assessment(
    conn: sqlite3.Connection,
    region_id: int,
    assessment_date: str,
    severity: str,
    severity_score: float,
    priority_score: float,
    factors: str,
) -> None:
    conn.execute(
        """INSERT INTO risk_assessments
           (region_id, assessment_date, severity, severity_score, priority_score, factors)
           VALUES (?, ?, ?, ?, ?, ?)
           ON CONFLICT (region_id, assessment_date)
           DO UPDATE SET severity = excluded.severity,
                         severity_score = excluded.severity_score,
                         priority_score = excluded.priority_score,
                         factors = excluded.factors""",
        (region_id, assessment_date, severity, severity_score, priority_score, factors),
    )


def upsert_recommendation(
    conn: sqlite3.Connection,
    region_id: int,
    recommendation_date: str,
    action: str,
    reason: str,
    source_rule: str | None,
) -> None:
    conn.execute(
        """INSERT INTO response_recommendations
           (region_id, recommendation_date, action, reason, source_rule)
           VALUES (?, ?, ?, ?, ?)
           ON CONFLICT (region_id, recommendation_date, action)
           DO UPDATE SET reason = excluded.reason, source_rule = excluded.source_rule""",
        (region_id, recommendation_date, action, reason, source_rule),
    )


def clear_prediction_assets(conn: sqlite3.Connection) -> None:
    """Remove previously computed prediction/risk/recommendation rows (used when
    re-running prediction jobs so the demo never accumulates stale weeks)."""
    conn.execute("DELETE FROM response_recommendations")
    conn.execute("DELETE FROM risk_assessments")
    conn.execute("DELETE FROM predictions")


def iter_observations_with_features(
    conn: sqlite3.Connection,
) -> Iterable[sqlite3.Row]:
    """Observations in the analytic form used by the ML pipeline.

    The ML pipeline re-reads `data/dengue_data.csv` directly (it computes
    rolling features itself); this loader exists for API convenience.
    """
    return get_observations(conn)