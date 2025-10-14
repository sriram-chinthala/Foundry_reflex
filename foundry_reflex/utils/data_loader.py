# In: foundry_reflex/utils/data_loader.py

import duckdb
import pandas as pd
from pathlib import Path
import yaml

try:
    with open("config.yaml", "r") as f:
        CONFIG = yaml.safe_load(f)
    DB_PATH = CONFIG.get("paths", {}).get("market_data_db")
except FileNotFoundError:
    DB_PATH = "data/market_data.duckdb"

def get_price_data(symbol: str, start_date, end_date) -> pd.DataFrame:
    """
    Fetches historical price data for a given symbol from the DuckDB database.
    """
    try:
        con = duckdb.connect(database=DB_PATH, read_only=True)
        query = f"""
        SELECT
            "Date" as date, "Open" as open, "High" as high,
            "Low" as low, "Close" as close, "Volume" as volume
        FROM market_data
        WHERE "Ticker" = '{symbol}'
        AND "Date" >= '{start_date}'
        AND "Date" <= '{end_date}'
        ORDER BY "Date" ASC
        """
        data_df = con.execute(query).fetchdf()
        
        if 'date' in data_df.columns:
            data_df['date'] = pd.to_datetime(data_df['date'])
            data_df.set_index('date', inplace=True)

        con.close()
        return data_df
        
    except Exception as e:
        print(f"Failed to load price data for {symbol}: {e}")
        return pd.DataFrame()