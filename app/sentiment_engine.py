"""Sentiment analysis engine powered by Google Gemini.

Fetches recent news headlines for a stock ticker via yfinance and
sends them to the Gemini generative-AI model for summarisation and
overall sentiment classification (Bullish / Bearish / Neutral).
"""

import json
import os
import sys

import google.generativeai as genai
import streamlit as st
import yfinance as yf
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Allow imports from the project root when running this file standalone
# (e.g.  python app/sentiment_engine.py).
# ---------------------------------------------------------------------------
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---------------------------------------------------------------------------
# Load environment variables and configure the Gemini client.
# ---------------------------------------------------------------------------
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "config", ".env"))

GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")

# Maximum number of headlines to feed into the prompt.
MAX_HEADLINES: int = 10


def get_news_headlines(ticker: str) -> list[str]:
    """Fetch recent news headlines for a stock ticker using yfinance.

    Args:
        ticker: The stock ticker symbol (e.g., ``"AAPL"``).

    Returns:
        A list of up to ``MAX_HEADLINES`` headline strings.  Returns an
        empty list if no news is available or if fetching fails.
    """
    try:
        stock = yf.Ticker(ticker)
        news_items: list[dict] = stock.news or []
        headlines: list[str] = [
            item["title"]
            for item in news_items
            if "title" in item
        ]
        return headlines[:MAX_HEADLINES]
    except Exception as e:
        print(f"WARNING: Could not fetch news for {ticker}. Error: {e}")
        return []


@st.cache_data(ttl=600)
def analyze_sentiment(ticker: str) -> dict:
    """Analyse the sentiment of recent news for a given ticker.

    Retrieves headlines via :func:`get_news_headlines`, builds a prompt
    asking the Gemini model for a 3-4 sentence summary and an overall
    sentiment label, then parses the JSON response.

    Args:
        ticker: The stock ticker symbol (e.g., ``"AAPL"``).

    Returns:
        A dict with two keys:

        - ``"summary"`` – A short natural-language summary of the news.
        - ``"sentiment"`` – One of ``"Bullish"``, ``"Bearish"``, or
          ``"Neutral"``.

        If anything goes wrong a safe fallback dict is returned.
    """
    fallback: dict = {
        "summary": "Unable to analyse sentiment at this time.",
        "sentiment": "Neutral",
    }

    headlines = get_news_headlines(ticker)

    if not headlines:
        return {"summary": "No news available", "sentiment": "Neutral"}

    numbered_headlines = "\n".join(
        f"{i}. {headline}" for i, headline in enumerate(headlines, start=1)
    )

    prompt = (
        f"You are a professional financial analyst.\n\n"
        f"Below are the latest news headlines for the stock ticker "
        f"**{ticker}**:\n\n"
        f"{numbered_headlines}\n\n"
        f"Based on these headlines:\n"
        f"1. Summarise the overall news in 3-4 concise sentences.\n"
        f"2. Assign an overall sentiment label: Bullish, Bearish, or "
        f"Neutral.\n\n"
        f"Respond ONLY with valid JSON in this exact format — no "
        f"markdown, no extra text:\n"
        f'{{"summary": "...", "sentiment": "Bullish/Bearish/Neutral"}}'
    )

    try:
        response = model.generate_content(prompt)
        raw_text: str = response.text.strip()

        # Strip markdown code fences if the model wraps the JSON.
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1]
        if raw_text.endswith("```"):
            raw_text = raw_text.rsplit("```", 1)[0].strip()

        result: dict = json.loads(raw_text)

        # Validate expected keys are present.
        if "summary" not in result or "sentiment" not in result:
            print("WARNING: Gemini response missing expected keys.")
            return fallback

        return result

    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse Gemini response as JSON. {e}")
        return fallback
    except Exception as e:
        print(f"ERROR: Sentiment analysis failed for {ticker}. {e}")
        return fallback


if __name__ == "__main__":
    result = analyze_sentiment("AAPL")
    print(f"\n--- Sentiment Analysis for AAPL ---")
    print(f"  Summary:   {result['summary']}")
    print(f"  Sentiment: {result['sentiment']}")
