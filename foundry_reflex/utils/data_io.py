# In: foundry_reflex/utils/data_io.py

import pandas as pd
from pathlib import Path
import yaml
import glob
import duckdb
import json
import os

def load_glossary(path=Path("glossary.yaml")):
    if path.exists():
        with open(path, 'r') as file:
            return yaml.safe_load(file)
    return {}

def load_universes(path):
    if not path.exists():
        return {}
    with open(path, 'r') as file:
        return yaml.safe_load(file)

def save_universes(path, universes):
    path.parent.mkdir(exist_ok=True)
    with open(path, 'w') as file:
        yaml.dump(universes, file, default_flow_style=False)

def load_performance_library(path):
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)

def get_all_known_tickers(db_path):
    if not Path(db_path).exists():
        return []
    try:
        con = duckdb.connect(database=db_path, read_only=True)
        tickers = con.execute("SELECT DISTINCT Ticker FROM market_data ORDER BY Ticker").fetchdf()
        con.close()
        return tickers['Ticker'].tolist()
    except Exception as e:
        print(f"Error loading tickers from DB: {e}")
        return []

def get_latest_prices(db_path):
    if not Path(db_path).exists():
        return pd.DataFrame()
    try:
        con = duckdb.connect(database=str(db_path), read_only=True)
        query = """
        SELECT Ticker AS symbol, Close AS latest_price
        FROM market_data
        QUALIFY ROW_NUMBER() OVER (PARTITION BY Ticker ORDER BY Date DESC) = 1
        """
        latest_prices_df = con.execute(query).fetchdf()
        con.close()
        return latest_prices_df
    except Exception as e:
        print(f"Error loading latest prices: {e}")
        return pd.DataFrame()

def get_strategy_presets(path):
    preset_files = glob.glob(f"{path}/*.json")
    return [Path(f).stem for f in preset_files]

def load_strategy_preset(path, preset_name):
    file_path = path / f"{preset_name}.json"
    if file_path.exists():
        with open(file_path, 'r') as f:
            return json.load(f)
    return None

def save_strategy_preset(path, strategy_data):
    path.mkdir(exist_ok=True)
    final_preset = {
        "strategy_name": strategy_data.get("strategy_name"),
        "strategy_file": strategy_data.get("strategy_file"),
        "strategy_class": strategy_data.get("strategy_class"),
        "parameters": {
            "rules": strategy_data.get("rules", {})
        }
    }
    file_name = final_preset["strategy_name"] or "untitled_strategy"
    file_path = path / f"{file_name}.json"
    with open(file_path, 'w') as f:
        json.dump(final_preset, f, indent=4)

def delete_strategy_preset(path, preset_name):
    file_path = path / f"{preset_name}.json"
    if file_path.exists():
        try:
            os.remove(file_path)
            return True
        except OSError as e:
            print(f"Error deleting preset file: {e}")
            return False
    return False