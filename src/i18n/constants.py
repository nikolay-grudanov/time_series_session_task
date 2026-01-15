"""
Message key constants for i18n module.

All user-facing message keys are defined here as enum values for type safety
and autocomplete support.
"""

from enum import Enum


class MessageKey(str, Enum):
    """
    Enumeration of all message keys used throughout the bot.

    Each key corresponds to a user-facing message that needs translation.
    Keys follow snake_case naming convention per project standards.
    """

    # Language Selection
    welcome = "welcome"
    select_lang_prompt = "select_lang_prompt"
    lang_selected_ru = "lang_selected_ru"
    lang_selected_en = "lang_selected_en"
    cmd_lang_description = "cmd_lang_description"

    # Settings
    settings_title = "settings_title"
    current_lang = "current_lang"

    # Errors
    error_generic = "error_generic"
    error_invalid_input = "error_invalid_input"
    error_user_not_found = "error_user_not_found"
    error_invalid_ticker = "error_invalid_ticker"
    error_invalid_amount = "error_invalid_amount"

    # Notifications
    notification_subscribed = "notification_subscribed"
    notification_unsubscribed = "notification_unsubscribed"

    # Forecast
    forecast_requested = "forecast_requested"
    forecast_generating = "forecast_generating"
    forecast_ready = "forecast_ready"
    forecast_error = "forecast_error"

    # Help & Info
    help_title = "help_title"
    help_commands = "help_commands"
    about = "about"

    # Stocks
    stocks_title = "stocks_title"
    stocks_empty = "stocks_empty"
    stocks_page_info = "stocks_page_info"

    # Start command
    start_title = "start_title"
    start_description = "start_description"
    start_available_commands = "start_available_commands"
    start_example = "start_example"

    # Help command
    help_stocks = "help_stocks"
    help_forecast = "help_forecast"
    help_model_status = "help_model_status"
    help_lang = "help_lang"
    help_input_format = "help_input_format"
    help_examples = "help_examples"

    # Model status
    model_status_title = "model_status_title"
    model_status_updating = "model_status_updating"
    model_status_ready = "model_status_ready"
    model_status_last_update = "model_status_last_update"

    # Validation
    validation_ticker_info = "validation_ticker_info"
    validation_amount_info = "validation_amount_info"
    validation_help_examples = "validation_help_examples"

    # Stocks pagination and display
    stocks_showing = "stocks_showing"
    stocks_tap_to_use = "stocks_tap_to_use"
    stocks_forecast_example = "stocks_forecast_example"
    stocks_error_loading = "stocks_error_loading"
    pagination_invalid_page = "pagination_invalid_page"
    stocks_not_found = "stocks_not_found"
    stock_selected = "stock_selected"
    stock_company = "stock_company"
    stock_sector = "stock_sector"
    stock_forecast_instruction = "stock_forecast_instruction"
    stock_selection_error = "stock_selection_error"

    # Search
    search_title = "search_title"
    search_prompt = "search_prompt"
    search_example = "search_example"
    search_results = "search_results"
    search_direct_use = "search_direct_use"

    # Model status detailed
    status_scheduler_enabled = "status_scheduler_enabled"
    status_scheduler_disabled = "status_scheduler_disabled"
    status_retraining_in_progress = "status_retraining_in_progress"
    status_retraining_idle = "status_retraining_idle"
    status_last_retraining = "status_last_retraining"
    status_last_retraining_time = "status_last_retraining_time"
    status_last_retraining_status = "status_last_retraining_status"
    status_last_retraining_never = "status_last_retraining_never"
    status_next_scheduled = "status_next_scheduled"
    status_next_scheduled_time = "status_next_scheduled_time"
    status_next_scheduled_never = "status_next_scheduled_never"
    status_config_retry = "status_config_retry"
    status_config_interval = "status_config_interval"
    status_config_fallback = "status_config_fallback"
    status_error = "status_error"
    status_models_info = "status_models_info"
    status_training_data = "status_training_data"
    status_training_timeout = "status_training_timeout"
    status_retraining_success = "status_retraining_success"
    status_retraining_failed = "status_retraining_failed"
    status_retraining_retry = "status_retraining_retry"
    retraining_history_title = "retraining_history_title"
    no_history = "no_history"

    # Forecast main flow
    forecast_usage_error = "forecast_usage_error"
    forecast_format = "forecast_format"
    forecast_example = "forecast_example"
    forecast_downloading = "forecast_downloading"
    forecast_no_data = "forecast_no_data"
    forecast_generating_v2 = "forecast_generating_v2"
    forecast_analyzing = "forecast_analyzing"
    forecast_calculating = "forecast_calculating"
    forecast_result_caption = "forecast_result_caption"
    forecast_expected_change = "forecast_expected_change"
    forecast_last_price = "forecast_last_price"
    forecast_end_price = "forecast_end_price"
    forecast_best_model = "forecast_best_model"
    forecast_recommendations_title = "forecast_recommendations_title"
    profit_analysis_title = "profit_analysis_title"
    profit_potential = "profit_potential"
    roi_label = "roi_label"
    active_vs_hold = "active_vs_hold"
    effectiveness = "effectiveness"

    # Trading recommendations formatting
    trading_recommendations_header = "trading_recommendations_header"
    profit_info = "profit_info"
    roi_info = "roi_info"
    trading_actions_header = "trading_actions_header"
    buy_opportunities = "buy_opportunities"
    sell_opportunities = "sell_opportunities"
    buy_date = "buy_date"
    sell_date = "sell_date"
    no_opportunities = "no_opportunities"
    market_neutral = "market_neutral"

    @classmethod
    def all_keys(cls) -> list[str]:
        """Return list of all message keys."""
        return [member.value for member in cls]

    @classmethod
    def has_key(cls, key: str) -> bool:
        """Check if a key exists in the enumeration."""
        return key in cls.all_keys()
