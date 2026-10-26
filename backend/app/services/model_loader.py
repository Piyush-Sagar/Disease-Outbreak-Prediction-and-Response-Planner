"""Model loading + latest-feature serving.

This service is the single bridge between the trained `ml` package and the
FastAPI layer. It loads the saved artifacts once, then serves per-region
outbreak probabilities together with explanatory feature values.
"""

from dataclasses import dataclass, field

from ml.config import risk_category
from ml.features import FEATURE_COLUMNS, build_features, feature_matrix
from ml.predict import OutbreakPredictor
from ml.preprocess import load_dataset

from .. import config


@dataclass
class PredictionRecord:
    region: str
    region_name: str
    observation_date: str
    prediction_date: str
    probability: float
    probability_lr: float
    risk_category: str
    features: dict = field(default_factory=dict)


class ModelService:

    def __init__(self, artifacts_dir: str | None = None):
        self.predictor = OutbreakPredictor(artifacts_dir or config.MODEL_ARTIFACTS_DIR)
        self._feature_frame = None
        self._latest_features: dict[str, dict] = {}
        self._loaded_until: str | None = None

    def _ensure_feature_frame(self):
        if self._feature_frame is None:
            df = load_dataset()
            self._feature_frame = build_features(df)
        return self._feature_frame

    def latest_regional_features(self) -> list[dict]:
        """One feature vector per region, built from info up to the latest week."""
        if not self._latest_features:
            frame = self._ensure_feature_frame()
            self._latest_features = {
                row["region"]: feature_matrix(row.to_frame().T).iloc[0].to_dict()
                for _, row in frame.groupby("region", sort=False).tail(1).iterrows()
            }
        return [{"region": name, **feats} for name, feats in self._latest_features.items()]

    def latest_observation_date(self) -> str:
        if self._loaded_until is None:
            frame = self._ensure_feature_frame()
            self._loaded_until = str(frame["date"].max().date())
        return self._loaded_until

    def prediction_date_for(self, observation_date: str) -> str:
        import datetime as dt

        return str((dt.date.fromisoformat(observation_date) + dt.timedelta(weeks=1)))

    def predict_all(self) -> list[PredictionRecord]:
        obs_date = self.latest_observation_date()
        pred_date = self.prediction_date_for(obs_date)
        records = []
        for entry in self.latest_regional_features():
            region = entry["region"]
            feats = {k: entry[k] for k in FEATURE_COLUMNS}
            prob = self.predictor.predict_proba_main(feats)
            prob_lr = self.predictor.predict_proba_baseline(feats)
            records.append(
                PredictionRecord(
                    region=region,
                    region_name=region,
                    observation_date=obs_date,
                    prediction_date=pred_date,
                    probability=prob,
                    probability_lr=prob_lr,
                    risk_category=config.risk_category(prob * 100),
                    features=feats,
                )
            )
        return records