"""
analysis.py
-----------
Business KPI computation and customer segmentation for the
Customer Churn & Revenue Intelligence Analytics project.
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")   # non-interactive backend for script execution
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

# ---------------------------------------------------------------------------
# Plot style
# ---------------------------------------------------------------------------
sns.set_theme(style="whitegrid", palette="muted", font_scale=1.1)
PALETTE_CHURN = {1: "#E63946", 0: "#457B9D"}   # red = churned, blue = retained
FIG_DIR = os.path.join("outputs", "figures")
os.makedirs(FIG_DIR, exist_ok=True)


def _save(fig, name: str) -> str:
    path = os.path.join(FIG_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[PLOT] Saved -> {path}")
    return path


# ===========================================================================
# SECTION 1 — BUSINESS KPI CALCULATION
# ===========================================================================

def compute_kpis(df: pd.DataFrame) -> dict:
    """
    Calculate all supported business KPIs from the cleaned dataset.

    Formulas
    --------
    Total Customers         : len(df)
    Churned Customers       : sum(Churn == 1)
    Active Customers        : sum(Churn == 0)
    Churn Rate              : Churned / Total × 100
    Retention Rate          : Active  / Total × 100
    Total Revenue           : sum(TotalCharges)
    Avg Monthly Revenue     : mean(MonthlyCharges)
    Avg Tenure (months)     : mean(tenure)
    Avg Historical CLV      : mean(HistoricalCLV)
    Revenue Lost to Churn   : sum(TotalCharges where Churn==1)
    Monthly Revenue at Risk : sum(MonthlyCharges where Churn==0 &
                                   ChurnRiskScore >= 60)
    High-Value Customers    : count(ValueSegment == 'High Value')
    High-Risk Customers     : count(ChurnRiskScore >= 60 & Churn==0)
    """
    total = len(df)
    churned = int(df["Churn"].sum())
    active = total - churned

    churn_rate = round(churned / total * 100, 2)
    retention_rate = round(active / total * 100, 2)

    total_revenue = round(df["TotalCharges"].sum(), 2)
    avg_monthly_rev = round(df["MonthlyCharges"].mean(), 2)
    avg_tenure = round(df["tenure"].mean(), 2)

    # HistoricalCLV may not exist if FE not run; fall back to TotalCharges
    clv_col = "HistoricalCLV" if "HistoricalCLV" in df.columns else "TotalCharges"
    avg_clv = round(df[clv_col].mean(), 2)

    revenue_lost = round(df.loc[df["Churn"] == 1, "TotalCharges"].sum(), 2)

    # Revenue at Risk: active customers with high churn risk score
    if "ChurnRiskScore" in df.columns:
        at_risk_mask = (df["Churn"] == 0) & (df["ChurnRiskScore"] >= 60)
        monthly_at_risk = round(df.loc[at_risk_mask, "MonthlyCharges"].sum(), 2)
        high_risk_count = int(at_risk_mask.sum())
    else:
        monthly_at_risk = np.nan
        high_risk_count = np.nan

    high_value_count = int(
        (df["ValueSegment"] == "High Value").sum()
    ) if "ValueSegment" in df.columns else np.nan

    kpis = {
        "Total Customers": total,
        "Active Customers": active,
        "Churned Customers": churned,
        "Churn Rate (%)": churn_rate,
        "Retention Rate (%)": retention_rate,
        "Total Revenue (USD)": total_revenue,
        "Avg Monthly Revenue per Customer (USD)": avg_monthly_rev,
        "Avg Customer Tenure (months)": avg_tenure,
        "Avg Historical CLV (USD)": avg_clv,
        "Revenue Lost to Churn (USD)": revenue_lost,
        "Monthly Revenue at Risk (USD)": monthly_at_risk,
        "High-Value Customers": high_value_count,
        "High-Risk Active Customers": high_risk_count
    }

    print("\n" + "=" * 52)
    print("  BUSINESS KPI SUMMARY")
    print("=" * 52)
    for k, v in kpis.items():
        print(f"  {k:<42} {v:>12}")
    print("=" * 52)
    return kpis


# ===========================================================================
# SECTION 2 — EDA VISUALISATIONS
# ===========================================================================

def plot_churn_distribution(df: pd.DataFrame) -> str:
    """Churn vs Retention count plot."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    counts = df["Churn"].map({1: "Churned", 0: "Retained"}).value_counts()
    axes[0].bar(counts.index, counts.values,
                color=[PALETTE_CHURN[1], PALETTE_CHURN[0]], edgecolor="black")
    axes[0].set_title("Customer Churn Distribution", fontsize=14, fontweight="bold")
    axes[0].set_ylabel("Number of Customers")
    for i, (label, val) in enumerate(counts.items()):
        axes[0].text(i, val + 30, f"{val}\n({val/len(df)*100:.1f}%)",
                     ha="center", fontsize=11)

    axes[1].pie(counts.values, labels=counts.index,
                colors=[PALETTE_CHURN[1], PALETTE_CHURN[0]],
                autopct="%1.1f%%", startangle=90, textprops={"fontsize": 12})
    axes[1].set_title("Churn Proportion", fontsize=14, fontweight="bold")

    fig.suptitle("Q: What proportion of customers have churned?",
                 fontsize=12, style="italic")
    plt.tight_layout()
    return _save(fig, "01_churn_distribution.png")


def plot_churn_by_contract(df: pd.DataFrame) -> str:
    """Business Q: Which contract type has the highest churn rate?"""
    ct = df.groupby("Contract")["Churn"].agg(
        Total="count", Churned="sum"
    ).reset_index()
    ct["Churn Rate (%)"] = (ct["Churned"] / ct["Total"] * 100).round(1)
    ct_sorted = ct.sort_values("Churn Rate (%)", ascending=False)

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(ct_sorted["Contract"], ct_sorted["Churn Rate (%)"],
                  color=["#E63946", "#F4A261", "#2A9D8F"], edgecolor="black")
    ax.set_title("Churn Rate by Contract Type\nQ: Which contract type drives the most churn?",
                 fontsize=13, fontweight="bold")
    ax.set_ylabel("Churn Rate (%)")
    ax.set_xlabel("Contract Type")
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.5,
                f"{bar.get_height():.1f}%", ha="center", fontsize=11)
    plt.tight_layout()
    return _save(fig, "02_churn_by_contract.png")


def plot_churn_by_tenure(df: pd.DataFrame) -> str:
    """Business Q: Do newer customers churn more?"""
    tenure_churn = df.groupby("TenureBand")["Churn"].mean().reset_index()
    tenure_churn["Churn Rate (%)"] = (tenure_churn["Churn"] * 100).round(1)
    tenure_churn["TenureBand"] = tenure_churn["TenureBand"].astype(str)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(tenure_churn["TenureBand"], tenure_churn["Churn Rate (%)"],
           color=sns.color_palette("RdYlGn_r", len(tenure_churn)),
           edgecolor="black")
    ax.set_title("Churn Rate by Tenure Band\nQ: Does tenure protect against churn?",
                 fontsize=13, fontweight="bold")
    ax.set_ylabel("Churn Rate (%)")
    ax.set_xlabel("Customer Lifecycle Stage")
    plt.xticks(rotation=15)
    plt.tight_layout()
    return _save(fig, "03_churn_by_tenure.png")


def plot_churn_by_payment(df: pd.DataFrame) -> str:
    """Business Q: Does payment method correlate with churn?"""
    pm_churn = df.groupby("PaymentMethod")["Churn"].mean().reset_index()
    pm_churn["Churn Rate (%)"] = (pm_churn["Churn"] * 100).round(1)
    pm_churn = pm_churn.sort_values("Churn Rate (%)", ascending=True)

    fig, ax = plt.subplots(figsize=(10, 5))
    colors = sns.color_palette("Blues_r", len(pm_churn))
    ax.barh(pm_churn["PaymentMethod"], pm_churn["Churn Rate (%)"],
            color=colors, edgecolor="black")
    ax.set_title("Churn Rate by Payment Method\nQ: Which payment method is highest-risk?",
                 fontsize=13, fontweight="bold")
    ax.set_xlabel("Churn Rate (%)")
    for i, v in enumerate(pm_churn["Churn Rate (%)"]):
        ax.text(v + 0.3, i, f"{v}%", va="center", fontsize=10)
    plt.tight_layout()
    return _save(fig, "04_churn_by_payment.png")


def plot_monthly_charges_distribution(df: pd.DataFrame) -> str:
    """Business Q: Do high-charge customers churn more?"""
    fig, ax = plt.subplots(figsize=(11, 5))
    for churn_val, label, color in [
        (1, "Churned", "#E63946"),
        (0, "Retained", "#457B9D")
    ]:
        subset = df[df["Churn"] == churn_val]["MonthlyCharges"]
        ax.hist(subset, bins=40, alpha=0.65, label=label,
                color=color, edgecolor="white")
    ax.axvline(df.loc[df["Churn"] == 1, "MonthlyCharges"].mean(),
               color="#E63946", linestyle="--", linewidth=2,
               label=f"Churned Mean: ${df.loc[df['Churn']==1,'MonthlyCharges'].mean():.0f}")
    ax.axvline(df.loc[df["Churn"] == 0, "MonthlyCharges"].mean(),
               color="#457B9D", linestyle="--", linewidth=2,
               label=f"Retained Mean: ${df.loc[df['Churn']==0,'MonthlyCharges'].mean():.0f}")
    ax.set_title(
        "Monthly Charges Distribution by Churn Status\n"
        "Q: Do higher monthly charges correlate with churn?",
        fontsize=13, fontweight="bold"
    )
    ax.set_xlabel("Monthly Charges (USD)")
    ax.set_ylabel("Customer Count")
    ax.legend()
    plt.tight_layout()
    return _save(fig, "05_monthly_charges_distribution.png")


def plot_internet_service_churn(df: pd.DataFrame) -> str:
    """Business Q: Which internet service type has highest churn?"""
    is_churn = df.groupby("InternetService")["Churn"].agg(
        Total="count", Churned="sum"
    ).reset_index()
    is_churn["Churn Rate (%)"] = (
        is_churn["Churned"] / is_churn["Total"] * 100
    ).round(1)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    axes[0].bar(is_churn["InternetService"], is_churn["Churn Rate (%)"],
                color=["#2A9D8F", "#E63946", "#457B9D"], edgecolor="black")
    axes[0].set_title("Churn Rate by Internet Service", fontsize=12, fontweight="bold")
    axes[0].set_ylabel("Churn Rate (%)")
    for i, row in is_churn.iterrows():
        axes[0].text(i, row["Churn Rate (%)"] + 0.5,
                     f"{row['Churn Rate (%)']:.1f}%", ha="center")

    axes[1].bar(is_churn["InternetService"], is_churn["Total"],
                color="#264653", label="Total", edgecolor="black")
    axes[1].bar(is_churn["InternetService"], is_churn["Churned"],
                color="#E63946", label="Churned", edgecolor="black")
    axes[1].set_title("Customer Count vs Churned by Internet Service",
                      fontsize=12, fontweight="bold")
    axes[1].set_ylabel("Count")
    axes[1].legend()

    fig.suptitle("Q: Does fiber optic service show higher churn?",
                 fontsize=11, style="italic")
    plt.tight_layout()
    return _save(fig, "06_internet_service_churn.png")


def plot_value_segment_churn(df: pd.DataFrame) -> str:
    """Business Q: Which value segment churns the most?"""
    vs_churn = df.groupby("ValueSegment")["Churn"].agg(
        Total="count", Churned="sum"
    ).reset_index()
    vs_churn["Churn Rate (%)"] = (
        vs_churn["Churned"] / vs_churn["Total"] * 100
    ).round(1)
    vs_churn["ValueSegment"] = vs_churn["ValueSegment"].astype(str)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(vs_churn["ValueSegment"], vs_churn["Churn Rate (%)"],
           color=["#90BE6D", "#F9C74F", "#F94144"], edgecolor="black")
    ax.set_title("Churn Rate by Value Segment\nQ: Is high value associated with higher churn?",
                 fontsize=13, fontweight="bold")
    ax.set_ylabel("Churn Rate (%)")
    ax.set_xlabel("Value Segment")
    for i, row in vs_churn.iterrows():
        ax.text(i, row["Churn Rate (%)"] + 0.3,
                f"{row['Churn Rate (%)']:.1f}%", ha="center")
    plt.tight_layout()
    return _save(fig, "07_value_segment_churn.png")


def plot_correlation_heatmap(df: pd.DataFrame) -> str:
    """Numeric feature correlation heatmap."""
    numeric_df = df.select_dtypes(include=[np.number])
    if "customerID" in numeric_df.columns:
        numeric_df = numeric_df.drop(columns=["customerID"])
    corr = numeric_df.corr()

    fig, ax = plt.subplots(figsize=(14, 10))
    mask = np.triu(np.ones_like(corr, dtype=bool))
    sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap="coolwarm",
                center=0, linewidths=0.5, ax=ax, annot_kws={"size": 8})
    ax.set_title("Numeric Feature Correlation Heatmap\n"
                 "Q: Which features most correlate with Churn?",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    return _save(fig, "08_correlation_heatmap.png")


def plot_addons_vs_churn(df: pd.DataFrame) -> str:
    """Business Q: Do customers with more add-ons churn less?"""
    addon_churn = df.groupby("NumAddOns")["Churn"].mean().reset_index()
    addon_churn["Churn Rate (%)"] = (addon_churn["Churn"] * 100).round(1)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(addon_churn["NumAddOns"], addon_churn["Churn Rate (%)"],
            marker="o", color="#E63946", linewidth=2, markersize=8)
    ax.fill_between(addon_churn["NumAddOns"], addon_churn["Churn Rate (%)"],
                    alpha=0.2, color="#E63946")
    ax.set_title("Churn Rate by Number of Add-On Services\n"
                 "Q: Does product stickiness reduce churn?",
                 fontsize=13, fontweight="bold")
    ax.set_xlabel("Number of Add-On Services")
    ax.set_ylabel("Churn Rate (%)")
    ax.set_xticks(range(7))
    plt.tight_layout()
    return _save(fig, "09_addons_vs_churn.png")


def run_eda_plots(df: pd.DataFrame) -> list:
    """Run all EDA visualisations and return list of saved paths."""
    saved = []
    saved.append(plot_churn_distribution(df))
    saved.append(plot_churn_by_contract(df))
    saved.append(plot_churn_by_tenure(df))
    saved.append(plot_churn_by_payment(df))
    saved.append(plot_monthly_charges_distribution(df))
    saved.append(plot_internet_service_churn(df))
    saved.append(plot_value_segment_churn(df))
    saved.append(plot_correlation_heatmap(df))
    saved.append(plot_addons_vs_churn(df))
    print(f"\n[EDA] {len(saved)} plots saved.")
    return saved


# ===========================================================================
# SECTION 3 — CUSTOMER SEGMENTATION (K-Means)
# ===========================================================================

def run_kmeans_segmentation(df: pd.DataFrame,
                             n_clusters: int = 4,
                             random_state: int = 42) -> pd.DataFrame:
    """
    K-Means Customer Segmentation
    ------------------------------
    Why K-Means?
      - We have continuous numeric features (tenure, MonthlyCharges,
        ChurnRiskScore, NumAddOns) and no natural labels.
      - K-Means is interpretable and computationally efficient.
      - We use Elbow + Silhouette to choose k.

    Features used:
      - tenure               (customer loyalty proxy)
      - MonthlyCharges       (revenue contribution)
      - NumAddOns            (product stickiness)
      - ChurnRiskScore       (risk proxy)

    Segmentation is a business description, NOT a classification model.
    Do NOT interpret cluster centroids as churn predictions.
    """
    seg_features = ["tenure", "MonthlyCharges", "NumAddOns", "ChurnRiskScore"]
    available = [c for c in seg_features if c in df.columns]

    seg_df = df[available].dropna().copy()
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(seg_df)

    # Elbow + Silhouette evaluation
    inertias, silhouettes = [], []
    k_range = range(2, 9)
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        labels = km.fit_predict(X_scaled)
        inertias.append(km.inertia_)
        silhouettes.append(silhouette_score(X_scaled, labels))

    # Plot elbow + silhouette
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    axes[0].plot(list(k_range), inertias, marker="o", color="#2A9D8F", linewidth=2)
    axes[0].axvline(n_clusters, color="#E63946", linestyle="--",
                    label=f"Chosen k={n_clusters}")
    axes[0].set_title("Elbow Method — Inertia vs k", fontsize=12, fontweight="bold")
    axes[0].set_xlabel("Number of Clusters (k)")
    axes[0].set_ylabel("Inertia")
    axes[0].legend()

    axes[1].plot(list(k_range), silhouettes, marker="s", color="#E76F51", linewidth=2)
    axes[1].axvline(n_clusters, color="#E63946", linestyle="--",
                    label=f"Chosen k={n_clusters}")
    axes[1].set_title("Silhouette Score vs k", fontsize=12, fontweight="bold")
    axes[1].set_xlabel("Number of Clusters (k)")
    axes[1].set_ylabel("Silhouette Score")
    axes[1].legend()

    fig.suptitle("K-Means Cluster Selection", fontsize=13, fontweight="bold")
    plt.tight_layout()
    _save(fig, "10_kmeans_elbow_silhouette.png")

    # Fit final model
    km_final = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    labels = km_final.fit_predict(X_scaled)
    sil_score = silhouette_score(X_scaled, labels)
    print(f"[KMEANS] Final model: k={n_clusters}, Silhouette={sil_score:.3f}")

    df = df.copy()
    df.loc[seg_df.index, "Cluster"] = labels.astype(int)

    # Profile clusters
    profile = df.groupby("Cluster").agg(
        N=("customerID", "count"),
        Avg_Tenure=("tenure", "mean"),
        Avg_MonthlyCharges=("MonthlyCharges", "mean"),
        Avg_NumAddOns=("NumAddOns", "mean"),
        Avg_ChurnRiskScore=("ChurnRiskScore", "mean"),
        Churn_Rate=("Churn", "mean")
    ).round(2)

    print("\n[KMEANS] Cluster Profiles:")
    print(profile.to_string())

    # Business label assignment (sorted by churn risk & charges)
    profile_sorted = profile.sort_values(
        ["Avg_ChurnRiskScore", "Avg_MonthlyCharges"],
        ascending=[False, False]
    )
    segment_labels = {
        profile_sorted.index[0]: "High Value / High Risk",
        profile_sorted.index[1]: "High Value / Low Risk",
        profile_sorted.index[2]: "Low Value / High Risk",
        profile_sorted.index[3]: "Low Value / Low Risk"
    }
    df["BusinessSegment"] = df["Cluster"].map(segment_labels)

    # Cluster visualisation
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    colors_clust = sns.color_palette("Set2", n_clusters)
    for cid in range(n_clusters):
        sub = df[df["Cluster"] == cid]
        ax2.scatter(sub["tenure"], sub["MonthlyCharges"],
                    alpha=0.5, s=25, color=colors_clust[cid],
                    label=segment_labels.get(cid, f"Cluster {cid}"))
    ax2.set_title("Customer Segments: Tenure vs Monthly Charges",
                  fontsize=13, fontweight="bold")
    ax2.set_xlabel("Tenure (months)")
    ax2.set_ylabel("Monthly Charges (USD)")
    ax2.legend(title="Segment")
    plt.tight_layout()
    _save(fig2, "11_customer_segments_scatter.png")

    return df


# ===========================================================================
# SECTION 4 — POWER BI DATASET EXPORT
# ===========================================================================

def export_powerbi_dataset(df: pd.DataFrame,
                            path: str = os.path.join(
                                "dashboard", "powerbi_dataset.csv")) -> None:
    """
    Export a clean, Power BI-ready CSV.
    Includes all business KPI columns, segment labels, and risk scores.
    """
    columns_to_export = [
        "customerID", "gender", "SeniorCitizenLabel", "Partner", "Dependents",
        "tenure", "TenureBand", "PhoneService", "MultipleLines",
        "InternetService", "Contract", "PaperlessBilling", "PaymentMethod",
        "MonthlyCharges", "TotalCharges", "AvgMonthlyRevenue",
        "NumAddOns", "ValueSegment", "ChurnRiskScore",
        "ProjectedCLV", "HistoricalCLV",
        "Cluster", "BusinessSegment", "Churn"
    ]
    available = [c for c in columns_to_export if c in df.columns]
    export_df = df[available].copy()

    # Make TenureBand and ValueSegment plain strings for Power BI
    for col in ["TenureBand", "ValueSegment", "BusinessSegment"]:
        if col in export_df.columns:
            export_df[col] = export_df[col].astype(str)

    export_df["ChurnLabel"] = export_df["Churn"].map({1: "Churned", 0: "Retained"})

    os.makedirs(os.path.dirname(path), exist_ok=True)
    export_df.to_csv(path, index=False)
    print(f"[EXPORT] Power BI dataset saved -> {path}  |  {export_df.shape}")


# ===========================================================================
# SECTION 5 — BUSINESS INSIGHTS REPORT
# ===========================================================================

def generate_insights_report(df: pd.DataFrame, kpis: dict,
                              path: str = os.path.join(
                                  "outputs", "reports",
                                  "business_insights.txt")) -> None:
    """
    Derive and write the 10 key business insights directly from the dataset.
    Every number is calculated from the actual data.
    """

    def pct(col_filter, col, total=None):
        n = df.loc[col_filter, col].sum() if col != "count" else col_filter.sum()
        t = total or len(df)
        return round(n / t * 100, 1)

    # Pre-compute insight data
    # 1. Contract type churn
    ct = df.groupby("Contract")["Churn"].mean() * 100
    mtm_churn = ct.get("Month-to-month", 0)
    twyr_churn = ct.get("Two year", 0)

    # 2. Tenure churn
    new_churn = df[df["tenure"] <= 12]["Churn"].mean() * 100
    loyal_churn = df[df["tenure"] > 48]["Churn"].mean() * 100

    # 3. Payment method
    pm_churn = df.groupby("PaymentMethod")["Churn"].mean() * 100
    highest_pm = pm_churn.idxmax()
    highest_pm_rate = pm_churn.max()

    # 4. Internet service
    is_churn = df.groupby("InternetService")["Churn"].mean() * 100
    fiber_churn = is_churn.get("Fiber optic", 0)
    dsl_churn = is_churn.get("DSL", 0)

    # 5. Add-ons
    no_addon_churn = df[df["NumAddOns"] == 0]["Churn"].mean() * 100
    max_addon_churn = df[df["NumAddOns"] == 6]["Churn"].mean() * 100

    # 6. Senior citizens
    senior_churn = df[df["SeniorCitizen"] == 1]["Churn"].mean() * 100
    non_senior_churn = df[df["SeniorCitizen"] == 0]["Churn"].mean() * 100

    # 7. Value segment
    hv_churn = df[df["ValueSegment"] == "High Value"]["Churn"].mean() * 100
    lv_churn = df[df["ValueSegment"] == "Low Value"]["Churn"].mean() * 100

    # 8. Revenue at risk
    rev_lost = kpis.get("Revenue Lost to Churn (USD)", 0)
    total_rev = kpis.get("Total Revenue (USD)", 1)
    rev_lost_pct = round(rev_lost / total_rev * 100, 1)

    # 9. Partner / dependents
    partner_churn = df[df["Partner"] == "Yes"]["Churn"].mean() * 100
    no_partner_churn = df[df["Partner"] == "No"]["Churn"].mean() * 100

    # 10. PaperlessBilling
    pb_churn = df[df["PaperlessBilling"] == "Yes"]["Churn"].mean() * 100
    npb_churn = df[df["PaperlessBilling"] == "No"]["Churn"].mean() * 100

    lines = [
        "=" * 70,
        "  CUSTOMER CHURN & REVENUE INTELLIGENCE — BUSINESS INSIGHTS REPORT",
        "=" * 70,
        "",
        "All figures are calculated directly from the cleaned dataset.",
        "",
    ]

    insights = [
        {
            "title": "1. Month-to-Month Contracts Drive Disproportionate Churn",
            "finding": (f"Month-to-month customers churn at {mtm_churn:.1f}% versus "
                        f"{twyr_churn:.1f}% for two-year contract holders — a "
                        f"{mtm_churn - twyr_churn:.1f}pp gap."),
            "evidence": "SQL Query 11 / Contract churn bar chart (Fig 02).",
            "impact": "Month-to-month customers represent the single largest churn risk pool.",
            "action": ("Launch contract-upgrade incentive campaigns (e.g., 10% discount "
                       "for switching to annual contracts). Focus on first 3 months.")
        },
        {
            "title": "2. New Customers (≤12 months) Are Highly Vulnerable",
            "finding": (f"Customers in their first 12 months churn at {new_churn:.1f}%, "
                        f"versus {loyal_churn:.1f}% for customers with 48+ months tenure."),
            "evidence": "Tenure band churn chart (Fig 03).",
            "impact": "Early churn destroys CLV before the customer becomes profitable.",
            "action": ("Implement a 90-day onboarding engagement program. Assign customer "
                       "success touchpoints at 30, 60, and 90 days.")
        },
        {
            "title": f"3. {highest_pm} Users Churn Most",
            "finding": (f"{highest_pm} payment method has the highest churn rate at "
                        f"{highest_pm_rate:.1f}%."),
            "evidence": "Payment method churn chart (Fig 04).",
            "impact": "Payment friction and lack of auto-pay commitment correlates with churn.",
            "action": ("Incentivise migration to automatic payment methods. "
                       "Offer a 5% bill credit for switching to auto-pay.")
        },
        {
            "title": "4. Fiber Optic Internet Customers Churn at Alarming Rates",
            "finding": (f"Fiber optic customers churn at {fiber_churn:.1f}% vs "
                        f"{dsl_churn:.1f}% for DSL customers."),
            "evidence": "Internet service churn chart (Fig 06).",
            "impact": ("High-value fiber customers leaving represents significant MRR loss. "
                       "Fiber optic is the highest ARPU segment."),
            "action": ("Investigate service-quality issues for fiber subscribers. "
                       "Deploy proactive support outreach when ticket volume spikes.")
        },
        {
            "title": "5. Add-On Services Are a Powerful Retention Tool",
            "finding": (f"Customers with no add-ons churn at {no_addon_churn:.1f}% "
                        f"vs {max_addon_churn:.1f}% for those with all 6 add-ons."),
            "evidence": "Add-ons vs churn line chart (Fig 09).",
            "impact": "Each additional add-on increases product stickiness and reduces churn.",
            "action": ("Cross-sell OnlineSecurity and TechSupport to unprotected high-risk "
                       "segments. Bundle add-ons into retention offers.")
        },
        {
            "title": "6. Senior Citizens Face Higher Churn Risk",
            "finding": (f"Senior citizens churn at {senior_churn:.1f}% vs "
                        f"{non_senior_churn:.1f}% for non-seniors."),
            "evidence": "Demographic analysis in EDA notebook.",
            "impact": "Seniors may need more support and simpler pricing clarity.",
            "action": ("Create a 'Senior Care' program with dedicated support lines and "
                       "simplified billing to reduce friction and confusion.")
        },
        {
            "title": "7. High-Value Customers Are Not Immune to Churn",
            "finding": (f"High Value segment churns at {hv_churn:.1f}% while "
                        f"Low Value segment churns at {lv_churn:.1f}%."),
            "evidence": "Value segment churn chart (Fig 07).",
            "impact": ("High-value customers churning has disproportionately large "
                       "revenue impact per customer."),
            "action": ("Deploy a dedicated high-value customer retention team. "
                       "Offer exclusive loyalty rewards to High Value customers at risk.")
        },
        {
            "title": "8. Revenue Lost to Churn Is Substantial",
            "finding": (f"${rev_lost:,.0f} in total charges ({rev_lost_pct:.1f}% of all "
                        "revenue) was generated by customers who have since churned."),
            "evidence": "KPI Summary Table / Revenue analysis SQL.",
            "impact": "This is historical lost revenue; monthly MRR risk compounds forward.",
            "action": ("Reducing churn rate by even 5 percentage points would protect "
                       "significant future MRR. Prioritise retention ROI calculations.")
        },
        {
            "title": "9. Customers Without Partners Churn More",
            "finding": (f"Customers without partners churn at {no_partner_churn:.1f}% "
                        f"vs {partner_churn:.1f}% for those with partners."),
            "evidence": "Demographic EDA.",
            "impact": "Family/shared accounts may feel more switching friction.",
            "action": ("Consider household/family plan offers to single subscribers "
                       "to increase switching cost and household commitment.")
        },
        {
            "title": "10. Paperless Billing Correlates with Higher Churn",
            "finding": (f"Paperless billing customers churn at {pb_churn:.1f}% vs "
                        f"{npb_churn:.1f}% for paper-billed customers."),
            "evidence": "Demographic EDA (billing analysis).",
            "impact": "Digital-first customers may be more price-sensitive or tech-savvy shoppers.",
            "action": ("Activate personalised digital retention journeys (email/app) "
                       "for paperless-billing customers flagged as high risk.")
        }
    ]

    for ins in insights:
        lines.append(f"\n{'─'*68}")
        lines.append(f"  {ins['title']}")
        lines.append(f"{'─'*68}")
        lines.append(f"  FINDING   : {ins['finding']}")
        lines.append(f"  EVIDENCE  : {ins['evidence']}")
        lines.append(f"  IMPACT    : {ins['impact']}")
        lines.append(f"  ACTION    : {ins['action']}")

    lines += [
        "", "=" * 70,
        "  RETENTION STRATEGY RECOMMENDATIONS",
        "=" * 70,
        "",
        "Strategy 1 — Contract Upgrade Campaign",
        "  Target   : Month-to-month customers with tenure < 12 months",
        "  Offer    : 10–15% discount on first annual contract",
        "  Channel  : Email + in-app notification",
        "",
        "Strategy 2 — Onboarding Success Program",
        "  Target   : All new customers (tenure ≤ 3 months)",
        "  Offer    : Proactive check-in calls at 30/60/90 days",
        "  Goal     : Reduce New segment churn by 20%",
        "",
        "Strategy 3 — Add-On Cross-Sell Retention",
        "  Target   : Active customers with NumAddOns = 0 or 1",
        "  Offer    : Free 3-month trial of OnlineSecurity",
        "  Rationale: Every add-on reduces churn probability",
        "",
        "Strategy 4 — High-Value At-Risk Program",
        "  Target   : BusinessSegment = 'High Value / High Risk'",
        "  Offer    : Dedicated account manager + loyalty reward",
        "  Channel  : Direct phone outreach",
        "",
        "Strategy 5 — Payment Method Migration",
        "  Target   : Electronic check users with high churn risk",
        "  Offer    : $10 bill credit for switching to auto-pay",
        "  Rationale: Auto-pay reduces voluntary cancellation friction",
        ""
    ]

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[REPORT] Business insights report saved -> {path}")
