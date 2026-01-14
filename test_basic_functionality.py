"""
Basic test to verify the implementation works as expected.
"""
import sys
import os

# Add the src directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all modules can be imported without errors."""
    print("Testing imports...")
    
    try:
        from src.models.neural_networks import NeuralNetworkModels
        from src.models.statistical import StatisticalModels
        from src.models.model_selector import ModelSelector
        from src.services.data_loader import DataLoaderService
        from src.services.forecasting import ForecastingService
        from src.services.trading_strategy import TradingStrategyService
        from src.services.profit_calculator import ProfitCalculatorService
        from src.services.logger_service import LoggerService
        from src.services.model_evaluation import ModelEvaluationService
        from src.utils.validators import validate_ticker, validate_investment_amount
        from src.utils.helpers import calculate_percentage_change
        from src.utils.visualizer import create_forecast_visualization, calculate_confidence_intervals
        from src.config.settings import TELEGRAM_BOT_TOKEN
        
        print("✓ All modules imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error during import: {e}")
        return False

def test_ticker_validation():
    """Test ticker validation functionality."""
    print("\nTesting ticker validation...")
    
    from src.utils.validators import validate_ticker
    
    valid_tickers = ["AAPL", "GOOGL", "TSLA", "BRK.B"]
    invalid_tickers = ["invalid", "TOOLONGNAME", "123ABC", ""]
    
    all_passed = True
    
    for ticker in valid_tickers:
        result = validate_ticker(ticker)
        if result:
            print(f"✓ Valid ticker '{ticker}' correctly validated")
        else:
            print(f"✗ Valid ticker '{ticker}' incorrectly rejected")
            all_passed = False
    
    for ticker in invalid_tickers:
        result = validate_ticker(ticker)
        if not result:
            print(f"✓ Invalid ticker '{ticker}' correctly rejected")
        else:
            print(f"✗ Invalid ticker '{ticker}' incorrectly accepted")
            all_passed = False
    
    return all_passed

def test_investment_validation():
    """Test investment amount validation."""
    print("\nTesting investment validation...")
    
    from src.utils.validators import validate_investment_amount
    
    valid_investments = [1, 100, 50000, 1000000]
    invalid_investments = [0, -100, 1000001, "invalid"]
    
    all_passed = True
    
    for investment in valid_investments:
        is_valid, msg = validate_investment_amount(investment)
        if is_valid:
            print(f"✓ Valid investment ${investment} correctly validated")
        else:
            print(f"✗ Valid investment ${investment} incorrectly rejected: {msg}")
            all_passed = False
    
    for investment in invalid_investments:
        is_valid, msg = validate_investment_amount(investment)
        if not is_valid:
            print(f"✓ Invalid investment {investment} correctly rejected: {msg}")
        else:
            print(f"✗ Invalid investment {investment} incorrectly accepted")
            all_passed = False
    
    return all_passed

def test_model_creation():
    """Test that model instances can be created."""
    print("\nTesting model creation...")
    
    try:
        from src.models.neural_networks import NeuralNetworkModels
        from src.models.statistical import StatisticalModels
        from src.models.model_selector import ModelSelector
        
        nn_models = NeuralNetworkModels()
        stat_models = StatisticalModels()
        model_selector = ModelSelector()
        
        print("✓ NeuralNetworkModels instance created successfully")
        print("✓ StatisticalModels instance created successfully")
        print("✓ ModelSelector instance created successfully")
        
        return True
    except Exception as e:
        print(f"✗ Error creating model instances: {e}")
        return False

def main():
    """Run all tests."""
    print("Running basic functionality tests...\n")
    
    tests = [
        test_imports,
        test_ticker_validation,
        test_investment_validation,
        test_model_creation
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print(f"\n{'='*50}")
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)