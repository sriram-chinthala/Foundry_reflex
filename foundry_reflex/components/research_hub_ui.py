# In: foundry_reflex/foundry_reflex/components/research_hub_ui.py

import reflex as rx
from foundry_reflex.state.engine_state import EngineState

def research_hub_page() -> rx.Component:
    """The UI for the Research Hub, including the Performance Engine control panel."""
    return rx.container(
        rx.vstack(
            rx.heading("Research Hub", size="8"),
            rx.text("Control panel for managing and running backtesting jobs."),
            rx.divider(),
            
            rx.card(
                rx.vstack(
                    rx.heading("Performance Engine", size="6"),
                    rx.hstack(
                        rx.select(
                            EngineState.stock_universes.keys(),
                            placeholder="Select a Universe...",
                            on_change=EngineState.set_selected_universe,
                            size="3",
                        ),
                        rx.select(
                            EngineState.strategy_presets,
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
                        spacing="4",
                        width="100%",
                    ),
                    rx.button(
                        "🚀 Launch Engine",
                        on_click=EngineState.run_performance_engine,
                        is_loading=EngineState.is_engine_running,
                        loading_text="Engine is running...",
                        width="100%",
                        size="3",
                        margin_top="1em"
                    ),
                    # Last Run Summary Card
                    rx.cond(
                        EngineState.last_run_summary,
                        rx.box(
                            rx.hstack(
                                # --- THIS IS THE CORRECTED SECTION ---
                                # Each "stat" is now a vstack of a text and a heading.
                                rx.vstack(
                                    rx.text("Status", size="2", color_scheme="gray", weight="medium"),
                                    rx.heading(EngineState.last_run_summary.get("status", "N/A"), size="5"),
                                    spacing="1",
                                    align_items="center",
                                ),
                                rx.vstack(
                                    rx.text("Stocks Processed", size="2", color_scheme="gray", weight="medium"),
                                    rx.heading(EngineState.last_run_summary.get("stocks", "N/A").to_string(), size="5"),
                                    spacing="1",
                                    align_items="center",
                                ),
                                rx.vstack(
                                    rx.text("Strategies Tested", size="2", color_scheme="gray", weight="medium"),
                                    rx.heading(EngineState.last_run_summary.get("strategies", "N/A").to_string(), size="5"),
                                    spacing="1",
                                    align_items="center",
                                ),
                                # --- END OF CORRECTION ---
                                spacing="6",
                                justify_content="space-around", # Helps space them out evenly
                                width="100%",
                            ),
                            margin_top="1em",
                            padding="1em",
                            border="1px solid #e0e0e0",
                            border_radius="8px",
                            width="100%",
                        )
                    ),
                    spacing="4"
                )
            ),
            
            rx.card(
                rx.vstack(
                    rx.heading("Live Engine Log", size="5"),
                    rx.code_block(
                        EngineState.engine_log,
                        language="log",
                        width="100%",
                        height="300px",
                        overflow_y="auto",
                    ),
                    align_items="flex-start",
                    width="100%",
                )
            ),
            spacing="5",
            width="100%"
        ),
        padding_top="2em",
        max_width="1200px"
    )