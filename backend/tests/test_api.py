"""API smoke tests against the running FastAPI app."""

from fastapi.testclient import TestClient  # noqa: F401
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_dashboard_summary(client):
    resp = client.get("/api/dashboard/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["regions_count"] == 12
    assert 0 <= body["avg_probability"] <= 1
    assert "demo" in body["demo_data_disclaimer"].lower()


def test_predictions_shape(client):
    resp = client.get("/api/predictions")
    assert resp.status_code == 200
    preds = resp.json()
    assert len(preds) == 12
    probs = [p["probability"] for p in preds]
    assert all(0 <= p <= 1 for p in probs)
    # the model quality setup guarantees a spread, so the demo map is interesting
    assert max(probs) >= 0.50
    assert min(probs) <= 0.20


def test_prediction_detail_with_explainability(client):
    resp = client.get("/api/predictions/1")
    assert resp.status_code == 200
    body = resp.json()
    assert "probability" in body
    assert "severity_band" in body
    assert body["explainability"]["attributions"]
    assert all(r["feature"] for r in body["explainability"]["attributions"])


def test_priority_ranked_desc(client):
    resp = client.get("/api/regions/priority")
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 12
    scores = [r["priority_score"] for r in rows]
    assert scores == sorted(scores, reverse=True)


def test_regions_and_health_centers(client):
    regions = client.get("/api/regions").json()
    centers = client.get("/api/health-centers").json()
    assert len(regions) == 12
    assert len(centers) == 6
    assert all(r["latitude"] and r["longitude"] for r in regions)


def test_recommendations_nonempty_for_high_risk(client):
    resp = client.get("/api/recommendations/4")  # Delhi (region id 4)
    assert resp.status_code == 200
    assert len(resp.json()) > 0
    assert resp.json()[0]["action"]


def test_alerts_include_critical_for_high_risk(client):
    alerts = client.get("/api/alerts").json()
    assert alerts
    levels = {a["level"] for a in alerts}
    assert "critical" in levels


def test_dataset_info(client):
    body = client.get("/api/dataset-info").json()
    assert body["observations"] > 1000
    assert body["disease"] == "Dengue"
    assert "synthetic" in body["synthetic_notice"].lower()


def test_model_performance(client):
    body = client.get("/api/model-performance").json()
    names = [m["model"] for m in body["metrics"]["models"]]
    assert "Random Forest" in names
    assert "Logistic Regression" in names
    assert body["figures"]


def test_route_post(client):
    resp = client.post(
        "/api/route",
        json={"start": "Delhi", "goal": "Mumbai", "weight": "time"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["dijkstra"]["path"][0] == "city-delhi"
    assert body["dijkstra"]["path"][-1] == "city-mumbai"
    assert body["astar"]["total_weight"] == body["dijkstra"]["total_weight"]


def test_route_unknown_location(client):
    resp = client.post("/api/route", json={"start": "Nope", "goal": "Delhi", "weight": "time"})
    assert resp.status_code == 404


def test_route_graph(client):
    body = client.get("/api/route/graph").json()
    assert body["counts"]["nodes"] >= 12
    assert body["counts"]["edges"] >= 20