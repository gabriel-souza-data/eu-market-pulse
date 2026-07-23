-- ============================================================
-- EU Market Pulse — Database Schema
-- ============================================================

-- Dimension table: country reference data
CREATE TABLE countries (
    country_code VARCHAR(2) PRIMARY KEY,
    country_name VARCHAR(50) NOT NULL UNIQUE,
    region_group VARCHAR(30) NOT NULL
);

-- Fact table: yearly market indicators by country
CREATE TABLE market_indicators (
    id SERIAL PRIMARY KEY,
    country_code VARCHAR(2) NOT NULL REFERENCES countries(country_code),
    year INTEGER NOT NULL,
    inflation_rate NUMERIC(5,2),
    price_level_index NUMERIC(6,2),
    house_price_index NUMERIC(6,2),
    UNIQUE (country_code, year)
);

-- Aggregated table: business KPI scores by country
CREATE TABLE country_kpis (
    country_code VARCHAR(2) PRIMARY KEY REFERENCES countries(country_code),
    cost_of_living_score NUMERIC(5,2),
    inflation_stability_score NUMERIC(5,2),
    housing_pressure_score NUMERIC(5,2),
    overall_expansion_score NUMERIC(5,2)
);