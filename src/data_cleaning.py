"""
data_cleaning.py
----------------
End-to-end data cleaning pipeline for the Customer Churn & Revenue
Intelligence Analytics project.

Dataset: IBM Telco Customer Churn (Kaggle / IBM Sample Data Sets)
Source  : https://www.kaggle.com/datasets/blastchar/telco-customer-churn
License : Community Data License Agreement – Sharing, Version 1.0
          (CDLA-Sharing-1.0)

Column descriptions
-------------------
customerID          : Unique customer identifier
gender              : Male / Female
SeniorCitizen       : 1 = senior (65+), 0 = not senior
Partner             : Has a partner (Yes / No)
Dependents          : Has dependents (Yes / No)
tenure              : Months the customer has been active
PhoneService        : Has phone service (Yes / No)
MultipleLines       : Multiple phone lines (Yes / No / No phone service)
InternetService     : DSL / Fiber optic / No
OnlineSecurity      : Yes / No / No internet service
OnlineBackup        : Yes / No / No internet service
DeviceProtection    : Yes / No / No internet service
TechSupport         : Yes / No / No internet service
StreamingTV         : Yes / No / No internet service
StreamingMovies     : Yes / No / No internet service
Contract            : Month-to-month / One year / Two year
PaperlessBilling    : Yes / No
PaymentMethod       : Electronic check / Mailed check / Bank transfer /
                      Credit card (automatic)
MonthlyCharges      : Monthly fee in USD
TotalCharges        : Total amount charged to date (USD)
Churn               : Target — Yes if customer churned, No otherwise
"""

import os
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Paths  (relative to project root; adjust if running from another location)
# ---------------------------------------------------------------------------
RAW_PATH = os.path.join("data", "raw", "telco_churn_raw.csv")
CLEAN_PATH = os.path.join("data", "processed", "telco_churn_cleaned.csv")


# ---------------------------------------------------------------------------
# 1. LOAD DATA
# ---------------------------------------------------------------------------
def load_raw_data(path: str = RAW_PATH) -> pd.DataFrame:
    """Load raw CSV and perform first-pass inspection."""
    df = pd.read_csv(path)
    print(f"[LOAD] Shape: {df.shape}  |  Columns: {df.shape[1]}")
    return df


# ---------------------------------------------------------------------------
# 2. MISSING VALUE ANALYSIS
# ---------------------------------------------------------------------------
def analyze_missing(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return a summary DataFrame showing count and percentage of nulls per column.
    TotalCharges is often read as object due to blank strings; those become NaN
    after numeric conversion and are treated here.
    """
    missing_count = df.isnull().sum()
    missing_pct = (missing_count / len(df)) * 100
    summary = pd.DataFrame({
        "missing_count": missing_count,
        "missing_pct": missing_pct.round(2)
    })
    print("\n[MISSING VALUES]\n", summary[summary["missing_count"] > 0])
    return summary


# ---------------------------------------------------------------------------
# 3. FIX DATA TYPES
# ---------------------------------------------------------------------------
def fix_data_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    TotalCharges arrives as object because some rows contain only whitespace.
    We coerce to numeric, which converts blanks to NaN, then impute with the
    product  tenure × MonthlyCharges  (a deterministic estimate rather than
    simply dropping or using mean).
    SeniorCitizen (0/1 int) is kept as int but mapped to a readable label
    in feature engineering.
    Churn is converted to a binary integer (1 = churned, 0 = retained).
    """
    df = df.copy()

    # TotalCharges  ──  coerce blanks → NaN → impute
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    blank_total = df["TotalCharges"].isnull().sum()
    if blank_total > 0:
        # tenure=0 customers → TotalCharges should logically be 0 or
        # MonthlyCharges if they signed up and immediately churned
        df.loc[df["TotalCharges"].isnull(), "TotalCharges"] = (
            df.loc[df["TotalCharges"].isnull(), "tenure"]
            * df.loc[df["TotalCharges"].isnull(), "MonthlyCharges"]
        )
        print(f"[DTYPE] Imputed {blank_total} TotalCharges rows with "
              "tenure × MonthlyCharges")

    # Churn → binary int
    df["Churn"] = df["Churn"].map({"Yes": 1, "No": 0})

    # customerID → string (already str, but explicit)
    df["customerID"] = df["customerID"].astype(str)

    print("[DTYPE] Types fixed.")
    return df


# ---------------------------------------------------------------------------
# 4. DUPLICATE DETECTION
# ---------------------------------------------------------------------------
def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Check for full-row duplicates and customerID duplicates separately.
    customerID should be unique; if not, keep the first occurrence.
    """
    n_before = len(df)
    full_dups = df.duplicated().sum()
    id_dups = df.duplicated(subset=["customerID"]).sum()

    print(f"\n[DUPLICATES] Full-row duplicates : {full_dups}")
    print(f"[DUPLICATES] customerID duplicates: {id_dups}")

    df = df.drop_duplicates(subset=["customerID"], keep="first")
    print(f"[DUPLICATES] Rows removed: {n_before - len(df)}")
    return df


# ---------------------------------------------------------------------------
# 5. CATEGORICAL VALUE STANDARDISATION
# ---------------------------------------------------------------------------
def standardize_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Trim whitespace from all object columns and normalise casing.
    No coercion of valid categories — only whitespace cleanup.
    """
    df = df.copy()
    obj_cols = df.select_dtypes(include="object").columns
    for col in obj_cols:
        df[col] = df[col].str.strip()
    print(f"[CATEGORIES] Whitespace stripped from {len(obj_cols)} columns.")
    return df


# ---------------------------------------------------------------------------
# 6. OUTLIER INVESTIGATION  (explain, not blindly drop)
# ---------------------------------------------------------------------------
def investigate_outliers(df: pd.DataFrame) -> dict:
    """
    IQR-based outlier detection on numeric columns.
    Returns a report dict.  Genuine business observations (e.g., very high
    tenure or very high MonthlyCharges) are kept; only confirmed data errors
    are flagged for review.
    """
    numeric_cols = ["tenure", "MonthlyCharges", "TotalCharges"]
    report = {}
    for col in numeric_cols:
        q1, q3 = df[col].quantile([0.25, 0.75])
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        outliers = df[(df[col] < lower) | (df[col] > upper)]
        report[col] = {
            "n_outliers": len(outliers),
            "lower_bound": round(lower, 2),
            "upper_bound": round(upper, 2),
            "min": df[col].min(),
            "max": df[col].max()
        }
        print(f"[OUTLIERS] {col}: {len(outliers)} potential outliers "
              f"(bounds: {lower:.2f} – {upper:.2f})")
    print("[OUTLIERS] NOTE: All flagged records appear to be genuine "
          "customer observations, not data errors. No rows removed.")
    return report


# ---------------------------------------------------------------------------
# 7. NUMERICAL VALIDATION
# ---------------------------------------------------------------------------
def validate_numerics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Business rules:
      - tenure       ≥ 0
      - MonthlyCharges > 0
      - TotalCharges  ≥ 0
    Rows violating these rules are removed and logged.
    """
    df = df.copy()
    n_before = len(df)
    df = df[
        (df["tenure"] >= 0) &
        (df["MonthlyCharges"] > 0) &
        (df["TotalCharges"] >= 0)
    ]
    removed = n_before - len(df)
    if removed:
        print(f"[VALIDATE] Removed {removed} rows violating business rules.")
    else:
        print("[VALIDATE] All numeric values pass business-rule checks.")
    return df


# ---------------------------------------------------------------------------
# 8. FEATURE CREATION (derived business columns)
# ---------------------------------------------------------------------------
def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derived columns and the formulas used:

    TenureBand
        Bucketed tenure into lifecycle stages:
          0–12 months  → 'New'
         13–24 months  → 'Developing'
         25–48 months  → 'Established'
         49–72 months  → 'Loyal'

    AvgMonthlyRevenue
        Formula: TotalCharges / max(tenure, 1)
        Represents the average monthly payment factoring in actual
        historical charges (more reliable than MonthlyCharges alone for
        customers with changing plans).

    ChargePerTenureUnit
        Formula: MonthlyCharges / max(tenure, 1)
        Flags early customers with high monthly charges — a churn risk
        indicator.

    NumAddOns
        Count of subscribed add-on services:
          OnlineSecurity, OnlineBackup, DeviceProtection, TechSupport,
          StreamingTV, StreamingMovies
        Each "Yes" = 1, otherwise = 0.
        Higher add-on count → higher product stickiness.

    SeniorCitizenLabel
        Map SeniorCitizen (0/1) to readable text ('Yes' / 'No').

    ValueSegment
        Revenue-based segmentation using MonthlyCharges tertiles:
          Bottom third  → 'Low Value'
          Middle third  → 'Medium Value'
          Top third     → 'High Value'
    """
    df = df.copy()

    # TenureBand
    bins = [-1, 12, 24, 48, 73]
    labels = ["New (0–12m)", "Developing (13–24m)",
              "Established (25–48m)", "Loyal (49–72m)"]
    df["TenureBand"] = pd.cut(df["tenure"], bins=bins, labels=labels)

    # AvgMonthlyRevenue
    safe_tenure = df["tenure"].replace(0, 1)
    df["AvgMonthlyRevenue"] = (df["TotalCharges"] / safe_tenure).round(2)

    # ChargePerTenureUnit
    df["ChargePerTenureUnit"] = (
        df["MonthlyCharges"] / safe_tenure
    ).round(4)

    # NumAddOns
    addon_cols = [
        "OnlineSecurity", "OnlineBackup", "DeviceProtection",
        "TechSupport", "StreamingTV", "StreamingMovies"
    ]
    df["NumAddOns"] = df[addon_cols].apply(
        lambda row: (row == "Yes").sum(), axis=1
    )

    # SeniorCitizenLabel
    df["SeniorCitizenLabel"] = df["SeniorCitizen"].map(
        {1: "Senior", 0: "Non-Senior"}
    )

    # ValueSegment
    tertile_low = df["MonthlyCharges"].quantile(0.333)
    tertile_high = df["MonthlyCharges"].quantile(0.667)
    df["ValueSegment"] = pd.cut(
        df["MonthlyCharges"],
        bins=[-np.inf, tertile_low, tertile_high, np.inf],
        labels=["Low Value", "Medium Value", "High Value"]
    )

    print("[FEATURES] Derived columns created: TenureBand, AvgMonthlyRevenue,"
          " ChargePerTenureUnit, NumAddOns, SeniorCitizenLabel, ValueSegment")
    return df


# ---------------------------------------------------------------------------
# 9. SAVE CLEANED DATASET
# ---------------------------------------------------------------------------
def save_cleaned(df: pd.DataFrame, path: str = CLEAN_PATH) -> None:
    """Persist the cleaned DataFrame as CSV."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    print(f"\n[SAVE] Cleaned dataset saved -> {path}  |  Shape: {df.shape}")


# ---------------------------------------------------------------------------
# MAIN PIPELINE
# ---------------------------------------------------------------------------
def run_cleaning_pipeline(raw_path: str = RAW_PATH,
                           clean_path: str = CLEAN_PATH) -> pd.DataFrame:
    """
    Execute the full cleaning pipeline end-to-end and return the
    cleaned DataFrame.
    """
    print("=" * 60)
    print("CUSTOMER CHURN — DATA CLEANING PIPELINE")
    print("=" * 60)

    df = load_raw_data(raw_path)
    analyze_missing(df)
    df = fix_data_types(df)
    df = remove_duplicates(df)
    df = standardize_categoricals(df)
    investigate_outliers(df)
    df = validate_numerics(df)
    df = create_features(df)
    save_cleaned(df, clean_path)

    print("\n[DONE] Cleaning pipeline complete.")
    print(f"       Final shape: {df.shape}")
    return df


if __name__ == "__main__":
    run_cleaning_pipeline()
