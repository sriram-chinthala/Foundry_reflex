# utils/performance_library_engine.py

import logging
import multiprocessing
import os
import time
from pathlib import Path

import duckdb
import pandas as pd
import yaml
from backtesting import Backtest
from tqdm import tqdm
from utils.logger_setup import get_logger
logger = get_logger("engine", "logs/engine.log")

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# --- Helper Functions & Imports ---

# This allows us to dynamically import the strategy class from a file
from importlib import import_module

# Configure logging for clear, structured output
# This will log to both a file and the console
log_file_path = Path("logs/engine.log")
log_file_path.parent.mkdir(exist_ok=True)


# Load configuration
try:
    # --- CHANGE #1: Use the absolute path to load config.yaml ---
    config_path = project_root / "config.yaml"
    with open(config_path, "r") as f:
        CONFIG = yaml.safe_load(f)
    PATHS = CONFIG.get("paths", {})
except FileNotFoundError:
    logging.error(f"Configuration file 'config.yaml' not found at {config_path}. Please ensure it exists.")
    sys.exit(1) # Use sys.exit to stop execution if config is missing


def load_strategy_class(strategy_file, strategy_class_name):
    """Dynamically loads a strategy class from a given file."""
    try:
        module_path = f"strategies.{strategy_file}"
        strategy_module = import_module(module_path)
        return getattr(strategy_module, strategy_class_name)
    except (ImportError, AttributeError) as e:
        logging.error(f"Could not load strategy '{strategy_class_name}' from '{strategy_file}.py'. Error: {e}")
        return None

# --- Core Backtesting Function (for parallel execution) ---

def _execute_single_backtest(args):
    """
    Executes a single backtest job. Designed to be run in a separate process.
    Includes robust error isolation.
    """
    symbol, strategy_preset = args
    db_path = PATHS.get("market_data_db")
    
    try:
        # 1. Load Data for the specific symbol
        con = duckdb.connect(database=db_path, read_only=True)
        # Important: Ensure data is sorted by date for backtesting.py
        data = con.execute(f"SELECT * FROM market_data WHERE Ticker = '{symbol}' ORDER BY date").fetchdf()
        con.close()

        if data.empty:
            logging.warning(f"SKIPPING: No market data found for symbol '{symbol}'.")
            return None

        # Rename columns to what backtesting.py expects
        data = data.rename(columns={
            'date': 'Date',
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        })
        data.set_index('Date', inplace=True)

        # 2. Load and Prepare Strategy
        strategy_class = load_strategy_class(strategy_preset["strategy_file"], strategy_preset["strategy_class"])
        if strategy_class is None:
            return None # Error already logged

        # 3. Run the Backtest
        bt = Backtest(data, strategy_class, cash=100_000, commission=.002, finalize_trades=True)
        stats = bt.run(**strategy_preset.get("parameters", {}))

        # 4. Extract Key Performance Indicators (KPIs) - FINAL, TRULY ROBUST METHOD
        # Use the .get() method to provide a default value (0 or NaN) if a key
        # does not exist. This is crucial for stats that are only calculated
        # when trades occur, like SQN.
        stats_series = stats # The result is a Pandas Series
        kpis = {
            'symbol': symbol,
            'strategy_name': strategy_preset["strategy_name"],
            
            # Core Performance Metrics
            'start_date': stats_series.get('Start'),
            'end_date': stats_series.get('End'),
            'duration_days': (stats_series.get('End') - stats_series.get('Start')).days if 'Start' in stats_series and 'End' in stats_series else 0,
            'return_pct': stats_series.get('Return [%]', 0.0),
            'buy_hold_return_pct': stats_series.get('Buy & Hold Return [%]', 0.0),
            'equity_final': stats_series.get('Equity Final [$]', 0.0),
            'max_drawdown_pct': stats_series.get('Max. Drawdown [%]', 0.0),

            # Risk-Adjusted Ratios
            'sharpe_ratio': stats_series.get('Sharpe Ratio', 0.0),
            'sortino_ratio': stats_series.get('Sortino Ratio', 0.0),
            'calmar_ratio': stats_series.get('Calmar Ratio', 0.0),
            
            # Trade-Specific Metrics
            'total_trades': stats_series.get('# Trades', 0),
            'win_rate_pct': stats_series.get('Win Rate [%]', 0.0),
            'profit_factor': stats_series.get('Profit Factor', 0.0),
            'expectancy_pct': stats_series.get('Expectancy [%]', 0.0),
            'avg_trade_pct': stats_series.get('Avg. Trade [%]', 0.0),
            'sqn': stats_series.get('System Quality Number', 0.0), # CRITICAL FIX HERE
        }
        return kpis

    except Exception as e:
        # This is the critical Error Isolation block
        logging.error(f"FAIL: Backtest for '{symbol}' with '{strategy_preset['strategy_name']}' failed. Reason: {e}", exc_info=False)
        return None

# --- Main Performance Engine Class ---

class PerformanceEngine:
    """
    Manages the creation and updating of the performance library.
    """
    def __init__(self, stock_universe, strategy_presets_files):
        self.stock_universe = stock_universe
        self.strategy_presets = self._load_strategy_presets(strategy_presets_files)
        self.library_path = Path(PATHS.get("performance_library"))

    def _load_strategy_presets(self, preset_files):
        """Loads strategy configurations from JSON files."""
        presets = {}
        presets_dir = Path(PATHS.get("strategy_presets"))
        for file_name in preset_files:
            try:
                with open(presets_dir / f"{file_name}.json", 'r') as f:
                    preset_data = pd.read_json(f, typ='series').to_dict()
                    # Use filename as the key
                    presets[file_name] = preset_data
            except Exception as e:
                logging.error(f"Failed to load strategy preset '{file_name}.json'. Error: {e}")
        return presets

    def _get_job_list(self):
        """Generates all possible (symbol, strategy) job combinations."""
        return [(symbol, preset) for symbol in self.stock_universe for preset in self.strategy_presets.values()]

    def run(self, mode='update'):
        """
        Main entry point to run the engine.
        
        Args:
            mode (str): 'update' to run only missing jobs, 'full' to rebuild entire library.
        """
        logging.info(f"--- Performance Engine Started (Mode: {mode.upper()}) ---")
        
        all_jobs = self._get_job_list()
        jobs_to_run = []

        # 1. Intelligent Delta Update Logic
        existing_library = None
        if mode == 'update' and self.library_path.exists():
            logging.info(f"Loading existing library from: {self.library_path}")
            existing_library = pd.read_parquet(self.library_path)
            
            # Create a unique identifier for existing jobs
            existing_jobs_set = set(zip(existing_library['symbol'], existing_library['strategy_name']))
            
            # Determine which jobs are missing
            for symbol, preset in all_jobs:
                if (symbol, preset['strategy_name']) not in existing_jobs_set:
                    jobs_to_run.append((symbol, preset))
            
            if not jobs_to_run:
                logging.info("Performance library is already up-to-date. No new jobs to run.")
                return
        else:
            jobs_to_run = all_jobs
            if mode == 'full':
                logging.info("Full rebuild requested. All existing results will be replaced.")

        logging.info(f"Found {len(jobs_to_run)} new jobs to run out of {len(all_jobs)} total possible combinations.")

        # 2. Parallel Processing
        start_time = time.time()
        results = []
        # Use slightly less than all cores to keep system responsive
        cpu_count = max(1, multiprocessing.cpu_count() - 1) 
        
        with multiprocessing.Pool(processes=cpu_count) as pool:
            # Use tqdm for a live progress bar in the console/log
            results = list(tqdm(pool.imap(_execute_single_backtest, jobs_to_run), total=len(jobs_to_run), desc="Running Backtests"))

        # 3. Process and Save Results
        # Filter out failed jobs (which return None)
        successful_results = [res for res in results if res is not None]
        
        logging.info(f"Successfully completed {len(successful_results)} out of {len(jobs_to_run)} jobs.")

        if not successful_results:
            logging.warning("No new results were generated.")
            return

        new_results_df = pd.DataFrame(successful_results)

        # 4. Combine and Save
        if mode == 'update' and existing_library is not None:
            final_library_df = pd.concat([existing_library, new_results_df], ignore_index=True)
        else:
            final_library_df = new_results_df
        
        self.library_path.parent.mkdir(exist_ok=True)
        final_library_df.to_parquet(self.library_path)

        end_time = time.time()
        logging.info(f"Performance library saved to {self.library_path}")
        logging.info(f"--- Engine run finished in {end_time - start_time:.2f} seconds. ---")


if __name__ == '__main__':
    """
    This block allows the engine to be run from the command line,
    accepting arguments for stock universe, strategies, and run mode.
    This is how the Streamlit UI will trigger the engine.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Foundry Performance Library Engine")
    parser.add_argument(
        '--stocks',
        nargs='+',  # This means it accepts one or more stock symbols
        required=True,
        help="List of stock symbols to run backtests on (e.g., NSE:RELIANCE-EQ NSE:TCS-EQ)"
    )
    parser.add_argument(
        '--strategies',
        nargs='+',
        required=True,
        help="List of strategy preset filenames (without .json extension)"
    )
    parser.add_argument(
        '--mode',
        choices=['update', 'full'],
        default='update',
        help="Run mode: 'update' (default) or 'full' for a complete rebuild."
    )
    
    args = parser.parse_args()

    logger.info("--- Running Performance Engine via Command Line ---")
    
    # INITIALIZE AND RUN THE ENGINE with arguments from the command line
    engine = PerformanceEngine(
        stock_universe=args.stocks,
        strategy_presets_files=args.strategies
    )
    
    engine.run(mode=args.mode)