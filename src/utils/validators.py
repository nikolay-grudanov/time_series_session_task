"""
Validation utilities for inputs.
Provides enhanced validation with specific, actionable error messages.
"""

import re
from dataclasses import dataclass
from enum import Enum


class ValidationErrorType(Enum):
    """Types of validation errors."""

    EMPTY = "empty"
    INVALID_FORMAT = "invalid_format"
    OUT_OF_RANGE = "out_of_range"
    NON_NUMERIC = "non_numeric"
    TOO_LONG = "too_long"
    UNKNOWN = "unknown"


@dataclass
class ValidationResult:
    """Result of a validation check."""

    is_valid: bool
    error_type: ValidationErrorType | None
    error_message: str | None


class ValidationError(Exception):
    """Custom exception for validation errors."""

    def __init__(
        self,
        message: str,
        error_type: ValidationErrorType = ValidationErrorType.UNKNOWN,
    ) -> None:
        self.message = message
        self.error_type = error_type
        super().__init__(message)


def validate_ticker(ticker: str) -> ValidationResult:
    """
    Validates ticker symbol based on stock exchange format.

    Ticker format: 1-5 uppercase letters, optionally with dots for special cases
    (e.g., BRK.B, BRK.A).

    Returns:
        ValidationResult with success status and specific error message
    """
    if not ticker:
        return ValidationResult(
            is_valid=False,
            error_type=ValidationErrorType.EMPTY,
            error_message="Ticker symbol cannot be empty. Please enter a stock ticker (e.g., AAPL).",
        )

    if not isinstance(ticker, str):
        return ValidationResult(
            is_valid=False,
            error_type=ValidationErrorType.INVALID_FORMAT,
            error_message="Ticker must be text. Please enter a valid stock ticker.",
        )

    ticker_clean = ticker.strip().upper()

    # Allow 1-5 uppercase letters, and dots for special cases like BRK.B
    pattern = r"^[A-Z]{1,5}(\.[A-Z]{1,2})?$"

    if not re.match(pattern, ticker_clean):
        return ValidationResult(
            is_valid=False,
            error_type=ValidationErrorType.INVALID_FORMAT,
            error_message=(
                f"Invalid ticker format: '{ticker}'. "
                "Tickers must be 1-5 uppercase letters (e.g., AAPL, GOOGL, MSFT). "
                "Use format like BRK.B for certain stock classes."
            ),
        )

    return ValidationResult(is_valid=True, error_type=None, error_message=None)


def validate_investment_amount(amount: float | str) -> ValidationResult:
    """
    Validates investment amount is within acceptable range ($1 to $1,000,000).

    Args:
        amount: Investment amount as number or string

    Returns:
        ValidationResult with success status and specific error message
    """
    # Handle None
    if amount is None:
        return ValidationResult(
            is_valid=False,
            error_type=ValidationErrorType.EMPTY,
            error_message="Investment amount cannot be empty. Please enter an amount.",
        )

    # Handle string input
    if isinstance(amount, str):
        amount_clean = amount.strip()

        # Check if empty string
        if not amount_clean:
            return ValidationResult(
                is_valid=False,
                error_type=ValidationErrorType.EMPTY,
                error_message="Investment amount cannot be empty. Please enter an amount.",
            )

        # Try to convert to float
        try:
            amount_value = float(amount_clean.replace(",", ""))
        except ValueError:
            return ValidationResult(
                is_valid=False,
                error_type=ValidationErrorType.NON_NUMERIC,
                error_message=(
                    f"Invalid amount format: '{amount}'. "
                    "Please enter a numeric value (e.g., 1000 or 1,000.50)."
                ),
            )
    else:
        # Handle numeric input
        try:
            amount_value = float(amount)
        except (ValueError, TypeError):
            return ValidationResult(
                is_valid=False,
                error_type=ValidationErrorType.NON_NUMERIC,
                error_message=f"Invalid amount: {amount}. Please enter a numeric value.",
            )

    # Check minimum
    if amount_value < 1:
        return ValidationResult(
            is_valid=False,
            error_type=ValidationErrorType.OUT_OF_RANGE,
            error_message=(
                f"Investment amount must be at least $1. "
                f"You entered ${amount_value:.2f}."
            ),
        )

    # Check maximum
    if amount_value > 1_000_000:
        return ValidationResult(
            is_valid=False,
            error_type=ValidationErrorType.OUT_OF_RANGE,
            error_message=(
                f"Investment amount cannot exceed $1,000,000. "
                f"You entered ${amount_value:,.2f}."
            ),
        )

    return ValidationResult(is_valid=True, error_type=None, error_message=None)


def validate_forecast_request(ticker: str, amount: float | str) -> ValidationResult:
    """
    Validates a complete forecast request.

    Args:
        ticker: Stock ticker symbol
        amount: Investment amount

    Returns:
        ValidationResult with success status and specific error message
    """
    # Validate ticker first
    ticker_result = validate_ticker(ticker)
    if not ticker_result.is_valid:
        return ticker_result

    # Validate amount
    amount_result = validate_investment_amount(amount)
    if not amount_result.is_valid:
        return amount_result

    return ValidationResult(is_valid=True, error_type=None, error_message=None)


def validate_stock_volatility(daily_returns) -> ValidationResult:
    """
    Validates if stock is extremely volatile (>5% daily variance).

    Args:
        daily_returns: pandas Series of daily returns

    Returns:
        ValidationResult with volatility check result
    """
    if daily_returns is None or len(daily_returns) == 0:
        return ValidationResult(
            is_valid=False,
            error_type=ValidationErrorType.EMPTY,
            error_message="Cannot calculate volatility: no data available.",
        )

    daily_variance = daily_returns.std()

    if daily_variance > 0.05:  # 5% threshold
        return ValidationResult(
            is_valid=False,
            error_type=ValidationErrorType.OUT_OF_RANGE,
            error_message=(
                f"Stock has high volatility ({daily_variance * 100:.2f}%). "
                "Consider reducing investment amount for volatile stocks."
            ),
        )

    return ValidationResult(is_valid=True, error_type=None, error_message=None)


def get_validation_help_text() -> str:
    """
    Get help text for valid input formats.

    Returns:
        Formatted help string
    """
    return """
📊 **Valid Input Formats:**

**Ticker:**
- 1-5 uppercase letters: `AAPL`, `MSFT`, `GOOGL`
- With class suffix: `BRK.A`, `BRK.B`

**Amount:**
- Numeric value: `1000`, `1500.50`, `1,000`
- Range: $1 to $1,000,000

**Example:**
`AAPL 1000` - Invest $1000 in Apple stock

For a list of available stocks, use `/stocks` command.
"""
