"""High-incidence-event label construction.

The prototype defines a label column called `high_incidence_event` that is
used as a PROJECT-DEFINED proxy for outbreak risk:

    high_incidence_event = 1  iff
        weekly case growth rate > growth_threshold          AND
        weekly cases >= case_multiplier x regional baseline

This is NOT an official epidemiological outbreak definition. The definition
is configurable through `ml/config.py` and documented in README + docs.
"""

import pandas as pd

from . import config


def trailing_baseline(df: pd.DataFrame) -> pd.Series:
    """
    Regional trailing baseline = median of the previous `baseline_window_weeks`
    weeks (shift to exclude the current week; no future information used).
    """
    window = config.LABEL_CONFIG["baseline_window_weeks"]
    return (
        df.groupby("region")["reported_cases"]
        .transform(lambda s: s.shift(1).rolling(window=window, min_periods=1).median())
        .reindex(df.index)
    )


def compute_label(df: pd.DataFrame, horizon: int = None) -> pd.DataFrame:
    """
    Add the `high_incidence_event` column (0/1) using only past information.

    The label at week t is the high-incidence event at week t + horizon
    (default 1): we predict events one week in advance. Rows where the
    event cannot be computed (first weeks, or last `horizon` weeks per
    region) get NaN and are dropped by the caller.
    """
    horizon = horizon if horizon is not None else config.PREDICT_HORIZON_WEEKS
    out = df.copy()
    baseline = trailing_baseline(out)
    threshold = config.LABEL_CONFIG["growth_threshold"]
    multiplier = config.LABEL_CONFIG["case_multiplier"]

    cases_above_baseline = out["reported_cases"] >= (multiplier * baseline)
    growth_high = out["case_growth_rate"] > threshold
    out["_event_now"] = (cases_above_baseline & growth_high).astype(int)

    out[config.LABEL_COLUMN] = out.groupby("region")["_event_now"].transform(
        lambda s: s.shift(-horizon)
    )
    out = out.drop(columns=["_event_now"])
    return out


def label_description() -> str:
    """Human-readable description of the label definition."""
    return config.LABEL_METHODOLOGY