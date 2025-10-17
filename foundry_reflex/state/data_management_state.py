import reflex as rx
from pathlib import Path
import yaml
from .trading_state import TradingState  # Inherits from our base state
from ..utils import data_io  # Imports the migrated utility functions

class DataManagementState(TradingState):
    """
    Manages loading and holding all project configuration data like
    universes, strategies, and performance library summaries.
    """
    # --- State Variables to hold loaded data ---
    stock_universes: dict = {}
    strategy_presets: list[str] = []
    performance_library_summary: dict = {}
    glossary_data: dict = {} 
    is_data_loaded: bool = False

    # --- Private variable to cache the loaded config file ---
    _config: dict = {}

    @rx.var
    def config(self) -> dict:
        """
        Loads the main config.yaml file once and caches it.
        This is a robust way to access configuration from anywhere in the state.
        """
        if not self._config:
            try:
                config_path = Path(__file__).resolve().parent.parent.parent / "config.yaml"
                with open(config_path, 'r') as f:
                    self._config = yaml.safe_load(f)
            except FileNotFoundError:
                print("ERROR: config.yaml not found in the project root!")
                return {}
        return self._config

    # --- NEWLY ADDED COMPUTED VAR ---
    @rx.var
    def stock_universe_names(self) -> list[str]:
        """Safely returns the names (keys) of the stock universes for the UI."""
        return list(self.stock_universes.keys())
    # --- END OF NEW CODE ---

    @rx.var
    def total_backtests_str(self) -> str:
        """Safely gets the total backtests as a string for display."""
        return str(self.performance_library_summary.get("Total Backtests", "N/A"))

    @rx.var
    def unique_strategies_str(self) -> str:
        """Safely gets the unique strategies as a string for display."""
        return str(self.performance_library_summary.get("Unique Strategies", "N/A"))

    @rx.var
    def unique_stocks_str(self) -> str:
        """Safely gets the unique stocks as a string for display."""
        return str(self.performance_library_summary.get("Unique Stocks", "N/A"))
        
    @rx.var
    def total_trades_definition(self) -> str:
        """
        Safely gets the definition for 'total_trades' from the glossary data.
        """
        if not self.glossary_data:
            return "Glossary not loaded."
        return self.glossary_data.get("total_trades", {}).get("definition", "Definition not found.")

    def load_project_data(self):
        """
        An event handler that loads all necessary data from disk.
        """
        if self.is_data_loaded:
            return

        print("\n--- LOADING PROJECT DATA ---")
        paths = self.config.get("paths", {})
        project_root = Path(__file__).resolve().parent.parent.parent

        universes_path = project_root / paths.get("stock_universes", "")
        self.stock_universes = data_io.load_universes(universes_path)
        
        presets_path_str = str(project_root / paths.get("strategy_presets", ""))
        self.strategy_presets = data_io.get_strategy_presets(presets_path_str)
        
        perf_lib_path = project_root / paths.get("performance_library", "")
        if perf_lib_path.exists():
            df = data_io.load_performance_library(perf_lib_path)
            self.performance_library_summary = {
                "Total Backtests": len(df),
                "Unique Strategies": df['strategy_name'].nunique(),
                "Unique Stocks": df['symbol'].nunique()
            }
        else:
            self.performance_library_summary = {"Status": "Not Found"}
            print(f"Warning: Performance library not found at {perf_lib_path}")

        glossary_path = project_root / "glossary.yaml"
        self.glossary_data = data_io.load_glossary(glossary_path)
        
        self.is_data_loaded = True
        print("--- DATA LOADING COMPLETE ---\n")

