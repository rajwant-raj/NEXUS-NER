"""
NEXUS-NER | Module C — Model Training Script
=============================================
Trains a Logistic Regression (baseline) and a Random Forest (primary)
on the generated synthetic dataset, evaluates both, selects the best
model by recall-weighted F1 score, and serialises it.

⚠️  Trained on SYNTHETIC data — do NOT present these metrics as
    real-world accuracy.

Usage
-----
    python services/ai/training/train.py

Outputs
-------
    services/ai/models/risk_model.pkl
    services/ai/models/model_metadata.json
    services/ai/models/confusion_matrix.png
"""

import json
import sys
import time
import warnings
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
AI_ROOT    = Path(__file__).resolve().parent.parent
DATA_FILE  = AI_ROOT / "data" / "processed" / "dataset.csv"
MODELS_DIR = AI_ROOT / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH    = MODELS_DIR / "risk_model.pkl"
METADATA_PATH = MODELS_DIR / "model_metadata.json"
CM_PATH       = MODELS_DIR / "confusion_matrix.png"

# ---------------------------------------------------------------------------
# Feature / target columns
# ---------------------------------------------------------------------------
sys.path.insert(0, str(AI_ROOT))
from features.feature_engineering import (
    RAW_FEATURE_COLUMNS,
    RoadFeatureEngineer,
    FEATURE_COLUMNS,
)

TARGET = "disruption"


# ---------------------------------------------------------------------------
# Data loading & splitting
# ---------------------------------------------------------------------------

def load_and_split(path: Path):
    """Load CSV and return stratified train / val / test splits."""
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {path}\n"
            "Run  python data/generate_dataset.py  first."
        )

    df = pd.read_csv(path)
    print(f"📂 Loaded dataset: {len(df):,} rows, {len(df.columns)} columns")
    print(f"   Disruption rate: {df[TARGET].mean():.1%}")

    X = df[RAW_FEATURE_COLUMNS]
    y = df[TARGET]

    # 70 / 15 / 15 stratified split — no data leakage
    sss1 = StratifiedShuffleSplit(n_splits=1, test_size=0.30, random_state=42)
    train_idx, temp_idx = next(sss1.split(X, y))

    X_train, y_train = X.iloc[train_idx], y.iloc[train_idx]
    X_temp,  y_temp  = X.iloc[temp_idx],  y.iloc[temp_idx]

    sss2 = StratifiedShuffleSplit(n_splits=1, test_size=0.50, random_state=42)
    val_idx, test_idx = next(sss2.split(X_temp, y_temp))

    X_val,  y_val  = X_temp.iloc[val_idx],  y_temp.iloc[val_idx]
    X_test, y_test = X_temp.iloc[test_idx], y_temp.iloc[test_idx]

    print(f"\n   Train : {len(X_train):,} rows")
    print(f"   Val   : {len(X_val):,} rows")
    print(f"   Test  : {len(X_test):,} rows")

    return X_train, X_val, X_test, y_train, y_val, y_test


# ---------------------------------------------------------------------------
# Model definitions
# ---------------------------------------------------------------------------

def _make_logistic_pipeline() -> Pipeline:
    return Pipeline([
        ("engineer", RoadFeatureEngineer()),
        ("scaler",   StandardScaler()),
        ("clf",      LogisticRegression(
            max_iter=1000,
            class_weight="balanced",   # handles class imbalance
            random_state=42,
        )),
    ])


def _make_rf_pipeline() -> Pipeline:
    return Pipeline([
        ("engineer", RoadFeatureEngineer()),
        ("clf",      RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=10,
            min_samples_leaf=4,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        )),
    ])


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def evaluate(name: str, pipeline, X, y, split_name: str = "Test") -> dict:
    """Evaluate a pipeline and print a report."""
    y_pred  = pipeline.predict(X)
    y_proba = pipeline.predict_proba(X)[:, 1]

    acc  = accuracy_score(y, y_pred)
    prec = precision_score(y, y_pred, zero_division=0)
    rec  = recall_score(y, y_pred, zero_division=0)
    f1   = f1_score(y, y_pred, zero_division=0)
    auc  = roc_auc_score(y, y_proba)

    print(f"\n  [{name}] — {split_name} metrics")
    print(f"    Accuracy  : {acc:.4f}")
    print(f"    Precision : {prec:.4f}")
    print(f"    Recall    : {rec:.4f}   ← priority metric (miss fewer real risks)")
    print(f"    F1 Score  : {f1:.4f}")
    print(f"    ROC-AUC   : {auc:.4f}")

    return {
        "model": name,
        "split": split_name,
        "accuracy":  round(acc,  4),
        "precision": round(prec, 4),
        "recall":    round(rec,  4),
        "f1":        round(f1,   4),
        "roc_auc":   round(auc,  4),
    }


def save_confusion_matrix(pipeline, X_test, y_test, model_name: str, path: Path):
    """Save a confusion matrix heatmap."""
    y_pred = pipeline.predict(X_test)
    cm = confusion_matrix(y_test, y_pred)

    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues",
        xticklabels=["No Disruption", "Disruption"],
        yticklabels=["No Disruption", "Disruption"],
        ax=ax,
    )
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(f"Confusion Matrix — {model_name}")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"\n📊 Confusion matrix saved → {path}")


# ---------------------------------------------------------------------------
# Main training loop
# ---------------------------------------------------------------------------

def train():
    print("🚀 NEXUS-NER | Model Training")
    print("=" * 55)

    X_train, X_val, X_test, y_train, y_val, y_test = load_and_split(DATA_FILE)

    candidates = {
        "Logistic Regression": _make_logistic_pipeline(),
        "Random Forest":       _make_rf_pipeline(),
    }

    val_metrics = {}
    test_metrics = {}
    trained     = {}

    for name, pipeline in candidates.items():
        print(f"\n{'─'*55}")
        print(f"  Training: {name} …")
        t0 = time.time()
        pipeline.fit(X_train, y_train)
        elapsed = time.time() - t0
        print(f"  Trained in {elapsed:.1f}s")

        val_m  = evaluate(name, pipeline, X_val,  y_val,  split_name="Validation")
        test_m = evaluate(name, pipeline, X_test, y_test, split_name="Test")

        val_metrics[name]  = val_m
        test_metrics[name] = test_m
        trained[name]      = pipeline

    # ── Model selection ────────────────────────────────────────────────────
    print(f"\n{'─'*55}")
    print("  Model Selection (by Validation F1 Score)")
    best_name = max(val_metrics, key=lambda k: val_metrics[k]["f1"])
    best_pipeline = trained[best_name]
    print(f"  ✅  Winner: {best_name}  (F1={val_metrics[best_name]['f1']:.4f})")

    # ── Serialise ──────────────────────────────────────────────────────────
    joblib.dump(best_pipeline, MODEL_PATH)
    print(f"\n💾 Model saved → {MODEL_PATH}")

    # ── Feature importances (Random Forest only) ───────────────────────────
    feature_importances = {}
    if best_name == "Random Forest":
        clf = best_pipeline.named_steps["clf"]
        fi  = dict(zip(FEATURE_COLUMNS, clf.feature_importances_))
        feature_importances = dict(
            sorted(fi.items(), key=lambda x: x[1], reverse=True)
        )
        print("\n  Top-10 Feature Importances:")
        for feat, imp in list(feature_importances.items())[:10]:
            bar = "█" * int(imp * 50)
            print(f"    {feat:30s} {imp:.4f}  {bar}")

    # ── Confusion matrix ───────────────────────────────────────────────────
    save_confusion_matrix(best_pipeline, X_test, y_test, best_name, CM_PATH)

    # ── Metadata ───────────────────────────────────────────────────────────
    metadata = {
        "model_type":       best_name,
        "trained_at":       time.strftime("%Y-%m-%dT%H:%M:%S"),
        "dataset_file":     str(DATA_FILE),
        "n_train":          int(len(X_train)),
        "n_val":            int(len(X_val)),
        "n_test":           int(len(X_test)),
        "features":         FEATURE_COLUMNS,
        "target":           TARGET,
        "metric_priority":  "recall (minimise missed disruptions)",
        "validation_metrics": val_metrics[best_name],
        "test_metrics":       test_metrics[best_name],
        "all_model_results":  {
            k: {"validation": val_metrics[k], "test": test_metrics[k]}
            for k in val_metrics
        },
        "feature_importances": feature_importances,
        "disclaimer": (
            "⚠️  This model was trained on SYNTHETIC data generated for "
            "prototype purposes. Metrics do NOT represent real-world performance. "
            "Replace with real operational data before production deployment."
        ),
    }

    with open(METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"📋 Metadata saved → {METADATA_PATH}")

    print(f"\n{'='*55}")
    print("✅ Training complete.")
    print(f"   Best model : {best_name}")
    print(f"   Test F1    : {test_metrics[best_name]['f1']:.4f}")
    print(f"   Test Recall: {test_metrics[best_name]['recall']:.4f}")
    print(f"   Test AUC   : {test_metrics[best_name]['roc_auc']:.4f}\n")


if __name__ == "__main__":
    train()
