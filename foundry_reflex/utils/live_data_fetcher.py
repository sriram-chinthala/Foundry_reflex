# In: foundry_reflex/utils/live_data_fetcher.py

import pandas as pd
from fyers_apiv3 import fyersModel
from datetime import datetime, timedelta

def get_live_intraday_data(symbol: str, client_id: str, access_token: str, timeframe_resolution: str, days_back: int) -> pd.DataFrame:
    """ Fetches live intraday data from the Fyers API. """
    
    if not client_id or not access_token:
        print("Fyers API credentials not provided.")
        return pd.DataFrame()

    fyers = fyersModel.FyersModel(client_id=client_id, token=access_token, log_path="")
    
    date_to = datetime.now().strftime("%Y-%m-%d")
    date_from = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    
    data = {
        "symbol": symbol, "resolution": timeframe_resolution, "date_format": "1",
        "range_from": date_from, "range_to": date_to, "cont_flag": "1"
    }

    try:
        response = fyers.history(data=data)
        if response.get("s") == "ok" and response.get('candles'):
            df = pd.DataFrame(response['candles'], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            df.set_index('timestamp', inplace=True)
            df.index = df.index.tz_localize('UTC').tz_convert('Asia/Kolkata')
            return df
        else:
            print(f"Could not fetch intraday data for {symbol}. Response: {response.get('message', 'Unknown error')}")
            return pd.DataFrame()
    except Exception as e:
        print(f"API Error fetching intraday data for {symbol}: {e}")
        return pd.DataFrame()