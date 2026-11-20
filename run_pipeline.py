"""
run_pipeline.py
---------------
Master script: Download dataset (if needed), run the complete
data-cleaning → feature-engineering → analysis → modelling pipeline
end-to-end.

Run from the project root:
    python run_pipeline.py

The script will:
  1. Download the IBM Telco Customer Churn dataset from a public URL
     (if not already present).
  2. Run the full data cleaning pipeline.
  3. Run feature engineering.
  4. Compute business KPIs.
  5. Generate all EDA plots.
  6. Run K-Means customer segmentation.
  7. Train and evaluate churn prediction models.
  8. Export Power BI dataset.
  9. Generate business insights report.
"""

import utils.http_session
import utils.transport
import utils.session
import os
import sys
import urllib.request
import pandas as pd

# ---------------------------------------------------------------------------
# Ensure src/ is on the path regardless of where the script is run from
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from data_cleaning import run_cleaning_pipeline
from feature_engineering import run_feature_engineering
from analysis import (
    compute_kpis,
    run_eda_plots,
    run_kmeans_segmentation,
    export_powerbi_dataset,
    generate_insights_report
)
from modeling import run_modeling_pipeline

# ---------------------------------------------------------------------------
# DATASET DOWNLOAD
# ---------------------------------------------------------------------------
RAW_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "telco_churn_raw.csv")
CLEAN_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "telco_churn_cleaned.csv")
FINAL_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "telco_churn_final.csv")

# IBM Telco dataset hosted on GitHub (original Kaggle source by IBM)
DATASET_URL = (
    "https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/"
    "master/data/Telco-Customer-Churn.csv"
)


def download_dataset(url: str, dest: str) -> None:
    """Download dataset if not already present."""
    if os.path.exists(dest):
        print(f"[DOWNLOAD] Dataset already exists at: {dest}")
        return
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    print(f"[DOWNLOAD] Downloading dataset from:\n  {url}")
    try:
        urllib.request.urlretrieve(url, dest)
        size_kb = os.path.getsize(dest) / 1024
        print(f"[DOWNLOAD] Success. File size: {size_kb:.1f} KB")
    except Exception as exc:
        print(f"[DOWNLOAD] Failed: {exc}")
        print("\nManual download instructions:")
        print("  1. Go to https://www.kaggle.com/datasets/blastchar/telco-customer-churn")
        print("  2. Download 'WA_Fn-UseC_-Telco-Customer-Churn.csv'")
        print(f"  3. Save it as: {dest}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# MAIN PIPELINE
# ---------------------------------------------------------------------------
def main():
    print("\n" + "=" * 65)
    print("  CUSTOMER CHURN & REVENUE INTELLIGENCE ANALYTICS")
    print("  Full Pipeline Run")
    print("=" * 65 + "\n")

    os.chdir(PROJECT_ROOT)

    # Step 1 — Download
    download_dataset(DATASET_URL, RAW_PATH)

    # Step 2 — Data Cleaning
    df_clean = run_cleaning_pipeline(RAW_PATH, CLEAN_PATH)

    # Step 3 — Feature Engineering
    df_fe = run_feature_engineering(df_clean)

    # Step 4 — Business KPIs
    kpis = compute_kpis(df_fe)

    # Step 5 — EDA Plots
    run_eda_plots(df_fe)

    # Step 6 — Customer Segmentation
    df_seg = run_kmeans_segmentation(df_fe, n_clusters=4)

    # Step 7 — Churn Prediction
    lr_pipe, rf_pipe, metrics_list, df_model = run_modeling_pipeline(df_seg)

    # Step 8 — Export Power BI Dataset
    export_powerbi_dataset(df_model, os.path.join(
        PROJECT_ROOT, "dashboard", "powerbi_dataset.csv"
    ))

    # Step 9 — Business Insights
    generate_insights_report(df_model, kpis, os.path.join(
        PROJECT_ROOT, "outputs", "reports", "business_insights.txt"
    ))

    # Step 10 — Save final enriched dataset
    os.makedirs(os.path.dirname(FINAL_PATH), exist_ok=True)
    df_model.to_csv(FINAL_PATH, index=False)
    print(f"\n[FINAL] Enriched dataset saved -> {FINAL_PATH}")

    print("\n" + "=" * 65)
    print("  PIPELINE COMPLETE")
    print("  Outputs:")
    print("    data/processed/telco_churn_cleaned.csv")
    print("    data/processed/telco_churn_final.csv")
    print("    outputs/figures/  (14 charts)")
    print("    outputs/reports/business_insights.txt")
    print("    outputs/reports/model_performance.txt")
    print("    dashboard/powerbi_dataset.csv")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
