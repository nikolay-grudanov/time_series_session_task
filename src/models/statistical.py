"""
Statistical models for stock price forecasting: ARIMA, ETS, Prophet.
"""

import logging
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

try:
    from prophet import Prophet
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.exponential_smoothing.ets import ETSModel
except ImportError:
    raise ImportError(
        "Please install required packages: pip install statsmodels prophet"
    )

if TYPE_CHECKING:
    from src.utils.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class StatisticalModels:
    """
    Wrapper class to manage statistical models.
    """

    def __init__(self, cache_manager: "CacheManager | None" = None):
        self.models = {"ARIMA": None, "ETS": None, "Prophet": None}
        self.trained_models = {}
        self.scalers = {}  # Store scalers for each model
        self.cache_manager = cache_manager

    def prepare_prophet_data(self, data: pd.Series) -> pd.DataFrame:
        """
        Prepares data in the format required by Prophet.

        Args:
            data: Time series data with a DatetimeIndex

        Returns:
            DataFrame with 'ds' and 'y' columns
        """
        df = pd.DataFrame({"ds": data.index, "y": data.values})
        df["ds"] = pd.to_datetime(df["ds"])
        if df["ds"].dt.tz is not None:
            df["ds"] = df["ds"].dt.tz_localize(None)
        return df

    def _align_for_metrics(
        self, data: pd.Series, forecast: pd.DataFrame
    ) -> tuple[pd.Series, pd.Series]:
        """
        Align actual and predicted values for metric calculation.
        Handles timezone-aware and tz-naive indices.

        Args:
            data: Original time series data
            forecast: Prophet forecast DataFrame

        Returns:
            Tuple of (actual_values, predictions) aligned by date
        """
        forecast_dates = forecast["ds"]

        # Normalize dates for comparison (remove timezone info for matching)
        data_index_normalized = data.index
        forecast_dates_normalized = forecast_dates

        if data_index_normalized.tz is not None:
            data_index_normalized = data_index_normalized.tz_localize(None)
        if forecast_dates_normalized.dt.tz is not None:
            forecast_dates_normalized = forecast_dates_normalized.dt.tz_localize(None)

        # Create a mapping from normalized date to original date
        date_mapping = dict(zip(data_index_normalized, data.index))

        # Filter forecast to only include dates that exist in original data
        valid_mask = forecast_dates_normalized.isin(data_index_normalized)
        forecast_filtered = forecast[valid_mask].copy()

        if len(forecast_filtered) == 0:
            logger.warning("No matching dates found for Prophet metrics calculation")
            return pd.Series(dtype=float), pd.Series(dtype=float)

        # Map forecast dates back to original index
        forecast_filtered["original_date"] = forecast_filtered["ds"].map(date_mapping)
        forecast_filtered = forecast_filtered.dropna(subset=["original_date"])
        forecast_filtered = forecast_filtered.set_index("original_date")
        forecast_filtered = forecast_filtered.sort_index()

        # Align actual and predicted values
        actual_values = data.loc[forecast_filtered.index]
        predictions = forecast_filtered["yhat"]

        return actual_values, predictions

    def train_arima(
        self,
        data: pd.Series,
        order: tuple[int, int, int] = (1, 1, 1),
        ticker: str = "unknown",
    ) -> dict:
        """
        Trains an ARIMA model.

        Args:
            data: Time series data
            order: ARIMA order (p, d, q)
            ticker: Stock ticker symbol for caching

        Returns:
            Dictionary with model and metrics
        """
        if self.cache_manager is not None and self.cache_manager.is_cache_valid(
            ticker, "ARIMA", "statistical"
        ):
            cached_result = self.cache_manager.load_statistical_model(ticker, "ARIMA")
            if cached_result is not None:
                logger.info(f"Loaded ARIMA model from cache for {ticker}")
                self.models["ARIMA"] = cached_result["model"]
                self.trained_models["ARIMA"] = cached_result["model"]
                return cached_result

        logger.info(f"Training ARIMA model with order {order}...")

        try:
            # Fit the ARIMA model
            model = ARIMA(data, order=order)
            fitted_model = model.fit()

            # Store the fitted model
            self.models["ARIMA"] = fitted_model
            self.trained_models["ARIMA"] = fitted_model

            # Make in-sample predictions for metric calculation
            predictions = fitted_model.fittedvalues

            # Calculate metrics
            actual_values = data[data.index.isin(predictions.index)]
            rmse = np.sqrt(np.mean((actual_values - predictions) ** 2))
            mape = np.mean(np.abs((actual_values - predictions) / actual_values)) * 100
            mae = np.mean(np.abs(actual_values - predictions))

            logger.info(
                f"ARIMA model trained. RMSE: {rmse:.4f}, MAPE: {mape:.4f}%, MAE: {mae:.4f}"
            )

            return {
                "model": fitted_model,
                "rmse": rmse,
                "mape": mape,
                "mae": mae,
                "aic": fitted_model.aic,
                "bic": fitted_model.bic,
            }
        except Exception as e:
            logger.error(f"Error training ARIMA model: {e!s}")
            return {
                "model": None,
                "rmse": float("inf"),
                "mape": float("inf"),
                "mae": float("inf"),
                "error": str(e),
            }

    def _save_to_cache(self, ticker: str, model_name: str, result: dict) -> None:
        """Save model result to cache if cache manager is available."""
        if (
            self.cache_manager is not None
            and ticker != "unknown"
            and result.get("model") is not None
        ):
            self.cache_manager.save_statistical_model(ticker, model_name, result)

    def train_ets(
        self,
        data: pd.Series,
        error: str = "add",
        trend: str = "add",
        seasonal: str = "add",
        ticker: str = "unknown",
    ) -> dict:
        """
        Trains an ETS model.

        Args:
            data: Time series data
            error: Error type ('add' or 'mul')
            trend: Trend type ('add', 'mul', or None)
            seasonal: Seasonal type ('add', 'mul', or None)
            ticker: Stock ticker symbol for caching

        Returns:
            Dictionary with model and metrics
        """
        if self.cache_manager is not None and self.cache_manager.is_cache_valid(
            ticker, "ETS", "statistical"
        ):
            cached_result = self.cache_manager.load_statistical_model(ticker, "ETS")
            if cached_result is not None:
                logger.info(f"Loaded ETS model from cache for {ticker}")
                self.models["ETS"] = cached_result["model"]
                self.trained_models["ETS"] = cached_result["model"]
                return cached_result

        logger.info(
            f"Training ETS model with error={error}, trend={trend}, seasonal={seasonal}..."
        )

        try:
            data_copy = data.copy()

            # Ensure the index has a frequency for proper forecasting
            if hasattr(data_copy.index, "freq") and data_copy.index.freq is None:
                try:
                    inferred_freq = pd.infer_freq(data_copy.index)
                    if inferred_freq:
                        data_copy = data_copy.asfreq(inferred_freq)
                    else:
                        data_copy = data_copy.asfreq("B")
                except (ValueError, AttributeError):
                    pass

            model = ETSModel(data_copy, error=error, trend=trend, seasonal=seasonal)
            fitted_model = model.fit()

            # Store the fitted model
            self.models["ETS"] = fitted_model
            self.trained_models["ETS"] = fitted_model

            # Make in-sample predictions for metric calculation
            predictions = fitted_model.fittedvalues

            # Calculate metrics
            actual_values = data[data.index.isin(predictions.index)]
            rmse = np.sqrt(np.mean((actual_values - predictions) ** 2))
            mape = np.mean(np.abs((actual_values - predictions) / actual_values)) * 100
            mae = np.mean(np.abs(actual_values - predictions))

            logger.info(
                f"ETS model trained. RMSE: {rmse:.4f}, MAPE: {mape:.4f}%, MAE: {mae:.4f}"
            )

            return {
                "model": fitted_model,
                "rmse": rmse,
                "mape": mape,
                "mae": mae,
                "aic": fitted_model.aic,
                "bic": fitted_model.bic,
            }
        except Exception as e:
            logger.error(f"Error training ETS model: {e!s}")
            return {
                "model": None,
                "rmse": float("inf"),
                "mape": float("inf"),
                "mae": float("inf"),
                "error": str(e),
            }

    def train_prophet(
        self,
        data: pd.Series,
        changepoint_prior_scale: float = 0.05,
        seasonality_prior_scale: float = 10.0,
        ticker: str = "unknown",
    ) -> dict:
        """
        Trains a Prophet model.

        Args:
            data: Time series data with a DatetimeIndex
            changepoint_prior_scale: Parameter for controlling flexibility of trend
            seasonality_prior_scale: Parameter for controlling strength of seasonality
            ticker: Stock ticker symbol for caching

        Returns:
            Dictionary with model and metrics
        """
        if self.cache_manager is not None and self.cache_manager.is_cache_valid(
            ticker, "Prophet", "statistical"
        ):
            cached_result = self.cache_manager.load_statistical_model(ticker, "Prophet")
            if cached_result is not None:
                logger.info(f"Loaded Prophet model from cache for {ticker}")
                self.models["Prophet"] = cached_result["model"]
                self.trained_models["Prophet"] = cached_result["model"]
                return cached_result

        logger.info("Training Prophet model...")

        try:
            # Prepare data for Prophet
            prophet_data = self.prepare_prophet_data(data)

            # Initialize and fit the Prophet model
            model = Prophet(
                changepoint_prior_scale=changepoint_prior_scale,
                seasonality_prior_scale=seasonality_prior_scale,
            )
            model.fit(prophet_data)

            # Store the fitted model
            self.models["Prophet"] = model
            self.trained_models["Prophet"] = model

            # Make in-sample predictions for metric calculation
            future = model.make_future_dataframe(periods=0)
            forecast = model.predict(future)

            # Align actual and predicted values (handles timezone issues)
            actual_values, predictions = self._align_for_metrics(data, forecast)

            # Remove NaN values for metric calculation
            mask = ~(actual_values.isna() | predictions.isna())
            actual_values = actual_values[mask]
            predictions = predictions[mask]

            # Calculate metrics
            if len(actual_values) > 0:
                rmse = np.sqrt(np.mean((actual_values - predictions) ** 2))
                mape = (
                    np.mean(np.abs((actual_values - predictions) / actual_values)) * 100
                )
                mae = np.mean(np.abs(actual_values - predictions))
            else:
                rmse = mape = mae = float("inf")

            logger.info(
                f"Prophet model trained. RMSE: {rmse:.4f}, MAPE: {mape:.4f}%, MAE: {mae:.4f}"
            )

            return {"model": model, "rmse": rmse, "mape": mape, "mae": mae}
        except Exception as e:
            logger.error(f"Error training Prophet model: {e!s}")
            return {
                "model": None,
                "rmse": float("inf"),
                "mape": float("inf"),
                "mae": float("inf"),
                "error": str(e),
            }

    def train_all_models(
        self, data: pd.Series, ticker: str = "unknown"
    ) -> dict[str, dict]:
        """
        Trains all statistical models.

        Args:
            data: Time series data
            ticker: Stock ticker symbol for caching

        Returns:
            Dictionary with results for each model
        """
        results = {}

        # Train ARIMA
        results["ARIMA"] = self.train_arima(data, ticker=ticker)

        # Train ETS
        results["ETS"] = self.train_ets(data, ticker=ticker)

        # Train Prophet
        results["Prophet"] = self.train_prophet(data, ticker=ticker)

        return results

    def predict_arima(self, steps: int = 30) -> np.ndarray:
        """
        Makes predictions using the trained ARIMA model.

        Args:
            steps: Number of steps to forecast

        Returns:
            Array of predictions
        """
        if "ARIMA" not in self.trained_models:
            raise ValueError("ARIMA model has not been trained yet")

        model = self.trained_models["ARIMA"]
        forecast = model.forecast(steps=steps)
        return forecast.values

    def predict_ets(
        self, steps: int = 30, last_price: float | None = None
    ) -> np.ndarray:
        """
        Makes predictions using the trained ETS model.

        Args:
            steps: Number of steps to forecast
            last_price: Last known price from the original data

        Returns:
            Array of predictions
        """
        if "ETS" not in self.trained_models:
            raise ValueError("ETS model has not been trained yet")

        model = self.trained_models["ETS"]

        try:
            forecast = model.forecast(steps=steps)

            # Handle case where forecast returns NaN (due to missing frequency)
            if (
                isinstance(forecast, (np.ndarray, pd.Series))
                and np.isnan(forecast).all()
            ):
                logger.warning("ETS forecast returned all NaN, using last known price")
                # Fallback: use last known price from data
                if last_price is None:
                    last_value = (
                        float(model.endog[-1]) if hasattr(model, "endog") else 100.0
                    )
                else:
                    last_value = last_price

                forecast = np.array(
                    [last_value * (1 + np.random.randn() * 0.01) for _ in range(steps)]
                )

            if hasattr(forecast, "values"):
                return forecast.values
            return np.array(forecast)
        except Exception as e:
            logger.error(f"ETS prediction error: {e!s}")
            # Return flat forecast as fallback
            last_value = last_price if last_price else 100.0
            return np.full(steps, last_value)

    def predict_prophet(self, periods: int = 30, freq: str = "D") -> pd.DataFrame:
        """
        Makes predictions using the trained Prophet model.

        Args:
            periods: Number of periods to forecast
            freq: Frequency of the forecast ('D' for daily, 'W' for weekly, etc.)

        Returns:
            DataFrame with forecast
        """
        if "Prophet" not in self.trained_models:
            raise ValueError("Prophet model has not been trained yet")

        model = self.trained_models["Prophet"]
        future = model.make_future_dataframe(periods=periods, freq=freq)
        forecast = model.predict(future)
        return forecast
