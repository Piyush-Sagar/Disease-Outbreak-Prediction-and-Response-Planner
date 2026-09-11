"""Model evaluation: metrics, confusion matrices, ROC curves, feature importance.

Produces:
  - a metrics summary (accuracy / precision / recall / F1 / ROC-AUC)
  - confusion-matrix PNGs per model
  - a combined ROC-curve PNG
  - a random-forest feature-importance PNG + CSV
"""

import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn.metrics as skm
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from . import config


def evaluate_model(y_true, y_prob, model_name: str) -> dict:
    """Return standard metrics for a binary classifier given probabilities."""
    y_pred = (np.asarray(y_prob) >= 0.5).astype(int)
    y_true = np.asarray(y_true)
    return {
        "model": model_name,
        "accuracy": round(accuracy_score(y_true, y_pred), 4),
        "precision": round(precision_score(y_true, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y_true, y_pred, zero_division=0), 4),
        "f1": round(f1_score(y_true, y_pred, zero_division=0), 4),
        "roc_auc": round(roc_auc_score(y_true, y_prob), 4),
        "n_train": len(y_true),
        "n_positive": int(y_true.sum()),
    }


def plot_confusion_matrix(y_true, y_prob, model_name: str, save_path: str) -> None:
    """Save a labelled confusion-matrix figure."""
    y_pred = (np.asarray(y_prob) >= 0.5).astype(int)
    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(4.5, 4))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks([0, 1], labels=["No event", "Event"])
    ax.set_yticks([0, 1], labels=["No event", "Event"])
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(f"Confusion Matrix - {model_name}")
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center", fontsize=14,
                    color="white" if cm[i, j] > cm.max() / 2 else "black")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_roc_curves(data: dict, save_path: str) -> None:
    """`data`: {model_label: (y_true, y_prob)}. Draws a combined ROC figure."""
    fig, ax = plt.subplots(figsize=(5.5, 5))
    for label, (y_true, y_prob) in data.items():
        fpr, tpr, _ = skm.roc_curve(y_true, y_prob)
        auc = roc_auc_score(y_true, y_prob)
        ax.plot(fpr, tpr, label=f"{label} (AUC={auc:.3f})")
    ax.plot([0, 1], [0, 1], "k--", alpha=0.4, label="Chance")
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.set_title("ROC Curves (held-out test weeks)")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_feature_importance(importances: dict, save_path: str) -> None:
    """Horizontal bar chart of model feature importances (sorted)."""
    items = sorted(importances.items(), key=lambda kv: kv[1], reverse=True)
    labels = [k for k, _ in items]
    values = [v for v, _ in items]
    fig, ax = plt.subplots(figsize=(7, 5))
    colors = plt.cm.viridis(np.linspace(0.2, 0.9, len(values)))
    ax.barh(range(len(values)), values, color=colors)
    ax.set_yticks(range(len(values)), labels=labels)
    ax.set_xlabel("Mean decrease in impurity (Gini)")
    ax.set_title("Random Forest - Feature Importance")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def save_metrics(metrics: list[dict], path: str) -> None:
    """Persist model-comparison metrics as JSON."""
    with open(path, "w") as f:
        json.dump({"models": metrics}, f, indent=2)


def save_feature_importance_csv(importances: dict, path: str) -> None:
    rows = [{"feature": k, "importance": round(v, 4)} for k, v in
            sorted(importances.items(), key=lambda kv: kv[1], reverse=True)]
    pd.DataFrame(rows).to_csv(path, index=False)