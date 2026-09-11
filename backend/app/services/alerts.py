"""Alert generation.

Builds actionable alert entries from a region's predicted risk and severity.
Severity of alerts maps to the same risk bands used everywhere else.
"""

from .. import config


def build_alerts(region_name: str, probability: float, severity_band: str) -> list[dict]:
    risk_pct = probability * 100
    category = config.risk_category(risk_pct)
    alerts = []

    if risk_pct >= 70:
        alerts.append(
            {
                "level": "critical",
                "type": "risk",
                "region": region_name,
                "message": (
                    f"Very High predicted outbreak risk ({risk_pct:.0f}%) in {region_name} "
                    "during the next 7 days."
                ),
                "probability": risk_pct,
            }
        )
    elif risk_pct >= 50:
        alerts.append(
            {
                "level": "high",
                "type": "risk",
                "region": region_name,
                "message": (
                    f"High predicted outbreak risk ({risk_pct:.0f}%) in {region_name} "
                    "during the next 7 days."
                ),
                "probability": risk_pct,
            }
        )

    if severity_band == "CRITICAL":
        alerts.append(
            {
                "level": "critical",
                "type": "severity",
                "region": region_name,
                "message": f"CRITICAL severity conditions reported in {region_name}.",
                "probability": risk_pct,
            }
        )
    elif severity_band == "HIGH":
        alerts.append(
            {
                "level": "high",
                "type": "severity",
                "region": region_name,
                "message": f"High severity conditions reported in {region_name}.",
                "probability": risk_pct,
            }
        )
    return alerts