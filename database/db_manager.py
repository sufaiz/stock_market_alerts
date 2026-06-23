"""Database manager for stock price alerts using SQLite."""

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "stock_alerts.db")


def _get_connection() -> sqlite3.Connection:
    """Return a connection to the SQLite database.

    Uses sqlite3.Row as the row factory so that rows can be accessed
    by column name as well as by index.

    Returns:
        A sqlite3.Connection instance.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the database file and the alerts table if they don't exist.

    The alerts table stores user-defined price alerts with the following
    columns: id, ticker, threshold_price, direction, email, triggered.
    """
    conn = _get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                threshold_price REAL NOT NULL,
                direction TEXT NOT NULL,
                email TEXT NOT NULL,
                triggered INTEGER DEFAULT 0
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def add_alert(
    ticker: str,
    threshold_price: float,
    direction: str,
    email: str,
) -> None:
    """Insert a new alert into the alerts table.

    Args:
        ticker: The stock ticker symbol (e.g., "AAPL").
        threshold_price: The price threshold that triggers the alert.
        direction: Either "above" or "below", indicating whether the
            alert fires when the price crosses above or below the
            threshold.
        email: The email address to notify when the alert is triggered.
    """
    conn = _get_connection()
    try:
        conn.execute(
            """
            INSERT INTO alerts (ticker, threshold_price, direction, email)
            VALUES (?, ?, ?, ?)
            """,
            (ticker, threshold_price, direction, email),
        )
        conn.commit()
    finally:
        conn.close()


def get_alerts() -> list[sqlite3.Row]:
    """Retrieve all rows from the alerts table.

    Returns:
        A list of sqlite3.Row objects representing every alert in the
        database.
    """
    conn = _get_connection()
    try:
        cursor = conn.execute("SELECT * FROM alerts")
        return cursor.fetchall()
    finally:
        conn.close()


def mark_triggered(alert_id: int) -> None:
    """Mark an alert as triggered by setting its triggered column to 1.

    Args:
        alert_id: The primary-key id of the alert to update.
    """
    conn = _get_connection()
    try:
        conn.execute(
            "UPDATE alerts SET triggered = 1 WHERE id = ?",
            (alert_id,),
        )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print("Database initialised.")

    add_alert("AAPL", 200.0, "above", "test@example.com")
    print("Test alert added.")

    alerts = get_alerts()
    print(f"\n--- All Alerts ({len(alerts)}) ---")
    for alert in alerts:
        print(
            f"  id={alert['id']}  ticker={alert['ticker']}  "
            f"threshold={alert['threshold_price']}  "
            f"direction={alert['direction']}  "
            f"email={alert['email']}  "
            f"triggered={alert['triggered']}"
        )
