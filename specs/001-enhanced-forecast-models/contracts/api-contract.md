# API Contract: Enhanced Forecast Models

## Overview
This document defines the API contracts for the enhanced forecasting models service. The bot operates primarily through Telegram interactions, but this contract defines the internal service interfaces.

## Service Interfaces

### Model Training Service
```python
def train_enhanced_models(stock_data: StockData) -> List[EnhancedModels]:
    """
    Trains enhanced time series models on the provided stock data.
    
    Args:
        stock_data: Historical stock data to train models on
    
    Returns:
        List of trained enhanced time series models (LSTM, GRU, RNN, ARIMA, ETS, Prophet)
        
    Raises:
        TimeoutError: If training takes longer than 5 minutes
        InsufficientDataError: If there isn't enough data to train models
    """
```

### Model Evaluation Service
```python
def evaluate_models(models: List[EnhancedModels], test_data: StockData) -> Dict[str, float]:
    """
    Evaluates models using enhanced performance metrics (RMSE, MAE, AUC).
    
    Args:
        models: List of trained enhanced time series models
        test_data: Test data to evaluate model performance
    
    Returns:
        Dictionary of performance metrics for each model
    """
```

### Model Selection Service
```python
def select_best_model(models: List[EnhancedModels], metrics: Dict[str, Dict[str, float]]) -> EnhancedModels:
    """
    Selects the best performing model based on enhanced metrics (RMSE, MAE, AUC).
    
    Args:
        models: List of trained enhanced time series models
        metrics: Performance metrics for each model
    
    Returns:
        The best performing model based on RMSE, MAE, AUC metrics
    """
```

### Interactive Visualization Service
```python
def generate_interactive_chart(forecast_result: ForecastResult) -> InteractiveChart:
    """
    Generates an interactive chart with confidence intervals for the forecast.
    
    Args:
        forecast_result: The forecast result to visualize
    
    Returns:
        InteractiveChart object with confidence intervals and interactive elements
    """
```

### Ticker Validation Service
```python
def validate_ticker_symbol(ticker: str) -> bool:
    """
    Validates ticker symbol based on stock exchange format criteria.
    
    Args:
        ticker: The ticker symbol to validate
    
    Returns:
        Boolean indicating whether the ticker is valid
    """
```

### Volatility Assessment Service
```python
def assess_volatility(stock_data: StockData) -> Tuple[bool, float]:
    """
    Assesses if the stock is extremely volatile (above 5% daily variance).
    
    Args:
        stock_data: Historical stock data to assess
    
    Returns:
        Tuple of (is_volatile, variance_percentage)
    """
```

### Logging Service
```python
def log_with_rotation(message: str, level: str = "INFO") -> None:
    """
    Logs a message using standard Python logging with configurable rotation.
    
    Args:
        message: The message to log
        level: The log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
```