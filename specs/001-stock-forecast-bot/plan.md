# Implementation Plan: Stock Forecast Telegram Bot

**Branch**: `001-stock-forecast-bot` | **Date**: 2026-01-14 | **Spec**: [spec link](/home/gna/workspase/education/MEPHI/time_series_session_task/specs/001-stock-forecast-bot/spec.md)
**Input**: Feature specification from `/specs/001-stock-forecast-bot/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implementation of a Telegram bot that allows users to input a company ticker symbol and investment amount to receive a 30-day stock price forecast. The system will automatically download historical stock data from Yahoo Finance, train at least three different model types (Classical ML, Statistical, Neural Network), select the best performing model based on quality metrics (RMSE, MAPE), and generate forecasts with confidence intervals. The bot will provide graphical representations of forecasts, trading recommendations, and profit calculations. All user requests will be logged with key parameters for monitoring and analysis.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: aiogram (Telegram bot), yfinance (Yahoo Finance API), pandas, numpy, scikit-learn, statsmodels, tensorflow/pytorch (neural networks), matplotlib/plotly (visualization), python-dotenv (environment management)
**Storage**: CSV files for data persistence as per constitution
**Testing**: pytest for unit and integration tests
**Target Platform**: Linux server (can run on cloud infrastructure)
**Project Type**: Single project (Python application with Telegram bot interface)
**Performance Goals**: Model training completes within 5 minutes; user requests processed within 2 minutes; 80% success rate for valid ticker symbols
**Constraints**: Must handle API rate limits from Yahoo Finance; investment amounts between $1-$1,000,000; 1-year log retention; weekly model retraining
**Scale/Scope**: Individual investors using the Telegram bot for stock forecasting

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Compliance Verification

- **I. Python-Centric Development**: ✅ Confirmed - Using Python 3.12 as required
- **II. uv Package Management**: ✅ Confirmed - Will use uv for dependency management
- **III. Telegram Bot Implementation with aiogram**: ✅ Confirmed - Using aiogram library as required
- **IV. CSV Data Storage Standard**: ✅ Confirmed - Using CSV format for data persistence
- **V. Yahoo Finance Data Integration**: ✅ Confirmed - Using yfinance library as required
- **VI. One Commit Per Task Policy**: ✅ Confirmed - Following one-commit-per-task practice
- **VII. Multi-Class Model Implementation for Forecasting**: ✅ Confirmed - Implementing Classical ML, Statistical, and Neural Network models

### Additional Requirements Compliance

- **Development Workflow**: ✅ Unit and integration tests will cover components and prediction pipeline
- **Model Evaluation Standards**: ✅ Using RMSE, MAPE metrics with automatic model selection
- **Error Handling Requirements**: ✅ Handling invalid tickers, API limits, and providing proper logging

## Project Structure

### Documentation (this feature)

```text
specs/001-stock-forecast-bot/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
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

tests/
├── __init__.py
├── unit/
│   ├── __init__.py
│   ├── test_models/
│   │   ├── __init__.py
│   │   ├── test_classical_ml.py
│   │   ├── test_statistical.py
│   │   └── test_neural_networks.py
│   ├── test_services/
│   │   ├── __init__.py
│   │   ├── test_data_loader.py
│   │   ├── test_forecasting.py
│   │   └── test_trading_strategy.py
│   └── test_utils/
│       ├── __init__.py
│       └── test_validators.py
├── integration/
│   ├── __init__.py
│   └── test_prediction_pipeline.py # Integration test for the full prediction pipeline
└── contract/
    ├── __init__.py
    └── test_api_contracts.py

data/
├── raw/                    # Raw downloaded stock data (CSV format)
├── processed/              # Processed data ready for model training (CSV format)
└── models/                 # Saved trained models (if needed)

logs/
└── requests.log            # Log file for user requests (retained for 1 year)

.env                           # Environment variables file (not committed)
pyproject.toml                 # Project dependencies managed with uv
uv.lock                        # Lock file for reproducible builds
README.md                      # Project documentation
```

**Structure Decision**: Selected single project structure with clear separation of concerns. The application is organized into logical modules: models for different ML approaches, services for business logic, utils for helper functions, and handlers for Telegram bot interactions. This structure supports the constitution's requirements for clean, modular architecture with proper documentation.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |

## Post-Design Constitution Check

*Re-evaluation after Phase 1 design*

### Compliance Verification

- **I. Python-Centric Development**: ✅ Confirmed - Using Python 3.12 as required
- **II. uv Package Management**: ✅ Confirmed - Will use uv for dependency management in pyproject.toml
- **III. Telegram Bot Implementation with aiogram**: ✅ Confirmed - Using aiogram library as required in handlers/telegram_handlers.py
- **IV. CSV Data Storage Standard**: ✅ Confirmed - Using CSV format for data persistence in data/ directory
- **V. Yahoo Finance Data Integration**: ✅ Confirmed - Using yfinance library as required in services/data_loader.py
- **VI. One Commit Per Task Policy**: ✅ Confirmed - Following one-commit-per-task practice as outlined in quickstart.md
- **VII. Multi-Class Model Implementation for Forecasting**: ✅ Confirmed - Implementing Classical ML, Statistical, and Neural Network models in models/ directory

### Additional Requirements Compliance

- **Development Workflow**: ✅ Unit and integration tests will cover components and prediction pipeline as outlined in tests/ directory structure
- **Model Evaluation Standards**: ✅ Using RMSE, MAPE metrics with automatic model selection in models/model_selector.py
- **Error Handling Requirements**: ✅ Handling invalid tickers, API limits, and providing proper logging as outlined in services/logger_service.py
