# Data Model: Stock Forecast Telegram Bot

## Entities

### UserRequest
Represents a user's input including ticker symbol and investment amount, with associated metadata like user ID and timestamp.

**Fields**:
- user_id: str - Unique identifier for the Telegram user
- ticker_symbol: str - Stock ticker symbol (e.g., AAPL, GOOGL)
- investment_amount: float - Investment amount between $1 and $1,000,000
- timestamp: datetime - Time when the request was made
- status: str - Current status of the request (e.g., processing, completed, failed)

### StockData
Historical stock price information including open, close, high, low prices and volume for a given ticker.

**Fields**:
- ticker_symbol: str - Stock ticker symbol
- date: datetime - Date of the stock data point
- open_price: float - Opening price for the day
- high_price: float - Highest price for the day
- low_price: float - Lowest price for the day
- close_price: float - Closing price for the day
- volume: int - Trading volume for the day
- adjusted_close: float - Adjusted closing price accounting for splits/dividends

### TimeSeriesModels
Collection of different model types (Classical ML, Statistical, Neural Network) used for forecasting with weekly retraining.

**Fields**:
- model_id: str - Unique identifier for the model
- model_type: str - Type of model (classical_ml, statistical, neural_network)
- model_name: str - Specific model name (e.g., Random Forest, ARIMA, LSTM)
- training_date: datetime - Date when the model was last trained
- hyperparameters: dict - Model-specific hyperparameters
- performance_metrics: dict - Metrics like RMSE, MAPE, etc.

### ForecastResult
The 30-day price forecast with confidence intervals, associated metrics and trading recommendations.

**Fields**:
- forecast_id: str - Unique identifier for the forecast
- ticker_symbol: str - Stock ticker symbol
- forecast_dates: list[datetime] - List of 30 future dates
- forecast_prices: list[float] - Predicted prices for each date
- confidence_intervals: list[tuple(float, float)] - Lower and upper bounds of confidence interval for each date
- model_used: str - ID of the model that generated the forecast
- performance_metrics: dict - Metrics of the selected model
- created_at: datetime - Timestamp when forecast was created

### TradingRecommendation
Specific days and strategies for buying and selling based on forecast data.

**Fields**:
- recommendation_id: str - Unique identifier for the recommendation
- forecast_id: str - Reference to the forecast this recommendation is based on
- buy_dates: list[datetime] - Recommended dates to buy
- sell_dates: list[datetime] - Recommended dates to sell
- confidence_level: float - Confidence level of the recommendation
- created_at: datetime - Timestamp when recommendation was created

### ProfitCalculation
Estimated financial gain/loss based on investment amount and trading strategy.

**Fields**:
- calculation_id: str - Unique identifier for the calculation
- recommendation_id: str - Reference to the trading recommendation
- investment_amount: float - Original investment amount
- estimated_profit: float - Estimated profit based on strategy
- estimated_roi: float - Estimated return on investment percentage
- worst_case_scenario: float - Potential loss in worst case
- best_case_scenario: float - Potential gain in best case
- created_at: datetime - Timestamp when calculation was created

### RequestLog
Record of all user interactions with the system for monitoring and analysis with 1-year retention.

**Fields**:
- log_id: str - Unique identifier for the log entry
- user_id: str - User who made the request
- ticker_symbol: str - Ticker symbol in the request
- investment_amount: float - Investment amount in the request
- request_timestamp: datetime - Time when request was made
- response_timestamp: datetime - Time when response was generated
- selected_model: str - Model that was selected for the forecast
- performance_metrics: dict - Performance metrics of the selected model
- profit_estimate: float - Estimated profit from the recommendation
- retention_until: datetime - Date until which this log should be retained (1 year from request)