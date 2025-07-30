#!/usr/bin/env python
"""
Test script for the Fibonacci Strategy Dashboard

This script tests the basic functionality of the Fibonacci Strategy Dashboard
by starting the server, making API requests, and verifying responses.
"""

import os
import sys
import json
import time
import unittest
import threading
import requests
from urllib.parse import urljoin

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.fibonacci_strategy_dashboard import app, start_server, stop_server

class TestFibonacciDashboard(unittest.TestCase):
    """Test case for the Fibonacci Strategy Dashboard"""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test environment"""
        # Start the server in a separate thread
        cls.host = "127.0.0.1"
        cls.port = 5002  # Use a different port for testing
        cls.base_url = f"http://{cls.host}:{cls.port}"
        
        # Start server without opening browser
        threading.Thread(target=start_server, args=(cls.host, cls.port, False)).start()
        
        # Wait for server to start
        time.sleep(2)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up the test environment"""
        # Stop the server
        stop_server()
    
    def test_server_running(self):
        """Test that the server is running"""
        response = requests.get(self.base_url)
        self.assertEqual(response.status_code, 200)
    
    def test_api_endpoints(self):
        """Test the API endpoints"""
        # Test active trades endpoint
        response = requests.get(urljoin(self.base_url, "/api/active-trades"))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)
        
        # Test trade history endpoint
        response = requests.get(urljoin(self.base_url, "/api/trade-history"))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)
        
        # Test signals endpoint
        response = requests.get(urljoin(self.base_url, "/api/signals"))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)
        
        # Test recent activity endpoint
        response = requests.get(urljoin(self.base_url, "/api/recent-activity"))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)
        
        # Test metrics endpoint
        response = requests.get(urljoin(self.base_url, "/api/metrics"))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
    
    def test_add_signal(self):
        """Test adding a signal"""
        # Create a test signal
        test_signal = {
            "symbol": "EURUSD",
            "side": "buy",
            "quantity": 1.0,
            "entry": 1.1000,
            "fib_low": 1.0900,
            "fib_high": 1.1100,
            "description": "Test signal",
            "stealth_level": 1
        }
        
        # Add the signal
        response = requests.post(
            urljoin(self.base_url, "/api/add-signal"),
            json=test_signal
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get("success"))
        
        # Verify the signal was added
        response = requests.get(urljoin(self.base_url, "/api/signals"))
        signals = response.json()
        
        # Find our test signal
        found = False
        for signal in signals:
            if (signal.get("symbol") == test_signal["symbol"] and
                signal.get("entry") == test_signal["entry"] and
                signal.get("description") == test_signal["description"]):
                found = True
                break
        
        self.assertTrue(found, "Test signal was not found in the signals list")

def main():
    """Run the tests"""
    unittest.main()

if __name__ == "__main__":
    main()