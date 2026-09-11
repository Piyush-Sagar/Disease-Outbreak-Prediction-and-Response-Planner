"""Prediction helper: loads saved artifacts and returns outbreak probabilities.

Used by the backend to serve predictions without retraining.
"""

import os
import sys

if not __package__:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import joblib
import numpy as np

from ml import config
from ml.features import FEATURE_COLUMNS


class OutbreakPredictor:
    """
    Thin wrapper over the saved scikit-learn models.

    Exposes `predict_proba(features)` returning the positive-class
    probability (0-1). The web dashboard multiplies this by 100 to show
    "Predicted Outbreak Risk".
    """

    def __init__(self, artifacts_dir: str = None):
        self.artifacts_dir = artifacts_dir or config.ARTIFACTS_DIR
        self.model_rf = joblib.load(f"{self.artifacts_dir}/model_rf.joblib")
        self.model_rf_unweighted = joblib.load(f"{self.artifacts_dir}/model_rf_unweighted.joblib")
        self.model_lr = joblib.load(f"{self.artifacts_dir}/model_lr.joblib")
        self.scaler = joblib.load(f"{self.artifacts_dir}/scaler.joblib")

    def _featurize(self, X) -> np.ndarray:
        """Ensure X is an ordered 2D array matching the trained feature order."""
        if isinstance(X, dict):
            X = [X[f] for f in FEATURE_COLUMNS]
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X.reshape(1, -1)
        if X.shape[1] != len(FEATURE_COLUMNS):
            raise ValueError(
                f"Expected {len(FEATURE_COLUMNS)} features, got {X.shape[1]}"
            )
        return X

    def predict_proba(self, X):
        X = self.scaler.transform(self._featurize(X))
        return self.model_rf.predict_proba(X)[:, 1]

    def predict_proba_main(self, X) -> float:
        """
        Probability (0-1) from the Random Forest (main serving model).

        Uses the unweighted RF so that risk percentages reflect the observed
        base rate of high-incidence events rather than class-balanced shares.
        """
        X = self._featurize(X)
        return float(self.model_rf_unweighted.predict_proba(X)[:, 1][0])

    def predict_proba_baseline(self, X) -> float:
        """Probability (0-1) from the Logistic Regression (baseline)."""
        return float(self.model_lr.predict_proba(self.scaler.transform(self._featurize(X)))[:, 1][0])


def artifacts_exist(artifacts_dir: str = None) -> bool:
    """True when all required model artifacts are present."""
    d = artifacts_dir or config.ARTIFACTS_DIR
    required = ["model_rf.joblib", "model_lr.joblib", "scaler.joblib"]
    return all(os.path.exists(os.path.join(d, f)) for f in required)


if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from ml.label import compute_label
    from ml.preprocess import load_dataset
    from ml.features import build_features, feature_matrix

    predictor = OutbreakPredictor()
    df = load_dataset()
    df = build_features(df)
    df = compute_label(df)
    latest = df.groupby("region").tail(1)
    print(f"{'Region':<12}{'Pred(prob)':>10}")
    for _, row in latest.iterrows():
        prob = predictor.predict_proba_main(feature_matrix(row.to_frame().T).iloc[0].to_dict())
        print(f"{row['region']:<12}{prob*100:>9.1f}%")