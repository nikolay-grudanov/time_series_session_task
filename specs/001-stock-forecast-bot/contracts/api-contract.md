# API Contract: Stock Forecast Telegram Bot

## Overview
This document defines the API contracts for the stock forecast telegram bot service. The bot operates primarily through Telegram interactions, but this contract defines the internal service interfaces.

## Service Interfaces

### Data Loader Service
```python
def load_historical_data(ticker_symbol: str, start_date: datetime, end_date: datetime) -> StockData:
    """
    Loads historical stock data for a given ticker symbol within a date range.
    
    Args:
        ticker_symbol: The stock ticker symbol (e.g., AAPL, GOOGL)
        start_date: Start date for historical data
        end_date: End date for historical data
    
    Returns:
        StockData object containing historical price information
        
    Raises:
        ValueError: If ticker symbol is invalid
        ConnectionError: If unable to connect to data source
        TimeoutError: If data retrieval takes too long
    """
```

### Model Training Service
```python
def train_models(stock_data: StockData) -> List[TimeSeriesModel]:
    """
    Trains multiple time series models on the provided stock data.
    
    Args:
        stock_data: Historical stock data to train models on
    
    Returns:
        List of trained time series models
        
    Raises:
        TimeoutError: If training takes longer than 5 minutes
        InsufficientDataError: If there isn't enough data to train models
    """
```

### Model Selection Service
```python
def select_best_model(models: List[TimeSeriesModel], test_data: StockData) -> TimeSeriesModel:
    """
    Evaluates models using quality metrics and selects the best performing one.
    
    Args:
        models: List of trained time series models
        test_data: Test data to evaluate model performance
    
    Returns:
        The best performing model based on RMSE and MAPE metrics
    """
```

### Forecasting Service
```python
def generate_forecast(model: TimeSeriesModel, periods: int = 30) -> ForecastResult:
    """
    Generates a forecast using the selected model for the specified number of periods.
    
    Args:
        model: The selected time series model
        periods: Number of days to forecast (default 30)
    
    Returns:
        ForecastResult object containing predictions and confidence intervals
    """
```

### Trading Strategy Service
```python
def generate_trading_recommendations(forecast_result: ForecastResult) -> TradingRecommendation:
    """
    Generates buy/sell recommendations based on the forecast.
    
    Args:
        forecast_result: The forecast result to base recommendations on
    
    Returns:
        TradingRecommendation object with buy/sell dates
    """
```

### Profit Calculator Service
```python
def calculate_potential_profit(
    investment_amount: float, 
    trading_recommendation: TradingRecommendation,
    forecast_result: ForecastResult
) -> ProfitCalculation:
    """
    Calculates potential profit based on investment amount and trading strategy.
    
    Args:
        investment_amount: The amount invested
        trading_recommendation: The trading strategy to follow
        forecast_result: The forecast to base calculations on
    
    Returns:
        ProfitCalculation object with estimated gains/losses
    """
```

### Logger Service
```python
def log_request(user_request: UserRequest, forecast_result: ForecastResult, 
                profit_calculation: ProfitCalculation) -> None:
    """
    Logs the user request and results for monitoring and analysis.
    
    Args:
        user_request: The original user request
        forecast_result: The forecast generated
        profit_calculation: The profit calculation
    """
```