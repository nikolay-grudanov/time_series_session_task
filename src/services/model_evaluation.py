"""
Service for evaluating model performance and storing metrics.
"""
import csv
import logging
import os
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

logger = logging.getLogger(__name__)


class ModelEvaluationService:
    """
    Service for evaluating model performance and storing metrics for comparison.
    """
    def __init__(self, metrics_file_path: str = "data/model_performance.csv"):
        self.metrics_file_path = metrics_file_path
        self.ensure_metrics_file_exists()

    def ensure_metrics_file_exists(self):
        """
        Ensures the metrics file exists with proper headers.
        """
        if not os.path.exists(self.metrics_file_path):
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.metrics_file_path), exist_ok=True)

            # Create file with headers
            with open(self.metrics_file_path, 'w', newline='') as csvfile:
                fieldnames = [
                    'timestamp', 'ticker', 'model_name',
                    'rmse', 'mae', 'mape', 'auc',
                    'training_time', 'data_size', 'notes'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

    def store_model_performance(
        self,
        ticker: str,
        model_name: str,
        metrics: dict[str, float],
        training_time: float,
        data_size: int,
        notes: str = ""
    ):
        """
        Stores model performance metrics to CSV file for comparison and analysis.

        Args:
            ticker: Stock ticker symbol
            model_name: Name of the model
            metrics: Dictionary containing performance metrics (rmse, mae, mape, auc)
            training_time: Time taken to train the model in seconds
            data_size: Size of the training data
            notes: Additional notes about the model run
        """
        logger.info(f"Storing performance metrics for {model_name} on {ticker}")

        # Prepare row data
        row = {
            'timestamp': datetime.now().isoformat(),
            'ticker': ticker,
            'model_name': model_name,
            'rmse': metrics.get('rmse', ''),
            'mae': metrics.get('mae', ''),
            'mape': metrics.get('mape', ''),
            'auc': metrics.get('auc', ''),
            'training_time': training_time,
            'data_size': data_size,
            'notes': notes
        }

        # Append to CSV file
        with open(self.metrics_file_path, 'a', newline='') as csvfile:
            fieldnames = [
                'timestamp', 'ticker', 'model_name',
                'rmse', 'mae', 'mape', 'auc',
                'training_time', 'data_size', 'notes'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerow(row)

        logger.info(f"Performance metrics stored for {model_name} on {ticker}")

    def get_model_comparison(self, ticker: str | None = None) -> pd.DataFrame:
        """
        Retrieves model performance metrics for comparison.

        Args:
            ticker: Optional ticker symbol to filter results

        Returns:
            DataFrame with model performance metrics
        """
        try:
            df = pd.read_csv(self.metrics_file_path)

            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'])

            # Filter by ticker if provided
            if ticker:
                df = df[df['ticker'] == ticker]

            # Convert numeric columns
            numeric_cols = ['rmse', 'mae', 'mape', 'auc', 'training_time', 'data_size']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            return df
        except FileNotFoundError:
            logger.warning(f"Metrics file not found: {self.metrics_file_path}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error reading metrics file: {e!s}")
            return pd.DataFrame()

    def get_best_model_by_metric(self, ticker: str, metric: str = 'rmse') -> dict[str, Any]:
        """
        Gets the best performing model for a ticker based on a specific metric.

        Args:
            ticker: Stock ticker symbol
            metric: Metric to use for comparison ('rmse', 'mae', 'mape', 'auc')

        Returns:
            Dictionary with best model information
        """
        df = self.get_model_comparison(ticker)

        if df.empty:
            return {}

        # Remove rows where the metric is null
        df_filtered = df.dropna(subset=[metric])

        if df_filtered.empty:
            return {}

        # For metrics like RMSE, MAE, MAPE - lower is better
        # For AUC - higher is better
        if metric.lower() in ['rmse', 'mae', 'mape']:
            best_row = df_filtered.loc[df_filtered[metric].idxmin()]
        elif metric.lower() == 'auc':
            best_row = df_filtered.loc[df_filtered[metric].idxmax()]
        else:
            # Default to RMSE if unknown metric
            best_row = df_filtered.loc[df_filtered['rmse'].idxmin()]

        return best_row.to_dict()

    def calculate_composite_score(self, metrics: dict[str, float]) -> float:
        """
        Calculates a composite score combining multiple metrics.
        Lower scores are better.

        Args:
            metrics: Dictionary containing rmse, mae, mape, auc

        Returns:
            Composite score
        """
        # Normalize metrics and create a composite score
        # For error metrics (RMSE, MAE, MAPE), lower is better
        # For AUC, higher is better (so we subtract it from 1)
        rmse = metrics.get('rmse', 0)
        mae = metrics.get('mae', 0)
        mape = metrics.get('mape', 0)
        auc = metrics.get('auc', 0.5)  # Default to 0.5 if not provided

        # Weighted combination (these weights can be adjusted based on importance)
        # Using a simple approach: sum of normalized errors minus auc contribution
        composite_score = (rmse * 0.3) + (mae * 0.3) + (mape * 0.2) + ((1 - auc) * 0.2)

        return composite_score

    def get_overall_best_model(self, ticker: str) -> dict[str, Any]:
        """
        Gets the best performing model for a ticker based on composite scoring.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with best model information
        """
        df = self.get_model_comparison(ticker)

        if df.empty:
            return {}

        # Calculate composite scores for each model
        df['composite_score'] = df.apply(
            lambda row: self.calculate_composite_score({
                'rmse': row['rmse'],
                'mae': row['mae'],
                'mape': row['mape'],
                'auc': row['auc']
            }), axis=1
        )

        # Remove rows where composite score is null
        df_filtered = df.dropna(subset=['composite_score'])

        if df_filtered.empty:
            return {}

        # Find the model with the lowest composite score (better performance)
        best_row = df_filtered.loc[df_filtered['composite_score'].idxmin()]

        return best_row.to_dict()

    def generate_performance_report(self, ticker: str | None = None) -> str:
        """
        Generates a performance report comparing all models.

        Args:
            ticker: Optional ticker symbol to filter results

        Returns:
            String with performance report
        """
        df = self.get_model_comparison(ticker)

        if df.empty:
            return "No performance data available."

        report_lines = []
        report_lines.append("Model Performance Report")
        report_lines.append("=" * 50)

        if ticker:
            report_lines.append(f"For Ticker: {ticker}")
            report_lines.append("-" * 30)

        # Group by model name and calculate mean metrics
        grouped = df.groupby('model_name').agg({
            'rmse': ['mean', 'std'],
            'mae': ['mean', 'std'],
            'mape': ['mean', 'std'],
            'auc': ['mean', 'std'],
            'training_time': ['mean', 'std']
        }).round(4)

        for model_name in grouped.index:
            report_lines.append(f"\nModel: {model_name}")
            report_lines.append(f"  RMSE: {grouped.loc[model_name, ('rmse', 'mean')]:.4f} ± {grouped.loc[model_name, ('rmse', 'std')]:.4f}")
            report_lines.append(f"  MAE:  {grouped.loc[model_name, ('mae', 'mean')]:.4f} ± {grouped.loc[model_name, ('mae', 'std')]:.4f}")
            report_lines.append(f"  MAPE: {grouped.loc[model_name, ('mape', 'mean')]:.4f}% ± {grouped.loc[model_name, ('mape', 'std')]:.4f}%")
            report_lines.append(f"  AUC:  {grouped.loc[model_name, ('auc', 'mean')]:.4f} ± {grouped.loc[model_name, ('auc', 'std')]:.4f}")
            report_lines.append(f"  Training Time: {grouped.loc[model_name, ('training_time', 'mean')]:.2f}s ± {grouped.loc[model_name, ('training_time', 'std')]:.2f}s")

        # Identify best model by composite score
        if ticker:
            best_model = self.get_overall_best_model(ticker)
            if best_model:
                report_lines.append(f"\nOverall Best Model for {ticker}: {best_model['model_name']}")
                report_lines.append(f"  Composite Score: {best_model['composite_score']:.4f}")

        return "\n".join(report_lines)

    def evaluate_predictions(self, actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
        """
        Evaluates predictions against actual values using multiple metrics.

        Args:
            actual: Array of actual values
            predicted: Array of predicted values

        Returns:
            Dictionary with evaluation metrics
        """
        # Calculate RMSE
        rmse = np.sqrt(np.mean((actual - predicted) ** 2))

        # Calculate MAE
        mae = np.mean(np.abs(actual - predicted))

        # Calculate MAPE
        mape = np.mean(np.abs((actual - predicted) / actual)) * 100

        # Calculate AUC (area under the curve) - treating this as a ranking problem
        try:

            # Create binary labels based on whether values are above or below median
            threshold = np.median(actual)
            actual_binary = (actual > threshold).astype(int)

            # Normalize predictions to 0-1 range for AUC calculation
            pred_normalized = (predicted - predicted.min()) / (predicted.max() - predicted.min() + 1e-8)

            auc = roc_auc_score(actual_binary, pred_normalized)
        except ImportError:
            # If sklearn is not available, use a simpler approximation
            auc = 0.5  # Neutral value

        return {
            'rmse': rmse,
            'mae': mae,
            'mape': mape,
            'auc': auc
        }
