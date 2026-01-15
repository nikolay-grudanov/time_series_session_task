# time_series_session_task Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-01-15

## Active Technologies
- Python 3.12 + aiogram 3.x, pydantic (validation), locales/ru.json, locales/en.json (001-bot-i18n)
- Python 3.12 + aiogram 3.x, yfinance, APScheduler, pandas, numpy, scikit-learn, prophet, tensorflow/keras (002-stock-catalog-retraining)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.11+: Follow standard conventions

## Recent Changes
- 001-bot-i18n: Added Python 3.12 + aiogram 3.x, pydantic (validation), i18n with MessageLoader and LanguageMiddleware

- 002-stock-catalog-retraining: Added Python 3.12 + aiogram 3.x, yfinance, APScheduler, pandas, numpy, scikit-learn, prophet, tensorflow/keras

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
