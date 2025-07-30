#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Comprehensive Test Suite for Fibonacci Strategy Dashboard

This script provides a comprehensive test suite for the Fibonacci Strategy Dashboard,
testing all major features and integration points including:
- Dashboard API endpoints
- Signal management
- Trade execution
- Trade history management
- Metrics calculation
- Settings management

Usage:
    python comprehensive_fibonacci_dashboard_test.py
"""

import unittest
import json
import os
import sys
import time
import threading
import requests
import tempfile
import shutil
from datetime import datetime, timedelta

# Add parent directory to path to import dashboard module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the dashboard module
from backend.fibonacci_strategy_dashboard import app, start_server


class TestFibonacciDashboard(unittest.TestCase):
    """Comprehensive test suite for the Fibonacci Strategy Dashboard"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment before running tests"""
        # Create temporary directories for test files
        cls.temp_dir = tempfile.mkdtemp()
        cls.history_file = os.path.join(cls.temp_dir, "test_fibonacci_trades.json")
        cls.signals_file = os.path.join(cls.temp_dir, "test_fibonacci_signals.json")
        
        # Create sample history and signals files
        cls._create_sample_history_file()
        cls._create_sample_signals_file()
        
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['HISTORY_FILE'] = cls.history_file
        app.config['SIGNALS_FILE'] = cls.signals_file
        cls.client = app.test_client()
        
        # Start server in a separate thread
        cls.port = 5555
        cls.server_thread = threading.Thread(
            target=start_server,
            args=("localhost", cls.port, cls.history_file, cls.signals_file, False)
        )
        cls.server_thread.daemon = True
        cls.server_thread.start()
        
        # Wait for server to start
        time.sleep(2)
        cls.base_url = f"http://localhost:{cls.port}"
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after tests"""
        # Remove temporary directory and files
        shutil.rmtree(cls.temp_dir)
    
    @classmethod
    def _create_sample_history_file(cls):
        """Create a sample trade history file for testing"""
        sample_history = [
            {
                "timestamp": (datetime.now() - timedelta(days=5)).isoformat(),
                "symbol": "BTCUSD",
                "side": "long",
                "quantity": 0.1,
                "entry": 50000,
                "fib_level": 0.618,
                "action": "entry",
                "price": 50000,
                "status": "success"
            },
            {
                "timestamp": (datetime.now() - timedelta(days=4)).isoformat(),
                "symbol": "BTCUSD",
                "side": "long",
                "quantity": 0.05,
                "entry": 50000,
                "fib_level": 0.5,
                "action": "partial_exit",
                "price": 55000,
                "status": "success"
            },
            {
                "timestamp": (datetime.now() - timedelta(days=3)).isoformat(),
                "symbol": "ETHUSD",
                "side": "short",
                "quantity": 1.0,
                "entry": 3000,
                "fib_level": 0.382,
                "action": "entry",
                "price": 3000,
                "status": "success"
            },
            {
                "timestamp": (datetime.now() - timedelta(days=2)).isoformat(),
                "symbol": "ETHUSD",
                "side": "short",
                "quantity": 0.5,
                "entry": 3000,
                "fib_level": 0.236,
                "action": "partial_exit",
                "price": 2800,
                "status": "success"
            },
            {
                "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
                "symbol": "XAUUSD",
                "side": "long",
                "quantity": 0.1,
                "entry": 1800,
                "fib_level": 0.786,
                "action": "entry",
                "price": 1800,
                "status": "success"
            }
        ]
        with open(cls.history_file, 'w') as f:
            json.dump(sample_history, f, indent=2)
    
    @classmethod
    def _create_sample_signals_file(cls):
        """Create a sample signals file for testing"""
        sample_signals = [
            {
                "id": "1",
                "symbol": "BTCUSD",
                "side": "long",
                "quantity": 0.1,
                "entry": 50000,
                "fib_low": 45000,
                "fib_high": 60000,
                "stopLoss": 44000,
                "takeProfit": 65000,
                "stealth_level": 2,
                "description": "Test BTC long position"
            },
            {
                "id": "2",
                "symbol": "ETHUSD",
                "side": "short",
                "quantity": 1.0,
                "entry": 3000,
                "fib_low": 2500,
                "fib_high": 3500,
                "stopLoss": 3600,
                "takeProfit": 2400,
                "stealth_level": 3,
                "description": "Test ETH short position"
            },
            {
                "id": "3",
                "symbol": "XAUUSD",
                "side": "long",
                "quantity": 0.1,
                "entry": 1800,
                "fib_low": 1750,
                "fib_high": 1900,
                "stopLoss": 1700,
                "takeProfit": 2000,
                "stealth_level": 1,
                "description": "Test Gold long position"
            }
        ]
        with open(cls.signals_file, 'w') as f:
            json.dump(sample_signals, f, indent=2)
    
    def test_01_dashboard_home(self):
        """Test that the dashboard home page loads correctly"""
        response = requests.get(f"{self.base_url}/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Fibonacci Strategy Dashboard", response.text)
    
    def test_02_active_trades_api(self):
        """Test the active trades API endpoint"""
        response = requests.get(f"{self.base_url}/api/active-trades")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        # The active trades should be the ones with entry action and no corresponding exit
        active_symbols = [trade["symbol"] for trade in data]
        self.assertIn("BTCUSD", active_symbols)
        self.assertIn("ETHUSD", active_symbols)
        self.assertIn("XAUUSD", active_symbols)
    
    def test_03_trade_history_api(self):
        """Test the trade history API endpoint"""
        response = requests.get(f"{self.base_url}/api/trade-history")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 5)  # We created 5 sample trades
    
    def test_04_signals_api(self):
        """Test the signals API endpoint"""
        response = requests.get(f"{self.base_url}/api/signals")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 3)  # We created 3 sample signals
    
    def test_05_recent_activity_api(self):
        """Test the recent activity API endpoint"""
        response = requests.get(f"{self.base_url}/api/recent-activity")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        # Should return the 5 most recent activities
        self.assertLessEqual(len(data), 5)
    
    def test_06_metrics_api(self):
        """Test the metrics API endpoint"""
        response = requests.get(f"{self.base_url}/api/metrics")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, dict)
        # Check that all expected metrics are present
        expected_metrics = [
            "total_trades", "successful_trades", "success_rate", 
            "total_symbols", "long_trades", "short_trades",
            "avg_fib_level", "most_traded_symbol", "most_successful_fib_level"
        ]
        for metric in expected_metrics:
            self.assertIn(metric, data)
    
    def test_07_add_signal(self):
        """Test adding a new signal"""
        new_signal = {
            "symbol": "EURUSD",
            "side": "short",
            "quantity": 0.5,
            "entry": 1.1000,
            "fib_low": 1.0800,
            "fib_high": 1.1200,
            "stopLoss": 1.1300,
            "takeProfit": 1.0700,
            "stealth_level": 2,
            "description": "Test EUR short position"
        }
        response = requests.post(
            f"{self.base_url}/api/add-signal",
            json=new_signal
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        
        # Verify the signal was added
        response = requests.get(f"{self.base_url}/api/signals")
        signals = response.json()
        self.assertEqual(len(signals), 4)  # Now we should have 4 signals
        
        # Find the new signal
        new_signals = [s for s in signals if s["symbol"] == "EURUSD"]
        self.assertEqual(len(new_signals), 1)
        self.assertEqual(new_signals[0]["side"], "short")
    
    def test_08_delete_signal(self):
        """Test deleting a signal"""
        # First get all signals to find the ID of the one we want to delete
        response = requests.get(f"{self.base_url}/api/signals")
        signals = response.json()
        eurusd_signal = next(s for s in signals if s["symbol"] == "EURUSD")
        signal_id = eurusd_signal["id"]
        
        # Delete the signal
        response = requests.delete(f"{self.base_url}/api/delete-signal/{signal_id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        
        # Verify the signal was deleted
        response = requests.get(f"{self.base_url}/api/signals")
        signals = response.json()
        self.assertEqual(len(signals), 3)  # Back to 3 signals
        eurusd_signals = [s for s in signals if s["symbol"] == "EURUSD"]
        self.assertEqual(len(eurusd_signals), 0)  # No EURUSD signals left
    
    def test_09_update_settings(self):
        """Test updating dashboard settings"""
        new_settings = {
            "history_file": os.path.join(self.temp_dir, "new_history.json"),
            "signals_file": os.path.join(self.temp_dir, "new_signals.json")
        }
        response = requests.post(
            f"{self.base_url}/api/update-settings",
            json=new_settings
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        
        # Create the new files to avoid errors
        shutil.copy(self.history_file, new_settings["history_file"])
        shutil.copy(self.signals_file, new_settings["signals_file"])
        
        # Verify settings were updated by checking that API calls still work
        response = requests.get(f"{self.base_url}/api/trade-history")
        self.assertEqual(response.status_code, 200)
    
    def test_10_mock_execute_trade(self):
        """Test the execute trade API endpoint with mock execution"""
        # For testing, we'll mock the trade execution to avoid actual trading
        # This is done by setting a special test flag in the request
        trade_params = {
            "symbol": "USDJPY",
            "side": "long",
            "quantity": 0.1,
            "entry": 150.00,
            "fib_low": 145.00,
            "fib_high": 155.00,
            "stopLoss": 144.00,
            "takeProfit": 160.00,
            "stealth_level": 1,
            "test_mode": True  # This flag tells the server to mock execution
        }
        response = requests.post(
            f"{self.base_url}/api/execute-trade",
            json=trade_params
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        
        # Verify the trade was added to history
        response = requests.get(f"{self.base_url}/api/trade-history")
        history = response.json()
        usdjpy_trades = [t for t in history if t["symbol"] == "USDJPY"]
        self.assertGreaterEqual(len(usdjpy_trades), 1)
    
    def test_11_mock_execute_signal(self):
        """Test executing a saved signal with mock execution"""
        # First get all signals to find the ID of the one we want to execute
        response = requests.get(f"{self.base_url}/api/signals")
        signals = response.json()
        btc_signal = next(s for s in signals if s["symbol"] == "BTCUSD")
        signal_id = btc_signal["id"]
        
        # Execute the signal with test mode
        response = requests.post(
            f"{self.base_url}/api/execute-signal/{signal_id}",
            json={"test_mode": True}  # This flag tells the server to mock execution
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        
        # Verify a new trade was added to history
        response = requests.get(f"{self.base_url}/api/trade-history")
        history = response.json()
        # Count BTC trades before and after should differ
        self.assertGreaterEqual(len(history), 6)  # At least one more trade


if __name__ == "__main__":
    unittest.main()