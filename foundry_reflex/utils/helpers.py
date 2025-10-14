# utils/helpers.py

import re
import uuid
import json
import streamlit as st 
from pathlib import Path

def validate_ticker_format(ticker):
    """Validates ticker format."""
    pattern = re.compile(r'^[A-Z_]+:[A-Z0-9_\-]+-[A-Z_]+$')
    return pattern.match(ticker) is not None

def generate_insight_summary(selected_row):
    """Generates a list of plain-English insights based on backtest metrics."""
    insights = []
    row = selected_row.to_dict()

    if row.get('sortino_ratio', 0) > 2.0:
        insights.append("✅ **Strength:** Excellent performance when accounting for downside risk (high Sortino Ratio).")
    elif row.get('sharpe_ratio', 0) > 1.5:
        insights.append("✅ **Strength:** Great risk-adjusted return (high Sharpe Ratio).")
    if row.get('calmar_ratio', 0) > 1.0:
        insights.append("✅ **Strength:** Very good return relative to the maximum drawdown (high Calmar Ratio).")
    if row.get('win_rate_pct', 0) > 60:
        insights.append("✅ **Strength:** High win rate indicates consistent profitability on trades.")
    if row.get('max_drawdown_pct', 0) < -35:
        insights.append(f"⚠️ **Warning:** The maximum drawdown of {row['max_drawdown_pct']:.2f}% is very high, indicating significant risk.")
    if row.get('total_trades', 0) < 30:
        insights.append(f"💡 **Observation:** The sample size of {row['total_trades']} trades is small; results may not be statistically significant.")
    if not insights:
        insights.append("This strategy shows average or inconclusive performance based on the available metrics.")
    return insights

def upgrade_preset_for_builder(strategy_data):
    """Ensures a loaded preset has the modern nested 'rules' structure."""
    if 'rules' not in strategy_data or not isinstance(strategy_data.get('rules'), dict):
        strategy_data['rules'] = {
            "entry": [{"id": str(uuid.uuid4()), "type": "group", "logical_op": "AND", "conditions": []}],
            "exit": []
        }
    return strategy_data

STATE_FILE = Path("session_state_backup.json")

# Define which keys from st.session_state you want to save
PERSISTENT_KEYS = ["selected_universe", "filters_enabled", "rl_min_sharpe", "rl_min_sortino", "rl_min_calmar", "rl_max_dd", "rl_min_trades", "rl_min_win_rate"]

def save_persisted_state():
    """Saves the specified keys from the session state to a JSON file."""
    state_to_save = {key: st.session_state.get(key) for key in PERSISTENT_KEYS if key in st.session_state}
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state_to_save, f, indent=4)
    except Exception as e:
        print(f"Error saving state: {e}")


def load_persisted_state():
    """Loads state from the JSON file and populates the session state."""
    if not STATE_FILE.exists():
        return
    try:
        with open(STATE_FILE, "r") as f:
            persisted_state = json.load(f)
        
        for key, value in persisted_state.items():
            # Only load if the key isn't already set (e.g., by another widget)
            if key not in st.session_state:
                st.session_state[key] = value
    except (json.JSONDecodeError, TypeError) as e:
        print(f"Error loading state file: {e}")
        # If the file is corrupt, delete it for the next run
        STATE_FILE.unlink()