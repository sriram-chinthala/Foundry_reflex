import reflex as rx

def metric_card(title: str, value: rx.Var[str]) -> rx.Component:
    """A reusable card component with a bright color for the main value."""
    return rx.card(
        rx.vstack(
            rx.text(title, size="2", color_scheme="gray", weight="medium"),
            rx.heading(value, size="6", weight="bold", color_scheme="teal"),
            align_items="center",
            spacing="1",
        ),
        box_shadow="var(--shadow-2)",
        border="1px solid var(--gray-3)",
    )
