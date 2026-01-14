<!--
Sync Impact Report:
Version change: [CONSTITUTION_VERSION] → 1.0.0
Modified principles: New constitution created from template
Added sections: All core principles and governance sections
Removed sections: None (template placeholders replaced)
Templates requiring updates: ✅ All templates remain compatible
Follow-up TODOs: None
-->

# Stock Forecast Bot Constitution

## Core Principles

### I. Python-Centric Development
All development MUST use Python as the primary language. The project structure, dependencies, and tooling MUST be Python-native. This ensures consistency, maintainability, and leverages the rich ecosystem of Python libraries for data science and machine learning applications.

### II. uv Package Management
Dependency management MUST use uv as the package manager. All project dependencies MUST be declared in `pyproject.toml` and locked with `uv.lock`. This ensures reproducible builds, fast dependency resolution, and modern Python packaging practices.

### III. Telegram Bot Implementation with aiogram
The user interface MUST be implemented as a Telegram bot using the aiogram library. All user interactions MUST go through Telegram bot handlers. This provides a consistent, accessible interface for users while leveraging aiogram's modern async/await patterns and robust message handling.

### IV. CSV Data Storage Standard
When data persistence is required, the storage format MUST be CSV. Historical stock data, logs, and model outputs MUST be stored in CSV format for simplicity, portability, and easy inspection. Database systems are prohibited unless explicitly justified for performance requirements.

### V. Yahoo Finance Data Integration
Stock market data MUST be sourced exclusively from Yahoo Finance using the yfinance library. This ensures consistent, reliable, and free access to historical and current market data. Alternative data sources are prohibited to maintain data consistency and avoid API complexity.

### VI. One Commit Per Task Policy
Each implementation task MUST result in exactly one git commit. Commits MUST be atomic, focused, and directly traceable to a specific task ID. This ensures clear development history, easy rollbacks, and precise change tracking for project management and code review purposes.

### VII. Multi-Class Model Implementation for Forecasting
The forecasting system MUST implement at least three models from different classes: one Classical ML model (Random Forest, Ridge Regression with lag features), one Statistical model (ARIMA, ETS, Prophet), and one Neural Network model (LSTM, GRU, RNN). Model selection MUST be automated based on performance metrics (RMSE, MAE, MAPE). This ensures robust forecasting through model diversity and evidence-based selection.

## Development Standards

### Code Quality Requirements
- All Python code MUST follow PEP 8 style guidelines
- Type hints MUST be used for all function signatures and class attributes
- Docstrings MUST be provided for all public functions and classes using Google style
- Unit tests MUST achieve minimum 80% code coverage for core functionality
- Integration tests MUST cover the complete forecast generation pipeline

### Performance Standards
- Model training MUST complete within 5 minutes for typical stock datasets
- Telegram bot responses MUST be delivered within 30 seconds for forecast requests
- The system MUST handle API rate limits gracefully with appropriate retry mechanisms
- Memory usage MUST not exceed 1GB during normal operation

### Error Handling Requirements
- Invalid ticker symbols MUST be validated and rejected with clear error messages
- Network failures MUST be handled with exponential backoff retry logic
- Model training failures MUST be logged and fallback models MUST be available
- All exceptions MUST be logged with sufficient context for debugging

## Governance

This constitution supersedes all other development practices and guidelines. Any deviation from these principles MUST be explicitly documented and justified in the project documentation.

### Amendment Process
1. Proposed changes MUST be documented with clear rationale
2. Impact assessment MUST be performed on existing codebase
3. Migration plan MUST be provided for breaking changes
4. Version number MUST be incremented according to semantic versioning

### Compliance Review
- All pull requests MUST verify compliance with constitutional principles
- Code reviews MUST explicitly check adherence to multi-model requirements
- Deployment readiness MUST include constitutional compliance verification
- Quarterly reviews MUST assess ongoing adherence to these principles

### Version Control
Constitution changes follow semantic versioning:
- MAJOR: Principle removal or incompatible redefinition
- MINOR: New principle addition or material expansion
- PATCH: Clarifications, wording improvements, non-semantic changes

**Version**: 1.0.0 | **Ratified**: 2026-01-14 | **Last Amended**: 2026-01-14