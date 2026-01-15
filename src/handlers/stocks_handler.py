"""
Telegram bot handler for /stocks command.
Displays paginated list of available stock tickers.
"""

import logging
from math import ceil
from typing import Any

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from src.i18n.constants import MessageKey
from src.i18n.loader import MessageLoader
from src.i18n.middleware import get_language_middleware
from src.services.catalog_service import get_catalog_service
from src.utils.catalog_cache import StockEntry

logger = logging.getLogger(__name__)

# Pagination settings (per FR-002)
STOCKS_PER_PAGE = 20

# Router for stocks-related handlers
router = Router()

# Initialize i18n components
_message_loader: MessageLoader | None = None
_middleware = None


def _get_loader() -> MessageLoader:
    """Get or create MessageLoader singleton."""
    global _message_loader
    if _message_loader is None:
        _message_loader = MessageLoader()
    return _message_loader


async def _get_user_language(user_id: int) -> str:
    """Get user's preferred language."""
    middleware = get_language_middleware()
    return await middleware.get_user_language(user_id)


def create_stocks_keyboard(
    current_page: int, total_pages: int, stocks_on_page: list[StockEntry]
) -> InlineKeyboardMarkup:
    """
    Create inline keyboard with stock list and pagination buttons.

    Args:
        current_page: Current page number (0-based)
        total_pages: Total number of pages
        stocks_on_page: List of stocks to display

    Returns:
        InlineKeyboardMarkup with stock buttons and pagination
    """
    keyboard: list[list[InlineKeyboardButton]] = []

    # Add stock buttons
    for stock in stocks_on_page:
        button = InlineKeyboardButton(
            text=f"{stock.ticker} - {stock.name[:25]}...",
            callback_data=f"stock_{stock.ticker}",
        )
        keyboard.append([button])

    # Pagination row
    pagination_row: list[InlineKeyboardButton] = []

    # Previous button
    if current_page > 0:
        pagination_row.append(
            InlineKeyboardButton(
                text="◀️ Prev", callback_data=f"stocks_page_{current_page - 1}"
            )
        )

    # Page indicator
    pagination_row.append(
        InlineKeyboardButton(
            text=f"{current_page + 1}/{total_pages}", callback_data="stocks_page_info"
        )
    )

    # Next button
    if current_page < total_pages - 1:
        pagination_row.append(
            InlineKeyboardButton(
                text="Next ▶️", callback_data=f"stocks_page_{current_page + 1}"
            )
        )

    keyboard.append(pagination_row)

    # Search row
    keyboard.append(
        [
            InlineKeyboardButton(text="🔍 Search", callback_data="stocks_search"),
            InlineKeyboardButton(text="📋 All Stocks", callback_data="stocks_all"),
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def format_stocks_page(
    stocks: list[StockEntry], page: int, total_pages: int, language: str
) -> str:
    """
    Format a page of stocks for display.

    Args:
        stocks: List of stocks on this page
        page: Current page number (0-based)
        total_pages: Total pages
        language: User's language code

    Returns:
        Formatted message text
    """
    loader = _get_loader()

    lines = [
        loader.get(MessageKey.stocks_title, language),
        "",
        loader.get(
            MessageKey.stocks_showing,
            language,
            count=len(stocks),
            total=sum(1 for _ in get_catalog_service().get_stocks()),
            page=page + 1,
            total_pages=total_pages,
        ),
        "",
    ]

    for stock in stocks:
        sector_info = f" ({stock.sector})" if stock.sector else ""
        lines.append(f"• *{stock.ticker}* - {stock.name}{sector_info}")

    lines.extend(
        [
            "",
            loader.get(MessageKey.stocks_tap_to_use, language),
            "",
            loader.get(MessageKey.stocks_forecast_example, language),
        ]
    )

    return "\n".join(lines)


@router.message(Command("stocks"))
async def cmd_stocks(message: Message) -> None:
    """
    Handle /stocks command.
    Returns paginated list of available stock tickers.
    """
    user_id = message.from_user.id if message.from_user else 0
    language = await _get_user_language(user_id)
    loader = _get_loader()

    try:
        catalog = get_catalog_service()
        stocks = catalog.get_stocks()

        if not stocks:
            await message.answer(
                loader.get(MessageKey.stocks_empty, language),
                disable_web_page_preview=True,
            )
            return

        # Sort stocks by ticker
        stocks_sorted = sorted(stocks, key=lambda x: x.ticker)

        # Calculate pagination
        total_pages = ceil(len(stocks_sorted) / STOCKS_PER_PAGE)
        page = 0
        stocks_page = stocks_sorted[:STOCKS_PER_PAGE]

        # Format and send message
        text = format_stocks_page(stocks_page, page, total_pages, language)
        keyboard = create_stocks_keyboard(page, total_pages, stocks_page)

        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

        logger.info(f"Displayed stocks list to user {user_id}")

    except Exception as e:
        logger.error(f"Error displaying stocks: {e!s}")
        await message.answer(loader.get(MessageKey.stocks_error_loading, language))


@router.callback_query(lambda c: c.data and c.data.startswith("stocks_page_"))
async def callback_stocks_page(callback: CallbackQuery) -> None:
    """
    Handle pagination callbacks for stocks list.
    """
    user_id = callback.from_user.id if callback.from_user else 0
    language = await _get_user_language(user_id)
    loader = _get_loader()

    try:
        # Parse page number
        page_str = callback.data.replace("stocks_page_", "")
        if page_str == "info":
            await callback.answer(
                callback.message.reply_markup.inline_keyboard[0][1].text,
                show_alert=False,
            )
            return

        new_page = int(page_str)

        # Reload stocks
        catalog = get_catalog_service()
        stocks = catalog.get_stocks()

        if not stocks:
            await callback.answer(
                loader.get(MessageKey.stocks_empty, language), show_alert=True
            )
            return

        # Sort and paginate
        stocks_sorted = sorted(stocks, key=lambda x: x.ticker)
        total_pages = ceil(len(stocks_sorted) / STOCKS_PER_PAGE)

        if new_page < 0 or new_page >= total_pages:
            await callback.answer(
                loader.get(MessageKey.pagination_invalid_page, language),
                show_alert=True,
            )
            return

        stocks_page = stocks_sorted[
            new_page * STOCKS_PER_PAGE : (new_page + 1) * STOCKS_PER_PAGE
        ]

        # Update message
        text = format_stocks_page(stocks_page, new_page, total_pages, language)
        keyboard = create_stocks_keyboard(new_page, total_pages, stocks_page)

        await callback.message.edit_text(
            text, reply_markup=keyboard, parse_mode="Markdown"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Error handling stocks page callback: {e!s}")
        await callback.answer(
            loader.get(MessageKey.stock_selection_error, language), show_alert=True
        )


@router.callback_query(lambda c: c.data and c.data.startswith("stock_"))
async def callback_stock_selected(callback: CallbackQuery) -> None:
    """
    Handle stock selection from the list.
    """
    user_id = callback.from_user.id if callback.from_user else 0
    language = await _get_user_language(user_id)
    loader = _get_loader()

    try:
        ticker = callback.data.replace("stock_", "")

        catalog = get_catalog_service()
        stock = catalog.get_stock(ticker)

        if stock:
            await callback.message.edit_text(
                loader.get(
                    MessageKey.stock_selected,
                    language,
                    ticker=stock.ticker,
                    company=stock.name,
                    sector=stock.sector or "Unknown",
                ),
                parse_mode="Markdown",
            )
        else:
            await callback.answer(
                loader.get(MessageKey.stocks_not_found, language), show_alert=True
            )

    except Exception as e:
        logger.error(f"Error handling stock selection: {e!s}")
        await callback.answer(
            loader.get(MessageKey.stock_selection_error, language), show_alert=True
        )


@router.callback_query(lambda c: c.data == "stocks_search")
async def callback_stocks_search(callback: CallbackQuery) -> None:
    """
    Handle search button callback.
    """
    user_id = callback.from_user.id if callback.from_user else 0
    language = await _get_user_language(user_id)
    loader = _get_loader()

    await callback.message.edit_text(
        loader.get(MessageKey.search_title, language)
        + "\n\n"
        + loader.get(MessageKey.search_prompt, language)
        + "\n"
        + loader.get(MessageKey.search_example, language)
        + "\n"
        + loader.get(MessageKey.search_results, language)
        + "\n\n"
        + loader.get(MessageKey.search_direct_use, language),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "stocks_all")
async def callback_stocks_all(callback: CallbackQuery) -> None:
    """
    Handle 'All Stocks' button - shows first page.
    """
    # Just reload first page
    await cmd_stocks(callback.message)
    await callback.answer()


async def get_stocks_list(
    page: int = 0, per_page: int = STOCKS_PER_PAGE
) -> dict[str, Any]:
    """
    Get paginated stocks list for external use.

    Args:
        page: Page number (0-based)
        per_page: Items per page

    Returns:
        Dictionary with stocks data and pagination info
    """
    catalog = get_catalog_service()
    stocks = catalog.get_stocks()

    if not stocks:
        return {"stocks": [], "page": page, "total_pages": 0, "total_count": 0}

    stocks_sorted = sorted(stocks, key=lambda x: x.ticker)
    total_pages = ceil(len(stocks_sorted) / per_page)

    start = page * per_page
    end = start + per_page
    stocks_page = stocks_sorted[start:end]

    return {
        "stocks": [
            {"ticker": s.ticker, "name": s.name, "sector": s.sector}
            for s in stocks_page
        ],
        "page": page,
        "total_pages": total_pages,
        "total_count": len(stocks_sorted),
    }


def get_stocks_count() -> int:
    """Get total number of stocks in catalog."""
    catalog = get_catalog_service()
    return catalog.get_stock_count()


def is_stock_available(ticker: str) -> bool:
    """Check if a ticker is in the catalog."""
    catalog = get_catalog_service()
    return catalog.is_stock_available(ticker)
