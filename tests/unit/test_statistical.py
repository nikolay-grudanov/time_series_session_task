"""
Unit tests for statistical models (ARIMA, ETS, Prophet).

Tests cover:
- Prophet timezone handling
- ARIMA and ETS training
- Model alignment for metrics
"""

import numpy as np
import pandas as pd
import pytest

from src.models.statistical import StatisticalModels


class TestProphetTimezoneHandling:
    """Test Prophet model timezone handling."""

    def test_prepare_prophet_data_tz_naive(self):
        """Test Prophet data preparation with timezone-naive data."""
        model = StatisticalModels()

        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        data = pd.Series(np.random.randn(100), index=dates)

        prophet_df = model.prepare_prophet_data(data)

        assert "ds" in prophet_df.columns
        assert "y" in prophet_df.columns
        assert len(prophet_df) == 100
        assert prophet_df["ds"].dt.tz is None

    def test_prepare_prophet_data_tz_aware(self):
        """Test Prophet data preparation with timezone-aware data."""
        model = StatisticalModels()

        dates = pd.date_range("2024-01-01", periods=100, freq="D", tz="UTC")
        data = pd.Series(np.random.randn(100), index=dates)

        prophet_df = model.prepare_prophet_data(data)

        assert "ds" in prophet_df.columns
        assert "y" in prophet_df.columns
        assert len(prophet_df) == 100
        assert prophet_df["ds"].dt.tz is None

    def test_prepare_prophet_data_different_timezones(self):
        """Test Prophet data preparation with different timezones."""
        model = StatisticalModels()

        dates_us = pd.date_range(
            "2024-01-01", periods=100, freq="D", tz="America/New_York"
        )
        data = pd.Series(np.random.randn(100), index=dates_us)

        prophet_df = model.prepare_prophet_data(data)

        assert "ds" in prophet_df.columns
        assert prophet_df["ds"].dt.tz is None


class TestAlignForMetrics:
    """Test metric alignment between data and forecasts."""

    def test_align_for_metrics_tz_naive(self):
        """Test alignment with timezone-naive data."""
        model = StatisticalModels()

        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        data = pd.Series(np.random.randn(100), index=dates)

        forecast = pd.DataFrame(
            {
                "ds": dates,
                "yhat": np.random.randn(100),
                "yhat_lower": np.random.randn(100),
                "yhat_upper": np.random.randn(100),
            }
        )

        actual, predicted = model._align_for_metrics(data, forecast)

        assert isinstance(actual, pd.Series)
        assert isinstance(predicted, pd.Series)
        assert len(actual) == len(predicted)

    def test_align_for_metrics_tz_aware_data(self):
        """Test alignment with timezone-aware data."""
        model = StatisticalModels()

        dates_tz = pd.date_range("2024-01-01", periods=100, freq="D", tz="UTC")
        data = pd.Series(np.random.randn(100), index=dates_tz)

        forecast = pd.DataFrame(
            {
                "ds": pd.date_range("2024-01-01", periods=100, freq="D"),
                "yhat": np.random.randn(100),
                "yhat_lower": np.random.randn(100),
                "yhat_upper": np.random.randn(100),
            }
        )

        actual, predicted = model._align_for_metrics(data, forecast)

        assert isinstance(actual, pd.Series)
        assert isinstance(predicted, pd.Series)

    def test_align_for_metrics_mismatched_indices(self):
        """Test alignment with mismatched date indices."""
        model = StatisticalModels()

        dates1 = pd.date_range("2024-01-01", periods=50, freq="D")
        data = pd.Series(np.random.randn(50), index=dates1)

        forecast = pd.DataFrame(
            {
                "ds": pd.date_range("2024-01-15", periods=50, freq="D"),
                "yhat": np.random.randn(50),
                "yhat_lower": np.random.randn(50),
                "yhat_upper": np.random.randn(50),
            }
        )

        actual, predicted = model._align_for_metrics(data, forecast)

        assert isinstance(actual, pd.Series)
        assert isinstance(predicted, pd.Series)


class TestArimaModel:
    """Test ARIMA model training."""

    def test_train_arima_basic(self):
        """Test basic ARIMA training."""
        model = StatisticalModels()

        dates = pd.date_range("2024-01-01", periods=200, freq="D")
        data = pd.Series(np.cumsum(np.random.randn(200)), index=dates)

        result = model.train_arima(data, order=(1, 1, 1), ticker="TEST")

        assert result["model"] is not None
        assert "rmse" in result
        assert "mape" in result
        assert "mae" in result

    def test_train_arima_with_cache(self):
        """Test ARIMA training with cache hit."""
        model = StatisticalModels()

        dates = pd.date_range("2024-01-01", periods=200, freq="D")
        data = pd.Series(np.cumsum(np.random.randn(200)), index=dates)

        result1 = model.train_arima(data, order=(1, 1, 1), ticker="CACHED_TICKER")

        assert result1["model"] is not None

        result2 = model.train_arima(data, order=(1, 1, 1), ticker="CACHED_TICKER")

        assert result2["model"] is not None


class TestEtsModel:
    """Test ETS model training."""

    def test_train_ets_basic(self):
        """Test basic ETS training."""
        model = StatisticalModels()

        dates = pd.date_range("2024-01-01", periods=200, freq="D")
        data = pd.Series(np.cumsum(np.random.randn(200)), index=dates)

        result = model.train_ets(data, ticker="TEST_ETS")

        assert result["model"] is not None
        assert "rmse" in result
        assert "mape" in result
        assert "mae" in result

    def test_train_ets_no_frequency_index(self):
        """Test ETS training with index without frequency (regression test for asfreq error)."""
        model = StatisticalModels()

        dates = pd.date_range("2024-01-01", periods=200, freq="D")
        data = pd.Series(np.cumsum(np.random.randn(200)), index=dates)
        data.index = pd.DatetimeIndex(data.index)  # Remove freq attribute

        result = model.train_ets(data, ticker="TEST_ETS_NO_FREQ")

        assert result["model"] is not None
        assert "rmse" in result
        assert "mape" in result
        assert "mae" in result


class TestProphetModel:
    """Test Prophet model training."""

    def test_train_prophet_basic(self):
        """Test basic Prophet training."""
        model = StatisticalModels()

        dates = pd.date_range("2024-01-01", periods=200, freq="D")
        data = pd.Series(np.random.randn(200) + 100, index=dates)

        result = model.train_prophet(data, ticker="TEST_PROPHET")

        assert result["model"] is not None
        assert "rmse" in result
        assert "mape" in result
        assert "mae" in result

    def test_train_prophet_tz_aware_data(self, caplog=None):
        """Test Prophet training with timezone-aware data (regression test for tz-join error)."""
        model = StatisticalModels()

        dates = pd.date_range(
            "2024-01-01", periods=200, freq="D", tz="America/New_York"
        )
        data = pd.Series(np.random.randn(200) + 100, index=dates)

        result = model.train_prophet(data, ticker="TEST_PROPHET_TZ")

        assert result["model"] is not None
        assert "error" not in result or result.get("error") is None
        assert "rmse" in result

    def test_train_prophet_with_cache(self):
        """Test Prophet training with cache hit."""
        model = StatisticalModels()

        dates = pd.date_range("2024-01-01", periods=200, freq="D")
        data = pd.Series(np.random.randn(200) + 100, index=dates)

        result1 = model.train_prophet(data, ticker="CACHED_PROPHET")

        assert result1["model"] is not None

        result2 = model.train_prophet(data, ticker="CACHED_PROPHET")

        assert result2["model"] is not None


class TestTrainAllModels:
    """Test training all statistical models."""

    def test_train_all_models(self):
        """Test training all models at once."""
        model = StatisticalModels()

        dates = pd.date_range("2024-01-01", periods=250, freq="D")
        data = pd.Series(np.cumsum(np.random.randn(250)) + 100, index=dates)

        results = model.train_all_models(data, ticker="ALL_MODELS")

        assert "ARIMA" in results
        assert "ETS" in results
        assert "Prophet" in results

        assert results["ARIMA"]["model"] is not None
        assert results["ETS"]["model"] is not None
        assert results["Prophet"]["model"] is not None
