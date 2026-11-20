-- =============================================================================
-- 01_schema.sql
-- Customer Churn & Revenue Intelligence Analytics
-- PostgreSQL Database Schema
-- =============================================================================
-- How to use:
--   psql -U <username> -d <dbname> -f sql/01_schema.sql
--
-- Or from psql prompt:
--   \i sql/01_schema.sql
-- =============================================================================

-- Create the analytics database (run as superuser if needed)
-- CREATE DATABASE churn_analytics;

-- Connect to the database
-- \c churn_analytics

-- Drop and recreate tables for a clean load
DROP TABLE IF EXISTS customer_churn CASCADE;
DROP TABLE IF EXISTS customer_segments CASCADE;
DROP TABLE IF EXISTS model_predictions CASCADE;

-- =============================================================================
-- MAIN CUSTOMER TABLE
-- =============================================================================
CREATE TABLE customer_churn (
    customer_id             VARCHAR(20)    PRIMARY KEY,
    gender                  VARCHAR(10)    NOT NULL,
    senior_citizen          SMALLINT       NOT NULL CHECK (senior_citizen IN (0, 1)),
    partner                 VARCHAR(5)     NOT NULL CHECK (partner IN ('Yes', 'No')),
    dependents              VARCHAR(5)     NOT NULL CHECK (dependents IN ('Yes', 'No')),
    tenure                  SMALLINT       NOT NULL CHECK (tenure >= 0),
    phone_service           VARCHAR(5)     NOT NULL,
    multiple_lines          VARCHAR(25)    NOT NULL,
    internet_service        VARCHAR(20)    NOT NULL,
    online_security         VARCHAR(25)    NOT NULL,
    online_backup           VARCHAR(25)    NOT NULL,
    device_protection       VARCHAR(25)    NOT NULL,
    tech_support            VARCHAR(25)    NOT NULL,
    streaming_tv            VARCHAR(25)    NOT NULL,
    streaming_movies        VARCHAR(25)    NOT NULL,
    contract                VARCHAR(20)    NOT NULL,
    paperless_billing       VARCHAR(5)     NOT NULL,
    payment_method          VARCHAR(40)    NOT NULL,
    monthly_charges         NUMERIC(8,2)   NOT NULL CHECK (monthly_charges > 0),
    total_charges           NUMERIC(10,2)  NOT NULL CHECK (total_charges >= 0),
    avg_monthly_revenue     NUMERIC(10,2),
    num_addons              SMALLINT       DEFAULT 0,
    tenure_band             VARCHAR(30),
    value_segment           VARCHAR(20),
    senior_citizen_label    VARCHAR(15),
    churn_risk_score        NUMERIC(5,1),
    projected_clv           NUMERIC(10,2),
    historical_clv          NUMERIC(10,2),
    business_segment        VARCHAR(35),
    churn                   SMALLINT       NOT NULL CHECK (churn IN (0, 1)),
    created_at              TIMESTAMP      DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- CUSTOMER SEGMENTS SUMMARY TABLE
-- (Pre-aggregated for Power BI and reporting)
-- =============================================================================
CREATE TABLE customer_segments (
    segment_id              SERIAL         PRIMARY KEY,
    segment_name            VARCHAR(35)    NOT NULL,
    customer_count          INT,
    avg_tenure              NUMERIC(6,2),
    avg_monthly_charges     NUMERIC(8,2),
    avg_num_addons          NUMERIC(4,2),
    avg_churn_risk_score    NUMERIC(5,1),
    churn_rate              NUMERIC(5,2),
    total_monthly_revenue   NUMERIC(12,2),
    created_at              TIMESTAMP      DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- MODEL PREDICTIONS TABLE
-- =============================================================================
CREATE TABLE model_predictions (
    customer_id             VARCHAR(20)    PRIMARY KEY REFERENCES customer_churn(customer_id),
    churn_probability       NUMERIC(6,4),
    predicted_churn         SMALLINT       CHECK (predicted_churn IN (0, 1)),
    risk_tier               VARCHAR(15),   -- 'Very High', 'High', 'Medium', 'Low'
    created_at              TIMESTAMP      DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- INDEXES for common query patterns
-- =============================================================================
CREATE INDEX idx_cc_churn         ON customer_churn(churn);
CREATE INDEX idx_cc_contract      ON customer_churn(contract);
CREATE INDEX idx_cc_tenure        ON customer_churn(tenure);
CREATE INDEX idx_cc_value_seg     ON customer_churn(value_segment);
CREATE INDEX idx_cc_biz_seg       ON customer_churn(business_segment);
CREATE INDEX idx_cc_payment       ON customer_churn(payment_method);
CREATE INDEX idx_cc_internet      ON customer_churn(internet_service);
CREATE INDEX idx_mp_risk          ON model_predictions(risk_tier);

-- =============================================================================
-- LOAD DATA FROM CSV
-- Update the file path to match your local system.
-- =============================================================================

-- Load main customer data (run from psql with \copy or use Python SQLAlchemy)
-- \copy customer_churn (
--     customer_id, gender, senior_citizen, partner, dependents,
--     tenure, phone_service, multiple_lines, internet_service,
--     online_security, online_backup, device_protection, tech_support,
--     streaming_tv, streaming_movies, contract, paperless_billing,
--     payment_method, monthly_charges, total_charges, avg_monthly_revenue,
--     num_addons, tenure_band, value_segment, senior_citizen_label,
--     churn_risk_score, projected_clv, historical_clv,
--     business_segment, churn
-- )
-- FROM '/absolute/path/to/data/processed/telco_churn_final.csv'
-- WITH (FORMAT CSV, HEADER TRUE, NULL '');

-- Verify row count after load:
-- SELECT COUNT(*) FROM customer_churn;

SELECT 'Schema created successfully.' AS status;
