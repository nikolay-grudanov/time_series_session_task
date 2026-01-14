# Contributing to Stock Forecast Telegram Bot

Thank you for your interest in contributing to the Stock Forecast Telegram Bot! This document outlines the process for contributing to the project.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Environment](#development-environment)
3. [Coding Standards](#coding-standards)
4. [Testing](#testing)
5. [Pull Request Process](#pull-request-process)
6. [Documentation](#documentation)
7. [Issue Reporting](#issue-reporting)

## Getting Started

### Prerequisites

- Python 3.12
- uv package manager
- Git

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/time_series_session_task.git
   cd time_series_session_task
   ```

### Install Dependencies

```bash
uv sync
```

Or if using pip:
```bash
pip install -r requirements.txt
```

## Development Environment

### Setting Up

1. Create a virtual environment (if not using uv):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Create a `.env` file with your configuration:
   ```
   TELEGRAM_BOT_TOKEN=your_test_bot_token
   ```

### Running the Bot Locally

```bash
python src/main.py
```

## Coding Standards

### Python Style

- Follow PEP 8 style guidelines
- Use 4 spaces for indentation (no tabs)
- Line length should not exceed 88 characters
- Use descriptive variable and function names
- Write type hints for all functions and methods

### Code Quality Tools

This project uses several tools to maintain code quality:

1. **Ruff**: For style checking and linting
   ```bash
   ruff check src/
   ruff check --fix src/  # Auto-fix issues
   ```

2. **Pyright**: For type checking
   ```bash
   pyright src/
   ```

3. **Black**: For code formatting (optional, as Ruff handles most formatting)
   ```bash
   black src/
   ```

### Naming Conventions

- Use `snake_case` for functions, variables, and filenames
- Use `PascalCase` for class names
- Use `UPPER_SNAKE_CASE` for constants
- Private attributes/methods should start with `_`

### Documentation

- Include docstrings for all public functions, classes, and modules
- Use Google-style docstrings
- Document all parameters, return values, and exceptions

Example:
```python
def calculate_rmse(actual: np.ndarray, predicted: np.ndarray) -> float:
    """
    Calculate Root Mean Square Error between actual and predicted values.

    Args:
        actual: Array of actual values
        predicted: Array of predicted values

    Returns:
        RMSE value as a float

    Raises:
        ValueError: If arrays have different shapes
    """
    if actual.shape != predicted.shape:
        raise ValueError("Arrays must have the same shape")
    
    return np.sqrt(np.mean((actual - predicted) ** 2))
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_models/test_neural_networks.py

# Run with coverage
pytest --cov=src

# Run with verbose output
pytest -v
```

### Test Structure

Tests are organized in the `tests/` directory:

```
tests/
├── unit/                    # Unit tests for individual components
│   ├── test_models/
│   ├── test_services/
│   └── test_utils/
├── integration/             # Integration tests for the full pipeline
└── contract/                # Contract tests for API specifications
```

### Writing Tests

1. Place unit tests in the appropriate subdirectory under `tests/unit/`
2. Name test files with the pattern `test_*.py`
3. Name test functions with the pattern `test_*`
4. Use descriptive test names that explain what is being tested
5. Follow the AAA pattern: Arrange, Act, Assert

Example test:
```python
import pytest
import numpy as np
from src.models.model_selector import ModelSelector

def test_calculate_rmse():
    """Test RMSE calculation with known values."""
    # Arrange
    actual = np.array([1, 2, 3, 4, 5])
    predicted = np.array([1.1, 2.2, 2.8, 3.9, 5.1])
    expected_rmse = 0.1414  # Approximate expected value
    
    # Act
    result = calculate_rmse(actual, predicted)
    
    # Assert
    assert abs(result - expected_rmse) < 0.01
```

## Pull Request Process

### Before Submitting

1. Ensure all tests pass
2. Run code quality checks:
   ```bash
   ruff check src/
   pyright src/
   ```
3. Update documentation if needed
4. Add or update tests if adding new functionality
5. Squash commits if necessary to have a clean history

### Creating a Pull Request

1. Create a new branch for your feature/bug fix:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b bugfix/issue-description
   ```

2. Make your changes and commit them with clear, descriptive messages:
   ```bash
   git add .
   git commit -m "Add feature: description of what was added"
   ```

3. Push your branch:
   ```bash
   git push origin feature/your-feature-name
   ```

4. Open a pull request on GitHub with:
   - Clear title describing the change
   - Detailed description of what was changed and why
   - Reference any related issues

### PR Review Process

- PRs will be reviewed by maintainers
- Address any feedback provided during review
- PRs should have at least one approval before merging
- PRs should not be merged by the author unless specifically allowed

## Documentation

### Updating Documentation

When adding new features or changing existing functionality:

1. Update docstrings in the code
2. Update relevant documentation files in the `docs/` directory
3. Update the README if necessary
4. Add examples if appropriate

### Documentation Standards

- Use Markdown for documentation files
- Keep documentation clear and concise
- Include examples where helpful
- Use consistent terminology throughout

## Issue Reporting

### Bug Reports

When reporting bugs, please include:

1. A clear, descriptive title
2. Steps to reproduce the issue
3. Expected behavior
4. Actual behavior
5. Environment information (Python version, OS, etc.)
6. Relevant error messages or logs

### Feature Requests

When requesting features, please include:

1. A clear, descriptive title
2. Detailed description of the requested feature
3. Use cases for the feature
4. Any relevant examples or mockups

## Code of Conduct

Please note that this project is released with a [Contributor Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.

## Questions?

If you have questions about contributing, feel free to open an issue or contact the maintainers.

Thank you for contributing to the Stock Forecast Telegram Bot!