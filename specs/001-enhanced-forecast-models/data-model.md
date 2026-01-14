# Data Model: Enhanced Forecast Models

## Entities

### EnhancedModels
Collection of neural network models (LSTM, GRU, RNN) and statistical models (ARIMA, ETS, Prophet) for improved forecasting accuracy.

**Fields**:
- model_id: str - Unique identifier for the model
- model_type: str - Type of model (neural_network, statistical)
- model_subtype: str - Specific model name (LSTM, GRU, RNN, ARIMA, ETS, Prophet)
- training_date: datetime - Date when the model was last trained
- hyperparameters: dict - Model-specific hyperparameters
- performance_metrics: dict - Metrics like RMSE, MAE, AUC

### InteractiveChart
Visualization component that displays forecasts with confidence intervals and allows user interaction.

**Fields**:
- chart_id: str - Unique identifier for the chart
- forecast_result_id: str - Reference to the forecast result this chart represents
- interactive_elements: list[str] - List of interactive elements available on the chart
- confidence_intervals: list[tuple(float, float)] - Lower and upper bounds of confidence interval for each date
- chart_format: str - Format of the chart (e.g., 'plotly', 'matplotlib')
- created_at: datetime - Timestamp when chart was created

### ValidationCriteria
Set of rules and checks for determining the validity of ticker symbols based on valid stock exchange symbol format.

**Fields**:
- criteria_id: str - Unique identifier for the validation criteria
- symbol_pattern: str - Regular expression pattern for valid stock exchange symbol format
- exchange_list: list[str] - List of valid exchanges to validate against
- validation_rules: dict - Additional validation rules to apply
- created_at: datetime - Timestamp when criteria were defined

### LoggingFormat
Standard Python logging structure with configurable rotation strategy for maintenance.

**Fields**:
- format_id: str - Unique identifier for the logging format
- log_format: str - Format string for log entries
- rotation_strategy: str - Rotation strategy (daily, weekly, monthly, size-based)
- retention_period: int - Number of days/rotations to retain logs
- log_level: str - Minimum log level to record (DEBUG, INFO, WARNING, ERROR, CRITICAL)

### PerformanceMetrics
Quantitative measures (RMSE, MAE, AUC) used to evaluate and compare model effectiveness.

**Fields**:
- metric_id: str - Unique identifier for the metric set
- rmse: float - Root Mean Square Error value
- mae: float - Mean Absolute Error value
- auc: float - Area Under the Curve value
- calculated_on: datetime - When the metrics were calculated
- model_id: str - Reference to the model these metrics belong to
- dataset_used: str - Dataset used for calculating the metrics

### TrainingTimeout
Constraint that model training must complete within 5 minutes or return appropriate timeout error.

**Fields**:
- timeout_id: str - Unique identifier for the timeout configuration
- max_duration: int - Maximum allowed duration in minutes
- timeout_enabled: bool - Whether the timeout is enabled
- timeout_action: str - Action to take when timeout occurs (e.g., 'cancel', 'return_partial')
- created_at: datetime - Timestamp when timeout was configured

### VolatilityThreshold
Measure for identifying extremely volatile stocks (price variance above 5% daily) requiring special confidence interval handling.

**Fields**:
- threshold_id: str - Unique identifier for the threshold
- variance_percentage: float - Percentage threshold for volatility (5.0 for 5%)
- special_handling_required: bool - Whether special confidence interval handling is needed
- confidence_adjustment_factor: float - Factor by which to adjust confidence intervals for volatile stocks
- created_at: datetime - Timestamp when threshold was defined