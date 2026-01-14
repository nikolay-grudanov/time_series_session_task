"""
Validation utilities for inputs.
"""
import re


def validate_ticker(ticker: str) -> bool:
    """
    Validates ticker symbol based on stock exchange format.
    Typically 1-5 uppercase letters and dots for special cases (e.g., BRK.B).
    """
    if not ticker or not isinstance(ticker, str):
        return False

    # Allow 1-5 uppercase letters, and dots for special cases like BRK.B
    pattern = r'^[A-Z]{1,5}(\.[A-Z]{1,2})?$'
    return bool(re.match(pattern, ticker.strip()))


def validate_investment_amount(amount: float | str) -> tuple[bool, str]:
    """
    Validates investment amount is within acceptable range ($1 to $1,000,000).
    Returns (is_valid, error_message).
    """
    try:
        amount = float(amount)
        if amount < 1:
            return False, f"Investment amount must be at least $1, got ${amount}"
        elif amount > 1_000_000:
            return False, f"Investment amount must not exceed $1,000,000, got ${amount}"
        return True, ""
    except (ValueError, TypeError):
        return False, f"Invalid investment amount format: {amount}"


def validate_stock_volatility(daily_returns) -> bool:
    """
    Validates if stock is extremely volatile (>5% daily variance).
    Expects a pandas Series of daily returns.
    """
    if len(daily_returns) == 0:
        return False

    daily_variance = daily_returns.std()
    return daily_variance > 0.05  # 5% threshold
