"""
Integration tests for complete language selection user journeys.

Tests cover:
- New user language selection flow
- Existing user language change flow
- Language preference persistence
- Edge cases and error handling
"""

import asyncio
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram import Bot, Dispatcher
from aiogram.methods import SendMessage
from aiogram.types import (
    CallbackQuery,
    Chat,
    Message,
    Update,
    User,
)

from src.i18n.constants import MessageKey
from src.i18n.loader import MessageLoader
from src.i18n.middleware import LanguageMiddleware


@contextmanager
def temp_middleware_context() -> Generator[LanguageMiddleware, None, None]:
    """Context manager for temporary middleware with automatic cleanup."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_file = Path(tmpdir) / "test_users.csv"
        middleware = LanguageMiddleware(data_file=data_file)
        yield middleware


class TestLanguageSelectionFlow:
    """Integration tests for language selection user journey."""

    @pytest.fixture
    def mock_message(self) -> MagicMock:
        """Create a mock Telegram message."""
        message = MagicMock(spec=Message)
        message.from_user = MagicMock(spec=User)
        message.from_user.id = 12345
        message.from_user.first_name = "Test"
        message.chat = MagicMock(spec=Chat)
        message.chat.id = 12345
        message.text = "/start"
        message.answer = AsyncMock()
        return message

    @pytest.fixture
    def mock_callback(self) -> MagicMock:
        """Create a mock Telegram callback query."""
        callback = MagicMock(spec=CallbackQuery)
        callback.from_user = MagicMock(spec=User)
        callback.from_user.id = 12345
        callback.data = "lang:ru"
        callback.message = MagicMock()
        callback.message.edit_text = AsyncMock()
        callback.answer = AsyncMock()
        return callback

    def test_new_user_language_selection_flow(self, mock_message: MagicMock) -> None:
        """
        Test complete flow for new user language selection.

        Scenario:
        1. User starts conversation with /start
        2. Bot detects new user (no language preference)
        3. Bot shows language selection menu
        4. User selects language
        5. Language preference is saved
        6. Confirmation message shown
        """
        loader = MessageLoader()

        with temp_middleware_context() as middleware:

            async def run_test() -> dict:
                # Step 1: Check user is new
                is_new = await middleware.is_new_user(12345)
                assert is_new, "User should be identified as new"

                # Step 2: Get language selection message
                select_prompt = loader.get(MessageKey.select_lang_prompt, "ru")

                # Step 3: Simulate language selection
                await middleware.set_user_language(12345, "ru")

                # Step 4: Verify language is saved
                language = await middleware.get_user_language(12345)
                assert language == "ru", "Language should be saved as 'ru'"

                # Step 5: Get confirmation
                confirmation = loader.get(MessageKey.lang_selected_ru, "ru")

                return {
                    "is_new": is_new,
                    "language": language,
                    "confirmation": confirmation,
                }

            result = asyncio.run(run_test())

            assert result["is_new"] is True
            assert result["language"] == "ru"
            assert "русский" in result["confirmation"].lower()

    def test_existing_user_language_change_flow(self, mock_message: MagicMock) -> None:
        """
        Test complete flow for existing user language change.

        Scenario:
        1. User has existing language preference
        2. User sends /lang command
        3. Bot shows current language and selection menu
        4. User selects different language
        5. Language preference is updated
        6. Confirmation in new language shown
        """
        loader = MessageLoader()

        with temp_middleware_context() as middleware:

            async def run_test() -> dict:
                # Step 1: Set initial language
                await middleware.set_user_language(12345, "en")
                initial_lang = await middleware.get_user_language(12345)
                assert initial_lang == "en"

                # Step 2: User wants to change language
                current_lang_name = await middleware.get_user_language_formatted(12345)

                # Step 3: Change to Russian
                await middleware.set_user_language(12345, "ru")

                # Step 4: Verify update
                new_lang = await middleware.get_user_language(12345)
                assert new_lang == "ru"

                # Step 5: Get confirmation in new language
                confirmation = loader.get(MessageKey.lang_selected_ru, "ru")

                return {
                    "initial": initial_lang,
                    "new": new_lang,
                    "confirmation": confirmation,
                }

            result = asyncio.run(run_test())

            assert result["initial"] == "en"
            assert result["new"] == "ru"
            assert "русский" in result["confirmation"].lower()

    def test_language_persistence_across_restarts(self) -> None:
        """Test that language preference persists when middleware is recreated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_file = Path(tmpdir) / "test_users.csv"

            # First session
            middleware1 = LanguageMiddleware(data_file=data_file)

            async def set_language() -> None:
                await middleware1.set_user_language(12345, "ru")
                language = await middleware1.get_user_language(12345)
                assert language == "ru"

            asyncio.run(set_language())

            # Simulate restart by creating new middleware with same file
            middleware2 = LanguageMiddleware(data_file=data_file)

            async def check_persistence() -> str:
                return await middleware2.get_user_language(12345)

            persisted_language = asyncio.run(check_persistence())
            assert persisted_language == "ru"

    def test_zero_mixed_language_responses(self, mock_message: MagicMock) -> None:
        """Test that bot responses are always in a single language."""

        loader = MessageLoader()

        with temp_middleware_context() as middleware:

            async def run_test() -> dict:
                # Set user to Russian
                await middleware.set_user_language(12345, "ru")

                # Get multiple messages in same language
                welcome = loader.get(MessageKey.start_title, "ru")
                help_title = loader.get(MessageKey.help_title, "ru")
                error_msg = loader.get(MessageKey.error_generic, "ru")

                # Check for Cyrillic letters (not just any high unicode like emojis)
                welcome_has_cyrillic = any(1040 <= ord(c) <= 1103 for c in welcome)
                help_has_cyrillic = any(1040 <= ord(c) <= 1103 for c in help_title)
                error_has_cyrillic = any(1040 <= ord(c) <= 1103 for c in error_msg)

                # Set user to English
                await middleware.set_user_language(12345, "en")

                welcome_en = loader.get(MessageKey.start_title, "en")
                help_en = loader.get(MessageKey.help_title, "en")

                # English messages should NOT contain Cyrillic letters
                welcome_no_cyrillic = not any(
                    1040 <= ord(c) <= 1103 for c in welcome_en
                )
                help_no_cyrillic = not any(1040 <= ord(c) <= 1103 for c in help_en)

                return {
                    "ru_welcome_cyrillic": welcome_has_cyrillic,
                    "ru_help_cyrillic": help_has_cyrillic,
                    "ru_error_cyrillic": error_has_cyrillic,
                    "en_welcome_clean": welcome_no_cyrillic,
                    "en_help_clean": help_no_cyrillic,
                }

            result = asyncio.run(run_test())

            # All Russian messages should contain Cyrillic letters
            assert (
                result["ru_welcome_cyrillic"]
                and result["ru_help_cyrillic"]
                and result["ru_error_cyrillic"]
            ), f"Russian language responses should contain Cyrillic letters: {result}"

            # All English messages should NOT contain Cyrillic letters
            assert result["en_welcome_clean"] and result["en_help_clean"], (
                f"English language responses should not contain Cyrillic letters: {result}"
            )

    def test_invalid_language_selection_handling(self) -> None:
        """Test handling of invalid language selection."""

        with temp_middleware_context() as middleware:

            async def run_test() -> None:
                # Test invalid language code
                try:
                    await middleware.set_user_language(12345, "fr")
                    pytest.fail("Should raise ValueError for invalid language")
                except ValueError as e:
                    assert "Unsupported language" in str(e)

                # Language should remain default
                language = await middleware.get_user_language(12345)
                assert language == "ru", (
                    "Language should remain default after failed update"
                )

            asyncio.run(run_test())


class TestMessageLoaderIntegration:
    """Integration tests for MessageLoader with handlers."""

    def test_all_stocks_handler_messages_available(self) -> None:
        """Test that all stocks handler messages are available."""
        loader = MessageLoader()

        required_keys = [
            MessageKey.stocks_title,
            MessageKey.stocks_empty,
            MessageKey.stocks_showing,
            MessageKey.stocks_tap_to_use,
            MessageKey.stocks_forecast_example,
            MessageKey.stocks_error_loading,
            MessageKey.pagination_invalid_page,
            MessageKey.stocks_not_found,
            MessageKey.stock_selected,
            MessageKey.stock_selection_error,
            MessageKey.search_title,
            MessageKey.search_prompt,
            MessageKey.search_example,
        ]

        for key in required_keys:
            msg_ru = loader.get(key, "ru")
            msg_en = loader.get(key, "en")

            assert msg_ru, f"Missing Russian translation for {key}"
            assert msg_en, f"Missing English translation for {key}"
            assert len(msg_ru) > 0, f"Empty Russian translation for {key}"
            assert len(msg_en) > 0, f"Empty English translation for {key}"

    def test_all_status_handler_messages_available(self) -> None:
        """Test that all status handler messages are available."""
        loader = MessageLoader()

        required_keys = [
            MessageKey.model_status_title,
            MessageKey.status_scheduler_enabled,
            MessageKey.status_scheduler_disabled,
            MessageKey.status_retraining_in_progress,
            MessageKey.status_retraining_idle,
            MessageKey.status_last_retraining,
            MessageKey.status_last_retraining_never,
            MessageKey.status_next_scheduled,
            MessageKey.status_next_scheduled_never,
            MessageKey.status_error,
            MessageKey.status_models_info,
            MessageKey.retraining_history_title,
            MessageKey.no_history,
        ]

        for key in required_keys:
            msg_ru = loader.get(key, "ru")
            msg_en = loader.get(key, "en")

            assert msg_ru, f"Missing Russian translation for {key}"
            assert msg_en, f"Missing English translation for {key}"

    def test_all_forecast_messages_available(self) -> None:
        """Test that all forecast flow messages are available."""
        loader = MessageLoader()

        required_keys = [
            MessageKey.forecast_usage_error,
            MessageKey.forecast_format,
            MessageKey.forecast_example,
            MessageKey.forecast_downloading,
            MessageKey.forecast_no_data,
            MessageKey.forecast_generating_v2,
            MessageKey.forecast_analyzing,
            MessageKey.forecast_calculating,
            MessageKey.forecast_result_caption,
            MessageKey.forecast_expected_change,
            MessageKey.forecast_last_price,
            MessageKey.forecast_end_price,
            MessageKey.forecast_best_model,
            MessageKey.forecast_recommendations_title,
            MessageKey.profit_analysis_title,
            MessageKey.profit_potential,
            MessageKey.roi_label,
            MessageKey.active_vs_hold,
            MessageKey.effectiveness,
        ]

        for key in required_keys:
            msg_ru = loader.get(key, "ru")
            msg_en = loader.get(key, "en")

            assert msg_ru, f"Missing Russian translation for {key}"
            assert msg_en, f"Missing English translation for {key}"


class TestAcceptanceScenarios:
    """Tests for verifying acceptance scenarios from specification."""

    def test_us1_scenario_1_new_user_language_selection(self) -> None:
        """
        US1 Scenario 1: New user starts → bot shows language selection menu

        Requirements: FR-001, FR-002, FR-003
        """
        loader = MessageLoader()

        async def run_test() -> bool:
            middleware = LanguageMiddleware()
            user_id = 99999

            # Check user is new
            is_new = await middleware.is_new_user(user_id)
            if not is_new:
                return False

            # Get language selection message
            welcome = loader.get(MessageKey.start_title, "ru")
            select_prompt = loader.get(MessageKey.select_lang_prompt, "ru")

            # Both should be non-empty
            return len(welcome) > 0 and len(select_prompt) > 0

        result = asyncio.run(run_test())
        assert result, "US1 Scenario 1 should work: new user gets language menu"

    def test_us1_scenario_2_russian_selection(self) -> None:
        """
        US1 Scenario 2: User selects Russian → all messages in Russian

        Requirements: FR-004, SC-001
        """
        loader = MessageLoader()

        # Messages should be in Russian
        welcome_ru = loader.get(MessageKey.start_title, "ru")
        help_ru = loader.get(MessageKey.help_title, "ru")
        error_ru = loader.get(MessageKey.error_generic, "ru")

        # Verify Russian content (Cyrillic)
        assert "Бот" in welcome_ru or "Прогноз" in welcome_ru
        assert "Помощь" in help_ru
        assert "ошибка" in error_ru.lower()

    def test_us1_scenario_3_english_selection(self) -> None:
        """
        US1 Scenario 3: User selects English → all messages in English

        Requirements: FR-004, SC-001
        """
        loader = MessageLoader()

        # Messages should be in English
        welcome_en = loader.get(MessageKey.start_title, "en")
        help_en = loader.get(MessageKey.help_title, "en")
        error_en = loader.get(MessageKey.error_generic, "en")

        # Verify English content
        assert "Hello" in welcome_en or "Stock" in welcome_en
        assert "Help" in help_en
        assert "error" in error_en.lower() or "Error" in error_en

    def test_us2_scenario_1_language_change_command(self) -> None:
        """
        US2 Scenario 1: User with preference sends /lang → sees current language and menu

        Requirements: FR-007
        """
        loader = MessageLoader()

        # Should be able to get settings and language selection messages
        settings_title = loader.get(MessageKey.settings_title, "ru")
        current_lang = loader.get(MessageKey.current_lang, "ru", lang="Русский")
        select_prompt = loader.get(MessageKey.select_lang_prompt, "ru")

        assert len(settings_title) > 0
        assert "Русский" in current_lang
        assert len(select_prompt) > 0

    def test_sc_005_zero_mixed_language_responses(self) -> None:
        """
        SC-005: Zero mixed-language responses

        All user-facing messages should be completely in one language.
        """
        loader = MessageLoader()

        # Test multiple messages in each language
        ru_messages = [
            loader.get(MessageKey.start_title, "ru"),
            loader.get(MessageKey.help_title, "ru"),
            loader.get(MessageKey.error_generic, "ru"),
            loader.get(MessageKey.stocks_title, "ru"),
        ]

        en_messages = [
            loader.get(MessageKey.start_title, "en"),
            loader.get(MessageKey.help_title, "en"),
            loader.get(MessageKey.error_generic, "en"),
            loader.get(MessageKey.stocks_title, "en"),
        ]

        # Russian messages should be predominantly Cyrillic
        for msg in ru_messages:
            cyrillic_count = sum(1 for c in msg if ord(c) > 127)
            latin_count = sum(1 for c in msg if ord(c) < 128 and c.isalpha())
            if latin_count > 0:
                assert cyrillic_count > 0, (
                    f"Russian message should have Cyrillic: {msg}"
                )

        # English messages should be predominantly Latin
        for msg in en_messages:
            latin_count = sum(1 for c in msg if ord(c) < 128 and c.isalpha())
            assert latin_count > 0, f"English message should have Latin: {msg}"
