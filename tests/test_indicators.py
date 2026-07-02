"""Unit tests for the technical indicators module."""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

from app.indicators import calculate_sma, calculate_rsi


def test_sma_basic() -> None:
    """SMA with window=3 on 5 rows: last value should be 40.0, first two NaN."""
    df = pd.DataFrame({"Close": [10, 20, 30, 40, 50]})
    result = calculate_sma(df, window=3)

    assert result.iloc[-1] == 40.0
    assert pd.isna(result.iloc[0])
    assert pd.isna(result.iloc[1])


def test_sma_window_larger_than_data() -> None:
    """When window exceeds row count every value should be NaN."""
    df = pd.DataFrame({"Close": [10, 20, 30]})
    result = calculate_sma(df, window=5)

    assert result.isna().all()


def test_rsi_neutral_fill() -> None:
    """RSI should have no NaN values (filled with 50) and stay in 0-100."""
    df = pd.DataFrame(
        {"Close": [100, 102, 101, 105, 107, 108, 106, 110, 112, 115]}
    )
    result = calculate_rsi(df, window=5)

    assert not result.isna().any()
    assert (result >= 0).all() and (result <= 100).all()


def test_rsi_rising_market() -> None:
    """In a consistently rising market the RSI should be above 70."""
    prices = list(range(100, 130, 2))  # [100, 102, ..., 128]
    df = pd.DataFrame({"Close": prices})
    result = calculate_rsi(df, window=14)

    assert result.iloc[-1] > 70


def test_sma_correct_calculation() -> None:
    """Verify exact SMA values at specific positions."""
    df = pd.DataFrame({"Close": [10, 20, 30, 40, 50, 60, 70]})
    result = calculate_sma(df, window=3)

    assert result.iloc[2] == 20.0
    assert result.iloc[-1] == 60.0
