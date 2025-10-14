import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))
import duckdb
import yaml
import tomllib
import pandas as pd
from utils.logger_setup import get_logger
from utils.symbol_resolver import get_symbol_master, resolve_symbols
from utils.fyers_dataprovider import fetch_all_data_concurrently
from utils.regime_filter import calculate_market_regime
from utils.rs_ranking import calculate_rs_ranking

logger = get_logger("pipeline", "logs/pipeline.log")

def load_config():
    # This path is now correct, going up three levels to the Root Folder
    config_path = Path(__file__).parent.parent.parent / "config.yaml"
    with open(config_path, 'r') as file: return yaml.safe_load(file)

def load_credentials():
    # This path is also now correct, pointing to the Root Folder
    secrets_path = Path(__file__).parent.parent.parent / "secrets.toml"
    with open(secrets_path, 'rb') as file: secrets = tomllib.load(file)
    creds = secrets.get('fyers_credentials', {}) # This key might be 'fyers' based on other files
    if not creds:
         creds = secrets.get('fyers', {}) # Check for the other common key name

    if 'PASTE_YOUR' in creds.get('access_token', ''):
        raise ValueError("Access token in secrets.toml is a placeholder. Please run 'generate_fyers_token.py' and update it.")
    logger.info("Secrets and access token loaded.")
    return creds

def setup_database(conn):
    conn.execute("CREATE TABLE IF NOT EXISTS market_data (Date DATE, Ticker VARCHAR, Open DOUBLE, High DOUBLE, Low DOUBLE, Close DOUBLE, Volume BIGINT, PRIMARY KEY (Date, Ticker));")
    conn.execute("CREATE TABLE IF NOT EXISTS market_regimes (Date DATE PRIMARY KEY, Ticker VARCHAR, Close DOUBLE, SMA DOUBLE, ADX DOUBLE, Regime VARCHAR);")
    conn.execute("CREATE TABLE IF NOT EXISTS rs_rankings (Ticker VARCHAR PRIMARY KEY, Last_Date DATE, Last_Close DOUBLE, RS_Score DOUBLE, RS_Rank DOUBLE);")
    logger.info("Database setup complete.")
def save_data_to_db(conn, all_market_data_df, regime_df, rankings_df):
    conn.execute("INSERT OR IGNORE INTO market_data BY NAME SELECT * FROM all_market_data_df;")
    logger.info(f"Saved {len(all_market_data_df)} raw price records.")
    regime_cols = ['Date', 'Ticker', 'Close', 'SMA', f'ADX_14', 'Regime']
    regime_to_save = regime_df.dropna(subset=regime_cols)[regime_cols].rename(columns={f'ADX_14': 'ADX'})
    conn.execute("INSERT OR IGNORE INTO market_regimes BY NAME SELECT * FROM regime_to_save;")
    logger.info(f"Saved {len(regime_to_save)} market regime records.")
    conn.execute("INSERT INTO rs_rankings BY NAME SELECT * FROM rankings_df ON CONFLICT(Ticker) DO UPDATE SET Last_Date = excluded.Last_Date, Last_Close = excluded.Last_Close, RS_Score = excluded.RS_Score, RS_Rank = excluded.RS_Rank;")
    logger.info(f"Saved/Updated {len(rankings_df)} RS ranking records.")

def run_pipeline():
    logger.info("--- Starting Foundry Data Pipeline ---")
    try:
        config, credentials = load_config(), load_credentials()
        logger.info("Downloading Fyers symbol master..."); symbol_master_df = get_symbol_master()
        tickers_to_resolve = config['tickers'] + [config['market_index']]
        
        logger.info(f"Resolving {len(tickers_to_resolve)} configured tickers...");
        # WHAT: The function now returns a dictionary (map).
        # WHY:  This gives us a reliable way to look up tickers.
        resolved_map = resolve_symbols(tickers_to_resolve, symbol_master_df)
        
        if not resolved_map: raise RuntimeError("Symbol resolution failed.")
        
        # WHAT: We get the list of tickers to fetch from the dictionary's values.
        # WHY:  This is the correct way to use our new map.
        tickers_to_fetch = list(resolved_map.values())
        all_market_data_df = fetch_all_data_concurrently(client_id=credentials['client_id'], access_token=credentials['access_token'], symbols=tickers_to_fetch, days=1095)
        
        if all_market_data_df.empty: raise RuntimeError("Data fetch returned no data.")
        
        logger.info("Calculating Intelligence Layers...");
        
        # WHAT: We look up the index ticker directly from our map using the original config key.
        # WHY:  This is the definitive fix for the crash. It's 100% reliable.
        resolved_index_name = resolved_map.get(config['market_index'])
        
        if not resolved_index_name: raise RuntimeError("Could not find the resolved Nifty 50 index ticker in the map.")
        
        index_df = all_market_data_df[all_market_data_df['Ticker'] == resolved_index_name].copy()
        regime_df = calculate_market_regime(index_df)
        
        stock_df = all_market_data_df[all_market_data_df['Ticker'] != resolved_index_name].copy()
        rankings_df = calculate_rs_ranking(stock_df)
        
        logger.info("Intelligence calculated.")
        logger.info("Connecting to database and saving all data...")
        db_path = Path(config['database']['market_data_path'])
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with duckdb.connect(database=str(db_path), read_only=False) as conn:
            setup_database(conn)
            save_data_to_db(conn, all_market_data_df, regime_df, rankings_df)
            
        logger.info("--- Foundry Data Pipeline Finished Successfully ---")
    except Exception as e:
        logger.critical("--- PIPELINE FAILED ---", exc_info=True)

if __name__ == "__main__":
    run_pipeline()