# Research Summary: Stock Forecast Telegram Bot

## Decision: Model Architecture
**Rationale**: Need to implement three different model types as required by the constitution: Classical ML, Statistical, and Neural Network models.
**Alternatives considered**: 
- Using only one type of model (rejected - doesn't meet constitutional requirement)
- Using different specific models within each category

## Decision: Technology Stack
**Rationale**: Selected libraries that align with the project constitution and requirements:
- aiogram for Telegram bot implementation
- yfinance for Yahoo Finance data retrieval
- pandas/numpy for data manipulation
- scikit-learn for classical ML models
- statsmodels for statistical models
- tensorflow/pytorch for neural networks
- matplotlib/plotly for visualization
**Alternatives considered**: Different ML libraries (e.g., PyTorch vs TensorFlow) - decided to implement with TensorFlow initially with possibility to switch if needed

## Decision: Data Storage Format
**Rationale**: Using CSV format as mandated by the constitution for data persistence.
**Alternatives considered**: JSON, SQLite, Parquet (rejected - constitution specifies CSV)

## Decision: Model Training Schedule
**Rationale**: Implementing weekly retraining as specified in the clarifications to ensure model accuracy with updated data.
**Alternatives considered**: Daily, monthly retraining cycles (selected weekly as balanced approach)

## Decision: Error Handling Strategy
**Rationale**: Implement comprehensive error handling for API limits, invalid inputs, and model training timeouts as specified in requirements.
**Alternatives considered**: Different error handling approaches (selected comprehensive approach to meet requirements)

## Decision: Confidence Intervals Implementation
**Rationale**: Including confidence intervals as required by the clarifications to ensure forecast reliability.
**Alternatives considered**: Not including confidence intervals (rejected - required by specification)