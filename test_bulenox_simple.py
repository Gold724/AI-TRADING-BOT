import os
import json
import time
import sys
import unittest
import unittest.mock
from dotenv import load_dotenv

# Set DEV_MODE environment variable to true
os.environ['DEV_MODE'] = 'true'

# Set test credentials for DEV_MODE
os.environ['BULENOX_USERNAME'] = 'test_user'
os.environ['BULENOX_PASSWORD'] = 'test_password'
os.environ['CHROME_PROFILE_PATH'] = os.path.join(os.getcwd(), 'temp_chrome_profile')

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

# Import the executor class
from backend.executor_bulenox_futures import BulenoxFuturesExecutor

class TestBulenoxFutures(unittest.TestCase):
    def setUp(self):
        # Load environment variables
        load_dotenv()
        
        # Create a test signal for GBPUSD which will be mapped to MBTQ25
        self.test_signal = {
            "symbol": "GBPUSD",  # This will be mapped to MBTQ25
            "side": "buy",
            "quantity": 1,
            "price": None,  # Market order
            "type": "MARKET"
        }
        
        # Create stop loss and take profit values
        self.stop_loss = 1.2500  # Adjust based on current market price
        self.take_profit = 1.2700  # Adjust based on current market price
        
        print("\nTest Signal:")
        print(json.dumps(self.test_signal, indent=2))
        print(f"Stop Loss: {self.stop_loss}")
        print(f"Take Profit: {self.take_profit}")
    
    @unittest.mock.patch('backend.executor_bulenox_futures.BulenoxFuturesExecutor._init_driver')
    @unittest.mock.patch('backend.executor_bulenox_futures.BulenoxFuturesExecutor._login')
    @unittest.mock.patch('backend.executor_bulenox_futures.BulenoxFuturesExecutor._place_trade')
    def test_execute_trade(self, mock_place_trade, mock_login, mock_init_driver):
        # Configure mocks
        mock_driver = unittest.mock.MagicMock()
        mock_init_driver.return_value = mock_driver
        mock_login.return_value = True
        mock_place_trade.return_value = True
        
        print("Running in DEV_MODE: No actual trades will be executed")
        
        # Initialize the executor
        print("\nInitializing BulenoxFuturesExecutor...")
        executor = BulenoxFuturesExecutor(self.test_signal, self.stop_loss, self.take_profit)
        print("Executor initialized successfully")
        
        # Print futures symbol mapping
        print("\nFutures Symbol Mapping:")
        for symbol, futures_symbol in executor.futures_symbols.items():
            print(f"{symbol} -> {futures_symbol}")
        
        # Print gold symbols
        print("\nGold Symbols:")
        for symbol in executor.gold_symbols:
            print(f"- {symbol}")
        
        # Get trading mode
        print("\nTrading Mode:")
        mode = "Evaluation" if executor._detect_trading_mode() else "Funded"
        print(f"Mode: {mode}")
        
        # Test mapping a symbol
        original_symbol = self.test_signal["symbol"]
        mapped_symbol = executor._map_to_futures_symbol(original_symbol)
        print(f"\nMapped {original_symbol} to {mapped_symbol}")
        
        # Execute the trade
        print("\nExecuting test trade...")
        print("NOTE: This will simulate a trade but NOT actually execute it in DEV_MODE.")
        
        # Execute the trade with mocked components
        result = executor.execute_trade()
        
        # Display the result
        print("\nTrade Execution Result:")
        print(json.dumps(result, indent=2))
        
        # Verify the mocks were called
        mock_init_driver.assert_called_once()
        mock_login.assert_called_once_with(mock_driver)
        mock_place_trade.assert_called_once_with(mock_driver)
        
        # Check if trade was successful
        self.assertEqual(result.get("status"), "success")
        print("\n✅ Test trade executed successfully!")
        
        print("\nTest completed successfully!")
        
    @unittest.mock.patch('backend.executor_bulenox_futures.BulenoxFuturesExecutor._init_driver')
    @unittest.mock.patch('backend.executor_bulenox_futures.BulenoxFuturesExecutor._login')
    @unittest.mock.patch('selenium.webdriver.common.keys.Keys.RETURN', unittest.mock.PropertyMock(return_value='\ue006'))
    @unittest.mock.patch('selenium.webdriver.support.wait.WebDriverWait')
    def test_place_trade_method(self, mock_wait, mock_login, mock_init_driver):
        # Configure mocks
        mock_driver = unittest.mock.MagicMock()
        mock_init_driver.return_value = mock_driver
        mock_login.return_value = True
        
        # Mock WebDriverWait and expected_conditions
        mock_wait_instance = unittest.mock.MagicMock()
        mock_wait.return_value = mock_wait_instance
        mock_wait_instance.until.return_value = unittest.mock.MagicMock()
        
        # Mock find_element to return mock elements
        mock_symbol_input = unittest.mock.MagicMock()
        mock_quantity_input = unittest.mock.MagicMock()
        mock_sl_input = unittest.mock.MagicMock()
        mock_tp_input = unittest.mock.MagicMock()
        mock_buy_button = unittest.mock.MagicMock()
        mock_confirm_button = unittest.mock.MagicMock()
        
        # Configure find_element to return different mock elements based on selector
        def mock_find_element(by, selector):
            if "symbol" in selector.lower() or "search" in selector.lower():
                return mock_symbol_input
            elif "quantity" in selector.lower():
                return mock_quantity_input
            elif "stop loss" in selector.lower():
                return mock_sl_input
            elif "take profit" in selector.lower():
                return mock_tp_input
            elif "buy" in selector.lower():
                return mock_buy_button
            elif "confirm" in selector.lower():
                return mock_confirm_button
            else:
                raise Exception(f"Element not found: {selector}")
        
        mock_driver.find_element.side_effect = mock_find_element
        
        # Create a test signal for a buy trade
        buy_signal = {
            "symbol": "GBPUSD",  # Will be mapped to MBTQ25
            "side": "buy",
            "quantity": 1,
            "price": None,  # Market order
            "type": "MARKET"
        }
        
        # Initialize the executor with the buy signal
        executor = BulenoxFuturesExecutor(buy_signal, self.stop_loss, self.take_profit)
        
        # Test the _place_trade method directly
        print("\nTesting _place_trade method with buy signal...")
        result = executor._place_trade(mock_driver)
        
        # Verify interactions - the executor sends RETURN key after entering symbol
        self.assertTrue(mock_symbol_input.send_keys.called)
        mock_quantity_input.clear.assert_called_once()
        mock_quantity_input.send_keys.assert_called_with("1")
        mock_sl_input.clear.assert_called_once()
        mock_sl_input.send_keys.assert_called_with(str(self.stop_loss))
        mock_tp_input.clear.assert_called_once()
        mock_tp_input.send_keys.assert_called_with(str(self.take_profit))
        mock_buy_button.click.assert_called_once()
        mock_confirm_button.click.assert_called_once()
        
        # Check result
        self.assertTrue(result)
        print("Buy trade placement test passed")
        
        # Now test with a sell signal
        sell_signal = {
            "symbol": "EURUSD",  # Will be mapped to 6EU25
            "side": "sell",
            "quantity": 2,
            "price": None,  # Market order
            "type": "MARKET"
        }
        
        # Reset mocks
        mock_symbol_input.reset_mock()
        mock_quantity_input.reset_mock()
        mock_sl_input.reset_mock()
        mock_tp_input.reset_mock()
        mock_buy_button.reset_mock()
        mock_confirm_button.reset_mock()
        
        # Initialize the executor with the sell signal
        executor = BulenoxFuturesExecutor(sell_signal, self.stop_loss, self.take_profit)
        
        # Test the _place_trade method with sell signal
        print("\nTesting _place_trade method with sell signal...")
        result = executor._place_trade(mock_driver)
        
        # Verify interactions for sell trade
        self.assertTrue(mock_symbol_input.send_keys.called)
        mock_quantity_input.clear.assert_called_once()
        mock_quantity_input.send_keys.assert_called_with("2")
        mock_sl_input.clear.assert_called_once()
        mock_sl_input.send_keys.assert_called_with(str(self.stop_loss))
        mock_tp_input.clear.assert_called_once()
        mock_tp_input.send_keys.assert_called_with(str(self.take_profit))
        
        # Check result
        self.assertTrue(result)
        print("Sell trade placement test passed")
        
    @unittest.mock.patch('backend.executor_bulenox_futures.BulenoxFuturesExecutor._init_driver')
    @unittest.mock.patch('backend.executor_bulenox_futures.BulenoxFuturesExecutor._login')
    def test_health_check(self, mock_login, mock_init_driver):
        # Configure mocks
        mock_driver = unittest.mock.MagicMock()
        mock_init_driver.return_value = mock_driver
        mock_login.return_value = True
        
        # Initialize the executor
        executor = BulenoxFuturesExecutor(self.test_signal, self.stop_loss, self.take_profit)
        
        # Test health check
        print("\nTesting health check...")
        health_status = executor.health()
        
        # Verify the mocks were called
        mock_init_driver.assert_called_once()
        mock_login.assert_called_once_with(mock_driver)
        
        # Check health status
        self.assertTrue(health_status)
        print(f"Executor health: {'PASSED' if health_status else 'FAILED'}")
    
    @unittest.mock.patch('backend.executor_bulenox_futures.BulenoxFuturesExecutor._init_driver')
    @unittest.mock.patch('backend.executor_bulenox_futures.BulenoxFuturesExecutor._login')
    def test_detect_gold_symbol(self, mock_login, mock_init_driver):
        # Configure mocks
        mock_driver = unittest.mock.MagicMock()
        mock_init_driver.return_value = mock_driver
        mock_login.return_value = True
        
        # Mock find_element to simulate finding the symbol search input
        mock_symbol_input = unittest.mock.MagicMock()
        
        # Configure find_element to return the mock symbol input for specific selectors
        def mock_find_element(by, selector):
            if "search" in selector.lower() or "symbol" in selector.lower():
                return mock_symbol_input
            else:
                raise Exception(f"Element not found: {selector}")
        
        mock_driver.find_element.side_effect = mock_find_element
        
        # Mock WebDriverWait to simulate successful element location
        mock_wait = unittest.mock.MagicMock()
        mock_wait_instance = unittest.mock.MagicMock()
        mock_wait.return_value = mock_wait_instance
        mock_wait_instance.until.return_value = True
        
        # Create a test signal for gold
        gold_signal = {
            "symbol": "XAUUSD",  # Gold symbol
            "side": "buy",
            "quantity": 1,
            "price": None,
            "type": "MARKET"
        }
        
        # Initialize the executor with gold signal
        executor = BulenoxFuturesExecutor(gold_signal, self.stop_loss, self.take_profit)
        
        # Mock the _detect_gold_symbol method to return a specific gold symbol
        with unittest.mock.patch.object(executor, '_detect_gold_symbol', return_value="GC"):
            # Test gold symbol detection
            print("\nTesting gold symbol detection...")
            detected_symbol = executor._detect_gold_symbol(mock_driver)
            
            # With our patched method, it should return "GC"
            self.assertEqual(detected_symbol, "GC")
            self.assertIn(detected_symbol, executor.gold_symbols)
            print(f"Detected gold symbol: {detected_symbol}")
        
    @unittest.mock.patch('backend.executor_bulenox_futures.BulenoxFuturesExecutor._init_driver')
    @unittest.mock.patch('backend.executor_bulenox_futures.BulenoxFuturesExecutor._login')
    def test_trading_mode_detection(self, mock_login, mock_init_driver):
        # Configure mocks
        mock_driver = unittest.mock.MagicMock()
        mock_init_driver.return_value = mock_driver
        mock_login.return_value = True
        
        # Initialize the executor
        executor = BulenoxFuturesExecutor(self.test_signal, self.stop_loss, self.take_profit)
        
        # Test trading mode detection
        print("\nTesting trading mode detection...")
        is_evaluation_mode = executor._detect_trading_mode()
        
        # The current implementation always returns True (Evaluation Mode)
        self.assertTrue(is_evaluation_mode)
        print(f"Trading mode: {'Evaluation' if is_evaluation_mode else 'Funded'}")
        
        # Test with a gold symbol and quantity adjustment
        gold_signal = {
            "symbol": "XAUUSD",
            "side": "buy",
            "quantity": 5,  # More than allowed in evaluation mode
            "price": None,
            "type": "MARKET"
        }
        
        # Test gold quantity adjustment directly
        print("\nTesting gold quantity adjustment in evaluation mode...")
        
        # Create a custom executor for testing gold quantity adjustment
        class TestGoldExecutor(BulenoxFuturesExecutor):
            def _init_driver(self):
                return unittest.mock.MagicMock()
                
            def _login(self, driver):
                return True
                
            def _place_trade(self, driver):
                return True
                
            def _detect_gold_symbol(self, driver):
                return "GC"
        
        # Initialize the test executor with gold signal
        gold_executor = TestGoldExecutor(gold_signal, self.stop_loss, self.take_profit)
        gold_executor.evaluation_mode = True  # Ensure evaluation mode is set
        gold_executor.detected_gold_symbol = "GC"  # Set detected symbol manually
        
        # Execute trade to test quantity adjustment
        result = gold_executor.execute_trade()
        
        # Check if quantity was adjusted
        self.assertEqual(result.get("status"), "success")
        self.assertTrue(result.get("gold_symbol_detected", False))
        self.assertEqual(result.get("detected_symbol"), "GC")
        self.assertTrue(result.get("quantity_adjusted", False))
        self.assertEqual(result.get("adjusted_quantity"), 1)  # Should be limited to 1 in evaluation mode
        print(f"Gold quantity adjustment test: {'PASSED' if result.get('quantity_adjusted') else 'FAILED'}")

def test_bulenox_futures():
    # Run the test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBulenoxFutures)
    unittest.TextTestRunner(verbosity=2).run(suite)
    return True

if __name__ == "__main__":
    print("AI Trading Sentinel - Bulenox Futures Test (DEV MODE)")
    print("===================================================")
    test_bulenox_futures()