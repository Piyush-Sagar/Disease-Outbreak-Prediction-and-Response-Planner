#!/usr/bin/env python3
"""
Generate synthetic demonstration dataset for Dengue outbreak prediction.

This script creates clearly labelled DEMO/SYNTHETIC data for development
and academic prototyping. The data is NOT real-world epidemiological data.

The case-generating process encodes plausible correlations between
environmental factors and dengue incidence to allow the ML models
to learn meaningful patterns during training.
"""

import csv
import json
import math
import os
import random

SEED = 42
random.seed(SEED)

# ── Regions ────────────────────────────────────────────────────────────────
REGIONS = [
    {"id": 1,  "name": "Chennai",     "latitude": 13.0827, "longitude": 80.2707, "population": 10971000, "population_density": 26553},
    {"id": 2,  "name": "Kochi",       "latitude": 9.9312,  "longitude": 76.2673, "population": 2117000,  "population_density": 8601},
    {"id": 3,  "name": "Mumbai",      "latitude": 19.0760, "longitude": 72.8777, "population": 20411000, "population_density": 32303},
    {"id": 4,  "name": "Delhi",       "latitude": 28.7041, "longitude": 77.1025, "population": 19814000, "population_density": 29259},
    {"id": 5,  "name": "Kolkata",     "latitude": 22.5726, "longitude": 88.3639, "population": 14850000, "population_density": 24306},
    {"id": 6,  "name": "Bengaluru",   "latitude": 12.9716, "longitude": 77.5946, "population": 12327000, "population_density": 18653},
    {"id": 7,  "name": "Hyderabad",   "latitude": 17.3850, "longitude": 78.4867, "population": 10004000, "population_density": 18480},
    {"id": 8,  "name": "Pune",        "latitude": 18.5204, "longitude": 73.8567, "population": 7421000,  "population_density": 11967},
    {"id": 9,  "name": "Jaipur",      "latitude": 26.9124, "longitude": 75.7873, "population": 3909000,  "population_density": 6500},
    {"id": 10, "name": "Lucknow",     "latitude": 26.8467, "longitude": 80.9462, "population": 3681000,  "population_density": 7625},
    {"id": 11, "name": "Varanasi",    "latitude": 25.3176, "longitude": 83.0064, "population": 1435000,  "population_density": 23906},
    {"id": 12, "name": "Guwahati",    "latitude": 26.1445, "longitude": 91.7362, "population": 962000,   "population_density": 4409},
]

HEALTH_CENTERS = [
    {"id": 1, "name": "Chennai GH",        "region_id": 1,  "latitude": 13.0827, "longitude": 80.2707},
    {"id": 2, "name": "Kochi Medical",     "region_id": 2,  "latitude": 9.9312,  "longitude": 76.2673},
    {"id": 3, "name": "Mumbai J.J.",       "region_id": 3,  "latitude": 19.0760, "longitude": 72.8777},
    {"id": 4, "name": "Delhi AIIMS",       "region_id": 4,  "latitude": 28.7041, "longitude": 77.1025},
    {"id": 5, "name": "Kolkata Medical",   "region_id": 5,  "latitude": 22.5726, "longitude": 88.3639},
    {"id": 6, "name": "Bengaluru Victoria","region_id": 6,  "latitude": 12.9716, "longitude": 77.5946},
]

# Region-specific environmental profile baselines (monthly, Jan–Dec)
# Indian dengue seasonality: cases peak July–October (post-monsoon)
TEMP_BASELINES = {  # Monthly avg temperature per region (simplified)
    "Chennai":   [26, 27, 29, 31, 33, 34, 33, 33, 32, 31, 29, 27],
    "Kochi":     [27, 28, 30, 31, 30, 28, 27, 28, 29, 29, 28, 27],
    "Mumbai":    [25, 26, 28, 30, 31, 30, 29, 29, 30, 31, 29, 27],
    "Delhi":     [14, 17, 23, 30, 36, 38, 35, 33, 33, 29, 22, 16],
    "Kolkata":   [18, 22, 28, 32, 33, 32, 31, 31, 31, 30, 25, 20],
    "Bengaluru": [22, 24, 27, 28, 28, 27, 26, 27, 27, 27, 25, 23],
    "Hyderabad": [22, 25, 29, 32, 34, 32, 30, 30, 31, 30, 26, 23],
    "Pune":      [21, 23, 27, 30, 32, 29, 27, 27, 28, 29, 25, 22],
    "Jaipur":    [16, 19, 25, 31, 36, 37, 33, 31, 32, 30, 24, 18],
    "Lucknow":   [15, 18, 25, 31, 35, 35, 31, 30, 31, 28, 23, 17],
    "Varanasi":  [16, 19, 26, 32, 36, 35, 31, 30, 31, 29, 24, 18],
    "Guwahati":  [16, 18, 22, 26, 28, 29, 29, 29, 29, 27, 22, 17],
}

RAIN_BASELINES = {  # Monthly avg rainfall mm
    "Chennai":   [20, 10, 10, 20, 40, 50, 90, 120, 120, 260, 350, 140],
    "Kochi":     [15, 20, 30, 120, 320, 550, 500, 300, 260, 290, 160, 40],
    "Mumbai":    [1,  2,  1,  5,  10, 500, 700, 500, 300, 80,  15,  3],
    "Delhi":     [20, 25, 30, 15, 20, 70,  200, 230, 140, 20,  5,   10],
    "Kolkata":   [10, 20, 35, 50, 140, 280, 330, 330, 270, 140, 20,  5],
    "Bengaluru": [2,  5,  8,  40, 120, 80,  100, 130, 180, 180, 50, 15],
    "Hyderabad": [5,  10, 15, 20, 40, 120, 160, 170, 160, 60,  20,  5],
    "Pune":      [2,  2,  5,  10, 20, 200, 250, 200, 120, 50,  10,  3],
    "Jaipur":    [7,  10, 8,  5,  15, 70,  200, 220, 110, 20,  5,   5],
    "Lucknow":   [15, 15, 10, 5,  15, 100, 300, 280, 200, 50,  5,   10],
    "Varanasi":  [15, 15, 10, 5,  20, 100, 300, 290, 220, 50,  5,   8],
    "Guwahati":  [10, 25, 50, 120, 230, 280, 300, 250, 200, 120, 30,  10],
}

HUMIDITY_BASELINES = {  # Monthly avg relative humidity %
    "Chennai":   [70, 65, 65, 70, 65, 60, 62, 65, 72, 78, 80, 75],
    "Kochi":     [70, 68, 70, 75, 80, 85, 85, 82, 82, 82, 78, 72],
    "Mumbai":    [60, 58, 62, 68, 70, 82, 86, 85, 82, 75, 65, 60],
    "Delhi":     [55, 45, 40, 35, 35, 50, 72, 78, 70, 50, 45, 55],
    "Kolkata":   [60, 55, 58, 65, 72, 80, 85, 86, 83, 78, 65, 58],
    "Bengaluru": [55, 50, 50, 60, 65, 62, 63, 65, 68, 72, 65, 58],
    "Hyderabad": [55, 48, 45, 50, 55, 65, 72, 75, 75, 72, 62, 55],
    "Pune":      [50, 45, 42, 45, 50, 68, 78, 78, 75, 65, 55, 48],
    "Jaipur":    [45, 40, 35, 30, 35, 50, 72, 78, 65, 45, 42, 48],
    "Lucknow":   [60, 50, 45, 40, 40, 55, 78, 82, 75, 60, 52, 60],
    "Varanasi":  [60, 52, 45, 38, 42, 58, 80, 85, 78, 62, 52, 62],
    "Guwahati":  [60, 55, 55, 65, 75, 82, 85, 85, 82, 78, 62, 58],
}


def month_from_week(week_start: str) -> int:
    """Extract month (1-12) from a date string."""
    import datetime
    dt = datetime.datetime.strptime(week_start, "%Y-%m-%d")
    return dt.month


def generate_dengue_data(regions: list[dict], p=None) -> list[dict]:
    """
    Generate weekly dengue data from 2023-01 to 2026-09.

    The process:
    1. Environmental base = region monthly baseline + noise
    2. Water accumulation index is a weighted function of recent rainfall
    3. Dengue cases are driven by:
       - Temperature (optimal: 25-35C)
       - Rainfall (lagged effect: 2-4 weeks for mosquito breeding)
       - Humidity (higher = more breeding)
       - Water accumulation index
       - Population density
    4. Outbreaks occur stochastically when environmental suitability is high
       during a region's post-monsoon window (region-specific peak month),
       so the model must learn to combine environmental + seasonal signals
       rather than a fixed calendar rule.
    """
    import datetime

    # Tunable generation parameters (used by the tuning harness).
    if p is None:
        p = {
            "noise_std": 4,      # env -> cases stochastic noise
            "ac_self": 0.85,     # weight on environment-driven base
            "ac_prev": 0.15,     # weight on previous week's cases
            "ac_noise_std": 2,   # autocorrelation noise
            "surge_threshold_base": 0.48,  # sustained-favorability threshold offset
            "outbreak_mult_lo": 2.5,       # surge multiplier range
            "outbreak_mult_hi": 1.6,       # (added to lo)
        }
    # Region-specific post-monsoon peak month (1-12) for outbreak propensity.
    OUTBREAK_PEAK_MONTH = {
        "Chennai": 10, "Kochi": 8, "Mumbai": 9, "Delhi": 10, "Kolkata": 10,
        "Bengaluru": 10, "Hyderabad": 9, "Pune": 9, "Jaipur": 8, "Lucknow": 9,
        "Varanasi": 10, "Guwahati": 8,
    }
    # Relative outbreak propensity per region (higher = larger/earlier surge).
    OUTBREAK_STRENGTH = {
        "Chennai": 1.0, "Kochi": 0.8, "Mumbai": 0.9, "Delhi": 0.8, "Kolkata": 0.8,
        "Bengaluru": 0.2, "Hyderabad": 0.2, "Pune": 0.6, "Jaipur": 0.4,
        "Lucknow": 0.5, "Varanasi": 0.7, "Guwahati": 0.4,
    }

    all_rows = []
    start_date = datetime.date(2023, 1, 2)
    total_weeks = 188  # ~3.7 years (2023-01 -> 2026-08)

    for region in regions:
        rname = region["name"]
        temp_base = TEMP_BASELINES[rname]
        rain_base = RAIN_BASELINES[rname]
        humid_base = HUMIDITY_BASELINES[rname]
        pop_density = region["population_density"]
        peak_month = OUTBREAK_PEAK_MONTH[rname]
        strength = OUTBREAK_STRENGTH[rname]

        recent_rain = [0.0] * 4
        weekly_cases_base = 15 + (pop_density / 1000)
        fav_history = []

        for w in range(total_weeks):
            week_date = start_date + datetime.timedelta(weeks=w)
            month = week_date.month - 1  # 0-indexed

            temperature = temp_base[month] + random.gauss(0, 1.5)
            temperature = max(10, min(42, temperature))

            rainfall = max(0, rain_base[month] * (0.4 + random.random()))
            humidity = humid_base[month] + random.gauss(0, 3)
            humidity = max(20, min(98, humidity))

            recent_rain.append(rainfall)
            recent_rain.pop(0)

            water_index = sum(r * w for r, w in zip(recent_rain, [0.4, 0.3, 0.2, 0.1])) / 20.0
            water_index = max(0, min(10, water_index))

            # ── Environmental suitability (0-1) ───────────────────────
            temp_suit = max(0, 1 - abs(temperature - 30) / 10)
            rain_suit = min(1, rainfall / 200)
            humid_suit = humidity / 100
            water_suit = min(1, water_index / 5)
            density_factor = pop_density / 30000

            suitability = (
                0.30 * temp_suit
                + 0.25 * rain_suit
                + 0.15 * humid_suit
                + 0.15 * water_suit
                + 0.15 * density_factor
            )

            raw_cases = weekly_cases_base * (0.5 + 4.0 * suitability) + random.gauss(0, p["noise_std"])

            # ── Sustained-favorability outbreak trigger ───────────────
            # Outbreaks fire when a 6-week smoothed suitability exceeds a
            # region-specific threshold during the post-monsoon window.
            # Because the smoothed index is itself driven by the observed
            # environmental series, the ML model can learn the pattern from
            # its rolling temperature/rainfall/humidity features.
            fav_history.append(suitability)
            continuous_fav = sum(fav_history[-6:]) / min(len(fav_history), 6) if fav_history else 0.0

            dist_to_peak = min(abs(week_date.month - peak_month), 12 - abs(week_date.month - peak_month))
            seasonal_boost = math.exp(-(dist_to_peak ** 2) / (2 * 2.0 ** 2))
            surge_threshold = p["surge_threshold_base"] - 0.18 * strength
            if continuous_fav >= surge_threshold and seasonal_boost > 0.4:
                raw_cases *= p["outbreak_mult_lo"] + random.random() * p["outbreak_mult_hi"]

            # Weak autocorrelation: recent cases pull, but environment dominates.
            if all_rows:
                prev = [r for r in all_rows if r["region"] == rname]
                if prev:
                    raw_cases = (p["ac_self"] * raw_cases
                                 + p["ac_prev"] * prev[-1]["reported_cases"]
                                 + random.gauss(0, p["ac_noise_std"]))

            reported_cases = max(0, int(round(raw_cases)))

            death_rate = 0.008 + (0.015 if suitability > 0.6 else 0) + random.random() * 0.006
            deaths = max(0, int(round(reported_cases * death_rate))) if reported_cases > 12 else 0

            prev_week_cases = 0
            prev_month_cases = 0
            prev_data = [r for r in all_rows if r["region"] == rname]
            if len(prev_data) >= 1:
                prev_week_cases = prev_data[-1]["reported_cases"]
            if len(prev_data) >= 4:
                prev_month_cases = sum(r["reported_cases"] for r in prev_data[-4:])

            all_rows.append({
                "date": week_date.strftime("%Y-%m-%d"),
                "region": rname,
                "latitude": region["latitude"],
                "longitude": region["longitude"],
                "population": region["population"],
                "reported_cases": reported_cases,
                "previous_week_cases": prev_week_cases,
                "previous_month_cases": prev_month_cases,
                "deaths": deaths,
                "temperature": round(temperature, 1),
                "rainfall": round(rainfall, 1),
                "humidity": round(humidity, 1),
                "water_accumulation_index": round(water_index, 2),
                "population_density": pop_density,
            })

    return all_rows


def generate_roads_graph() -> dict:
    """
    Generate a simplified road graph connecting Indian cities.
    Nodes include cities and intermediate junction points.
    Edges represent roads with distance (km) and estimated travel time (min).
    Based on approximate real-world distances between Indian cities.
    """
    nodes = [
        {"id": "J-Chennai-Hyderabad", "name": "Junction NH44-CH", "latitude": 14.5, "longitude": 78.9},
        {"id": "J-Mumbai-Pune", "name": "Junction Mumbai-Pune", "latitude": 19.0, "longitude": 73.5},
        {"id": "J-Delhi-Lucknow", "name": "Junction NH44-DL", "latitude": 27.8, "longitude": 78.5},
        {"id": "J-Kolkata-Varanasi", "name": "Junction NH2-KV", "latitude": 24.5, "longitude": 85.5},
        {"id": "J-Pune-Hyderabad", "name": "Junction Pune-Hyd", "latitude": 17.8, "longitude": 76.0},
        {"id": "J-Mumbai-Nashik", "name": "Junction MH-NH", "latitude": 20.0, "longitude": 73.8},
        {"id": "J-Delhi-Jaipur", "name": "Junction NH48-DJ", "latitude": 27.9, "longitude": 76.2},
    ]

    city_nodes = []
    for r in REGIONS:
        city_nodes.append({
            "id": f"city-{r['name'].lower()}",
            "name": r["name"],
            "latitude": r["latitude"],
            "longitude": r["longitude"],
        })

    all_nodes = city_nodes + nodes

    # Edges: (from_id, to_id, distance_km, travel_time_min)
    edge_data = [
        ("city-chennai",        "J-Chennai-Hyderabad",   195,  180),
        ("J-Chennai-Hyderabad", "city-hyderabad",         520,  450),
        ("city-chennai",        "city-bengaluru",         340,  300),
        ("city-bengaluru",      "J-Pune-Hyderabad",       460,  390),
        ("J-Pune-Hyderabad",    "city-pune",               230,  190),
        ("J-Pune-Hyderabad",    "city-hyderabad",          150,  130),
        ("city-mumbai",         "J-Mumbai-Pune",           120,  100),
        ("J-Mumbai-Pune",       "city-pune",                65,   50),
        ("city-mumbai",         "J-Mumbai-Nashik",         165,  140),
        ("J-Mumbai-Nashik",     "city-pune",               200,  170),
        ("city-mumbai",         "city-kolkata",           1900, 1500),
        ("city-mumbai",         "city-jaipur",             950,  810),
        ("city-mumbai",         "city-delhi",             1400, 1180),
        ("city-delhi",          "J-Delhi-Lucknow",        490,  420),
        ("J-Delhi-Lucknow",     "city-lucknow",            120,  100),
        ("city-delhi",          "J-Delhi-Jaipur",         270,  230),
        ("J-Delhi-Jaipur",      "city-jaipur",             180,  150),
        ("city-delhi",          "city-varanasi",          820,  700),
        ("city-kolkata",        "J-Kolkata-Varanasi",     640,  540),
        ("J-Kolkata-Varanasi",  "city-varanasi",           220,  185),
        ("city-kolkata",        "city-guwahati",         1000,  850),
        ("city-kolkata",        "city-lucknow",           980,  830),
        ("city-lucknow",        "city-varanasi",          310,  270),
        ("city-guwahati",       "city-varanasi",          830,  700),
        ("city-kochi",          "city-bengaluru",          520,  450),
        ("city-kochi",          "city-chennai",            700,  600),
        ("city-bengaluru",      "city-hyderabad",          570,  490),
    ]

    edges = []
    for from_id, to_id, dist, time in edge_data:
        edges.append({
            "from": from_id,
            "to": to_id,
            "distance_km": dist,
            "travel_time_min": time,
        })

    return {"nodes": all_nodes, "edges": edges}


def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_root, "data")

    # 1. Regions CSV
    regions_path = os.path.join(data_dir, "regions.csv")
    with open(regions_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(REGIONS[0].keys()))
        writer.writeheader()
        writer.writerows(REGIONS)
    print(f"Wrote {len(REGIONS)} regions to {regions_path}")

    # 2. Dengue data CSV
    rows = generate_dengue_data(REGIONS)
    dengue_path = os.path.join(data_dir, "dengue_data.csv")
    with open(dengue_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} weekly observations to {dengue_path}")

    # 3. Roads graph JSON
    roads = generate_roads_graph()
    roads_path = os.path.join(data_dir, "roads.json")
    with open(roads_path, "w") as f:
        json.dump(roads, f, indent=2)
    print(f"Wrote road graph ({len(roads['nodes'])} nodes, {len(roads['edges'])} edges) to {roads_path}")

    # 4. Health centers CSV
    hc_path = os.path.join(data_dir, "health_centers.csv")
    with open(hc_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(HEALTH_CENTERS[0].keys()))
        writer.writeheader()
        writer.writerows(HEALTH_CENTERS)
    print(f"Wrote {len(HEALTH_CENTERS)} health centers to {hc_path}")


if __name__ == "__main__":
    main()
