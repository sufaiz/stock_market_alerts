"""Streamlit entry point for the AI-Powered Stock Tracker."""

import os
import sys
import streamlit as st
import plotly.graph_objects as go

# Add workspace root to python path to avoid import errors
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.data_handler import get_stock_data
from app.indicators import calculate_sma, calculate_rsi
from database.db_manager import init_db, add_alert, get_alerts

# Initialize DB on load
init_db()

st.set_page_config(
    page_title="AI-Powered Stock Tracker",
    layout="wide",
)

st.title("📈 AI-Powered Stock Tracker")

# Sidebar - Quick Selection & Custom Input
st.sidebar.header("Select Stock")

presets = {
    "Apple (AAPL)": "AAPL",
    "Microsoft (MSFT)": "MSFT",
    "Alphabet (GOOGL)": "GOOGL",
    "Amazon (AMZN)": "AMZN",
    "Tesla (TSLA)": "TSLA",
    "NVIDIA (NVDA)": "NVDA",
    "Meta (META)": "META",
    "Custom Ticker...": "CUSTOM",
}

selected_preset = st.sidebar.selectbox("Popular Stocks", list(presets.keys()))

if presets[selected_preset] == "CUSTOM":
    ticker = st.sidebar.text_input("Enter Ticker Symbol", value="AAPL").upper().strip()
else:
    ticker = presets[selected_preset]

# Timeframe / Interval selection
st.sidebar.header("Chart Settings")

timeframe_mode = st.sidebar.radio("Timeframe Mode", ["Presets", "Custom Date Range"])

# Initialize values
period = None
start_date = None
end_date = None
interval = "1d"

if timeframe_mode == "Presets":
    timeframe = st.sidebar.selectbox(
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
        index=4  # Default to 6 Months
    )

    # Map selections to period/interval for yfinance
    if timeframe == "1 Day (Real-time, 1m)":
        period, interval = "1d", "1m"
    elif timeframe == "5 Days (Intraday, 15m)":
        period, interval = "5d", "15m"
    elif timeframe == "1 Month (Daily)":
        period, interval = "1mo", "1d"
    elif timeframe == "3 Months (Daily)":
        period, interval = "3mo", "1d"
    elif timeframe == "6 Months (Daily)":
        period, interval = "6mo", "1d"
    elif timeframe == "1 Year (Daily)":
        period, interval = "1y", "1d"
    elif timeframe == "5 Years (Weekly)":
        period, interval = "5y", "1wk"
    else:
        period, interval = "max", "1mo"
else:
    import datetime
    today = datetime.date.today()
    one_year_ago = today - datetime.timedelta(days=365)
    
    start_date = st.sidebar.date_input("Start Date", value=one_year_ago)
    end_date = st.sidebar.date_input("End Date", value=today)
    
    interval = st.sidebar.selectbox(
        "Interval",
        options=["1m", "5m", "15m", "1h", "1d", "1wk", "1mo"],
        index=4  # Default to 1d
    )
    
    # Simple validation
    if start_date > end_date:
        st.sidebar.error("Start Date must be before End Date.")

chart_type = st.sidebar.radio("Chart Type", ["Candlestick", "Line"])

# Add manual refresh button
if st.sidebar.button("🔄 Refresh Data"):
    st.rerun()

# Alert Form in Sidebar
st.sidebar.header("Stock Price Alerts")

if ticker:
    # Fetch data based on the mode selected
    if timeframe_mode == "Presets":
        df = get_stock_data(ticker, period=period, interval=interval)
    else:
        df = get_stock_data(
            ticker, 
            interval=interval, 
            start=start_date.strftime("%Y-%m-%d"), 
            end=end_date.strftime("%Y-%m-%d")
        )


    if df.empty:
        st.error(
            f"No data found for **{ticker}**. "
            "Please check the ticker symbol and try again."
        )
    else:
        df["SMA_20"] = calculate_sma(df, window=20)
        df["SMA_50"] = calculate_sma(df, window=50)
        df["RSI"] = calculate_rsi(df)

        # Get latest price for the default threshold field
        latest_price = float(df["Close"].iloc[-1])

        # Render Alert Form
        with st.sidebar.form("new_alert_form"):
            st.write(f"**Set alert for {ticker}**")
            st.write(f"Current Price: **${latest_price:.2f}**")
            
            threshold = st.number_input("Threshold Price ($)", value=latest_price, step=1.0)
            direction = st.selectbox("Trigger when price goes:", ["above", "below"])
            email = st.text_input("Notify Email")
            
            submit_btn = st.form_submit_button("Set Alert")
            if submit_btn:
                if email.strip() == "":
                    st.sidebar.error("Please enter a valid email.")
                else:
                    add_alert(ticker, threshold, direction, email)
                    st.sidebar.success(f"Alert set for {ticker} {direction} ${threshold:.2f}!")

        # Main Layout: Visualizations
        col1, col2 = st.columns([3, 1])

        with col1:
            st.subheader(f"{ticker} — Stock Price Chart ({timeframe})")
            fig = go.Figure()

            # Add primary price series
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

            # Add overlay SMAs
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df["SMA_20"],
                    mode="lines",
                    name="SMA 20",
                    line=dict(color="orange", width=1.5),
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df["SMA_50"],
                    mode="lines",
                    name="SMA 50",
                    line=dict(color="blue", width=1.5),
                )
            )

            # Configure layout
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Price (USD)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
                margin=dict(l=40, r=40, t=20, b=40),
                xaxis_rangeslider_visible=False,  # Turn off slider to save vertical space
            )

            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Key Statistics")
            st.metric("Latest Close", f"${latest_price:.2f}")
            
            # Show change relative to previous point
            if len(df) > 1:
                prev_price = float(df["Close"].iloc[-2])
                price_change = latest_price - prev_price
                pct_change = (price_change / prev_price) * 100
                st.metric(
                    "Price Change",
                    f"${price_change:+.2f}",
                    delta=f"{pct_change:+.2f}%",
                )

            latest_rsi = float(df["RSI"].iloc[-1])
            st.metric("RSI (14)", f"{latest_rsi:.1f}")

        # Active Alerts Section
        st.subheader("Active Alerts")
        alerts = get_alerts()
        active_alerts = [a for a in alerts if not a["triggered"]]
        if active_alerts:
            alert_data = []
            for a in active_alerts:
                alert_data.append({
                    "Ticker": a["ticker"],
                    "Threshold": f"${a['threshold_price']:.2f}",
                    "Direction": a["direction"],
                    "Email": a["email"]
                })
            st.table(alert_data)
        else:
            st.info("No active alerts configured.")


