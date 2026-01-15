"""
Stock catalog service for managing stock data.
Handles loading, refreshing, and providing access to stock catalog.
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import yfinance as yf

from src.config import settings
from src.utils.catalog_cache import CatalogCache, StockEntry

logger = logging.getLogger(__name__)


class CatalogService:
    """
    Service for managing stock catalog.

    Features:
    - Load catalog from CSV or API
    - Refresh catalog from Yahoo Finance
    - Handle API failures with graceful degradation
    - Rate limiting for API calls
    """

    def __init__(self, catalog_path: Path | str | None = None) -> None:
        """
        Initialize the catalog service.

        Args:
            catalog_path: Optional path to catalog CSV file
        """
        self.cache = CatalogCache(catalog_path)
        self._rate_limit_delay = settings.API_RATE_LIMIT_DELAY

        logger.info("CatalogService initialized")

    def load_catalog(self, force_refresh: bool = False) -> list[StockEntry]:
        """
        Load stock catalog from cache or file.

        Args:
            force_refresh: Force reload from source

        Returns:
            List of StockEntry objects
        """
        success = self.cache.load_catalog(force_refresh=force_refresh)

        if not success:
            logger.warning("Failed to load catalog, using default stocks")

        return self.cache.get_stocks()

    def refresh_catalog(self) -> tuple[bool, str]:
        """
        Refresh catalog from Yahoo Finance API.

        Returns:
            Tuple of (success, message)
        """
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.cache._last_api_call

        if time_since_last < self._rate_limit_delay:
            wait_time = self._rate_limit_delay - time_since_last
            logger.debug(f"Rate limiting: waiting {wait_time:.2f}s before API call")
            time.sleep(wait_time)

        try:
            logger.info("Fetching stock info from Yahoo Finance API")

            # Download info for all tickers in catalog
            tickers = self.cache.get_tickers()

            if not tickers:
                logger.warning("No tickers in catalog to refresh")
                return False, "No tickers to refresh"

            # Download in batches to avoid rate limits
            batch_size = 50
            updated_stocks = []

            for i in range(0, len(tickers), batch_size):
                batch = tickers[i : i + batch_size]
                logger.info(f"Fetching batch {i // batch_size + 1}: {batch[:5]}...")

                try:
                    for ticker in batch:
                        stock = self._fetch_stock_info(ticker)
                        if stock:
                            updated_stocks.append(stock)

                        # Rate limit delay
                        time.sleep(self._rate_limit_delay)

                except Exception as e:
                    logger.error(f"Error fetching batch {i // batch_size + 1}: {e!s}")

            # Update cache
            if updated_stocks:
                self.cache.refresh_catalog(updated_stocks)
                logger.info(f"Refreshed {len(updated_stocks)} stocks")
                return True, f"Updated {len(updated_stocks)} stocks"

            logger.warning("No stocks were updated")
            return False, "No stocks updated"

        except Exception as e:
            logger.error(f"Error refreshing catalog: {e!s}")
            return False, f"API error: {e!s}"

    def _fetch_stock_info(self, ticker: str) -> dict[str, Any] | None:
        """
        Fetch single stock info from Yahoo Finance.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with stock info or None if failed
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            return {
                "ticker": ticker.upper(),
                "name": info.get("longName", info.get("shortName", ticker)),
                "sector": info.get("sector", "Unknown"),
                "last_updated": datetime.now().strftime("%Y-%m-%d"),
            }

        except Exception as e:
            logger.debug(f"Could not fetch info for {ticker}: {e!s}")
            # Return cached value if available
            cached = self.cache.get_stock(ticker)
            if cached:
                return {
                    "ticker": cached.ticker,
                    "name": cached.name,
                    "sector": cached.sector,
                    "last_updated": cached.last_updated,
                }
            return None

    def get_stocks(
        self, force_refresh: bool = False, use_api: bool = False
    ) -> list[StockEntry]:
        """
        Get all available stocks.

        Args:
            force_refresh: Force reload from source
            use_api: Force refresh from API if True

        Returns:
            List of StockEntry objects
        """
        if use_api:
            success, _ = self.refresh_catalog()
            if not success:
                logger.warning("API refresh failed, using cached data")

        return self.load_catalog(force_refresh=force_refresh)

    def get_stock(self, ticker: str) -> StockEntry | None:
        """
        Get a specific stock by ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            StockEntry or None
        """
        return self.cache.get_stock(ticker)

    def search_stocks(self, query: str) -> list[StockEntry]:
        """
        Search stocks by query.

        Args:
            query: Search query

        Returns:
            List of matching StockEntry objects
        """
        return self.cache.search_stocks(query)

    def get_tickers(self) -> list[str]:
        """Get all ticker symbols."""
        return self.cache.get_tickers()

    def get_stock_count(self) -> int:
        """Get the number of stocks in catalog."""
        return self.cache.get_stock_count()

    def is_stock_available(self, ticker: str) -> bool:
        """
        Check if a ticker is in the catalog.

        Args:
            ticker: Stock ticker symbol

        Returns:
            True if stock is available
        """
        return self.cache.get_stock(ticker.upper().strip()) is not None

    def get_catalog_status(self) -> dict[str, Any]:
        """
        Get catalog status information.

        Returns:
            Dictionary with status info
        """
        info = self.cache.get_cache_info()
        return {
            **info,
            "stocks_available": self.get_stock_count(),
            "last_refresh": datetime.now().isoformat()
            if self.get_stock_count() > 0
            else None,
        }

    def handle_api_failure(self) -> str:
        """
        Handle Yahoo Finance API failure.

        Returns:
            User-friendly message about the failure
        """
        cache_info = self.cache.get_cache_info()

        if cache_info.get("is_valid"):
            return (
                "⚠️ Yahoo Finance API is temporarily unavailable. "
                "Showing cached data from "
                f"{cache_info['metadata']['load_time']}. "
                "Data may be slightly outdated."
            )
        else:
            return (
                "⚠️ Yahoo Finance API is unavailable and no cached data exists. "
                "Please try again later or contact support."
            )


# Singleton instance
_catalog_service: CatalogService | None = None


def get_catalog_service(catalog_path: Path | str | None = None) -> CatalogService:
    """
    Factory function to get CatalogService instance.

    Args:
        catalog_path: Optional path to catalog CSV file

    Returns:
        CatalogService singleton instance
    """
    global _catalog_service
    if _catalog_service is None:
        _catalog_service = CatalogService(catalog_path)
    return _catalog_service
