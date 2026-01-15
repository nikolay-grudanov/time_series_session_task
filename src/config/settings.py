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
MODEL_TRAINING_TIMEOUT = 300  # 5 minutes in seconds (constitution requirement)
FORECAST_DAYS = 30
MIN_INVESTMENT_AMOUNT = 1
MAX_INVESTMENT_AMOUNT = 1_000_000

# Stock Data Configuration
HISTORICAL_YEARS = 2
API_RATE_LIMIT_DELAY = 1  # seconds between API calls

# Stock Catalog Configuration
CATALOG_PATH = os.path.join("src", "config", "catalog.csv")
CATALOG_CACHE_TTL_HOURS = 24

# Scheduler Configuration (FR-008, FR-012)
SCHEDULER_RETRAINING_INTERVAL = "weekly"  # "daily", "weekly", "monthly"
SCHEDULER_RETRAINING_DAY = 0  # Day of week (0=Monday, 6=Sunday) - for weekly
SCHEDULER_RETRAINING_HOUR = 2  # Hour of day (2 AM default)
SCHEDULER_RETRAINING_MINUTE = 0
SCHEDULER_RETRY_COUNT = 3  # Max retry attempts per FR-012
SCHEDULER_RETRY_DELAY = 60  # Seconds between retries
SCHEDULER_ENABLED = True  # Enable/disable scheduler

# Fallback Model Configuration (FR-011)
FALLBACK_MODEL_RETENTION_DAYS = 14  # Keep fallback models for 2 weeks
FALLBACK_ENABLED = True

# User Session Logging (FR-016)
USER_SESSION_LOG_PATH = os.path.join(LOGS_DIR, "user_sessions.csv")
USER_SESSION_TXT_LOG_PATH = os.path.join(LOGS_DIR, "user_sessions.txt")

# Retraining Log (FR-014)
RETRAINING_LOG_PATH = os.path.join(LOGS_DIR, "retraining.csv")
