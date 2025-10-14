import pandas as pd
def calculate_rs_ranking(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return pd.DataFrame()
    latest_date = df['Date'].max()
    df_filtered = df[df['Date'] > (latest_date - pd.Timedelta(days=300))]
    close_prices = df_filtered.pivot(index='Date', columns='Ticker', values='Close')
    c_minus_21 = close_prices.pct_change(21); c_minus_63 = close_prices.pct_change(63)
    c_minus_126 = close_prices.pct_change(126); c_minus_252 = close_prices.pct_change(252)
    rs_score = (c_minus_21 * 0.4) + (c_minus_63 * 0.2) + (c_minus_126 * 0.2) + (c_minus_252 * 0.2)
    latest_rs = rs_score.iloc[-1]
    rs_rank = latest_rs.rank(pct=True) * 100
    results_df = pd.DataFrame({'Last_Date': latest_date, 'Last_Close': close_prices.iloc[-1], 'RS_Score': latest_rs, 'RS_Rank': rs_rank}).reset_index()
    return results_df.sort_values(by='RS_Rank', ascending=False)