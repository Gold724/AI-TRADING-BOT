#!/usr/bin/env python3
"""
Test script for QuantConnect integration with AI Trading Sentinel

This script allows you to test the QuantConnect integration locally
before deploying to Ubuntu with Docker.
"""

import os
import sys
import json
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our QuantConnect integration
try:
    from quantconnect_integration import QuantConnectIntegration, QC_API_KEY, QC_PROJECT_ID
    from strategies.quantconnect_strategy import SentinelQuantConnectStrategy, create_algorithm
except ImportError as e:
    print(f"Error importing QuantConnect modules: {e}")
    print("Make sure you've created the quantconnect_integration.py file")
    sys.exit(1)

def test_local_algorithm():
    """Test the QuantConnect algorithm locally"""
    print("\n===== Testing Local Algorithm =====\n")
    try:
        # Create algorithm instance
        algorithm = create_algorithm()
        print(f"Created algorithm instance: {algorithm.__class__.__name__}")
        
        # Initialize the algorithm
        algorithm.Initialize()
        print("Algorithm initialized successfully")
        
        # Generate signals
        if hasattr(algorithm, 'GenerateSignals'):
            signals = algorithm.GenerateSignals()
            print(f"Generated signals: {signals}")
        else:
            print("Algorithm does not have GenerateSignals method")
            
        print("Local algorithm test completed successfully")
        return True
    except Exception as e:
        print(f"Error testing local algorithm: {e}")
        return False

def test_quantconnect_api():
    """Test the QuantConnect API integration"""
    print("\n===== Testing QuantConnect API Integration =====\n")
    
    # Check if API key and project ID are set
    if not QC_API_KEY or not QC_PROJECT_ID:
        print("QuantConnect API key or project ID not set in environment variables")
        print("Please set QC_API_KEY and QC_PROJECT_ID in your .env file")
        return False
    
    try:
        # Initialize QuantConnect integration
        qc = QuantConnectIntegration()
        print(f"Initialized QuantConnect integration with project ID: {QC_PROJECT_ID}")
        
        # Get project details
        project = qc.get_project()
        if project:
            print(f"Project name: {project.get('name')}")
            print(f"Created: {project.get('created')}")
            print(f"Language: {project.get('language')}")
        else:
            print("Failed to get project details")
            return False
        
        # List backtests
        backtests = qc.list_backtests()
        if backtests:
            print(f"Found {len(backtests)} backtests")
            for i, backtest in enumerate(backtests[:3]):  # Show first 3
                print(f"  {i+1}. {backtest.get('name')} - {backtest.get('created')}")
        else:
            print("No backtests found or failed to retrieve backtests")
        
        # Check live algorithm status
        live_status = qc.check_live_algorithm_status()
        print(f"Live algorithm status: {live_status}")
        
        print("QuantConnect API integration test completed successfully")
        return True
    except Exception as e:
        print(f"Error testing QuantConnect API integration: {e}")
        return False

def main():
    """Main test function"""
    print("\n===== AI Trading Sentinel - QuantConnect Integration Test =====\n")
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test local algorithm
    local_test_success = test_local_algorithm()
    
    # Test QuantConnect API
    api_test_success = test_quantconnect_api()
    
    # Print summary
    print("\n===== Test Summary =====\n")
    print(f"Local algorithm test: {'SUCCESS' if local_test_success else 'FAILED'}")
    print(f"QuantConnect API test: {'SUCCESS' if api_test_success else 'FAILED'}")
    
    if local_test_success and api_test_success:
        print("\nAll tests passed! The QuantConnect integration is ready for deployment.")
    else:
        print("\nSome tests failed. Please fix the issues before deploying.")

if __name__ == "__main__":
    main()