"""Rule-based response planner.

Given a predicted-risk and severity situation for a region, chooses the
recommended response actions from `config.RESPONSE_RULES`. Every action
carries a human-readable reason populated from live values so the dashboard
can justify each recommendation (with a demo-data disclaimer).
"""

from .. import config

SEVERITY_RANK = {"LOW": 0, "MODERATE": 1, "HIGH": 2, "CRITICAL": 3}


def _fmt(value, digits=0):
    return f"{float(value):,.{digits}f}"


def plan_response(
    region: str,
    probability: float,
    risk_category: str,
    severity_band: str,
    context: dict | None = None,
) -> list[dict]:
    """Return matching response actions sorted by escalation level."""
    context = context or {}
    risk_pct = probability * 100
    active = [
        rule
        for rule in config.RESPONSE_RULES
        if SEVERITY_RANK.get(rule["min_severity"], 0) <= SEVERITY_RANK.get(severity_band, 0)
    ]
    ordered = sorted(
        active,
        key=lambda r: (SEVERITY_RANK.get(r["min_severity"], 0), r["id"]),
    )
    recommendations = []
    for rule in ordered:
        reason = rule["reason_template"].format(
            risk=_fmt(risk_pct),
            severity=severity_band,
            growth=_fmt(context.get("growth_rate", 0)),
            cases=_fmt(context.get("reported_cases", 0)),
            deaths=_fmt(context.get("deaths_4wk", 0)),
        )
        recommendations.append(
            {
                "action": rule["action"],
                "reason": reason,
                "severity_level": rule["min_severity"],
                "source_rule": rule["id"],
            }
        )
    return recommendations