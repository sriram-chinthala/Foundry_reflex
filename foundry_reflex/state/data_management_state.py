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
                # This is the CORRECT path to the Root Folder
                # state -> foundry_reflex (App) -> foundry_reflex (Root)
                config_path = Path(__file__).resolve().parent.parent.parent / "config.yaml"
                with open(config_path, 'r') as f:
                    self._config = yaml.safe_load(f)
            except FileNotFoundError:
                print("ERROR: config.yaml not found in the project root!")
                return {}
        return self._config

    def load_project_data(self):
        """
        An event handler that loads all necessary data from disk and includes
        diagnostic print statements to isolate workflow issues.
        """
        # --- THIS IS THE ISOLATION TEST ---
        # We will print the values at each critical step.
        print("\n--- ISOLATING WORKFLOW ---")

        # Step 1: Check if the config file is being loaded correctly.
        print(f"1. self.config content: {self.config}")

        paths = self.config.get("paths", {})
        # Step 2: Check if the 'paths' dictionary was extracted correctly.
        print(f"2. 'paths' dictionary content: {paths}")
    
        project_root = Path(__file__).resolve().parent.parent.parent
        # Step 3: Check the calculated project root path.
        print(f"3. Calculated 'project_root': {project_root}")

        universes_path = project_root / paths.get("stock_universes", "")
        # Step 4: Check the final path being passed to the open() command.
        print(f"4. Final 'universes_path' to be opened: {universes_path}")
        print("--- END ISOLATION ---\n")
        # --- END OF TEST ---

        if self.is_data_loaded:
            return

        # The rest of the function continues as before...
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
        glossary_path = project_root / "glossary.yaml"
        self.glossary_data = data_io.load_glossary(glossary_path)
        self.is_data_loaded = True
        
    @rx.var
    def total_trades_definition(self) -> str:
        """
        Safely gets the definition for 'total_trades' from the glossary data.
        This does the complex logic on the backend so the UI doesn't have to.
        """
        if not self.glossary_data:
            return "Glossary not loaded."
        
        # This is safe Python dictionary access
        return self.glossary_data.get("total_trades", {}).get("definition", "Definition not found.")
