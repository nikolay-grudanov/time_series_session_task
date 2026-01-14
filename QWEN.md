# Time Series Session Task - Telegram Bot for Stock Analysis and Forecasting

## Project Overview

This is a Python-based Telegram bot project that analyzes and forecasts stock prices using time series models. The bot allows users to input a company ticker symbol and investment amount, then automatically downloads historical stock data, trains multiple time series models, selects the best performing model, and generates a forecast for the next 30 days.

### Key Features
- **User Interaction**: Accepts company ticker symbols and investment amounts via Telegram
- **Data Retrieval**: Downloads historical stock data using `yfinance` from Yahoo Finance
- **Model Training**: Implements at least three different model types:
  - Classical ML models (Random Forest, Ridge Regression with lag features)
  - Statistical models (ARIMA, ETS, Prophet)
  - Neural network models (LSTM, GRU, RNN)
- **Model Selection**: Automatically selects the best model based on performance metrics (RMSE, MAPE)
- **Forecasting**: Generates 30-day price forecasts
- **Visualization**: Provides graphical representation of historical and predicted prices
- **Trading Recommendations**: Identifies optimal buy/sell days and calculates potential profit
- **Logging**: Maintains a log of all user requests with key parameters

## Technical Stack

- **Language**: Python 3.12
- **Framework**: aiogram or python-telegram-bot
- **Data Source**: yfinance for Yahoo Finance API integration
- **ML Libraries**: scikit-learn, statsmodels, TensorFlow/Keras (for neural networks)
- **Data Processing**: pandas, numpy
- **Visualization**: matplotlib, plotly
- **Dependency Management**: uv (based on uv.lock file)

## Building and Running

### Prerequisites
- Python 3.12
- Telegram Bot Token (obtained from @BotFather)

### Setup Instructions
```bash
# Clone the repository
git clone <repository-url>

# Navigate to project directory
cd time_series_session_task

# Install dependencies using uv (recommended)
uv sync

# Or install dependencies using pip
pip install -r requirements.txt
```

### Package Management
This project uses `uv` for dependency management. To add new packages:
```bash
uv add <package-name>
```

This ensures all dependencies are properly synchronized and reflected in both `pyproject.toml` and `uv.lock` files.

### Virtual Environment
A virtual environment has already been created in the `.venv` directory. The `uv sync` command will use this environment. If you need to recreate it:
```bash
uv venv
```

### Environment Configuration
Create a `.env` file in the project root with the following variables:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

### Running the Bot
```bash
python main.py
```

## Project Structure

- `main.py`: Main entry point for the Telegram bot
- `project_statement.md`: Detailed project requirements and specifications
- `pyproject.toml`: Project metadata and dependencies
- `README.md`: Project documentation
- `uv.lock`: Dependency lock file for uv package manager
- `.python-version`: Specifies Python version (3.12)

## Development Conventions

### Coding Standards
- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Include docstrings for all functions and classes
- Write type hints where appropriate

### Model Implementation Requirements
- Implement at least 3 different model types (Classical ML, Statistical, Neural Networks)
- Evaluate models using RMSE, MAPE, and other relevant metrics
- Automatically select the best-performing model for forecasting
- Train on 2 years of historical data

### Error Handling
- Handle invalid ticker symbols gracefully
- Manage API rate limits from Yahoo Finance
- Provide informative error messages to users
- Log errors for debugging purposes

### Testing
- Unit tests for individual components
- Integration tests for the full prediction pipeline
- Validation of model accuracy metrics

## Project Phases

### Phase 1: User Interaction
- Implement Telegram bot interface
- Accept ticker symbol and investment amount
- Download historical stock data using yfinance

### Phase 2: Model Training and Selection
- Implement three different model types
- Train models on historical data
- Compare models using performance metrics
- Select the best model automatically

### Phase 3: Forecasting and Visualization
- Generate 30-day price forecast
- Create visualizations of historical vs predicted prices
- Calculate expected price change

### Phase 4: Investment Recommendations
- Identify optimal buy/sell days based on predictions
- Calculate potential profit from trading strategy
- Generate summary report for user

### Phase 5: Logging
- Maintain log of all user requests
- Record key parameters: user ID, timestamp, ticker, investment amount, selected model, metrics, profit estimate

## Current Status

The project is in early development stage with a basic `main.py` file containing only a placeholder function. The implementation needs to be built according to the project specifications outlined in `project_statement.md`.

## Dependencies to Add

Based on the project requirements, the following dependencies should be added to `pyproject.toml`:
- `aiogram` or `python-telegram-bot` for Telegram integration
- `yfinance` for stock data retrieval
- `pandas`, `numpy` for data processing
- `scikit-learn` for classical ML models
- `statsmodels` for statistical models
- `tensorflow` or `torch` for neural network models
- `matplotlib` or `plotly` for visualization
- `python-dotenv` for environment variable management

## Active Technologies
- Python 3.12 + aiogram (Telegram bot), yfinance (Yahoo Finance API), pandas, numpy, scikit-learn, statsmodels, tensorflow/pytorch (neural networks), matplotlib/plotly (visualization), python-dotenv (environment management) (001-stock-forecast-bot)
- CSV files for data persistence as per constitution (001-stock-forecast-bot)
- Python 3.12 + aiogram (Telegram bot), yfinance (Yahoo Finance API), pandas, numpy, scikit-learn, statsmodels, pytorch (neural networks), matplotlib/plotly (visualization), python-dotenv (environment management) (001-enhanced-forecast-models)

## Recent Changes
- 001-stock-forecast-bot: Added Python 3.12 + aiogram (Telegram bot), yfinance (Yahoo Finance API), pandas, numpy, scikit-learn, statsmodels, tensorflow/pytorch (neural networks), matplotlib/plotly (visualization), python-dotenv (environment management)
