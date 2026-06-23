"""Data handler module for fetching stock market data using yfinance."""

import pandas as pd
import yfinance as yf


def get_stock_data(
    ticker: str,
    period: str = None,
    interval: str = "1d",
    start: str = None,
    end: str = None,
) -> pd.DataFrame:
    """Fetch historical OHLCV data for a given stock ticker.

    Args:
        ticker: The stock ticker symbol (e.g., "AAPL").
        period: The time period to fetch data for (e.g., "6mo"). If start/end
            are provided, period should be None. Defaults to None.
        interval: The data interval. Defaults to "1d".
        start: Start date string (YYYY-MM-DD) or datetime. Defaults to None.
        end: End date string (YYYY-MM-DD) or datetime. Defaults to None.

    Returns:
        A DataFrame containing historical OHLCV data.
    """
    stock = yf.Ticker(ticker)
    if start or end:
        data = stock.history(start=start, end=end, interval=interval)
    else:
        # If no period and no start/end, default to "6mo"
        p = period if period is not None else "6mo"
        data = stock.history(period=p, interval=interval)
    return data



def get_stock_info(ticker: str) -> dict:
    """Fetch key stock information for a given ticker.

    Retrieves currentPrice, dayHigh, dayLow, volume, and trailingPE
    from the yfinance .info dictionary. Missing keys are handled
    gracefully and returned as None.

    Args:
        ticker: The stock ticker symbol (e.g., "AAPL").

    Returns:
        A dict with keys: currentPrice, dayHigh, dayLow, volume,
        trailingPE.
    """
    stock = yf.Ticker(ticker)
    info = stock.info
    keys = ["currentPrice", "dayHigh", "dayLow", "volume", "trailingPE"]
    return {key: info.get(key) for key in keys}


if __name__ == "__main__":
    symbol = "AAPL"

    print(f"--- Stock Data for {symbol} ---")
    df = get_stock_data(symbol)
    print(df)

    print(f"\n--- Stock Info for {symbol} ---")
    info = get_stock_info(symbol)
    for key, value in info.items():
        print(f"  {key}: {value}")
