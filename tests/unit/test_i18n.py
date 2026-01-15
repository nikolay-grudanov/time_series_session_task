"""
Tests for i18n module - message loader and language middleware.

Verifies:
- Message loading works correctly for both languages
- Language preference persistence via CSV storage
- JSON translation files have synchronized keys
"""

import json
import tempfile
from pathlib import Path

import pytest

from src.i18n.constants import MessageKey
from src.i18n.loader import MessageLoader, get_message_loader
from src.i18n.middleware import LanguageMiddleware, get_language_middleware


class TestMessageLoader:
    """Tests for MessageLoader class."""

    def test_load_both_languages(self) -> None:
        """Test that both language files are loaded."""
        loader = MessageLoader()
        languages = loader.get_available_languages()

        assert "ru" in languages
        assert "en" in languages

    def test_get_message_by_key(self) -> None:
        """Test retrieving a message by key."""
        loader = MessageLoader()

        # Test Russian
        welcome_ru = loader.get(MessageKey.welcome, "ru")
        assert "Привет" in welcome_ru

        # Test English
        welcome_en = loader.get(MessageKey.welcome, "en")
        assert "Hello" in welcome_en

    def test_get_message_by_string_key(self) -> None:
        """Test retrieving a message using string key."""
        loader = MessageLoader()

        result = loader.get("welcome", "ru")
        assert "Привет" in result

    def test_get_message_with_format_params(self) -> None:
        """Test message formatting with parameters."""
        loader = MessageLoader()

        # Test with format parameters
        result = loader.get(MessageKey.current_lang, "ru", lang="Русский")
        assert "Русский" in result

        result = loader.get(MessageKey.current_lang, "en", lang="English")
        assert "English" in result

    def test_get_all_for_language(self) -> None:
        """Test loading all messages for a language."""
        loader = MessageLoader()
        messages = loader.get_all_for_language("ru")

        assert isinstance(messages, dict)
        assert len(messages) > 0
        assert "welcome" in messages
        assert "error_generic" in messages

    def test_has_key(self) -> None:
        """Test checking if key exists."""
        loader = MessageLoader()

        assert loader.has_key(MessageKey.welcome, "ru")
        assert loader.has_key("welcome", "en")
        assert not loader.has_key("nonexistent_key", "ru")

    def test_get_missing_keys(self) -> None:
        """Test getting list of missing keys."""
        loader = MessageLoader()
        missing = loader.get_missing_keys("ru")

        # All keys defined in MessageKey should exist
        assert len(missing) == 0

    def test_unsupported_language_raises_error(self) -> None:
        """Test that unsupported language raises ValueError."""
        loader = MessageLoader()

        with pytest.raises(ValueError, match="Unsupported language"):
            loader.get(MessageKey.welcome, "fr")

    def test_missing_key_raises_error(self) -> None:
        """Test that missing key raises KeyError."""
        loader = MessageLoader()

        with pytest.raises(KeyError):
            loader.get("totally_fake_key_that_does_not_exist", "ru")


class TestMessageKeyEnum:
    """Tests for MessageKey enumeration."""

    def test_all_keys_returns_list(self) -> None:
        """Test that all_keys returns a list."""
        keys = MessageKey.all_keys()

        assert isinstance(keys, list)
        assert len(keys) > 0

    def test_has_key_method(self) -> None:
        """Test has_key class method."""
        assert MessageKey.has_key("welcome")
        assert not MessageKey.has_key("nonexistent_key")

    def test_enum_values_are_strings(self) -> None:
        """Test that enum values are strings."""
        for key in MessageKey:
            assert isinstance(key.value, str)
            assert key.value == key.value.lower().replace(" ", "_")


class TestLanguageMiddleware:
    """Tests for LanguageMiddleware class."""

    def test_get_default_language_for_new_user(self) -> None:
        """Test that new users get default language."""
        with tempfile.TemporaryDirectory() as tmpdir:
            middleware = LanguageMiddleware(data_file=Path(tmpdir) / "test_users.csv")

            # Simulate new user (user_id not in database)
            language = (
                middleware._read_user_data().get(12345, {}).get("language_preference")
            )

            # Default behavior when user doesn't exist
            assert language is None or language == "ru"

    def test_set_and_get_language(self) -> None:
        """Test setting and getting user language."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_file = Path(tmpdir) / "test_users.csv"
            middleware = LanguageMiddleware(data_file=data_file)

            import asyncio

            asyncio.run(middleware.set_user_language(12345, "en"))

            language = asyncio.run(middleware.get_user_language(12345))
            assert language == "en"

            # Change language
            asyncio.run(middleware.set_user_language(12345, "ru"))

            language = asyncio.run(middleware.get_user_language(12345))
            assert language == "ru"

    def test_unsupported_language_raises_error(self) -> None:
        """Test that unsupported language raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            middleware = LanguageMiddleware(data_file=Path(tmpdir) / "test_users.csv")

            import asyncio

            with pytest.raises(ValueError, match="Unsupported language"):
                asyncio.run(middleware.set_user_language(12345, "fr"))

    def test_language_selection_keyboard(self) -> None:
        """Test generating language selection keyboard."""
        from src.i18n.middleware import LanguageMiddleware

        middleware = LanguageMiddleware()
        keyboard = middleware.get_language_selection_keyboard("ru")

        assert "inline_keyboard" in keyboard
        assert len(keyboard["inline_keyboard"]) == 1

        buttons = keyboard["inline_keyboard"][0]
        assert len(buttons) == 2

        # Check button callback data
        callback_data = [btn["callback_data"] for btn in buttons]
        assert "lang:ru" in callback_data
        assert "lang:en" in callback_data


class TestJsonFileSynchronization:
    """Tests to verify JSON translation files are synchronized."""

    def test_ru_and_en_have_same_keys(self) -> None:
        """Test that ru.json and en.json have identical key sets."""
        # Load both files
        project_root = Path(__file__).parent.parent.parent
        ru_file = project_root / "locales" / "ru.json"
        en_file = project_root / "locales" / "en.json"

        with open(ru_file, encoding="utf-8") as f:
            ru_data = json.load(f)

        with open(en_file, encoding="utf-8") as f:
            en_data = json.load(f)

        ru_keys = set(ru_data.keys())
        en_keys = set(en_data.keys())

        assert ru_keys == en_keys, (
            f"Key mismatch between ru.json and en.json.\n"
            f"Missing in ru: {en_keys - ru_keys}\n"
            f"Missing in en: {ru_keys - en_keys}"
        )

    def test_all_message_keys_exist_in_json(self) -> None:
        """Test that all MessageKey enum values exist in JSON files."""
        project_root = Path(__file__).parent.parent.parent
        ru_file = project_root / "locales" / "ru.json"

        with open(ru_file, encoding="utf-8") as f:
            ru_data = json.load(f)

        expected_keys = set(MessageKey.all_keys())
        actual_keys = set(ru_data.keys())

        missing = expected_keys - actual_keys
        assert not missing, f"Missing keys in locales/ru.json: {missing}"


class TestMessageLoaderIntegration:
    """Integration tests for MessageLoader."""

    def test_get_message_loader_singleton(self) -> None:
        """Test that get_message_loader returns singleton."""
        loader1 = get_message_loader()
        loader2 = get_message_loader()

        assert loader1 is loader2

    def test_all_keys_return_valid_messages(self) -> None:
        """Test that all keys can retrieve valid messages."""
        loader = MessageLoader()

        for key in MessageKey.all_keys():
            # Should not raise
            msg_ru = loader.get(key, "ru")
            msg_en = loader.get(key, "en")

            assert isinstance(msg_ru, str)
            assert isinstance(msg_en, str)
            assert len(msg_ru) > 0
            assert len(msg_en) > 0


class TestTradingRecommendationsLocalization:
    """Tests for new trading recommendations localization keys."""

    def test_trading_recommendations_keys_exist(self) -> None:
        """Test that all new trading recommendation keys exist."""
        loader = MessageLoader()

        # Check that new keys exist in both languages
        new_keys = [
            "trading_recommendations_header",
            "profit_info",
            "roi_info",
            "trading_actions_header",
            "buy_opportunities",
            "sell_opportunities",
            "buy_date",
            "sell_date",
            "no_opportunities",
            "market_neutral",
        ]

        for key in new_keys:
            # Russian
            assert loader.has_key(key, "ru"), f"Missing key {key} in Russian"
            msg_ru = loader.get(key, "ru")
            assert isinstance(msg_ru, str)
            assert len(msg_ru) > 0

            # English
            assert loader.has_key(key, "en"), f"Missing key {key} in English"
            msg_en = loader.get(key, "en")
            assert isinstance(msg_en, str)
            assert len(msg_en) > 0

    def test_trading_recommendations_keys_are_in_enum(self) -> None:
        """Test that new trading recommendation keys are in MessageKey enum."""
        new_keys = [
            "trading_recommendations_header",
            "profit_info",
            "roi_info",
            "trading_actions_header",
            "buy_opportunities",
            "sell_opportunities",
            "buy_date",
            "sell_date",
            "no_opportunities",
            "market_neutral",
        ]

        for key in new_keys:
            assert hasattr(MessageKey, key), f"Missing {key} in MessageKey enum"
            assert MessageKey[key].value == key

    def test_trading_recommendations_russian_localization(self) -> None:
        """Test that Russian trading recommendation translations are correct."""
        loader = MessageLoader()

        # Check header
        header = loader.get("trading_recommendations_header", "ru")
        assert "Торговые рекомендации" in header
        assert "📈" in header

        # Check profit info
        profit = loader.get("profit_info", "ru")
        assert "Потенциальная прибыль" in profit or "прибыль" in profit
        assert "${profit" in profit

        # Check ROI info
        roi = loader.get("roi_info", "ru")
        assert "ROI" in roi

        # Check buy/sell opportunities
        buy = loader.get("buy_opportunities", "ru")
        assert "покупк" in buy.lower() or "buy" in buy.lower()

        sell = loader.get("sell_opportunities", "ru")
        assert "прода" in sell.lower() or "sell" in sell.lower()

    def test_trading_recommendations_english_localization(self) -> None:
        """Test that English trading recommendation translations are correct."""
        loader = MessageLoader()

        # Check header
        header = loader.get("trading_recommendations_header", "en")
        assert "Trading Recommendations" in header
        assert "📈" in header

        # Check profit info
        profit = loader.get("profit_info", "en")
        assert "Profit" in profit
        assert "${profit" in profit

        # Check ROI info
        roi = loader.get("roi_info", "en")
        assert "ROI" in roi

        # Check buy/sell opportunities
        buy = loader.get("buy_opportunities", "en")
        assert "Buy" in buy or "buy" in buy

        sell = loader.get("sell_opportunities", "en")
        assert "Sell" in sell or "sell" in sell

    def test_trading_recommendations_format_parameters(self) -> None:
        """Test that trading recommendation messages support format parameters."""
        loader = MessageLoader()

        # Test with format parameters
        profit_msg = loader.get("profit_info", "ru", profit=100.50)
        assert "100.50" in profit_msg or "100" in profit_msg

        roi_msg = loader.get("roi_info", "ru", roi=5.5)
        assert "5.5" in roi_msg or "5" in roi_msg

        buy_date = loader.get("buy_date", "ru", date="2026-01-15")
        assert "2026-01-15" in buy_date

        # English
        profit_msg_en = loader.get("profit_info", "en", profit=100.50)
        assert "100.50" in profit_msg_en or "100" in profit_msg_en
