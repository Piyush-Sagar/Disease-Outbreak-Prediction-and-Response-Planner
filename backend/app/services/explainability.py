"""Model explainability (demo-grade feature attribution).

The prototype offers a lightweight, honest attribution: each feature is
perturbed one standard deviation from the region's own observed value and the
change in predicted outbreak probability is measured. The sign tells whether
the feature currently pushes risk up or down, and magnitude tells how much.
This is a perturbation sensitivity analysis, not a rigorous SHAP-style
attribution (documented as such).
"""

import numpy as np

from ml.features import FEATURE_COLUMNS

from .. import config
from .model_loader import ModelService


class Explainer:
    """Provides feature-level explanations for a region's prediction."""

    def __init__(self, model_service: ModelService):
        self.model_service = model_service
        self._std: dict[str, float] | None = None

    def _ensure_std(self) -> dict[str, float]:
        if self._std is None:
            frame = self.model_service._ensure_feature_frame()
            self._std = {
                col: float(np.std(frame[col].dropna())) if frame[col].notna().any() else 1.0
                for col in FEATURE_COLUMNS
            }
        return self._std

    def explain(self, region: str) -> dict:
        entry = next(
            (e for e in self.model_service.latest_regional_features() if e["region"] == region),
            None,
        )
        if entry is None:
            return {"region": region, "attributions": [], "methodology": config.EXPLAINABILITY_METHODOLOGY}
        feats = {k: entry[k] for k in FEATURE_COLUMNS}
        base = self.model_service.predictor.predict_proba_main(feats)
        std = self._ensure_std()
        rows = []
        for col in FEATURE_COLUMNS:
            candidate = dict(feats)
            candidate[col] = float(feats[col]) + std[col]
            shifted = self.model_service.predictor.predict_proba_main(candidate)
            delta = (shifted - base) * 100  # percentage points
            rows.append(
                {
                    "feature": col,
                    "value": round(float(feats[col]), 3),
                    "shift_std": 1,
                    "delta_pp": round(delta, 2),
                    "direction": "pushes_risk_up" if delta > 0 else "pushes_risk_down",
                }
            )
        rows.sort(key=lambda r: abs(r["delta_pp"]), reverse=True)
        return {
            "region": region,
            "base_probability_pct": round(base * 100, 1),
            "attributions": rows,
            "methodology": config.EXPLAINABILITY_METHODOLOGY,
        }