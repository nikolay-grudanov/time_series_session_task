"""
Neural network models for stock price forecasting: LSTM, GRU, RNN.
"""

import logging
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

if TYPE_CHECKING:
    from src.utils.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class LSTMModel(nn.Module):
    """
    LSTM model for stock price forecasting.
    """

    def __init__(
        self,
        input_size: int = 1,
        hidden_size: int = 50,
        num_layers: int = 2,
        output_size: int = 1,
    ):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)

        out, _ = self.lstm(x, (h0, c0))
        out = self.fc(out[:, -1, :])
        return out


class GRUModel(nn.Module):
    """
    GRU model for stock price forecasting.
    """

    def __init__(
        self,
        input_size: int = 1,
        hidden_size: int = 50,
        num_layers: int = 2,
        output_size: int = 1,
    ):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        self.gru = nn.GRU(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)

        out, _ = self.gru(x, h0)
        out = self.fc(out[:, -1, :])
        return out


class RNNModel(nn.Module):
    """
    RNN model for stock price forecasting.
    """

    def __init__(
        self,
        input_size: int = 1,
        hidden_size: int = 50,
        num_layers: int = 2,
        output_size: int = 1,
    ):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        self.rnn = nn.RNN(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)

        out, _ = self.rnn(x, h0)
        out = self.fc(out[:, -1, :])
        return out


class NeuralNetworkModels:
    """
    Wrapper class to manage neural network models.
    """

    def __init__(self, cache_manager: "CacheManager | None" = None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.models: dict[str, nn.Module | None] = {
            "LSTM": None,
            "GRU": None,
            "RNN": None,
        }
        self.trained_models = set()
        self.cache_manager = cache_manager

    def prepare_data(
        self, data: pd.Series, sequence_length: int = 60
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Prepares data for neural network training.

        Args:
            data: Time series data
            sequence_length: Length of sequences to create

        Returns:
            Tuple of (features, targets) as tensors
        """
        # Normalize the data
        scaler = data.max() - data.min()
        if scaler != 0:
            scaled_data = (data - data.min()) / scaler
        else:
            scaled_data = data - data.min()  # Handle case where all values are the same

        # Create sequences
        X, y = [], []
        for i in range(sequence_length, len(scaled_data)):
            X.append(scaled_data.iloc[i - sequence_length : i].values)
            y.append(scaled_data.iloc[i])

        X, y = np.array(X), np.array(y)

        # Convert to tensors
        X_tensor = torch.FloatTensor(X).unsqueeze(-1)  # Add feature dimension
        y_tensor = torch.FloatTensor(y)

        return X_tensor, y_tensor

    def train_model(
        self,
        model_name: str,
        data: pd.Series,
        epochs: int = 50,
        sequence_length: int = 60,
        ticker: str = "unknown",
    ) -> dict:
        """
        Trains a neural network model.

        Args:
            model_name: Name of the model ('LSTM', 'GRU', or 'RNN')
            data: Time series data
            epochs: Number of training epochs
            sequence_length: Length of sequences to create
            ticker: Stock ticker symbol for caching

        Returns:
            Dictionary with training metrics
        """
        if model_name not in self.models:
            raise ValueError(f"Unknown model: {model_name}")

        cache_key = f"{ticker}_{model_name}"
        cache_hit = False

        if self.cache_manager is not None and self.cache_manager.is_cache_valid(
            ticker, model_name, "neural"
        ):
            model_class = {"LSTM": LSTMModel, "GRU": GRUModel, "RNN": RNNModel}[
                model_name
            ]
            cached_result = self.cache_manager.load_neural_network(
                ticker, model_name, model_class
            )
            if cached_result is not None:
                logger.info(f"Loaded {model_name} model from cache for {ticker}")
                self.models[model_name] = cached_result["model"]
                self.trained_models.add(model_name)
                return cached_result

        logger.info(f"Training {model_name} model...")

        # Prepare data
        X, y = self.prepare_data(data, sequence_length)

        # Split data into train and test sets
        split_idx = int(0.8 * len(X))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        # Initialize model
        if model_name == "LSTM":
            model = LSTMModel().to(self.device)
        elif model_name == "GRU":
            model = GRUModel().to(self.device)
        elif model_name == "RNN":
            model = RNNModel().to(self.device)

        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

        # Move data to device
        X_train, y_train = X_train.to(self.device), y_train.to(self.device)
        X_test, y_test = X_test.to(self.device), y_test.to(self.device)

        # Training loop
        model.train()
        for epoch in range(epochs):
            optimizer.zero_grad()
            outputs = model(X_train)
            loss = criterion(outputs.squeeze(), y_train)
            loss.backward()
            optimizer.step()

            if (epoch + 1) % 10 == 0:
                logger.debug(f"Epoch [{epoch + 1}/{epochs}], Loss: {loss.item():.4f}")

        # Evaluate model
        model.eval()
        with torch.no_grad():
            test_outputs = model(X_test)
            test_loss = criterion(test_outputs.squeeze(), y_test)

            # Calculate metrics
            mse = test_loss.item()
            rmse = np.sqrt(mse)

            # Calculate MAPE
            mape = (
                torch.mean(torch.abs((y_test - test_outputs.squeeze()) / y_test)) * 100
            )

            # Calculate MAE
            mae = torch.mean(torch.abs(y_test - test_outputs.squeeze()))

        # Store the trained model
        self.models[model_name] = model
        self.trained_models.add(model_name)

        logger.info(
            f"Completed training {model_name} model. RMSE: {rmse:.4f}, MAPE: {mape:.4f}%, MAE: {mae:.4f}"
        )

        result = {
            "model": model,
            "rmse": rmse,
            "mape": mape.item(),
            "mae": mae.item(),
            "mse": mse,
        }

        if self.cache_manager is not None and ticker != "unknown":
            self.cache_manager.save_neural_network(ticker, model_name, result)

        return result

    def predict(
        self,
        model_name: str,
        data: pd.Series,
        sequence_length: int = 60,
        forecast_days: int = 30,
    ) -> np.ndarray:
        """
        Makes predictions using a trained model.

        Args:
            model_name: Name of the model to use
            data: Historical data to base predictions on
            sequence_length: Length of sequences to create
            forecast_days: Number of days to forecast

        Returns:
            Array of predictions
        """
        if model_name not in self.trained_models:
            raise ValueError(f"Model {model_name} has not been trained yet")

        model = self.models[model_name]
        model.eval()

        # Prepare the last sequence from data
        scaler = data.max() - data.min()
        if scaler != 0:
            scaled_data = (data - data.min()) / scaler
        else:
            scaled_data = data - data.min()

        last_sequence = scaled_data[-sequence_length:].values
        predictions = []

        model = model.to(self.device)

        with torch.no_grad():
            current_seq = (
                torch.FloatTensor(last_sequence)
                .unsqueeze(0)
                .unsqueeze(-1)
                .to(self.device)
            )

            for _ in range(forecast_days):
                next_pred = model(current_seq)

                # Add the prediction to our history
                next_pred_val = next_pred.cpu().item()
                predictions.append(next_pred_val)

                # Update the sequence by removing the first element and adding the prediction
                # next_pred shape: (1, 1), need to reshape to (1, 1, 1) to concatenate with (1, seq_len, 1)
                next_pred_reshaped = next_pred.unsqueeze(1)  # (1, 1, 1)
                current_seq = torch.cat(
                    [current_seq[:, 1:, :], next_pred_reshaped], dim=1
                )

        # Inverse transform the predictions
        if scaler != 0:
            predictions = np.array(predictions) * scaler + data.min()
        else:
            predictions = np.array(predictions) + data.min()

        return predictions
