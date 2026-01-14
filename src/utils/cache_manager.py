"""
Cache manager for trained models using pickle serialization.
"""

import logging
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import torch

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Manages caching of trained models to disk using pickle serialization.
    Supports both neural network models (PyTorch) and statistical models.
    """

    def __init__(self, cache_dir: Path | str = Path(".cache/models")):
        """
        Initialize the cache manager.

        Args:
            cache_dir: Directory to store cached models
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Cache manager initialized with directory: {self.cache_dir}")

    def get_cache_path(
        self, ticker: str, model_name: str, model_type: str = "neural"
    ) -> Path:
        """
        Get the cache file path for a specific model.

        Args:
            ticker: Stock ticker symbol
            model_name: Name of the model (e.g., 'LSTM', 'ARIMA')
            model_type: Type of model ('neural' or 'statistical')

        Returns:
            Path to the cache file
        """
        if model_type == "neural":
            extension = ".pt"
        else:
            extension = ".pkl"

        filename = f"{ticker}_{model_name}{extension}"
        return self.cache_dir / filename

    def is_cache_valid(
        self,
        ticker: str,
        model_name: str,
        model_type: str = "neural",
        max_age_hours: int = 24,
    ) -> bool:
        """
        Check if a cached model exists and is not expired.

        Args:
            ticker: Stock ticker symbol
            model_name: Name of the model
            model_type: Type of model ('neural' or 'statistical')
            max_age_hours: Maximum age of cache in hours

        Returns:
            True if cache exists and is valid, False otherwise
        """
        cache_path = self.get_cache_path(ticker, model_name, model_type)

        if not cache_path.exists():
            logger.debug(f"Cache file not found: {cache_path}")
            return False

        # Check file age
        file_mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        age = datetime.now() - file_mtime

        if age > timedelta(hours=max_age_hours):
            logger.info(
                f"Cache expired for {ticker}_{model_name} (age: {age.total_seconds() / 3600:.2f}h)"
            )
            return False

        logger.debug(f"Cache valid for {ticker}_{model_name}")
        return True

    def save_neural_network(
        self, ticker: str, model_name: str, model_info: dict[str, Any]
    ) -> None:
        """
        Save a trained neural network model to cache.

        Args:
            ticker: Stock ticker symbol
            model_name: Name of the model
            model_info: Dictionary containing model and metadata
                - model: PyTorch model
                - rmse: Root mean squared error
                - mape: Mean absolute percentage error
                - mae: Mean absolute error
                - mse: Mean squared error
        """
        cache_path = self.get_cache_path(ticker, model_name, "neural")

        try:
            # Save model state dict and metadata
            cache_data = {
                "model_state_dict": model_info["model"].state_dict(),
                "model_class": model_info["model"].__class__.__name__,
                "metrics": {
                    "rmse": model_info["rmse"],
                    "mape": model_info["mape"],
                    "mae": model_info["mae"],
                    "mse": model_info.get("mse", None),
                },
                "cached_at": datetime.now().isoformat(),
            }

            torch.save(cache_data, cache_path)
            logger.info(f"Saved neural network model to cache: {cache_path}")

        except Exception as e:
            logger.error(f"Error saving neural network model to cache: {e!s}")

    def load_neural_network(
        self, ticker: str, model_name: str, model_class: type
    ) -> dict[str, Any] | None:
        """
        Load a cached neural network model.

        Args:
            ticker: Stock ticker symbol
            model_name: Name of the model
            model_class: The model class to instantiate (e.g., LSTMModel)

        Returns:
            Dictionary with model and metrics, or None if loading fails
        """
        cache_path = self.get_cache_path(ticker, model_name, "neural")

        if not cache_path.exists():
            logger.debug(f"Cache file not found: {cache_path}")
            return None

        try:
            cache_data = torch.load(cache_path, weights_only=False)

            # Reconstruct the model
            model = model_class()
            model.load_state_dict(cache_data["model_state_dict"])
            model.eval()

            logger.info(f"Loaded neural network model from cache: {cache_path}")

            return {
                "model": model,
                "rmse": cache_data["metrics"]["rmse"],
                "mape": cache_data["metrics"]["mape"],
                "mae": cache_data["metrics"]["mae"],
                "mse": cache_data["metrics"].get("mse", None),
                "cached_at": cache_data["cached_at"],
            }

        except Exception as e:
            logger.error(f"Error loading neural network model from cache: {e!s}")
            return None

    def save_statistical_model(
        self, ticker: str, model_name: str, model_info: dict[str, Any]
    ) -> None:
        """
        Save a trained statistical model to cache.

        Args:
            ticker: Stock ticker symbol
            model_name: Name of the model
            model_info: Dictionary containing model and metadata
                - model: Fitted statistical model
                - rmse: Root mean squared error
                - mape: Mean absolute percentage error
                - mae: Mean absolute error
                - aic: Akaike information criterion (optional)
                - bic: Bayesian information criterion (optional)
        """
        cache_path = self.get_cache_path(ticker, model_name, "statistical")

        try:
            # Save model and metadata
            cache_data = {
                "model": model_info["model"],
                "metrics": {
                    "rmse": model_info["rmse"],
                    "mape": model_info["mape"],
                    "mae": model_info["mae"],
                    "aic": model_info.get("aic", None),
                    "bic": model_info.get("bic", None),
                },
                "cached_at": datetime.now().isoformat(),
            }

            with cache_path.open("wb") as f:
                pickle.dump(cache_data, f)

            logger.info(f"Saved statistical model to cache: {cache_path}")

        except Exception as e:
            logger.error(f"Error saving statistical model to cache: {e!s}")

    def load_statistical_model(
        self, ticker: str, model_name: str
    ) -> dict[str, Any] | None:
        """
        Load a cached statistical model.

        Args:
            ticker: Stock ticker symbol
            model_name: Name of the model

        Returns:
            Dictionary with model and metrics, or None if loading fails
        """
        cache_path = self.get_cache_path(ticker, model_name, "statistical")

        if not cache_path.exists():
            logger.debug(f"Cache file not found: {cache_path}")
            return None

        try:
            with cache_path.open("rb") as f:
                cache_data = pickle.load(f)

            logger.info(f"Loaded statistical model from cache: {cache_path}")

            return {
                "model": cache_data["model"],
                "rmse": cache_data["metrics"]["rmse"],
                "mape": cache_data["metrics"]["mape"],
                "mae": cache_data["metrics"]["mae"],
                "aic": cache_data["metrics"].get("aic", None),
                "bic": cache_data["metrics"].get("bic", None),
                "cached_at": cache_data["cached_at"],
            }

        except Exception as e:
            logger.error(f"Error loading statistical model from cache: {e!s}")
            return None

    def clear_expired_cache(self, max_age_hours: int = 24) -> int:
        """
        Clear expired cache files.

        Args:
            max_age_hours: Maximum age of cache in hours

        Returns:
            Number of files deleted
        """
        deleted_count = 0
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        for cache_file in self.cache_dir.glob("*"):
            if cache_file.is_file():
                file_mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)

                if file_mtime < cutoff_time:
                    try:
                        cache_file.unlink()
                        deleted_count += 1
                        logger.info(f"Deleted expired cache file: {cache_file}")
                    except Exception as e:
                        logger.error(f"Error deleting cache file {cache_file}: {e!s}")

        logger.info(f"Cleared {deleted_count} expired cache files")
        return deleted_count

    def clear_all_cache(self) -> int:
        """
        Clear all cache files.

        Returns:
            Number of files deleted
        """
        deleted_count = 0

        for cache_file in self.cache_dir.glob("*"):
            if cache_file.is_file():
                try:
                    cache_file.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted cache file: {cache_file}")
                except Exception as e:
                    logger.error(f"Error deleting cache file {cache_file}: {e!s}")

        logger.info(f"Cleared all {deleted_count} cache files")
        return deleted_count

    def get_cache_stats(self) -> dict[str, Any]:
        """
        Get statistics about the cache.

        Returns:
            Dictionary with cache statistics
        """
        cache_files = list(self.cache_dir.glob("*"))
        total_size = sum(f.stat().st_size for f in cache_files if f.is_file())

        return {
            "cache_dir": str(self.cache_dir),
            "file_count": len(cache_files),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
        }
