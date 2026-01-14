"""
Service for logging user requests with configurable rotation.
"""
import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from typing import Any


class LoggerService:
    def __init__(self, log_file_path: str):
        """
        Initializes the logger service with configurable rotation.

        Args:
            log_file_path: Path to the log file
        """
        self.log_file_path = log_file_path
        self.logger = self._setup_timed_rotating_logger()

    def _setup_timed_rotating_logger(self):
        """
        Sets up a timed rotating logger that rotates based on time intervals.
        """
        # Create directory if it doesn't exist
        log_dir = os.path.dirname(self.log_file_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        # Create logger
        logger = logging.getLogger('request_logger')
        logger.setLevel(logging.INFO)

        # Create timed rotating file handler (rotates daily)
        handler = TimedRotatingFileHandler(
            self.log_file_path,
            when="midnight",      # Rotate at midnight
            interval=1,           # Every 1 day
            backupCount=365       # Keep logs for 1 year
        )

        # Create formatter and add it to handler
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(handler)

        return logger

    def log_request(
        self,
        user_id: int,
        ticker: str,
        investment_amount: float,
        selected_model: str,
        metrics: dict[str, float],
        profit_estimate: float,
        additional_params: dict[str, Any] | None = None
    ):
        """
        Logs a user request with all key parameters.

        Args:
            user_id: Unique identifier of the user
            ticker: Stock ticker symbol
            investment_amount: Amount invested
            selected_model: Model selected for prediction
            metrics: Performance metrics of the selected model
            profit_estimate: Estimated profit from trading strategy
            additional_params: Additional parameters to log
        """
        log_data = {
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'ticker': ticker,
            'investment_amount': investment_amount,
            'selected_model': selected_model,
            'metrics': metrics,
            'profit_estimate': profit_estimate
        }

        if additional_params:
            log_data.update(additional_params)

        # Convert log_data to a string for logging
        log_message = " | ".join([f"{key}={value}" for key, value in log_data.items()])

        self.logger.info(log_message)

    def log_error(self, user_id: int, ticker: str, error_message: str):
        """
        Logs an error that occurred during request processing.

        Args:
            user_id: Unique identifier of the user
            ticker: Stock ticker symbol
            error_message: Error message to log
        """
        log_message = f"user_id={user_id} | ticker={ticker} | error={error_message}"
        self.logger.error(log_message)

    def log_model_training(self, ticker: str, model_name: str, training_time: float, success: bool):
        """
        Logs model training information.

        Args:
            ticker: Stock ticker symbol
            model_name: Name of the model being trained
            training_time: Time taken for training in seconds
            success: Whether training was successful
        """
        status = "SUCCESS" if success else "FAILED"
        log_message = (
            f"ticker={ticker} | model={model_name} | "
            f"training_time={training_time:.2f}s | status={status}"
        )
        self.logger.info(log_message)
