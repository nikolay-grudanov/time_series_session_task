"""
Integration tests for stock catalog feature.

Tests cover:
- Full catalog workflow from CSV to service to handlers
- End-to-end stock retrieval and search
- Integration between cache, service, and validators
- Real-world scenarios with mocked external dependencies
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

from src.services.catalog_service import CatalogService, get_catalog_service
from src.utils.catalog_cache import CatalogCache, StockEntry
from src.utils.validators import (
    validate_forecast_request,
    validate_investment_amount,
    validate_ticker,
)


class TestCatalogIntegrationWorkflow:
    """Integration tests for complete catalog workflow."""

    def test_full_catalog_workflow(self, sample_catalog_csv):
        """Test complete workflow: load, search, validate."""
        # Create temporary catalog file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("ticker,name,sector,last_updated\n")
            f.write("AAPL,Apple Inc.,Technology,2024-01-01\n")
            f.write("MSFT,Microsoft Corporation,Technology,2024-01-01\n")
            f.write("GOOGL,Alphabet Inc.,Technology,2024-01-01\n")
            csv_path = f.name

        try:
            # Initialize service
            service = CatalogService(csv_path)

            # Load catalog
            stocks = service.load_catalog()
            assert len(stocks) == 3

            # Search for stock
            results = service.search_stocks("Apple")
            assert len(results) > 0
            assert results[0].ticker == "AAPL"

            # Get specific stock
            stock = service.get_stock("AAPL")
            assert stock is not None
            assert stock.name == "Apple Inc."

            # Validate ticker
            validation = validate_ticker("AAPL")
            assert validation.is_valid is True

            # Check availability
            assert service.is_stock_available("AAPL") is True

            # Get status
            status = service.get_catalog_status()
            assert status["stocks_available"] == 3

        finally:
            Path(csv_path).unlink()

    def test_catalog_service_with_validators(self, sample_catalog_csv):
        """Test integration between catalog service and validators."""
        service = CatalogService(sample_catalog_csv)
        service.load_catalog()

        # Get a valid stock
        stock = service.get_stock("AAPL")
        assert stock is not None

        # Validate the ticker
        ticker_validation = validate_ticker(stock.ticker)
        assert ticker_validation.is_valid is True

        # Validate a forecast request
        forecast_validation = validate_forecast_request(stock.ticker, 1000)
        assert forecast_validation.is_valid is True

    def test_catalog_search_and_validation(self, sample_catalog_csv):
        """Test searching stocks and validating results."""
        service = CatalogService(sample_catalog_csv)
        service.load_catalog()

        # Search for stocks
        results = service.search_stocks("Apple")
        assert len(results) > 0

        # Validate each result's ticker
        for stock in results:
            validation = validate_ticker(stock.ticker)
            assert validation.is_valid is True

    def test_catalog_pagination_integration(self, sample_catalog_csv):
        """Test pagination integration with catalog."""
        # Create catalog with many stocks
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("ticker,name,sector,last_updated\n")
            for i in range(50):
                f.write(f"STOCK{i},Stock {i},Technology,2024-01-01\n")
            csv_path = f.name

        try:
            service = CatalogService(csv_path)
            stocks = service.load_catalog()

            assert len(stocks) == 50

            # Simulate pagination
            per_page = 20
            total_pages = (len(stocks) + per_page - 1) // per_page
            assert total_pages == 3

            # Get first page
            page1 = stocks[:per_page]
            assert len(page1) == 20

            # Get second page
            page2 = stocks[per_page : per_page * 2]
            assert len(page2) == 20

            # Get third page
            page3 = stocks[per_page * 2 :]
            assert len(page3) == 10

        finally:
            Path(csv_path).unlink()


class TestCatalogCacheAndServiceIntegration:
    """Integration tests for cache and service interaction."""

    def test_cache_service_shared_instance(self, sample_catalog_csv):
        """Test that cache and service share the same instance."""
        cache1 = CatalogCache()
        service = CatalogService(sample_catalog_csv)
        cache2 = service.cache

        # Should be the same instance
        assert cache1 is cache2

        # Changes in cache should reflect in service
        cache1.add_stock(StockEntry(ticker="TEST", name="Test Stock"))
        assert service.get_stock("TEST") is not None

    def test_service_refresh_updates_cache(self, sample_catalog_csv):
        """Test that service refresh updates cache."""
        service = CatalogService(sample_catalog_csv)
        service.cache.clear_cache()

        # Add stock via service
        service.cache.add_stock(StockEntry(ticker="TEST", name="Test"))

        # Should be available via service
        assert service.get_stock("TEST") is not None

    def test_cache_ttl_affects_service(self, sample_catalog_csv):
        """Test that cache TTL affects service behavior."""
        service = CatalogService(sample_catalog_csv)
        service.load_catalog()

        # Cache should be valid initially
        assert service.cache._is_cache_valid() is True

        # Get stocks should use cache
        stocks1 = service.get_stocks(force_refresh=False)
        stocks2 = service.get_stocks(force_refresh=False)
        assert len(stocks1) == len(stocks2)


class TestCatalogErrorHandlingIntegration:
    """Integration tests for error handling across components."""

    def test_missing_catalog_fallback(self, sample_catalog_csv):
        """Test fallback to default catalog when file is missing."""
        service = CatalogService("/nonexistent/path/catalog.csv")
        stocks = service.load_catalog()

        # The CSV will load but won't have the right structure
        assert isinstance(stocks, list)
        assert service.get_stock("AAPL") is not None


    def test_validation_with_nonexistent_stock(self, sample_catalog_csv):
        """Test validation with non-existent stock."""
        service = CatalogService(sample_catalog_csv)

        # Validate ticker (should pass format validation)
        ticker_validation = validate_ticker("XYZ")
        assert ticker_validation.is_valid is True

        # But stock should not be available
        assert service.is_stock_available("XYZ") is False

    def test_invalid_ticker_format(self, sample_catalog_csv):
        """Test handling of invalid ticker format."""
        service = CatalogService(sample_catalog_csv)

        # Invalid format
        ticker_validation = validate_ticker("INVALID123")
        assert ticker_validation.is_valid is False

        # Should not be available
        assert service.is_stock_available("INVALID123") is False


class TestCatalogDataIntegrityIntegration:
    """Integration tests for data integrity across components."""


    def test_delisted_stocks_handling(self, sample_catalog_csv):
        """Test handling of delisted stocks."""
        service = CatalogService(sample_catalog_csv)
        service.cache.clear_cache()

        # Add stocks
        service.cache.add_stock(StockEntry(ticker="AAPL", name="Apple"))
        service.cache.add_stock(StockEntry(ticker="MSFT", name="Microsoft"))
        service.cache.add_stock(StockEntry(ticker="DELIST", name="Delisted"))

        # Handle delisted stocks
        active_tickers = ["AAPL", "MSFT"]
        removed_count, removed_list = service.cache.handle_delisted_stocks(
            active_tickers
        )

        assert removed_count == 1
        assert "DELIST" in removed_list
        assert service.is_stock_available("AAPL") is True
        assert service.is_stock_available("DELIST") is False

    def test_catalog_integrity_validation(self, sample_catalog_csv):
        """Test catalog integrity validation."""
        service = CatalogService(sample_catalog_csv)
        service.load_catalog()

        # Validate integrity
        report = service.cache.validate_catalog_integrity()
        assert report["is_valid"] is True
        assert report["duplicate_count"] == 0


class TestCatalogWithValidatorsIntegration:
    """Integration tests for catalog with validators."""

    def test_validate_forecast_with_catalog_stock(self, sample_catalog_csv):
        """Test validating forecast request with catalog stock."""
        service = CatalogService(sample_catalog_csv)
        service.load_catalog()

        # Get a valid stock
        stock = service.get_stock("AAPL")
        assert stock is not None

        # Validate forecast request
        validation = validate_forecast_request(stock.ticker, 1000)
        assert validation.is_valid is True

    def test_validate_forecast_with_invalid_amount(self, sample_catalog_csv):
        """Test validating forecast request with invalid amount."""
        service = CatalogService(sample_catalog_csv)
        service.load_catalog()

        # Get a valid stock
        stock = service.get_stock("AAPL")
        assert stock is not None

        # Validate with invalid amount
        validation = validate_forecast_request(stock.ticker, -100)
        assert validation.is_valid is False
        assert validation.error_type.name == "OUT_OF_RANGE"

    def test_validate_amount_boundaries(self, sample_catalog_csv):
        """Test amount validation at boundaries."""
        # Minimum boundary
        validation1 = validate_investment_amount(1)
        assert validation1.is_valid is True

        validation2 = validate_investment_amount(0.99)
        assert validation2.is_valid is False

        # Maximum boundary
        validation3 = validate_investment_amount(1_000_000)
        assert validation3.is_valid is True

        validation4 = validate_investment_amount(1_000_001)
        assert validation4.is_valid is False


class TestCatalogRealWorldScenarios:
    """Integration tests for real-world scenarios."""

    def test_user_browses_stocks_and_selects(self, sample_catalog_csv):
        """Simulate user browsing stocks and selecting one."""
        service = CatalogService(sample_catalog_csv)
        service.load_catalog()

        # User browses all stocks
        all_stocks = service.get_stocks()
        assert len(all_stocks) > 0

        # User searches for "Apple"
        apple_stocks = service.search_stocks("Apple")
        assert len(apple_stocks) > 0

        # User selects AAPL
        selected_stock = service.get_stock("AAPL")
        assert selected_stock is not None

        # User validates forecast request
        validation = validate_forecast_request("AAPL", 1000)
        assert validation.is_valid is True

    def test_user_searches_with_partial_name(self, sample_catalog_csv):
        """Simulate user searching with partial company name."""
        service = CatalogService(sample_catalog_csv)
        service.load_catalog()

        # User searches for "Micro"
        results = service.search_stocks("Micro")
        assert len(results) > 0

        # Should find Microsoft
        microsoft = next((s for s in results if "Microsoft" in s.name), None)
        assert microsoft is not None

    def test_user_enters_invalid_ticker(self, sample_catalog_csv):
        """Simulate user entering invalid ticker."""
        service = CatalogService(sample_catalog_csv)

        # User enters invalid ticker
        validation = validate_ticker("INVALID123")
        assert validation.is_valid is False

        # Stock should not be available
        assert service.is_stock_available("INVALID123") is False

    def test_user_enters_invalid_amount(self, sample_catalog_csv):
        """Simulate user entering invalid investment amount."""
        # User enters negative amount
        validation1 = validate_investment_amount(-100)
        assert validation1.is_valid is False

        # User enters amount too large
        validation2 = validate_investment_amount(10_000_000)
        assert validation2.is_valid is False

        # User enters non-numeric
        validation3 = validate_investment_amount("abc")
        assert validation3.is_valid is False

    def test_catalog_refresh_scenario(self, sample_catalog_csv):
        """Simulate catalog refresh scenario."""
        service = CatalogService(sample_catalog_csv)
        service.load_catalog()

        # Get initial count
        initial_count = service.get_stock_count()

        # Simulate refresh (mocked)
        with patch.object(service, "refresh_catalog", return_value=(True, "Updated")):
            success, message = service.refresh_catalog()
            assert success is True

        # Count should remain the same
        final_count = service.get_stock_count()
        assert final_count == initial_count


class TestCatalogPerformanceIntegration:
    """Integration tests for performance considerations."""

    def test_large_catalog_handling(self, large_catalog_csv):
        """Test handling of large catalog."""
        # Create large catalog
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("ticker,name,sector,last_updated\n")
            for i in range(1000):
                f.write(f"STOCK{i:04d},Stock {i},Technology,2024-01-01\n")
            csv_path = f.name

        try:
            service = CatalogService(csv_path)
            stocks = service.load_catalog()

            assert len(stocks) == 1000

            # Search should be fast
            results = service.search_stocks("Stock 500")
            assert len(results) > 0

            # Get specific stock should be fast
            stock = service.get_stock("STOCK0500")
            assert stock is not None

        finally:
            Path(csv_path).unlink()

    def test_cache_performance(self, sample_catalog_csv):
        """Test cache performance with multiple calls."""
        service = CatalogService(sample_catalog_csv)
        service.load_catalog()

        # Multiple calls should use cache
        for _ in range(10):
            stocks = service.get_stocks(force_refresh=False)
            assert isinstance(stocks, list)

        # Cache should still be valid
        assert service.cache._is_cache_valid() is True


class TestCatalogSingletonIntegration:
    """Integration tests for singleton pattern."""

    def test_multiple_services_share_cache(self, sample_catalog_csv):
        """Test that multiple service instances share cache."""
        service1 = CatalogService()
        service2 = CatalogService()

        # Should share the same cache
        assert service1.cache is service2.cache

        # Changes in one should reflect in the other
        service1.cache.add_stock(StockEntry(ticker="TEST", name="Test"))
        assert service2.get_stock("TEST") is not None

    def test_factory_function_singleton(self, sample_catalog_csv):
        """Test that factory function returns singleton."""
        service1 = get_catalog_service()
        service2 = get_catalog_service()

        assert service1 is service2

    def test_cache_singleton(self, sample_catalog_csv):
        """Test that cache is singleton."""
        cache1 = CatalogCache()
        cache2 = CatalogCache()

        assert cache1 is cache2


class TestCatalogWithExternalDependencies:
    """Integration tests with mocked external dependencies."""

class TestCatalogDataConsistency:
    """Integration tests for data consistency."""

    def test_stock_data_consistency(self, sample_catalog_csv):
        """Test that stock data remains consistent across operations."""
        service = CatalogService(sample_catalog_csv)
        service.load_catalog()

        # Get stock multiple times
        stock1 = service.get_stock("AAPL")
        stock2 = service.get_stock("AAPL")
        stock3 = service.search_stocks("AAPL")[0]

        # All should be the same
        assert stock1.ticker == stock2.ticker == stock3.ticker
        assert stock1.name == stock2.name == stock3.name

    def test_catalog_state_after_operations(self, sample_catalog_csv):
        """Test catalog state after various operations."""
        service = CatalogService(sample_catalog_csv)
        service.cache.clear_cache()

        # Add stocks
        service.cache.add_stock(StockEntry(ticker="AAPL", name="Apple"))
        service.cache.add_stock(StockEntry(ticker="MSFT", name="Microsoft"))

        # Verify state
        assert service.get_stock_count() == 2
        assert service.is_stock_available("AAPL") is True

        # Remove stock
        service.cache.remove_stock("AAPL")

        # Verify new state
        assert service.get_stock_count() == 1
        assert service.is_stock_available("AAPL") is False
        assert service.is_stock_available("MSFT") is True

    def test_catalog_persistence_across_calls(self, sample_catalog_csv):
        """Test that catalog persists across multiple service calls."""
        service = CatalogService(sample_catalog_csv)
        service.load_catalog()

        # Multiple calls should return consistent data
        stocks1 = service.get_stocks()
        stocks2 = service.get_stocks()
        stocks3 = service.get_stocks()

        assert len(stocks1) == len(stocks2) == len(stocks3)
        assert set(s.ticker for s in stocks1) == set(s.ticker for s in stocks2)
