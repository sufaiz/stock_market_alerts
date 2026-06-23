"""Technical indicators module for stock market analysis."""

import pandas as pd


def calculate_sma(df: pd.DataFrame, window: int = 20) -> pd.Series:
    """Calculate the Simple Moving Average (SMA) on the Close price.

    The SMA is a widely used technical indicator that smooths out price
    data by computing the arithmetic mean of the closing price over a
    specified number of periods. It helps identify the direction of a
    trend by filtering out short-term fluctuations.

    Args:
        df: A DataFrame containing at least a 'Close' column with
            historical price data.
        window: The number of periods over which to calculate the
            moving average. A smaller window (e.g., 20) reacts faster
            to price changes, while a larger window (e.g., 50) produces
            a smoother line that better reflects the long-term trend.
            Defaults to 20.

    Returns:
        A Series containing the SMA values, with NaN for the first
        (window - 1) entries where insufficient data is available.
    """
    return df["Close"].rolling(window=window).mean()


def calculate_rsi(df: pd.DataFrame, window: int = 14) -> pd.Series:
    """Calculate the Relative Strength Index (RSI) on the Close price.

    The RSI is a momentum oscillator that measures the speed and magnitude
    of recent price changes on a scale of 0 to 100. It is computed as:

        delta = Close.diff()
        avg_gain = mean of positive deltas over `window` periods
        avg_loss = mean of negative deltas (absolute) over `window` periods
        RS = avg_gain / avg_loss
        RSI = 100 - (100 / (1 + RS))

    Interpretation of the 0-100 scale:
        - RSI above 70 is generally considered **overbought**, suggesting
          the asset may be due for a pullback or reversal.
        - RSI below 30 is generally considered **oversold**, suggesting
          the asset may be undervalued and due for a bounce.
        - RSI around 50 indicates neutral momentum.

    Leading NaN values produced by the rolling window are filled with 50
    (neutral) so the series length matches the input DataFrame.

    Args:
        df: A DataFrame containing at least a 'Close' column with
            historical price data.
        window: The look-back period for the rolling average of gains
            and losses. Defaults to 14.

    Returns:
        A Series containing RSI values in the range [0, 100].
    """
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.fillna(50)
    return rsi


if __name__ == "__main__":
    from app.data_handler import get_stock_data

    symbol = "AAPL"
    df = get_stock_data(symbol)

    df["SMA_20"] = calculate_sma(df, window=20)
    df["SMA_50"] = calculate_sma(df, window=50)
    df["RSI"] = calculate_rsi(df)

    print(f"--- {symbol}: Last 10 rows (Close, SMA_20, SMA_50, RSI) ---")
    print(df[["Close", "SMA_20", "SMA_50", "RSI"]].tail(10))
