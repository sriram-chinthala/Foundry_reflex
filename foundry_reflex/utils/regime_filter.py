import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pandas_ta")
import pandas as pd
import pandas_ta as ta
import numpy as np

def calculate_market_regime(df: pd.DataFrame, sma_period: int = 50, adx_period: int = 14) -> pd.DataFrame:
    if df.empty or len(df) < sma_period: return df
    df['SMA'] = ta.sma(df['Close'], length=sma_period)
    adx_indicator = ta.adx(df['High'], df['Low'], df['Close'], length=adx_period)
    df = df.join(adx_indicator)
    conditions = [(df['Close'] > df['SMA']) & (df[f'ADX_{adx_period}'] > 20), (df['Close'] < df['SMA']) & (df[f'ADX_{adx_period}'] > 20)]
    outcomes = ['Uptrend', 'Downtrend']
    df['Regime'] = np.select(conditions, outcomes, default='Sideways')
    return df