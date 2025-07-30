# Testing Documentation for AI Trading Sentinel

## Overview

This document provides detailed information about the testing approach used in the AI Trading Sentinel project, with a specific focus on the Bulenox Futures Executor component.

## Test Files

### 1. test_bulenox_simple.py

This is the primary test file that uses mocking to test the `BulenoxFuturesExecutor` class without requiring actual browser interaction. It includes the following test cases:

- **test_execute_trade**: Tests the full trade execution flow
- **test_health_check**: Tests the health check functionality
- **test_place_trade_method**: Tests the internal `_place_trade` method directly
- **test_detect_gold_symbol**: Tests gold symbol detection
- **test_trading_mode_detection**: Tests trading mode detection and quantity adjustment

### 2. test_bulenox_selenium_dev.py

This test file attempts to interact with the Bulenox platform directly using Selenium. It's useful for integration testing but requires actual browser interaction.

### 3. test_bulenox_futures_executor_dev.py

This test file is specifically designed for testing the `BulenoxFuturesExecutor` in development mode.

## Mocking Approach

The tests in `test_bulenox_simple.py` use Python's `unittest.mock` to mock various components:

### Mocked Components

1. **Selenium WebDriver**: The Chrome WebDriver is mocked to avoid launching an actual browser
2. **WebDriverWait**: The wait functionality is mocked to avoid actual waiting periods
3. **Element Interactions**: Methods like `find_element`, `click`, and `send_keys` are mocked
4. **Login Process**: The `_login` method is mocked to simulate successful login
5. **Trade Placement**: The `_place_trade` method is mocked when testing the overall execution flow

### Example of Mocking

```python
@patch('executor_bulenox_futures.BulenoxFuturesExecutor._init_driver')
@patch('executor_bulenox_futures.BulenoxFuturesExecutor._login')
@patch('executor_bulenox_futures.BulenoxFuturesExecutor._place_trade')
def test_execute_trade(self, mock_place_trade, mock_login, mock_init_driver):
    # Configure mocks
    mock_place_trade.return_value = True
    
    # Create executor instance
    executor = BulenoxFuturesExecutor(self.signal, self.stop_loss, self.take_profit)
    
    # Execute trade
    result = executor.execute_trade()
    
    # Verify mocks were called
    mock_init_driver.assert_called_once()
    mock_login.assert_called_once()
    mock_place_trade.assert_called_once()
    
    # Verify result
    self.assertEqual(result['status'], 'success')
```

## Testing Gold Symbol Detection and Quantity Adjustment

A key feature of the `BulenoxFuturesExecutor` is its ability to detect gold symbols (GC, MGC, XAUUSD) and adjust trade quantities based on the trading mode (Evaluation or Live). The tests verify this functionality using a custom test class:

```python
class TestGoldExecutor(BulenoxFuturesExecutor):
    def _init_driver(self):
        pass
        
    def _login(self):
        pass
        
    def _place_trade(self):
        return True
        
    def _detect_gold_symbol(self):
        return "GC"
```

This approach allows for testing the quantity adjustment logic without requiring actual browser interaction.

## DEV_MODE Testing

The `DEV_MODE` environment variable plays a crucial role in the testing process. When set to `true`, it enables several features that make testing easier:

1. **Default Test Credentials**: Uses default test credentials if none are provided
2. **Enhanced Logging**: Logs more detailed information about the execution process
3. **Screenshot Capture**: Takes screenshots of key steps for debugging purposes
4. **Trade Simulation**: Prevents actual trade execution on the broker platform
5. **Quantity Adjustment**: Automatically adjusts trade quantities for gold symbols in evaluation mode

## Running the Tests

To run the mocked tests:

```bash
python test_bulenox_simple.py
```

This will execute all the test cases in the `TestBulenoxFutures` class and output the results.

## Test Results

Successful test execution will show output similar to:

```
Ran 5 tests in 32.086s

OK
```

If any tests fail, detailed error messages will be displayed to help diagnose the issue.

## Adding New Tests

When adding new tests, follow these guidelines:

1. Use the `unittest.TestCase` class as the base class for your tests
2. Use `unittest.mock.patch` to mock external dependencies
3. Create clear, descriptive test method names that indicate what is being tested
4. Include assertions that verify both the behavior and the state of the system
5. Keep tests independent of each other to avoid cascading failures

## Continuous Integration

These tests can be integrated into a CI/CD pipeline to ensure that changes to the codebase don't break existing functionality. The mocked tests are particularly well-suited for CI environments since they don't require actual browser interaction.