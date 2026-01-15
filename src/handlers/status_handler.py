"""
Telegram bot handler for /model_status command.
Displays model retraining status and metrics.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.config import settings
from src.i18n.constants import MessageKey
from src.i18n.loader import MessageLoader
from src.i18n.middleware import get_language_middleware
from src.services.scheduler_service import get_scheduler_service

logger = logging.getLogger(__name__)

# Router for status-related handlers
router = Router()

# Initialize i18n components
_message_loader: MessageLoader | None = None


def _get_loader() -> MessageLoader:
    """Get or create MessageLoader singleton."""
    global _message_loader
    if _message_loader is None:
        _message_loader = MessageLoader()
    return _message_loader


async def _get_user_language(user_id: int) -> str:
    """Get user's preferred language."""
    middleware = get_language_middleware()
    return await middleware.get_user_language(user_id)


def get_retraining_status_text(language: str) -> str:
    """
    Generate status message for /model_status command.

    Args:
        language: User's language code

    Returns:
        Formatted status message
    """
    loader = _get_loader()
    scheduler = get_scheduler_service()
    status = scheduler.get_status()

    lines = [
        loader.get(MessageKey.model_status_title, language),
        "",
    ]

    # Scheduler status
    if status["enabled"]:
        lines.append(loader.get(MessageKey.status_scheduler_enabled, language))
    else:
        lines.append(loader.get(MessageKey.status_scheduler_disabled, language))

    # Currently retraining
    if status["running"]:
        lines.append(loader.get(MessageKey.status_retraining_in_progress, language))
    else:
        lines.append(loader.get(MessageKey.status_retraining_idle, language))

    lines.append("")

    # Last retraining
    if status["last_retrain_time"]:
        last_time = datetime.fromisoformat(status["last_retrain_time"])
        last_time_str = last_time.strftime("%Y-%m-%d %H:%M:%S")
        success_status = (
            loader.get(MessageKey.status_retraining_success, language)
            if status["last_retrain_success"]
            else loader.get(MessageKey.status_retraining_failed, language)
        )
        lines.extend(
            [
                loader.get(MessageKey.status_last_retraining, language),
                f"  {last_time_str}",
                loader.get(
                    MessageKey.status_last_retraining_status,
                    language,
                    status=success_status,
                ),
            ]
        )
    else:
        lines.append(loader.get(MessageKey.status_last_retraining_never, language))

    lines.append("")

    # Next scheduled run
    next_run = scheduler.get_next_scheduled_run()
    if next_run:
        next_run_str = next_run.strftime("%Y-%m-%d %H:%M:%S")
        lines.extend(
            [
                loader.get(MessageKey.status_next_scheduled, language),
                f"  {next_run_str}",
            ]
        )
    else:
        lines.append(loader.get(MessageKey.status_next_scheduled_never, language))

    lines.append("")

    # Retry configuration
    lines.extend(
        [
            "⚙️ *Configuration:*",
            loader.get(
                MessageKey.status_config_retry, language, count=status["retry_count"]
            ),
            loader.get(
                MessageKey.status_config_interval,
                language,
                interval=settings.SCHEDULER_RETRAINING_INTERVAL,
            ),
            loader.get(
                MessageKey.status_config_fallback,
                language,
                status=loader.get(MessageKey.status_scheduler_enabled, language)
                if settings.FALLBACK_ENABLED
                else loader.get(MessageKey.status_scheduler_disabled, language),
            ),
        ]
    )

    # Error message if last run failed
    if status["last_error"]:
        lines.extend(
            [
                "",
                loader.get(MessageKey.status_error, language),
                f"  {status['last_error'][:200]}",  # Truncate long errors
            ]
        )

    lines.extend(
        [
            "",
            "---",
            loader.get(MessageKey.status_models_info, language),
            loader.get(MessageKey.status_training_data, language),
            loader.get(MessageKey.status_training_timeout, language),
        ]
    )

    return "\n".join(lines)


def get_retraining_history_text(language: str, limit: int = 5) -> str:
    """
    Generate recent retraining history text.

    Args:
        language: User's language code
        limit: Number of recent events to show

    Returns:
        Formatted history message
    """
    loader = _get_loader()
    scheduler = get_scheduler_service()
    history = scheduler.get_retraining_history(limit)

    if not history:
        return loader.get(MessageKey.no_history, language)

    lines = [loader.get(MessageKey.retraining_history_title, language), ""]

    for i, event in enumerate(history, 1):
        event_type = event.get("event_type", "unknown")
        timestamp = event.get("timestamp", "N/A")
        details = event.get("details", "")

        # Icon based on event type
        if event_type == "start":
            icon = "🚀"
        elif event_type == "success":
            icon = "✅"
        elif event_type == "failure":
            icon = "❌"
        elif event_type == "retry":
            icon = "🔄"
        else:
            icon = "📝"

        # Parse timestamp
        try:
            dt = datetime.fromisoformat(timestamp)
            time_str = dt.strftime("%m/%d %H:%M")
        except (ValueError, TypeError):
            time_str = timestamp[:16] if timestamp else "N/A"

        lines.append(f"{icon} *{time_str}* - {event_type.upper()}")

        if details:
            # Truncate long details
            if len(details) > 80:
                details = details[:77] + "..."
            lines.append(f"   {details}")

        lines.append("")

    return "\n".join(lines)


@router.message(Command("model_status"))
async def cmd_model_status(message: Message) -> None:
    """
    Handle /model_status command.
    Returns model retraining status and metrics.
    """
    user_id = message.from_user.id if message.from_user else 0
    language = await _get_user_language(user_id)
    loader = _get_loader()

    try:
        # Ensure logs directory exists
        Path(settings.LOGS_DIR).mkdir(parents=True, exist_ok=True)

        status_text = get_retraining_status_text(language)

        await message.answer(status_text, parse_mode="Markdown")

        logger.info(f"Displayed model status to user {message.from_user.id}")

    except Exception as e:
        logger.error(f"Error displaying model status: {e!s}")
        await message.answer(loader.get(MessageKey.stocks_error_loading, language))


@router.message(Command("retraining_history"))
async def cmd_retraining_history(message: Message) -> None:
    """
    Handle /retraining_history command.
    Returns recent retraining events.
    """
    user_id = message.from_user.id if message.from_user else 0
    language = await _get_user_language(user_id)
    loader = _get_loader()

    try:
        history_text = get_retraining_history_text(language)

        await message.answer(history_text, parse_mode="Markdown")

        logger.info(f"Displayed retraining history to user {message.from_user.id}")

    except Exception as e:
        logger.error(f"Error displaying retraining history: {e!s}")
        await message.answer(loader.get(MessageKey.stocks_error_loading, language))


def get_quick_status() -> dict[str, Any]:
    """
    Get quick status summary for monitoring.

    Returns:
        Dictionary with status summary
    """
    scheduler = get_scheduler_service()
    status = scheduler.get_status()

    return {
        "scheduler_enabled": status["enabled"],
        "retraining_in_progress": status["running"],
        "last_success": status["last_retrain_success"],
        "last_run_time": status["last_retrain_time"],
        "next_run": (
            scheduler.get_next_scheduled_run().isoformat()
            if scheduler.get_next_scheduled_run()
            else None
        ),
        "error": status["last_error"],
    }
