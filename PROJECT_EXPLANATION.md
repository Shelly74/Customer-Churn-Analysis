# Project Explanation — Customer Churn & Revenue Intelligence Analytics

*Prepared for Data Analyst fresher interviews.*

---

## 60-Second Explanation

"I built an end-to-end analytics project for a telecommunications company to address a real business problem: customer churn. Using the publicly available IBM Telco dataset of 7,043 customers, I performed complete data cleaning, exploratory data analysis, K-Means customer segmentation, and built churn prediction models using Logistic Regression and Random Forest.

The project uses Python with Pandas, NumPy, Matplotlib, Seaborn, and Scikit-learn for the analytics layer. I also wrote 50+ SQL queries in PostgreSQL covering everything from basic aggregations to window functions and CTEs. The final output includes business KPIs — like churn rate, revenue at risk, and customer lifetime value — plus a Power BI-ready dataset and evidence-based retention strategy recommendations.

My key finding was that month-to-month contract customers churn at a dramatically higher rate than two-year contract customers, and customers with zero add-on services are the most at-risk group."

---

## 2-Minute Explanation

"This project solves a problem every subscription business faces: why do customers leave, and what can we do about it?

I started with the IBM Telco Customer Churn dataset — 7,043 real customer records from a telecommunications company. The dataset includes demographic information, subscription details like contract type and internet service, payment information, and a churn label indicating whether each customer left.

**Data Cleaning:** I built a systematic cleaning pipeline. The biggest issue was `TotalCharges` being stored as a string with blank entries. I converted it to numeric and imputed blanks using a business-logical formula: tenure × MonthlyCharges. I also created six derived features — including a Churn Risk Score and Customer Lifetime Value — to enrich the analysis.

**Business KPIs:** I calculated the key metrics a business stakeholder would care about: total customers, churn rate, retention rate, total MRR, average CLV, revenue lost to churn, and monthly revenue at risk from high-risk active customers.

**EDA:** Nine visualisations, each answering a specific business question. For example: do customers on month-to-month contracts churn more than annual customers? Answer: yes, significantly. Do customers with more add-on services churn less? Answer: yes — product stickiness is a measurable retention factor.

**SQL:** I designed a PostgreSQL schema and wrote 50+ queries including window functions, CTEs, running totals, ranking, and a full retention targeting query ready for CRM export.

**Machine Learning:** Logistic Regression and Random Forest models, evaluated using accuracy, precision, recall, F1-score, and ROC-AUC. I emphasise that accuracy alone is insufficient for churn problems due to class imbalance.

**Segmentation:** K-Means clustering created 4 customer segments mapped to a High/Low Value × High/Low Risk matrix, enabling prioritised retention targeting.

The final deliverable includes a Power BI-ready dataset with 30+ columns and a complete business insights report with 10 evidence-based recommendations."

---

## 5-Minute Explanation

### The Business Problem

"The project addresses a critical challenge in subscription businesses: customer churn. When customers cancel their subscriptions, companies lose both current revenue and the customer's future lifetime value. The business question is not just 'what is our churn rate?' but 'why are customers leaving, who is most at risk, how much revenue is at stake, and what should we do about it?'

### Dataset

I used the IBM Telco Customer Churn dataset — a publicly available dataset of 7,043 telecom customers with 21 columns covering demographics, subscription features, payment information, and a churn indicator. It's licensed under the Community Data License Agreement and is widely used in the data science community.

### Phase 1 — Data Cleaning

The raw data had a few issues. `TotalCharges` was stored as a string because some blank rows were present for customers with zero tenure. Rather than dropping these rows or using mean imputation, I imputed using `tenure × MonthlyCharges` — a business-logical approach that produces an accurate estimate for new customers who haven't yet been billed.

I also investigated outliers using the IQR method. High-tenure, high-charge customers were flagged, but these are genuine long-term customers — not data errors — so they were retained. I then created six derived features: TenureBand (lifecycle stage), NumAddOns (product stickiness proxy), ValueSegment (MonthlyCharges tertile), ChurnRiskScore (weighted composite 0-100), ProjectedCLV, and HistoricalCLV.

### Phase 2 — Exploratory Data Analysis

I built nine targeted visualisations, each answering a specific business question. Key findings:

1. **Contract type is the strongest churn predictor.** Month-to-month customers churn at a rate several times higher than two-year contract holders.
2. **Tenure is inversely correlated with churn.** New customers (0–12 months) are the most vulnerable.
3. **Electronic check users have the highest payment-method churn rate.** This suggests payment friction or less commitment.
4. **Fiber optic customers churn more than DSL customers** despite higher charges.
5. **Every add-on service reduces churn probability.** Zero-add-on customers have the highest churn rate.

### Phase 3 — SQL Analysis

I designed a PostgreSQL schema with three tables: `customer_churn`, `customer_segments`, and `model_predictions`. I wrote 50+ SQL queries across six script files:

- Basic aggregations for KPIs
- GROUP BY with CASE WHEN for conditional analysis
- CTEs for multi-step queries
- Window functions: RANK(), ROW_NUMBER(), NTILE(), SUM() OVER() for running totals and revenue concentration analysis
- A full retention targeting query that joins customer data with model predictions and produces a prioritised list for the CRM team

### Phase 4 — Customer Segmentation

I applied K-Means clustering on four features: tenure, MonthlyCharges, NumAddOns, and ChurnRiskScore. I used the Elbow Method and Silhouette Score to select k=4. The resulting clusters were profiled and assigned business labels:

- **High Value / High Risk** — urgent retention priority
- **High Value / Low Risk** — protect proactively
- **Low Value / High Risk** — low-cost digital outreach
- **Low Value / Low Risk** — monitor only

### Phase 5 — Churn Prediction

I trained two models: Logistic Regression and Random Forest, both using stratified train/test splits and class weight balancing. The models are evaluated on held-out test data using five metrics. I use 5-fold cross-validation to verify generalizability.

I specifically explain why accuracy is the wrong metric for churn: with ~74% class-0 customers, a naive model achieves 74% accuracy while catching zero churners. Recall and ROC-AUC are the right metrics for this business problem.

Feature importance from Random Forest shows that tenure, contract type, and monthly charges are the top predictors — consistent with the EDA findings.

### Phase 6 — Business Insights and Recommendations

The project ends with 10 evidence-based business insights, each with:
- The specific finding with numbers from the data
- The evidence (which analysis or chart)
- The business impact
- A concrete recommended action

Five retention strategies are recommended with specific targeting criteria, offer mechanics, channels, and estimated impact. These are directly connected to the analytical findings — no generic advice.

### Technical Highlights

- **Python:** Modular src/ code with four clean modules
- **SQL:** 50+ queries demonstrating the full spectrum of analytical SQL
- **ML:** Two models with proper evaluation, cross-validation, and business context
- **Power BI:** Ready-to-import CSV with 30+ columns and recommended DAX measures
- **Documentation:** Professional README, interview prep files, and business insights report

### What I Would Do Next

If I had more time, I would add survival analysis using Kaplan-Meier curves to model the distribution of time-to-churn, SHAP values for individual customer explanations, and a Streamlit dashboard for interactive retention targeting."

---

## Key Numbers to Remember

> Run `python run_pipeline.py` to generate actual numbers. The following are example reference points:

| Metric | Approximate Value |
|--------|------------------|
| Dataset size | 7,043 customers |
| Churn rate | ~26–27% |
| Month-to-month churn rate | ~43–45% |
| Two-year contract churn rate | ~2–3% |
| New customer (≤12m) churn rate | ~45–50% |
| Electronic check churn rate | ~45% |
| Fiber optic churn rate | ~41% |

*All exact numbers are generated by the pipeline from the actual dataset.*

---

*Good luck in your interview!*
