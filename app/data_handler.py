"""Data handler module for fetching stock market data using yfinance."""

import pandas as pd
import yfinance as yf


def get_stock_data(
    ticker: str, period: str = "6mo", interval: str = "1d"
) -> pd.DataFrame:
    """Fetch historical OHLCV data for a given stock ticker.

    Args:
        ticker: The stock ticker symbol (e.g., "AAPL").
        period: The time period to fetch data for. Defaults to "6mo".
        interval: The data interval. Defaults to "1d".

    Returns:
        A DataFrame containing historical OHLCV data.
    """
    stock = yf.Ticker(ticker)
    data = stock.history(period=period, interval=interval)
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
