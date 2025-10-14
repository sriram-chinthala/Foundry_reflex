import pandas as pd
import requests
from datetime import datetime, timedelta
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from .logger_setup import get_logger

logger = get_logger("fyers_dataprovider", "logs/pipeline.log")

class FyersRateLimiter:
    def __init__(self, sec_rate=9.0, sec_cap=10.0):
        self.bucket = {
            "rate": sec_rate, "capacity": sec_cap, "tokens": sec_cap,
            "lock": threading.Lock(), # The lock is the key to thread safety
            "last_refill": time.monotonic()
        }
    def _refill(self):
        now = time.monotonic()
        elapsed = now - self.bucket["last_refill"]
        if elapsed > 0:
            new_tokens = elapsed * self.bucket["rate"]
            self.bucket["tokens"] = min(self.bucket["capacity"], self.bucket["tokens"] + new_tokens)
            self.bucket["last_refill"] = now
    def wait_for_token(self):
        while True:
            # WHAT: The lock is acquired here. Only one thread can be inside this block at a time.
            # WHY: This makes the check-and-take operation atomic and solves the race condition.
            with self.bucket["lock"]:
                self._refill()
                if self.bucket["tokens"] >= 1:
                    self.bucket["tokens"] -= 1
                    return # A token was successfully consumed
            # If no token was available, the thread waits outside the lock
            time.sleep(0.05) 

FYERS_RATE_LIMITER = FyersRateLimiter()

def fetch_data_chunk(symbol, access_token, client_id, date_from, date_to):
    FYERS_RATE_LIMITER.wait_for_token()
    api_url = "https://api-t1.fyers.in/data/history"
    headers = {'Authorization': f'{client_id}:{access_token}'}
    params = {"symbol": symbol, "resolution": "D", "date_format": "1", "range_from": date_from.strftime('%Y-%m-%d'), "range_to": date_to.strftime('%Y-%m-%d'), "cont_flag": "1"}
    try:
        response = requests.get(url=api_url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        if data.get("s") == "ok" and data.get('candles'): return data['candles']
        logger.warning(f"API non-ok for {symbol} chunk. Msg: {data.get('message', 'N/A')}")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP chunk request failed for {symbol}: {e}"); return []
def get_historical_data_stitched(symbol, access_token, client_id, total_days=1095):
    all_candles = []; end_date = datetime.now(); chunk_size_days = 360
    for days_ago in range(0, total_days, chunk_size_days):
        range_to = end_date - timedelta(days=days_ago); range_from = range_to - timedelta(days=chunk_size_days)
        candles = fetch_data_chunk(symbol, access_token, client_id, range_from, range_to)
        if candles: all_candles.extend(candles)
    if not all_candles: return None
    df = pd.DataFrame(all_candles, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df.drop_duplicates(subset='Timestamp', inplace=True); df['Date'] = pd.to_datetime(df['Timestamp'], unit='s').dt.date
    df['Ticker'] = symbol; df.sort_values(by='Date', inplace=True)
    return df[['Date', 'Ticker', 'Open', 'High', 'Low', 'Close', 'Volume']]
def fetch_all_data_concurrently(client_id, access_token, symbols, days=1095, max_workers=5):
    all_data = []; logger.info(f"Fetching {days} days of data for {len(symbols)} symbols...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(get_historical_data_stitched, s, access_token, client_id, days): s for s in symbols}
        for i, future in enumerate(as_completed(futures)):
            result_df = future.result()
            if result_df is not None: all_data.append(result_df)
            print(f"  -> Progress: {(i + 1) / len(symbols):.0%}", end='\r')
    logger.info("Concurrent data fetch complete.")
    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()