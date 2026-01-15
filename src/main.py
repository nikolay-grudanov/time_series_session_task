"""
Main entry point for the Telegram bot that provides stock price forecasts.
"""

import asyncio
import logging
from datetime import datetime

import pandas as pd
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile

from src.config.settings import REQUEST_LOG_FILE, TELEGRAM_BOT_TOKEN
from src.handlers.language_selection import router as language_router
from src.handlers.status_handler import router as status_router
from src.handlers.stocks_handler import router as stocks_router
from src.i18n.constants import MessageKey
from src.i18n.loader import MessageLoader
from src.i18n.middleware import get_language_middleware
from src.services.data_loader import DataLoaderService
from src.services.forecasting import ForecastingService
from src.services.logger_service import LoggerService
from src.services.profit_calculator import ProfitCalculatorService
from src.services.trading_strategy import TradingStrategyService
from src.utils.logging_config import setup_logging_with_rotation
from src.utils.validators import validate_investment_amount, validate_ticker

# Set up logging
setup_logging_with_rotation(REQUEST_LOG_FILE)

logger = logging.getLogger(__name__)

# Initialize services
data_loader = DataLoaderService()
forecasting_service = ForecastingService()
trading_strategy_service = TradingStrategyService()
profit_calculator_service = ProfitCalculatorService()
logger_service = LoggerService(REQUEST_LOG_FILE)


# Initialize bot - handle case where TELEGRAM_BOT_TOKEN might be None
if TELEGRAM_BOT_TOKEN:
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
else:
    logger.error("TELEGRAM_BOT_TOKEN is not set in environment variables")
    raise ValueError("TELEGRAM_BOT_TOKEN is not set in environment variables")
dp = Dispatcher()

_message_loader: MessageLoader | None = None


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


def _format_trading_recommendations(trading_recommendations, ticker, language, loader):
    """
    Format trading recommendations in a human-readable way.

    Args:
        trading_recommendations: Dict with trade signals and potential profits
        ticker: Stock ticker symbol
        language: User's language code
        loader: MessageLoader instance

    Returns:
        Formatted message string
    """
    lines = []
    lines.append(
        loader.get(MessageKey.trading_recommendations_header, language, ticker=ticker)
    )

    profit = trading_recommendations["potential_profits"]["potential_profit"]
    roi = trading_recommendations["potential_profits"]["roi_percentage"]

    lines.append(loader.get(MessageKey.profit_info, language, profit=profit, roi=roi))
    lines.append(loader.get(MessageKey.trading_actions_header, language))

    if trading_recommendations["trade_signals"]["buy_signals"]:
        lines.append(loader.get(MessageKey.buy_opportunities, language))
        for signal in trading_recommendations["trade_signals"]["buy_signals"]:
            date_str = signal["date"].strftime("%Y-%m-%d")
            lines.append(loader.get(MessageKey.buy_date, language, date=date_str))
        lines.append("")

    if trading_recommendations["trade_signals"]["sell_signals"]:
        lines.append(loader.get(MessageKey.sell_opportunities, language))
        for signal in trading_recommendations["trade_signals"]["sell_signals"]:
            date_str = signal["date"].strftime("%Y-%m-%d")
            lines.append(loader.get(MessageKey.sell_date, language, date=date_str))
        lines.append("")

    if (
        not trading_recommendations["trade_signals"]["buy_signals"]
        and not trading_recommendations["trade_signals"]["sell_signals"]
    ):
        lines.append(loader.get(MessageKey.no_opportunities, language))
        lines.append(loader.get(MessageKey.market_neutral, language))

    return "\n".join(lines)


def is_not_command(message: types.Message) -> bool:
    """Check if message is not a command."""
    if not message.text:
        return True
    return not message.text.startswith("/")


@dp.message(is_not_command)
async def handle_forecast_request(message: types.Message):
    """
    Handler for forecast requests without command.
    Expected format: "<TICKER> <INVESTMENT_AMOUNT>"
    """
    await _process_forecast(message)


@dp.message(Command("forecast"))
async def cmd_forecast(message: types.Message):
    """
    Handler for /forecast command.
    Expected format: "/forecast <TICKER> <INVESTMENT_AMOUNT>"
    """
    user_input = message.text.strip() if message.text else ""

    parts = user_input.split()
    if len(parts) >= 3:
        user_input = " ".join(parts[1:3])

    await _process_forecast(message, user_input)


async def _process_forecast(message: types.Message, user_input: str | None = None):
    """
    Core forecast processing logic used by both handlers.

    Args:
        message: Message object
        user_input: Optional pre-parsed input (for /forecast command)
    """
    user_id = message.from_user.id if message.from_user else 0
    if user_input is None:
        user_input = message.text.strip() if message.text else ""
    language = await _get_user_language(user_id)
    loader = _get_loader()

    logger.info(f"Received request from user {user_id}: {user_input}")

    ticker = "UNKNOWN"

    try:
        parts = user_input.split()
        if len(parts) != 2:
            await message.answer(
                loader.get(MessageKey.forecast_usage_error, language)
                + loader.get(
                    MessageKey.forecast_format,
                    language,
                    ticker="<TICKER>",
                    amount="<AMOUNT>",
                )
                + "\n"
                + loader.get(
                    MessageKey.forecast_example, language, ticker="AAPL", amount="1000"
                ),
                parse_mode="Markdown",
            )
            return

        ticker, investment_str = parts
        ticker = ticker.upper()

        ticker_result = validate_ticker(ticker)
        if not ticker_result.is_valid:
            error_msg = ticker_result.error_message or "Invalid ticker symbol"
            await message.answer(
                loader.get(MessageKey.error_invalid_ticker, language),
                parse_mode="Markdown",
            )
            logger_service.log_error(user_id, ticker, f"Invalid ticker: {error_msg}")
            return

        amount_result = validate_investment_amount(investment_str)
        if not amount_result.is_valid:
            error_msg = amount_result.error_message or "Invalid investment amount"
            await message.answer(loader.get(MessageKey.error_invalid_amount, language))
            logger_service.log_error(
                user_id, ticker, f"Invalid investment amount: {error_msg}"
            )
            return

        investment_amount = float(investment_str)

        await message.answer(
            loader.get(MessageKey.forecast_downloading, language, ticker=ticker)
        )
        historical_data = data_loader.download_historical_data(ticker)

        if historical_data is None or historical_data.empty:
            error_msg = loader.get(MessageKey.forecast_no_data, language, ticker=ticker)
            await message.answer(error_msg)
            logger_service.log_error(user_id, ticker, error_msg)
            return

        await message.answer(loader.get(MessageKey.forecast_generating_v2, language))
        close_prices_raw = (
            historical_data["Close"]
            if "Close" in historical_data.columns
            else historical_data
        )
        close_prices = (
            pd.Series(close_prices_raw)
            if not isinstance(close_prices_raw, pd.Series)
            else close_prices_raw
        )
        forecast_result = (
            forecasting_service.generate_forecast_with_volatility_adjustment(
                ticker=ticker,
                historical_data=close_prices,
            )
        )

        await message.answer(loader.get(MessageKey.forecast_analyzing, language))
        trading_recommendations = (
            trading_strategy_service.generate_trading_recommendations(
                forecast_data=forecast_result["forecast_data"],
                historical_data=close_prices,
                forecast_dates=forecast_result["forecast_dates"],
                investment_amount=investment_amount,
            )
        )

        await message.answer(loader.get(MessageKey.forecast_calculating, language))
        profit_analysis = profit_calculator_service.calculate_detailed_profit_analysis(
            buy_signals=trading_recommendations["trade_signals"]["buy_signals"],
            sell_signals=trading_recommendations["trade_signals"]["sell_signals"],
            investment_amount=investment_amount,
            initial_price=historical_data["Close"].iloc[-1],
            final_price=forecast_result["forecast_data"][-1],
        )

        plot_filename = (
            f"forecast_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )
        with open(plot_filename, "wb") as f:
            f.write(forecast_result["plot_bytes"])

        plot_file = FSInputFile(plot_filename)
        caption = (
            loader.get(MessageKey.forecast_result_caption, language, ticker=ticker)
            + loader.get(
                MessageKey.forecast_expected_change,
                language,
                change=forecast_result["expected_change_pct"],
            )
            + "\n"
            + loader.get(
                MessageKey.forecast_last_price,
                language,
                price=forecast_result["last_known_price"],
            )
            + "\n"
            + loader.get(
                MessageKey.forecast_end_price,
                language,
                price=forecast_result["forecast_end_price"],
            )
            + "\n"
            + loader.get(
                MessageKey.forecast_best_model,
                language,
                model=forecast_result["best_model_name"],
            )
        )
        await message.answer_photo(
            photo=plot_file, caption=caption, parse_mode="Markdown"
        )

        formatted_recommendations = _format_trading_recommendations(
            trading_recommendations, ticker, language, loader
        )
        await message.answer(formatted_recommendations, parse_mode="Markdown")

        profit_title = loader.get(MessageKey.profit_analysis_title, language)
        profit_text = (
            profit_title
            + loader.get(
                MessageKey.profit_potential,
                language,
                profit=profit_analysis["trading_strategy"]["profit"],
            )
            + "\n"
            + loader.get(
                MessageKey.roi_label,
                language,
                roi=profit_analysis["trading_strategy"]["roi_percentage"],
            )
            + "\n"
            + loader.get(
                MessageKey.active_vs_hold,
                language,
                diff=profit_analysis["comparison"]["active_vs_hold"],
            )
            + "\n"
            + loader.get(
                MessageKey.effectiveness, language, eff=profit_analysis["effectiveness"]
            )
        )
        await message.answer(profit_text)

        logger_service.log_request(
            user_id=user_id,
            ticker=ticker,
            investment_amount=investment_amount,
            selected_model=forecast_result["best_model_name"],
            metrics=forecast_result["model_metrics"][
                forecast_result["best_model_name"]
            ],
            profit_estimate=profit_analysis["trading_strategy"]["profit"],
            additional_params={
                "volatility_assessment": forecast_result["volatility_assessment"][
                    "is_extremely_volatile"
                ]
            },
        )

        logger.info(
            f"Successfully processed request for user {user_id}, ticker {ticker}"
        )

    except Exception as e:
        error_msg = f"An error occurred while processing your request: {e!s}"
        await message.answer(loader.get(MessageKey.error_generic, language))
        logger.error(error_msg, exc_info=True)
        logger_service.log_error(
            user_id, ticker if "ticker" in locals() else "unknown", str(e)
        )


async def main():
    """
    Main function to start the bot.
    """
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set in environment variables")
        return

    dp.include_router(language_router)
    dp.include_router(stocks_router)
    dp.include_router(status_router)
    logger.info("Starting the Stock Forecast Telegram Bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
