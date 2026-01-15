"""
Stock catalog cache utility for in-memory stock data management.
Provides caching layer for stock catalog with TTL support.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class StockEntry:
    """Represents a single stock in the catalog."""

    ticker: str
    name: str
    sector: str | None = None
    last_updated: str | None = None


@dataclass
class CacheMetadata:
    """Metadata for cached stock catalog."""

    load_time: datetime
    source: str  # 'csv' or 'api'
    entry_count: int
    ttl_seconds: int


class CatalogCache:
    """
    Manages in-memory caching of stock catalog data.

    Features:
    - Thread-safe singleton pattern
    - TTL-based cache expiration
    - CSV file source support
    - API refresh capability
    """

    _instance: "CatalogCache | None" = None
    _lock = __import__("threading").Lock()

    def __new__(cls, catalog_path: Path | str | None = None) -> "CatalogCache":
        """Singleton pattern for catalog cache."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, catalog_path: Path | str | None = None) -> None:
        """Initialize the catalog cache."""
        if self._initialized:
            return

        if catalog_path is None:
            # Default path to config/catalog.csv
            self.catalog_path = Path(__file__).parent.parent / "config" / "catalog.csv"
        else:
            self.catalog_path = Path(catalog_path)

        # In-memory cache
        self._stocks: dict[str, StockEntry] = {}
        self._metadata: CacheMetadata | None = None

        # Cache TTL: 24 hours by default
        self._default_ttl_seconds = 24 * 60 * 60

        # API rate limiting
        self._last_api_call: float = 0
        self._api_rate_limit_delay: float = 1.0  # seconds

        self._initialized = True
        logger.info(f"CatalogCache initialized with catalog path: {self.catalog_path}")

    def load_catalog(self, force_refresh: bool = False) -> bool:
        """
        Load stock catalog from CSV file.

        Args:
            force_refresh: Force reload even if cache is valid

        Returns:
            True if load successful, False otherwise
        """
        try:
            # Check if cache is still valid
            if not force_refresh and self._is_cache_valid():
                logger.debug("Using cached stock catalog (still valid)")
                return True

            # Load from CSV
            if not self.catalog_path.exists():
                logger.warning(f"Catalog file not found: {self.catalog_path}")
                return self._load_default_catalog()

            df = pd.read_csv(self.catalog_path)

            # Clear existing cache
            self._stocks.clear()

            # Parse stocks
            for _, row in df.iterrows():
                ticker = str(row.get("ticker", "")).strip().upper()
                if not ticker:
                    continue

                sector_value = row.get("sector")
                name_value = row.get("name")
                last_updated_value = row.get("last_updated")

                stock = StockEntry(
                    ticker=ticker,
                    name=str(name_value) if name_value else "",
                    sector=str(sector_value) if sector_value else None,
                    last_updated=str(last_updated_value)
                    if last_updated_value
                    else None,
                )
                self._stocks[ticker] = stock

            # Update metadata
            self._metadata = CacheMetadata(
                load_time=datetime.now(),
                source="csv",
                entry_count=len(self._stocks),
                ttl_seconds=self._default_ttl_seconds,
            )

            logger.info(f"Loaded {len(self._stocks)} stocks from {self.catalog_path}")
            return True

        except Exception as e:
            logger.error(f"Error loading catalog from {self.catalog_path}: {e!s}")
            return self._load_default_catalog()

    def _load_default_catalog(self) -> bool:
        """
        Load a minimal default catalog with top stocks.

        Used when the catalog file is missing or corrupted.
        """
        logger.info("Loading default catalog with top 10 stocks")

        default_stocks = [
            ("AAPL", "Apple Inc.", "Technology"),
            ("GOOGL", "Alphabet Inc.", "Technology"),
            ("MSFT", "Microsoft Corporation", "Technology"),
            ("AMZN", "Amazon.com Inc.", "Consumer Cyclical"),
            ("TSLA", "Tesla Inc.", "Consumer Cyclical"),
            ("META", "Meta Platforms Inc.", "Technology"),
            ("NVDA", "NVIDIA Corporation", "Technology"),
            ("JPM", "JPMorgan Chase & Co.", "Financial Services"),
            ("V", "Visa Inc.", "Financial Services"),
            ("JNJ", "Johnson & Johnson", "Healthcare"),
        ]

        self._stocks.clear()
        for ticker, name, sector in default_stocks:
            self._stocks[ticker] = StockEntry(
                ticker=ticker,
                name=name,
                sector=sector,
                last_updated=datetime.now().strftime("%Y-%m-%d"),
            )

        self._metadata = CacheMetadata(
            load_time=datetime.now(),
            source="default",
            entry_count=len(self._stocks),
            ttl_seconds=self._default_ttl_seconds,
        )

        logger.info(f"Loaded {len(self._stocks)} default stocks")
        return True

    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid."""
        if self._metadata is None:
            return False

        elapsed = (datetime.now() - self._metadata.load_time).total_seconds()
        return elapsed < self._metadata.ttl_seconds

    def get_stocks(self, force_refresh: bool = False) -> list[StockEntry]:
        """
        Get all stocks from catalog.

        Args:
            force_refresh: Force reload from source

        Returns:
            List of StockEntry objects
        """
        if not self._stocks or force_refresh:
            self.load_catalog(force_refresh)

        return list(self._stocks.values())

    def get_stock(self, ticker: str) -> StockEntry | None:
        """
        Get a specific stock by ticker.

        Args:
            ticker: Stock ticker symbol (case-insensitive)

        Returns:
            StockEntry or None if not found
        """
        ticker = ticker.upper().strip()
        return self._stocks.get(ticker)

    def search_stocks(self, query: str) -> list[StockEntry]:
        """
        Search stocks by ticker or name.

        Args:
            query: Search query (partial match)

        Returns:
            List of matching StockEntry objects
        """
        query = query.lower().strip()
        results = []

        for stock in self._stocks.values():
            if query in stock.ticker.lower() or query in stock.name.lower():
                results.append(stock)

        return results

    def get_tickers(self) -> list[str]:
        """Get list of all ticker symbols."""
        return list(self._stocks.keys())

    def get_stock_count(self) -> int:
        """Get the number of stocks in catalog."""
        return len(self._stocks)

    def refresh_catalog(self, new_data: list[dict[str, Any]] | None = None) -> bool:
        """
        Refresh catalog with new data from API or provided data.

        Args:
            new_data: List of stock dictionaries. If None, attempts API refresh.

        Returns:
            True if refresh successful
        """
        if new_data is not None:
            # Update with provided data
            self._stocks.clear()
            for item in new_data:
                ticker = str(item.get("ticker", "")).strip().upper()
                if ticker:
                    self._stocks[ticker] = StockEntry(
                        ticker=ticker,
                        name=str(item.get("name", "")),
                        sector=str(item.get("sector", ""))
                        if item.get("sector")
                        else None,
                        last_updated=datetime.now().strftime("%Y-%m-%d"),
                    )

            self._metadata = CacheMetadata(
                load_time=datetime.now(),
                source="api",
                entry_count=len(self._stocks),
                ttl_seconds=self._default_ttl_seconds,
            )
            logger.info(f"Refreshed catalog with {len(self._stocks)} stocks from API")
            return True

        # This would be implemented with yfinance API call
        # For now, just reload from CSV
        return self.load_catalog(force_refresh=True)

    def add_stock(self, stock: StockEntry) -> None:
        """Add or update a stock in the catalog."""
        self._stocks[stock.ticker.upper()] = stock

    def remove_stock(self, ticker: str) -> bool:
        """
        Remove a stock from the catalog.

        Args:
            ticker: Stock ticker symbol (case-insensitive)

        Returns:
            True if stock was removed, False if not found
        """
        ticker = ticker.upper().strip()
        if ticker in self._stocks:
            del self._stocks[ticker]
            logger.info(f"Removed stock {ticker} from catalog")
            return True
        return False

    def deduplicate_catalog(self) -> int:
        """
        Remove duplicate ticker entries from the catalog.
        Keeps the first occurrence of each ticker.

        Returns:
            Number of duplicates removed
        """
        original_count = len(self._stocks)
        seen: set[str] = set()
        duplicates_found: list[str] = []

        for ticker, stock in list(self._stocks.items()):
            if ticker in seen:
                duplicates_found.append(ticker)
                del self._stocks[ticker]
            else:
                seen.add(ticker)

        if duplicates_found:
            logger.warning(
                f"Found and removed {len(duplicates_found)} duplicate tickers: "
                f"{duplicates_found}"
            )

        removed_count = original_count - len(self._stocks)
        return removed_count

    def handle_delisted_stocks(
        self, active_tickers: list[str]
    ) -> tuple[int, list[str]]:
        """
        Remove stocks that are no longer available (delisted).

        Args:
            active_tickers: List of currently active ticker symbols

        Returns:
            Tuple of (removed_count, list of removed tickers)
        """
        active_set = {t.upper().strip() for t in active_tickers}
        removed: list[str] = []

        for ticker in list(self._stocks.keys()):
            if ticker not in active_set:
                removed.append(ticker)
                del self._stocks[ticker]

        if removed:
            logger.info(f"Removed {len(removed)} delisted stocks: {removed}")

        return len(removed), removed

    def validate_catalog_integrity(self) -> dict[str, Any]:
        """
        Validate catalog integrity and return status report.

        Returns:
            Dictionary with validation results
        """
        report: dict[str, Any] = {
            "total_stocks": len(self._stocks),
            "duplicate_count": 0,
            "empty_tickers": [],
            "empty_names": [],
            "is_valid": True,
            "issues": [],
        }

        # Check for duplicates
        seen: set[str] = set()
        for ticker, stock in self._stocks.items():
            if ticker in seen:
                report["duplicate_count"] += 1
                report["issues"].append(f"Duplicate ticker: {ticker}")
            seen.add(ticker)

            # Check for empty required fields
            if not stock.ticker:
                report["empty_tickers"].append(stock.name)
                report["is_valid"] = False

            if not stock.name:
                report["empty_names"].append(stock.ticker)
                report["is_valid"] = False

        if report["duplicate_count"] > 0:
            report["is_valid"] = False

        return report

    def get_cache_info(self) -> dict[str, Any]:
        """Get cache status information."""
        return {
            "catalog_path": str(self.catalog_path),
            "stock_count": len(self._stocks),
            "is_valid": self._is_cache_valid(),
            "metadata": {
                "load_time": self._metadata.load_time.isoformat()
                if self._metadata
                else None,
                "source": self._metadata.source if self._metadata else None,
                "entry_count": self._metadata.entry_count if self._metadata else 0,
                "ttl_seconds": self._metadata.ttl_seconds if self._metadata else 0,
            }
            if self._metadata
            else None,
        }

    def clear_cache(self) -> None:
        """Clear the in-memory cache."""
        self._stocks.clear()
        self._metadata = None
        logger.info("Catalog cache cleared")

    @property
    def is_empty(self) -> bool:
        """Check if cache is empty."""
        return len(self._stocks) == 0


def get_catalog_cache(catalog_path: Path | str | None = None) -> CatalogCache:
    """
    Factory function to get CatalogCache instance.

    Args:
        catalog_path: Optional path to catalog CSV file

    Returns:
        CatalogCache singleton instance
    """
    return CatalogCache(catalog_path)
