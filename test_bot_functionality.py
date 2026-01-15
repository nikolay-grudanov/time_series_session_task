#!/usr/bin/env python3
"""
Test script to verify the functionality of the stock forecast bot.

These tests are meant to be run via main() function for manual verification.
They are skipped in pytest because they require network access and take too long.
"""

import pandas as pd
import pytest

from src.services.data_loader import DataLoaderService
from src.services.forecasting import ForecastingService
from src.services.profit_calculator import ProfitCalculatorService
from src.services.trading_strategy import TradingStrategyService
from src.utils.validators import validate_forecast_request


@pytest.mark.skip(reason="Manual test requiring network access - run via main()")
def test_data_loading():
    """Test data loading functionality."""
    print("Testing data loading...")
    loader = DataLoaderService()

    ticker = "AAPL"
    try:
        data = loader.download_historical_data(ticker)
        if data is not None and not data.empty:
            print(f"Successfully loaded {len(data)} data points for {ticker}")
            print(f"  Date range: {data.index[0]} to {data.index[-1]}")
            print(
                f"  Price range: ${data['Close'].min():.2f} to ${data['Close'].max():.2f}"
            )
            return data
        else:
            print(f"Failed to load data for {ticker}")
            return None
    except Exception as e:
        print(f"Error loading data for {ticker}: {e}")
        return None


@pytest.mark.skip(reason="Manual test requiring network access - run via main()")
def test_model_training_and_forecasting():
    """Test model training and forecasting functionality."""
    print("\nTesting model training and forecasting...")

    historical_data = test_data_loading()

    if historical_data is None or historical_data.empty:
        print("Cannot test forecasting without historical data")
        return None

    close_prices = historical_data["Close"]
    if not isinstance(close_prices, pd.Series):
        close_prices = pd.Series(close_prices)

    forecasting_service = ForecastingService(forecast_days=30)

    try:
        result = forecasting_service.generate_forecast_with_volatility_adjustment(
            ticker="AAPL", historical_data=close_prices
        )

        print("Forecast generated successfully")
        print(f"  Forecast length: {len(result['forecast_data'])} days")
        print(f"  Expected change: {result['expected_change_pct']:+.2f}%")
        print(f"  Best model: {result['best_model_name']}")
        print(
            f"  Volatility: {'High' if result['volatility_assessment']['is_extremely_volatile'] else 'Normal'}"
        )

        print("  Model Metrics:")
        for model_name, metrics in result["model_metrics"].items():
            print(f"    {model_name}: RMSE={metrics['rmse']:.4f}")

        return result
    except Exception as e:
        print(f"Error generating forecast: {e}")
        return None


@pytest.mark.skip(reason="Manual test requiring network access - run via main()")
def test_trading_strategy():
    """Test trading strategy generation."""
    print("\nTesting trading strategy generation...")

    forecast_result = test_model_training_and_forecasting()
    historical_data = test_data_loading()

    if forecast_result is None:
        print("Cannot test trading strategy without forecast result")
        return None

    try:
        trading_service = TradingStrategyService()

        close_prices = historical_data["Close"]
        if not isinstance(close_prices, pd.Series):
            close_prices = pd.Series(close_prices)

        recommendations = trading_service.generate_trading_recommendations(
            forecast_data=forecast_result["forecast_data"],
            historical_data=close_prices,
            forecast_dates=forecast_result["forecast_dates"],
            investment_amount=1000.0,
        )

        print("Trading recommendations generated")
        print(f"  Buy signals: {recommendations['trade_signals']['total_buy_signals']}")
        print(
            f"  Sell signals: {recommendations['trade_signals']['total_sell_signals']}"
        )

        return recommendations
    except Exception as e:
        print(f"Error generating trading recommendations: {e}")
        return None


def test_validation():
    """Test input validation functionality."""
    print("\nTesting input validation...")

    result = validate_forecast_request("AAPL", "1000")
    if result.is_valid:
        print("Valid input correctly validated")
    else:
        print(f"Valid input incorrectly rejected: {result.error_message}")

    result = validate_forecast_request("INVALIDTICKER123", "1000")
    if not result.is_valid:
        print("Invalid ticker correctly rejected")
    else:
        print("Invalid ticker incorrectly accepted")

    result = validate_forecast_request("AAPL", "-500")
    if not result.is_valid:
        print("Invalid amount correctly rejected")
    else:
        print("Invalid amount incorrectly accepted")


def main():
    """Main test function."""
    print("Starting Stock Forecast Bot functionality tests...\n")

    test_validation()
    test_model_training_and_forecasting()
    test_trading_strategy()

    print("\n" + "=" * 60)
    print("Functionality test completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
