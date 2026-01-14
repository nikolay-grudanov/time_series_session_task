"""
Service for generating forecasts.
"""
import logging
from datetime import timedelta
from typing import Any

import pandas as pd

from src.models.model_selector import ModelSelector
from src.utils.helpers import calculate_percentage_change
from src.utils.visualizer import (
    calculate_confidence_intervals,
    create_forecast_visualization,
)

logger = logging.getLogger(__name__)


class ForecastingService:
    """
    Service for generating stock price forecasts.
    """
    def __init__(self, forecast_days: int = 30):
        self.forecast_days = forecast_days
        self.model_selector = ModelSelector()

    def generate_forecast(
        self,
        ticker: str,
        historical_data: pd.Series,
        include_confidence_intervals: bool = True
    ) -> dict[str, Any]:
        """
        Generates a forecast for the given ticker using historical data.

        Args:
            ticker: Stock ticker symbol
            historical_data: Historical stock price data
            include_confidence_intervals: Whether to calculate confidence intervals

        Returns:
            Dictionary with forecast results
        """
        logger.info(f"Generating forecast for {ticker} using {len(historical_data)} historical data points")

        try:
            # Train all models
            training_results = self.model_selector.train_all_models(historical_data)

            # Select the best model
            best_model_name, _ = self.model_selector.select_best_model()

            # Generate forecast using the best model
            forecast_data = self.model_selector.predict(forecast_days=self.forecast_days)

            # Calculate confidence intervals if requested
            confidence_intervals = None
            if include_confidence_intervals:
                lower_bound, upper_bound = calculate_confidence_intervals(
                    forecast_data,
                    historical_data
                )
                confidence_intervals = (lower_bound, upper_bound)

            # Calculate expected price change
            last_known_price = historical_data.iloc[-1]
            forecast_end_price = forecast_data[-1]
            expected_change_pct = calculate_percentage_change(last_known_price, forecast_end_price)

            # Create visualization
            plot_bytes = create_forecast_visualization(
                historical_data=historical_data,
                forecast_data=forecast_data,
                confidence_intervals=confidence_intervals,
                title=f"{ticker} Stock Price Forecast"
            )

            # Get model metrics
            model_metrics = self.model_selector.get_model_metrics()

            result = {
                'ticker': ticker,
                'forecast_data': forecast_data,
                'forecast_dates': pd.date_range(
                    start=historical_data.index[-1] + timedelta(days=1),
                    periods=self.forecast_days,
                    freq='D'
                ),
                'confidence_intervals': confidence_intervals,
                'expected_change_pct': expected_change_pct,
                'last_known_price': last_known_price,
                'forecast_end_price': forecast_end_price,
                'best_model_name': best_model_name,
                'model_metrics': model_metrics,
                'plot_bytes': plot_bytes,
                'training_results': training_results
            }

            logger.info(f"Forecast generated successfully for {ticker}. Best model: {best_model_name}")
            return result

        except Exception as e:
            logger.error(f"Error generating forecast for {ticker}: {e!s}")
            raise

    def assess_volatility(self, historical_data: pd.Series) -> dict[str, Any]:
        """
        Assesses the volatility of the stock based on historical data.

        Args:
            historical_data: Historical stock price data

        Returns:
            Dictionary with volatility assessment
        """
        # Calculate daily returns
        returns = historical_data.pct_change().dropna()

        # Calculate volatility metrics
        volatility = returns.std()
        avg_return = returns.mean()
        var_ratio = returns.var()

        # Determine if the stock is extremely volatile (>5% daily variance)
        is_extremely_volatile = volatility > 0.05

        return {
            'volatility': volatility,
            'average_daily_return': avg_return,
            'variance': var_ratio,
            'is_extremely_volatile': is_extremely_volatile,
            'daily_returns': returns
        }

    def generate_forecast_with_volatility_adjustment(
        self,
        ticker: str,
        historical_data: pd.Series
    ) -> dict[str, Any]:
        """
        Generates a forecast with special handling for extremely volatile stocks.

        Args:
            ticker: Stock ticker symbol
            historical_data: Historical stock price data

        Returns:
            Dictionary with forecast results
        """
        # Assess volatility
        volatility_assessment = self.assess_volatility(historical_data)

        # Generate forecast
        result = self.generate_forecast(
            ticker=ticker,
            historical_data=historical_data,
            include_confidence_intervals=True
        )

        # Add volatility information to the result
        result['volatility_assessment'] = volatility_assessment

        # Adjust confidence intervals for extremely volatile stocks
        if volatility_assessment['is_extremely_volatile']:
            logger.warning(f"{ticker} is extremely volatile. Widening confidence intervals.")

            # Increase the width of confidence intervals for volatile stocks
            if result['confidence_intervals']:
                lower_bound, upper_bound = result['confidence_intervals']
                forecast_mid = result['forecast_data']

                # Calculate adjustment factor based on volatility
                vol_factor = min(volatility_assessment['volatility'] / 0.05, 3.0)  # Cap at 3x

                # Widen the intervals
                adjusted_lower = forecast_mid - (forecast_mid - lower_bound) * vol_factor
                adjusted_upper = forecast_mid + (upper_bound - forecast_mid) * vol_factor

                result['confidence_intervals'] = (adjusted_lower, adjusted_upper)
                result['adjusted_for_volatility'] = True

        return result
