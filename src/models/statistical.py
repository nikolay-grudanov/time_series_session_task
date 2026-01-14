"""
Statistical models for stock price forecasting: ARIMA, ETS, Prophet.
"""
import logging

import numpy as np
import pandas as pd

try:
    from prophet import Prophet
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.exponential_smoothing.ets import ETSModel
except ImportError:
    raise ImportError("Please install required packages: pip install statsmodels prophet")

logger = logging.getLogger(__name__)


class StatisticalModels:
    """
    Wrapper class to manage statistical models.
    """
    def __init__(self):
        self.models = {
            'ARIMA': None,
            'ETS': None,
            'Prophet': None
        }
        self.trained_models = {}
        self.scalers = {}  # Store scalers for each model

    def prepare_prophet_data(self, data: pd.Series) -> pd.DataFrame:
        """
        Prepares data in the format required by Prophet.

        Args:
            data: Time series data with a DatetimeIndex

        Returns:
            DataFrame with 'ds' and 'y' columns
        """
        df = pd.DataFrame({
            'ds': data.index,
            'y': data.values
        })
        # Ensure 'ds' column is datetime
        df['ds'] = pd.to_datetime(df['ds'])
        return df

    def train_arima(self, data: pd.Series, order: tuple[int, int, int] = (1, 1, 1)) -> dict:
        """
        Trains an ARIMA model.

        Args:
            data: Time series data
            order: ARIMA order (p, d, q)

        Returns:
            Dictionary with model and metrics
        """
        logger.info(f"Training ARIMA model with order {order}...")

        try:
            # Fit the ARIMA model
            model = ARIMA(data, order=order)
            fitted_model = model.fit()

            # Store the fitted model
            self.models['ARIMA'] = fitted_model
            self.trained_models['ARIMA'] = fitted_model

            # Make in-sample predictions for metric calculation
            predictions = fitted_model.fittedvalues

            # Calculate metrics
            actual_values = data[data.index.isin(predictions.index)]
            rmse = np.sqrt(np.mean((actual_values - predictions) ** 2))
            mape = np.mean(np.abs((actual_values - predictions) / actual_values)) * 100
            mae = np.mean(np.abs(actual_values - predictions))

            logger.info(f"ARIMA model trained. RMSE: {rmse:.4f}, MAPE: {mape:.4f}%, MAE: {mae:.4f}")

            return {
                'model': fitted_model,
                'rmse': rmse,
                'mape': mape,
                'mae': mae,
                'aic': fitted_model.aic,
                'bic': fitted_model.bic
            }
        except Exception as e:
            logger.error(f"Error training ARIMA model: {e!s}")
            return {
                'model': None,
                'rmse': float('inf'),
                'mape': float('inf'),
                'mae': float('inf'),
                'error': str(e)
            }

    def train_ets(self, data: pd.Series, error: str = 'add', trend: str = 'add', seasonal: str = 'add') -> dict:
        """
        Trains an ETS model.

        Args:
            data: Time series data
            error: Error type ('add' or 'mul')
            trend: Trend type ('add', 'mul', or None)
            seasonal: Seasonal type ('add', 'mul', or None)

        Returns:
            Dictionary with model and metrics
        """
        logger.info(f"Training ETS model with error={error}, trend={trend}, seasonal={seasonal}...")

        try:
            # Fit the ETS model
            model = ETSModel(data, error=error, trend=trend, seasonal=seasonal)
            fitted_model = model.fit()

            # Store the fitted model
            self.models['ETS'] = fitted_model
            self.trained_models['ETS'] = fitted_model

            # Make in-sample predictions for metric calculation
            predictions = fitted_model.fittedvalues

            # Calculate metrics
            actual_values = data[data.index.isin(predictions.index)]
            rmse = np.sqrt(np.mean((actual_values - predictions) ** 2))
            mape = np.mean(np.abs((actual_values - predictions) / actual_values)) * 100
            mae = np.mean(np.abs(actual_values - predictions))

            logger.info(f"ETS model trained. RMSE: {rmse:.4f}, MAPE: {mape:.4f}%, MAE: {mae:.4f}")

            return {
                'model': fitted_model,
                'rmse': rmse,
                'mape': mape,
                'mae': mae,
                'aic': fitted_model.aic,
                'bic': fitted_model.bic
            }
        except Exception as e:
            logger.error(f"Error training ETS model: {e!s}")
            return {
                'model': None,
                'rmse': float('inf'),
                'mape': float('inf'),
                'mae': float('inf'),
                'error': str(e)
            }

    def train_prophet(self, data: pd.Series, changepoint_prior_scale: float = 0.05, seasonality_prior_scale: float = 10.0) -> dict:
        """
        Trains a Prophet model.

        Args:
            data: Time series data with a DatetimeIndex
            changepoint_prior_scale: Parameter for controlling flexibility of trend
            seasonality_prior_scale: Parameter for controlling strength of seasonality

        Returns:
            Dictionary with model and metrics
        """
        logger.info("Training Prophet model...")

        try:
            # Prepare data for Prophet
            prophet_data = self.prepare_prophet_data(data)

            # Initialize and fit the Prophet model
            model = Prophet(
                changepoint_prior_scale=changepoint_prior_scale,
                seasonality_prior_scale=seasonality_prior_scale
            )
            model.fit(prophet_data)

            # Store the fitted model
            self.models['Prophet'] = model
            self.trained_models['Prophet'] = model

            # Make in-sample predictions for metric calculation
            future = model.make_future_dataframe(periods=0)
            forecast = model.predict(future)

            # Align actual and predicted values
            actual_values = data.reindex(forecast['ds'])
            predictions = forecast.set_index('ds')['yhat'].reindex(data.index)

            # Remove NaN values for metric calculation
            mask = ~(actual_values.isna() | predictions.isna())
            actual_values = actual_values[mask]
            predictions = predictions[mask]

            # Calculate metrics
            rmse = np.sqrt(np.mean((actual_values - predictions) ** 2))
            mape = np.mean(np.abs((actual_values - predictions) / actual_values)) * 100
            mae = np.mean(np.abs(actual_values - predictions))

            logger.info(f"Prophet model trained. RMSE: {rmse:.4f}, MAPE: {mape:.4f}%, MAE: {mae:.4f}")

            return {
                'model': model,
                'rmse': rmse,
                'mape': mape,
                'mae': mae
            }
        except Exception as e:
            logger.error(f"Error training Prophet model: {e!s}")
            return {
                'model': None,
                'rmse': float('inf'),
                'mape': float('inf'),
                'mae': float('inf'),
                'error': str(e)
            }

    def train_all_models(self, data: pd.Series) -> dict[str, dict]:
        """
        Trains all statistical models.

        Args:
            data: Time series data

        Returns:
            Dictionary with results for each model
        """
        results = {}

        # Train ARIMA
        results['ARIMA'] = self.train_arima(data)

        # Train ETS
        results['ETS'] = self.train_ets(data)

        # Train Prophet
        results['Prophet'] = self.train_prophet(data)

        return results

    def predict_arima(self, steps: int = 30) -> np.ndarray:
        """
        Makes predictions using the trained ARIMA model.

        Args:
            steps: Number of steps to forecast

        Returns:
            Array of predictions
        """
        if 'ARIMA' not in self.trained_models:
            raise ValueError("ARIMA model has not been trained yet")

        model = self.trained_models['ARIMA']
        forecast = model.forecast(steps=steps)
        return forecast.values

    def predict_ets(self, steps: int = 30) -> np.ndarray:
        """
        Makes predictions using the trained ETS model.

        Args:
            steps: Number of steps to forecast

        Returns:
            Array of predictions
        """
        if 'ETS' not in self.trained_models:
            raise ValueError("ETS model has not been trained yet")

        model = self.trained_models['ETS']
        forecast = model.forecast(steps=steps)
        return forecast.values

    def predict_prophet(self, periods: int = 30, freq: str = 'D') -> pd.DataFrame:
        """
        Makes predictions using the trained Prophet model.

        Args:
            periods: Number of periods to forecast
            freq: Frequency of the forecast ('D' for daily, 'W' for weekly, etc.)

        Returns:
            DataFrame with forecast
        """
        if 'Prophet' not in self.trained_models:
            raise ValueError("Prophet model has not been trained yet")

        model = self.trained_models['Prophet']
        future = model.make_future_dataframe(periods=periods, freq=freq)
        forecast = model.predict(future)
        return forecast
