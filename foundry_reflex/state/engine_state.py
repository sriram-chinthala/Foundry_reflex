import reflex as rx
import subprocess
import sys
import asyncio
from pathlib import Path
from .data_management_state import DataManagementState

class EngineState(DataManagementState):
    """Manages the state and execution of the performance engine."""

    # UI selections
    selected_universe: str = ""
    selected_strategy: str = ""
    selected_mode: str = "update"

    # Engine status
    is_engine_running: bool = False
    engine_log: str = "Engine has not been run yet."
    last_run_summary: dict = {}

    # --- COMPUTED VARS FOR SAFE UI DISPLAY ---
    # This is the correct pattern to avoid VarAttributeError.
    # The UI will use these safe, pre-processed variables.

    @rx.var
    def universe_options(self) -> list[str]:
        """Safely gets the list of universe names for the UI."""
        return list(self.stock_universes.keys()) if self.stock_universes else []

    @rx.var
    def strategy_options(self) -> list[str]:
        """Safely gets the list of strategy presets for the UI."""
        return self.strategy_presets if self.strategy_presets else []

    @rx.var
    def summary_status(self) -> str:
        """Safely gets the status from the last run summary."""
        return self.last_run_summary.get("status", "N/A")

    @rx.var
    def summary_stocks_processed(self) -> str:
        """Safely gets the stock count from the last run summary."""
        return str(self.last_run_summary.get("stocks", "N/A"))

    @rx.var
    def summary_strategies_tested(self) -> str:
        """Safely gets the strategy count from the last run summary."""
        return str(self.last_run_summary.get("strategies", "N/A"))
    
    # --- END OF COMPUTED VARS ---


    def start_engine_subprocess(self):
        """Event handler to prepare for and launch the engine background task."""
        if self.is_engine_running:
            return
        if not self.selected_universe or not self.selected_strategy:
            self.engine_log = "ERROR: Please select a universe and a strategy before launching."
            return

        self.is_engine_running = True
        self.last_run_summary = {}
        self.engine_log = f"Launching engine for universe '{self.selected_universe}' with strategy '{self.selected_strategy}'...\n"
        
        return EngineState.run_engine_background

    @rx.background
    async def run_engine_background(self):
        """Runs the performance library engine in a subprocess without blocking the UI."""
        try:
            stocks_to_run = self.stock_universes.get(self.selected_universe, [])
            project_root = Path(__file__).resolve().parent.parent.parent
            
            command = [
                sys.executable, "-m", "foundry_reflex.utils.performance_library_engine",
                "--stocks", *stocks_to_run,
                "--strategies", self.selected_strategy,
                "--mode", self.selected_mode,
            ]

            process = await asyncio.create_subprocess_exec(
                *command, 
                stdout=asyncio.subprocess.PIPE, 
                stderr=asyncio.subprocess.STDOUT,
                cwd=str(project_root)
            )

            while True:
                line_bytes = await process.stdout.readline()
                if not line_bytes:
                    break
                async with self:
                    self.engine_log += line_bytes.decode('utf-8', errors='ignore')

            await process.wait()
            
            async with self:
                self.last_run_summary = {
                    "status": "✅ Success" if process.returncode == 0 else "❌ Failed",
                    "stocks": len(stocks_to_run),
                    "strategies": 1,
                    "return_code": process.returncode
                }
                if process.returncode == 0:
                    # Reload data to update the main dashboard's summary
                    self.load_project_data()

        except Exception as e:
            async with self:
                self.engine_log += f"\nFATAL ERROR: {e}"
                self.last_run_summary = {"status": "❌ Error", "error": str(e)}
        finally:
            async with self:
                self.engine_log += "\n--- Engine run complete. ---"
                self.is_engine_running = False

