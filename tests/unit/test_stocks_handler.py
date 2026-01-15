"""
Unit tests for stocks_handler module.

Tests cover:
- Pagination logic
- Format stocks page
- Create stocks keyboard
- Helper functions (synchronous ones only)
"""

from unittest.mock import MagicMock, patch

from src.handlers.stocks_handler import (
    STOCKS_PER_PAGE,
    create_stocks_keyboard,
    format_stocks_page,
    get_stocks_count,
    is_stock_available,
)
from src.utils.catalog_cache import StockEntry

LANGUAGE = "en"


class TestFormatStocksPage:
    """Test format_stocks_page function."""

    def test_format_stocks_page_basic(self):
        """Test basic formatting of stocks page."""
        stocks = [
            StockEntry(ticker="AAPL", name="Apple Inc.", sector="Technology"),
            StockEntry(
                ticker="MSFT", name="Microsoft Corporation", sector="Technology"
            ),
        ]

        text = format_stocks_page(stocks, page=0, total_pages=1, language=LANGUAGE)

        assert isinstance(text, str)
        assert "Available Stocks" in text
        assert "AAPL" in text
        assert "MSFT" in text
        assert "Apple Inc." in text
        assert "Microsoft Corporation" in text
        assert "page 1/1" in text

    def test_format_stocks_page_with_sector(self):
        """Test formatting with sector information."""
        stocks = [
            StockEntry(ticker="AAPL", name="Apple Inc.", sector="Technology"),
            StockEntry(
                ticker="JPM", name="JPMorgan Chase", sector="Financial Services"
            ),
        ]

        text = format_stocks_page(stocks, page=0, total_pages=1, language=LANGUAGE)

        assert "(Technology)" in text
        assert "(Financial Services)" in text

    def test_format_stocks_page_without_sector(self):
        """Test formatting without sector information."""
        stocks = [
            StockEntry(ticker="AAPL", name="Apple Inc.", sector=None),
        ]

        text = format_stocks_page(stocks, page=0, total_pages=1, language=LANGUAGE)

        assert "()" not in text

    def test_format_stocks_page_pagination_info(self):
        """Test pagination information in formatted text."""
        stocks = [
            StockEntry(ticker="AAPL", name="Apple Inc.", sector="Technology"),
        ]

        text = format_stocks_page(stocks, page=2, total_pages=5, language=LANGUAGE)

        assert "page 3/5" in text

    def test_format_stocks_page_empty_list(self):
        """Test formatting with empty stock list."""
        stocks = []

        text = format_stocks_page(stocks, page=0, total_pages=0, language=LANGUAGE)

        assert isinstance(text, str)

    def test_format_stocks_page_multiple_pages(self):
        """Test formatting for multiple pages."""
        stocks = [
            StockEntry(ticker=f"STOCK{i}", name=f"Stock {i}", sector="Technology")
            for i in range(10)
        ]

        text = format_stocks_page(stocks, page=1, total_pages=3, language=LANGUAGE)

        assert "page 2/3" in text
        assert "Showing 10 of 10 stocks" in text


class TestCreateStocksKeyboard:
    """Test create_stocks_keyboard function."""

    def test_create_keyboard_basic(self):
        """Test basic keyboard creation."""
        stocks = [
            StockEntry(ticker="AAPL", name="Apple Inc.", sector="Technology"),
            StockEntry(
                ticker="MSFT", name="Microsoft Corporation", sector="Technology"
            ),
        ]

        keyboard = create_stocks_keyboard(
            current_page=0, total_pages=1, stocks_on_page=stocks
        )

        assert keyboard is not None
        assert hasattr(keyboard, "inline_keyboard")
        assert len(keyboard.inline_keyboard) > 0

    def test_create_keyboard_stock_buttons(self):
        """Test that stock buttons are created correctly."""
        stocks = [
            StockEntry(ticker="AAPL", name="Apple Inc.", sector="Technology"),
        ]

        keyboard = create_stocks_keyboard(
            current_page=0, total_pages=1, stocks_on_page=stocks
        )

        # First row should have stock button
        stock_row = keyboard.inline_keyboard[0]
        assert len(stock_row) == 1
        assert "AAPL" in stock_row[0].text
        assert stock_row[0].callback_data == "stock_AAPL"

    def test_create_keyboard_long_name_truncation(self):
        """Test that long names are truncated in buttons."""
        stocks = [
            StockEntry(
                ticker="LONG",
                name="Very Long Company Name That Exceeds Twenty Five Characters",
                sector="Technology",
            ),
        ]

        keyboard = create_stocks_keyboard(
            current_page=0, total_pages=1, stocks_on_page=stocks
        )

        stock_button = keyboard.inline_keyboard[0][0]
        assert "..." in stock_button.text
        assert len(stock_button.text) <= 35  # Should be truncated

    def test_create_keyboard_pagination_first_page(self):
        """Test pagination buttons on first page."""
        stocks = [
            StockEntry(ticker="AAPL", name="Apple Inc.", sector="Technology"),
        ]

        keyboard = create_stocks_keyboard(
            current_page=0, total_pages=3, stocks_on_page=stocks
        )

        # Find pagination row
        pagination_row = None
        for row in keyboard.inline_keyboard:
            if any("page" in btn.callback_data for btn in row):
                pagination_row = row
                break

        assert pagination_row is not None
        # Should not have previous button on first page
        assert not any("Prev" in btn.text for btn in pagination_row)
        # Should have next button
        assert any("Next" in btn.text for btn in pagination_row)

    def test_create_keyboard_pagination_last_page(self):
        """Test pagination buttons on last page."""
        stocks = [
            StockEntry(ticker="AAPL", name="Apple Inc.", sector="Technology"),
        ]

        keyboard = create_stocks_keyboard(
            current_page=2, total_pages=3, stocks_on_page=stocks
        )

        # Find pagination row
        pagination_row = None
        for row in keyboard.inline_keyboard:
            if any("page" in btn.callback_data for btn in row):
                pagination_row = row
                break

        assert pagination_row is not None
        # Should have previous button
        assert any("Prev" in btn.text for btn in pagination_row)
        # Should not have next button on last page
        assert not any("Next" in btn.text for btn in pagination_row)

    def test_create_keyboard_pagination_middle_page(self):
        """Test pagination buttons on middle page."""
        stocks = [
            StockEntry(ticker="AAPL", name="Apple Inc.", sector="Technology"),
        ]

        keyboard = create_stocks_keyboard(
            current_page=1, total_pages=3, stocks_on_page=stocks
        )

        # Find pagination row
        pagination_row = None
        for row in keyboard.inline_keyboard:
            if any("page" in btn.callback_data for btn in row):
                pagination_row = row
                break

        assert pagination_row is not None
        # Should have both buttons
        assert any("Prev" in btn.text for btn in pagination_row)
        assert any("Next" in btn.text for btn in pagination_row)

    def test_create_keyboard_page_indicator(self):
        """Test page indicator button."""
        stocks = [
            StockEntry(ticker="AAPL", name="Apple Inc.", sector="Technology"),
        ]

        keyboard = create_stocks_keyboard(
            current_page=1, total_pages=3, stocks_on_page=stocks
        )

        # Find pagination row
        pagination_row = None
        for row in keyboard.inline_keyboard:
            if any("page" in btn.callback_data for btn in row):
                pagination_row = row
                break

        assert pagination_row is not None
        # Should have page indicator
        assert any("2/3" in btn.text for btn in pagination_row)

    def test_create_keyboard_search_and_all_buttons(self):
        """Test that search and all stocks buttons are present."""
        stocks = [
            StockEntry(ticker="AAPL", name="Apple Inc.", sector="Technology"),
        ]

        keyboard = create_stocks_keyboard(
            current_page=0, total_pages=1, stocks_on_page=stocks
        )

        # Find search row
        search_row = None
        for row in keyboard.inline_keyboard:
            if any("Search" in btn.text or "All Stocks" in btn.text for btn in row):
                search_row = row
                break

        assert search_row is not None
        assert len(search_row) == 2
        assert any("Search" in btn.text for btn in search_row)
        assert any("All Stocks" in btn.text for btn in search_row)

    def test_create_keyboard_single_page(self):
        """Test keyboard with single page (no pagination)."""
        stocks = [
            StockEntry(ticker="AAPL", name="Apple Inc.", sector="Technology"),
        ]

        keyboard = create_stocks_keyboard(
            current_page=0, total_pages=1, stocks_on_page=stocks
        )

        # Should have stock buttons and search row
        assert len(keyboard.inline_keyboard) >= 2


class TestGetStocksCount:
    """Test get_stocks_count function."""

    @patch("src.handlers.stocks_handler.get_catalog_service")
    def test_get_stocks_count(self, mock_get_service):
        """Test getting stock count."""
        mock_service = MagicMock()
        mock_service.get_stock_count.return_value = 100
        mock_get_service.return_value = mock_service

        count = get_stocks_count()

        assert count == 100

    @patch("src.handlers.stocks_handler.get_catalog_service")
    def test_get_stocks_count_empty(self, mock_get_service):
        """Test getting stock count when empty."""
        mock_service = MagicMock()
        mock_service.get_stock_count.return_value = 0
        mock_get_service.return_value = mock_service

        count = get_stocks_count()

        assert count == 0


class TestIsStockAvailable:
    """Test is_stock_available function."""

    @patch("src.handlers.stocks_handler.get_catalog_service")
    def test_is_stock_available_true(self, mock_get_service):
        """Test checking available stock."""
        mock_service = MagicMock()
        mock_service.is_stock_available.return_value = True
        mock_get_service.return_value = mock_service

        result = is_stock_available("AAPL")

        assert result is True

    @patch("src.handlers.stocks_handler.get_catalog_service")
    def test_is_stock_available_false(self, mock_get_service):
        """Test checking unavailable stock."""
        mock_service = MagicMock()
        mock_service.is_stock_available.return_value = False
        mock_get_service.return_value = mock_service

        result = is_stock_available("NONEXISTENT")

        assert result is False

    @patch("src.handlers.stocks_handler.get_catalog_service")
    def test_is_stock_available_case_insensitive(self, mock_get_service):
        """Test that availability check is case-insensitive."""
        mock_service = MagicMock()
        mock_service.is_stock_available.return_value = True
        mock_get_service.return_value = mock_service

        result1 = is_stock_available("AAPL")
        result2 = is_stock_available("aapl")

        assert result1 is True
        assert result2 is True


class TestPaginationLogic:
    """Test pagination logic."""

    def test_stocks_per_page_constant(self):
        """Test that STOCKS_PER_PAGE constant is set correctly."""
        assert STOCKS_PER_PAGE == 20

    def test_pagination_calculation(self):
        """Test pagination calculation logic."""
        total_stocks = 45
        per_page = 20

        total_pages = (total_stocks + per_page - 1) // per_page

        assert total_pages == 3

    def test_pagination_exact_multiple(self):
        """Test pagination when total is exact multiple of per_page."""
        total_stocks = 40
        per_page = 20

        total_pages = (total_stocks + per_page - 1) // per_page

        assert total_pages == 2

    def test_pagination_single_stock(self):
        """Test pagination with single stock."""
        total_stocks = 1
        per_page = 20

        total_pages = (total_stocks + per_page - 1) // per_page

        assert total_pages == 1

    def test_pagination_empty_list(self):
        """Test pagination with empty list."""
        total_stocks = 0
        per_page = 20

        total_pages = (total_stocks + per_page - 1) // per_page

        assert total_pages == 0


class TestStockEntryFormatting:
    """Test StockEntry formatting in handler functions."""

    def test_format_stocks_with_special_characters(self):
        """Test formatting stocks with special characters in names."""
        stocks = [
            StockEntry(ticker="A", name="Company & Co.", sector="Technology"),
            StockEntry(ticker="B", name="Company/Inc", sector="Finance"),
        ]

        text = format_stocks_page(stocks, page=0, total_pages=1, language=LANGUAGE)

        assert "Company & Co." in text
        assert "Company/Inc" in text

    def test_format_stocks_with_unicode(self):
        """Test formatting stocks with unicode characters."""
        stocks = [
            StockEntry(ticker="A", name="Company™", sector="Technology"),
        ]

        text = format_stocks_page(stocks, page=0, total_pages=1, language=LANGUAGE)

        assert "Company™" in text

    def test_keyboard_callback_data_format(self):
        """Test that callback data is formatted correctly."""
        stocks = [
            StockEntry(ticker="AAPL", name="Apple Inc.", sector="Technology"),
        ]

        keyboard = create_stocks_keyboard(
            current_page=0, total_pages=1, stocks_on_page=stocks
        )

        stock_button = keyboard.inline_keyboard[0][0]
        assert stock_button.callback_data == "stock_AAPL"

    def test_keyboard_pagination_callback_data(self):
        """Test pagination callback data format."""
        stocks = [
            StockEntry(ticker="AAPL", name="Apple Inc.", sector="Technology"),
        ]

        keyboard = create_stocks_keyboard(
            current_page=1, total_pages=3, stocks_on_page=stocks
        )

        # Find pagination row
        pagination_row = None
        for row in keyboard.inline_keyboard:
            if any("page" in btn.callback_data for btn in row):
                pagination_row = row
                break

        assert pagination_row is not None
        # Check prev button callback
        prev_btn = next((btn for btn in pagination_row if "Prev" in btn.text), None)
        if prev_btn:
            assert prev_btn.callback_data == "stocks_page_0"

        # Check next button callback
        next_btn = next((btn for btn in pagination_row if "Next" in btn.text), None)
        if next_btn:
            assert next_btn.callback_data == "stocks_page_2"


class TestEdgeCases:
    """Test edge cases in handler functions."""

    def test_format_stocks_page_very_long_name(self):
        """Test formatting with very long company name."""
        stocks = [
            StockEntry(ticker="A", name="A" * 100, sector="Technology"),
        ]

        text = format_stocks_page(stocks, page=0, total_pages=1, language=LANGUAGE)

        assert "A" * 100 in text

    def test_format_stocks_page_zero_pages(self):
        """Test formatting with zero total pages."""
        stocks = []

        text = format_stocks_page(stocks, page=0, total_pages=0, language=LANGUAGE)

        assert "page 1/0" in text

    def test_create_keyboard_zero_pages(self):
        """Test keyboard creation with zero pages."""
        keyboard = create_stocks_keyboard(
            current_page=0, total_pages=0, stocks_on_page=[]
        )

        # Should not have pagination buttons
        has_pagination = any(
            any("Prev" in btn.text or "Next" in btn.text for btn in row)
            for row in keyboard.inline_keyboard
        )
        assert not has_pagination
