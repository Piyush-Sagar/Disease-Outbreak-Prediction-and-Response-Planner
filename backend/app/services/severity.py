"""Severity classification service.

Combines the model outbreak probability with epidemiological context into a
project-defined severity score (0-1) and band (LOW/MODERATE/HIGH/CRITICAL).
"""

from .. import config


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _cases_score(current_cases: float, regional_max_cases: float) -> float:
    if not regional_max_cases:
        return 0.0
    return _clip01(current_cases / regional_max_cases)


def _growth_score(growth_rate: float) -> float:
    # growth=0 -> 0, growth >= 2.0 (200%) -> 1
    return _clip01((growth_rate + 1.0) / 2.0) if growth_rate < 0 else _clip01(growth_rate / 2.0)


def _death_score(deaths_4wk: float, ref_deaths: float = 20.0) -> float:
    return _clip01(deaths_4wk / ref_deaths)


def _spread_score(high_risk_share: float) -> float:
    return _clip01(high_risk_share)


def compute_severity(
    probability: float,
    current_cases: float,
    regional_max_cases: float,
    growth_rate: float,
    deaths_4wk: float,
    high_risk_share: float,
) -> dict:
    """Return {score, band, factors} where factors explains each sub-score."""
    prob_score = _clip01(probability)
    cs = _cases_score(current_cases, regional_max_cases)
    gs = _growth_score(growth_rate)
    ds = _death_score(deaths_4wk)
    ss = _spread_score(high_risk_share)

    weights = config.SEVERITY_CONFIG["weights"]
    score = (
        weights["probability_score"] * prob_score
        + weights["cases_score"] * cs
        + weights["growth_score"] * gs
        + weights["death_score"] * ds
        + weights["spread_score"] * ss
    )
    score = round(_clip01(score), 4)
    band = config.severity_band(score)
    factors = {
        "probability_score": round(prob_score, 3),
        "cases_score": round(cs, 3),
        "growth_score": round(gs, 3),
        "death_score": round(ds, 3),
        "spread_score": round(ss, 3),
    }
    return {"score": score, "band": band, "factors": factors, "methodology": config.SEVERITY_METHODOLOGY}