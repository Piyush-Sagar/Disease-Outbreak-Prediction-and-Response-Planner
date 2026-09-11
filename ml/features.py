"""Feature engineering for the outbreak-prediction pipeline.

Every feature is computed from information available at, or before, the
observation week only (rolling windows, lags). No future information is
leaked into the features, which is what makes the time-based evaluation fair.
"""

import numpy as np
import pandas as pd

from . import config

FEATURE_COLUMNS = [
    "cases_7d_avg",
    "cases_14d_avg",
    "cases_30d_avg",
    "case_growth_rate",
    "rainfall_14d_avg",
    "temperature_14d_avg",
    "humidity_14d_avg",
    "water_accumulation_index",
    "population_density",
    "cases_lag1",
    "cases_lag2",
    "cases_lag3",
    "cases_lag4",
    "season_sin",
    "season_cos",
    "weekly_incidence_per_100k",
    "cases_30d_per_100k",
]


def _rolling_mean(df: pd.DataFrame, column: str, window: int) -> pd.Series:
    """Rolling mean grouped by region (min_periods=window -> NaN in warmup)."""
    return (
        df.groupby("region")[column]
        .transform(lambda s: s.rolling(window=window, min_periods=window).mean())
    )


def _case_growth_rate(df: pd.DataFrame, baseline_weeks: int) -> pd.Series:
    """Current cases vs the average of the previous `baseline_weeks` weeks."""
    grouped = df.groupby("region", sort=False)["reported_cases"]
    baseline = grouped.transform(
        lambda s: s.shift(1).rolling(window=baseline_weeks, min_periods=1).mean()
    )
    growth = (df["reported_cases"] - baseline) / baseline.replace(0, np.nan)
    return growth.clip(lower=-1.0, upper=10.0)


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Augment the preprocessed observation frame with engineered features."""
    out = df.copy()

    out["cases_7d_avg"] = _rolling_mean(out, "reported_cases", 7)
    out["cases_14d_avg"] = _rolling_mean(out, "reported_cases", 14)
    out["cases_30d_avg"] = _rolling_mean(out, "reported_cases", 30)

    out["case_growth_rate"] = _case_growth_rate(
        out, config.LABEL_CONFIG["growth_baseline_weeks"]
    )

    out["rainfall_14d_avg"] = _rolling_mean(out, "rainfall", 14)
    out["temperature_14d_avg"] = _rolling_mean(out, "temperature", 14)
    out["humidity_14d_avg"] = _rolling_mean(out, "humidity", 14)

    for lag in range(1, 5):
        out[f"cases_lag{lag}"] = out.groupby("region")["reported_cases"].shift(lag)

    # Seasonality: sin/cos of week-of-year so the model can learn annual cycles.
    weekday = out["date"].dt.isocalendar().week.astype(float)
    out["season_sin"] = np.sin(2 * np.pi * weekday / 52)
    out["season_cos"] = np.cos(2 * np.pi * weekday / 52)

    # Per-capita metrics: make the model distinguish regions by burden level.
    out["weekly_incidence_per_100k"] = out["reported_cases"] * 1e5 / out["population"]
    out["cases_30d_per_100k"] = out["cases_30d_avg"] * 1e5 / out["population"]

    return out


def time_based_split(df: pd.DataFrame, test_ratio: float = None):
    """Split chronologically per region: first X% train, last Y% test."""
    ratio = test_ratio if test_ratio is not None else config.TRAIN_CONFIG["test_ratio"]
    train_rows, test_rows = [], []
    for _, group in df.groupby("region", sort=False):
        n = len(group)
        cut = int(n * (1 - ratio))
        train_rows.append(group.iloc[:cut])
        test_rows.append(group.iloc[cut:])
    train = pd.concat(train_rows, ignore_index=True)
    test = pd.concat(test_rows, ignore_index=True)
    return train, test


def feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Return the feature columns as a clean matrix (drops first 4 rows/lag NaNs)."""
    return df[FEATURE_COLUMNS].copy()