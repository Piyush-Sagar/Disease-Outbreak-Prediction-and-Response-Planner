# Response Planning Methodology

How predicted risk becomes severity, priority, recommended actions, alerts and
routing — all demonstration formulas for ranking and planning a response to the
predicted high-incidence event.

## Risk probability bands

The predicted probability (0–100%) maps to a risk category shared by every
layer (defined once in `ml/config.py`):

| Band | Range (%) | Colour |
| --- | --- | --- |
| Low | 0–29 | `#16a34a` |
| Moderate | 30–49 | `#eab308` |
| High | 50–69 | `#f97316` |
| Very High | 70–100 | `#dc2626` |

## Severity score (`services/severity.py`)

A weighted composite score (0–1) from five normalized sub-scores:

| Factor | Weight | Computation |
| --- | --- | --- |
| `probability_score` | 0.25 | model outbreak probability (0–1) |
| `cases_score` | 0.20 | current cases ÷ regional historical max |
| `growth_score` | 0.20 | weekly growth rate: negative → `(g+1)/2`; else `g/2`, clipped to 0–1 |
| `death_score` | 0.15 | deaths (4 wk) ÷ 20, clipped |
| `spread_score` | 0.20 | share of other regions at ≥50% predicted risk |

```text
severity_score = 0.25·prob + 0.20·cases + 0.20·growth + 0.15·death + 0.20·spread
```

Bands (`severity_band(score)`):

| Band | Score |
| --- | --- |
| LOW | ≤ 0.30 |
| MODERATE | ≤ 0.55 |
| HIGH | ≤ 0.80 |
| CRITICAL | ≤ 1.00 |

## Priority score (`services/priority.py`)

Ranks regions for resource allocation, 0–100:

```text
priority_score = 100 × (0.50 × probability + 0.30 × severity_weight + 0.20 × population_factor)
```

Severity weights:

| Severity | Weight |
| --- | --- |
| LOW | 0.10 |
| MODERATE | 0.35 |
| HIGH | 0.70 |
| CRITICAL | 1.00 |

`population_factor` is the region population log-scaled to 0–1 using the most
populous region as the top anchor. Example ordering from the seeded Real data
(latest week): Delhi 88.4, Kolkata 86.6, Chennai 85.0, Varanasi 84.4,
Bengaluru 83.5.

## Response actions (`services/response_planner.py`)

13 rules (`config.RESPONSE_RULES`) map severity bands to recommended actions.
A rule applies when the region’s severity band rank is **at least** the rule’s
`min_severity` (so CRITICAL regions get the union of LOW→CRITICAL actions),
sorted by escalation level. Every action stores the region-specific values in
its `reason` string.

| min_severity | Action |
| --- | --- |
| LOW | Continue routine surveillance · Monitor environmental conditions |
| MODERATE | Increase monitoring frequency · Inspect potential breeding areas · Increase public awareness |
| HIGH | Deploy additional health workers · Prioritize testing and surveillance · Inspect high-risk locations · Monitor neighboring regions |
| CRITICAL | Immediate field response · Prioritize health-worker deployment · Coordinate emergency response resources · Increase surveillance and testing across all wards |

Example persisted row for Delhi (HIGH):

```json
{
  "action": "Deploy additional health workers",
  "reason": "High predicted risk (95%) with elevated severity (HIGH) requires extra field staff.",
  "source_rule": "high-s1"
}
```

## Alerts (`services/alerts.py`)

Alerts are generated from predicted risk and severity:

- `risk_pct >= 70` → **critical** risk alert · `>= 50` → **high** risk alert
- `severity == CRITICAL` → **critical** severity alert · `severity == HIGH` →
  **high** severity alert

`GET /api/alerts` returns all alerts sorted critical-first and by descending
probability. `GET /api/dashboard/summary` reports the count of **critical**
alerts only.

## Routing (Dijkstra vs A*)

The road network (`data/roads.json`) has 19 nodes (12 city nodes + synthetic
highway junctions) and 27 bidirectional edges, each with `distance_km` and
`travel_time_min`.

- **Dijkstra** (`services/routing/dijkstra.py`) — classic heap-based shortest
  path; `weight = "time"` (minutes) or `"distance"` (km).
- **A*** (`services/routing/astar.py`) — same result, but guides the search with
  an **admissible heuristic**: the haversine great-circle distance to the goal
  divided by the fastest edge speed on the network (for time), or the haversine
  distance itself (for distance). Admissibility guarantees the same optimal path
  while typically visiting fewer nodes.

`POST /api/route` returns both results plus `nodes`/`edges` for map rendering, so
the `/routes` page can compare explored-node counts side by side.

## From prediction to persisted answer

`PredictionPipeline` (`services/pipeline.py`) computes all of the above for every
region for the latest week and persists:

1. serving + baseline predictions (`predictions`)
2. severity + priority (`risk_assessments`, with JSON `factors`)
3. response actions (`response_recommendations`)

The dashboard then reads these persisted rows, keeping every page consistent.