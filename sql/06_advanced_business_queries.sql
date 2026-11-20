-- =============================================================================
-- 06_advanced_business_queries.sql
-- Advanced Business Intelligence Queries
-- Window Functions · CTEs · Ranking · Segmentation · Retention Targeting
-- =============================================================================

-- ----------------------------------------------------------------------------
-- Q1. Customer Rank within Value Segment by Monthly Charges
-- Business: Who are the top customers in each value segment?
-- Logic: RANK() window function partitioned by value_segment.
-- ----------------------------------------------------------------------------
SELECT
    customer_id,
    value_segment,
    monthly_charges,
    total_charges,
    tenure,
    churn,
    RANK() OVER (
        PARTITION BY value_segment
        ORDER BY monthly_charges DESC
    ) AS rank_within_segment
FROM customer_churn
WHERE value_segment IS NOT NULL
QUALIFY RANK() OVER (
    PARTITION BY value_segment ORDER BY monthly_charges DESC
) <= 10   -- Remove this QUALIFY if your PostgreSQL version < 15; use a subquery instead.
ORDER BY value_segment, rank_within_segment;

-- Alternative without QUALIFY (PostgreSQL compatible):
WITH ranked AS (
    SELECT
        customer_id, value_segment, monthly_charges, total_charges,
        tenure, churn,
        RANK() OVER (PARTITION BY value_segment ORDER BY monthly_charges DESC)
            AS rank_within_segment
    FROM customer_churn
    WHERE value_segment IS NOT NULL
)
SELECT * FROM ranked
WHERE rank_within_segment <= 10
ORDER BY value_segment, rank_within_segment;

-- ----------------------------------------------------------------------------
-- Q2. Running Revenue Total by Customer (ordered by join tenure)
-- Business: How does cumulative revenue accumulate across the customer base?
-- Logic: SUM(...) OVER (ORDER BY tenure ROWS UNBOUNDED PRECEDING).
-- ----------------------------------------------------------------------------
WITH revenue_ranked AS (
    SELECT
        customer_id,
        tenure,
        monthly_charges,
        total_charges,
        churn,
        SUM(total_charges) OVER (
            ORDER BY total_charges DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS running_revenue_total,
        SUM(total_charges) OVER () AS grand_total_revenue
    FROM customer_churn
)
SELECT
    customer_id, tenure, monthly_charges, total_charges, churn,
    ROUND(running_revenue_total, 2) AS running_revenue_total,
    ROUND(running_revenue_total * 100.0 / grand_total_revenue, 2)
        AS cumulative_pct_of_revenue
FROM revenue_ranked
ORDER BY total_charges DESC
LIMIT 30;

-- ----------------------------------------------------------------------------
-- Q3. Churn prediction model output with risk tiering
-- Business: Segment active customers by predicted churn probability.
-- Logic: CTE + CASE WHEN for risk tiers.
-- (Requires model_predictions table populated from modeling.py output)
-- ----------------------------------------------------------------------------
WITH risk_tiered AS (
    SELECT
        c.customer_id,
        c.monthly_charges,
        c.total_charges,
        c.contract,
        c.tenure,
        c.value_segment,
        c.business_segment,
        p.churn_probability,
        CASE
            WHEN p.churn_probability >= 0.75 THEN 'Very High Risk'
            WHEN p.churn_probability >= 0.55 THEN 'High Risk'
            WHEN p.churn_probability >= 0.35 THEN 'Medium Risk'
            ELSE 'Low Risk'
        END AS risk_tier
    FROM customer_churn c
    INNER JOIN model_predictions p ON c.customer_id = p.customer_id
    WHERE c.churn = 0
)
SELECT
    risk_tier,
    COUNT(*) AS customers,
    ROUND(AVG(monthly_charges), 2) AS avg_monthly_charges,
    ROUND(SUM(monthly_charges), 2) AS total_mrr_at_risk,
    ROUND(AVG(churn_probability), 4) AS avg_churn_probability
FROM risk_tiered
GROUP BY risk_tier
ORDER BY avg_churn_probability DESC;

-- ----------------------------------------------------------------------------
-- Q4. LAG comparison — compare each customer's charges to the segment average
-- Business: Which customers pay significantly above or below their peer group?
-- Logic: AVG() OVER (PARTITION BY) window function.
-- ----------------------------------------------------------------------------
SELECT
    customer_id,
    value_segment,
    monthly_charges,
    ROUND(AVG(monthly_charges) OVER (PARTITION BY value_segment), 2)
        AS segment_avg_charges,
    ROUND(monthly_charges -
          AVG(monthly_charges) OVER (PARTITION BY value_segment), 2)
        AS deviation_from_segment_avg,
    churn
FROM customer_churn
WHERE value_segment IS NOT NULL
ORDER BY deviation_from_segment_avg DESC
LIMIT 30;

-- ----------------------------------------------------------------------------
-- Q5. Business segment churn matrix
-- Business: 2×2 matrix: which segments are High Value + High Risk?
-- Logic: CTE with pre-computed metrics, then filtered output.
-- ----------------------------------------------------------------------------
WITH segment_matrix AS (
    SELECT
        business_segment,
        COUNT(*) AS total_customers,
        COUNT(*) FILTER (WHERE churn = 1) AS churned_count,
        ROUND(AVG(monthly_charges), 2) AS avg_monthly_charges,
        ROUND(AVG(churn) * 100, 2) AS churn_rate_pct,
        ROUND(SUM(monthly_charges), 2) AS total_mrr
    FROM customer_churn
    WHERE business_segment IS NOT NULL
    GROUP BY business_segment
)
SELECT
    business_segment,
    total_customers,
    churned_count,
    avg_monthly_charges,
    churn_rate_pct,
    total_mrr,
    CASE
        WHEN avg_monthly_charges > 65 AND churn_rate_pct > 25
            THEN '🔴 Urgent: High Value + High Churn'
        WHEN avg_monthly_charges > 65 AND churn_rate_pct <= 25
            THEN '🟢 Protect: High Value + Low Churn'
        WHEN avg_monthly_charges <= 65 AND churn_rate_pct > 25
            THEN '🟡 Monitor: Low Value + High Churn'
        ELSE '⚪ Stable: Low Value + Low Churn'
    END AS strategic_priority
FROM segment_matrix
ORDER BY avg_monthly_charges DESC, churn_rate_pct DESC;

-- ----------------------------------------------------------------------------
-- Q6. Retention ROI estimate
-- Business: What is the financial impact of retaining at-risk customers?
-- Logic: CTE to compute potential revenue saved at different retention rates.
-- ----------------------------------------------------------------------------
WITH at_risk_revenue AS (
    SELECT
        SUM(monthly_charges) AS monthly_mrr_at_risk
    FROM customer_churn
    WHERE churn = 0
      AND churn_risk_score >= 60
)
SELECT
    ROUND(monthly_mrr_at_risk, 2) AS total_mrr_at_risk,
    ROUND(monthly_mrr_at_risk * 0.10, 2) AS saved_if_10pct_retained,
    ROUND(monthly_mrr_at_risk * 0.20, 2) AS saved_if_20pct_retained,
    ROUND(monthly_mrr_at_risk * 0.30, 2) AS saved_if_30pct_retained,
    ROUND(monthly_mrr_at_risk * 12, 2) AS annualised_mrr_at_risk
FROM at_risk_revenue;

-- ----------------------------------------------------------------------------
-- Q7. Contract upgrade opportunity — month-to-month customers with long tenure
-- Business: Long-tenure month-to-month customers are upgrade candidates.
-- Logic: LEFT JOIN pattern — filter customer_churn for specific criteria.
-- ----------------------------------------------------------------------------
SELECT
    c.customer_id,
    c.tenure,
    c.monthly_charges,
    c.total_charges,
    c.num_addons,
    c.churn_risk_score,
    c.payment_method,
    c.internet_service,
    ROUND(c.monthly_charges * 12, 2) AS potential_annual_value
FROM customer_churn c
WHERE c.contract = 'Month-to-month'
  AND c.tenure >= 12
  AND c.churn = 0
ORDER BY c.monthly_charges DESC, c.tenure DESC
LIMIT 40;

-- ----------------------------------------------------------------------------
-- Q8. Senior citizen × internet service churn deep-dive
-- Business: Are seniors struggling specifically with fiber optic pricing?
-- Logic: Multi-dimension GROUP BY with conditional aggregation.
-- ----------------------------------------------------------------------------
SELECT
    senior_citizen_label,
    internet_service,
    COUNT(*) AS customers,
    ROUND(AVG(monthly_charges), 2) AS avg_monthly_charges,
    ROUND(AVG(churn) * 100, 2) AS churn_rate_pct,
    COUNT(*) FILTER (WHERE churn = 1) AS churned_count
FROM customer_churn
GROUP BY senior_citizen_label, internet_service
ORDER BY churn_rate_pct DESC;

-- ----------------------------------------------------------------------------
-- Q9. NTILE revenue concentration (top 20% of customers contribute what % MRR?)
-- Business: Revenue concentration / Pareto analysis.
-- Logic: NTILE(5) window function.
-- ----------------------------------------------------------------------------
WITH quintile_data AS (
    SELECT
        customer_id,
        monthly_charges,
        NTILE(5) AS revenue_quintile
    FROM customer_churn
    WHERE churn = 0
)
SELECT
    revenue_quintile,
    COUNT(*) AS customers,
    ROUND(SUM(monthly_charges), 2) AS total_mrr,
    ROUND(SUM(monthly_charges) * 100.0 /
          SUM(SUM(monthly_charges)) OVER (), 2) AS pct_of_active_mrr,
    ROUND(MIN(monthly_charges), 2) AS min_charge,
    ROUND(MAX(monthly_charges), 2) AS max_charge
FROM quintile_data
GROUP BY revenue_quintile
ORDER BY revenue_quintile DESC;

-- ----------------------------------------------------------------------------
-- Q10. Full retention targeting report — ready for Power BI / CRM export
-- Business: Provides a prioritised list for the retention campaigns team.
-- Logic: CTE + LEFT JOIN to model_predictions + CASE WHEN for action priority.
-- ----------------------------------------------------------------------------
WITH retention_targets AS (
    SELECT
        c.customer_id,
        c.gender,
        c.senior_citizen_label,
        c.tenure,
        c.contract,
        c.internet_service,
        c.payment_method,
        c.monthly_charges,
        c.total_charges,
        c.num_addons,
        c.churn_risk_score,
        c.value_segment,
        c.business_segment,
        COALESCE(p.churn_probability, 0) AS churn_probability,
        CASE
            WHEN c.churn_risk_score >= 75 AND c.value_segment = 'High Value'
                THEN '1 - Priority Urgent'
            WHEN c.churn_risk_score >= 60 AND c.value_segment = 'High Value'
                THEN '2 - Priority High'
            WHEN c.churn_risk_score >= 75 AND c.value_segment != 'High Value'
                THEN '3 - Priority Medium'
            ELSE '4 - Priority Standard'
        END AS retention_priority,
        CASE
            WHEN c.contract = 'Month-to-month' AND c.tenure >= 12
                THEN 'Contract Upgrade Offer'
            WHEN c.num_addons = 0
                THEN 'Add-On Cross-Sell'
            WHEN c.payment_method LIKE '%check%'
                THEN 'Payment Method Migration'
            ELSE 'General Retention Outreach'
        END AS recommended_action
    FROM customer_churn c
    LEFT JOIN model_predictions p ON c.customer_id = p.customer_id
    WHERE c.churn = 0
      AND c.churn_risk_score >= 55
)
SELECT *
FROM retention_targets
ORDER BY retention_priority, monthly_charges DESC;

SELECT 'Advanced business queries complete.' AS status;
