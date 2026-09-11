"""Reproducible training script.

Usage:  python train.py

Pipeline:
  1. Load + preprocess observations
  2. Build features and the high-incidence-event label
  3. Time-based train/test split (no temporal leakage)
  4. Train LogisticRegression (baseline) + RandomForestClassifier (main)
  5. Evaluate both on held-out test weeks
  6. Save artifacts + metrics + figures
  7. Print the model-comparison table
"""

import json
import os
import sys
import time

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml import config  # noqa: E402
from ml import evaluate as evaluate_mod  # noqa: E402
from ml.features import FEATURE_COLUMNS, build_features, feature_matrix, time_based_split  # noqa: E402
from ml.label import compute_label  # noqa: E402
from ml.preprocess import load_dataset  # noqa: E402


def prepare_data() -> pd.DataFrame:
    """Full feature+label construction; rows with incomplete features dropped."""
    df = load_dataset()
    df = build_features(df)
    df = compute_label(df)
    complete = df.dropna(subset=FEATURE_COLUMNS).copy()
    # Drop feature+label NaN rows (rolling/lag warmup).
    missing_label = complete[complete[config.LABEL_COLUMN].isna()]
    if not missing_label.empty:
        complete = complete.dropna(subset=[config.LABEL_COLUMN])

    label_col = config.LABEL_COLUMN
    print(f"Observations after preprocessing: {len(df)}")
    print(f"Rows with complete features:       {len(complete)}")
    print("Label (high-incidence-event) distribution:")
    print(complete[label_col].value_counts().to_string())
    return complete


def main():
    t0 = time.time()
    os.makedirs(config.ARTIFACTS_DIR, exist_ok=True)
    os.makedirs(config.FIGURES_DIR, exist_ok=True)

    data = prepare_data()
    label_col = config.LABEL_COLUMN

    train, test = time_based_split(data, test_ratio=config.TRAIN_CONFIG["test_ratio"])
    print(f"\nTrain rows: {len(train)}, Test rows: {len(test)}")

    X_train = feature_matrix(train).to_numpy()
    y_train = train[label_col].to_numpy()
    X_test = feature_matrix(test).to_numpy()
    y_test = test[label_col].to_numpy()

    scaler = StandardScaler().fit(X_train)
    X_train_s = scaler.transform(X_train)
    X_test_s = scaler.transform(X_test)

    rs = config.TRAIN_CONFIG["random_state"]

    # ── Baseline: Logistic Regression ──
    lr = LogisticRegression(
        max_iter=config.TRAIN_CONFIG["lr_max_iter"],
        class_weight="balanced",
        random_state=rs,
    )
    lr.fit(X_train_s, y_train)
    prob_lr = lr.predict_proba(X_test_s)[:, 1]
    metrics_lr = evaluate_mod.evaluate_model(y_test, prob_lr, "Logistic Regression")

    # ── Main model: Random Forest ──
    rf = RandomForestClassifier(
        n_estimators=config.TRAIN_CONFIG["rf_n_estimators"],
        max_depth=config.TRAIN_CONFIG["rf_max_depth"],
        min_samples_leaf=config.TRAIN_CONFIG["rf_min_samples_leaf"],
        class_weight="balanced",
        oob_score=True,
        random_state=rs,
        n_jobs=-1,
    )
    rf.fit(X_train, y_train)  # note: RF is scale-invariant, so raw features
    prob_rf = rf.predict_proba(X_test)[:, 1]
    metrics_rf = evaluate_mod.evaluate_model(y_test, prob_rf, "Random Forest")

    # ── Unweighted RF for realistic base-rate probabilities ──
    rf_uw = RandomForestClassifier(
        n_estimators=config.TRAIN_CONFIG["rf_n_estimators"],
        max_depth=config.TRAIN_CONFIG["rf_max_depth"],
        min_samples_leaf=config.TRAIN_CONFIG["rf_min_samples_leaf"],
        oob_score=True,
        random_state=rs,
        n_jobs=-1,
    )
    rf_uw.fit(X_train, y_train)
    prob_rf_uw = rf_uw.predict_proba(X_test)[:, 1]
    metrics_rf_uw = evaluate_mod.evaluate_model(y_test, prob_rf_uw, "Random Forest (unweighted)")

    # ── Persist artifacts ──
    import joblib

    joblib.dump(rf, f"{config.ARTIFACTS_DIR}/model_rf.joblib")
    joblib.dump(rf_uw, f"{config.ARTIFACTS_DIR}/model_rf_unweighted.joblib")
    joblib.dump(lr, f"{config.ARTIFACTS_DIR}/model_lr.joblib")
    joblib.dump(scaler, f"{config.ARTIFACTS_DIR}/scaler.joblib")

    # ── Evaluation outputs ──
    metrics = [metrics_lr, metrics_rf, metrics_rf_uw]
    evaluate_mod.save_metrics(metrics, f"{config.ARTIFACTS_DIR}/metrics.json")

    evaluate_mod.plot_roc_curves(
        {"Logistic Regression": (y_test, prob_lr),
         "Random Forest": (y_test, prob_rf),
         "RF (unweighted)": (y_test, prob_rf_uw)},
        f"{config.FIGURES_DIR}/roc_curve.png",
    )
    evaluate_mod.plot_confusion_matrix(
        y_test, prob_lr, "Logistic Regression",
        f"{config.FIGURES_DIR}/confusion_matrix_lr.png",
    )
    evaluate_mod.plot_confusion_matrix(
        y_test, prob_rf, "Random Forest",
        f"{config.FIGURES_DIR}/confusion_matrix_rf.png",
    )
    evaluate_mod.plot_confusion_matrix(
        y_test, prob_rf_uw, "RF (unweighted)",
        f"{config.FIGURES_DIR}/confusion_matrix_rf_uw.png",
    )

    importance = {f: float(v) for f, v in zip(FEATURE_COLUMNS, rf.feature_importances_)}
    evaluate_mod.plot_feature_importance(importance, f"{config.FIGURES_DIR}/feature_importance.png")
    evaluate_mod.save_feature_importance_csv(importance, f"{config.ARTIFACTS_DIR}/feature_importance.csv")

    # ── Metadata ──
    metadata = {
        "disease": config.DISEASE,
        "label_column": label_col,
        "label_definition": config.LABEL_METHODOLOGY,
        "features": FEATURE_COLUMNS,
        "trained_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "random_state": rs,
        "oob_score": float(rf.oob_score_),
    }
    with open(f"{config.ARTIFACTS_DIR}/metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    # ── Pretty print ──
    print("\n" + "=" * 62)
    print("  MODEL COMPARISON (held-out test weeks)")
    print("=" * 62)
    header = f"{'Model':<24}{'Acc':>7}{'Prec':>7}{'Rec':>7}{'F1':>7}{'AUC':>7}"
    print(header)
    print("-" * len(header))
    for m in metrics:
        print(
            f"{m['model']:<24}{m['accuracy']:>7.3f}{m['precision']:>7.3f}"
            f"{m['recall']:>7.3f}{m['f1']:>7.3f}{m['roc_auc']:>7.3f}"
        )
    print("-" * len(header))
    print(f"RF OOB score (balanced): {rf.oob_score_:.4f}")
    print(f"RF OOB score (unweighted): {rf_uw.oob_score_:.4f}")
    print()
    print(f"Artifacts saved to   : {config.ARTIFACTS_DIR}")
    print(f"Figures saved to     : {config.FIGURES_DIR}")
    print(f"Elapsed              : {time.time() - t0:.1f}s")
    print("\nHigh-incidence-event definition (project-defined proxy, "
          "NOT official):")
    print("  " + config.LABEL_METHODOLOGY)


if __name__ == "__main__":
    main()