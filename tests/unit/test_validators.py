"""
Unit tests for validators module.

Tests cover:
- Ticker validation
- Investment amount validation
- Forecast request validation
- Stock volatility validation
- Help text generation
"""

import pandas as pd
import pytest

from src.utils.validators import (
    ValidationError,
    ValidationErrorType,
    ValidationResult,
    get_validation_help_text,
    validate_forecast_request,
    validate_investment_amount,
    validate_stock_volatility,
    validate_ticker,
)


class TestValidateTicker:
    """Test ticker validation."""

    def test_validate_ticker_valid_simple(self):
        """Test validation of valid simple ticker."""
        result = validate_ticker("AAPL")

        assert result.is_valid is True
        assert result.error_type is None
        assert result.error_message is None

    def test_validate_ticker_valid_multiple_letters(self):
        """Test validation of valid tickers with different lengths."""
        for ticker in ["A", "AA", "AAA", "AAAA", "AAAAA"]:
            result = validate_ticker(ticker)
            assert result.is_valid is True, f"Failed for ticker: {ticker}"

    def test_validate_ticker_valid_with_class_suffix(self):
        """Test validation of valid tickers with class suffix."""
        result1 = validate_ticker("BRK.A")
        result2 = validate_ticker("BRK.B")

        assert result1.is_valid is True
        assert result2.is_valid is True

    def test_validate_ticker_valid_case_insensitive(self):
        """Test that validation is case-insensitive."""
        result1 = validate_ticker("AAPL")
        result2 = validate_ticker("aapl")
        result3 = validate_ticker("AaPl")

        assert result1.is_valid is True
        assert result2.is_valid is True
        assert result3.is_valid is True

    def test_validate_ticker_valid_with_whitespace(self):
        """Test that whitespace is trimmed."""
        result = validate_ticker("  AAPL  ")

        assert result.is_valid is True

    def test_validate_ticker_empty(self):
        """Test validation of empty ticker."""
        result = validate_ticker("")

        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.EMPTY
        assert "cannot be empty" in result.error_message.lower()

    def test_validate_ticker_none(self):
        """Test validation of None ticker."""
        result = validate_ticker(None)

        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.EMPTY

    def test_validate_ticker_non_string(self):
        """Test validation of non-string input."""
        result = validate_ticker(123)

        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.INVALID_FORMAT
        assert "must be text" in result.error_message.lower()

    def test_validate_ticker_too_long(self):
        """Test validation of ticker that's too long."""
        result = validate_ticker("AAAAAA")

        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.INVALID_FORMAT

    def test_validate_ticker_invalid_characters(self):
        """Test validation of ticker with invalid characters."""
        invalid_tickers = ["AAPL1", "AAPL-", "AAPL_", "AAPL!"]

        for ticker in invalid_tickers:
            result = validate_ticker(ticker)
            assert result.is_valid is False, f"Failed for ticker: {ticker}"

    def test_validate_ticker_invalid_class_suffix(self):
        """Test validation of ticker with invalid class suffix."""
        invalid_tickers = ["BRK.ABC", "BRK.1", "BRK."]

        for ticker in invalid_tickers:
            result = validate_ticker(ticker)
            assert result.is_valid is False, f"Failed for ticker: {ticker}"

    def test_validate_ticker_special_cases(self):
        """Test validation of special case tickers."""
        # Valid special cases
        valid_tickers = ["BRK.A", "BRK.B", "GOOG", "GOOGL"]

        for ticker in valid_tickers:
            result = validate_ticker(ticker)
            assert result.is_valid is True, f"Failed for ticker: {ticker}"


class TestValidateInvestmentAmount:
    """Test investment amount validation."""

    def test_validate_amount_valid_integer(self):
        """Test validation of valid integer amount."""
        result = validate_investment_amount(1000)

        assert result.is_valid is True
        assert result.error_type is None
        assert result.error_message is None

    def test_validate_amount_valid_float(self):
        """Test validation of valid float amount."""
        result = validate_investment_amount(1000.50)

        assert result.is_valid is True

    def test_validate_amount_valid_string(self):
        """Test validation of valid string amount."""
        result = validate_investment_amount("1000")

        assert result.is_valid is True

    def test_validate_amount_valid_string_with_commas(self):
        """Test validation of string amount with commas."""
        result = validate_investment_amount("1,000")

        assert result.is_valid is True

    def test_validate_amount_valid_string_with_decimals(self):
        """Test validation of string amount with decimals."""
        result = validate_investment_amount("1,000.50")

        assert result.is_valid is True

    def test_validate_amount_minimum_boundary(self):
        """Test validation at minimum boundary ($1)."""
        result = validate_investment_amount(1)

        assert result.is_valid is True

    def test_validate_amount_maximum_boundary(self):
        """Test validation at maximum boundary ($1,000,000)."""
        result = validate_investment_amount(1_000_000)

        assert result.is_valid is True

    def test_validate_amount_below_minimum(self):
        """Test validation of amount below minimum."""
        result = validate_investment_amount(0.99)

        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.OUT_OF_RANGE
        assert "at least $1" in result.error_message

    def test_validate_amount_zero(self):
        """Test validation of zero amount."""
        result = validate_investment_amount(0)

        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.OUT_OF_RANGE

    def test_validate_amount_negative(self):
        """Test validation of negative amount."""
        result = validate_investment_amount(-100)

        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.OUT_OF_RANGE

    def test_validate_amount_above_maximum(self):
        """Test validation of amount above maximum."""
        result = validate_investment_amount(1_000_001)

        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.OUT_OF_RANGE
        assert "cannot exceed $1,000,000" in result.error_message

    def test_validate_amount_very_large(self):
        """Test validation of very large amount."""
        result = validate_investment_amount(10_000_000)

        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.OUT_OF_RANGE

    def test_validate_amount_empty_string(self):
        """Test validation of empty string."""
        result = validate_investment_amount("")

        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.EMPTY

    def test_validate_amount_whitespace_string(self):
        """Test validation of whitespace string."""
        result = validate_investment_amount("   ")

        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.EMPTY

    def test_validate_amount_none(self):
        """Test validation of None."""
        result = validate_investment_amount(None)

        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.EMPTY

    def test_validate_amount_invalid_string(self):
        """Test validation of invalid string."""
        result = validate_investment_amount("abc")

        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.NON_NUMERIC
        assert "numeric value" in result.error_message.lower()

    def test_validate_amount_invalid_string_with_text(self):
        """Test validation of string with text."""
        result = validate_investment_amount("1000 dollars")

        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.NON_NUMERIC

    def test_validate_amount_string_with_currency_symbol(self):
        """Test validation of string with currency symbol."""
        result = validate_investment_amount("$1000")

        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.NON_NUMERIC

    def test_validate_amount_very_small_positive(self):
        """Test validation of very small positive amount."""
        result = validate_investment_amount(0.01)

        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.OUT_OF_RANGE


class TestValidateForecastRequest:
    """Test forecast request validation."""

    def test_validate_forecast_request_valid(self):
        """Test validation of valid forecast request."""
        result = validate_forecast_request("AAPL", 1000)

        assert result.is_valid is True
        assert result.error_type is None
        assert result.error_message is None

    def test_validate_forecast_request_valid_string_amount(self):
        """Test validation with string amount."""
        result = validate_forecast_request("AAPL", "1000")

        assert result.is_valid is True

    def test_validate_forecast_request_invalid_ticker(self):
        """Test validation with invalid ticker."""
        result = validate_forecast_request("INVALID123", 1000)

        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.INVALID_FORMAT

    def test_validate_forecast_request_empty_ticker(self):
        """Test validation with empty ticker."""
        result = validate_forecast_request("", 1000)

        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.EMPTY

    def test_validate_forecast_request_invalid_amount(self):
        """Test validation with invalid amount."""
        result = validate_forecast_request("AAPL", -100)

        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.OUT_OF_RANGE

    def test_validate_forecast_request_both_invalid(self):
        """Test validation with both ticker and amount invalid."""
        result = validate_forecast_request("INVALID123", -100)

        assert result.is_valid is False
        # Should fail on ticker first
        assert result.error_type == ValidationErrorType.INVALID_FORMAT

    def test_validate_forecast_request_none_ticker(self):
        """Test validation with None ticker."""
        result = validate_forecast_request(None, 1000)

        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.EMPTY

    def test_validate_forecast_request_none_amount(self):
        """Test validation with None amount."""
        result = validate_forecast_request("AAPL", None)

        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.EMPTY

    def test_validate_forecast_request_both_none(self):
        """Test validation with both None."""
        result = validate_forecast_request(None, None)

        assert result.is_valid is False
        # Should fail on ticker first
        assert result.error_type == ValidationErrorType.EMPTY


class TestValidateStockVolatility:
    """Test stock volatility validation."""

    def test_validate_volatility_normal(self):
        """Test validation of normal volatility."""
        returns = pd.Series([0.01, -0.01, 0.02, -0.02, 0.01])
        result = validate_stock_volatility(returns)

        assert result.is_valid is True

    def test_validate_volatility_high(self):
        """Test validation of high volatility (>5%)."""
        returns = pd.Series([0.06, -0.06, 0.07, -0.07, 0.06])
        result = validate_stock_volatility(returns)

        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.OUT_OF_RANGE
        assert "high volatility" in result.error_message.lower()

    def test_validate_volatility_none(self):
        """Test validation with None input."""
        result = validate_stock_volatility(None)

        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.EMPTY

    def test_validate_volatility_empty_series(self):
        """Test validation with empty series."""
        returns = pd.Series([])
        result = validate_stock_volatility(returns)

        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.EMPTY

    def test_validate_volatility_single_value(self):
        """Test validation with single value (std=0)."""
        returns = pd.Series([0.01])
        result = validate_stock_volatility(returns)

        assert result.is_valid is True

    def test_validate_volatility_exactly_threshold(self):
        """Test validation at exactly 5% threshold."""
        returns = pd.Series([0.05, -0.05, 0.05, -0.05, 0.05])
        result = validate_stock_volatility(returns)

        # Should be invalid at exactly 5%
        assert result.is_valid is False


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_validation_result_valid(self):
        """Test creating valid ValidationResult."""
        result = ValidationResult(is_valid=True, error_type=None, error_message=None)

        assert result.is_valid is True
        assert result.error_type is None
        assert result.error_message is None

    def test_validation_result_invalid(self):
        """Test creating invalid ValidationResult."""
        result = ValidationResult(
            is_valid=False,
            error_type=ValidationErrorType.INVALID_FORMAT,
            error_message="Invalid format",
        )

        assert result.is_valid is False
        assert result.error_type == ValidationErrorType.INVALID_FORMAT
        assert result.error_message == "Invalid format"


class TestValidationError:
    """Test ValidationError exception."""

    def test_validation_error_creation(self):
        """Test creating ValidationError."""
        error = ValidationError(
            message="Test error message", error_type=ValidationErrorType.INVALID_FORMAT
        )

        assert error.message == "Test error message"
        assert error.error_type == ValidationErrorType.INVALID_FORMAT

    def test_validation_error_default_type(self):
        """Test ValidationError with default error type."""
        error = ValidationError(message="Test error")

        assert error.message == "Test error"
        assert error.error_type == ValidationErrorType.UNKNOWN

    def test_validation_error_as_exception(self):
        """Test that ValidationError can be raised."""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Test error")

        assert str(exc_info.value) == "Test error"


class TestGetValidationHelpText:
    """Test validation help text generation."""

    def test_get_validation_help_text(self):
        """Test getting validation help text."""
        help_text = get_validation_help_text()

        assert isinstance(help_text, str)
        assert len(help_text) > 0

    def test_help_text_contains_ticker_info(self):
        """Test that help text contains ticker information."""
        help_text = get_validation_help_text()

        assert "Ticker" in help_text or "ticker" in help_text.lower()
        assert "AAPL" in help_text

    def test_help_text_contains_amount_info(self):
        """Test that help text contains amount information."""
        help_text = get_validation_help_text()

        assert "Amount" in help_text or "amount" in help_text.lower()
        assert "$1" in help_text or "1,000,000" in help_text

    def test_help_text_contains_examples(self):
        """Test that help text contains examples."""
        help_text = get_validation_help_text()

        assert "Example" in help_text or "example" in help_text.lower()

    def test_help_text_formatting(self):
        """Test that help text has proper formatting."""
        help_text = get_validation_help_text()

        # Should contain markdown formatting
        assert "**" in help_text or "`" in help_text


class TestValidationEdgeCases:
    """Test edge cases in validation."""

    def test_validate_ticker_unicode(self):
        """Test validation with unicode characters."""
        result = validate_ticker("AAPL🚀")

        assert result.is_valid is False

    def test_validate_amount_scientific_notation(self):
        """Test validation with scientific notation."""
        result = validate_investment_amount("1e3")

        assert result.is_valid is True

    def test_validate_amount_very_small_decimal(self):
        """Test validation with very small decimal."""
        result = validate_investment_amount(0.0001)

        assert result.is_valid is False

    def test_validate_amount_with_tabs(self):
        """Test validation with tabs."""
        result = validate_investment_amount("\t1000\t")

        assert result.is_valid is True

    def test_validate_forecast_request_whitespace_only(self):
        """Test validation with whitespace-only inputs."""
        # Whitespace is trimmed, but ticker validation checks format first
        result = validate_forecast_request("   ", "   ")

        assert result.is_valid is False
        # Ticker validation fails on whitespace-only (invalid format)
        assert result.error_type in [
            ValidationErrorType.EMPTY,
            ValidationErrorType.INVALID_FORMAT,
        ]

    def test_validate_ticker_mixed_case_with_suffix(self):
        """Test validation of mixed case ticker with suffix."""
        result = validate_ticker("BrK.a")

        assert result.is_valid is True

    def test_validate_amount_multiple_decimals(self):
        """Test validation with multiple decimal points."""
        result = validate_investment_amount("1.000.50")

        assert result.is_valid is False

    def test_validate_amount_leading_zeros(self):
        """Test validation with leading zeros."""
        result = validate_investment_amount("0001000")

        assert result.is_valid is True
