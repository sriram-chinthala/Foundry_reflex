import reflex as rx
from foundry_reflex.state.engine_state import EngineState
from .shared.metric_card import metric_card

def research_hub_page() -> rx.Component:
    """A modern, bright UI for the Research Hub."""
    return rx.box(
        rx.vstack(
            # --- HEADER ---
            rx.vstack(
                rx.heading("Research Hub", size="8", weight="bold", color_scheme="gray"),
                rx.text(
                    "Select a stock universe and strategy to run a new backtest.",
                    size="4",
                    color_scheme="gray",
                ),
                spacing="1",
                align_items="start",
                width="100%",
            ),
            
            # --- CONTROL PANEL ---
            rx.card(
                rx.vstack(
                    rx.grid(
                        rx.select(
                            EngineState.universe_options,
                            placeholder="Select a Universe...",
                            on_change=EngineState.set_selected_universe,
                            size="3",
                        ),
                        rx.select(
                            EngineState.strategy_options,
                            placeholder="Select a Strategy...",
                            on_change=EngineState.set_selected_strategy,
                            size="3",
                        ),
                        rx.select(
                            ["update", "full"],
                            default_value="update",
                            on_change=EngineState.set_selected_mode,
                            size="3",
                        ),
                        columns="3",
                        spacing="4",
                        width="100%",
                    ),
                    rx.button(
                        rx.icon(tag="rocket", margin_right="0.5em"),
                        "Launch Engine",
                        on_click=EngineState.start_engine_subprocess,
                        is_loading=EngineState.is_engine_running,
                        loading_text="Engine is running...",
                        width="100%",
                        size="3",
                        margin_top="1em",
                        color_scheme="teal", # The main button is now bright teal
                    ),
                    spacing="4",
                ),
                box_shadow="var(--shadow-4)",
                border="1px solid var(--gray-3)",
            ),

            # --- LAST RUN SUMMARY ---
            rx.cond(
                EngineState.last_run_summary,
                rx.vstack(
                    rx.divider(),
                    rx.heading("Last Run Summary", size="5", weight="medium", color_scheme="gray"),
                    rx.grid(
                        metric_card("Status", EngineState.summary_status),
                        metric_card("Stocks Processed", EngineState.summary_stocks_processed),
                        metric_card("Strategies Tested", EngineState.summary_strategies_tested),
                        columns="3",
                        spacing="4",
                        width="100%",
                    ),
                    spacing="4",
                    width="100%",
                )
            ),
            
            # --- LIVE LOG ---
            rx.card(
                rx.vstack(
                    rx.heading("Live Engine Log", size="5", weight="medium", color_scheme="gray"),
                    rx.code_block(
                        EngineState.engine_log,
                        language="log",
                        width="100%",
                        height="300px",
                        background="var(--gray-2)", # A light gray background for readability
                        border="1px solid var(--gray-4)",
                        border_radius="var(--radius-3)",
                    ),
                    align_items="flex-start",
                    width="100%",
                    spacing="4",
                ),
                box_shadow="var(--shadow-4)",
                border="1px solid var(--gray-3)",
            ),
            spacing="6",
            width="100%"
        ),
        on_mount=EngineState.load_project_data,
        padding="2em",
        max_width="1200px",
        margin="0 auto",
    )

