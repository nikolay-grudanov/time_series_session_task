"""
Pytest configuration and shared fixtures for stock catalog tests.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.services.catalog_service import CatalogService
from src.utils.catalog_cache import CatalogCache, StockEntry


@pytest.fixture
def sample_catalog_csv():
    """Create a temporary CSV file with sample stock data."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("ticker,name,sector,last_updated\n")
        f.write("AAPL,Apple Inc.,Technology,2024-01-01\n")
        f.write("MSFT,Microsoft Corporation,Technology,2024-01-01\n")
        f.write("GOOGL,Alphabet Inc.,Technology,2024-01-01\n")
        f.write("AMZN,Amazon.com Inc.,Consumer Cyclical,2024-01-01\n")
        f.write("TSLA,Tesla Inc.,Consumer Cyclical,2024-01-01\n")
        f.write("META,Meta Platforms Inc.,Technology,2024-01-01\n")
        f.write("NVDA,NVIDIA Corporation,Technology,2024-01-01\n")
        f.write("JPM,JPMorgan Chase & Co.,Financial Services,2024-01-01\n")
        f.write("V,Visa Inc.,Financial Services,2024-01-01\n")
        f.write("JNJ,Johnson & Johnson,Healthcare,2024-01-01\n")
        csv_path = f.name

    yield csv_path

    # Cleanup
    Path(csv_path).unlink()


@pytest.fixture
def empty_catalog_csv():
    """Create a temporary empty CSV file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("ticker,name,sector,last_updated\n")
        csv_path = f.name

    yield csv_path

    # Cleanup
    Path(csv_path).unlink()


@pytest.fixture
def corrupted_catalog_csv():
    """Create a temporary corrupted CSV file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("invalid,csv,content\n")
        f.write("not,a,valid,catalog\n")
        csv_path = f.name

    yield csv_path

    # Cleanup
    Path(csv_path).unlink()


@pytest.fixture
def large_catalog_csv():
    """Create a temporary CSV file with many stocks."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("ticker,name,sector,last_updated\n")
        for i in range(100):
            f.write(f"STOCK{i:03d},Stock {i},Technology,2024-01-01\n")
        csv_path = f.name

    yield csv_path

    # Cleanup
    Path(csv_path).unlink()


@pytest.fixture
def sample_stocks():
    """Create a list of sample StockEntry objects."""
    return [
        StockEntry(ticker="AAPL", name="Apple Inc.", sector="Technology"),
        StockEntry(ticker="MSFT", name="Microsoft Corporation", sector="Technology"),
        StockEntry(ticker="GOOGL", name="Alphabet Inc.", sector="Technology"),
        StockEntry(ticker="AMZN", name="Amazon.com Inc.", sector="Consumer Cyclical"),
        StockEntry(ticker="TSLA", name="Tesla Inc.", sector="Consumer Cyclical"),
    ]


@pytest.fixture
def catalog_cache(sample_catalog_csv):
    """Create a CatalogCache instance with sample data."""
    cache = CatalogCache(sample_catalog_csv)
    cache.load_catalog()
    return cache


@pytest.fixture
def catalog_service(sample_catalog_csv):
    """Create a CatalogService instance with sample data."""
    service = CatalogService(sample_catalog_csv)
    service.load_catalog()
    return service


@pytest.fixture
def empty_catalog_cache():
    """Create an empty CatalogCache instance."""
    cache = CatalogCache()
    cache.clear_cache()
    return cache


@pytest.fixture
def mock_yfinance_ticker():
    """Create a mock yfinance Ticker object."""
    mock_stock = MagicMock()
    mock_stock.info = {
        "longName": "Test Company Inc.",
        "shortName": "Test Company",
        "sector": "Technology",
    }
    return mock_stock


@pytest.fixture
def mock_yfinance_ticker_multiple():
    """Create multiple mock yfinance Ticker objects."""
    mock_stocks = {}
    for ticker in ["AAPL", "MSFT", "GOOGL"]:
        mock_stock = MagicMock()
        mock_stock.info = {
            "longName": f"{ticker} Company Inc.",
            "shortName": ticker,
            "sector": "Technology",
        }
        mock_stocks[ticker] = mock_stock
    return mock_stocks


@pytest.fixture(autouse=True)
def reset_catalog_cache():
    """Reset CatalogCache singleton before each test."""
    # Clear the singleton instance
    CatalogCache._instance = None
    CatalogCache._initialized = False
    yield
    # Reset after test
    CatalogCache._instance = None
    CatalogCache._initialized = False


@pytest.fixture
def mock_message():
    """Create a mock Telegram message object."""
    message = MagicMock()
    message.from_user.id = 123456789
    message.from_user.username = "testuser"
    message.answer = MagicMock()
    return message


@pytest.fixture
def mock_callback_query():
    """Create a mock Telegram callback query object."""
    callback = MagicMock()
    callback.data = "test_callback"
    callback.message = MagicMock()
    callback.message.edit_text = MagicMock()
    callback.answer = MagicMock()
    return callback


@pytest.fixture
def mock_inline_keyboard_button():
    """Create a mock inline keyboard button."""
    button = MagicMock()
    button.text = "Test Button"
    button.callback_data = "test_data"
    return button


@pytest.fixture
def mock_inline_keyboard_markup():
    """Create a mock inline keyboard markup."""
    markup = MagicMock()
    markup.inline_keyboard = []
    return markup


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "slow: marks tests as slow running")
    config.addinivalue_line(
        "markers", "external: marks tests that require external dependencies"
    )


# Custom assertions
def assert_stock_entry_equal(stock1, stock2):
    """Assert that two StockEntry objects are equal."""
    assert stock1.ticker == stock2.ticker
    assert stock1.name == stock2.name
    assert stock1.sector == stock2.sector


def assert_validation_result_valid(result):
    """Assert that a ValidationResult is valid."""
    assert result.is_valid is True
    assert result.error_type is None
    assert result.error_message is None


def assert_validation_result_invalid(result, error_type=None):
    """Assert that a ValidationResult is invalid."""
    assert result.is_valid is False
    if error_type:
        assert result.error_type == error_type
    assert result.error_message is not None
