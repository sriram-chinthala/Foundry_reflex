# In: foundry_reflex/state/trading_state.py

import reflex as rx
import toml
from pathlib import Path

class TradingState(rx.State):
    """
    The base state for the entire application, handling API credentials
    and core portfolio information.
    """
    # --- Private variable to hold secrets ---
    # This ensures secrets are loaded only once.
    _secrets: dict = {}

    # --- Core Portfolio Data (Placeholders) ---
    portfolio_value: float = 100000.00
    cash_on_hand: float = 100000.00
    positions: list[dict] = []

    # --- Computed Variables for Secure Credential Access ---
    # In: foundry_reflex/state/trading_state.py

    @rx.var
    def secrets(self) -> dict:
        """
        Loads the secrets.toml file securely from the project root.
        """
        if not self._secrets:
            try:
                # This is the CORRECT path to the Root Folder
                # state -> foundry_reflex (App) -> foundry_reflex (Root)
                secrets_path = Path(__file__).resolve().parent.parent.parent / "secrets.toml"
                self._secrets = toml.load(secrets_path)
            except FileNotFoundError:
                print("ERROR: secrets.toml not found in the root folder!")
                return {}
        return self._secrets

    @rx.var
    def fyers_client_id(self) -> str:
        """Provides the Fyers Client ID from the loaded secrets."""
        return self.secrets.get("fyers", {}).get("client_id", "NOT_FOUND")

    @rx.var
    def fyers_access_token(self) -> str:
        """Provides the Fyers Access Token from the loaded secrets."""
        return self.secrets.get("fyers", {}).get("access_token", "NOT_FOUND")