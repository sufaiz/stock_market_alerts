"""Streamlit entry point for the AI-Powered Stock Tracker.

Uses TradingView's Lightweight Charts (open-source) for a native
TradingView charting experience.
"""

import os
import sys
import json
import datetime

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

# Add workspace root to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.data_handler import get_stock_data, get_stock_info
from app.indicators import calculate_sma, calculate_rsi
from database.db_manager import init_db, add_alert, get_alerts

init_db()

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="StockPulse — AI-Powered Tracker",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session State Defaults ───────────────────────────────────────────────────
if "timeframe" not in st.session_state:
    st.session_state.timeframe = "D"
if "chart_type" not in st.session_state:
    st.session_state.chart_type = "Candlestick"
if "custom_range" not in st.session_state:
    st.session_state.custom_range = False

# TradingView-style timeframes: label → (yfinance period, yfinance interval)
# yfinance limits: 1m→7d max, 2m/5m/15m/30m→60d max, 1h→730d max
TIMEFRAMES = {
    "1":   ("5d",   "1m"),     # 1-minute candles
    "2":   ("60d",  "2m"),     # 2-minute candles
    "5":   ("60d",  "5m"),     # 5-minute candles
    "15":  ("60d",  "15m"),    # 15-minute candles
    "30":  ("60d",  "30m"),    # 30-minute candles
    "1H":  ("2y",   "1h"),     # 1-hour candles
    "D":   ("1y",   "1d"),     # Daily candles
    "W":   ("5y",   "1wk"),    # Weekly candles
    "M":   ("max",  "1mo"),    # Monthly candles
}


# ── Premium CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {
    --tv-bg: #131722;
    --bg-secondary: #1e222d;
    --border: #2a2e39;
    --text: #d1d4dc;
    --text-dim: #787b86;
    --green: #26a69a;
    --red: #ef5350;
    --blue: #2962ff;
    --accent-gradient: linear-gradient(135deg, #2962ff 0%, #7b61ff 100%);
}

html, body, .stApp {
    font-family: 'Inter', -apple-system, sans-serif !important;
    background: var(--tv-bg) !important;
    color: var(--text) !important;
}
.stApp > header { background: transparent !important; }
.block-container { padding-top: 0.5rem !important; max-width: 100% !important; }
#MainMenu, footer { visibility: hidden; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #1e222d !important;
    border-right: 1px solid #2a2e39 !important;
}
section[data-testid="stSidebar"] * {
    font-family: 'Inter', sans-serif !important;
}

/* Ticker Header */
.tv-header {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 8px 0 4px 0;
    flex-wrap: wrap;
}
.tv-symbol {
    font-size: 1.5rem;
    font-weight: 800;
    color: #d1d4dc;
    letter-spacing: -0.01em;
}
.tv-exchange {
    font-size: 0.75rem;
    color: #787b86;
    font-weight: 500;
    padding: 2px 8px;
    background: rgba(120,123,134,0.1);
    border-radius: 4px;
}
.tv-price {
    font-size: 1.5rem;
    font-weight: 700;
}
.tv-change {
    font-size: 0.85rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 4px;
}
.tv-up { color: #26a69a; }
.tv-down { color: #ef5350; }
.tv-change.tv-up { background: rgba(38,166,154,0.12); }
.tv-change.tv-down { background: rgba(239,83,80,0.12); }

/* Timeframe Toolbar */
.tv-toolbar {
    display: flex;
    align-items: center;
    gap: 2px;
    padding: 4px 0;
    border-bottom: 1px solid #2a2e39;
    margin-bottom: 4px;
    flex-wrap: wrap;
}
.tv-toolbar .sep {
    width: 1px;
    height: 18px;
    background: #2a2e39;
    margin: 0 6px;
}

/* Streamlit button overrides for toolbar */
.stButton > button {
    background: transparent !important;
    color: #787b86 !important;
    border: none !important;
    border-radius: 4px !important;
    font-weight: 600 !important;
    font-size: 0.78rem !important;
    font-family: 'Inter', sans-serif !important;
    padding: 4px 10px !important;
    min-height: 0 !important;
    height: auto !important;
    line-height: 1.4 !important;
}
.stButton > button:hover {
    background: rgba(41,98,255,0.1) !important;
    color: #2962ff !important;
}
.stButton > button:focus {
    box-shadow: none !important;
}

/* Metric Cards */
.mc-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 10px;
    margin-top: 10px;
}
.mc {
    background: #1e222d;
    border: 1px solid #2a2e39;
    border-radius: 8px;
    padding: 14px 16px;
    transition: border-color 0.2s;
}
.mc:hover { border-color: #363a45; }
.mc-label {
    font-size: 0.65rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #787b86;
    margin-bottom: 4px;
}
.mc-val {
    font-size: 1.2rem;
    font-weight: 700;
    color: #d1d4dc;
}
.mc-delta {
    font-size: 0.78rem;
    font-weight: 600;
    margin-top: 2px;
}

/* RSI Gauge */
.rsi-gauge-bar {
    height: 6px;
    border-radius: 3px;
    background: linear-gradient(90deg, #ef5350 0%, #ffd54f 30%, #26a69a 50%, #ffd54f 70%, #ef5350 100%);
    position: relative;
    margin: 8px 0 4px 0;
}
.rsi-dot {
    width: 12px; height: 12px;
    background: #fff;
    border: 2px solid #131722;
    border-radius: 50%;
    position: absolute;
    top: -3px;
    transform: translateX(-50%);
    box-shadow: 0 0 6px rgba(255,255,255,0.3);
}
.rsi-ticks {
    display: flex;
    justify-content: space-between;
    font-size: 0.6rem;
    color: #787b86;
}

/* Alert Table */
.at { width:100%; border-collapse:separate; border-spacing:0; border-radius:8px; overflow:hidden; border:1px solid #2a2e39; }
.at th { background:#1e222d; color:#787b86; font-size:0.65rem; font-weight:600; text-transform:uppercase; letter-spacing:0.08em; padding:8px 14px; text-align:left; }
.at td { padding:10px 14px; color:#d1d4dc; font-size:0.82rem; border-top:1px solid rgba(42,46,57,0.5); background:#131722; }
.at tr:hover td { background:#1e222d; }
.badge { display:inline-block; padding:2px 10px; border-radius:12px; font-size:0.7rem; font-weight:700; }
.badge.above { background:rgba(38,166,154,0.15); color:#26a69a; }
.badge.below { background:rgba(239,83,80,0.15); color:#ef5350; }

/* Section label */
.sec-label {
    font-size: 0.7rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.1em; color: #787b86; margin: 18px 0 8px 0;
    padding-bottom: 6px; border-bottom: 1px solid #2a2e39;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# CHART RENDERING — TradingView Lightweight Charts
# ══════════════════════════════════════════════════════════════════════════════

def prepare_chart_data(df: pd.DataFrame):
    """Convert DataFrame to JSON-ready lists for Lightweight Charts."""
    candles, volumes, sma20, sma50, rsi_data = [], [], [], [], []

    for idx, row in df.iterrows():
        ts = int(pd.Timestamp(idx).timestamp())

        candles.append({
            "time": ts,
            "open": round(float(row["Open"]), 4),
            "high": round(float(row["High"]), 4),
            "low": round(float(row["Low"]), 4),
            "close": round(float(row["Close"]), 4),
        })

        vol = float(row.get("Volume", 0))
        vol_color = "rgba(38,166,154,0.35)" if row["Close"] >= row["Open"] else "rgba(239,83,80,0.35)"
        volumes.append({"time": ts, "value": vol, "color": vol_color})

        if pd.notna(row.get("SMA_20")):
            sma20.append({"time": ts, "value": round(float(row["SMA_20"]), 4)})
        if pd.notna(row.get("SMA_50")):
            sma50.append({"time": ts, "value": round(float(row["SMA_50"]), 4)})

        rsi_data.append({"time": ts, "value": round(float(row["RSI"]), 2)})

    return candles, volumes, sma20, sma50, rsi_data


def render_tv_chart(df, ticker, chart_type="Candlestick"):
    """Render a TradingView Lightweight Charts component."""
    candles, volumes, sma20, sma50, rsi_data = prepare_chart_data(df)
    has_volume = any(v["value"] > 0 for v in volumes)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ background:#131722; font-family:'Inter',-apple-system,sans-serif; overflow:hidden; }}
        #wrapper {{ width:100%; height:100vh; display:flex; flex-direction:column; }}
        #main-container {{ flex:1; position:relative; min-height:0; }}
        #rsi-container {{ height:120px; position:relative; border-top:1px solid #2a2e39; }}

        /* OHLC Legend */
        .legend {{
            position:absolute; top:8px; left:12px; z-index:10;
            font-size:11px; font-family:'Inter',monospace;
            display:flex; gap:14px; align-items:center;
            pointer-events:none;
        }}
        .legend .sym {{ color:#d1d4dc; font-weight:700; font-size:13px; }}
        .legend .lbl {{ color:#787b86; }}
        .legend .val {{ font-weight:600; font-variant-numeric:tabular-nums; }}
        .legend .up {{ color:#26a69a; }}
        .legend .dn {{ color:#ef5350; }}

        /* RSI Legend */
        .rsi-legend {{
            position:absolute; top:4px; left:12px; z-index:10;
            font-size:11px; font-family:'Inter',monospace;
            display:flex; gap:10px; align-items:center;
            pointer-events:none;
        }}
        .rsi-legend .lbl {{ color:#787b86; font-weight:600; }}
        .rsi-legend .val {{ color:#7b61ff; font-weight:700; }}

        /* SMA Legend */
        .sma-legend {{
            position:absolute; top:26px; left:12px; z-index:10;
            font-size:10px; font-family:'Inter',monospace;
            display:flex; gap:16px;
            pointer-events:none;
        }}
        .sma-legend .sma-item {{ display:flex; align-items:center; gap:4px; }}
        .sma-legend .dot {{ width:8px; height:3px; border-radius:1px; }}
    </style>
    </head>
    <body>
    <div id="wrapper">
        <div id="main-container">
            <div class="legend" id="legend">
                <span class="sym">{ticker}</span>
                <span><span class="lbl">O</span> <span class="val" id="l-o">—</span></span>
                <span><span class="lbl">H</span> <span class="val" id="l-h">—</span></span>
                <span><span class="lbl">L</span> <span class="val" id="l-l">—</span></span>
                <span><span class="lbl">C</span> <span class="val" id="l-c">—</span></span>
                <span><span class="lbl">Vol</span> <span class="val" id="l-v" style="color:#787b86;">—</span></span>
            </div>
            <div class="sma-legend" id="sma-legend">
                <div class="sma-item">
                    <span class="dot" style="background:#e9963e;"></span>
                    <span style="color:#e9963e;">SMA 20: <span id="l-sma20">—</span></span>
                </div>
                <div class="sma-item">
                    <span class="dot" style="background:#7b61ff;"></span>
                    <span style="color:#7b61ff;">SMA 50: <span id="l-sma50">—</span></span>
                </div>
            </div>
        </div>
        <div id="rsi-container">
            <div class="rsi-legend">
                <span class="lbl">RSI(14)</span>
                <span class="val" id="l-rsi">—</span>
            </div>
        </div>
    </div>

    <script src="https://unpkg.com/lightweight-charts@4.1/dist/lightweight-charts.standalone.production.js"></script>
    <script>
    (function() {{
        const candleData = {json.dumps(candles)};
        const volumeData = {json.dumps(volumes)};
        const sma20Data  = {json.dumps(sma20)};
        const sma50Data  = {json.dumps(sma50)};
        const rsiData    = {json.dumps(rsi_data)};
        const chartType  = "{chart_type}";
        const hasVolume  = {"true" if has_volume else "false"};

        // ── Main Chart ──────────────────────────────────────────────
        const mainEl = document.getElementById('main-container');
        const mainChart = LightweightCharts.createChart(mainEl, {{
            width: mainEl.clientWidth,
            height: mainEl.clientHeight,
            layout: {{
                background: {{ type: 'solid', color: '#131722' }},
                textColor: '#787b86',
                fontFamily: "'Inter', -apple-system, sans-serif",
                fontSize: 11,
            }},
            grid: {{
                vertLines: {{ color: '#1e222d' }},
                horzLines: {{ color: '#1e222d' }},
            }},
            crosshair: {{
                mode: LightweightCharts.CrosshairMode.Normal,
                vertLine: {{
                    color: '#758696',
                    width: 1,
                    style: LightweightCharts.LineStyle.Dashed,
                    labelBackgroundColor: '#2a2e39',
                }},
                horzLine: {{
                    color: '#758696',
                    width: 1,
                    style: LightweightCharts.LineStyle.Dashed,
                    labelBackgroundColor: '#2a2e39',
                }},
            }},
            rightPriceScale: {{
                borderColor: '#2a2e39',
                scaleMargins: {{ top: 0.1, bottom: hasVolume ? 0.25 : 0.1 }},
            }},
            timeScale: {{
                borderColor: '#2a2e39',
                timeVisible: true,
                secondsVisible: false,
                rightOffset: 5,
                barSpacing: 8,
                minBarSpacing: 2,
            }},
            handleScroll: {{ vertTouchDrag: false }},
        }});

        // Price series
        let priceSeries;
        if (chartType === "Candlestick") {{
            priceSeries = mainChart.addCandlestickSeries({{
                upColor: '#26a69a',
                downColor: '#ef5350',
                borderUpColor: '#26a69a',
                borderDownColor: '#ef5350',
                wickUpColor: '#26a69a',
                wickDownColor: '#ef5350',
            }});
            priceSeries.setData(candleData);
        }} else {{
            priceSeries = mainChart.addAreaSeries({{
                lineColor: '#2962ff',
                lineWidth: 2,
                topColor: 'rgba(41,98,255,0.28)',
                bottomColor: 'rgba(41,98,255,0.02)',
                crosshairMarkerRadius: 4,
                crosshairMarkerBorderColor: '#2962ff',
                crosshairMarkerBackgroundColor: '#131722',
            }});
            const lineData = candleData.map(d => ({{ time: d.time, value: d.close }}));
            priceSeries.setData(lineData);
        }}

        // Volume
        let volSeries = null;
        if (hasVolume) {{
            volSeries = mainChart.addHistogramSeries({{
                priceFormat: {{ type: 'volume' }},
                priceScaleId: 'vol',
            }});
            mainChart.priceScale('vol').applyOptions({{
                scaleMargins: {{ top: 0.82, bottom: 0 }},
            }});
            volSeries.setData(volumeData);
        }}

        // SMA 20
        const sma20Series = mainChart.addLineSeries({{
            color: '#e9963e',
            lineWidth: 1,
            lineStyle: LightweightCharts.LineStyle.Solid,
            crosshairMarkerVisible: false,
            priceLineVisible: false,
            lastValueVisible: false,
        }});
        sma20Series.setData(sma20Data);

        // SMA 50
        const sma50Series = mainChart.addLineSeries({{
            color: '#7b61ff',
            lineWidth: 1,
            lineStyle: LightweightCharts.LineStyle.Solid,
            crosshairMarkerVisible: false,
            priceLineVisible: false,
            lastValueVisible: false,
        }});
        sma50Series.setData(sma50Data);

        // ── RSI Chart ───────────────────────────────────────────────
        const rsiEl = document.getElementById('rsi-container');
        const rsiChart = LightweightCharts.createChart(rsiEl, {{
            width: rsiEl.clientWidth,
            height: 120,
            layout: {{
                background: {{ type: 'solid', color: '#131722' }},
                textColor: '#787b86',
                fontFamily: "'Inter', -apple-system, sans-serif",
                fontSize: 10,
            }},
            grid: {{
                vertLines: {{ color: '#1e222d' }},
                horzLines: {{ color: '#1e222d' }},
            }},
            crosshair: {{
                mode: LightweightCharts.CrosshairMode.Normal,
                vertLine: {{
                    color: '#758696', width: 1,
                    style: LightweightCharts.LineStyle.Dashed,
                    labelBackgroundColor: '#2a2e39',
                }},
                horzLine: {{
                    color: '#758696', width: 1,
                    style: LightweightCharts.LineStyle.Dashed,
                    labelBackgroundColor: '#2a2e39',
                }},
            }},
            rightPriceScale: {{
                borderColor: '#2a2e39',
                scaleMargins: {{ top: 0.1, bottom: 0.05 }},
            }},
            timeScale: {{
                borderColor: '#2a2e39',
                timeVisible: true,
                visible: true,
                rightOffset: 5,
                barSpacing: 8,
                minBarSpacing: 2,
            }},
            handleScroll: {{ vertTouchDrag: false }},
        }});

        const rsiSeries = rsiChart.addLineSeries({{
            color: '#7b61ff',
            lineWidth: 1.5,
            priceLineVisible: false,
            lastValueVisible: false,
            crosshairMarkerRadius: 3,
        }});
        rsiSeries.setData(rsiData);

        // Overbought / Oversold lines
        const ob = rsiChart.addLineSeries({{
            color: 'rgba(239,83,80,0.4)', lineWidth: 1,
            lineStyle: LightweightCharts.LineStyle.Dashed,
            priceLineVisible: false, lastValueVisible: false,
            crosshairMarkerVisible: false,
        }});
        ob.setData(rsiData.map(d => ({{ time: d.time, value: 70 }})));

        const os_ = rsiChart.addLineSeries({{
            color: 'rgba(38,166,154,0.4)', lineWidth: 1,
            lineStyle: LightweightCharts.LineStyle.Dashed,
            priceLineVisible: false, lastValueVisible: false,
            crosshairMarkerVisible: false,
        }});
        os_.setData(rsiData.map(d => ({{ time: d.time, value: 30 }})));

        // Middle line (50)
        const mid = rsiChart.addLineSeries({{
            color: 'rgba(120,123,134,0.2)', lineWidth: 1,
            lineStyle: LightweightCharts.LineStyle.Dotted,
            priceLineVisible: false, lastValueVisible: false,
            crosshairMarkerVisible: false,
        }});
        mid.setData(rsiData.map(d => ({{ time: d.time, value: 50 }})));

        // ── Synchronize Charts ──────────────────────────────────────
        let isSyncing = false;

        mainChart.timeScale().subscribeVisibleLogicalRangeChange(range => {{
            if (isSyncing) return;
            isSyncing = true;
            rsiChart.timeScale().setVisibleLogicalRange(range);
            isSyncing = false;
        }});

        rsiChart.timeScale().subscribeVisibleLogicalRangeChange(range => {{
            if (isSyncing) return;
            isSyncing = true;
            mainChart.timeScale().setVisibleLogicalRange(range);
            isSyncing = false;
        }});

        // Sync crosshair
        mainChart.subscribeCrosshairMove(param => {{
            if (param.time) {{
                const rsiVal = param.seriesData && param.seriesData.get ? null : null;
                // Find matching RSI point
                const rp = rsiData.find(d => d.time === param.time);
                if (rp) rsiChart.setCrosshairPosition(rp.value, param.time, rsiSeries);
            }} else {{
                rsiChart.clearCrosshairPosition();
            }}
        }});

        rsiChart.subscribeCrosshairMove(param => {{
            if (param.time) {{
                const cp = candleData.find(d => d.time === param.time);
                if (cp) mainChart.setCrosshairPosition(cp.close, param.time, priceSeries);
            }} else {{
                mainChart.clearCrosshairPosition();
            }}
            // Update RSI legend
            if (param.time && param.seriesData) {{
                const rd = param.seriesData.get(rsiSeries);
                if (rd) document.getElementById('l-rsi').textContent = rd.value.toFixed(1);
            }}
        }});

        // ── OHLC Legend Update ───────────────────────────────────────
        function fmt(v) {{ return v !== undefined && v !== null ? v.toFixed(2) : '—'; }}
        function fmtVol(v) {{
            if (!v) return '—';
            if (v >= 1e9) return (v/1e9).toFixed(2) + 'B';
            if (v >= 1e6) return (v/1e6).toFixed(2) + 'M';
            if (v >= 1e3) return (v/1e3).toFixed(1) + 'K';
            return v.toFixed(0);
        }}

        function updateLegend(param) {{
            const lO = document.getElementById('l-o');
            const lH = document.getElementById('l-h');
            const lL = document.getElementById('l-l');
            const lC = document.getElementById('l-c');
            const lV = document.getElementById('l-v');
            const lS20 = document.getElementById('l-sma20');
            const lS50 = document.getElementById('l-sma50');
            const lRsi = document.getElementById('l-rsi');

            if (!param.time || !param.seriesData) {{
                // Reset to last values
                const last = candleData[candleData.length - 1];
                if (last) {{
                    lO.textContent = fmt(last.open);
                    lH.textContent = fmt(last.high);
                    lL.textContent = fmt(last.low);
                    lC.textContent = fmt(last.close);
                    const cls = last.close >= last.open ? 'up' : 'dn';
                    [lO, lH, lL, lC].forEach(el => el.className = 'val ' + cls);
                }}
                return;
            }}

            const d = param.seriesData.get(priceSeries);
            if (d) {{
                const isCandle = d.open !== undefined;
                const o = isCandle ? d.open : d.value;
                const h = isCandle ? d.high : d.value;
                const l = isCandle ? d.low  : d.value;
                const c = isCandle ? d.close : d.value;
                const cls = c >= o ? 'up' : 'dn';

                lO.textContent = fmt(o);
                lH.textContent = fmt(h);
                lL.textContent = fmt(l);
                lC.textContent = fmt(c);
                [lO, lH, lL, lC].forEach(el => el.className = 'val ' + cls);
            }}

            if (volSeries) {{
                const vd = param.seriesData.get(volSeries);
                if (vd) lV.textContent = fmtVol(vd.value);
            }}

            const s20 = param.seriesData.get(sma20Series);
            if (s20) lS20.textContent = fmt(s20.value);

            const s50 = param.seriesData.get(sma50Series);
            if (s50) lS50.textContent = fmt(s50.value);
        }}

        mainChart.subscribeCrosshairMove(updateLegend);

        // Set initial legend
        if (candleData.length) {{
            const last = candleData[candleData.length - 1];
            const cls = last.close >= last.open ? 'up' : 'dn';
            document.getElementById('l-o').textContent = fmt(last.open);
            document.getElementById('l-h').textContent = fmt(last.high);
            document.getElementById('l-l').textContent = fmt(last.low);
            document.getElementById('l-c').textContent = fmt(last.close);
            ['l-o','l-h','l-l','l-c'].forEach(id => document.getElementById(id).className = 'val ' + cls);
        }}
        if (volumeData.length) {{
            document.getElementById('l-v').textContent = fmtVol(volumeData[volumeData.length-1].value);
        }}
        if (rsiData.length) {{
            document.getElementById('l-rsi').textContent = rsiData[rsiData.length-1].value.toFixed(1);
        }}
        if (sma20Data.length) {{
            document.getElementById('l-sma20').textContent = fmt(sma20Data[sma20Data.length-1].value);
        }}
        if (sma50Data.length) {{
            document.getElementById('l-sma50').textContent = fmt(sma50Data[sma50Data.length-1].value);
        }}

        // ── Resize ──────────────────────────────────────────────────
        const ro = new ResizeObserver(() => {{
            mainChart.applyOptions({{ width: mainEl.clientWidth }});
            rsiChart.applyOptions({{ width: rsiEl.clientWidth }});
        }});
        ro.observe(mainEl);

        // Fit content
        mainChart.timeScale().fitContent();
        rsiChart.timeScale().fitContent();
    }})();
    </script>
    </body>
    </html>
    """
    components.html(html, height=620, scrolling=False)


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

st.sidebar.markdown(
    "<div style='padding:4px 0 8px 0;'>"
    "<span style='font-size:1.2rem; font-weight:800; "
    "background:linear-gradient(135deg,#2962ff,#7b61ff); "
    "-webkit-background-clip:text; -webkit-text-fill-color:transparent;'>"
    "⚡ StockPulse</span>"
    "<br><span style='color:#787b86; font-size:0.7rem;'>AI-Powered Market Tracker</span>"
    "</div>",
    unsafe_allow_html=True,
)
st.sidebar.markdown("---")

# Asset class
asset_class = st.sidebar.selectbox(
    "Asset Class",
    ["US Stocks", "Indian Stocks (NSE)", "Commodities", "Forex Pairs", "Custom"],
)

ticker = "AAPL"

if asset_class == "US Stocks":
    opts = {
        "AAPL — Apple": "AAPL", "MSFT — Microsoft": "MSFT",
        "GOOGL — Alphabet": "GOOGL", "AMZN — Amazon": "AMZN",
        "TSLA — Tesla": "TSLA", "NVDA — NVIDIA": "NVDA",
        "META — Meta": "META", "NFLX — Netflix": "NFLX",
        "AMD — AMD": "AMD", "JPM — JPMorgan": "JPM",
    }
    ticker = opts[st.sidebar.selectbox("Symbol", list(opts.keys()))]

elif asset_class == "Indian Stocks (NSE)":
    opts = {
        "RELIANCE.NS — Reliance": "RELIANCE.NS",
        "TCS.NS — TCS": "TCS.NS",
        "HDFCBANK.NS — HDFC Bank": "HDFCBANK.NS",
        "INFY.NS — Infosys": "INFY.NS",
        "ICICIBANK.NS — ICICI Bank": "ICICIBANK.NS",
        "SBIN.NS — SBI": "SBIN.NS",
        "WIPRO.NS — Wipro": "WIPRO.NS",
        "TATAMOTORS.NS — Tata Motors": "TATAMOTORS.NS",
        "BHARTIARTL.NS — Bharti Airtel": "BHARTIARTL.NS",
        "LT.NS — L&T": "LT.NS",
        "ADANIENT.NS — Adani Enterprises": "ADANIENT.NS",
        "ITC.NS — ITC": "ITC.NS",
    }
    ticker = opts[st.sidebar.selectbox("Symbol", list(opts.keys()))]

elif asset_class == "Commodities":
    opts = {
        "GC=F — Gold": "GC=F", "SI=F — Silver": "SI=F",
        "CL=F — Crude Oil": "CL=F", "NG=F — Natural Gas": "NG=F",
        "HG=F — Copper": "HG=F", "PL=F — Platinum": "PL=F",
    }
    ticker = opts[st.sidebar.selectbox("Symbol", list(opts.keys()))]

elif asset_class == "Forex Pairs":
    opts = {
        "EURUSD=X — EUR/USD": "EURUSD=X", "GBPUSD=X — GBP/USD": "GBPUSD=X",
        "USDJPY=X — USD/JPY": "USDJPY=X", "USDINR=X — USD/INR": "USDINR=X",
        "AUDUSD=X — AUD/USD": "AUDUSD=X", "USDCAD=X — USD/CAD": "USDCAD=X",
    }
    ticker = opts[st.sidebar.selectbox("Symbol", list(opts.keys()))]

else:
    ticker = st.sidebar.text_input("Ticker (e.g. BTC-USD)", value="AAPL").upper().strip()

st.sidebar.markdown("---")
st.sidebar.markdown("<p style='color:#787b86;font-size:0.65rem;font-weight:600;"
                    "text-transform:uppercase;letter-spacing:0.08em;'>🔔 Price Alerts</p>",
                    unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN AREA
# ══════════════════════════════════════════════════════════════════════════════

if ticker:
    # ── Determine period/interval ────────────────────────────────────────
    if st.session_state.custom_range:
        period = None
        interval = st.session_state.get("custom_interval", "1d")
        start = st.session_state.get("custom_start")
        end = st.session_state.get("custom_end")
    else:
        tf = st.session_state.timeframe
        period, interval = TIMEFRAMES.get(tf, ("6mo", "1d"))
        start, end = None, None

    # ── Fetch data ───────────────────────────────────────────────────────
    if start and end:
        df = get_stock_data(ticker, interval=interval,
                            start=start.strftime("%Y-%m-%d"),
                            end=end.strftime("%Y-%m-%d"))
    else:
        df = get_stock_data(ticker, period=period, interval=interval)

    if df.empty:
        st.markdown(
            "<div style='text-align:center;padding:100px 0;'>"
            "<p style='font-size:3rem;'>📭</p>"
            f"<p style='color:#787b86;'>No data found for <strong style='color:#d1d4dc;'>"
            f"{ticker}</strong>. Check the symbol and try again.</p></div>",
            unsafe_allow_html=True,
        )
    else:
        df["SMA_20"] = calculate_sma(df, window=20)
        df["SMA_50"] = calculate_sma(df, window=50)
        df["RSI"] = calculate_rsi(df)

        latest_price = float(df["Close"].iloc[-1])
        prev_price = float(df["Close"].iloc[-2]) if len(df) > 1 else latest_price
        price_change = latest_price - prev_price
        pct_change = (price_change / prev_price) * 100 if prev_price else 0
        is_up = price_change >= 0
        cls = "tv-up" if is_up else "tv-down"
        arrow = "▲" if is_up else "▼"
        latest_rsi = float(df["RSI"].iloc[-1])
        day_high = float(df["High"].iloc[-1])
        day_low = float(df["Low"].iloc[-1])
        volume = int(df["Volume"].iloc[-1]) if "Volume" in df.columns else 0

        # ── Alert form (sidebar) ─────────────────────────────────────
        with st.sidebar.form("alert_form"):
            st.markdown(f"<p style='color:#d1d4dc;font-size:0.85rem;font-weight:600;'>"
                        f"{ticker} · ${latest_price:,.2f}</p>", unsafe_allow_html=True)
            threshold = st.number_input("Threshold ($)", value=latest_price, step=1.0)
            direction = st.selectbox("Direction", ["above", "below"])
            email = st.text_input("Email")
            if st.form_submit_button("⚡ Set Alert"):
                if not email.strip():
                    st.error("Enter a valid email.")
                else:
                    add_alert(ticker, threshold, direction, email)
                    st.success(f"Alert: {ticker} {direction} ${threshold:,.2f}")

        # ── Ticker Header ────────────────────────────────────────────
        st.markdown(
            f"""<div class="tv-header">
                <span class="tv-symbol">{ticker}</span>
                <span class="tv-exchange">{asset_class}</span>
                <span class="tv-price {cls}">${latest_price:,.2f}</span>
                <span class="tv-change {cls}">
                    {arrow} {abs(price_change):,.2f} ({abs(pct_change):.2f}%)
                </span>
            </div>""",
            unsafe_allow_html=True,
        )

        # ── Timeframe Toolbar ────────────────────────────────────────
        tf_labels = list(TIMEFRAMES.keys()) + ["Custom", "─", "🕯", "📈"]
        cols = st.columns(len(tf_labels))
        for i, label in enumerate(tf_labels):
            with cols[i]:
                if label == "─":
                    st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                elif label == "🕯":
                    if st.button("🕯️", key="btn_candle", use_container_width=True):
                        st.session_state.chart_type = "Candlestick"
                        st.rerun()
                elif label == "📈":
                    if st.button("📈", key="btn_line", use_container_width=True):
                        st.session_state.chart_type = "Line"
                        st.rerun()
                elif label == "Custom":
                    if st.button("Custom", key="btn_custom", use_container_width=True):
                        st.session_state.custom_range = not st.session_state.custom_range
                        st.rerun()
                else:
                    if st.button(label, key=f"btn_{label}", use_container_width=True):
                        st.session_state.timeframe = label
                        st.session_state.custom_range = False
                        st.rerun()

        # Custom date range inputs
        if st.session_state.custom_range:
            c1, c2, c3, c4 = st.columns([1, 1, 1, 0.5])
            today = datetime.date.today()
            with c1:
                st.session_state.custom_start = st.date_input(
                    "Start", value=today - datetime.timedelta(days=365))
            with c2:
                st.session_state.custom_end = st.date_input("End", value=today)
            with c3:
                st.session_state.custom_interval = st.selectbox(
                    "Interval", ["1m", "5m", "15m", "1h", "1d", "1wk", "1mo"], index=4)
            with c4:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Apply", use_container_width=True):
                    st.rerun()

        # ── Render Chart ─────────────────────────────────────────────
        render_tv_chart(df, ticker, st.session_state.chart_type)

        # ── Metric Cards ─────────────────────────────────────────────
        def fmt_vol(v):
            if v >= 1e9: return f"{v/1e9:.2f}B"
            if v >= 1e6: return f"{v/1e6:.2f}M"
            if v >= 1e3: return f"{v/1e3:.1f}K"
            return str(v) if v > 0 else "N/A"

        rsi_color = "#ef5350" if latest_rsi > 70 else ("#26a69a" if latest_rsi < 30 else "#787b86")
        rsi_label = "Overbought" if latest_rsi > 70 else ("Oversold" if latest_rsi < 30 else "Neutral")
        delta_color = "#26a69a" if is_up else "#ef5350"

        st.markdown(
            f"""
            <div class="mc-row">
                <div class="mc">
                    <div class="mc-label">Close</div>
                    <div class="mc-val">${latest_price:,.2f}</div>
                    <div class="mc-delta" style="color:{delta_color};">
                        {arrow} ${abs(price_change):,.2f} ({abs(pct_change):.2f}%)
                    </div>
                </div>
                <div class="mc">
                    <div class="mc-label">High</div>
                    <div class="mc-val">${day_high:,.2f}</div>
                </div>
                <div class="mc">
                    <div class="mc-label">Low</div>
                    <div class="mc-val">${day_low:,.2f}</div>
                </div>
                <div class="mc">
                    <div class="mc-label">Volume</div>
                    <div class="mc-val">{fmt_vol(volume)}</div>
                </div>
                <div class="mc">
                    <div class="mc-label">RSI (14)</div>
                    <div class="mc-val" style="color:{rsi_color};">{latest_rsi:.1f}</div>
                    <div class="mc-delta" style="color:{rsi_color};">{rsi_label}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # RSI Gauge
        rsi_pct = max(0, min(100, latest_rsi))
        st.markdown(
            f"""
            <div style="margin-top:10px; background:#1e222d; border:1px solid #2a2e39;
                        border-radius:8px; padding:12px 16px;">
                <div style="display:flex; justify-content:space-between;">
                    <span class="mc-label" style="margin:0;">RSI Gauge</span>
                    <span style="color:{rsi_color}; font-weight:700; font-size:0.85rem;">{latest_rsi:.1f}</span>
                </div>
                <div class="rsi-gauge-bar">
                    <div class="rsi-dot" style="left:{rsi_pct}%;"></div>
                </div>
                <div class="rsi-ticks">
                    <span>Oversold</span><span>30</span><span>50</span><span>70</span><span>Overbought</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Active Alerts ────────────────────────────────────────────
        st.markdown('<div class="sec-label">🔔 Active Alerts</div>', unsafe_allow_html=True)
        alerts = get_alerts()
        active = [a for a in alerts if not a["triggered"]]
        if active:
            rows = ""
            for a in active:
                rows += (f"<tr><td><strong>{a['ticker']}</strong></td>"
                         f"<td>${a['threshold_price']:,.2f}</td>"
                         f"<td><span class='badge {a['direction']}'>{a['direction'].upper()}</span></td>"
                         f"<td>{a['email']}</td></tr>")
            st.markdown(
                f"<table class='at'><thead><tr><th>Ticker</th><th>Threshold</th>"
                f"<th>Direction</th><th>Email</th></tr></thead><tbody>{rows}</tbody></table>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div style='text-align:center;padding:24px;color:#787b86;font-size:0.85rem;"
                "background:#1e222d;border:1px solid #2a2e39;border-radius:8px;'>"
                "No active alerts. Use the sidebar to set one.</div>",
                unsafe_allow_html=True,
            )
