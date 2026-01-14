"""
Service to download historical stock data using yfinance.
"""
import logging
import time
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

from src.config.settings import API_RATE_LIMIT_DELAY, HISTORICAL_YEARS

logger = logging.getLogger(__name__)


class DataLoaderService:
    def __init__(self):
        self.rate_limit_delay = API_RATE_LIMIT_DELAY

    def download_historical_data(
        self,
        ticker: str,
        period_years: int = HISTORICAL_YEARS
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
            start_date = (datetime.now() - timedelta(days=period_years * 365)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')

            logger.info(f"Downloading historical data for {ticker} from {start_date} to {end_date}")

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

    def get_company_info(self, ticker: str) -> dict | None:
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
