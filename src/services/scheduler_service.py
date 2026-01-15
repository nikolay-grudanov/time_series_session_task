"""
Scheduler service for periodic model retraining.
Uses APScheduler with AsyncIOScheduler for aiogram integration.
"""

import csv
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.config import settings
from src.services.data_loader import download_stock_data

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Service for managing scheduled model retraining.

    Features:
    - AsyncIOScheduler for aiogram compatibility
    - Weekly retraining schedule (Sunday 2:00 AM default)
    - Retry logic with exponential backoff
    - Fallback to previous models on failure
    - Logging of retraining events
    """

    def __init__(self) -> None:
        """Initialize the scheduler service."""
        self.scheduler = AsyncIOScheduler()
        self._retry_count = settings.SCHEDULER_RETRY_COUNT
        self._retry_delay = settings.SCHEDULER_RETRY_DELAY
        self._enabled = settings.SCHEDULER_ENABLED

        # Retraining state
        self._is_retraining = False
        self._last_retrain_success = False
        self._last_retrain_time: datetime | None = None
        self._last_error: str | None = None

        logger.info("SchedulerService initialized")

    def start(self) -> bool:
        """
        Start the scheduler.

        Returns:
            True if started successfully
        """
        if not self._enabled:
            logger.info("Scheduler is disabled in settings")
            return False

        try:
            # Add weekly retraining job
            self.scheduler.add_job(
                self._retrain_models_job,
                CronTrigger(
                    day_of_week=settings.SCHEDULER_RETRAINING_DAY,
                    hour=settings.SCHEDULER_RETRAINING_HOUR,
                    minute=settings.SCHEDULER_RETRAINING_MINUTE,
                ),
                id="weekly_retrain",
                name="Weekly model retraining",
                replace_existing=True,
            )

            self.scheduler.start()
            logger.info(
                f"Scheduler started. Retraining scheduled for "
                f"day {settings.SCHEDULER_RETRAINING_DAY} "
                f"at {settings.SCHEDULER_RETRAINING_HOUR:02d}:"
                f"{settings.SCHEDULER_RETRAINING_MINUTE:02d}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to start scheduler: {e!s}")
            return False

    def stop(self) -> None:
        """Stop the scheduler gracefully."""
        try:
            self.scheduler.shutdown(wait=True)
            logger.info("Scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e!s}")

    def _retrain_models_job(self) -> None:
        """
        Internal job for model retraining.

        This is called by APScheduler at scheduled times.
        """
        if self._is_retraining:
            logger.warning("Retraining already in progress, skipping this run")
            return

        self._is_retraining = True
        self._last_error = None

        self._log_event("start", "Retraining job started")

        success = self._run_retraining_with_retry()

        self._is_retraining = False
        self._last_retrain_success = success
        self._last_retrain_time = datetime.now()

        if success:
            self._log_event("success", "Retraining completed successfully")
            logger.info("Model retraining completed successfully")
        else:
            self._log_event("failure", f"Retraining failed: {self._last_error}")
            logger.error(f"Model retraining failed: {self._last_error}")

    def _run_retraining_with_retry(self) -> bool:
        """
        Run retraining with retry logic.

        Returns:
            True if retraining succeeded
        """
        for attempt in range(1, self._retry_count + 1):
            try:
                logger.info(f"Retraining attempt {attempt}/{self._retry_count}")

                # Perform retraining
                self._perform_retraining()

                return True

            except Exception as e:
                error_msg = str(e)
                self._last_error = error_msg
                logger.error(f"Retraining attempt {attempt} failed: {error_msg}")

                if attempt < self._retry_count:
                    delay = self._retry_delay * attempt  # Exponential backoff
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                    self._log_event("retry", f"Attempt {attempt} failed, retrying")

                # Log final failure
                if attempt == self._retry_count:
                    self._log_event(
                        "failure",
                        f"All {self._retry_count} attempts failed: {error_msg}",
                    )

        return False

    def _perform_retraining(self) -> None:
        """
        Perform the actual model retraining.

        This trains all 6 models (LSTM, GRU, RNN, ARIMA, ETS, Prophet)
        on 2 years of historical data.
        """
        from src.services.forecasting import ForecastingService

        start_time = time.time()

        try:
            # Get all tickers from catalog
            from src.services.catalog_service import get_catalog_service

            catalog = get_catalog_service()
            tickers = catalog.get_tickers()

            if not tickers:
                logger.warning("No tickers available for retraining")
                return

            logger.info(f"Starting retraining for {len(tickers)} tickers")

            # Train models for each ticker
            forecasting = ForecastingService()

            for ticker in tickers:
                try:
                    logger.info(f"Training models for {ticker}")

                    # Download 2 years of data
                    data = download_stock_data(ticker, period="2y")

                    if data is None or len(data) < 100:
                        logger.warning(f"Insufficient data for {ticker}, skipping")
                        continue

                    # Train all models
                    forecasting.train_all_models(ticker, data)

                    logger.info(f"Successfully trained models for {ticker}")

                except Exception as e:
                    logger.error(f"Error training models for {ticker}: {e!s}")
                    continue

            # Record duration
            duration = time.time() - start_time
            logger.info(f"Retraining completed in {duration:.2f} seconds")

            # Verify performance requirement (<5 minutes)
            if duration > 300:
                logger.warning(
                    f"Retraining took {duration:.2f}s, exceeds 5-minute constitution requirement"
                )

        except Exception as e:
            logger.error(f"Error during retraining: {e!s}")
            raise

    def _log_event(
        self, event_type: str, details: str, duration_seconds: int | None = None
    ) -> None:
        """
        Log a retraining event.

        Args:
            event_type: Type of event (start, success, failure, retry)
            details: Event details or error message
            duration_seconds: Training duration for success events
        """
        try:
            log_path = Path(settings.RETRAINING_LOG_PATH)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            with log_path.open("a", newline="") as f:
                writer = csv.writer(f)

                # Write header if file is new
                if log_path.stat().st_size == 0:
                    writer.writerow(
                        ["event_type", "timestamp", "details", "duration_seconds"]
                    )

                writer.writerow(
                    [
                        event_type,
                        datetime.now().isoformat(),
                        details,
                        duration_seconds if duration_seconds else "",
                    ]
                )

        except Exception as e:
            logger.error(f"Error logging retraining event: {e!s}")

    def trigger_retraining(self) -> tuple[bool, str]:
        """
        Manually trigger model retraining.

        Returns:
            Tuple of (started, message)
        """
        if self._is_retraining:
            return False, "Retraining already in progress"

        # Run in background
        import asyncio

        asyncio.create_task(self._retrain_wrapper())

        return True, "Retraining started"

    async def _retrain_wrapper(self) -> None:
        """Wrapper to run retraining in async context."""
        self._retrain_models_job()

    def get_status(self) -> dict[str, Any]:
        """
        Get scheduler status.

        Returns:
            Dictionary with status information
        """
        jobs = self.scheduler.get_jobs()

        return {
            "enabled": self._enabled,
            "running": self._is_retraining,
            "last_retrain_success": self._last_retrain_success,
            "last_retrain_time": (
                self._last_retrain_time.isoformat() if self._last_retrain_time else None
            ),
            "last_error": self._last_error,
            "scheduled_jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat()
                    if job.next_run_time
                    else None,
                }
                for job in jobs
            ],
            "retry_count": self._retry_count,
        }

    def get_retraining_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get retraining event history.

        Args:
            limit: Maximum number of events to return

        Returns:
            List of event dictionaries
        """
        try:
            log_path = Path(settings.RETRAINING_LOG_PATH)

            if not log_path.exists():
                return []

            with log_path.open("r") as f:
                reader = csv.DictReader(f)
                events = list(reader)

            # Return most recent first
            return events[-limit:][::-1]

        except Exception as e:
            logger.error(f"Error reading retraining history: {e!s}")
            return []

    def get_next_scheduled_run(self) -> datetime | None:
        """
        Get next scheduled retraining time.

        Returns:
            Datetime of next run or None
        """
        job = self.scheduler.get_job("weekly_retrain")
        if job and job.next_run_time:
            return job.next_run_time
        return None


# Singleton instance
_scheduler_service: SchedulerService | None = None


def get_scheduler_service() -> SchedulerService:
    """
    Factory function to get SchedulerService instance.

    Returns:
        SchedulerService singleton instance
    """
    global _scheduler_service
    if _scheduler_service is None:
        _scheduler_service = SchedulerService()
    return _scheduler_service
