"""
Language middleware for i18n module.

Manages user language preferences using CSV-based storage (per Constitution §IV).
"""

import csv
import logging
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any

from src.i18n.loader import MessageLoader

logger = logging.getLogger(__name__)

# Default data directory
DATA_DIR = Path(__file__).parent.parent.parent / "data"
USER_DATA_FILE = DATA_DIR / "user_data.csv"


class LanguageMiddleware:
    """
    Middleware for managing user language preferences.

    Uses CSV-based storage for user data per Constitution §IV.
    Thread-safe implementation with file locking.
    """

    def __init__(
        self,
        data_file: str | Path | None = None,
        message_loader: MessageLoader | None = None,
        default_language: str = "ru",
    ) -> None:
        """
        Initialize the language middleware.

        Args:
            data_file: Path to CSV file with user data.
                       Defaults to 'data/user_data.csv'.
            message_loader: MessageLoader instance for localized messages.
            default_language: Default language for new users.
        """
        if data_file is None:
            data_file = USER_DATA_FILE

        self._data_file = Path(data_file)
        self._message_loader = message_loader or MessageLoader()
        self._default_language = default_language
        self._lock = Lock()

        # Ensure data directory exists
        self._data_file.parent.mkdir(parents=True, exist_ok=True)

        # Initialize CSV file with headers if it doesn't exist
        self._ensure_csv_structure()

    def _ensure_csv_structure(self) -> None:
        """Create CSV file with headers if it doesn't exist."""
        if not self._data_file.exists():
            try:
                with open(self._data_file, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(
                        ["user_id", "language_preference", "created_at", "updated_at"]
                    )
                logger.info(f"Created user data file: {self._data_file}")
            except OSError as e:
                logger.error(f"Failed to create user data file: {e}")

    def _read_user_data(self) -> dict[int, dict[str, Any]]:
        """
        Read all user data from CSV file.

        Returns:
            Dictionary mapping user_id to user data dict
        """
        users: dict[int, dict[str, Any]] = {}

        if not self._data_file.exists():
            return users

        try:
            with open(self._data_file, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    user_id = int(row["user_id"])
                    users[user_id] = {
                        "user_id": user_id,
                        "language_preference": row.get("language_preference") or None,
                        "created_at": row.get("created_at", ""),
                        "updated_at": row.get("updated_at", ""),
                    }
        except (OSError, ValueError) as e:
            logger.error(f"Failed to read user data: {e}")

        return users

    def _write_user_data(self, users: dict[int, dict[str, Any]]) -> None:
        """
        Write all user data to CSV file.

        Args:
            users: Dictionary mapping user_id to user data dict
        """
        try:
            with open(self._data_file, "w", newline="", encoding="utf-8") as f:
                fieldnames = [
                    "user_id",
                    "language_preference",
                    "created_at",
                    "updated_at",
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for user_data in users.values():
                    writer.writerow(user_data)
        except OSError as e:
            logger.error(f"Failed to write user data: {e}")
            raise RuntimeError(f"Failed to persist user data: {e}")

    async def get_user_language(self, user_id: int) -> str:
        """
        Get user's preferred language.

        For new users (not in database), returns default language.

        Args:
            user_id: Telegram user ID

        Returns:
            Language code ('ru' or 'en')
        """
        with self._lock:
            users = self._read_user_data()

            if user_id not in users:
                logger.debug(
                    f"New user {user_id}, using default language '{self._default_language}'"
                )
                return self._default_language

            lang = users[user_id].get("language_preference")

            if lang is None:
                logger.debug(
                    f"User {user_id} has no language preference, using default"
                )
                return self._default_language

            return lang

    async def set_user_language(self, user_id: int, language: str) -> None:
        """
        Update user's language preference.

        Args:
            user_id: Telegram user ID
            language: Language code ('ru' or 'en')

        Raises:
            ValueError: If language is not supported
        """
        supported_languages = self._message_loader.get_available_languages()
        if language not in supported_languages:
            raise ValueError(
                f"Unsupported language: {language}. Supported: {supported_languages}"
            )

        with self._lock:
            users = self._read_user_data()

            now = datetime.now().isoformat()

            if user_id in users:
                # Update existing user
                users[user_id]["language_preference"] = language
                users[user_id]["updated_at"] = now
                logger.info(
                    f"Updated language preference for user {user_id} to '{language}'"
                )
            else:
                # Create new user entry
                users[user_id] = {
                    "user_id": user_id,
                    "language_preference": language,
                    "created_at": now,
                    "updated_at": now,
                }
                logger.info(f"Created new user {user_id} with language '{language}'")

            self._write_user_data(users)

    async def is_new_user(self, user_id: int) -> bool:
        """
        Check if user is new (has no language preference).

        Args:
            user_id: Telegram user ID

        Returns:
            True if user is new, False otherwise
        """
        with self._lock:
            users = self._read_user_data()

            if user_id not in users:
                return True

            return users[user_id].get("language_preference") is None

    async def get_user_language_formatted(self, user_id: int) -> str:
        """
        Get user's language as a formatted display string.

        Args:
            user_id: Telegram user ID

        Returns:
            Localized language name (e.g., "Русский" or "English")
        """
        language = await self.get_user_language(user_id)

        if language == "ru":
            return "Русский"
        return "English"

    def get_language_selection_keyboard(
        self,
        language: str,
        selected_callback_prefix: str = "lang",
    ) -> dict[str, Any]:
        """
        Generate inline keyboard for language selection.

        Args:
            language: Language for button labels
            selected_callback_prefix: Prefix for callback data

        Returns:
            Keyboard markup dict for aiogram
        """
        # Create inline keyboard
        keyboard = {
            "inline_keyboard": [
                [
                    {
                        "text": "🇷🇺 Русский",
                        "callback_data": f"{selected_callback_prefix}:ru",
                    },
                    {
                        "text": "🇺🇸 English",
                        "callback_data": f"{selected_callback_prefix}:en",
                    },
                ]
            ]
        }

        return keyboard


# Singleton instance for convenience
_default_middleware: LanguageMiddleware | None = None


def get_language_middleware() -> LanguageMiddleware:
    """
    Get the default language middleware instance.

    Returns:
        LanguageMiddleware instance
    """
    global _default_middleware
    if _default_middleware is None:
        _default_middleware = LanguageMiddleware()
    return _default_middleware
