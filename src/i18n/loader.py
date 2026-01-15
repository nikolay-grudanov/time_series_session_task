"""
Message loader for i18n module.

Loads translated messages from JSON files and provides access by key and language.
"""

import json
import logging
from pathlib import Path
from typing import Any

from src.i18n.constants import MessageKey

logger = logging.getLogger(__name__)


class MessageLoader:
    """
    Load and retrieve localized messages from JSON translation files.

    Supports:
    - Loading messages for 'ru' and 'en' languages
    - Format string interpolation for dynamic values
    - Fallback to default language on missing keys
    - Validation of language and key existence
    """

    def __init__(
        self,
        locales_dir: str | Path | None = None,
        default_language: str = "ru",
    ) -> None:
        """
        Initialize the message loader.

        Args:
            locales_dir: Directory containing locale JSON files.
                         Defaults to 'locales' in project root.
            default_language: Default language code ('ru' or 'en').
        """
        if locales_dir is None:
            # Default to locales directory relative to project root
            project_root = Path(__file__).parent.parent.parent
            locales_dir = project_root / "locales"

        self._locales_dir = Path(locales_dir)
        self._default_language = default_language
        self._messages: dict[str, dict[str, str]] = {}

        # Load all language files
        self._load_all_messages()

    def _load_all_messages(self) -> None:
        """Load messages from all available language files."""
        supported_languages = ["ru", "en"]

        for lang in supported_languages:
            lang_file = self._locales_dir / f"{lang}.json"
            if lang_file.exists():
                try:
                    with open(lang_file, encoding="utf-8") as f:
                        messages = json.load(f)
                        self._messages[lang] = messages
                        logger.info(
                            f"Loaded {len(messages)} messages for language '{lang}'"
                        )
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse {lang_file}: {e}")
                    self._messages[lang] = {}
            else:
                logger.warning(f"Locale file not found: {lang_file}")
                self._messages[lang] = {}

    def _get_language_messages(self, language: str) -> dict[str, str]:
        """
        Get messages for a specific language with fallback.

        Args:
            language: ISO 639-1 language code ('ru' or 'en')

        Returns:
            Dictionary of message keys to translated strings
        """
        # Normalize language code
        lang = language.lower().strip()
        if lang not in self._messages:
            logger.warning(
                f"Unsupported language: {lang}, using default '{self._default_language}'"
            )
            lang = self._default_language

        return self._messages.get(lang, {})

    def get(self, key: str | MessageKey, language: str, **kwargs: Any) -> str:
        """
        Retrieve a localized message by key.

        Args:
            key: Message key (e.g., 'welcome', 'error_generic') or MessageKey enum
            language: ISO 639-1 language code ('ru' or 'en')
            **kwargs: Format string parameters for interpolation

        Returns:
            Localized message text with parameters substituted

        Raises:
            KeyError: If key not found in the language file
            ValueError: If language is not supported
        """
        # Convert MessageKey enum to string if needed
        if isinstance(key, MessageKey):
            key_str = key.value
        else:
            key_str = key

        # Validate language
        if language not in self._messages:
            raise ValueError(
                f"Unsupported language: {language}. Supported: {list(self._messages.keys())}"
            )

        messages = self._messages[language]

        if key_str not in messages:
            # Try default language as fallback
            default_messages = self._messages.get(self._default_language, {})
            if key_str in default_messages:
                logger.debug(
                    f"Key '{key_str}' not found in '{language}', using default"
                )
                message = default_messages[key_str]
            else:
                raise KeyError(
                    f"Message key '{key_str}' not found in language '{language}' or default '{self._default_language}'"
                )
        else:
            message = messages[key_str]

        # Format message with provided parameters
        if kwargs:
            try:
                message = message.format(**kwargs)
            except KeyError as e:
                logger.warning(f"Missing format parameter for key '{key_str}': {e}")
                raise ValueError(f"Missing format parameter: {e}")

        return message

    def get_all_for_language(self, language: str) -> dict[str, str]:
        """
        Load all messages for a specified language.

        Args:
            language: ISO 639-1 language code ('ru' or 'en')

        Returns:
            Dictionary of all message keys to translated strings
        """
        return self._get_language_messages(language).copy()

    def get_available_languages(self) -> list[str]:
        """
        Get list of available language codes.

        Returns:
            List of supported language codes
        """
        return list(self._messages.keys())

    def has_key(self, key: str | MessageKey, language: str) -> bool:
        """
        Check if a message key exists in the specified language.

        Args:
            key: Message key to check
            language: Language to check in

        Returns:
            True if key exists, False otherwise
        """
        if isinstance(key, MessageKey):
            key_str = key.value
        else:
            key_str = key

        messages = self._get_language_messages(language)
        return key_str in messages

    def get_missing_keys(self, language: str) -> list[str]:
        """
        Get list of message keys missing in the specified language.

        Compares against keys defined in MessageKey enum.

        Args:
            language: Language to check

        Returns:
            List of missing message keys
        """
        messages = self._get_language_messages(language)
        expected_keys = MessageKey.all_keys()

        missing = []
        for key in expected_keys:
            if key not in messages:
                missing.append(key)

        return missing


# Singleton instance for convenience
_default_loader: MessageLoader | None = None


def get_message_loader() -> MessageLoader:
    """
    Get the default message loader instance.

    Returns:
        MessageLoader instance
    """
    global _default_loader
    if _default_loader is None:
        _default_loader = MessageLoader()
    return _default_loader
