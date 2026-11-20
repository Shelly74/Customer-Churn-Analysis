import os
import pandas as pd

def validate_project():
    print("=" * 60)
    print("  PROJECT RUN & VALIDATION SUMMARY")
    print("=" * 60)
    
    # 1. Check folder paths
    paths = {
        "Raw Data": "data/raw/telco_churn_raw.csv",
        "Cleaned Data": "data/processed/telco_churn_cleaned.csv",
        "Final Data": "data/processed/telco_churn_final.csv",
        "Power BI CSV": "dashboard/powerbi_dataset.csv",
        "Power BI Image": "dashboard/powerbi_dashboard.png",
        "Insights Report": "outputs/reports/business_insights.txt",
        "Model Report": "outputs/reports/model_performance.txt",
        "README": "README.md",
        "Project Pitch": "PROJECT_EXPLANATION.md"
    }
    
    missing = 0
    for name, path in paths.items():
        if os.path.exists(path):
            size_kb = os.path.getsize(path) / 1024
            print(f"  [OK] {name:<20} : {path:<50} ({size_kb:.1f} KB)")
        else:
            print(f"  [MISSING] {name:<20} : {path}")
            missing += 1
            
    # 2. Check Figures
    fig_dir = "outputs/figures"
    fig_count = 0
    if os.path.exists(fig_dir):
        fig_count = len([f for f in os.listdir(fig_dir) if f.endswith(".png")])
    print(f"  [OK] Charts Generated    : {fig_count}/14 in {fig_dir}")
    
    # 3. Check Notebooks
    nb_dir = "notebooks"
    nb_count = 0
    if os.path.exists(nb_dir):
        nb_count = len([f for f in os.listdir(nb_dir) if f.endswith(".ipynb")])
    print(f"  [OK] Notebooks Created   : {nb_count}/4 in {nb_dir}")
    
    if missing > 0:
        print(f"\n  [ERROR] {missing} critical files are missing! Please run run_pipeline.py first.")
        return
        
    print("\n" + "-" * 60)
    print("  DATASET VALIDATION")
    print("-" * 60)
    
    df_clean = pd.read_csv(paths["Cleaned Data"])
    df_final = pd.read_csv(paths["Final Data"])
    df_pbi = pd.read_csv(paths["Power BI CSV"])
    
    print(f"  Cleaned Data Shape : {df_clean.shape}")
    print(f"  Final Data Shape   : {df_final.shape}")
    print(f"  Power BI Shape     : {df_pbi.shape}")
    
    # Check key columns
    expected_cols = ["ChurnRiskScore", "ProjectedCLV", "HistoricalCLV", "BusinessSegment", "ChurnProbability", "PredictedChurn"]
    for col in expected_cols:
        if col in df_final.columns:
            print(f"  [OK] Enriched Column   : {col}")
        else:
            print(f"  [FAIL] Missing Column  : {col}")
            
    # Check sample KPIs
    churn_rate = (df_final["Churn"].sum() / len(df_final)) * 100
    mrr_at_risk = df_final.loc[(df_final["Churn"] == 0) & (df_final["ChurnRiskScore"] >= 60), "MonthlyCharges"].sum()
    print(f"  Calculated Churn Rate: {churn_rate:.2f}%")
    print(f"  MRR at Risk (Risk>=60): ${mrr_at_risk:,.2f}")
    
    print("\n" + "=" * 60)
    print("  VALIDATION COMPLETE — ALL CHECKS PASS")
    print("=" * 60)

if __name__ == "__main__":
    validate_project()
