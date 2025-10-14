# In: foundry_reflex/foundry_reflex/state/engine_state.py

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

    @rx.var
    def universe_options(self) -> list[str]:
        """Get list of available universes."""
        return list(self.stock_universes.keys()) if self.stock_universes else []
    
    @rx.var
    def strategy_options(self) -> list[str]:
        """Get list of available strategies."""
        return self.strategy_presets if self.strategy_presets else []

    async def run_performance_engine(self):
        """
        Runs the performance library engine as a background task.
        """
        async with self:
            if self.is_engine_running:
                return

            self.is_engine_running = True
            self.last_run_summary = {}
            self.engine_log = "Starting Performance Engine...\n"

        try:
            # Get stocks from the selected universe
            stocks_to_run = self.stock_universes.get(self.selected_universe, [])

            if not stocks_to_run or not self.selected_strategy:
                async with self:
                    self.engine_log += "\nERROR: A universe and a strategy must be selected."
                    self.is_engine_running = False
                return

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
                line = await process.stdout.readline()
                if not line:
                    break
                async with self:
                    self.engine_log += line.decode('utf-8', errors='ignore')

            await process.wait()
            
            async with self:
                self.last_run_summary = {
                    "status": "✅ Success" if process.returncode == 0 else "❌ Failed",
                    "stocks": len(stocks_to_run),
                    "strategies": 1,
                    "return_code": process.returncode
                }
                
                # Reload data after successful run
                if process.returncode == 0:
                    self.load_project_data()

        except Exception as e:
            async with self:
                self.engine_log += f"\nFATAL ERROR: {e}"
                self.last_run_summary = {"status": "❌ Error", "error": str(e)}
        finally:
            async with self:
                self.engine_log += "\n--- Engine run complete. ---"
                self.is_engine_running = False