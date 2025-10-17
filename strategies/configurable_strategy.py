# In: strategies/configurable_strategy.py

import logging
import re
from backtesting import Strategy
from backtesting.lib import crossover
import pandas as pd

# You can expand this dictionary with more indicators as you create them.
# The key is the string name, the value is the function to call.
# This makes the interpreter easily extensible.
AVAILABLE_INDICATORS = {}

def register_indicator(name):
    """A decorator to register new indicator functions."""
    def decorator(f):
        AVAILABLE_INDICATORS[name.upper()] = f
        return f
    return decorator

# --- Define and Register Your Indicator Functions Here ---
@register_indicator("SMA")
def SMA(series, n):
    return pd.Series(series).rolling(n).mean()

@register_indicator("RSI")
def RSI(series, n):
    delta = pd.Series(series).diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=n).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=n).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# --- The Main Interpreter Class ---

class ConfigurableStrategy(Strategy):
    """
    A universal strategy interpreter that builds its logic from a 'rules' dictionary.
    This class is designed to execute strategies created in a UI and saved as JSON.
    """
    rules = {} # The backtesting engine will inject the rules from the JSON here

    def init(self):
        """
        Pre-calculates all necessary indicators based on the provided rules.
        This is the setup phase and includes extensive error handling.
        """
        self.indicators = {}
        if not self.rules or not isinstance(self.rules, dict):
            logging.error("Strategy rules are missing or not in the correct format. Stopping.")
            # In backtesting.py, returning from init stops the strategy.
            return

        # Find all unique indicator strings from both entry and exit rules
        all_indicator_strings = set()
        for rule_type in ['entry', 'exit']:
            groups = self.rules.get(rule_type, [])
            for group in groups:
                self._extract_indicators_from_group(group, all_indicator_strings)
        
        # Calculate each unique indicator once and store it
        for indicator_str in all_indicator_strings:
            self._calculate_indicator(indicator_str)

    def next(self):
        """
        On each candle, evaluates the entry and exit rules recursively.
        """
        # Check entry rules if we don't have a position
        if not self.position:
            entry_signal = all(self._evaluate_group(group) for group in self.rules.get('entry', []))
            if entry_signal:
                self.buy()

        # Check exit rules if we do have a position
        else:
            exit_signal = all(self._evaluate_group(group) for group in self.rules.get('exit', []))
            if exit_signal:
                self.position.close()

    # --- Helper methods for parsing and evaluation ---

    def _extract_indicators_from_group(self, group, indicator_set):
        """Recursively find all indicator strings in a rule group."""
        for item in group.get('conditions', []):
            if item.get('type') == 'condition':
                if not item['left'].lower().startswith('value:'):
                    indicator_set.add(item['left'])
                if not item['right'].lower().startswith('value:'):
                    indicator_set.add(item['right'])
            elif item.get('type') == 'group':
                self._extract_indicators_from_group(item, indicator_set)

    def _calculate_indicator(self, indicator_str):
        """Parses an indicator string (e.g., 'SMA(50)'), calculates it, and stores it."""
        # Regex to parse NAME(param1, param2, ...)
        match = re.match(r'(\w+)\((.*?)\)', indicator_str)
        if not match:
            logging.warning(f"Skipping invalid indicator format: '{indicator_str}'")
            return

        name, params_str = match.groups()
        name = name.upper()

        if name not in AVAILABLE_INDICATORS:
            logging.warning(f"Skipping unknown indicator: '{name}'")
            return

        try:
            # Convert comma-separated params to numbers (int or float)
            params = [float(p.strip()) if '.' in p else int(p.strip()) for p in params_str.split(',') if p.strip()]
        except ValueError:
            logging.error(f"Invalid parameter in '{indicator_str}'. Could not convert to number. Skipping.")
            return
            
        indicator_func = AVAILABLE_INDICATORS[name]
        try:
            # Use self.I() to calculate and align the indicator with the data
            self.indicators[indicator_str] = self.I(indicator_func, self.data.Close, *params)
        except Exception as e:
            logging.error(f"Error calculating indicator '{indicator_str}': {e}")


    def _evaluate_group(self, group):
        """Recursively evaluates a rule group, returning True or False."""
        results = []
        for item in group.get('conditions', []):
            if item.get('type') == 'condition':
                results.append(self._evaluate_condition(item))
            elif item.get('type') == 'group':
                results.append(self._evaluate_group(item))
        
        if not results:
            return True # An empty group is considered true

        op = group.get('logical_op', 'AND').upper()
        if op == 'AND':
            return all(results)
        elif op == 'OR':
            return any(results)
        return False

    def _evaluate_condition(self, cond):
        """Evaluates a single condition (e.g., SMA(50) > SMA(200)), returning True or False."""
        op = cond.get('operator')
        
        # Get the current value for the left and right operands
        left_val = self._get_operand_value(cond['left'])
        right_val = self._get_operand_value(cond['right'])

        # If any operand failed to be resolved, the condition is false
        if left_val is None or right_val is None:
            return False

        # --- Operator Logic: Easily extensible ---
        if op == 'Crosses Above':
            # Crossover requires the series, not just the current value
            left_series = self._get_operand_value(cond['left'], series=True)
            right_series = self._get_operand_value(cond['right'], series=True)
            if left_series is None or right_series is None: return False
            return crossover(left_series, right_series)
        
        if op == 'Is Greater Than':
            return left_val > right_val
        if op == 'Is Less Than':
            return left_val < right_val
        
        # Add other operators like 'Equals', 'Is Between', etc. here
        
        logging.warning(f"Unsupported operator: '{op}'")
        return False

    def _get_operand_value(self, operand_str, series=False):
        """Gets the current value (or full series) for an operand string."""
        operand_str_lower = operand_str.lower()
        if operand_str_lower.startswith('value:'):
            try:
                # Extract the number after 'value:'
                return float(operand_str.split(':')[1])
            except (ValueError, IndexError):
                logging.error(f"Invalid static value format: '{operand_str}'")
                return None
        else:
            indicator = self.indicators.get(operand_str)
            if indicator is None:
                logging.warning(f"Could not find pre-calculated indicator for '{operand_str}'")
                return None
            return indicator if series else indicator[-1]