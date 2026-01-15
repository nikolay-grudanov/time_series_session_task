# Stock Catalog Tests

Comprehensive unit and integration tests for the stock catalog feature.

## Test Structure

```
tests/
├── conftest.py                          # Shared fixtures and pytest configuration
├── unit/
│   ├── test_catalog_cache.py            # Tests for CatalogCache class
│   ├── test_catalog_service.py          # Tests for CatalogService class
│   ├── test_validators.py              # Tests for validation utilities
│   └── test_stocks_handler.py          # Tests for stocks handler functions
└── integration/
    └── test_catalog_integration.py      # Integration tests for full workflow
```

## Running Tests

### Run all tests:
```bash
pytest tests/
```

### Run only unit tests:
```bash
pytest tests/unit/
```

### Run only integration tests:
```bash
pytest tests/integration/
```

### Run specific test file:
```bash
pytest tests/unit/test_catalog_cache.py
```

### Run specific test class:
```bash
pytest tests/unit/test_catalog_cache.py::TestCatalogCacheSingleton
```

### Run specific test:
```bash
pytest tests/unit/test_catalog_cache.py::TestCatalogCacheSingleton::test_singleton_returns_same_instance
```

### Run with verbose output:
```bash
pytest tests/ -v
```

### Run with coverage:
```bash
pytest tests/ --cov=src/utils/catalog_cache --cov=src/services/catalog_service --cov=src/utils/validators --cov=src/handlers/stocks_handler
```

### Run with coverage report:
```bash
pytest tests/ --cov=src/utils/catalog_cache --cov=src/services/catalog_service --cov=src/utils/validators --cov=src/handlers/stocks_handler --cov-report=html
```

## Test Coverage

### Unit Tests

#### test_catalog_cache.py
- Singleton pattern implementation
- Catalog loading from CSV
- Default catalog fallback
- Stock retrieval operations (get_stocks, get_stock, search_stocks)
- Cache validity and TTL
- Deduplication logic
- Delisted stock handling
- Catalog integrity validation
- Add/remove stock operations
- Utility methods

#### test_catalog_service.py
- Service initialization
- Catalog loading
- Stock retrieval
- Stock availability checks
- Catalog status retrieval
- API refresh (with mocked dependencies)
- Stock info fetching
- Error handling

#### test_validators.py
- Ticker validation (format, length, characters)
- Investment amount validation (range, type, format)
- Forecast request validation
- Stock volatility validation
- Help text generation
- Edge cases and error handling

#### test_stocks_handler.py
- Pagination logic
- Format stocks page
- Create stocks keyboard
- Helper functions (get_stocks_list, get_stocks_count, is_stock_available)
- Edge cases in formatting and pagination

### Integration Tests

#### test_catalog_integration.py
- Full catalog workflow (load, search, validate)
- Cache and service integration
- Error handling across components
- Data integrity validation
- Real-world user scenarios
- Performance considerations
- Singleton pattern behavior
- External dependency mocking
- Data consistency across operations

## Fixtures

Shared fixtures defined in `conftest.py`:

- `sample_catalog_csv` - Temporary CSV with sample stock data
- `empty_catalog_csv` - Empty CSV file
- `corrupted_catalog_csv` - Corrupted CSV file
- `large_catalog_csv` - CSV with 100 stocks
- `sample_stocks` - List of StockEntry objects
- `catalog_cache` - CatalogCache instance with sample data
- `catalog_service` - CatalogService instance with sample data
- `empty_catalog_cache` - Empty CatalogCache instance
- `mock_yfinance_ticker` - Mock yfinance Ticker object
- `mock_yfinance_ticker_multiple` - Multiple mock yfinance objects
- `mock_message` - Mock Telegram message
- `mock_callback_query` - Mock Telegram callback query

## Test Markers

Tests can be marked with:
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow running tests
- `@pytest.mark.external` - Tests requiring external dependencies

Run tests by marker:
```bash
pytest -m unit
pytest -m integration
pytest -m "not slow"
```

## Custom Assertions

Helper assertion functions in `conftest.py`:

- `assert_stock_entry_equal(stock1, stock2)` - Compare StockEntry objects
- `assert_validation_result_valid(result)` - Assert ValidationResult is valid
- `assert_validation_result_invalid(result, error_type)` - Assert ValidationResult is invalid

## Key Features Tested

### CatalogCache
- ✅ Thread-safe singleton pattern
- ✅ CSV file loading with error handling
- ✅ Default catalog fallback
- ✅ TTL-based cache expiration
- ✅ Stock search with partial matching
- ✅ Case-insensitive operations
- ✅ Deduplication logic
- ✅ Delisted stock handling
- ✅ Integrity validation

### CatalogService
- ✅ Service initialization
- ✅ Catalog loading and refreshing
- ✅ Stock retrieval and search
- ✅ Availability checking
- ✅ Status reporting
- ✅ API integration (mocked)
- ✅ Error handling and fallbacks

### Validators
- ✅ Ticker format validation
- ✅ Investment amount validation
- ✅ Range checking
- ✅ Type checking
- ✅ Error message generation
- ✅ Help text

### Stocks Handler
- ✅ Pagination logic
- ✅ Message formatting
- ✅ Keyboard creation
- ✅ Callback data handling
- ✅ Edge cases

## Notes

1. **External Dependencies**: All external dependencies (yfinance, filesystem) are mocked in tests
2. **Singleton Reset**: The CatalogCache singleton is reset between tests using the `reset_catalog_cache` fixture
3. **Temporary Files**: CSV files are created as temporary files and cleaned up automatically
4. **Async Tests**: The stocks_handler contains async functions, but the helper functions tested here are synchronous
5. **Coverage**: Aim for >80% code coverage across all tested modules

## Troubleshooting

### Tests fail with import errors
Make sure you're running tests from the project root:
```bash
cd /home/gna/workspase/education/MEPHI/time_series_session_task
pytest tests/
```

### Tests fail with "CatalogCache already initialized"
The singleton reset fixture should handle this. If issues persist, try:
```bash
pytest tests/ --forked
```

### Coverage report not generating
Install pytest-cov:
```bash
pip install pytest-cov
```

## Contributing

When adding new tests:
1. Follow the existing test structure
2. Use descriptive test names
3. Add appropriate fixtures to conftest.py if needed
4. Include docstrings for test classes and methods
5. Test both success and failure cases
6. Test edge cases and boundary conditions
7. Mock external dependencies
8. Clean up resources (files, connections, etc.)