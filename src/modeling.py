"""
modeling.py
-----------
Churn prediction modelling pipeline.
Trains Logistic Regression and Random Forest classifiers,
evaluates them rigorously, and outputs feature importance.

Why accuracy alone is insufficient for churn prediction:
  Churn datasets are typically class-imbalanced (~26–30% positive class).
  A naive classifier predicting "no churn" for every customer would
  achieve ~74% accuracy while catching ZERO actual churners.
  In a business context, the cost of missing a churner (false negative)
  is far higher than incorrectly flagging a retained customer (false positive).
  We therefore focus on Recall (catching churners) and ROC-AUC (overall
  discrimination ability) alongside Precision and F1-score.
"""

import os
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
    roc_curve, ConfusionMatrixDisplay
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

warnings.filterwarnings("ignore")

sns.set_theme(style="whitegrid", font_scale=1.1)
FIG_DIR = os.path.join("outputs", "figures")
RPT_DIR = os.path.join("outputs", "reports")
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(RPT_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# FEATURE SELECTION
# ---------------------------------------------------------------------------
FEATURE_COLUMNS = [
    "gender_Enc", "SeniorCitizen", "Partner_Enc", "Dependents_Enc",
    "tenure", "PhoneService_Enc", "MultipleLines_Enc",
    "InternetService_Enc",
    "OnlineSecurity_Enc", "OnlineBackup_Enc", "DeviceProtection_Enc",
    "TechSupport_Enc", "StreamingTV_Enc", "StreamingMovies_Enc",
    "Contract_Enc", "PaperlessBilling_Enc", "PaymentMethod_Enc",
    "MonthlyCharges", "TotalCharges", "NumAddOns"
]
TARGET = "Churn"


def prepare_train_test(df: pd.DataFrame, test_size: float = 0.20,
                       random_state: int = 42):
    """
    Stratified train/test split to preserve churn class ratio.
    Returns (X_train, X_test, y_train, y_test, feature_names).
    """
    available = [c for c in FEATURE_COLUMNS if c in df.columns]
    X = df[available].copy()
    y = df[TARGET].copy()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size,
        random_state=random_state, stratify=y
    )
    print(f"[SPLIT] Train: {len(X_train)} samples | Test: {len(X_test)} samples")
    print(f"[SPLIT] Churn in train: {y_train.mean()*100:.1f}% | "
          f"Churn in test: {y_test.mean()*100:.1f}%")
    return X_train, X_test, y_train, y_test, available


def build_lr_pipeline() -> Pipeline:
    """Logistic Regression with imputation and scaling."""
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("model", LogisticRegression(
            max_iter=1000, random_state=42, solver="lbfgs",
            class_weight="balanced"   # handle class imbalance
        ))
    ])


def build_rf_pipeline() -> Pipeline:
    """Random Forest with imputation (no scaling needed)."""
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("model", RandomForestClassifier(
            n_estimators=200, max_depth=10, min_samples_split=10,
            random_state=42, class_weight="balanced", n_jobs=-1
        ))
    ])


def evaluate_model(model_pipeline: Pipeline,
                   X_test: pd.DataFrame,
                   y_test: pd.Series,
                   model_name: str) -> dict:
    """
    Compute and print all evaluation metrics.
    Returns metrics dict.
    """
    y_pred = model_pipeline.predict(X_test)
    y_prob = model_pipeline.predict_proba(X_test)[:, 1]

    metrics = {
        "Model": model_name,
        "Accuracy": round(accuracy_score(y_test, y_pred), 4),
        "Precision": round(precision_score(y_test, y_pred, zero_division=0), 4),
        "Recall": round(recall_score(y_test, y_pred), 4),
        "F1-Score": round(f1_score(y_test, y_pred), 4),
        "ROC-AUC": round(roc_auc_score(y_test, y_prob), 4)
    }

    print(f"\n{'='*52}")
    print(f"  MODEL EVALUATION: {model_name}")
    print(f"{'='*52}")
    for k, v in metrics.items():
        if k != "Model":
            print(f"  {k:<15}: {v}")
    print("\n  Classification Report:")
    print(classification_report(y_test, y_pred,
                                 target_names=["Retained", "Churned"]))
    return metrics


def plot_confusion_matrices(lr_pipe, rf_pipe, X_test, y_test) -> str:
    """Side-by-side confusion matrices."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    for ax, pipe, name in zip(
        axes,
        [lr_pipe, rf_pipe],
        ["Logistic Regression", "Random Forest"]
    ):
        cm = confusion_matrix(y_test, pipe.predict(X_test))
        disp = ConfusionMatrixDisplay(cm, display_labels=["Retained", "Churned"])
        disp.plot(ax=ax, colorbar=False, cmap="Blues")
        ax.set_title(f"{name}\nConfusion Matrix", fontsize=12, fontweight="bold")

    plt.suptitle("Model Comparison — Confusion Matrices", fontsize=14, fontweight="bold")
    plt.tight_layout()
    path = os.path.join(FIG_DIR, "12_confusion_matrices.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[PLOT] Saved -> {path}")
    return path


def plot_roc_curves(lr_pipe, rf_pipe, X_test, y_test) -> str:
    """ROC curves for both models."""
    fig, ax = plt.subplots(figsize=(8, 6))

    for pipe, name, color in zip(
        [lr_pipe, rf_pipe],
        ["Logistic Regression", "Random Forest"],
        ["#E63946", "#2A9D8F"]
    ):
        y_prob = pipe.predict_proba(X_test)[:, 1]
        fpr, tpr, _ = roc_curve(y_test, y_prob)
        auc = roc_auc_score(y_test, y_prob)
        ax.plot(fpr, tpr, color=color, linewidth=2,
                label=f"{name} (AUC = {auc:.3f})")

    ax.plot([0, 1], [0, 1], "k--", linewidth=1, label="Random Classifier")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate (Recall)")
    ax.set_title("ROC Curves — Churn Prediction Models", fontsize=13, fontweight="bold")
    ax.legend(loc="lower right")
    plt.tight_layout()
    path = os.path.join(FIG_DIR, "13_roc_curves.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[PLOT] Saved -> {path}")
    return path


def plot_feature_importance(rf_pipe: Pipeline,
                             feature_names: list) -> str:
    """Random Forest feature importance bar chart."""
    rf_model = rf_pipe.named_steps["model"]
    importances = rf_model.feature_importances_
    indices = np.argsort(importances)[::-1]

    top_n = min(15, len(feature_names))
    top_features = [feature_names[i] for i in indices[:top_n]]
    top_importances = importances[indices[:top_n]]

    fig, ax = plt.subplots(figsize=(10, 7))
    colors = sns.color_palette("viridis_r", top_n)
    ax.barh(range(top_n), top_importances[::-1], color=colors[::-1],
            edgecolor="black")
    ax.set_yticks(range(top_n))
    ax.set_yticklabels(top_features[::-1])
    ax.set_xlabel("Feature Importance Score")
    ax.set_title(
        "Top Feature Importances — Random Forest\n"
        "Q: Which customer attributes most predict churn?",
        fontsize=13, fontweight="bold"
    )
    plt.tight_layout()
    path = os.path.join(FIG_DIR, "14_feature_importance.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[PLOT] Saved -> {path}")
    return path


def save_model_report(metrics_list: list,
                      path: str = os.path.join(
                          RPT_DIR, "model_performance.txt")) -> None:
    """Save model performance summary to text file."""
    lines = [
        "=" * 55,
        "  CHURN PREDICTION MODEL PERFORMANCE REPORT",
        "=" * 55,
        "",
        "NOTE: These metrics are calculated from the actual held-out",
        "test set. No values are fabricated.",
        "",
        "Why accuracy alone is insufficient:",
        "  Churn is a class-imbalanced problem (~26-30% positive).",
        "  A naive 'predict no churn' model achieves ~74% accuracy",
        "  while catching zero actual churners. We must maximise:",
        "    Recall    — to catch as many churners as possible",
        "    Precision — to not waste retention spend on non-churners",
        "    F1-Score  — harmonic mean balancing both",
        "    ROC-AUC   — overall discrimination ability",
        ""
    ]
    for m in metrics_list:
        lines += [
            f"  Model     : {m['Model']}",
            f"  Accuracy  : {m['Accuracy']}",
            f"  Precision : {m['Precision']}",
            f"  Recall    : {m['Recall']}",
            f"  F1-Score  : {m['F1-Score']}",
            f"  ROC-AUC   : {m['ROC-AUC']}",
            ""
        ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[REPORT] Model performance saved -> {path}")


def add_churn_probabilities(df: pd.DataFrame,
                             rf_pipe: Pipeline,
                             feature_names: list) -> pd.DataFrame:
    """
    Add predicted churn probability from the Random Forest model
    to the main DataFrame for use in Power BI and SQL analysis.
    """
    available = [c for c in feature_names if c in df.columns]
    X = df[available].copy()
    df = df.copy()
    df["ChurnProbability"] = rf_pipe.predict_proba(X)[:, 1].round(4)
    df["PredictedChurn"] = rf_pipe.predict(X)
    print("[MODEL] ChurnProbability and PredictedChurn columns added.")
    return df


def run_modeling_pipeline(df: pd.DataFrame):
    """
    Execute full modeling pipeline.
    Returns (lr_pipe, rf_pipe, metrics_list, df_with_probs).
    """
    print("\n" + "=" * 60)
    print("  CHURN PREDICTION MODELLING PIPELINE")
    print("=" * 60)

    X_train, X_test, y_train, y_test, feature_names = prepare_train_test(df)

    # Train models
    lr_pipe = build_lr_pipeline()
    lr_pipe.fit(X_train, y_train)
    print("[MODEL] Logistic Regression trained.")

    rf_pipe = build_rf_pipeline()
    rf_pipe.fit(X_train, y_train)
    print("[MODEL] Random Forest trained.")

    # Cross-validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    lr_cv_auc = cross_val_score(lr_pipe, X_train, y_train, cv=cv,
                                 scoring="roc_auc").mean()
    rf_cv_auc = cross_val_score(rf_pipe, X_train, y_train, cv=cv,
                                 scoring="roc_auc").mean()
    print(f"[CV] LR 5-fold ROC-AUC: {lr_cv_auc:.4f}")
    print(f"[CV] RF 5-fold ROC-AUC: {rf_cv_auc:.4f}")

    # Evaluate
    lr_metrics = evaluate_model(lr_pipe, X_test, y_test, "Logistic Regression")
    rf_metrics = evaluate_model(rf_pipe, X_test, y_test, "Random Forest")
    metrics_list = [lr_metrics, rf_metrics]

    # Plots
    plot_confusion_matrices(lr_pipe, rf_pipe, X_test, y_test)
    plot_roc_curves(lr_pipe, rf_pipe, X_test, y_test)
    plot_feature_importance(rf_pipe, feature_names)
    save_model_report(metrics_list)

    # Add probabilities to full dataset
    df_out = add_churn_probabilities(df, rf_pipe, feature_names)

    print("\n[DONE] Modelling pipeline complete.")
    return lr_pipe, rf_pipe, metrics_list, df_out
