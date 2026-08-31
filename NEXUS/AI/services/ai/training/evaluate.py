"""
NEXUS-NER | Module C — Model Evaluation Script
===============================================
Loads the saved model and prints a full evaluation report.
Can evaluate on any CSV file that contains the raw feature columns.

Usage
-----
    python services/ai/training/evaluate.py
    python services/ai/training/evaluate.py --data path/to/data.csv
"""

import argparse
import json
import sys
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
    roc_curve,
)

AI_ROOT    = Path(__file__).resolve().parent.parent
MODEL_PATH = AI_ROOT / "models" / "risk_model.pkl"
META_PATH  = AI_ROOT / "models" / "model_metadata.json"
DATA_FILE  = AI_ROOT / "data" / "processed" / "dataset.csv"

sys.path.insert(0, str(AI_ROOT))
from features.feature_engineering import RAW_FEATURE_COLUMNS

TARGET = "disruption"


def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model not found: {MODEL_PATH}\n"
            "Run  python training/train.py  first."
        )
    model = joblib.load(MODEL_PATH)
    print(f"✅ Loaded model from {MODEL_PATH}")
    return model


def load_metadata():
    if META_PATH.exists():
        with open(META_PATH) as f:
            return json.load(f)
    return {}


def print_report(y_true, y_pred, y_proba):
    print("\n" + "=" * 55)
    print("  CLASSIFICATION REPORT")
    print("=" * 55)
    print(classification_report(
        y_true, y_pred,
        target_names=["No Disruption", "Disruption"]
    ))

    acc = accuracy_score(y_true, y_pred)
    auc = roc_auc_score(y_true, y_proba)
    print(f"  Accuracy  : {acc:.4f}")
    print(f"  ROC-AUC   : {auc:.4f}")


def plot_roc(y_true, y_proba, save_path: Path):
    fpr, tpr, _ = roc_curve(y_true, y_proba)
    auc = roc_auc_score(y_true, y_proba)

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(fpr, tpr, color="#4361ee", lw=2, label=f"ROC (AUC = {auc:.3f})")
    ax.plot([0, 1], [0, 1], color="grey", lw=1, linestyle="--", label="Random")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC Curve — Disruption Prediction")
    ax.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"📊 ROC curve saved → {save_path}")


def plot_confusion(y_true, y_pred, save_path: Path):
    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues",
        xticklabels=["No Disruption", "Disruption"],
        yticklabels=["No Disruption", "Disruption"],
        ax=ax,
    )
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("Confusion Matrix")
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"📊 Confusion matrix saved → {save_path}")


def main(data_path: Path = DATA_FILE):
    print("🔍 NEXUS-NER | Model Evaluation")
    print("=" * 55)

    model = load_model()
    meta  = load_metadata()

    if meta:
        print(f"\n📋 Model Info")
        print(f"   Type         : {meta.get('model_type', 'Unknown')}")
        print(f"   Trained at   : {meta.get('trained_at', 'Unknown')}")
        print(f"   N train      : {meta.get('n_train', '?'):,}")
        print(f"   ⚠️  {meta.get('disclaimer', '')[:80]}…")

    if not data_path.exists():
        raise FileNotFoundError(f"Data not found: {data_path}")

    df = pd.read_csv(data_path)
    X  = df[RAW_FEATURE_COLUMNS]
    y  = df[TARGET]

    print(f"\n📂 Evaluating on: {data_path.name}  ({len(df):,} rows)")

    y_pred  = model.predict(X)
    y_proba = model.predict_proba(X)[:, 1]

    print_report(y, y_pred, y_proba)

    models_dir = AI_ROOT / "models"
    plot_roc(y, y_proba, models_dir / "roc_curve.png")
    plot_confusion(y, y_pred, models_dir / "confusion_matrix_eval.png")

    print("\n✅ Evaluation complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate NEXUS-NER disruption model")
    parser.add_argument("--data", type=Path, default=DATA_FILE,
                        help="Path to CSV dataset for evaluation")
    args = parser.parse_args()
    main(data_path=args.data)
