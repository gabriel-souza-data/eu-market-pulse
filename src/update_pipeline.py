"""
EU Market Pulse — Automated Data Update Pipeline

Fetches the latest HICP inflation rate, price level index, and house price 
index data directly from the Eurostat API, cleans it, and upserts it into 
the Supabase (Postgres) `market_indicators` table.

Designed to run unattended on a schedule via GitHub Actions.
"""

import os
import sys
import logging
import eurostat
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# ── Configuration ────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

COUNTRY_CODES = ['GB', 'CH', 'IE', 'DE', 'FR', 'NL', 'AT', 'BE',
                  'PT', 'ES', 'IT', 'GR', 'PL', 'RO', 'HU', 'CZ',
                  'SE', 'DK', 'FI']

EUROSTAT_CODE_MAP = {'EL': 'GR', 'UK': 'GB'}

UPSERT_QUERY = text("""
    INSERT INTO market_indicators (country_code, year, inflation_rate, price_level_index, house_price_index)
    VALUES (:country_code, :year, :inflation_rate, :price_level_index, :house_price_index)
    ON CONFLICT (country_code, year)
    DO UPDATE SET
        inflation_rate = EXCLUDED.inflation_rate,
        price_level_index = EXCLUDED.price_level_index,
        house_price_index = EXCLUDED.house_price_index;
""")


# ── Fetch and Clean Functions ────────────────────────────────────
def fetch_and_reshape(dataset_code, value_column_name, unit_filter=None, min_year=None):
    """Fetch a Eurostat dataset and reshape it from wide to long format."""
    logger.info(f"Fetching dataset: {dataset_code}")
    df_raw = eurostat.get_data_df(dataset_code)

    if unit_filter:
        df_raw = df_raw[df_raw['unit'] == unit_filter].copy()

    df_clean = df_raw.rename(columns={'geo\\TIME_PERIOD': 'country_code'})
    year_columns = [col for col in df_clean.columns if col.isdigit()]

    df_long = df_clean.melt(
        id_vars=['country_code'],
        value_vars=year_columns,
        var_name='year',
        value_name=value_column_name
    )
    df_long['year'] = df_long['year'].astype(int)
    df_long['country_code'] = df_long['country_code'].replace(EUROSTAT_CODE_MAP)

    if min_year:
        df_long = df_long[df_long['year'] >= min_year]

    df_long = df_long[df_long['country_code'].isin(COUNTRY_CODES)].dropna(subset=[value_column_name])
    df_long = df_long.sort_values(['country_code', 'year']).reset_index(drop=True)

    logger.info(f"  -> {len(df_long)} rows, {df_long['country_code'].nunique()} countries")
    return df_long


def build_market_indicators():
    """Fetch all three datasets and merge into a single table."""
    df_inflation = fetch_and_reshape('tec00118', 'inflation_rate')
    df_price = fetch_and_reshape('tec00120', 'price_level_index')
    df_house = fetch_and_reshape('tipsho10', 'house_price_index', unit_filter='I15_A_AVG', min_year=2016)

    merged = df_inflation.merge(
        df_price, on=['country_code', 'year'], how='left'
    ).merge(
        df_house, on=['country_code', 'year'], how='left'
    )
    return merged


# ── Database Upsert ──────────────────────────────────────────────
def upsert_market_indicators(engine, df):
    """Upsert all rows into the market_indicators table."""
    records = df.to_dict(orient='records')
    with engine.connect() as connection:
        for record in records:
            connection.execute(UPSERT_QUERY, record)
        connection.commit()
    logger.info(f"Upsert complete: {len(records)} rows processed.")


# ── Main ──────────────────────────────────────────────────────────
def main():
    load_dotenv()
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        logger.error("DATABASE_URL not found in environment. Aborting.")
        sys.exit(1)

    try:
        engine = create_engine(database_url)
        df = build_market_indicators()
        upsert_market_indicators(engine, df)
        logger.info("Pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()