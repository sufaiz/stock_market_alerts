"""Streamlit entry point for the AI-Powered Stock Tracker."""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.alert_service import start_alert_loop
from app.data_handler import get_stock_data, get_stock_info
from app.indicators import calculate_sma, calculate_rsi
from app.sentiment_engine import analyze_sentiment
from database.db_manager import init_db, add_alert, get_alerts

# ── 1. PAGE CONFIG ─────────────────────────────────────────────────────────
st.set_page_config(page_title="AI Stock Tracker", layout="wide")

# ── 2. INITIALIZATION ─────────────────────────────────────────────────────
init_db()

if "alert_loop_started" not in st.session_state:
    start_alert_loop()
    st.session_state["alert_loop_started"] = True

# ── Header ─────────────────────────────────────────────────────────────────
st.title("📈 AI Stock Tracker")

# ── Sidebar: Asset Selection ───────────────────────────────────────────────
st.sidebar.header("Select Asset")

asset_class = st.sidebar.selectbox(
    "Asset Class",
    ["US Stocks", "Indian Stocks", "Commodities", "Forex Pairs", "Custom Ticker"],
)

ticker: str = "AAPL"  # Default fallback

if asset_class == "US Stocks":
    us_presets = {
        "Apple (AAPL)": "AAPL",
        "Microsoft (MSFT)": "MSFT",
        "Alphabet (GOOGL)": "GOOGL",
        "Amazon (AMZN)": "AMZN",
        "Tesla (TSLA)": "TSLA",
        "NVIDIA (NVDA)": "NVDA",
        "Meta (META)": "META",
    }
    selected_us = st.sidebar.selectbox("US Stocks", list(us_presets.keys()))
    ticker = us_presets[selected_us]

elif asset_class == "Indian Stocks":
    in_presets = {
        "Reliance Industries (RELIANCE.NS)": "RELIANCE.NS",
        "Tata Consultancy Services (TCS.NS)": "TCS.NS",
        "HDFC Bank (HDFCBANK.NS)": "HDFCBANK.NS",
        "Infosys (INFY.NS)": "INFY.NS",
        "ICICI Bank (ICICIBANK.NS)": "ICICIBANK.NS",
        "State Bank of India (SBIN.NS)": "SBIN.NS",
    }
    selected_in = st.sidebar.selectbox(
        "Indian Stocks (NSE)", list(in_presets.keys())
    )
    ticker = in_presets[selected_in]

elif asset_class == "Commodities":
    comm_presets = {
        "Gold (GC=F)": "GC=F",
        "Silver (SI=F)": "SI=F",
        "Crude Oil (CL=F)": "CL=F",
        "Natural Gas (NG=F)": "NG=F",
    }
    selected_comm = st.sidebar.selectbox(
        "Commodities", list(comm_presets.keys())
    )
    ticker = comm_presets[selected_comm]

elif asset_class == "Forex Pairs":
    forex_presets = {
        "EUR / USD": "EURUSD=X",
        "GBP / USD": "GBPUSD=X",
        "USD / JPY": "USDJPY=X",
        "USD / INR": "USDINR=X",
    }
    selected_forex = st.sidebar.selectbox(
        "Forex Pairs", list(forex_presets.keys())
    )
    ticker = forex_presets[selected_forex]

else:
    ticker = (
        st.sidebar.text_input("Enter Ticker Symbol", value="AAPL")
        .upper()
        .strip()
    )

# ── 3. TICKER SEARCH ──────────────────────────────────────────────────────
st.sidebar.markdown("---")
ticker = st.text_input(
    "🔍 Search Ticker", value=ticker, help="Enter any valid ticker symbol"
).upper().strip()

if not ticker:
    st.warning("Please enter a ticker symbol to get started.")
    st.stop()

# ── Sidebar: Chart Settings ───────────────────────────────────────────────
st.sidebar.header("Chart Settings")

timeframe_mode = st.sidebar.radio(
    "Timeframe Mode", ["Presets", "Custom Date Range"]
)

period: str | None = None
start_date: datetime.date | None = None
end_date: datetime.date | None = None
interval: str = "1d"
timeframe_label: str = "6 Months (Daily)"

if timeframe_mode == "Presets":
    timeframe_label = st.sidebar.selectbox(
        "Timeframe",
        options=[
            "1 Day (Real-time, 1m)",
            "5 Days (Intraday, 15m)",
            "1 Month (Daily)",
            "3 Months (Daily)",
            "6 Months (Daily)",
            "1 Year (Daily)",
            "5 Years (Weekly)",
            "Max (Monthly)",
        ],
        index=4,
    )

    timeframe_map: dict[str, tuple[str, str]] = {
        "1 Day (Real-time, 1m)": ("1d", "1m"),
        "5 Days (Intraday, 15m)": ("5d", "15m"),
        "1 Month (Daily)": ("1mo", "1d"),
        "3 Months (Daily)": ("3mo", "1d"),
        "6 Months (Daily)": ("6mo", "1d"),
        "1 Year (Daily)": ("1y", "1d"),
        "5 Years (Weekly)": ("5y", "1wk"),
        "Max (Monthly)": ("max", "1mo"),
    }
    period, interval = timeframe_map[timeframe_label]
else:
    today = datetime.date.today()
    one_year_ago = today - datetime.timedelta(days=365)

    start_date = st.sidebar.date_input("Start Date", value=one_year_ago)
    end_date = st.sidebar.date_input("End Date", value=today)

    interval = st.sidebar.selectbox(
        "Interval",
        options=["1m", "5m", "15m", "1h", "1d", "1wk", "1mo"],
        index=4,
    )
    timeframe_label = f"Custom ({interval})"

    if start_date > end_date:
        st.sidebar.error("Start Date must be before End Date.")

chart_type = st.sidebar.radio("Chart Type", ["Candlestick", "Line"])

# ── Sidebar: Indicator Toggles ─────────────────────────────────────────────
st.sidebar.header("Indicators")
show_sma_20: bool = st.sidebar.checkbox("Show SMA 20", value=True)
show_sma_50: bool = st.sidebar.checkbox("Show SMA 50", value=True)
show_rsi_gauge: bool = st.sidebar.checkbox("Show RSI Gauge", value=True)

if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# ── Fetch Data ─────────────────────────────────────────────────────────────
with st.spinner("Fetching stock data..."):
    try:
        if timeframe_mode == "Presets":
            df = get_stock_data(ticker, period=period, interval=interval)
        else:
            df = get_stock_data(
                ticker,
                interval=interval,
                start=start_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d"),
            )
    except Exception as e:
        st.error(f"Failed to fetch price data for **{ticker}**: {e}")
        st.stop()

    if df.empty:
        st.error(
            f"No data found for **{ticker}**. "
            "Please check the ticker symbol and try again."
        )
        st.stop()

# Calculate indicators
df["SMA_20"] = calculate_sma(df, window=20)
df["SMA_50"] = calculate_sma(df, window=50)
df["RSI"] = calculate_rsi(df)

# ── Fetch Info ─────────────────────────────────────────────────────────────
try:
    info = get_stock_info(ticker)
except Exception:
    info = {}

current_price = info.get("currentPrice")
day_high = info.get("dayHigh")
day_low = info.get("dayLow")
volume = info.get("volume")
pe_ratio = info.get("trailingPE")
stock_name = info.get("shortName")
stock_sector = info.get("sector")
stock_industry = info.get("industry")

# Fallback: use DataFrame close if live info unavailable
if current_price is None:
    current_price = float(df["Close"].iloc[-1])

# ── 4a. SIDEBAR INFO ──────────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.header("📊 Stock Info")
st.sidebar.markdown(f"**Ticker:** {ticker}")
if stock_name:
    st.sidebar.markdown(f"**Name:** {stock_name}")
st.sidebar.markdown(
    f"**Price:** ${current_price:,.2f}" if current_price else "**Price:** N/A"
)
if stock_sector:
    st.sidebar.markdown(f"**Sector:** {stock_sector}")
if stock_industry:
    st.sidebar.markdown(f"**Industry:** {stock_industry}")

# ── Last Fetched Timestamp ─────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.text(f"Last fetched: {datetime.datetime.now().strftime('%H:%M:%S')}")

# ── 4. METRICS ROW ────────────────────────────────────────────────────────
st.subheader(f"{ticker} — Overview")

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Current Price", f"${current_price:,.2f}" if current_price else "N/A")
m2.metric("Day High", f"${day_high:,.2f}" if day_high else "N/A")
m3.metric("Day Low", f"${day_low:,.2f}" if day_low else "N/A")
m4.metric("Volume", f"{volume:,.0f}" if volume else "N/A")
m5.metric("P/E Ratio", f"{pe_ratio:.2f}" if pe_ratio else "N/A")

# ── 5. PRICE CHART ────────────────────────────────────────────────────────
st.subheader(f"{ticker} — Price Chart ({timeframe_label})")

fig = go.Figure()

if chart_type == "Candlestick":
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="OHLC",
        )
    )
else:
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["Close"],
            mode="lines",
            name="Close",
        )
    )

if show_sma_20:
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["SMA_20"],
            mode="lines",
            name="SMA 20",
            line=dict(color="orange", width=1.5),
        )
    )

if show_sma_50:
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["SMA_50"],
            mode="lines",
            name="SMA 50",
            line=dict(color="blue", width=1.5),
        )
    )

fig.update_layout(
    xaxis_title="Date",
    yaxis_title="Price (USD)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    margin=dict(l=40, r=40, t=20, b=40),
    xaxis_rangeslider_visible=False,
)

st.plotly_chart(fig, use_container_width=True)

# ── RSI GAUGE ──────────────────────────────────────────────────────────────
latest_rsi = float(df["RSI"].iloc[-1]) if not pd.isna(df["RSI"].iloc[-1]) else None

if show_rsi_gauge and latest_rsi is not None:
    rsi_fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=latest_rsi,
            title={"text": "RSI Indicator"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "white"},
                "steps": [
                    {"range": [0, 30], "color": "#2ecc71"},    # Oversold (green)
                    {"range": [30, 70], "color": "#95a5a6"},   # Neutral (gray)
                    {"range": [70, 100], "color": "#e74c3c"},  # Overbought (red)
                ],
                "threshold": {
                    "line": {"color": "black", "width": 3},
                    "thickness": 0.8,
                    "value": latest_rsi,
                },
            },
        )
    )
    rsi_fig.update_layout(
        height=300,
        margin=dict(l=40, r=40, t=60, b=20),
    )
    st.plotly_chart(rsi_fig, use_container_width=True)

# ── 6. ALERT FORM ─────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("🔔 Set Price Alert")

with st.form("new_alert_form"):
    alert_cols = st.columns([2, 1, 2, 1])

    with alert_cols[0]:
        threshold = st.number_input(
            "Threshold Price ($)",
            value=float(current_price) if current_price else 0.0,
            step=1.0,
        )
    with alert_cols[1]:
        direction = st.selectbox("Direction", ["above", "below"])
    with alert_cols[2]:
        email = st.text_input("Notify Email")
    with alert_cols[3]:
        st.write("")  # Spacer to align button
        submit_btn = st.form_submit_button("Set Alert")

    if submit_btn:
        if not email or not email.strip():
            st.error("Please enter a valid email address.")
        else:
            try:
                add_alert(ticker, threshold, direction, email.strip())
                st.success(
                    f"✅ Alert set for **{ticker}** "
                    f"{direction} **${threshold:,.2f}**!"
                )
            except Exception as e:
                st.error(f"Failed to save alert: {e}")

# ── 7. ALERTS TABLE ───────────────────────────────────────────────────────
st.subheader("📋 Active Alerts")

try:
    alerts = get_alerts()
    active_alerts = [a for a in alerts if not a["triggered"]]

    if active_alerts:
        alert_data = [
            {
                "Ticker": a["ticker"],
                "Threshold": f"${a['threshold_price']:,.2f}",
                "Direction": a["direction"],
                "Email": a["email"],
            }
            for a in active_alerts
        ]
        st.dataframe(
            pd.DataFrame(alert_data),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No active alerts configured.")
except Exception as e:
    st.error(f"Could not load alerts: {e}")

# ── 8. SENTIMENT CARD ─────────────────────────────────────────────────────
st.markdown("---")
st.subheader("🧠 AI News Sentiment")

if st.button("Analyze News Sentiment"):
    with st.spinner(f"Analysing latest news for {ticker}…"):
        try:
            result = analyze_sentiment(ticker)
            summary = result.get("summary", "No summary available.")
            sentiment = result.get("sentiment", "Neutral")

            st.markdown(f"**Summary:** {summary}")

            if sentiment == "Bullish":
                st.success(f"📈 Overall Sentiment: **{sentiment}**")
            elif sentiment == "Bearish":
                st.error(f"📉 Overall Sentiment: **{sentiment}**")
            else:
                st.warning(f"➡️ Overall Sentiment: **{sentiment}**")
        except Exception as e:
            st.error(f"Sentiment analysis failed: {e}")
