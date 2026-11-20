-- =============================================================================
-- 04_revenue_analysis.sql
-- Revenue Analysis — MRR, CLV, Revenue at Risk
-- =============================================================================

-- ----------------------------------------------------------------------------
-- Q1. Top-level revenue KPIs
-- Business: What is the overall revenue position?
-- Logic: SUM, AVG, COUNT aggregations on the full table.
-- ----------------------------------------------------------------------------
SELECT
    COUNT(*)                                           AS total_customers,
    SUM(monthly_charges)                               AS total_mrr,
    ROUND(AVG(monthly_charges), 2)                     AS avg_monthly_charges,
    SUM(total_charges)                                 AS total_historical_revenue,
    ROUND(AVG(total_charges), 2)                       AS avg_customer_revenue,
    ROUND(AVG(historical_clv), 2)                      AS avg_historical_clv,
    ROUND(AVG(projected_clv), 2)                       AS avg_projected_clv
FROM customer_churn;

-- ----------------------------------------------------------------------------
-- Q2. Monthly Recurring Revenue (MRR) by Contract Type
-- Business: Which contract type contributes the most MRR?
-- Logic: SUM(monthly_charges) grouped by contract.
-- ----------------------------------------------------------------------------
SELECT
    contract,
    COUNT(*) AS customers,
    ROUND(SUM(monthly_charges), 2) AS total_mrr,
    ROUND(AVG(monthly_charges), 2) AS avg_mrr_per_customer,
    ROUND(SUM(monthly_charges) * 100.0 /
          SUM(SUM(monthly_charges)) OVER (), 2) AS pct_of_total_mrr
FROM customer_churn
GROUP BY contract
ORDER BY total_mrr DESC;

-- ----------------------------------------------------------------------------
-- Q3. Revenue by Internet Service
-- Business: Which internet tier generates the most revenue?
-- ----------------------------------------------------------------------------
SELECT
    internet_service,
    COUNT(*) AS customers,
    ROUND(SUM(monthly_charges), 2) AS total_mrr,
    ROUND(AVG(monthly_charges), 2) AS avg_mrr,
    ROUND(AVG(total_charges), 2) AS avg_lifetime_revenue
FROM customer_churn
GROUP BY internet_service
ORDER BY total_mrr DESC;

-- ----------------------------------------------------------------------------
-- Q4. Revenue Lost to Churn
-- Business: How much total & monthly revenue was lost to churned customers?
-- Logic: Filter WHERE churn = 1 and SUM both charge columns.
-- ----------------------------------------------------------------------------
SELECT
    'Churned Customers' AS segment,
    COUNT(*) AS churned_customers,
    ROUND(SUM(total_charges), 2) AS total_historical_revenue_lost,
    ROUND(SUM(monthly_charges), 2) AS monthly_revenue_lost,
    ROUND(AVG(monthly_charges), 2) AS avg_monthly_charges,
    ROUND(AVG(total_charges), 2) AS avg_revenue_per_churned_customer
FROM customer_churn
WHERE churn = 1;

-- ----------------------------------------------------------------------------
-- Q5. Revenue at Risk — Active customers with high churn risk
-- Business: What MRR could be lost next month from high-risk active customers?
-- Logic: Subquery to identify at-risk customers; LEFT JOIN style aggregation.
-- ----------------------------------------------------------------------------
WITH at_risk AS (
    SELECT
        customer_id,
        monthly_charges,
        churn_risk_score,
        business_segment,
        CASE
            WHEN churn_risk_score >= 75 THEN 'Very High Risk'
            WHEN churn_risk_score >= 60 THEN 'High Risk'
            WHEN churn_risk_score >= 45 THEN 'Medium Risk'
            ELSE 'Low Risk'
        END AS risk_tier
    FROM customer_churn
    WHERE churn = 0   -- active customers only
)
SELECT
    risk_tier,
    COUNT(*) AS customers_at_risk,
    ROUND(SUM(monthly_charges), 2) AS mrr_at_risk,
    ROUND(AVG(monthly_charges), 2) AS avg_monthly_charges
FROM at_risk
GROUP BY risk_tier
ORDER BY mrr_at_risk DESC;

-- ----------------------------------------------------------------------------
-- Q6. Customer Lifetime Value — Top 20 by Projected CLV
-- Business: Which customers are most valuable on a forward-looking basis?
-- Logic: ROW_NUMBER() window function for ranking.
-- ----------------------------------------------------------------------------
SELECT
    ROW_NUMBER() OVER (ORDER BY projected_clv DESC) AS clv_rank,
    customer_id,
    tenure,
    contract,
    value_segment,
    business_segment,
    monthly_charges,
    total_charges,
    ROUND(projected_clv, 2) AS projected_clv,
    churn_risk_score,
    churn
FROM customer_churn
ORDER BY projected_clv DESC
LIMIT 20;

-- ----------------------------------------------------------------------------
-- Q7. Revenue distribution by Value Segment and Churn Status
-- Business: What portion of each segment's revenue is retained vs lost?
-- Logic: CASE WHEN churn to pivot the aggregation.
-- ----------------------------------------------------------------------------
SELECT
    value_segment,
    ROUND(SUM(CASE WHEN churn = 0 THEN total_charges ELSE 0 END), 2)
        AS retained_revenue,
    ROUND(SUM(CASE WHEN churn = 1 THEN total_charges ELSE 0 END), 2)
        AS lost_revenue,
    ROUND(SUM(total_charges), 2) AS total_revenue,
    ROUND(
        SUM(CASE WHEN churn = 1 THEN total_charges ELSE 0 END) * 100.0 /
        NULLIF(SUM(total_charges), 0),
        2
    ) AS pct_revenue_lost
FROM customer_churn
WHERE value_segment IS NOT NULL
GROUP BY value_segment
ORDER BY total_revenue DESC;

-- ----------------------------------------------------------------------------
-- Q8. MRR Percentile Distribution
-- Business: Revenue concentration — do top 10% of customers drive most MRR?
-- Logic: NTILE window function.
-- ----------------------------------------------------------------------------
WITH ntile_data AS (
    SELECT
        customer_id,
        monthly_charges,
        NTILE(10) AS decile
    FROM customer_churn
    WHERE churn = 0
)
SELECT
    decile,
    COUNT(*) AS customers,
    ROUND(MIN(monthly_charges), 2) AS min_charges,
    ROUND(MAX(monthly_charges), 2) AS max_charges,
    ROUND(SUM(monthly_charges), 2) AS total_mrr,
    ROUND(SUM(monthly_charges) * 100.0 /
          SUM(SUM(monthly_charges)) OVER (), 2) AS pct_of_active_mrr
FROM ntile_data
GROUP BY decile
ORDER BY decile;

-- ----------------------------------------------------------------------------
-- Q9. Avg revenue per customer — Business Segment comparison
-- Business: Which business segment generates the highest revenue per head?
-- ----------------------------------------------------------------------------
SELECT
    business_segment,
    COUNT(*) AS customers,
    ROUND(AVG(monthly_charges), 2) AS avg_monthly_charges,
    ROUND(AVG(total_charges), 2) AS avg_total_charges,
    ROUND(AVG(projected_clv), 2) AS avg_projected_clv,
    ROUND(AVG(churn) * 100, 2) AS churn_rate_pct
FROM customer_churn
WHERE business_segment IS NOT NULL
GROUP BY business_segment
ORDER BY avg_monthly_charges DESC;

-- ----------------------------------------------------------------------------
-- Q10. High-value customers at churn risk
-- Business: Which high-value customers need immediate retention action?
-- Logic: CTE for high-value + high-risk filter; ordered by churn risk score.
-- ----------------------------------------------------------------------------
WITH high_value_at_risk AS (
    SELECT
        customer_id,
        tenure,
        contract,
        payment_method,
        monthly_charges,
        total_charges,
        churn_risk_score,
        num_addons,
        value_segment,
        business_segment
    FROM customer_churn
    WHERE value_segment = 'High Value'
      AND churn = 0
      AND churn_risk_score >= 60
)
SELECT *
FROM high_value_at_risk
ORDER BY churn_risk_score DESC, monthly_charges DESC
LIMIT 30;

SELECT 'Revenue analysis queries complete.' AS status;
