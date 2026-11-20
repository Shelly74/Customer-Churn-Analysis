-- =============================================================================
-- 03_customer_analysis.sql
-- Customer Demographics and Profile Analysis
-- =============================================================================

-- ----------------------------------------------------------------------------
-- Q1. Gender distribution
-- Business: Understand demographic composition.
-- ----------------------------------------------------------------------------
SELECT
    gender,
    COUNT(*) AS customer_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct_of_total,
    ROUND(AVG(monthly_charges), 2) AS avg_monthly_charges
FROM customer_churn
GROUP BY gender
ORDER BY customer_count DESC;

-- ----------------------------------------------------------------------------
-- Q2. Senior citizen customer profile
-- Business: Do seniors represent a special segment?
-- ----------------------------------------------------------------------------
SELECT
    senior_citizen_label,
    COUNT(*) AS count,
    ROUND(AVG(monthly_charges), 2) AS avg_monthly_charges,
    ROUND(AVG(tenure), 1) AS avg_tenure_months,
    ROUND(AVG(churn) * 100, 2) AS churn_rate_pct
FROM customer_churn
GROUP BY senior_citizen_label
ORDER BY churn_rate_pct DESC;

-- ----------------------------------------------------------------------------
-- Q3. Partner and Dependents cross-analysis
-- Business: Does household status affect churn?
-- Logic: CASE WHEN to create a household profile column.
-- ----------------------------------------------------------------------------
SELECT
    partner,
    dependents,
    COUNT(*) AS customers,
    ROUND(AVG(monthly_charges), 2) AS avg_monthly_charges,
    ROUND(AVG(churn) * 100, 2) AS churn_rate_pct
FROM customer_churn
GROUP BY partner, dependents
ORDER BY churn_rate_pct DESC;

-- ----------------------------------------------------------------------------
-- Q4. Tenure band customer distribution
-- Business: How many customers are in each lifecycle stage?
-- ----------------------------------------------------------------------------
SELECT
    tenure_band,
    COUNT(*) AS customers,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct_of_total,
    ROUND(AVG(monthly_charges), 2) AS avg_monthly_charges,
    ROUND(AVG(total_charges), 2) AS avg_total_charges,
    ROUND(AVG(churn) * 100, 2) AS churn_rate_pct
FROM customer_churn
WHERE tenure_band IS NOT NULL
GROUP BY tenure_band
ORDER BY MIN(tenure);

-- ----------------------------------------------------------------------------
-- Q5. Contract type distribution and profile
-- Business: What proportion of customers are on each contract?
-- ----------------------------------------------------------------------------
SELECT
    contract,
    COUNT(*) AS customer_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct_of_customers,
    ROUND(AVG(monthly_charges), 2) AS avg_monthly_charges,
    ROUND(AVG(tenure), 1) AS avg_tenure_months,
    ROUND(AVG(churn) * 100, 2) AS churn_rate_pct,
    SUM(monthly_charges) AS total_monthly_revenue
FROM customer_churn
GROUP BY contract
ORDER BY avg_monthly_charges DESC;

-- ----------------------------------------------------------------------------
-- Q6. Payment method distribution
-- ----------------------------------------------------------------------------
SELECT
    payment_method,
    COUNT(*) AS customer_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct_of_customers,
    ROUND(AVG(monthly_charges), 2) AS avg_monthly_charges,
    ROUND(AVG(churn) * 100, 2) AS churn_rate_pct
FROM customer_churn
GROUP BY payment_method
ORDER BY churn_rate_pct DESC;

-- ----------------------------------------------------------------------------
-- Q7. Internet service × Contract cross-analysis
-- Business: Which internet+contract combination is highest risk?
-- Logic: INNER JOIN via GROUP BY multiple columns.
-- ----------------------------------------------------------------------------
SELECT
    internet_service,
    contract,
    COUNT(*) AS customers,
    ROUND(AVG(monthly_charges), 2) AS avg_monthly_charges,
    ROUND(AVG(churn) * 100, 2) AS churn_rate_pct
FROM customer_churn
GROUP BY internet_service, contract
ORDER BY churn_rate_pct DESC;

-- ----------------------------------------------------------------------------
-- Q8. Add-on service adoption rate
-- Business: What % of customers have each add-on service?
-- Logic: Conditional aggregation with CASE WHEN.
-- ----------------------------------------------------------------------------
SELECT
    ROUND(SUM(CASE WHEN online_security     = 'Yes' THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 1)
        AS pct_online_security,
    ROUND(SUM(CASE WHEN online_backup       = 'Yes' THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 1)
        AS pct_online_backup,
    ROUND(SUM(CASE WHEN device_protection   = 'Yes' THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 1)
        AS pct_device_protection,
    ROUND(SUM(CASE WHEN tech_support        = 'Yes' THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 1)
        AS pct_tech_support,
    ROUND(SUM(CASE WHEN streaming_tv        = 'Yes' THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 1)
        AS pct_streaming_tv,
    ROUND(SUM(CASE WHEN streaming_movies    = 'Yes' THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 1)
        AS pct_streaming_movies
FROM customer_churn;

-- ----------------------------------------------------------------------------
-- Q9. Customers ranked by total charges (top 20)
-- Business: Who are the most revenue-generating customers?
-- Logic: ORDER BY with LIMIT and ROW_NUMBER() window function.
-- ----------------------------------------------------------------------------
SELECT
    ROW_NUMBER() OVER (ORDER BY total_charges DESC) AS rank,
    customer_id,
    contract,
    internet_service,
    tenure,
    monthly_charges,
    total_charges,
    churn,
    business_segment
FROM customer_churn
ORDER BY total_charges DESC
LIMIT 20;

-- ----------------------------------------------------------------------------
-- Q10. Value segment profile
-- Business: Understand the revenue and risk profile of each value tier.
-- Logic: GROUP BY value_segment.
-- ----------------------------------------------------------------------------
SELECT
    value_segment,
    COUNT(*) AS customers,
    ROUND(AVG(monthly_charges), 2) AS avg_monthly_charges,
    ROUND(AVG(tenure), 1) AS avg_tenure,
    ROUND(AVG(num_addons), 2) AS avg_num_addons,
    ROUND(AVG(churn) * 100, 2) AS churn_rate_pct,
    ROUND(SUM(monthly_charges), 2) AS total_monthly_rev
FROM customer_churn
WHERE value_segment IS NOT NULL
GROUP BY value_segment
ORDER BY avg_monthly_charges DESC;

SELECT 'Customer analysis queries complete.' AS status;
