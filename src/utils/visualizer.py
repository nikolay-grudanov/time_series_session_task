"""
Utilities for creating forecast graphs with confidence intervals.
"""
import io
from datetime import timedelta

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def create_forecast_visualization(
    historical_data: pd.Series,
    forecast_data: np.ndarray,
    confidence_intervals: tuple[np.ndarray, np.ndarray] | None = None,
    title: str = "Stock Price Forecast"
) -> bytes:
    """
    Creates a visualization of historical and forecasted stock prices with confidence intervals.

    Args:
        historical_data: Historical stock price data with DateTime index
        forecast_data: Forecasted stock prices
        confidence_intervals: Tuple of (lower_bound, upper_bound) arrays for confidence intervals
        title: Title for the chart

    Returns:
        Bytes of the image in PNG format
    """
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot historical data
    ax.plot(historical_data.index, historical_data.values, label='Historical Prices', color='blue')

    # Generate future dates for forecast
    last_date = historical_data.index[-1]
    future_dates = pd.date_range(
        start=last_date + timedelta(days=1),
        periods=len(forecast_data),
        freq='D'
    )

    # Plot forecast data
    ax.plot(future_dates, forecast_data, label='Forecast', color='red', linestyle='--')

    # Add confidence intervals if provided
    if confidence_intervals:
        lower_bound, upper_bound = confidence_intervals

        # Extend the confidence intervals to match the forecast dates
        ax.fill_between(
            future_dates,
            lower_bound,
            upper_bound,
            color='red',
            alpha=0.2,
            label='Confidence Interval'
        )

    # Formatting
    ax.set_title(title)
    ax.set_xlabel('Date')
    ax.set_ylabel('Price')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.6)

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45)

    # Adjust layout to prevent label cutoff
    plt.tight_layout()

    # Save plot to bytes
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
    img_buffer.seek(0)

    # Get the image bytes
    img_bytes = img_buffer.getvalue()

    # Close the plot to free memory
    plt.close(fig)

    return img_bytes


def calculate_confidence_intervals(
    forecast_data: np.ndarray,
    historical_data: pd.Series,
    confidence_level: float = 0.95
) -> tuple[np.ndarray, np.ndarray]:
    """
    Calculates confidence intervals for the forecast based on historical volatility.

    Args:
        forecast_data: Forecasted stock prices
        historical_data: Historical stock price data
        confidence_level: Confidence level (e.g., 0.95 for 95%)

    Returns:
        Tuple of (lower_bound, upper_bound) arrays
    """
    # Calculate historical volatility (standard deviation of returns)
    returns = historical_data.pct_change().dropna()
    volatility = returns.std()

    # Calculate z-score for the confidence level
    z_score = abs(np.percentile(np.random.normal(0, 1, 10000), (1 - confidence_level) * 100 / 2))

    # Calculate margin of error based on forecast values and volatility
    # Using the last known price as a reference point for scaling the error
    last_price = historical_data.iloc[-1]
    margin_of_error = last_price * volatility * z_score

    # Create confidence bounds
    lower_bound = forecast_data - margin_of_error
    upper_bound = forecast_data + margin_of_error

    return lower_bound, upper_bound


def create_interactive_forecast_plot(
    historical_data: pd.Series,
    forecast_data: np.ndarray,
    confidence_intervals: tuple[np.ndarray, np.ndarray] | None = None,
    title: str = "Interactive Stock Price Forecast"
):
    """
    Creates an interactive forecast plot using matplotlib.
    Note: For true interactivity, libraries like plotly would be better,
    but this provides basic plotting functionality.

    Args:
        historical_data: Historical stock price data with DateTime index
        forecast_data: Forecasted stock prices
        confidence_intervals: Tuple of (lower_bound, upper_bound) arrays for confidence intervals
        title: Title for the chart
    """
    # Create figure and axis
    _, ax = plt.subplots(figsize=(14, 8))

    # Plot historical data
    ax.plot(historical_data.index, historical_data.values, label='Historical Prices', color='blue', linewidth=1.5)

    # Generate future dates for forecast
    last_date = historical_data.index[-1]
    future_dates = pd.date_range(
        start=last_date + timedelta(days=1),
        periods=len(forecast_data),
        freq='D'
    )

    # Plot forecast data
    ax.plot(future_dates, forecast_data, label='Forecast', color='red', linestyle='--', linewidth=1.5)

    # Add confidence intervals if provided
    if confidence_intervals:
        lower_bound, upper_bound = confidence_intervals

        ax.fill_between(
            future_dates,
            lower_bound,
            upper_bound,
            color='red',
            alpha=0.2,
            label='Confidence Interval'
        )

    # Formatting
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Price ($)', fontsize=12)
    ax.legend(fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.6)

    # Add horizontal line for the last known price
    last_price = historical_data.iloc[-1]
    ax.axhline(y=last_price, color='green', linestyle='-.', alpha=0.7, label=f'Last Price: ${last_price:.2f}')

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45)

    # Adjust layout to prevent label cutoff
    plt.tight_layout()

    # Show the plot
    plt.show()


def save_forecast_plot(
    historical_data: pd.Series,
    forecast_data: np.ndarray,
    filename: str,
    confidence_intervals: tuple[np.ndarray, np.ndarray] | None = None,
    title: str = "Stock Price Forecast"
):
    """
    Saves the forecast visualization to a file.

    Args:
        historical_data: Historical stock price data with DateTime index
        forecast_data: Forecasted stock prices
        filename: Name of the file to save the plot to
        confidence_intervals: Tuple of (lower_bound, upper_bound) arrays for confidence intervals
        title: Title for the chart
    """
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(14, 8))

    # Plot historical data
    ax.plot(historical_data.index, historical_data.values, label='Historical Prices', color='blue', linewidth=1.5)

    # Generate future dates for forecast
    last_date = historical_data.index[-1]
    future_dates = pd.date_range(
        start=last_date + timedelta(days=1),
        periods=len(forecast_data),
        freq='D'
    )

    # Plot forecast data
    ax.plot(future_dates, forecast_data, label='Forecast', color='red', linestyle='--', linewidth=1.5)

    # Add confidence intervals if provided
    if confidence_intervals:
        lower_bound, upper_bound = confidence_intervals

        ax.fill_between(
            future_dates,
            lower_bound,
            upper_bound,
            color='red',
            alpha=0.2,
            label='Confidence Interval'
        )

    # Formatting
    ax.set_title(title, fontsize=16, fontweight='bold')
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Price ($)', fontsize=12)
    ax.legend(fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.6)

    # Add horizontal line for the last known price
    last_price = historical_data.iloc[-1]
    ax.axhline(y=last_price, color='green', linestyle='-.', alpha=0.7, label=f'Last Price: ${last_price:.2f}')

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45)

    # Adjust layout to prevent label cutoff
    plt.tight_layout()

    # Save the plot
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Plot saved to {filename}")

    # Close the plot to free memory
    plt.close(fig)
