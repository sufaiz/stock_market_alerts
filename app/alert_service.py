"""Email alert service for stock price notifications.

Provides email sending, alert checking against live prices, and a
background loop that periodically monitors all active alerts.
"""

import os
import sys
import smtplib
import time
import threading
from datetime import datetime
from email.mime.text import MIMEText

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Allow imports from the project root when running this file standalone
# (e.g.  python app/alert_service.py).
# ---------------------------------------------------------------------------
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "config", ".env"))

# Interval (in seconds) between consecutive alert checks.
CHECK_INTERVAL: int = 300


def send_email_alert(
    to_email: str,
    ticker: str,
    price: float,
    direction: str,
) -> None:
    """Send an email alert when a stock price crosses a threshold.

    Loads sender credentials from the EMAIL_ADDRESS and
    EMAIL_APP_PASSWORD environment variables and sends the message
    via Gmail's SMTP-SSL server.

    Args:
        to_email: The recipient's email address.
        ticker: The stock ticker symbol (e.g., "AAPL").
        price: The current stock price that triggered the alert.
        direction: Either "above" or "below", indicating how the
            threshold was crossed.
    """
    sender_email = os.getenv("EMAIL_ADDRESS")
    sender_password = os.getenv("EMAIL_APP_PASSWORD")

    if not sender_email or not sender_password:
        print(
            "ERROR: EMAIL_ADDRESS and EMAIL_APP_PASSWORD must be set "
            "in the .env file."
        )
        return

    subject = f"Stock Alert: {ticker} crossed {direction} threshold"
    body = (
        f"Stock Alert\n"
        f"{'=' * 40}\n\n"
        f"Ticker:    {ticker}\n"
        f"Price:     ${price:,.2f}\n"
        f"Direction: The price has crossed {direction} your set threshold.\n\n"
        f"Please review your portfolio and take any necessary action."
    )

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())
        print(f"SUCCESS: Alert email sent to {to_email} for {ticker}.")
    except Exception as e:
        print(f"FAILURE: Could not send email to {to_email}. Error: {e}")


def check_alerts() -> None:
    """Check every un-triggered alert against the current live price.

    For each alert where ``triggered == 0``:
    - Fetches the current price via :func:`app.data_handler.get_stock_info`.
    - If the direction is ``"above"`` and the current price exceeds the
      threshold, sends an email and marks the alert as triggered.
    - If the direction is ``"below"`` and the current price is under the
      threshold, sends an email and marks the alert as triggered.
    """
    from database.db_manager import get_alerts, mark_triggered
    from app.data_handler import get_stock_info

    print(f"Checking alerts at {datetime.now()}")

    alerts = get_alerts()

    for alert in alerts:
        if alert["triggered"]:
            continue

        ticker: str = alert["ticker"]
        threshold: float = alert["threshold_price"]
        direction: str = alert["direction"]
        email: str = alert["email"]
        alert_id: int = alert["id"]

        try:
            info = get_stock_info(ticker)
            current_price: float | None = info.get("currentPrice")

            if current_price is None:
                print(
                    f"  WARNING: Could not fetch price for {ticker}. "
                    "Skipping."
                )
                continue

            triggered = False

            if direction == "above" and current_price > threshold:
                triggered = True
            elif direction == "below" and current_price < threshold:
                triggered = True

            if triggered:
                print(
                    f"  TRIGGERED: {ticker} is ${current_price:,.2f} "
                    f"({direction} ${threshold:,.2f}). Sending alert."
                )
                send_email_alert(email, ticker, current_price, direction)
                mark_triggered(alert_id)
            else:
                print(
                    f"  OK: {ticker} at ${current_price:,.2f} — "
                    f"threshold ${threshold:,.2f} ({direction}) not met."
                )
        except Exception as e:
            print(f"  ERROR checking {ticker}: {e}")


def start_alert_loop() -> None:
    """Start a repeating background loop that checks alerts every 5 minutes.

    Uses :class:`threading.Timer` to schedule :func:`check_alerts`
    every ``CHECK_INTERVAL`` seconds.  The timer thread is set as a
    daemon so it will not prevent the main process (e.g. Streamlit)
    from exiting.
    """

    def _loop() -> None:
        """Run one check and schedule the next iteration."""
        check_alerts()
        timer = threading.Timer(CHECK_INTERVAL, _loop)
        timer.daemon = True
        timer.start()

    # Kick off the first check immediately.
    timer = threading.Timer(0, _loop)
    timer.daemon = True
    timer.start()
    print(
        f"Alert loop started — checking every {CHECK_INTERVAL} seconds."
    )


if __name__ == "__main__":
    start_alert_loop()
    # Keep the main thread alive so the daemon timer keeps running.
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nAlert loop stopped.")
