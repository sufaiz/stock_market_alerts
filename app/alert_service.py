"""Email alert service for stock price notifications."""

import os
import smtplib
from email.mime.text import MIMEText

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "config", ".env"))


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


if __name__ == "__main__":
    send_email_alert(
        to_email="test@example.com",
        ticker="AAPL",
        price=200.50,
        direction="above",
    )
