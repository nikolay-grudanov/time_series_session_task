"""
Telegram bot handler for language selection flow.

Handles:
- Language selection during initial /start for new users
- Language change via /lang command
- Callback queries for language selection buttons
"""

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from src.i18n.constants import MessageKey
from src.i18n.loader import MessageLoader
from src.i18n.middleware import LanguageMiddleware, get_language_middleware

logger = logging.getLogger(__name__)

# Router for language-related handlers
router = Router()

# Initialize i18n components
_message_loader: MessageLoader | None = None
_middleware: LanguageMiddleware | None = None


def _get_loader() -> MessageLoader:
    """Get or create MessageLoader singleton."""
    global _message_loader
    if _message_loader is None:
        _message_loader = MessageLoader()
    return _message_loader


def _get_middleware() -> LanguageMiddleware:
    """Get or create LanguageMiddleware singleton."""
    global _middleware
    if _middleware is None:
        _middleware = get_language_middleware()
    return _middleware


def create_language_keyboard(
    language: str,
    callback_prefix: str = "lang",
) -> InlineKeyboardMarkup:
    """
    Create inline keyboard for language selection.

    Args:
        language: Language for button labels
        callback_prefix: Prefix for callback data

    Returns:
        InlineKeyboardMarkup with language options
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🇷🇺 Русский",
                    callback_data=f"{callback_prefix}:ru",
                ),
                InlineKeyboardButton(
                    text="🇺🇸 English",
                    callback_data=f"{callback_prefix}:en",
                ),
            ]
        ]
    )
    return keyboard


async def send_language_selection(
    message: Message,
    language: str,
) -> None:
    """
    Send language selection message with keyboard.

    Args:
        message: Original message to reply to
        language: Language for message text
    """
    loader = _get_loader()

    welcome_text = loader.get(MessageKey.start_title, language)
    description_text = loader.get(MessageKey.start_description, language)
    select_prompt = loader.get(MessageKey.select_lang_prompt, language)

    text = f"{welcome_text}\n\n{description_text}\n\n{select_prompt}"
    keyboard = create_language_keyboard(language)

    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")


async def send_language_confirmation(
    message_or_callback: Message | CallbackQuery,
    language: str,
    edit_message: bool = False,
) -> None:
    """
    Send language selection confirmation.

    Args:
        message_or_callback: Message or callback query
        language: Selected language code
        edit_message: Whether to edit existing message (for callbacks)
    """
    loader = _get_loader()

    if language == "ru":
        confirmation_text = loader.get(MessageKey.lang_selected_ru, language)
    else:
        confirmation_text = loader.get(MessageKey.lang_selected_en, language)

    # Remove keyboard after language selection - show only confirmation text
    if edit_message and hasattr(message_or_callback, "message"):
        try:
            msg = message_or_callback.message
            if msg and hasattr(msg, "edit_text"):
                await msg.edit_text(confirmation_text)
        except Exception:
            pass
        await message_or_callback.answer()
    else:
        await message_or_callback.answer(confirmation_text)


async def handle_language_selection(
    callback: CallbackQuery,
    selected_language: str,
) -> None:
    """
    Handle language selection callback.

    Args:
        callback: CallbackQuery from inline button
        selected_language: Selected language code ('ru' or 'en')
    """
    user_id = callback.from_user.id if callback.from_user else 0
    middleware = _get_middleware()
    loader = _get_loader()

    try:
        # Save language preference
        await middleware.set_user_language(user_id, selected_language)

        # Send confirmation
        await send_language_confirmation(
            callback,
            selected_language,
            edit_message=True,
        )

        logger.info(f"User {user_id} selected language: {selected_language}")

    except Exception as e:
        logger.error(f"Error saving language preference for user {user_id}: {e!s}")

        error_text = loader.get(MessageKey.error_generic, selected_language)

        if hasattr(callback, "message"):
            await callback.message.edit_text(error_text)
        await callback.answer(error_text, show_alert=True)


@router.callback_query(lambda c: c.data and c.data.startswith("lang:"))
async def callback_language_selected(callback: CallbackQuery) -> None:
    """
    Handle language selection callback query.

    Pattern: lang:ru or lang:en
    """
    if not callback.data:
        await callback.answer("Invalid callback", show_alert=True)
        return

    # Parse selected language
    _, lang_code = callback.data.split(":", 1)

    if lang_code not in ["ru", "en"]:
        await callback.answer("Invalid language", show_alert=True)
        return

    await handle_language_selection(callback, lang_code)


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """
    Handle /start command.
    For new users: show language selection.
    For existing users: show welcome message in their language.
    """
    user_id = message.from_user.id if message.from_user else 0
    middleware = _get_middleware()
    loader = _get_loader()

    try:
        # Check if user is new (no language preference)
        is_new = await middleware.is_new_user(user_id)

        if is_new:
            # New user: show language selection
            await send_language_selection(message, "ru")
            logger.info(f"New user {user_id}, showed language selection")
        else:
            # Existing user: get their language and show welcome
            language = await middleware.get_user_language(user_id)

            # Get localized welcome message
            welcome_text = loader.get(MessageKey.start_title, language)
            description_text = loader.get(MessageKey.start_description, language)
            available_commands = loader.get(
                MessageKey.start_available_commands, language
            )
            example_text = loader.get(MessageKey.start_example, language)

            text = f"{welcome_text}\n\n{description_text}\n\n{available_commands}\n\n{example_text}"

            await message.answer(text, parse_mode="Markdown")

            logger.info(f"Existing user {user_id} started, language: {language}")

    except Exception as e:
        logger.error(f"Error handling /start for user {user_id}: {e!s}")

        # Fallback to Russian
        error_text = loader.get(MessageKey.error_generic, "ru")
        await message.answer(error_text)


@router.message(Command("lang"))
async def cmd_language(message: Message) -> None:
    """
    Handle /lang command.
    Shows language selection menu for changing language.
    """
    user_id = message.from_user.id if message.from_user else 0
    middleware = _get_middleware()
    loader = _get_loader()

    try:
        # Get current language
        current_language = await middleware.get_user_language(user_id)
        current_lang_name = await middleware.get_user_language_formatted(user_id)

        # Get localized messages
        settings_title = loader.get(MessageKey.settings_title, current_language)
        current_lang_text = loader.get(
            MessageKey.current_lang, current_language, lang=current_lang_name
        )
        select_prompt = loader.get(MessageKey.select_lang_prompt, current_language)

        text = f"{settings_title}\n\n{current_lang_text}\n\n{select_prompt}"
        keyboard = create_language_keyboard(current_language)

        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

        logger.info(
            f"User {user_id} requested language change, current: {current_language}"
        )

    except Exception as e:
        logger.error(f"Error handling /lang for user {user_id}: {e!s}")

        error_text = loader.get(MessageKey.error_generic, "ru")
        await message.answer(error_text)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """
    Handle /help command.
    Shows help message in user's language.
    """
    user_id = message.from_user.id if message.from_user else 0
    logger.info(f"Help command from user {user_id}")

    middleware = _get_middleware()
    loader = _get_loader()

    try:
        language = await middleware.get_user_language(user_id)
        logger.debug(f"User {user_id} language: {language}")

        help_title = loader.get(MessageKey.help_title, language)
        help_stocks = loader.get(MessageKey.help_stocks, language)
        help_forecast = loader.get(MessageKey.help_forecast, language)
        help_model_status = loader.get(MessageKey.help_model_status, language)
        help_lang = loader.get(MessageKey.help_lang, language)
        help_input_format = loader.get(MessageKey.help_input_format, language)
        help_examples = loader.get(MessageKey.help_examples, language)

        text = (
            f"{help_title}\n\n"
            f"{help_stocks}\n\n"
            f"{help_forecast}\n\n"
            f"{help_model_status}\n\n"
            f"{help_lang}\n\n"
            f"{help_input_format}\n\n"
            f"{help_examples}"
        )

        await message.answer(text, parse_mode="Markdown")

        logger.info(f"Displayed help to user {user_id}, language: {language}")

    except Exception as e:
        logger.error(f"Error handling /help for user {user_id}: {e!s}", exc_info=True)

        try:
            error_text = loader.get(MessageKey.error_generic, "ru")
        except Exception:
            error_text = "Произошла ошибка. Попробуйте снова."
        await message.answer(error_text)


async def process_user_message_in_language(
    user_id: int,
    text: str,
) -> str:
    """
    Get localized text for a user.

    This is a helper for other handlers to use.

    Args:
        user_id: Telegram user ID
        text_key: Message key to localize
        **kwargs: Format string parameters

    Returns:
        Localized text string
    """
    middleware = _get_middleware()
    await middleware.get_user_language(user_id)
    return text


def get_welcome_text_for_user(user_id: int) -> str:
    """
    Get welcome text for a user (synchronous version).

    Args:
        user_id: Telegram user ID

    Returns:
        Localized welcome text
    """
    # This is a simplified version - full implementation would be async
    loader = _get_loader()
    return loader.get(MessageKey.start_title, "ru")
