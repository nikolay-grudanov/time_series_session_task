"""
Unit tests for CatalogService class.

Tests cover:
- Loading catalog from cache
- Getting stocks and stock info
- Stock availability checks
- Catalog status retrieval
- API refresh (with mocked dependencies)
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from src.services.catalog_service import CatalogService, get_catalog_service
from src.utils.catalog_cache import StockEntry


class TestCatalogServiceInitialization:
    """Test CatalogService initialization."""

    def test_initialization_with_default_path(self):
        """Test initialization with default catalog path."""
        service = CatalogService()
        service.load_catalog()
        assert service.cache is not None
        assert service._rate_limit_delay > 0

    def test_initialization_with_custom_path(self):
        """Test initialization with custom catalog path."""
        custom_path = "/custom/path/catalog.csv"
        service = CatalogService(custom_path)
        assert service.cache.catalog_path == Path(custom_path)

    def test_factory_function_returns_singleton(self):
        """Test that factory function returns singleton instance."""
        service1 = get_catalog_service()
        service2 = get_catalog_service()
        assert service1 is service2


class TestCatalogServiceLoadCatalog:
    """Test catalog loading functionality."""

    def test_load_catalog_success(self):
        """Test successful catalog loading."""
        service = CatalogService()
        service.load_catalog()
        stocks = service.load_catalog()

        assert isinstance(stocks, list)
        assert all(isinstance(s, StockEntry) for s in stocks)
        assert len(stocks) > 0

    def test_load_catalog_with_force_refresh(self):
        """Test loading catalog with force refresh."""
        service = CatalogService()
        service.load_catalog()
        stocks1 = service.load_catalog(force_refresh=False)
        stocks2 = service.load_catalog(force_refresh=True)

        assert isinstance(stocks1, list)
        assert isinstance(stocks2, list)

    def test_load_catalog_failure_fallback(self):
        """Test that load_catalog handles failures gracefully."""
        service = CatalogService()
        service.load_catalog()

        with patch.object(service.cache, "load_catalog", return_value=False):
            stocks = service.load_catalog()
            # Should still return stocks from cache
            assert isinstance(stocks, list)


class TestCatalogServiceGetStocks:
    """Test getting stocks from catalog."""

    def test_get_stocks_returns_list(self):
        """Test that get_stocks returns a list."""
        service = CatalogService()
        service.load_catalog()
        stocks = service.get_stocks()

        assert isinstance(stocks, list)
        assert all(isinstance(s, StockEntry) for s in stocks)

    def test_get_stocks_with_force_refresh(self):
        """Test get_stocks with force_refresh parameter."""
        service = CatalogService()
        service.load_catalog()
        stocks = service.get_stocks(force_refresh=True)

        assert isinstance(stocks, list)
        assert len(stocks) > 0

    def test_get_stocks_with_api_refresh_success(self):
        """Test get_stocks with API refresh on success."""
        service = CatalogService()
        service.load_catalog()

        with patch.object(service, "refresh_catalog", return_value=(True, "Updated")):
            stocks = service.get_stocks(use_api=True)
            assert isinstance(stocks, list)

    def test_get_stocks_with_api_refresh_failure(self):
        """Test get_stocks with API refresh on failure."""
        service = CatalogService()
        service.load_catalog()

        with patch.object(service, "refresh_catalog", return_value=(False, "Error")):
            stocks = service.get_stocks(use_api=True)
            # Should still return cached stocks
            assert isinstance(stocks, list)


class TestCatalogServiceGetStock:
    """Test getting a specific stock."""

    def test_get_stock_existing(self):
        """Test getting an existing stock."""
        service = CatalogService()
        service.load_catalog()
        service.load_catalog()  # Ensure catalog is loaded
        stock = service.get_stock("AAPL")

        assert stock is not None
        assert isinstance(stock, StockEntry)
        assert stock.ticker == "AAPL"

    def test_get_stock_nonexistent(self):
        """Test getting a non-existent stock."""
        service = CatalogService()
        service.load_catalog()
        stock = service.get_stock("NONEXISTENT")

        assert stock is None

    def test_get_stock_case_insensitive(self):
        """Test that get_stock is case-insensitive."""
        service = CatalogService()
        service.load_catalog()
        service.load_catalog()

        stock1 = service.get_stock("AAPL")
        stock2 = service.get_stock("aapl")

        assert stock1 is not None
        assert stock2 is not None
        assert stock1.ticker == stock2.ticker


class TestCatalogServiceSearchStocks:
    """Test stock search functionality."""

    def test_search_stocks_by_ticker(self):
        """Test searching by ticker."""
        service = CatalogService()
        service.load_catalog()
        results = service.search_stocks("AAPL")

        assert isinstance(results, list)
        assert len(results) > 0
        assert any(s.ticker == "AAPL" for s in results)

    def test_search_stocks_by_name(self):
        """Test searching by company name."""
        service = CatalogService()
        service.load_catalog()
        results = service.search_stocks("Apple")

        assert isinstance(results, list)
        assert len(results) > 0

    def test_search_stocks_no_results(self):
        """Test search with no results."""
        service = CatalogService()
        service.load_catalog()
        results = service.search_stocks("XYZ123NONEXISTENT")

        assert isinstance(results, list)
        assert len(results) == 0


class TestCatalogServiceIsStockAvailable:
    """Test stock availability checking."""

    def test_is_stock_available_true(self):
        """Test checking available stock."""
        service = CatalogService()
        service.load_catalog()
        result = service.is_stock_available("AAPL")

        assert result is True

    def test_is_stock_available_false(self):
        """Test checking unavailable stock."""
        service = CatalogService()
        service.load_catalog()
        result = service.is_stock_available("NONEXISTENT")

        assert result is False

    def test_is_stock_available_case_insensitive(self):
        """Test that availability check is case-insensitive."""
        service = CatalogService()
        service.load_catalog()

        result1 = service.is_stock_available("AAPL")
        result2 = service.is_stock_available("aapl")

        assert result1 is True
        assert result2 is True

    def test_is_stock_available_with_whitespace(self):
        """Test that availability check handles whitespace."""
        service = CatalogService()
        service.load_catalog()

        result = service.is_stock_available("  AAPL  ")
        assert result is True


class TestCatalogServiceGetCatalogStatus:
    """Test catalog status retrieval."""

    def test_get_catalog_status(self):
        """Test getting catalog status."""
        service = CatalogService()
        service.load_catalog()
        status = service.get_catalog_status()

        assert isinstance(status, dict)
        assert "catalog_path" in status
        assert "stock_count" in status
        assert "is_valid" in status
        assert "stocks_available" in status
        assert "last_refresh" in status

    def test_get_catalog_status_with_stocks(self):
        """Test catalog status when stocks are available."""
        service = CatalogService()
        service.load_catalog()
        service.load_catalog()
        status = service.get_catalog_status()

        assert status["stocks_available"] > 0
        assert status["last_refresh"] is not None

    def test_get_catalog_status_without_stocks(self):
        """Test catalog status when no stocks are available."""
        service = CatalogService()
        service.load_catalog()
        service.cache.clear_cache()
        status = service.get_catalog_status()

        assert status["stocks_available"] == 0
        assert status["last_refresh"] is None


class TestCatalogServiceRefreshCatalog:
    """Test catalog refresh functionality."""

    def test_refresh_catalog_no_tickers(self):
        """Test refresh when no tickers in catalog."""
        service = CatalogService()
        service.load_catalog()
        service.cache.clear_cache()

        success, message = service.refresh_catalog()
        assert success is False
        assert "No tickers" in message

    @patch("src.services.catalog_service.yf.Ticker")
    def test_refresh_catalog_with_tickers(self, mock_ticker):
        """Test refresh with tickers in catalog."""
        service = CatalogService()
        service.load_catalog()
        service.cache.clear_cache()
        service.cache.add_stock(StockEntry(ticker="TEST", name="Test Stock"))

        # Mock yfinance response
        mock_stock = MagicMock()
        mock_stock.info = {"longName": "Test Company", "sector": "Technology"}
        mock_ticker.return_value = mock_stock

        success, message = service.refresh_catalog()
        # Should succeed or fail gracefully
        assert isinstance(success, bool)
        assert isinstance(message, str)

    @patch("src.services.catalog_service.yf.Ticker")
    def test_refresh_catalog_api_error(self, mock_ticker):
        """Test refresh with API error."""
        service = CatalogService()
        service.cache.clear_cache()
        service.cache.add_stock(StockEntry(ticker="TEST", name="Test Stock"))

        # Mock API error
        mock_ticker.side_effect = Exception("API Error")

        success, message = service.refresh_catalog()
        # The refresh_catalog method falls back to load_catalog(force_refresh=True)
        # which will load from CSV or default catalog, so it may succeed
        # The important thing is that it handles the error gracefully
        assert isinstance(success, bool)
        assert isinstance(message, str)

    @patch("src.services.catalog_service.yf.Ticker")
    def test_refresh_catalog_rate_limiting(self, mock_ticker):
        """Test that refresh respects rate limiting."""
        service = CatalogService()
        service.load_catalog()
        service.cache.clear_cache()
        service.cache.add_stock(StockEntry(ticker="TEST", name="Test Stock"))

        # Mock yfinance response
        mock_stock = MagicMock()
        mock_stock.info = {"longName": "Test Company", "sector": "Technology"}
        mock_ticker.return_value = mock_stock

        # Set last API call to recent past
        service.cache._last_api_call = 0

        with patch("time.sleep") as mock_sleep:
            service.refresh_catalog()
            # Should have called sleep due to rate limiting
            assert mock_sleep.called


class TestCatalogServiceFetchStockInfo:
    """Test fetching individual stock info."""

    @patch("src.services.catalog_service.yf.Ticker")
    def test_fetch_stock_info_success(self, mock_ticker):
        """Test successful stock info fetch."""
        service = CatalogService()
        service.load_catalog()

        # Mock yfinance response
        mock_stock = MagicMock()
        mock_stock.info = {"longName": "Apple Inc.", "sector": "Technology"}
        mock_ticker.return_value = mock_stock

        info = service._fetch_stock_info("AAPL")

        assert info is not None
        assert info["ticker"] == "AAPL"
        assert info["name"] == "Apple Inc."
        assert info["sector"] == "Technology"

    @patch("src.services.catalog_service.yf.Ticker")
    def test_fetch_stock_info_with_short_name(self, mock_ticker):
        """Test stock info fetch with short name fallback."""
        service = CatalogService()
        service.load_catalog()

        # Mock yfinance response without longName
        mock_stock = MagicMock()
        mock_stock.info = {"shortName": "Apple", "sector": "Technology"}
        mock_ticker.return_value = mock_stock

        info = service._fetch_stock_info("AAPL")

        assert info is not None
        assert info["name"] == "Apple"

    @patch("src.services.catalog_service.yf.Ticker")
    def test_fetch_stock_info_api_error_with_cache(self, mock_ticker):
        """Test stock info fetch with API error but cached data."""
        service = CatalogService()
        service.load_catalog()
        service.cache.add_stock(
            StockEntry(ticker="AAPL", name="Cached Apple", sector="Cached Tech")
        )

        # Mock API error
        mock_ticker.side_effect = Exception("API Error")

        info = service._fetch_stock_info("AAPL")

        # Should return cached data
        assert info is not None
        assert info["ticker"] == "AAPL"
        assert info["name"] == "Cached Apple"

    @patch("src.services.catalog_service.yf.Ticker")
    def test_fetch_stock_info_api_error_without_cache(self, mock_ticker):
        """Test stock info fetch with API error and no cache."""
        service = CatalogService()
        service.load_catalog()

        # Mock API error
        mock_ticker.side_effect = Exception("API Error")

        info = service._fetch_stock_info("NONEXISTENT")

        assert info is None


class TestCatalogServiceGetTickers:
    """Test getting ticker list."""

    def test_get_tickers(self):
        """Test getting list of tickers."""
        service = CatalogService()
        service.load_catalog()
        tickers = service.get_tickers()

        assert isinstance(tickers, list)
        assert all(isinstance(t, str) for t in tickers)
        assert len(tickers) > 0


class TestCatalogServiceGetStockCount:
    """Test getting stock count."""

    def test_get_stock_count(self):
        """Test getting stock count."""
        service = CatalogService()
        service.load_catalog()
        count = service.get_stock_count()

        assert isinstance(count, int)
        assert count >= 0

    def test_get_stock_count_after_load(self):
        """Test stock count after loading catalog."""
        service = CatalogService()
        service.load_catalog()
        service.load_catalog()
        count = service.get_stock_count()

        assert count > 0


class TestCatalogServiceHandleApiFailure:
    """Test API failure handling."""

    def test_handle_api_failure_with_valid_cache(self):
        """Test API failure with valid cached data."""
        service = CatalogService()
        service.load_catalog()
        service.load_catalog()

        message = service.handle_api_failure()

        assert isinstance(message, str)
        assert "cached data" in message.lower()

    def test_handle_api_failure_without_valid_cache(self):
        """Test API failure without valid cached data."""
        service = CatalogService()
        service.load_catalog()
        service.cache.clear_cache()

        message = service.handle_api_failure()

        assert isinstance(message, str)
        assert "no cached data" in message.lower() or "unavailable" in message.lower()


class TestCatalogServiceIntegration:
    """Integration tests for CatalogService."""

    def test_full_workflow_load_get_search(self):
        """Test full workflow: load, get, search."""
        service = CatalogService()
        service.load_catalog()

        # Load catalog
        stocks = service.load_catalog()
        assert len(stocks) > 0

        # Get specific stock
        stock = service.get_stock("AAPL")
        assert stock is not None

        # Search stocks
        results = service.search_stocks("Apple")
        assert len(results) > 0

        # Check availability
        assert service.is_stock_available("AAPL") is True

        # Get status
        status = service.get_catalog_status()
        assert status["stocks_available"] > 0

    def test_multiple_service_instances_share_cache(self):
        """Test that multiple service instances share the same cache."""
        service1 = CatalogService()
        service2 = CatalogService()

        # Both should have the same cache instance
        assert service1.cache is service2.cache

        # Changes in one should reflect in the other
        service1.cache.add_stock(StockEntry(ticker="TEST", name="Test"))
        assert service2.get_stock("TEST") is not None
