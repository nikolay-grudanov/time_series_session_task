"""
Configuration settings for the stock forecast Telegram bot.
"""
import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Data Configuration
DATA_DIR = "data"
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
MODELS_DIR = os.path.join(DATA_DIR, "models")

# Logging Configuration
LOGS_DIR = "logs"
REQUEST_LOG_FILE = os.path.join(LOGS_DIR, "requests.log")

# Model Configuration
MODEL_TRAINING_TIMEOUT = 300  # 5 minutes in seconds
FORECAST_DAYS = 30
MIN_INVESTMENT_AMOUNT = 1
MAX_INVESTMENT_AMOUNT = 1_000_000

# Stock Data Configuration
HISTORICAL_YEARS = 2
API_RATE_LIMIT_DELAY = 1  # seconds between API calls
