# In: foundry_reflex/components/home_ui.py

import reflex as rx
from foundry_reflex.state.data_management_state import DataManagementState

def home_dashboard() -> rx.Component:
    """The main dashboard UI for the application."""
    return rx.container(
        # The positional argument (the main UI component) now comes FIRST.
        rx.vstack(
            rx.heading("Foundry Migration Status", size="8"),
            rx.text("This page tests the migrated data utility functions by loading data into the Reflex state."),
            rx.divider(),
            
            rx.cond(
                DataManagementState.is_data_loaded,
                rx.vstack(
                    rx.heading("✅ Project Data Loaded Successfully", size="6", color_scheme="green"),
                    
                    rx.card(
                        rx.vstack(
                            rx.text("Performance Library Summary", weight="bold"),
        
                                # --- NEW: Added a tooltip to this text component ---
                            rx.tooltip(
                                rx.text(f"Total Backtests: {DataManagementState.performance_library_summary.get('Total Backtests', 'N/A')}"),
                                content=DataManagementState.total_trades_definition,
                            ),
                            # --- END OF NEW CODE ---

        rx.text(f"Unique Strategies: {DataManagementState.performance_library_summary.get('Unique Strategies', 'N/A')}"),
        rx.text(f"Unique Stocks: {DataManagementState.performance_library_summary.get('Unique Stocks', 'N/A')}"),
        spacing="1"
    ),
    width="100%"
),
                    
                    rx.card(
                        rx.vstack(
                            rx.text("Strategy Presets Found", weight="bold"),
                            rx.foreach(
                                DataManagementState.strategy_presets,
                                lambda preset: rx.badge(preset, color_scheme="blue")
                            ),
                            spacing="1"
                        ),
                        width="100%"
                    ),

                    rx.card(
                        rx.vstack(
                            rx.text("Stock Universes Found", weight="bold"),
                             rx.foreach(
                                DataManagementState.stock_universes.keys(),
                                lambda universe: rx.badge(universe, color_scheme="purple")
                            ),
                            spacing="1"
                        ),
                        width="100%"
                    ),
                    spacing="4",
                    width="100%"
                ),
                
                rx.vstack(
                    rx.spinner(size="3"),
                    rx.text("Loading project data from disk...")
                )
            ),
            spacing="5",
            width="100%"
        ),
        
        # ALL keyword arguments now come AFTER the positional argument.
        on_mount=DataManagementState.load_project_data,
        padding_top="2em",
        max_width="800px"
    )