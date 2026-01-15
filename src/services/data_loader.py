"""
Service to download historical stock data using yfinance.
Handles data loading for model training and forecasting.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
import yfinance as yf

from src.config.settings import API_RATE_LIMIT_DELAY, HISTORICAL_YEARS

logger = logging.getLogger(__name__)


# Module-level function for scheduler_service import
def download_stock_data(ticker: str, period: str = "2y") -> pd.DataFrame | None:
    """
    Download historical stock data for a ticker.

    Args:
        ticker: Stock ticker symbol (e.g., AAPL)
        period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)

    Returns:
        DataFrame with historical stock data or None if failed
    """
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period=period)

        if data.empty:
            logger.warning(f"No data found for ticker {ticker}")
            return None

        # Rate limiting
        time.sleep(API_RATE_LIMIT_DELAY)

        logger.info(f"Downloaded {len(data)} records for {ticker} ({period})")
        return data

    except Exception as e:
        logger.error(f"Error downloading data for {ticker}: {e!s}")
        return None


class DataLoaderService:
    """
    Service for loading historical stock data.

    Features:
    - Download historical data with configurable period
    - Company info retrieval
    - API rate limiting
    - Error handling with graceful degradation
    """

    def __init__(self, rate_limit_delay: float | None = None) -> None:
        """
        Initialize the data loader service.

        Args:
            rate_limit_delay: Optional custom rate limit delay in seconds
        """
        self.rate_limit_delay = rate_limit_delay or API_RATE_LIMIT_DELAY
        logger.info("DataLoaderService initialized")

    def download_historical_data(
        self, ticker: str, period_years: int = HISTORICAL_YEARS
    ) -> pd.DataFrame | None:
        """
        Downloads historical stock data for the given ticker.

        Args:
            ticker: Stock ticker symbol (e.g., AAPL)
            period_years: Number of years of historical data to download

        Returns:
            DataFrame with historical stock data or None if failed
        """
        try:
            # Calculate the start date based on period_years
            start_date = (datetime.now() - timedelta(days=period_years * 365)).strftime(
                "%Y-%m-%d"
            )
            end_date = datetime.now().strftime("%Y-%m-%d")

            logger.info(
                f"Downloading historical data for {ticker} from {start_date} to {end_date}"
            )

            # Download data using yfinance
            stock = yf.Ticker(ticker)
            data = stock.history(start=start_date, end=end_date)

            if data.empty:
                logger.warning(f"No data found for ticker {ticker}")
                return None

            # Sleep to respect API rate limits
            time.sleep(self.rate_limit_delay)

            logger.info(f"Successfully downloaded {len(data)} records for {ticker}")
            return data

        except Exception as e:
            logger.error(f"Error downloading data for {ticker}: {e!s}")
            return None

    def download_2year_data(self, ticker: str) -> pd.DataFrame | None:
        """
        Download 2 years of historical stock data.

        This is the standard method for model training per FR-017.

        Args:
            ticker: Stock ticker symbol

        Returns:
            DataFrame with 2 years of historical data or None if failed
        """
        logger.info(f"Downloading 2-year data for {ticker} per FR-017")
        return self.download_historical_data(ticker, period_years=2)

    def get_company_info(self, ticker: str) -> dict[str, Any] | None:
        """
        Gets company information for the given ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with company information or None if failed
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Sleep to respect API rate limits
            time.sleep(self.rate_limit_delay)

            return info
        except Exception as e:
            logger.error(f"Error getting company info for {ticker}: {e!s}")
            return None

    def validate_data_sufficiency(
        self, data: pd.DataFrame, min_records: int = 500
    ) -> tuple[bool, str]:
        """
        Validate that downloaded data is sufficient for model training.

        Args:
            data: DataFrame with historical stock data
            min_records: Minimum number of records required

        Returns:
            Tuple of (is_sufficient, message)
        """
        if data is None or data.empty:
            return False, "No data available"

        record_count = len(data)

        if record_count < min_records:
            return False, (
                f"Insufficient data: {record_count} records, "
                f"minimum {min_records} required for model training"
            )

        # Check for sufficient date range
        date_range = data.index[-1] - data.index[0]
        min_days = min_records  # Approximate 1 record per trading day

        if date_range.days < min_days:
            return False, (
                f"Date range too short: {date_range.days} days, "
                f"minimum {min_days} days required"
            )

        return (
            True,
            f"Data sufficient: {record_count} records over {date_range.days} days",
        )

    def get_data_quality_report(self, data: pd.DataFrame) -> dict[str, Any]:
        """
        Generate a quality report for downloaded data.

        Args:
            data: DataFrame with historical stock data

        Returns:
            Dictionary with quality metrics
        """
        if data is None or data.empty:
            return {"error": "No data available"}

        return {
            "record_count": len(data),
            "date_range": {
                "start": data.index[0].isoformat(),
                "end": data.index[-1].isoformat(),
            },
            "date_range_days": (data.index[-1] - data.index[0]).days,
            "columns": list(data.columns),
            "missing_values": data.isnull().sum().to_dict(),
            "duplicate_rows": data.index.duplicated().sum(),
        }
