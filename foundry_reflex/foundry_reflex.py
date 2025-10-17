import reflex as rx
from foundry_reflex.components.home_ui import home_dashboard
from foundry_reflex.components.research_hub_ui import research_hub_page

# --- A simple navbar component for navigation (Theme Switcher REMOVED) ---
def navbar() -> rx.Component:
    """A polished navbar with a static theme."""
    return rx.box(
        rx.hstack(
            rx.hstack(
                # The icon color is now hard-coded to "teal"
                rx.icon("layers", size=28, color_scheme="teal"),
                rx.heading("Foundry", size="7", weight="bold"),
                align_items="center",
                spacing="2",
            ),
            rx.hstack(
                rx.link("Dashboard", href="/", color_scheme="gray", high_contrast=True),
                rx.link("Research Hub", href="/research-hub", color_scheme="gray", high_contrast=True),
                # The rx.select for the theme switcher has been completely removed.
                spacing="5",
                align_items="center",
            ),
            justify_content="space-between",
            align_items="center",
            padding_x="2em",
            width="100%",
        ),
        position="sticky",
        top="0",
        z_index="100",
        width="100%",
        height="4.5em",
        background_color="white",
        border_bottom="1px solid var(--gray-4)",
        box_shadow="sm",
    )

# --- Define the main layout for all pages ---
@rx.page()
def index() -> rx.Component:
    """The main dashboard page."""
    return rx.vstack(navbar(), home_dashboard(), spacing="0", background_color="#F8F9FA")

@rx.page(route="/research-hub")
def research_hub() -> rx.Component:
    """The Research Hub page for running backtests."""
    return rx.vstack(navbar(), research_hub_page(), spacing="0", background_color="#F8F9FA")

# --- Create and configure the app (Theme is now hard-coded) ---
app = rx.App(
    theme=rx.theme(
        accent_color="teal", # The theme is now permanently set to "teal"
        radius="medium",
    ),
)