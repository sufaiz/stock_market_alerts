# AI-Powered Stock Tracker & Alert Engine

A real-time stock market dashboard built with Python and Streamlit that tracks live stock prices across US equities, Indian stocks, commodities, and forex pairs. It displays interactive candlestick charts with SMA overlays, an RSI gauge with overbought/oversold zones, and lets you set price alerts that are monitored in the background. When a threshold is crossed, you get an email notification automatically. The app also integrates Google Gemini AI to pull recent news headlines and summarize overall market sentiment as Bullish, Bearish, or Neutral.

## Features

- **Live stock data** via the yfinance API — supports US stocks, Indian NSE stocks, commodities, and forex pairs
- **Interactive Plotly charts** with candlestick/line views and SMA 20 / SMA 50 overlays
- **RSI gauge** with color-coded overbought (red), oversold (green), and neutral (gray) zones
- **SQLite-backed alert registration** — set price alerts that persist across sessions
- **Automated email alerts** via Gmail SMTP — background thread checks prices every 5 minutes
- **AI-powered news sentiment analysis** — Google Gemini summarizes recent headlines and assigns a sentiment label
- **Streamlit caching** — data and API responses are cached to keep the dashboard snappy

## Tech Stack

| Component      | Technology                          |
| -------------- | ----------------------------------- |
| Frontend       | Streamlit                           |
| Data API       | yfinance                            |
| Indicators     | pandas / numpy (SMA, RSI)           |
| Charts         | Plotly (graph_objects)               |
| AI / LLM       | Google Gemini (`gemini-2.5-flash`)   |
| Database       | SQLite via Python `sqlite3`         |
| Email          | `smtplib` (Gmail SMTP-SSL)          |

## Project Structure

```
stock_market_alerts/
├── app/
│   ├── __init__.py            # Package marker
│   ├── main.py                # Streamlit dashboard entry point
│   ├── data_handler.py        # Fetches stock data & info via yfinance
│   ├── indicators.py          # SMA and RSI calculations
│   ├── alert_service.py       # Email alerts + background check loop
│   └── sentiment_engine.py    # Gemini-powered news sentiment analysis
├── database/
│   ├── __init__.py            # Package marker
│   └── db_manager.py          # SQLite CRUD for alerts table
├── config/
│   └── .env.example           # Template for environment variables
├── tests/
│   └── test_indicators.py     # Unit tests for SMA and RSI
├── requirements.txt           # Python dependencies
├── run.py                     # Convenience launcher script
├── .gitignore                 # Ignores venv, .env, __pycache__, *.db
└── README.md                  # This file
```

## Setup Instructions

1. **Clone the repository**

   ```bash
   git clone https://github.com/sufaiz/stock_market_alerts.git
   cd stock_market_alerts
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**

   - **Windows:**
     ```bash
     venv\Scripts\activate
     ```
   - **Mac / Linux:**
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

5. **Configure environment variables**

   ```bash
   cp config/.env.example config/.env
   ```

   Open `config/.env` and fill in your credentials:

   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   EMAIL_ADDRESS=your_gmail_address@gmail.com
   EMAIL_APP_PASSWORD=your_gmail_app_password_here
   ```

## How to Run

Start the dashboard with:

```bash
streamlit run app/main.py
```

The app will open in your browser at [http://localhost:8501](http://localhost:8501). Select an asset class from the sidebar, pick a ticker, and explore the charts, indicators, alerts, and sentiment analysis.

You can also use the convenience launcher:

```bash
python run.py
```

## How Alerts Work

Use the alert form on the dashboard to set a price threshold for any ticker. Enter the target price, choose whether to trigger when the price goes **above** or **below** that level, and provide your email address. The alert is saved to a local SQLite database. A background daemon thread runs every 5 minutes, checking the current price of each active alert against its threshold. When a price crosses the threshold, the system sends you an email notification via Gmail SMTP and marks the alert as triggered so you only get notified once.

## Environment Variables

| Variable             | Description                                      | Where to get it                                                                                          |
| -------------------- | ------------------------------------------------ | -------------------------------------------------------------------------------------------------------- |
| `GEMINI_API_KEY`     | API key for Google Gemini (sentiment analysis)   | [Google AI Studio](https://aistudio.google.com/app/apikey)                                               |
| `EMAIL_ADDRESS`      | Gmail address used to send alert emails          | Your Gmail account                                                                                       |
| `EMAIL_APP_PASSWORD` | App-specific password for Gmail SMTP             | [Google Account → Security → App Passwords](https://myaccount.google.com/apppasswords) (requires 2FA)   |

## Running Tests

Run the test suite with:

```bash
pytest tests/
```

For verbose output:

```bash
pytest tests/ -v
```
