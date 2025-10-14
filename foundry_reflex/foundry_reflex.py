# In: foundry_reflex/foundry_reflex.py (Root Folder)

import reflex as rx
from foundry_reflex.components.home_ui import home_dashboard
from foundry_reflex.components.research_hub_ui import research_hub_page

# --- A simple navbar component for navigation ---
def navbar():
    return rx.box(
        rx.hstack(
            rx.heading("Foundry", size="7"),
            rx.hstack(
                rx.link("Dashboard", href="/"),
                rx.link("Research Hub", href="/research-hub"),
                spacing="5",
            ),
            justify_content="space-between",
            align_items="center",
            padding_x="2em",
        ),
        position="sticky",
        top="0",
        z_index="10",
        width="100%",
        height="4em",
        background_color="#f0f0f0",
        border_bottom="1px solid #e0e0e0"
    )

# --- Define the main layout for all pages ---
@rx.page()
def index() -> rx.Component:
    return rx.vstack(navbar(), home_dashboard())

@rx.page(route="/research-hub")
def research_hub() -> rx.Component:
    return rx.vstack(navbar(), research_hub_page())

# --- Create and configure the app ---
app = rx.App()