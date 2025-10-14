# In: foundry_reflex/foundry_reflex/utils/symbol_resolver.py

import pandas as pd
from utils.logger_setup import get_logger


logger = get_logger("symbol_resolver", "logs/pipeline.log")
FYERS_SYMBOLS_URL = "https://public.fyers.in/sym_details/NSE_CM.csv"
def get_symbol_master():
    try:
        df = pd.read_csv(FYERS_SYMBOLS_URL, header=None, usecols=[1, 2, 9, 13], names=['Description', 'InstrumentType', 'FyersTicker', 'ShortName'])
        logger.info("Successfully downloaded and prepared the Fyers symbol master.")
        return df
    except Exception as e:
        logger.error(f"CRITICAL: Failed to download symbol master. Error: {e}")
        return pd.DataFrame()

def resolve_symbols(tickers_to_find: list, symbol_master: pd.DataFrame) -> dict: # Changed return type
    """
    Resolves a list of simple names to a dictionary mapping original_name -> fyers_ticker.
    """
    if symbol_master.empty: return {}
    # WHAT: We now create a dictionary to store our mappings.
    # WHY:  A dictionary is more explicit and prevents the "lost in translation" error.
    resolved_map = {} 
    symbol_master['CleanDescription'] = symbol_master['Description'].str.upper().str.strip()

    for ticker in tickers_to_find:
        ticker_upper = ticker.upper().strip()
        
        if "NIFTY" in ticker_upper or "INDIA VIX" in ticker_upper:
            index_match = symbol_master[symbol_master['CleanDescription'].str.contains(ticker_upper, na=False)]
            if not index_match.empty:
                best_match = index_match.loc[index_match['CleanDescription'].str.len().idxmin()]
                resolved = best_match['FyersTicker']
                logger.info(f"Resolved '{ticker}' -> '{resolved}' (Index ETF Match)")
                resolved_map[ticker] = resolved # Store as key-value pair
                continue
        
        exact_short_match = symbol_master[symbol_master['ShortName'] == ticker_upper]
        if not exact_short_match.empty:
            resolved = exact_short_match.iloc[0]['FyersTicker']
            logger.info(f"Resolved '{ticker}' -> '{resolved}' (Exact Short Name Match)")
            resolved_map[ticker] = resolved # Store as key-value pair
            continue
            
        logger.warning(f"Could not resolve symbol: '{ticker}'. It will be skipped.")
            
    return resolved_map # Return the entire dictionary