"""
General helper functions.
"""
import logging
import os
from datetime import datetime
from typing import Any


def setup_logging(log_file: str = "app.log", level: int = logging.INFO) -> None:
    """
    Sets up basic logging configuration.
    """
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )


def get_current_timestamp() -> str:
    """
    Returns current timestamp in YYYY-MM-DD HH:MM:SS format.
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def dict_to_str(data: dict[str, Any], separator: str = ", ") -> str:
    """
    Converts dictionary to string representation.
    """
    return separator.join([f"{k}={v}" for k, v in data.items()])


def calculate_percentage_change(start_value: float, end_value: float) -> float:
    """
    Calculates percentage change between two values.
    """
    if start_value == 0:
        return 0.0
    return ((end_value - start_value) / start_value) * 100


def round_if_number(value: Any, decimals: int = 2) -> Any:
    """
    Rounds a value to specified decimal places if it's a number.
    """
    if isinstance(value, (int, float)):
        return round(value, decimals)
    return value
