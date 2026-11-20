
# 📊 Customer Churn Analysis | End-to-End Data Analytics Project

**Project Name:** Customer Churn Analysis  
**Domain:** Data Analytics | Business Intelligence | Customer Retention  
**Tools & Technologies:** Python, SQL, Microsoft Excel, Power BI  
**Project Level:** Beginner to Advanced

---

## 🎯 1. Project Overview

Customer Churn Analysis is a data analytics project that focuses on identifying customers who stop using a company's products or services.

The main objective of this project is to analyze customer behavior, identify the major reasons behind customer churn, and provide actionable business insights to improve customer retention.

This project uses four powerful analytics tools:

- 🐍 **Python:** Data cleaning, preprocessing, EDA, and visualization.
- 🗄️ **SQL:** Data extraction, filtering, aggregation, and customer segmentation.
- 📗 **Excel:** Data cleaning, Pivot Tables, formulas, and reporting.
- 📊 **Power BI:** Interactive dashboards, KPIs, and business intelligence.

## 🎯 2. Business Objectives

The key objectives of this project are:

1. Identify customers who have left the company.
2. Calculate the overall customer churn rate.
3. Analyze customer demographics and behavior.
4. Identify the reasons behind customer churn.
5. Analyze monthly and yearly customer contracts.
6. Understand the relationship between customer tenure and churn.
7. Identify high-risk customer segments.
8. Provide recommendations to improve customer retention.
9. Support business decisions through data-driven insights.

## 📂 3. Dataset Description

The project can use a Telecom Customer Churn dataset.

**Important dataset columns:**

| Column | Description |
|---|---|
| CustomerID | Unique customer identification |
| Gender | Customer gender |
| SeniorCitizen | Senior citizen status |
| Partner | Whether customer has a partner |
| Dependents | Whether customer has dependents |
| Tenure | Number of months with company |
| PhoneService | Phone service subscription |
| InternetService | Internet service type |
| Contract | Contract type |
| PaymentMethod | Payment method |
| MonthlyCharges | Monthly customer charges |
| TotalCharges | Total customer charges |
| Churn | Whether customer left the company |

## 🐍 4. Python – Data Analysis & EDA

Python is used to clean, transform, analyze, and visualize the dataset.

**Libraries Used:**

- Pandas – Data manipulation
- NumPy – Numerical operations
- Matplotlib – Data visualization
- Seaborn – Statistical visualization
- Scikit-learn – Machine learning (optional)

**Python Tasks:**

1. Import dataset using Pandas.
2. Check dataset shape and structure.
3. Identify missing values.
4. Remove duplicate records.
5. Handle incorrect data types.
6. Perform Exploratory Data Analysis (EDA).
7. Analyze customer churn distribution.
8. Create correlation heatmaps.
9. Analyze customer tenure and monthly charges.
10. Identify important churn patterns.

**Example Python Code:**

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Load dataset
df = pd.read_csv("customer_churn.csv")

# Dataset information
print(df.head())
print(df.info())

# Check missing values
print(df.isnull().sum())

# Check duplicates
print(df.duplicated().sum())

# Churn distribution
print(df["Churn"].value_counts())

# Churn visualization
sns.countplot(data=df, x="Churn")
plt.title("Customer Churn Distribution")
plt.show()

# Average monthly charges
print(df.groupby("Churn")["MonthlyCharges"].mean())
```

## 🗄️ 5. SQL – Customer Data Analysis

SQL is used to extract customer information and generate business insights from structured databases.

**SQL Concepts Covered:**

- SELECT, WHERE, ORDER BY
- GROUP BY and HAVING
- Aggregate Functions
- COUNT(), SUM(), AVG()
- CASE WHEN
- JOINS
- Subqueries
- CTEs
- Window Functions

**Example SQL Queries:**

**1. Total Customers**

```sql
SELECT COUNT(*) AS Total_Customers
FROM customers;
```

**2. Churned Customers**

```sql
SELECT COUNT(*) AS Churned_Customers
FROM customers
WHERE Churn = 'Yes';
```

**3. Customer Churn Rate**

```sql
SELECT
    ROUND(
        100.0 * SUM(
            CASE WHEN Churn = 'Yes'
            THEN 1 ELSE 0 END
        ) / COUNT(*), 2
    ) AS Churn_Rate
FROM customers;
```

**4. Churn by Contract Type**

```sql
SELECT
    Contract,
    COUNT(*) AS Total_Customers,
    SUM(CASE WHEN Churn = 'Yes'
        THEN 1 ELSE 0 END) AS Churned_Customers
FROM customers
GROUP BY Contract;
```

**5. Average Monthly Charges**

```sql
SELECT
    Churn,
    AVG(MonthlyCharges) AS Average_Monthly_Charges
FROM customers
GROUP BY Churn;
```

## 📗 6. Microsoft Excel – Data Cleaning & Reporting

Excel is used for initial data exploration, cleaning, calculations, and reporting.

**Excel Tasks:**

1. Import customer churn dataset.
2. Remove duplicate records.
3. Handle blank and missing values.
4. Apply filters and sorting.
5. Use Conditional Formatting.
6. Create Pivot Tables.
7. Create Pivot Charts.
8. Calculate churn percentages.
9. Create summary reports.
10. Build an Excel dashboard.

**Important Excel Formulas:**

| Formula | Purpose |
|---|---|
| COUNT() | Count numeric values |
| COUNTA() | Count non-empty cells |
| COUNTIF() | Count based on condition |
| COUNTIFS() | Count multiple conditions |
| SUM() | Calculate total |
| SUMIF() | Conditional sum |
| AVERAGE() | Calculate average |
| IF() | Logical conditions |
| IFERROR() | Handle errors |
| VLOOKUP() | Lookup values |
| XLOOKUP() | Advanced lookup |
| TRIM() | Remove extra spaces |
| CONCAT() | Combine text |

**Example Churn Rate Formula:**

```excel
=COUNTIF(M2:M7044,"Yes")/COUNTA(M2:M7044)*100
```

*Adjust the range according to your actual dataset.*

## 📊 7. Power BI – Interactive Dashboard

Power BI is used to create interactive dashboards and visualize customer churn insights.

**Dashboard KPIs:**

- 👥 Total Customers
- 🚪 Churned Customers
- 📉 Customer Churn Rate
- 💰 Average Monthly Charges
- 📅 Average Customer Tenure
- 💵 Total Revenue / Charges

**Power BI Visualizations:**

1. KPI Cards – Overall business performance.
2. Donut Chart – Churned vs Retained Customers.
3. Bar Chart – Churn by Contract Type.
4. Pie Chart – Churn by Payment Method.
5. Column Chart – Churn by Internet Service.
6. Line Chart – Customer tenure analysis.
7. Stacked Bar Chart – Churn by Gender.
8. Matrix – Customer segment analysis.
9. Slicers – Gender, Contract, Payment Method, and Internet Service.

**DAX Measures:**

Total Customers:

```dax
Total Customers =
COUNTROWS(Customers)
```

Churned Customers:

```dax
Churned Customers =
CALCULATE(
    COUNTROWS(Customers),
    Customers[Churn] = "Yes"
)
```

Retained Customers:

```dax
Retained Customers =
CALCULATE(
    COUNTROWS(Customers),
    Customers[Churn] = "No"
)
```

Churn Rate:

```dax
Churn Rate =
DIVIDE(
    [Churned Customers],
    [Total Customers],
    0
) * 100
```

Average Monthly Charges:

```dax
Average Monthly Charges =
AVERAGE(Customers[MonthlyCharges])
```

## 🔍 8. Exploratory Data Analysis (EDA)

The following analysis areas are covered:

- Customer demographics analysis.
- Customer tenure distribution.
- Monthly and total charges analysis.
- Contract type analysis.
- Payment method analysis.
- Internet service analysis.
- Customer retention analysis.
- Churn distribution by customer segments.
- Correlation analysis.

## 💡 9. Key Business Insights

The analysis aims to answer these business questions:

1. Which customer segment has the highest churn?
2. Which contract type experiences more customer churn?
3. Does shorter customer tenure increase churn?
4. Which payment methods are associated with higher churn?
5. How do monthly charges relate to customer churn?
6. Which internet service customers are more likely to leave?
7. Which customers should receive retention offers?

*Actual findings should be added after analyzing the dataset.*

## 🚀 10. Business Recommendations

Based on the actual analysis, businesses can consider:

- Offer discounts to high-risk customers.
- Introduce long-term contract incentives.
- Improve customer support services.
- Provide personalized retention offers.
- Monitor customers with short tenure.
- Improve service quality.
- Introduce customer loyalty programs.
- Identify high-value customers at risk of leaving.

## 🛠️ 11. Project Workflow

1. 📥 Data Collection
2. 📗 Excel Data Cleaning
3. 🐍 Python Data Preprocessing
4. 🔍 Exploratory Data Analysis
5. 🗄️ SQL Business Queries
6. 📊 Power BI Dashboard Development
7. 📈 Business Insights Generation
8. 💡 Recommendations & Reporting

## 📁 12. Project Folder Structure

```text
Customer-Churn-Analysis/
│
├── Dataset/
│   └── customer_churn.csv
│
├── Python/
│   └── customer_churn_analysis.ipynb
│
├── SQL/
│   └── churn_analysis.sql
│
├── Excel/
│   └── customer_churn_analysis.xlsx
│
├── PowerBI/
│   └── customer_churn_dashboard.pbix
│
├── Images/
│   └── dashboard.png
│
└── README.md
```

## 🎓 13. Skills Gained

- Data Cleaning & Preprocessing
- Exploratory Data Analysis (EDA)
- SQL Query Writing
- Data Visualization
- Dashboard Development
- Business Intelligence
- Customer Segmentation
- KPI Development
- Analytical Thinking
- Data-Driven Decision Making

## 🏁 14. Conclusion

Customer Churn Analysis demonstrates how Python, SQL, Excel, and Power BI can work together to solve real-world business problems.

This project helps understand customer behavior, identify churn patterns, analyze business performance, and develop strategies to improve customer retention.

**The ultimate goal is to convert raw customer data into meaningful business insights.**

---

### 👩‍💻 Project Credits

**Created By:** Shelly Garg  
**Project:** Customer Churn Analysis  
**Domain:** Data Analytics  
**Technologies:** Python | SQL | Excel | Power BI

⭐ If you find this project useful, don't forget to star the repository!

#DataAnalytics #CustomerChurnAnalysis #Python #SQL #PowerBI #Excel #EDA #DataVisualization #BusinessIntelligence #DataAnalyst