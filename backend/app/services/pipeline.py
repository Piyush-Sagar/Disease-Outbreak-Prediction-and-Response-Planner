"""End-to-end prediction pipeline.

Runs the ML model, severity, priority and response planning for every region
for the latest observation week and persists the results into SQLite. The API
endpoints read from the database, so a single `run_pipeline()` keeps the demo
consistent across all pages.
"""

import json
import sqlite3

import numpy as np

from .. import config, database
from . import alerts as alerts_service
from . import explainability, model_loader, priority as priority_service
from . import response_planner, severity as severity_service

REGIONAL_MAX_CASES = 0
REGIONAL_POP = {}


def _regional_stats(feature_frame) -> tuple[dict, dict]:
    max_cases: dict[str, float] = {}
    pop: dict[str, int] = {}
    for _, row in feature_frame.iterrows():
        region = row["region"]
        max_cases[region] = max(max_cases.get(region, 0.0), float(row["reported_cases"]))
        pop[region] = int(row["population"])
    return max_cases, pop


class PredictionPipeline:
    def __init__(self, model_service: model_loader.ModelService | None = None):
        self.model_service = model_service or model_loader.ModelService()

    def compute_contexts(self) -> list[dict]:
        """Latest per-region context: prediction + severity + priority + actions."""
        frame = self.model_service._ensure_feature_frame()
        max_cases, pop = _regional_stats(frame)

        records = self.model_service.predict_all()
        probs = {r.region: r.probability for r in records}
        high_risk_share = {
            region: float(np.mean([1 if probs[o] >= 0.50 else 0 for o in probs if o != region]))
            for region in probs
        }

        contexts = []
        for record in records:
            region = record.region
            latest_row = frame[frame["region"] == region].sort_values("date").iloc[-1]
            context_row = {
                "reported_cases": float(latest_row["reported_cases"]),
                "growth_rate": float(latest_row["case_growth_rate"])
                if not np.isnan(latest_row["case_growth_rate"])
                else 0.0,
                "deaths_4wk": float(latest_row.get("deaths", 0) or 0),
                "population": pop[region],
                "regional_max_cases": max_cases[region],
            }

            severity = severity_service.compute_severity(
                probability=record.probability,
                current_cases=context_row["reported_cases"],
                regional_max_cases=max_cases[region],
                growth_rate=context_row["growth_rate"],
                deaths_4wk=context_row["deaths_4wk"],
                high_risk_share=high_risk_share[region],
            )

            priority = priority_service.compute_priority(
                probability=record.probability,
                severity_band=severity["band"],
                population=pop[region],
                max_population=max(pop.values()),
            )

            actions = response_planner.plan_response(
                region=region,
                probability=record.probability,
                risk_category=record.risk_category,
                severity_band=severity["band"],
                context=context_row,
            )

            alerts = alerts_service.build_alerts(
                region_name=region,
                probability=record.probability,
                severity_band=severity["band"],
            )

            contexts.append(
                {
                    "region": region,
                    "observation_date": record.observation_date,
                    "prediction_date": record.prediction_date,
                    "probability": record.probability,
                    "probability_lr": record.probability_lr,
                    "risk_category": record.risk_category,
                    "severity": severity,
                    "priority": priority,
                    "actions": actions,
                    "alerts": alerts,
                    "features": record.features,
                    "context": context_row,
                    "label_methodology": config.LABEL_METHODOLOGY,
                    "severity_methodology": config.SEVERITY_METHODOLOGY,
                    "priority_methodology": config.PRIORITY_METHODOLOGY,
                    "demo_data_disclaimer": config.DEMO_DATA_DISCLAIMER,
                }
            )
        return contexts

    def persist(self, conn: sqlite3.Connection) -> None:
        contexts = self.compute_contexts()
        database.clear_prediction_assets(conn)
        for ctx in contexts:
            region_id = conn.execute(
                "SELECT id FROM regions WHERE name = ?", (ctx["region"],)
            ).fetchone()["id"]
            database.upsert_prediction(
                conn,
                region_id=region_id,
                observation_date=ctx["observation_date"],
                prediction_date=ctx["prediction_date"],
                probability=ctx["probability"],
                risk_category=ctx["risk_category"],
                model_name="Random Forest (serving)",
            )
            database.upsert_prediction(
                conn,
                region_id=region_id,
                observation_date=ctx["observation_date"],
                prediction_date=ctx["prediction_date"],
                probability=ctx["probability_lr"],
                risk_category=config.risk_category(ctx["probability_lr"] * 100),
                model_name="Logistic Regression (baseline)",
            )
            database.upsert_risk_assessment(
                conn,
                region_id=region_id,
                assessment_date=ctx["prediction_date"],
                severity=ctx["severity"]["band"],
                severity_score=ctx["severity"]["score"],
                priority_score=ctx["priority"]["score"],
                factors=json.dumps(ctx["severity"]["factors"]),
            )
            for action in ctx["actions"]:
                database.upsert_recommendation(
                    conn,
                    region_id=region_id,
                    recommendation_date=ctx["prediction_date"],
                    action=action["action"],
                    reason=action["reason"],
                    source_rule=action["source_rule"],
                )
        conn.commit()


def run_pipeline(conn: sqlite3.Connection) -> dict:
    pipeline = PredictionPipeline()
    contexts = pipeline.compute_contexts()
    pipeline.persist(conn)
    return {
        "observation_date": contexts[0]["observation_date"],
        "prediction_date": contexts[0]["prediction_date"],
        "regions": len(contexts),
        "high_risk_regions": sum(1 for c in contexts if c["probability"] >= 0.50),
        "alerts": sum(len(c["alerts"]) for c in contexts),
    }