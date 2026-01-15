"""
Model selection based on performance metrics (RMSE, MAE, AUC).
"""

import logging
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from src.models.neural_networks import NeuralNetworkModels
from src.models.statistical import StatisticalModels
from src.utils.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class ModelSelector:
    """
    Class to select the best performing model based on performance metrics.
    """

    def __init__(
        self,
        timeout_seconds: int = 300,  # 5 minutes timeout
        cache_dir: Path | str = Path(".cache/models"),
        use_cache: bool = True,
    ):
        self.timeout_seconds = timeout_seconds
        self.use_cache = use_cache
        self.cache_manager = CacheManager(cache_dir) if use_cache else None
        self.neural_network_models = NeuralNetworkModels(
            cache_manager=self.cache_manager
        )
        self.statistical_models = StatisticalModels(cache_manager=self.cache_manager)
        self.training_results = {}
        self.selected_model = None
        self.selected_model_name = None
        self._training_data = None  # Store training data for neural network predictions
        self._ticker = None  # Store ticker for caching

    @contextmanager
    def timeout_manager(self):
        """
        Context manager to handle model training timeouts.
        """
        start_time = time.time()
        yield
        elapsed_time = time.time() - start_time
        if elapsed_time > self.timeout_seconds:
            raise TimeoutError(
                f"Model training exceeded {self.timeout_seconds} seconds"
            )

    def train_all_models(
        self, data: pd.Series, ticker: str = "unknown"
    ) -> dict[str, dict]:
        """
        Trains all available models and stores their performance metrics.

        Args:
            data: Time series data for training
            ticker: Stock ticker symbol for caching

        Returns:
            Dictionary with training results for each model
        """
        logger.info("Starting training of all models...")

        self._training_data = data  # Store training data for neural network predictions
        self._ticker = ticker

        results = {}

        # Train neural network models
        for model_name in ["LSTM", "GRU", "RNN"]:
            try:
                with self.timeout_manager():
                    start_time = time.time()
                    result = self.neural_network_models.train_model(
                        model_name, data, ticker=ticker
                    )
                    elapsed_time = time.time() - start_time

                    results[model_name] = result
                    logger.info(f"Trained {model_name} in {elapsed_time:.2f}s")

                    # Log training result
                    if "model" in result and result["model"] is not None:
                        logger.info(
                            f"Model {model_name} training completed successfully"
                        )
                    else:
                        logger.warning(
                            f"Model {model_name} training failed: {result.get('error', 'Unknown error')}"
                        )

            except TimeoutError as e:
                logger.error(f"Training {model_name} timed out: {e!s}")
                results[model_name] = {
                    "model": None,
                    "rmse": float("inf"),
                    "mape": float("inf"),
                    "mae": float("inf"),
                    "error": str(e),
                }
            except Exception as e:
                logger.error(f"Error training {model_name}: {e!s}")
                results[model_name] = {
                    "model": None,
                    "rmse": float("inf"),
                    "mape": float("inf"),
                    "mae": float("inf"),
                    "error": str(e),
                }

        # Train statistical models
        try:
            with self.timeout_manager():
                start_time = time.time()
                stat_results = self.statistical_models.train_all_models(
                    data, ticker=ticker
                )
                elapsed_time = time.time() - start_time

                results.update(stat_results)
                logger.info(f"Trained statistical models in {elapsed_time:.2f}s")

        except TimeoutError as e:
            logger.error(f"Training statistical models timed out: {e!s}")
            for model_name in ["ARIMA", "ETS", "Prophet"]:
                results[model_name] = {
                    "model": None,
                    "rmse": float("inf"),
                    "mape": float("inf"),
                    "mae": float("inf"),
                    "error": str(e),
                }
        except Exception as e:
            logger.error(f"Error training statistical models: {e!s}")
            for model_name in ["ARIMA", "ETS", "Prophet"]:
                results[model_name] = {
                    "model": None,
                    "rmse": float("inf"),
                    "mape": float("inf"),
                    "mae": float("inf"),
                    "error": str(e),
                }

        self.training_results = results
        logger.info("Completed training of all models")

        return results

    def calculate_auc(self, actual: np.ndarray, predicted: np.ndarray) -> float:
        """
        Calculates AUC (Area Under the Curve) for regression-like tasks.
        This is a simplified version treating the problem as a binary classification
        task based on whether values are above or below a threshold.

        Args:
            actual: Actual values
            predicted: Predicted values

        Returns:
            AUC value
        """
        try:
            # Normalize the values to 0-1 range
            actual_norm = (actual - actual.min()) / (actual.max() - actual.min() + 1e-8)
            pred_norm = (predicted - predicted.min()) / (
                predicted.max() - predicted.min() + 1e-8
            )

            # Create binary labels based on median threshold
            threshold = np.median(actual_norm)
            actual_binary = (actual_norm > threshold).astype(int)

            # Calculate AUC
            auc = roc_auc_score(actual_binary, pred_norm)
            return auc
        except Exception as e:
            logger.warning(f"Could not calculate AUC: {e!s}, returning 0.5")
            return 0.5  # Return neutral AUC if calculation fails

    def select_best_model(self) -> tuple[str, Any]:
        """
        Selects the best model based on performance metrics (RMSE, MAE, AUC).

        Returns:
            Tuple of (model_name, model_object)
        """
        if not self.training_results:
            raise ValueError("No models have been trained yet")

        # Calculate composite scores for each model
        model_scores = {}

        for model_name, result in self.training_results.items():
            if result.get("model") is None:
                # Skip models that failed to train
                continue

            # Extract metrics, defaulting to infinity if not available
            rmse = result.get("rmse", float("inf"))
            mae = result.get("mae", float("inf"))
            mape = result.get("mape", float("inf"))

            # Skip models with infinite or NaN metrics
            if rmse == float("inf") or rmse != rmse or mape != mape:  # NaN check
                logger.warning(f"Skipping {model_name} due to invalid metrics")
                continue

            # Normalize metrics to 0-1 scale based on the best performer

            # Calculate a composite score (lower is better)
            # RMSE, MAE, and MAPE are all error metrics (lower is better)
            # So we can sum them directly after normalization
            model_scores[model_name] = {
                "rmse": rmse,
                "mae": mae,
                "mape": mape,
                "composite_score": rmse + mae + mape,  # Simple weighted sum
            }

        if not model_scores:
            raise ValueError("No models trained successfully")

        # Find the model with the lowest composite score
        best_model_name = min(
            model_scores.keys(), key=lambda x: model_scores[x]["composite_score"]
        )
        best_result = self.training_results[best_model_name]

        logger.info(
            f"Selected {best_model_name} as the best model with composite score: {model_scores[best_model_name]['composite_score']:.4f}"
        )
        logger.info(
            f"Best model metrics - RMSE: {model_scores[best_model_name]['rmse']:.4f}, "
            f"MAE: {model_scores[best_model_name]['mae']:.4f}, "
            f"MAPE: {model_scores[best_model_name]['mape']:.4f}%"
        )

        self.selected_model = best_result["model"]
        self.selected_model_name = best_model_name

        return best_model_name, best_result["model"]

    def predict(self, forecast_days: int = 30) -> np.ndarray:
        """
        Makes predictions using the selected best model.

        Args:
            forecast_days: Number of days to forecast

        Returns:
            Array of predictions
        """
        if self.selected_model is None:
            raise ValueError(
                "No model has been selected yet. Call select_best_model() first."
            )

        if self.selected_model_name in ["LSTM", "GRU", "RNN"]:
            if self._training_data is None:
                raise ValueError(
                    "Training data is not available for neural network prediction"
                )
            return self.neural_network_models.predict(
                model_name=self.selected_model_name,
                data=self._training_data,
                forecast_days=forecast_days,
            )
        elif self.selected_model_name in ["ARIMA", "ETS"]:
            # Use statistical model for prediction
            if self.selected_model_name == "ARIMA":
                return self.statistical_models.predict_arima(steps=forecast_days)
            elif self.selected_model_name == "ETS":
                last_price = (
                    self._training_data.iloc[-1]
                    if self._training_data is not None
                    else None
                )
                return self.statistical_models.predict_ets(
                    steps=forecast_days, last_price=last_price
                )
        elif self.selected_model_name == "Prophet":
            # Prophet returns a dataframe, we need just the values
            forecast_df = self.statistical_models.predict_prophet(periods=forecast_days)
            return forecast_df.tail(forecast_days)["yhat"].values
        else:
            raise ValueError(f"Unknown model type: {self.selected_model_name}")

    def get_model_metrics(self) -> dict[str, dict[str, float]]:
        """
        Returns performance metrics for all trained models.

        Returns:
            Dictionary with metrics for each model
        """
        metrics = {}
        for model_name, result in self.training_results.items():
            if result.get("model") is not None:
                metrics[model_name] = {
                    "rmse": result.get("rmse", float("inf")),
                    "mae": result.get("mae", float("inf")),
                    "mape": result.get("mape", float("inf")),
                }
        return metrics
