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


@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    """
    Handler for the /start command.
    """
    welcome_text = (
        "Welcome to the Stock Forecast Bot!\n\n"
        "I can help you forecast stock prices and provide trading recommendations.\n\n"
        "To get started, send me a message in the format:\n"
        "`<TICKER SYMBOL> <INVESTMENT AMOUNT>`\n\n"
        "For example: `AAPL 1000`\n\n"
        "Supported ticker formats: 1-5 uppercase letters (e.g., AAPL, GOOGL, TSLA)\n"
        "Investment amount: Between $1 and $1,000,000"
    )
    await message.answer(welcome_text, parse_mode="Markdown")


@dp.message()
async def handle_forecast_request(message: types.Message):
    """
    Handler for forecast requests.
    Expected format: "<TICKER> <INVESTMENT_AMOUNT>"
    """
    user_id = message.from_user.id if message.from_user else 0
    user_input = message.text.strip() if message.text else ""

    logger.info(f"Received request from user {user_id}: {user_input}")

    # Initialize ticker to avoid unbound variable error
    ticker = "UNKNOWN"

    try:
        # Parse the user input
        parts = user_input.split()
        if len(parts) != 2:
            await message.answer(
                "Please provide both a ticker symbol and investment amount in the format: `<TICKER> <AMOUNT>`\n"
                "Example: `AAPL 1000`",
                parse_mode="Markdown"
            )
            return

        ticker, investment_str = parts
        ticker = ticker.upper()

        # Validate ticker symbol
        if not validate_ticker(ticker):
            await message.answer(
                f"Invalid ticker symbol: `{ticker}`\n"
                "Ticker should be 1-5 uppercase letters (e.g., AAPL, GOOGL, TSLA)",
                parse_mode="Markdown"
            )
            logger_service.log_error(user_id, ticker, "Invalid ticker symbol")
            return

        # Validate investment amount
        is_valid, error_msg = validate_investment_amount(investment_str)
        if not is_valid:
            await message.answer(error_msg)
            logger_service.log_error(user_id, ticker, f"Invalid investment amount: {error_msg}")
            return

        investment_amount = float(investment_str)

        # Download historical data
        await message.answer(f"Downloading historical data for {ticker}...")
        historical_data = data_loader.download_historical_data(ticker)

        if historical_data is None or historical_data.empty:
            error_msg = f"No historical data found for ticker: {ticker}"
            await message.answer(error_msg)
            logger_service.log_error(user_id, ticker, error_msg)
            return

        # Generate forecast
        await message.answer("Generating forecast...")
        # Ensure historical_data['Close'] is a pandas Series
        close_prices_raw = historical_data['Close'] if 'Close' in historical_data.columns else historical_data
        close_prices = pd.Series(close_prices_raw) if not isinstance(close_prices_raw, pd.Series) else close_prices_raw
        forecast_result = forecasting_service.generate_forecast_with_volatility_adjustment(
            ticker=ticker,
            historical_data=close_prices  # Use closing prices
        )

        # Generate trading recommendations
        await message.answer("Analyzing trading opportunities...")
        trading_recommendations = trading_strategy_service.generate_trading_recommendations(
            forecast_data=forecast_result['forecast_data'],
            historical_data=close_prices,  # Use the same close prices as used for forecasting
            forecast_dates=forecast_result['forecast_dates'],
            investment_amount=investment_amount
        )

        # Calculate potential profit
        await message.answer("Calculating potential profit...")
        profit_analysis = profit_calculator_service.calculate_detailed_profit_analysis(
            buy_signals=trading_recommendations['trade_signals']['buy_signals'],
            sell_signals=trading_recommendations['trade_signals']['sell_signals'],
            investment_amount=investment_amount,
            initial_price=historical_data['Close'].iloc[-1],  # Last known price
            final_price=forecast_result['forecast_data'][-1]  # Last forecasted price
        )

        # Create and send the forecast plot
        plot_filename = f"forecast_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        with open(plot_filename, 'wb') as f:
            f.write(forecast_result['plot_bytes'])

        plot_file = FSInputFile(plot_filename)
        await message.answer_photo(
            photo=plot_file,
            caption=(
                f"Forecast for {ticker}\n"
                f"Expected change: {forecast_result['expected_change_pct']:.2f}%\n"
                f"Last known price: ${forecast_result['last_known_price']:.2f}\n"
                f"Forecast end price: ${forecast_result['forecast_end_price']:.2f}\n"
                f"Best model: {forecast_result['best_model_name']}"
            )
        )

        # Send trading recommendations
        await message.answer(
            f"Trading Recommendations for {ticker}:\n"
            f"{trading_recommendations['recommendation_summary']}"
        )

        # Send profit analysis
        await message.answer(
            f"Profit Analysis:\n"
            f"Potential Profit: ${profit_analysis['trading_strategy']['profit']:.2f}\n"
            f"ROI: {profit_analysis['trading_strategy']['roi_percentage']:.2f}%\n"
            f"Active vs Holding: ${profit_analysis['comparison']['active_vs_hold']:.2f}\n"
            f"Strategy Effectiveness: {profit_analysis['effectiveness']}"
        )

        # Log the successful request
        logger_service.log_request(
            user_id=user_id,
            ticker=ticker,
            investment_amount=investment_amount,
            selected_model=forecast_result['best_model_name'],
            metrics=forecast_result['model_metrics'][forecast_result['best_model_name']],
            profit_estimate=profit_analysis['trading_strategy']['profit'],
            additional_params={
                'volatility_assessment': forecast_result['volatility_assessment']['is_extremely_volatile']
            }
        )

        logger.info(f"Successfully processed request for user {user_id}, ticker {ticker}")

    except Exception as e:
        error_msg = f"An error occurred while processing your request: {e!s}"
        await message.answer(error_msg)
        logger.error(error_msg, exc_info=True)
        logger_service.log_error(user_id, ticker if 'ticker' in locals() else 'unknown', str(e))


async def main():
    """
    Main function to start the bot.
    """
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set in environment variables")
        return

    logger.info("Starting the Stock Forecast Telegram Bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
