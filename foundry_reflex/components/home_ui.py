import reflex as rx
from foundry_reflex.state.data_management_state import DataManagementState

def home_dashboard() -> rx.Component:
    """The main dashboard UI for the application."""
    return rx.container(
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
                            
                            # Use the new, safe computed vars from the state
                            rx.tooltip(
                                rx.text(f"Total Backtests: {DataManagementState.total_backtests_str}"),
                                content=DataManagementState.total_trades_definition,
                            ),
                            rx.text(f"Unique Strategies: {DataManagementState.unique_strategies_str}"),
                            rx.text(f"Unique Stocks: {DataManagementState.unique_stocks_str}"),
                            
                            spacing="1"
                        ),
                        width="100%"
                    ),
                    
                    rx.card(
                        rx.vstack(
                            rx.text("Strategy Presets Found", weight="bold"),
                            # This foreach is safe because strategy_presets is already a list
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
                             # Use the new computed var that safely gets the keys as a list
                             rx.foreach(
                                DataManagementState.stock_universe_names,
                                lambda universe: rx.badge(universe, color_scheme="purple")
                            ),
                            spacing="1"
                        ),
                        width="100%"
                    ),
                    spacing="4",
                    width="100%"
                ),
                
                # This is the "else" part of rx.cond, shown while data is loading
                rx.vstack(
                    rx.spinner(size="3"),
                    rx.text("Loading project data from disk...")
                )
            ),
            spacing="5",
            width="100%"
        ),
        
        on_mount=DataManagementState.load_project_data,
        padding_top="2em",
        max_width="800px"
    )
