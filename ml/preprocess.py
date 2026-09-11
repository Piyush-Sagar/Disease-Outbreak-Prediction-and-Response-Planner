"""Preprocessing pipeline: clean and validate the raw observation dataset.

Used identically by the training script (`ml/train.py`) and the serving
backend (`backend/app/services/predictions.py`) so train/serve stay aligned.
"""

import pandas as pd

from . import config

# Columns required in any observation dataset (disease-specific pipeline).
REQUIRED_COLUMNS = [
    "date",
    "region",
    "latitude",
    "longitude",
    "population",
    "reported_cases",
    "previous_week_cases",
    "previous_month_cases",
    "deaths",
    "temperature",
    "rainfall",
    "humidity",
    "water_accumulation_index",
    "population_density",
]

# Continuous numeric columns used downstream.
NUMERIC_COLUMNS = [
    "latitude",
    "longitude",
    "population",
    "reported_cases",
    "previous_week_cases",
    "previous_month_cases",
    "deaths",
    "temperature",
    "rainfall",
    "humidity",
    "water_accumulation_index",
    "population_density",
]


def normalize_region_names(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise region name casing/spacing to a canonical form."""
    if "region" not in df.columns:
        return df
    df = df.copy()
    df["region"] = df["region"].astype(str).str.strip().str.title()
    return df


def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Parse the date column and enforce chronological order per region."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    if df["date"].isna().any():
        raise ValueError("Unparseable dates found; cannot build time series.")
    return df.sort_values(["region", "date"]).reset_index(drop=True)


def deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    """Drop exact duplicate rows and (region, date) duplicates."""
    df = df.copy()
    df = df.drop_duplicates()
    df = df.drop_duplicates(subset=["region", "date"], keep="last")
    return df.reset_index(drop=True)


def impute_missing(df: pd.DataFrame) -> pd.DataFrame:
    """
    Impute missing numeric values with the region-level median for the
    disease/environment columns. Rows that are fully empty are dropped.
    """
    df = df.copy()
    # Drop rows with no usable disease signal at all.
    df = df[~df["reported_cases"].isna()] if "reported_cases" in df.columns else df
    available_numeric = [c for c in NUMERIC_COLUMNS if c in df.columns]
    group = df.groupby("region")[available_numeric].transform(
        lambda s: s.fillna(s.median())
    )
    df[available_numeric] = group.fillna(group.median())
    return df.reset_index(drop=True)


def drop_warmup_rows(df: pd.DataFrame, warmup_weeks: int = None) -> pd.DataFrame:
    """
    Remove the first `warmup_weeks` rows of every region so that rolling
    features and baselines have enough history (avoids NaN/zero baselines).
    """
    warmup = warmup_weeks if warmup_weeks is not None else config.WARMUP_WEEKS
    if df.empty:
        return df
    chunks = [g.iloc[warmup:] for _, g in df.groupby("region", sort=False)]
    return pd.concat(chunks, ignore_index=True)


def preprocess(df: pd.DataFrame, drop_warmup: bool = True) -> pd.DataFrame:
    """Run the full preprocessing pipeline (dedupe -> dates -> impute)."""
    df = normalize_region_names(df)
    df = deduplicate(df)
    df = parse_dates(df)
    df = impute_missing(df)
    if drop_warmup:
        df = drop_warmup_rows(df)
    return df


def load_dataset(path: str = None) -> pd.DataFrame:
    """Load and preprocess the dengue observation CSV."""
    path = path or config.DENGUE_DATA_CSV
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Dataset missing required columns: {missing}")
    return preprocess(df)