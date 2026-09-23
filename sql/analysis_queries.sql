-- Hospital Readmissions Analysis — SQL (SQLite dialect)
-- Table: readmissions  (loaded from data/hospital_readmissions_data.csv by analysis.py)
-- "Not Available" values are loaded as NULL.

-- Q1. Data quality check: total rows and suppressed records
SELECT COUNT(*)                                        AS total_rows,
       SUM(CASE WHEN excess_ratio IS NULL THEN 1 ELSE 0 END) AS suppressed_rows,
       COUNT(DISTINCT facility_id)                     AS hospitals,
       COUNT(DISTINCT condition)                       AS conditions
FROM readmissions;

-- Q2. Performance by condition: average excess ratio, volume, share of hospitals above 1.0
SELECT condition,
       ROUND(AVG(excess_ratio), 3)                                   AS avg_excess_ratio,
       SUM(discharges)                                               AS total_discharges,
       ROUND(100.0 * SUM(CASE WHEN excess_ratio > 1 THEN 1 ELSE 0 END)
             / COUNT(excess_ratio), 1)                               AS pct_hospitals_above_1
FROM readmissions
GROUP BY condition
ORDER BY avg_excess_ratio DESC;

-- Q3. Estimated excess readmissions by condition (CTE)
-- Excess = actual readmissions - readmissions expected at a ratio of 1.0
WITH excess AS (
    SELECT condition,
           readmissions - (readmissions / excess_ratio) AS excess_readmissions
    FROM readmissions
    WHERE excess_ratio IS NOT NULL
)
SELECT condition,
       ROUND(SUM(excess_readmissions), 0) AS est_excess_readmissions
FROM excess
GROUP BY condition
ORDER BY est_excess_readmissions DESC;

-- Q4. Worst-performing hospitals overall (need at least 3 reported conditions)
SELECT facility_name,
       state,
       ROUND(AVG(excess_ratio), 3) AS avg_excess_ratio,
       COUNT(excess_ratio)          AS conditions_reported
FROM readmissions
GROUP BY facility_name, state
HAVING COUNT(excess_ratio) >= 3
ORDER BY avg_excess_ratio DESC
LIMIT 10;

-- Q5. Hospitals above the 1.0 benchmark in 4 or more conditions
SELECT facility_name,
       SUM(CASE WHEN excess_ratio > 1 THEN 1 ELSE 0 END) AS conditions_above_1
FROM readmissions
GROUP BY facility_name
HAVING conditions_above_1 >= 4
ORDER BY conditions_above_1 DESC, facility_name;

-- Q6. Worst 3 hospitals within each condition (window function)
WITH ranked AS (
    SELECT condition,
           facility_name,
           excess_ratio,
           RANK() OVER (PARTITION BY condition ORDER BY excess_ratio DESC) AS rank_in_condition
    FROM readmissions
    WHERE excess_ratio IS NOT NULL
)
SELECT condition, rank_in_condition, facility_name, excess_ratio
FROM ranked
WHERE rank_in_condition <= 3
ORDER BY condition, rank_in_condition;

-- Q7. Performance by state
SELECT state,
       ROUND(AVG(excess_ratio), 3) AS avg_excess_ratio,
       SUM(discharges)             AS total_discharges
FROM readmissions
GROUP BY state
ORDER BY avg_excess_ratio DESC;
