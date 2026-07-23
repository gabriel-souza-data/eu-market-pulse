-- ============================================================
-- EU Market Pulse — Analytical Queries
-- ============================================================

-- Query 1: Ranking within each region group
SELECT 
    c.region_group,
    c.country_name,
    k.overall_expansion_score,
    RANK() OVER (
        PARTITION BY c.region_group 
        ORDER BY k.overall_expansion_score DESC
    ) AS rank_in_region
FROM country_kpis k
JOIN countries c ON k.country_code = c.country_code
ORDER BY c.region_group, rank_in_region;


-- Query 2: Year-over-year change in inflation rate per country
SELECT 
    country_code,
    year,
    inflation_rate,
    inflation_rate - LAG(inflation_rate) OVER (
        PARTITION BY country_code 
        ORDER BY year
    ) AS yoy_change
FROM market_indicators
ORDER BY country_code, year;


-- Query 3: Top 5 expansion candidates, combining all business dimensions
WITH latest_indicators AS (
    SELECT DISTINCT ON (country_code)
        country_code,
        year,
        inflation_rate,
        price_level_index,
        house_price_index
    FROM market_indicators
    ORDER BY country_code, year DESC
)
SELECT 
    c.country_name,
    c.region_group,
    li.inflation_rate AS latest_inflation_rate,
    li.price_level_index AS latest_price_level,
    k.overall_expansion_score,
    RANK() OVER (ORDER BY k.overall_expansion_score DESC) AS overall_rank
FROM country_kpis k
JOIN countries c ON k.country_code = c.country_code
JOIN latest_indicators li ON k.country_code = li.country_code
ORDER BY overall_rank
LIMIT 5;


-- Query 4: Top 3 countries within each region
WITH ranked_countries AS (
    SELECT 
        c.region_group,
        c.country_name,
        k.overall_expansion_score,
        RANK() OVER (
            PARTITION BY c.region_group 
            ORDER BY k.overall_expansion_score DESC
        ) AS rank_in_region
    FROM country_kpis k
    JOIN countries c ON k.country_code = c.country_code
)
SELECT *
FROM ranked_countries
WHERE rank_in_region <= 3
ORDER BY region_group, rank_in_region;