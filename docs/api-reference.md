# API Reference

Base URL (default): `http://127.0.0.1:8000`

Interactive OpenAPI docs: [`/docs`](http://127.0.0.1:8000/docs) ·
ReDoc: `/redoc` · OpenAPI JSON: `/openapi.json`

All endpoints return JSON. Errors use standard FastAPI shapes, e.g.
`{"detail": "Region 99 not found"}` with status `404`, or `422` for validation
errors. CORS is open (`*`) so the Next.js dev server can call the API directly.

## General

| Method | Path | Description |
| --- | --- | --- |
| GET | `/` | HTML landing page linking to `/docs` |
| GET | `/health` | Liveness probe: `{status, demo_mode, disease}` |
| GET | `/static/figures/*.png` | Trained model figures (mounted from `ml/figures`) |

## Regions

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/regions` | All regions (`id, name, latitude, longitude, population, population_density`) |
| GET | `/api/regions/priority` | Regions ranked by priority score for the latest assessment date |
| GET | `/api/regions/{region_id}` | Single region (404 if missing) |
| GET | `/api/health-centers` | All health centers |

`GET /api/regions/priority` returns one object per region joined with its latest
risk assessment and serving-model prediction, ordered by `priority_score`
descending. Example element:

```json
{
  "id": 4,
  "name": "Delhi",
  "latitude": 28.7041,
  "longitude": 77.1025,
  "population": 19814000,
  "assessment_date": "2026-08-10",
  "severity": "HIGH",
  "severity_score": 0.7984,
  "priority_score": 88.4,
  "factors": "{\"probability_score\": 0.949, \"cases_score\": 0.841, \"growth_score\": 1.0, \"death_score\": 0.8, \"spread_score\": 0.364}",
  "outbreak_probability": 0.9494,
  "risk_category": "Very High"
}
```

## Predictions & risk

| Method | Path | Query params | Description |
| --- | --- | --- | --- |
| GET | `/api/predictions` | — | Latest serving-model prediction per region, ordered by probability desc |
| GET | `/api/predictions/{region_id}` | `explain` (bool, default `true`) | Prediction detail + severity factors + optional explainability (404 if none) |
| GET | `/api/risk-assessments` | — | All risk assessments ordered by priority score |
| GET | `/api/regions/{region_id}/history` | `limit` (8–500, default 52) | Weekly observations, oldest → newest (404 if region missing) |
| GET | `/api/timeseries/cases` | — | National weekly totals: `date, total_cases, total_deaths` |
| GET | `/api/dataset-rows` | `limit` (1–500, default 15) | Latest observation rows joined with region name |

`GET /api/predictions` element (schema `PredictionOut`):

```json
{
  "region": "Delhi",
  "region_name": "Delhi",
  "observation_date": "2026-08-03",
  "prediction_date": "2026-08-10",
  "probability": 0.9494,
  "probability_lr": 0.5,
  "risk_category": "Very High",
  "severity_band": "HIGH",
  "severity_score": 0.7984,
  "priority_score": 88.4
}
```

`GET /api/predictions/{region_id}` adds `severity_factors`, the three
methodology strings, the demo disclaimer, and (when `explain=true`) an
`explainability` block with feature attributions in percentage points.

## Response recommendations

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/recommendations` | All recommendations: `region, action, reason, date` |
| GET | `/api/recommendations/{region_id}` | Recommendations for one region (404 if region missing) |

## Routing (Dijkstra vs A*)

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/route/graph` | Road graph: `nodes`, `edges`, `counts` |
| POST | `/api/route` | Compute shortest path with both algorithms |

`POST /api/route` request (`RouteRequest`):

```json
{ "start": "Delhi", "goal": "Mumbai", "weight": "time" }
```

`weight` is `"time"` (minutes) or `"distance"` (km); `start`/`goal` accept a
region name or graph node id. Response (`RouteOut`) contains `dijkstra` and
`astar` result objects (`path`, `total_weight`, `total_distance`, `total_time`,
`explored`, `nodes_visited`), plus `nodes` and `edges` for map rendering. An
unknown location returns `404`.

## Model, dataset & alerts

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/model-performance` | `metrics.json`, `metadata.json`, `feature_importance`, `figures`, methodologies, `risk_bands` |
| GET | `/api/dataset-info` | Observation count, regions, date range, total cases, source files, synthetic notice |
| GET | `/api/alerts` | All alerts, critical first, then by descending probability |

Alert element:

```json
{
  "level": "critical",
  "type": "risk",
  "region": "Delhi",
  "message": "Very High predicted outbreak risk (95%) in Delhi during the next 7 days.",
  "probability": 94.9
}
```

## Dashboard

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/dashboard/summary` | National summary for the latest week |

```json
{
  "as_of_date": "2026-08-03",
  "regions_count": 12,
  "high_risk_regions": 5,
  "critical_regions": 0,
  "latest_week_cases": 4698,
  "latest_week_deaths": 119,
  "avg_probability": 0.4044,
  "alerts_count": 5,
  "demo_data_disclaimer": "DEMO DATA - NOT FOR REAL-WORLD HEALTHCARE DECISIONS"
}
```

## Typical client flow

```text
/dashboard       -> GET /api/dashboard/summary, /api/regions/priority, /api/alerts
/regions         -> GET /api/regions, /api/regions/priority, /api/regions/{id}/history
/predictions     -> GET /api/predictions
/predictions/[id]-> GET /api/predictions/{id}?explain=true, /api/recommendations/{id}
/response        -> GET /api/regions/priority, /api/recommendations
/routes          -> GET /api/route/graph, POST /api/route
/model           -> GET /api/model-performance
/data            -> GET /api/dataset-info, /api/dataset-rows, /api/timeseries/cases
```