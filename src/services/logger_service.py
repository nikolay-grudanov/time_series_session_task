"""
Service for logging user requests with configurable rotation and CSV format support.
Implements FR-016: User session logging in CSV format.
"""

import csv
import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Any


class LoggerService:
    """
    Service for logging user requests.

    Features:
    - Timed rotating file handler for general logs
    - CSV format user session logging per FR-016
    - Configurable retention period
    """

    # CSV header for user sessions (FR-016)
    USER_SESSION_CSV_HEADER = [
        "user_id",
        "timestamp",
        "ticker",
        "investment_amount",
        "best_model_name",
        "metric_value",
        "estimated_profit",
    ]

    def __init__(
        self,
        log_file_path: str,
        csv_log_path: str | None = None,
        txt_log_path: str | None = None,
        retention_days: int = 365,
    ):
        """
        Initializes the logger service with configurable rotation.

        Args:
            log_file_path: Path to the general log file
            csv_log_path: Path to the CSV user session log (FR-016)
            txt_log_path: Path to the text user session log
            retention_days: Number of days to retain logs
        """
        self.log_file_path = log_file_path
        self.csv_log_path = csv_log_path
        self.txt_log_path = txt_log_path
        self.retention_days = retention_days
        self.logger = self._setup_timed_rotating_logger()

        # Initialize CSV log file
        if self.csv_log_path:
            self._init_csv_log()

        # Initialize TXT log file
        if self.txt_log_path:
            self._init_txt_log()

    def _setup_timed_rotating_logger(self):
        """
        Sets up a timed rotating logger that rotates based on time intervals.
        """
        # Create directory if it doesn't exist
        log_dir = os.path.dirname(self.log_file_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        # Create logger
        logger = logging.getLogger("request_logger")
        logger.setLevel(logging.INFO)

        # Create timed rotating file handler (rotates daily)
        handler = TimedRotatingFileHandler(
            self.log_file_path,
            when="midnight",  # Rotate at midnight
            interval=1,  # Every 1 day
            backupCount=self.retention_days,  # Keep logs for configured period
        )

        # Create formatter and add it to handler
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(handler)

        return logger

    def _init_csv_log(self) -> None:
        """Initialize CSV log file with header if it doesn't exist."""
        if not self.csv_log_path:
            return

        try:
            csv_path = Path(self.csv_log_path)
            csv_path.parent.mkdir(parents=True, exist_ok=True)

            # Create file with header if it doesn't exist
            if not csv_path.exists():
                with csv_path.open("w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(self.USER_SESSION_CSV_HEADER)

            logger = logging.getLogger(__name__)
            logger.info(f"CSV user session log initialized: {self.csv_log_path}")

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to initialize CSV log: {e!s}")

    def _init_txt_log(self) -> None:
        """Initialize TXT log file with header if it doesn't exist."""
        if not self.txt_log_path:
            return

        try:
            txt_path = Path(self.txt_log_path)
            txt_path.parent.mkdir(parents=True, exist_ok=True)

            if not txt_path.exists():
                txt_path.write_text(
                    "# User Session Log\n"
                    "# Format: user_id | datetime | ticker | amount | model | metric | profit\n"
                    "# Example: 12345 | 2026-01-15 10:30:00 | AAPL | 1000.0 | LSTM | 2.5 | 150.0\n\n"
                )

            logger = logging.getLogger(__name__)
            logger.info(f"TXT user session log initialized: {self.txt_log_path}")

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to initialize TXT log: {e!s}")

    def log_request(
        self,
        user_id: int,
        ticker: str,
        investment_amount: float,
        selected_model: str,
        metrics: dict[str, float],
        profit_estimate: float,
        additional_params: dict[str, Any] | None = None,
    ):
        """
        Logs a user request with all key parameters.

        Args:
            user_id: Unique identifier of the user
            ticker: Stock ticker symbol
            investment_amount: Amount invested
            selected_model: Model selected for prediction
            metrics: Performance metrics of the selected model (RMSE, MAPE, etc.)
            profit_estimate: Estimated profit from trading strategy
            additional_params: Additional parameters to log
        """
        # Determine primary metric (prefer MAPE if available, otherwise RMSE)
        metric_value = metrics.get("mape", metrics.get("rmse", 0.0))

        # Log to rotating text file
        log_data = {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "ticker": ticker,
            "investment_amount": investment_amount,
            "selected_model": selected_model,
            "metrics": metrics,
            "profit_estimate": profit_estimate,
        }

        if additional_params:
            log_data.update(additional_params)

        log_message = " | ".join([f"{key}={value}" for key, value in log_data.items()])
        self.logger.info(log_message)

        # Log to CSV file (FR-016 requirement)
        self._log_to_csv(
            user_id=user_id,
            timestamp=datetime.now().isoformat(),
            ticker=ticker,
            investment_amount=investment_amount,
            best_model_name=selected_model,
            metric_value=metric_value,
            estimated_profit=profit_estimate,
        )

        # Log to TXT file (human-readable format)
        self._log_to_txt(
            user_id=user_id,
            timestamp=datetime.now().isoformat(),
            ticker=ticker,
            investment_amount=investment_amount,
            best_model_name=selected_model,
            metric_value=metric_value,
            estimated_profit=profit_estimate,
        )

    def _log_to_csv(
        self,
        user_id: int,
        timestamp: str,
        ticker: str,
        investment_amount: float,
        best_model_name: str,
        metric_value: float,
        estimated_profit: float,
    ) -> None:
        """
        Log user session to CSV file (FR-016).

        Args:
            user_id: Telegram user ID
            timestamp: ISO 8601 timestamp
            ticker: Stock ticker
            investment_amount: Investment amount in USD
            best_model_name: Name of best performing model
            metric_value: Primary metric value (RMSE or MAPE)
            estimated_profit: Estimated profit/loss
        """
        if not self.csv_log_path:
            return

        try:
            csv_path = Path(self.csv_log_path)

            with csv_path.open("a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        user_id,
                        timestamp,
                        ticker,
                        investment_amount,
                        best_model_name,
                        metric_value,
                        estimated_profit,
                    ]
                )

        except Exception as e:
            self.logger.error(f"Failed to write to CSV log: {e!s}")

    def _log_to_txt(
        self,
        user_id: int,
        timestamp: str,
        ticker: str,
        investment_amount: float,
        best_model_name: str,
        metric_value: float,
        estimated_profit: float,
    ) -> None:
        """
        Log user session to TXT file (human-readable format).

        Format: user_id | datetime | ticker | amount | model | metric | profit
        Example: 12345 | 2026-01-15 10:30:00 | AAPL | 1000.0 | LSTM | 2.5 | 150.0

        Args:
            user_id: Telegram user ID
            timestamp: Human-readable datetime string
            ticker: Stock ticker
            investment_amount: Investment amount in USD
            best_model_name: Name of best performing model
            metric_value: Primary metric value (MAPE or RMSE)
            estimated_profit: Estimated profit/loss
        """
        if not self.txt_log_path:
            return

        try:
            txt_path = Path(self.txt_log_path)

            log_line = (
                f"{user_id} | {timestamp} | {ticker} | {investment_amount} | "
                f"{best_model_name} | {metric_value:.4f} | {estimated_profit:.2f}\n"
            )

            with txt_path.open("a", encoding="utf-8") as f:
                f.write(log_line)

        except Exception as e:
            self.logger.error(f"Failed to write to TXT log: {e!s}")

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

    def log_model_training(
        self,
        ticker: str,
        model_name: str,
        training_time: float,
        success: bool,
        metrics: dict[str, float] | None = None,
    ):
        """
        Logs model training information.

        Args:
            ticker: Stock ticker symbol
            model_name: Name of the model being trained
            training_time: Time taken for training in seconds
            success: Whether training was successful
            metrics: Optional performance metrics
        """
        status = "SUCCESS" if success else "FAILED"
        log_message = (
            f"ticker={ticker} | model={model_name} | "
            f"training_time={training_time:.2f}s | status={status}"
        )

        if metrics:
            log_message += f" | metrics={metrics}"

        self.logger.info(log_message)

    def get_session_logs(
        self, user_id: int | None = None, ticker: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        Retrieve user session logs.

        Args:
            user_id: Optional filter by user ID
            ticker: Optional filter by ticker
            limit: Maximum number of records to return

        Returns:
            List of log entry dictionaries
        """
        if not self.csv_log_path or not Path(self.csv_log_path).exists():
            return []

        try:
            logs = []

            with open(self.csv_log_path, newline="") as f:
                reader = csv.DictReader(f)

                for row in reader:
                    # Apply filters
                    if user_id and row.get("user_id") != str(user_id):
                        continue
                    if ticker and row.get("ticker") != ticker.upper():
                        continue

                    logs.append(row)

                    if len(logs) >= limit:
                        break

            return logs

        except Exception as e:
            self.logger.error(f"Error reading session logs: {e!s}")
            return []

    def get_session_stats(self) -> dict[str, Any]:
        """
        Get statistics about user session logs.

        Returns:
            Dictionary with session statistics
        """
        if not self.csv_log_path or not Path(self.csv_log_path).exists():
            return {"total_sessions": 0}

        try:
            with open(self.csv_log_path, newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            return {
                "total_sessions": len(rows),
                "unique_users": len(set(r.get("user_id", "") for r in rows)),
                "unique_tickers": len(set(r.get("ticker", "") for r in rows)),
                "avg_investment": sum(
                    float(r.get("investment_amount", 0)) for r in rows
                )
                / len(rows)
                if rows
                else 0,
            }

        except Exception as e:
            self.logger.error(f"Error calculating session stats: {e!s}")
            return {"error": str(e)}
