"""
i18n (Internationalization) module for Telegram bot.

Provides language selection, message loading, and user language preference management.
"""

from src.i18n.constants import MessageKey
from src.i18n.loader import MessageLoader
from src.i18n.middleware import LanguageMiddleware

__all__ = [
    "LanguageMiddleware",
    "MessageKey",
    "MessageLoader",
]

# Default language for new users (Russian)
DEFAULT_LANGUAGE = "ru"

# Supported languages
SUPPORTED_LANGUAGES = ["ru", "en"]
