"""Priority scoring service.

Ranks regions for resource-allocation decisions using the project-defined
formula from `ml/config.py::PRIORITY_CONFIG`.
"""

import math

from .. import config


def population_factor(population: int, max_population: int) -> float:
    """Log-scaled population in 0-1 using the largest region as the top."""
    if max_population <= 0 or population <= 0:
        return 0.0
    lo, hi = math.log10(1), math.log10(max_population)
    if hi <= lo:
        return 1.0
    return max(0.0, min(1.0, (math.log10(population) - lo) / (hi - lo)))


def compute_priority(
    probability: float,
    severity_band: str,
    population: int,
    max_population: int,
) -> dict:
    """Return {score, components, methodology} with score in 0-100."""
    weights = config.PRIORITY_CONFIG["weights"]
    severity_weight = config.SEVERITY_BAND_WEIGHTS.get(severity_band, 0.35)
    pop_factor = population_factor(population, max_population)
    score = 100.0 * (
        weights["probability"] * max(0.0, min(1.0, probability))
        + weights["severity"] * severity_weight
        + weights["population"] * pop_factor
    )
    return {
        "score": round(min(100.0, score), 1),
        "components": {
            "probability_weight": weights["probability"],
            "severity_weight": weights["severity"],
            "population_weight": weights["population"],
            "severity_band": severity_band,
            "severity_band_factor": severity_weight,
            "population_factor": round(pop_factor, 3),
        },
        "methodology": config.PRIORITY_METHODOLOGY,
    }