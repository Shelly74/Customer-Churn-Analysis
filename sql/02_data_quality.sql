-- =============================================================================
-- 02_data_quality.sql
-- Data Quality Checks
-- Answers: "Is our loaded data clean and complete?"
-- =============================================================================

-- ----------------------------------------------------------------------------
-- Q1. How many total customers are loaded?
-- Logic : COUNT(*) on the main table.
-- Business: Confirms data load integrity.
-- ----------------------------------------------------------------------------
SELECT COUNT(*) AS total_customers
FROM customer_churn;

-- ----------------------------------------------------------------------------
-- Q2. Are there any NULL values in critical columns?
-- Logic : SUM(CASE WHEN col IS NULL THEN 1 ELSE 0 END) across key fields.
-- Business: Incomplete records can bias KPI calculations.
-- ----------------------------------------------------------------------------
SELECT
    SUM(CASE WHEN customer_id       IS NULL THEN 1 ELSE 0 END) AS null_customer_id,
    SUM(CASE WHEN monthly_charges   IS NULL THEN 1 ELSE 0 END) AS null_monthly_charges,
    SUM(CASE WHEN total_charges     IS NULL THEN 1 ELSE 0 END) AS null_total_charges,
    SUM(CASE WHEN tenure            IS NULL THEN 1 ELSE 0 END) AS null_tenure,
    SUM(CASE WHEN churn             IS NULL THEN 1 ELSE 0 END) AS null_churn
FROM customer_churn;

-- ----------------------------------------------------------------------------
-- Q3. Are there duplicate customer IDs?
-- Logic : GROUP BY customer_id HAVING COUNT > 1.
-- Business: Duplicate records inflate customer counts and distort churn rates.
-- ----------------------------------------------------------------------------
SELECT customer_id, COUNT(*) AS occurrence_count
FROM customer_churn
GROUP BY customer_id
HAVING COUNT(*) > 1
ORDER BY occurrence_count DESC;

-- ----------------------------------------------------------------------------
-- Q4. Monthly charges distribution summary
-- Logic : Basic descriptive stats on MonthlyCharges.
-- Business: Validates data range and flags anomalous values.
-- ----------------------------------------------------------------------------
SELECT
    MIN(monthly_charges)    AS min_charge,
    MAX(monthly_charges)    AS max_charge,
    ROUND(AVG(monthly_charges), 2) AS avg_charge,
    ROUND(STDDEV(monthly_charges), 2) AS stddev_charge,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY monthly_charges) AS q1,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY monthly_charges) AS median,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY monthly_charges) AS q3
FROM customer_churn;

-- ----------------------------------------------------------------------------
-- Q5. Tenure distribution summary
-- Logic : Descriptive stats on tenure.
-- Business: Validates that tenure ranges make business sense (0–72 months).
-- ----------------------------------------------------------------------------
SELECT
    MIN(tenure)    AS min_tenure,
    MAX(tenure)    AS max_tenure,
    ROUND(AVG(tenure), 2) AS avg_tenure,
    COUNT(*) FILTER (WHERE tenure = 0) AS zero_tenure_customers
FROM customer_churn;

-- ----------------------------------------------------------------------------
-- Q6. Churn label distribution
-- Logic : COUNT and percentage by churn value.
-- Business: Confirms class distribution before modelling.
-- ----------------------------------------------------------------------------
SELECT
    churn,
    CASE WHEN churn = 1 THEN 'Churned' ELSE 'Retained' END AS status,
    COUNT(*) AS customer_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct_of_total
FROM customer_churn
GROUP BY churn
ORDER BY churn;

-- ----------------------------------------------------------------------------
-- Q7. Validate categorical values for Contract column
-- Logic : List all distinct values; unexpected values indicate data issues.
-- ----------------------------------------------------------------------------
SELECT contract, COUNT(*) AS count
FROM customer_churn
GROUP BY contract
ORDER BY count DESC;

-- ----------------------------------------------------------------------------
-- Q8. Validate categorical values for PaymentMethod
-- ----------------------------------------------------------------------------
SELECT payment_method, COUNT(*) AS count
FROM customer_churn
GROUP BY payment_method
ORDER BY count DESC;

-- ----------------------------------------------------------------------------
-- Q9. Customers with TotalCharges < MonthlyCharges (possible data anomaly)
-- Logic : If tenure > 1, total_charges should logically be >= monthly_charges.
-- Business: Flag potential billing-data integrity issues.
-- ----------------------------------------------------------------------------
SELECT COUNT(*) AS suspicious_total_charges
FROM customer_churn
WHERE total_charges < monthly_charges
  AND tenure > 1;

-- ----------------------------------------------------------------------------
-- Q10. InternetService distribution
-- ----------------------------------------------------------------------------
SELECT internet_service, COUNT(*) AS count
FROM customer_churn
GROUP BY internet_service
ORDER BY count DESC;

SELECT 'Data quality checks complete.' AS status;
