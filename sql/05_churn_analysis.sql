-- =============================================================================
-- 05_churn_analysis.sql
-- Churn Analysis Queries
-- =============================================================================

-- ----------------------------------------------------------------------------
-- Q1. Overall churn rate and retention rate
-- Business: What is the company-wide churn rate?
-- Logic: COUNT FILTER and percentage calculation.
-- ----------------------------------------------------------------------------
SELECT
    COUNT(*) AS total_customers,
    COUNT(*) FILTER (WHERE churn = 1) AS churned,
    COUNT(*) FILTER (WHERE churn = 0) AS retained,
    ROUND(COUNT(*) FILTER (WHERE churn = 1) * 100.0 / COUNT(*), 2)
        AS churn_rate_pct,
    ROUND(COUNT(*) FILTER (WHERE churn = 0) * 100.0 / COUNT(*), 2)
        AS retention_rate_pct
FROM customer_churn;

-- ----------------------------------------------------------------------------
-- Q2. Churn rate by contract type
-- Business: Which contract type is the most significant churn driver?
-- Logic: GROUP BY + ROUND(AVG(churn)*100).
-- ----------------------------------------------------------------------------
SELECT
    contract,
    COUNT(*) AS total,
    SUM(churn) AS churned,
    ROUND(AVG(churn) * 100, 2) AS churn_rate_pct
FROM customer_churn
GROUP BY contract
ORDER BY churn_rate_pct DESC;

-- ----------------------------------------------------------------------------
-- Q3. Churn rate by tenure band (lifecycle stage)
-- Business: Which lifecycle stage is most vulnerable?
-- ----------------------------------------------------------------------------
SELECT
    tenure_band,
    COUNT(*) AS total,
    SUM(churn) AS churned,
    ROUND(AVG(churn) * 100, 2) AS churn_rate_pct,
    ROUND(AVG(monthly_charges), 2) AS avg_monthly_charges
FROM customer_churn
WHERE tenure_band IS NOT NULL
GROUP BY tenure_band
ORDER BY MIN(tenure);

-- ----------------------------------------------------------------------------
-- Q4. Churn by payment method
-- Business: Does payment friction correlate with churn?
-- ----------------------------------------------------------------------------
SELECT
    payment_method,
    COUNT(*) AS total,
    SUM(churn) AS churned,
    ROUND(AVG(churn) * 100, 2) AS churn_rate_pct
FROM customer_churn
GROUP BY payment_method
ORDER BY churn_rate_pct DESC;

-- ----------------------------------------------------------------------------
-- Q5. Churn rate by internet service type
-- Business: Does service type impact churn?
-- ----------------------------------------------------------------------------
SELECT
    internet_service,
    COUNT(*) AS total,
    SUM(churn) AS churned,
    ROUND(AVG(churn) * 100, 2) AS churn_rate_pct,
    ROUND(AVG(monthly_charges), 2) AS avg_monthly_charges
FROM customer_churn
GROUP BY internet_service
ORDER BY churn_rate_pct DESC;

-- ----------------------------------------------------------------------------
-- Q6. Churn by Number of Add-Ons (stickiness analysis)
-- Business: Do customers with more services churn less?
-- Logic: GROUP BY num_addons; CASE WHEN for stickiness label.
-- ----------------------------------------------------------------------------
SELECT
    num_addons,
    CASE
        WHEN num_addons = 0 THEN 'No Add-Ons (Low Stickiness)'
        WHEN num_addons BETWEEN 1 AND 2 THEN 'Low Add-Ons'
        WHEN num_addons BETWEEN 3 AND 4 THEN 'Medium Add-Ons'
        ELSE 'High Add-Ons (High Stickiness)'
    END AS stickiness_level,
    COUNT(*) AS total,
    SUM(churn) AS churned,
    ROUND(AVG(churn) * 100, 2) AS churn_rate_pct
FROM customer_churn
GROUP BY num_addons
ORDER BY num_addons;

-- ----------------------------------------------------------------------------
-- Q7. Churn rate by gender and senior citizen status
-- Business: Do demographics drive churn differences?
-- Logic: Multi-column GROUP BY with CASE WHEN for senior label.
-- ----------------------------------------------------------------------------
SELECT
    gender,
    senior_citizen_label,
    COUNT(*) AS total,
    SUM(churn) AS churned,
    ROUND(AVG(churn) * 100, 2) AS churn_rate_pct
FROM customer_churn
GROUP BY gender, senior_citizen_label
ORDER BY churn_rate_pct DESC;

-- ----------------------------------------------------------------------------
-- Q8. Churner profile — who churns? (using CTE)
-- Business: Build a composite profile of churned customers.
-- Logic: CTE filters churned customers, then aggregates their characteristics.
-- ----------------------------------------------------------------------------
WITH churned_customers AS (
    SELECT *
    FROM customer_churn
    WHERE churn = 1
)
SELECT
    'Churned Customers Profile' AS description,
    COUNT(*) AS n,
    ROUND(AVG(tenure), 1) AS avg_tenure_months,
    ROUND(AVG(monthly_charges), 2) AS avg_monthly_charges,
    ROUND(AVG(total_charges), 2) AS avg_total_charges,
    ROUND(AVG(num_addons), 2) AS avg_num_addons,
    ROUND(AVG(churn_risk_score), 1) AS avg_churn_risk_score,
    ROUND(AVG(senior_citizen)::NUMERIC * 100, 1) AS pct_senior,
    MODE() WITHIN GROUP (ORDER BY contract) AS most_common_contract,
    MODE() WITHIN GROUP (ORDER BY payment_method) AS most_common_payment,
    MODE() WITHIN GROUP (ORDER BY internet_service) AS most_common_internet
FROM churned_customers;

-- ----------------------------------------------------------------------------
-- Q9. Monthly churn trend simulated by tenure buckets
-- Business: At which tenure point does churn peak?
-- Logic: CASE WHEN for 6-month tenure buckets; window sum for running total.
-- ----------------------------------------------------------------------------
WITH tenure_buckets AS (
    SELECT
        CASE
            WHEN tenure BETWEEN 0  AND  5  THEN '00-05 months'
            WHEN tenure BETWEEN 6  AND 11  THEN '06-11 months'
            WHEN tenure BETWEEN 12 AND 17  THEN '12-17 months'
            WHEN tenure BETWEEN 18 AND 23  THEN '18-23 months'
            WHEN tenure BETWEEN 24 AND 35  THEN '24-35 months'
            WHEN tenure BETWEEN 36 AND 47  THEN '36-47 months'
            ELSE '48+ months'
        END AS tenure_bucket,
        churn
    FROM customer_churn
)
SELECT
    tenure_bucket,
    COUNT(*) AS total,
    SUM(churn) AS churned,
    ROUND(AVG(churn) * 100, 2) AS churn_rate_pct,
    SUM(SUM(churn)) OVER (
        ORDER BY tenure_bucket
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_churned_total
FROM tenure_buckets
GROUP BY tenure_bucket
ORDER BY tenure_bucket;

-- ----------------------------------------------------------------------------
-- Q10. High-risk churners — active customers most likely to churn next
-- Business: Who should retention campaigns target first?
-- Logic: Subquery for active customers, ordered by risk score; LEFT JOIN to
--        include all columns for context.
-- ----------------------------------------------------------------------------
SELECT
    c.customer_id,
    c.tenure,
    c.contract,
    c.payment_method,
    c.internet_service,
    c.monthly_charges,
    c.num_addons,
    c.churn_risk_score,
    c.value_segment,
    c.business_segment,
    c.senior_citizen_label
FROM customer_churn c
WHERE c.churn = 0
  AND c.churn_risk_score >= 70
ORDER BY c.churn_risk_score DESC, c.monthly_charges DESC
LIMIT 50;

SELECT 'Churn analysis queries complete.' AS status;
