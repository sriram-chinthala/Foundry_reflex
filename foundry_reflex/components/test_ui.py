import reflex as rx
from foundry_reflex.state.test_state import TestState

def isolation_test_page() -> rx.Component:
    """A minimal UI page to display the message from our test state."""
    return rx.container(
        rx.vstack(
            rx.heading("Core State Isolation Test"),
            rx.text(
                "The following message comes directly from a default value in a Python state class:"
            ),
            rx.card(
                # This will attempt to display the default message.
                rx.text(TestState.message)
            ),
            padding="2em",
        )
    )
