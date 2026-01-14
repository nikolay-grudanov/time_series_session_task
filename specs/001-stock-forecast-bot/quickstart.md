# Quickstart Guide: Stock Forecast Telegram Bot

## Prerequisites

- Python 3.12
- uv package manager
- Telegram Bot Token (from BotFather)

## Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd time_series_session_task
   ```

2. **Install dependencies using uv**
   ```bash
   uv sync
   ```

3. **Set up environment variables**
   Create a `.env` file in the project root:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```

## Running the Application

1. **Start the Telegram bot**
   ```bash
   python src/main.py
   ```

2. **Interact with the bot**
   - Find your bot on Telegram
   - Send a message with the format: `<ticker_symbol> <investment_amount>` (e.g., "AAPL 1000")
   - The bot will respond with a 30-day forecast, trading recommendations, and profit calculation

## Development

1. **Running tests**
   ```bash
   # Run all tests
   pytest
   
   # Run specific test module
   pytest tests/unit/test_models/test_classical_ml.py
   ```

2. **Adding dependencies**
   ```bash
   # Add a new dependency
   uv add <package-name>
   ```

3. **Making changes**
   - Follow the "One commit per task" policy
   - Each commit should represent complete, tested functionality
   - Use descriptive commit messages following conventional commit standards

## Project Structure

```
src/
├── __init__.py
├── main.py                 # Main entry point for the Telegram bot
├── config/
│   ├── __init__.py
│   └── settings.py         # Configuration and environment variables
├── models/
│   ├── __init__.py
│   ├── classical_ml.py     # Classical ML models (Random Forest, Ridge Regression)
│   ├── statistical.py      # Statistical models (ARIMA, ETS, Prophet)
│   ├── neural_networks.py  # Neural network models (LSTM, GRU, RNN)
│   └── model_selector.py   # Model selection based on performance metrics
├── services/
│   ├── __init__.py
│   ├── data_loader.py      # Service to download historical stock data using yfinance
│   ├── forecasting.py      # Service for generating forecasts
│   ├── trading_strategy.py # Service for generating buy/sell recommendations
│   ├── profit_calculator.py # Service for calculating potential profit
│   └── logger_service.py   # Service for logging user requests
├── utils/
│   ├── __init__.py
│   ├── validators.py       # Validation utilities for inputs
│   ├── visualizer.py       # Utilities for creating forecast graphs
│   └── helpers.py          # General helper functions
└── handlers/
    ├── __init__.py
    └── telegram_handlers.py # Telegram bot command handlers
```

## Key Features

1. **Multi-model Approach**: Implements Classical ML, Statistical, and Neural Network models
2. **Automatic Model Selection**: Selects the best performing model based on RMSE and MAPE metrics
3. **Confidence Intervals**: Provides confidence intervals with forecasts for reliability
4. **Trading Recommendations**: Identifies optimal buy/sell days based on forecasts
5. **Profit Calculation**: Estimates potential profit based on investment amount and strategy
6. **Comprehensive Logging**: Logs all user requests with key parameters for 1 year
7. **Weekly Retraining**: Models are retrained weekly to maintain accuracy