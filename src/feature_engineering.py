"""
feature_engineering.py
-----------------------
Advanced feature engineering and encoding for churn prediction.
Builds on the base features created in data_cleaning.py.
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler


# ---------------------------------------------------------------------------
# BINARY ENCODING  (Yes/No columns → 1/0)
# ---------------------------------------------------------------------------
BINARY_YES_NO_COLS = [
    "Partner", "Dependents", "PhoneService", "PaperlessBilling"
]

BINARY_SERVICE_COLS = [
    "OnlineSecurity", "OnlineBackup", "DeviceProtection",
    "TechSupport", "StreamingTV", "StreamingMovies", "MultipleLines"
]

INTERNET_SERVICE_MAP = {"DSL": 1, "Fiber optic": 2, "No": 0}
CONTRACT_MAP = {"Month-to-month": 0, "One year": 1, "Two year": 2}
PAYMENT_MAP = {
    "Electronic check": 0,
    "Mailed check": 1,
    "Bank transfer (automatic)": 2,
    "Credit card (automatic)": 3
}


def encode_binary_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Encode Yes/No columns to 1/0 and ordinal encode multi-class categoricals.
    Original string columns are kept alongside encoded versions for
    interpretability in EDA notebooks.
    """
    df = df.copy()

    for col in BINARY_YES_NO_COLS:
        if col in df.columns:
            df[col + "_Enc"] = df[col].map({"Yes": 1, "No": 0})

    for col in BINARY_SERVICE_COLS:
        if col in df.columns:
            df[col + "_Enc"] = df[col].apply(
                lambda x: 1 if x == "Yes" else 0
            )

    if "InternetService" in df.columns:
        df["InternetService_Enc"] = df["InternetService"].map(
            INTERNET_SERVICE_MAP
        ).fillna(0).astype(int)

    if "Contract" in df.columns:
        df["Contract_Enc"] = df["Contract"].map(CONTRACT_MAP)

    if "PaymentMethod" in df.columns:
        df["PaymentMethod_Enc"] = df["PaymentMethod"].map(PAYMENT_MAP)

    if "gender" in df.columns:
        df["gender_Enc"] = df["gender"].map({"Male": 1, "Female": 0})

    print("[ENC] Binary and ordinal encoding complete.")
    return df


# ---------------------------------------------------------------------------
# CHURN RISK SCORE  (simple rule-based composite)
# ---------------------------------------------------------------------------
def compute_churn_risk_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    A heuristic risk score (0–100) that combines:
      - MonthlyCharges (high charge → higher risk for some segments)
      - tenure (short tenure → higher risk)
      - Contract type (month-to-month → higher risk)
      - NumAddOns (few add-ons → higher risk, lower stickiness)
      - SeniorCitizen (seniors showed higher churn in EDA)

    Formula (normalised weighted composite):
      Risk = 0.35 × (1 − tenure_norm)
           + 0.30 × contract_risk   [0=m-to-m, 0.5=1yr, 1=2yr → inverted]
           + 0.20 × charge_norm
           + 0.10 × (1 − addon_norm)
           + 0.05 × senior_flag

    Scaled to 0–100 and rounded to 1 decimal place.
    """
    df = df.copy()

    # Normalise components to [0, 1]
    tenure_norm = (df["tenure"] - df["tenure"].min()) / (
        df["tenure"].max() - df["tenure"].min() + 1e-9
    )
    charge_norm = (df["MonthlyCharges"] - df["MonthlyCharges"].min()) / (
        df["MonthlyCharges"].max() - df["MonthlyCharges"].min() + 1e-9
    )
    addon_norm = df["NumAddOns"] / 6.0  # max possible add-ons = 6

    # Contract risk: month-to-month=1.0, one year=0.5, two year=0.0
    contract_risk_map = {"Month-to-month": 1.0, "One year": 0.5, "Two year": 0.0}
    contract_risk = df["Contract"].map(contract_risk_map).fillna(0.5)

    senior_flag = df["SeniorCitizen"].fillna(0)

    df["ChurnRiskScore"] = (
        0.35 * (1 - tenure_norm) +
        0.30 * contract_risk +
        0.20 * charge_norm +
        0.10 * (1 - addon_norm) +
        0.05 * senior_flag
    ) * 100
    df["ChurnRiskScore"] = df["ChurnRiskScore"].round(1)

    print("[RISK] ChurnRiskScore computed (0–100 scale).")
    return df


# ---------------------------------------------------------------------------
# CUSTOMER LIFETIME VALUE  (CLV)
# ---------------------------------------------------------------------------
def compute_clv(df: pd.DataFrame,
                avg_lifespan_months: float = 24.0) -> pd.DataFrame:
    """
    Simplified CLV formula:
        CLV = AvgMonthlyRevenue × avg_customer_lifespan_months

    avg_lifespan_months default = 24 (2-year planning horizon).
    This is a forward-looking estimate; use actual TotalCharges as historical CLV.

    We also compute:
        HistoricalCLV = TotalCharges  (actual money received from customer)
    """
    df = df.copy()
    df["ProjectedCLV"] = (df["AvgMonthlyRevenue"] * avg_lifespan_months).round(2)
    df["HistoricalCLV"] = df["TotalCharges"].round(2)
    print("[CLV] ProjectedCLV and HistoricalCLV columns added.")
    return df


# ---------------------------------------------------------------------------
# FEATURE MATRIX FOR ML
# ---------------------------------------------------------------------------
FEATURE_COLUMNS = [
    "gender_Enc", "SeniorCitizen", "Partner_Enc", "Dependents_Enc",
    "tenure", "PhoneService_Enc", "MultipleLines_Enc",
    "InternetService_Enc",
    "OnlineSecurity_Enc", "OnlineBackup_Enc", "DeviceProtection_Enc",
    "TechSupport_Enc", "StreamingTV_Enc", "StreamingMovies_Enc",
    "Contract_Enc", "PaperlessBilling_Enc", "PaymentMethod_Enc",
    "MonthlyCharges", "TotalCharges", "NumAddOns", "ChurnRiskScore"
]
TARGET_COLUMN = "Churn"


def build_feature_matrix(df: pd.DataFrame):
    """
    Select model features and target.
    Returns (X, y) where X is a DataFrame and y is a Series.
    """
    available = [c for c in FEATURE_COLUMNS if c in df.columns]
    X = df[available].copy()
    y = df[TARGET_COLUMN].copy()
    print(f"[FEATURES] Feature matrix: {X.shape[1]} features, {len(y)} samples")
    return X, y


def scale_features(X_train: pd.DataFrame,
                   X_test: pd.DataFrame):
    """
    StandardScaler fit on train, applied to both train and test.
    Returns (X_train_scaled, X_test_scaled, scaler).
    """
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    return X_train_scaled, X_test_scaled, scaler


# ---------------------------------------------------------------------------
# FULL FEATURE ENGINEERING PIPELINE
# ---------------------------------------------------------------------------
def run_feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all feature engineering steps and return enriched DataFrame."""
    df = encode_binary_features(df)
    df = compute_churn_risk_score(df)
    df = compute_clv(df)
    print("[FE] Full feature engineering pipeline complete.")
    return df
