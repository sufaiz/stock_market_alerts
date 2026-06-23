"""Streamlit entry point for the AI-Powered Stock Tracker."""

import os
import sys
import datetime

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# Add workspace root to python path to avoid import errors
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.data_handler import get_stock_data, get_stock_info
from app.indicators import calculate_sma, calculate_rsi
from database.db_manager import init_db, add_alert, get_alerts

# Initialize DB on load
init_db()

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="StockPulse — AI-Powered Tracker",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Premium Dark Theme CSS ───────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ─── Root Variables ─── */
:root {
    --bg-primary: #0d1117;
    --bg-secondary: #161b22;
    --bg-card: rgba(22, 27, 34, 0.8);
    --bg-card-hover: rgba(30, 37, 48, 0.9);
    --border-color: rgba(48, 54, 61, 0.6);
    --text-primary: #e6edf3;
    --text-secondary: #8b949e;
    --text-muted: #6e7681;
    --accent-green: #26a69a;
    --accent-red: #ef5350;
    --accent-blue: #58a6ff;
    --accent-purple: #bc8cff;
    --accent-orange: #f0883e;
    --accent-gradient: linear-gradient(135deg, #58a6ff 0%, #bc8cff 100%);
    --glow-green: 0 0 20px rgba(38, 166, 154, 0.3);
    --glow-red: 0 0 20px rgba(239, 83, 80, 0.3);
}

/* ─── Global ─── */
html, body, .stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
}

.stApp > header { background: transparent !important; }
.block-container { padding-top: 1rem !important; max-width: 100% !important; }

/* ─── Sidebar ─── */
section[data-testid="stSidebar"] {
    background: var(--bg-secondary) !important;
    border-right: 1px solid var(--border-color) !important;
}
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stTextInput label,
section[data-testid="stSidebar"] .stNumberInput label,
section[data-testid="stSidebar"] .stRadio label,
section[data-testid="stSidebar"] .stDateInput label {
    color: var(--text-secondary) !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: var(--text-primary) !important;
    font-weight: 600 !important;
}

/* ─── Timeframe Button Bar ─── */
.tf-bar {
    display: flex;
    gap: 4px;
    padding: 6px 8px;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    margin-bottom: 0.5rem;
    align-items: center;
    flex-wrap: wrap;
}
.tf-btn {
    padding: 6px 14px;
    border: none;
    border-radius: 6px;
    background: transparent;
    color: var(--text-secondary);
    font-family: 'Inter', sans-serif;
    font-size: 0.78rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    letter-spacing: 0.02em;
}
.tf-btn:hover {
    background: rgba(88, 166, 255, 0.1);
    color: var(--accent-blue);
}
.tf-btn.active {
    background: rgba(88, 166, 255, 0.15);
    color: var(--accent-blue);
    box-shadow: inset 0 -2px 0 var(--accent-blue);
}
.tf-sep {
    width: 1px;
    height: 20px;
    background: var(--border-color);
    margin: 0 4px;
}
.chart-type-btn {
    padding: 5px 10px;
    border: 1px solid var(--border-color);
    border-radius: 5px;
    background: transparent;
    color: var(--text-secondary);
    font-family: 'Inter', sans-serif;
    font-size: 0.75rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
}
.chart-type-btn:hover { border-color: var(--accent-blue); color: var(--accent-blue); }
.chart-type-btn.active {
    background: rgba(88, 166, 255, 0.15);
    border-color: var(--accent-blue);
    color: var(--accent-blue);
}

/* ─── Metric Cards ─── */
.metric-card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 16px 20px;
    backdrop-filter: blur(12px);
    transition: all 0.3s ease;
}
.metric-card:hover {
    background: var(--bg-card-hover);
    border-color: rgba(88, 166, 255, 0.3);
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}
.metric-label {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-muted);
    margin-bottom: 4px;
}
.metric-value {
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1.2;
}
.metric-delta {
    font-size: 0.85rem;
    font-weight: 600;
    margin-top: 4px;
    display: flex;
    align-items: center;
    gap: 4px;
}
.metric-delta.positive { color: var(--accent-green); }
.metric-delta.negative { color: var(--accent-red); }

/* ─── Ticker Header ─── */
.ticker-header {
    display: flex;
    align-items: baseline;
    gap: 16px;
    margin-bottom: 4px;
    flex-wrap: wrap;
}
.ticker-symbol {
    font-size: 1.8rem;
    font-weight: 800;
    background: var(--accent-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.02em;
}
.ticker-price {
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--text-primary);
}
.ticker-change {
    font-size: 1rem;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 6px;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}
.ticker-change.positive {
    color: var(--accent-green);
    background: rgba(38, 166, 154, 0.12);
}
.ticker-change.negative {
    color: var(--accent-red);
    background: rgba(239, 83, 80, 0.12);
}

/* ─── RSI Gauge ─── */
.rsi-gauge {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 16px 20px;
    backdrop-filter: blur(12px);
}
.rsi-bar-bg {
    height: 8px;
    background: linear-gradient(90deg, var(--accent-red) 0%, #ffd54f 30%, var(--accent-green) 70%, var(--accent-red) 100%);
    border-radius: 4px;
    position: relative;
    margin-top: 8px;
}
.rsi-marker {
    width: 14px;
    height: 14px;
    background: white;
    border: 2px solid var(--bg-primary);
    border-radius: 50%;
    position: absolute;
    top: -3px;
    transform: translateX(-50%);
    box-shadow: 0 0 8px rgba(255,255,255,0.4);
}
.rsi-labels {
    display: flex;
    justify-content: space-between;
    margin-top: 6px;
    font-size: 0.65rem;
    color: var(--text-muted);
    font-weight: 500;
}

/* ─── Alert Table ─── */
.alert-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid var(--border-color);
}
.alert-table th {
    background: var(--bg-secondary);
    color: var(--text-muted);
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 10px 16px;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
}
.alert-table td {
    padding: 12px 16px;
    color: var(--text-primary);
    font-size: 0.85rem;
    border-bottom: 1px solid rgba(48, 54, 61, 0.3);
    background: var(--bg-card);
}
.alert-table tr:last-child td { border-bottom: none; }
.alert-table tr:hover td { background: var(--bg-card-hover); }
.alert-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
}
.alert-badge.above {
    background: rgba(38, 166, 154, 0.15);
    color: var(--accent-green);
}
.alert-badge.below {
    background: rgba(239, 83, 80, 0.15);
    color: var(--accent-red);
}

/* ─── Section Headers ─── */
.section-header {
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text-muted);
    margin: 24px 0 12px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border-color);
}

/* ─── Hide default Streamlit elements ─── */
div[data-testid="stMetric"] { display: none; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

/* ─── Streamlit button overrides ─── */
.stButton > button {
    background: rgba(88, 166, 255, 0.1) !important;
    color: var(--accent-blue) !important;
    border: 1px solid rgba(88, 166, 255, 0.3) !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    background: rgba(88, 166, 255, 0.2) !important;
    border-color: var(--accent-blue) !important;
    box-shadow: 0 0 16px rgba(88, 166, 255, 0.2) !important;
}

/* ─── Custom date range area ─── */
.custom-range-box {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)


# ── Timeframe Configuration ──────────────────────────────────────────────────
TIMEFRAMES = {
    "1D":  ("1d",  "1m"),
    "5D":  ("5d",  "15m"),
    "1M":  ("1mo", "1d"),
    "3M":  ("3mo", "1d"),
    "6M":  ("6mo", "1d"),
    "1Y":  ("1y",  "1d"),
    "5Y":  ("5y",  "1wk"),
    "Max": ("max", "1mo"),
}

if "timeframe" not in st.session_state:
    st.session_state.timeframe = "6M"
if "chart_type" not in st.session_state:
    st.session_state.chart_type = "Candlestick"
if "custom_range" not in st.session_state:
    st.session_state.custom_range = False


# ── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.markdown(
    "<h2 style='margin-bottom:0; background: linear-gradient(135deg, #58a6ff, #bc8cff); "
    "-webkit-background-clip: text; -webkit-text-fill-color: transparent;'>"
    "⚡ StockPulse</h2>",
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    "<p style='color:#6e7681; font-size:0.75rem; margin-top:0;'>"
    "AI-Powered Market Tracker</p>",
    unsafe_allow_html=True,
)
st.sidebar.markdown("---")

# Asset Class Selection
st.sidebar.markdown(
    "<p class='metric-label' style='margin-bottom:4px;'>Asset Class</p>",
    unsafe_allow_html=True,
)
asset_class = st.sidebar.selectbox(
    "Asset Class",
    ["US Stocks", "Indian Stocks (NSE)", "Commodities", "Forex Pairs", "Custom Ticker"],
    label_visibility="collapsed",
)

ticker = "AAPL"

if asset_class == "US Stocks":
    us_presets = {
        "AAPL — Apple Inc.": "AAPL",
        "MSFT — Microsoft": "MSFT",
        "GOOGL — Alphabet": "GOOGL",
        "AMZN — Amazon": "AMZN",
        "TSLA — Tesla": "TSLA",
        "NVDA — NVIDIA": "NVDA",
        "META — Meta Platforms": "META",
        "NFLX — Netflix": "NFLX",
        "AMD — AMD": "AMD",
        "JPM — JPMorgan Chase": "JPM",
    }
    sel = st.sidebar.selectbox("Select", list(us_presets.keys()), label_visibility="collapsed")
    ticker = us_presets[sel]

elif asset_class == "Indian Stocks (NSE)":
    in_presets = {
        "RELIANCE.NS — Reliance Industries": "RELIANCE.NS",
        "TCS.NS — Tata Consultancy": "TCS.NS",
        "HDFCBANK.NS — HDFC Bank": "HDFCBANK.NS",
        "INFY.NS — Infosys": "INFY.NS",
        "ICICIBANK.NS — ICICI Bank": "ICICIBANK.NS",
        "SBIN.NS — State Bank of India": "SBIN.NS",
        "WIPRO.NS — Wipro": "WIPRO.NS",
        "TATAMOTORS.NS — Tata Motors": "TATAMOTORS.NS",
        "BHARTIARTL.NS — Bharti Airtel": "BHARTIARTL.NS",
        "LT.NS — Larsen & Toubro": "LT.NS",
        "ADANIENT.NS — Adani Enterprises": "ADANIENT.NS",
        "ITC.NS — ITC Limited": "ITC.NS",
    }
    sel = st.sidebar.selectbox("Select", list(in_presets.keys()), label_visibility="collapsed")
    ticker = in_presets[sel]

elif asset_class == "Commodities":
    comm_presets = {
        "GC=F — Gold Futures": "GC=F",
        "SI=F — Silver Futures": "SI=F",
        "CL=F — Crude Oil (WTI)": "CL=F",
        "NG=F — Natural Gas": "NG=F",
        "HG=F — Copper Futures": "HG=F",
        "PL=F — Platinum Futures": "PL=F",
    }
    sel = st.sidebar.selectbox("Select", list(comm_presets.keys()), label_visibility="collapsed")
    ticker = comm_presets[sel]

elif asset_class == "Forex Pairs":
    forex_presets = {
        "EURUSD=X — EUR / USD": "EURUSD=X",
        "GBPUSD=X — GBP / USD": "GBPUSD=X",
        "USDJPY=X — USD / JPY": "USDJPY=X",
        "USDINR=X — USD / INR": "USDINR=X",
        "AUDUSD=X — AUD / USD": "AUDUSD=X",
        "USDCAD=X — USD / CAD": "USDCAD=X",
        "GBPINR=X — GBP / INR": "GBPINR=X",
    }
    sel = st.sidebar.selectbox("Select", list(forex_presets.keys()), label_visibility="collapsed")
    ticker = forex_presets[sel]

else:
    ticker = st.sidebar.text_input(
        "Ticker Symbol (e.g. BTC-USD)", value="AAPL"
    ).upper().strip()

st.sidebar.markdown("---")

# ── Alert Form (Sidebar) ────────────────────────────────────────────────────
st.sidebar.markdown(
    "<p class='metric-label'>🔔 Price Alerts</p>",
    unsafe_allow_html=True,
)


# ── Determine Period / Interval ──────────────────────────────────────────────
def get_period_interval():
    """Return (period, interval, start, end) based on session state."""
    if st.session_state.custom_range:
        return None, st.session_state.get("custom_interval", "1d"), \
            st.session_state.get("custom_start"), st.session_state.get("custom_end")
    tf = st.session_state.timeframe
    p, i = TIMEFRAMES.get(tf, ("6mo", "1d"))
    return p, i, None, None


# ── Main Content ─────────────────────────────────────────────────────────────
if ticker:
    period, interval, start, end = get_period_interval()

    if start and end:
        df = get_stock_data(
            ticker, interval=interval,
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
        )
    else:
        df = get_stock_data(ticker, period=period, interval=interval)

    if df.empty:
        st.markdown(
            "<div style='text-align:center; padding:80px 0;'>"
            "<p style='font-size:3rem;'>😵</p>"
            f"<p style='color:var(--text-secondary); font-size:1.1rem;'>"
            f"No data found for <strong>{ticker}</strong>. Check the symbol and try again.</p>"
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        # ── Compute Indicators ───────────────────────────────────────────
        df["SMA_20"] = calculate_sma(df, window=20)
        df["SMA_50"] = calculate_sma(df, window=50)
        df["RSI"] = calculate_rsi(df)

        latest_price = float(df["Close"].iloc[-1])
        prev_price = float(df["Close"].iloc[-2]) if len(df) > 1 else latest_price
        price_change = latest_price - prev_price
        pct_change = (price_change / prev_price) * 100 if prev_price != 0 else 0
        latest_rsi = float(df["RSI"].iloc[-1])
        day_high = float(df["High"].iloc[-1])
        day_low = float(df["Low"].iloc[-1])
        latest_volume = int(df["Volume"].iloc[-1]) if "Volume" in df.columns else 0
        is_positive = price_change >= 0
        change_class = "positive" if is_positive else "negative"
        arrow = "▲" if is_positive else "▼"

        # ── Alert Form ───────────────────────────────────────────────────
        with st.sidebar.form("new_alert_form"):
            st.markdown(
                f"<p style='color:var(--text-primary); font-size:0.9rem; font-weight:600;'>"
                f"Set alert for {ticker}</p>"
                f"<p style='color:var(--text-muted); font-size:0.8rem;'>"
                f"Current: ${latest_price:,.2f}</p>",
                unsafe_allow_html=True,
            )
            threshold = st.number_input("Threshold ($)", value=latest_price, step=1.0)
            direction = st.selectbox("Direction", ["above", "below"])
            email = st.text_input("Email")
            submitted = st.form_submit_button("⚡ Set Alert")
            if submitted:
                if not email.strip():
                    st.error("Enter a valid email.")
                else:
                    add_alert(ticker, threshold, direction, email)
                    st.success(f"Alert set: {ticker} {direction} ${threshold:,.2f}")

        # ── Ticker Header ────────────────────────────────────────────────
        st.markdown(
            f"""
            <div class="ticker-header">
                <span class="ticker-symbol">{ticker}</span>
                <span class="ticker-price">${latest_price:,.2f}</span>
                <span class="ticker-change {change_class}">
                    {arrow} {abs(price_change):,.2f} ({abs(pct_change):.2f}%)
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Timeframe Button Bar (HTML) ──────────────────────────────────
        tf_buttons_html = ""
        for label in TIMEFRAMES:
            active = "active" if label == st.session_state.timeframe and not st.session_state.custom_range else ""
            tf_buttons_html += f'<span class="tf-btn {active}">{label}</span>'

        custom_active = "active" if st.session_state.custom_range else ""
        candle_active = "active" if st.session_state.chart_type == "Candlestick" else ""
        line_active = "active" if st.session_state.chart_type == "Line" else ""

        st.markdown(
            f"""
            <div class="tf-bar">
                {tf_buttons_html}
                <span class="tf-sep"></span>
                <span class="tf-btn {custom_active}">Custom</span>
                <span class="tf-sep"></span>
                <span class="chart-type-btn {candle_active}" title="Candlestick">🕯️</span>
                <span class="chart-type-btn {line_active}" title="Line">📈</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Functional timeframe controls (Streamlit columns)
        tf_cols = st.columns(len(TIMEFRAMES) + 3)
        for idx, label in enumerate(TIMEFRAMES):
            with tf_cols[idx]:
                if st.button(label, key=f"tf_{label}", use_container_width=True):
                    st.session_state.timeframe = label
                    st.session_state.custom_range = False
                    st.rerun()
        with tf_cols[len(TIMEFRAMES)]:
            if st.button("Custom", key="tf_custom", use_container_width=True):
                st.session_state.custom_range = not st.session_state.custom_range
                st.rerun()
        with tf_cols[len(TIMEFRAMES) + 1]:
            if st.button("🕯️", key="ct_candle", use_container_width=True):
                st.session_state.chart_type = "Candlestick"
                st.rerun()
        with tf_cols[len(TIMEFRAMES) + 2]:
            if st.button("📈", key="ct_line", use_container_width=True):
                st.session_state.chart_type = "Line"
                st.rerun()

        # Custom date range inputs
        if st.session_state.custom_range:
            cr1, cr2, cr3 = st.columns(3)
            with cr1:
                today = datetime.date.today()
                one_year_ago = today - datetime.timedelta(days=365)
                st.session_state.custom_start = st.date_input(
                    "Start", value=one_year_ago, key="cstart"
                )
            with cr2:
                st.session_state.custom_end = st.date_input(
                    "End", value=today, key="cend"
                )
            with cr3:
                st.session_state.custom_interval = st.selectbox(
                    "Interval",
                    ["1m", "5m", "15m", "1h", "1d", "1wk", "1mo"],
                    index=4,
                    key="cinterval",
                )
            if st.button("Apply Custom Range"):
                st.rerun()

        # ── Build Multi-Panel Chart ──────────────────────────────────────
        has_volume = "Volume" in df.columns and df["Volume"].sum() > 0

        row_heights = [0.55, 0.25, 0.20] if has_volume else [0.65, 0.35]
        num_rows = 3 if has_volume else 2
        subplot_titles = ("", "Volume", "RSI (14)") if has_volume else ("", "RSI (14)")

        fig = make_subplots(
            rows=num_rows, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=row_heights,
            subplot_titles=subplot_titles,
        )

        # ── Row 1: Price (Candlestick or Line) + SMAs ────────────────────
        if st.session_state.chart_type == "Candlestick":
            fig.add_trace(
                go.Candlestick(
                    x=df.index,
                    open=df["Open"],
                    high=df["High"],
                    low=df["Low"],
                    close=df["Close"],
                    name="OHLC",
                    increasing_line_color="#26a69a",
                    increasing_fillcolor="#26a69a",
                    decreasing_line_color="#ef5350",
                    decreasing_fillcolor="#ef5350",
                    increasing_line_width=1,
                    decreasing_line_width=1,
                ),
                row=1, col=1,
            )
        else:
            fig.add_trace(
                go.Scatter(
                    x=df.index, y=df["Close"],
                    mode="lines", name="Close",
                    line=dict(color="#58a6ff", width=2),
                    fill="tozeroy",
                    fillcolor="rgba(88, 166, 255, 0.06)",
                ),
                row=1, col=1,
            )

        # SMA overlays
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df["SMA_20"],
                mode="lines", name="SMA 20",
                line=dict(color="#f0883e", width=1.2, dash="dot"),
            ),
            row=1, col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df["SMA_50"],
                mode="lines", name="SMA 50",
                line=dict(color="#bc8cff", width=1.2, dash="dot"),
            ),
            row=1, col=1,
        )

        # ── Row 2: Volume ────────────────────────────────────────────────
        if has_volume:
            vol_colors = [
                "#26a69a" if c >= o else "#ef5350"
                for c, o in zip(df["Close"], df["Open"])
            ]
            fig.add_trace(
                go.Bar(
                    x=df.index, y=df["Volume"],
                    name="Volume",
                    marker_color=vol_colors,
                    opacity=0.5,
                    showlegend=False,
                ),
                row=2, col=1,
            )
            rsi_row = 3
        else:
            rsi_row = 2

        # ── Row 3 (or 2): RSI ────────────────────────────────────────────
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df["RSI"],
                mode="lines", name="RSI",
                line=dict(color="#58a6ff", width=1.5),
            ),
            row=rsi_row, col=1,
        )
        # Overbought / Oversold lines
        fig.add_hline(y=70, line_dash="dash", line_color="rgba(239,83,80,0.4)",
                      line_width=1, row=rsi_row, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="rgba(38,166,154,0.4)",
                      line_width=1, row=rsi_row, col=1)
        # Shade overbought / oversold zones
        fig.add_hrect(y0=70, y1=100, fillcolor="rgba(239,83,80,0.05)",
                      line_width=0, row=rsi_row, col=1)
        fig.add_hrect(y0=0, y1=30, fillcolor="rgba(38,166,154,0.05)",
                      line_width=0, row=rsi_row, col=1)

        # ── Chart Layout (TradingView Dark Theme) ────────────────────────
        fig.update_layout(
            height=680,
            paper_bgcolor="#0d1117",
            plot_bgcolor="#0d1117",
            font=dict(family="Inter, sans-serif", color="#8b949e", size=11),
            legend=dict(
                orientation="h",
                yanchor="bottom", y=1.01, x=0,
                font=dict(size=11, color="#8b949e"),
                bgcolor="rgba(0,0,0,0)",
            ),
            margin=dict(l=50, r=20, t=30, b=20),
            xaxis_rangeslider_visible=False,
            hovermode="x unified",
            hoverlabel=dict(
                bgcolor="#161b22",
                font_size=12,
                font_family="Inter, sans-serif",
                font_color="#e6edf3",
                bordercolor="#30363d",
            ),
        )

        # Style all x/y axes
        axis_style = dict(
            gridcolor="rgba(48,54,61,0.4)",
            zerolinecolor="rgba(48,54,61,0.4)",
            tickfont=dict(color="#6e7681", size=10),
            showgrid=True,
            gridwidth=1,
        )
        fig.update_xaxes(**axis_style)
        fig.update_yaxes(**axis_style)

        # RSI y-axis range
        fig.update_yaxes(range=[0, 100], row=rsi_row, col=1)

        # Subplot title styling
        for annotation in fig.layout.annotations:
            annotation.font = dict(size=11, color="#6e7681", family="Inter, sans-serif")

        # Crosshair cursor
        fig.update_xaxes(
            showspikes=True, spikethickness=1,
            spikecolor="#30363d", spikemode="across",
            spikesnap="cursor", spikedash="solid",
        )
        fig.update_yaxes(
            showspikes=True, spikethickness=1,
            spikecolor="#30363d", spikemode="across",
            spikesnap="cursor", spikedash="solid",
        )

        st.plotly_chart(fig, use_container_width=True, config={
            "displayModeBar": True,
            "displaylogo": False,
            "modeBarButtonsToAdd": ["drawline", "drawopenpath", "eraseshape"],
            "modeBarButtonsToRemove": ["lasso2d", "select2d"],
            "scrollZoom": True,
        })

        # ── Metric Cards Row ─────────────────────────────────────────────
        m1, m2, m3, m4, m5 = st.columns(5)

        with m1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Latest Close</div>
                    <div class="metric-value">${latest_price:,.2f}</div>
                    <div class="metric-delta {change_class}">
                        {arrow} ${abs(price_change):,.2f} ({abs(pct_change):.2f}%)
                    </div>
                </div>
                """, unsafe_allow_html=True,
            )

        with m2:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Day High</div>
                    <div class="metric-value">${day_high:,.2f}</div>
                </div>
                """, unsafe_allow_html=True,
            )

        with m3:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Day Low</div>
                    <div class="metric-value">${day_low:,.2f}</div>
                </div>
                """, unsafe_allow_html=True,
            )

        with m4:
            vol_display = f"{latest_volume:,.0f}" if latest_volume > 0 else "N/A"
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Volume</div>
                    <div class="metric-value">{vol_display}</div>
                </div>
                """, unsafe_allow_html=True,
            )

        with m5:
            rsi_status = "Overbought" if latest_rsi > 70 else ("Oversold" if latest_rsi < 30 else "Neutral")
            rsi_color = (
                "var(--accent-red)" if latest_rsi > 70
                else ("var(--accent-green)" if latest_rsi < 30 else "var(--accent-blue)")
            )
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">RSI (14)</div>
                    <div class="metric-value" style="color: {rsi_color};">{latest_rsi:.1f}</div>
                    <div class="metric-delta" style="color: {rsi_color};">{rsi_status}</div>
                </div>
                """, unsafe_allow_html=True,
            )

        # ── RSI Visual Gauge ─────────────────────────────────────────────
        rsi_pct = max(0, min(100, latest_rsi))
        st.markdown(
            f"""
            <div class="rsi-gauge" style="margin-top:8px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span class="metric-label" style="margin:0;">RSI Gauge</span>
                    <span style="color:{rsi_color}; font-weight:700; font-size:0.9rem;">{latest_rsi:.1f}</span>
                </div>
                <div class="rsi-bar-bg">
                    <div class="rsi-marker" style="left:{rsi_pct}%;"></div>
                </div>
                <div class="rsi-labels">
                    <span>0 — Oversold</span>
                    <span>30</span>
                    <span>50</span>
                    <span>70</span>
                    <span>100 — Overbought</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Active Alerts ────────────────────────────────────────────────
        st.markdown('<div class="section-header">🔔 Active Alerts</div>', unsafe_allow_html=True)

        alerts = get_alerts()
        active_alerts = [a for a in alerts if not a["triggered"]]
        if active_alerts:
            rows_html = ""
            for a in active_alerts:
                badge_class = a["direction"]
                rows_html += f"""
                <tr>
                    <td><strong>{a['ticker']}</strong></td>
                    <td>${a['threshold_price']:,.2f}</td>
                    <td><span class="alert-badge {badge_class}">{a['direction'].upper()}</span></td>
                    <td>{a['email']}</td>
                </tr>
                """
            st.markdown(
                f"""
                <table class="alert-table">
                    <thead>
                        <tr>
                            <th>Ticker</th>
                            <th>Threshold</th>
                            <th>Direction</th>
                            <th>Email</th>
                        </tr>
                    </thead>
                    <tbody>{rows_html}</tbody>
                </table>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div style='text-align:center; padding:32px; color:var(--text-muted); "
                "font-size:0.9rem; background:var(--bg-card); border:1px solid var(--border-color); "
                "border-radius:12px;'>"
                "No active alerts configured. Use the sidebar to set one.</div>",
                unsafe_allow_html=True,
            )
