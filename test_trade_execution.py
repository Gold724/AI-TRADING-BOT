import os
import json
import time
import requests
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

# API endpoint (default to localhost if running locally)
API_BASE = os.getenv('API_BASE', 'http://localhost:5000')

def test_login():
    """Test the login endpoint"""
    print("\n🔑 Testing login endpoint...")
    
    try:
        print(f"Sending login request to {API_BASE}/api/login with timeout=60s...")
        response = requests.post(
            f"{API_BASE}/api/login",
            json={
                "account_id": os.getenv('BULENOX_ACCOUNT_ID', 'BX64883')
            },
            timeout=60  # Increase timeout to 60 seconds as login may take longer
        )
        
        print(f"Status code: {response.status_code}")
        
        try:
            response_json = response.json()
            print(f"Response: {json.dumps(response_json, indent=2)}")
            
            if response.status_code == 200:
                print("✅ Login successful!")
                return response_json.get('session_id')
            else:
                print("❌ Login failed!")
                return None
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON response: {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection error: Could not connect to {API_BASE}")
        print("   Make sure the server is running and the API_BASE is correct.")
        return None
    except requests.exceptions.Timeout:
        print(f"❌ Login request timed out after 60 seconds.")
        print("   The login process may be taking longer than expected.")
        print("   Check the server logs for more information.")
        return None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_trade_execution(session_id=None):
    """Test the trade execution endpoint"""
    print("\n💹 Testing trade execution...")
    
    # Demo trade signal
    signal = {
        "symbol": "EURUSD",
        "side": "buy",
        "quantity": 1,
        "stop_loss": 50,
        "take_profit": 100
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/api/trade",
            json={
                "account_id": os.getenv('BULENOX_ACCOUNT_ID', 'BX64883'),
                "session_id": session_id,
                "signal": signal
            },
            timeout=30  # Trade execution might take longer
        )
        
        print(f"Status code: {response.status_code}")
        
        try:
            response_json = response.json()
            print(f"Response: {json.dumps(response_json, indent=2)}")
            
            if response.status_code == 200:
                print("✅ Trade execution successful!")
                return True
            else:
                print("❌ Trade execution failed!")
                return False
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON response: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection error: Could not connect to {API_BASE}")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timed out. Trade execution may take longer than expected.")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_webhook():
    """Test the webhook endpoint"""
    print("\n🔔 Testing webhook endpoint...")
    
    # Demo trade signal
    signal = {
        "symbol": "GBPUSD",
        "side": "sell",
        "quantity": 1,
        "stop_loss": 30,
        "take_profit": 90
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/api/webhook",
            json={
                "account_id": os.getenv('BULENOX_ACCOUNT_ID', 'BX64883'),
                "signal": signal
            },
            timeout=30  # Webhook processing might take longer
        )
        
        print(f"Status code: {response.status_code}")
        
        try:
            response_json = response.json()
            print(f"Response: {json.dumps(response_json, indent=2)}")
            
            if response.status_code == 200:
                print("✅ Webhook processing successful!")
                return True
            else:
                print("❌ Webhook processing failed!")
                return False
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON response: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection error: Could not connect to {API_BASE}")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timed out. Webhook processing may take longer than expected.")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_sessions():
    """Test the sessions endpoint"""
    print("\n👥 Testing sessions endpoint...")
    
    try:
        response = requests.get(f"{API_BASE}/api/sessions", timeout=10)
        
        print(f"Status code: {response.status_code}")
        
        try:
            response_json = response.json()
            print(f"Response: {json.dumps(response_json, indent=2)}")
            
            if response.status_code == 200:
                print(f"✅ Found {response_json.get('count', 0)} active sessions")
                return True
            else:
                print("❌ Failed to get sessions!")
                return False
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON response: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection error: Could not connect to {API_BASE}")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_status():
    """Test the status endpoint"""
    print("\n📊 Testing status endpoint...")
    
    try:
        response = requests.get(f"{API_BASE}/api/status", timeout=10)
        
        print(f"Status code: {response.status_code}")
        
        try:
            response_json = response.json()
            print(f"Response: {json.dumps(response_json, indent=2)}")
            
            if response.status_code == 200:
                print("✅ Status check successful!")
                return True
            else:
                print("❌ Status check failed!")
                return False
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON response: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection error: Could not connect to {API_BASE}")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def check_server_running():
    """Check if the API server is running"""
    print(f"🔍 Checking if API server is running at {API_BASE}...")
    
    try:
        response = requests.get(f"{API_BASE}/api/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ API server is running at {API_BASE}")
            return True
        else:
            print(f"❌ API server returned status code {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection error: Could not connect to {API_BASE}")
        print("   Make sure the server is running and the API_BASE is correct.")
        return False
    except Exception as e:
        print(f"❌ Error checking server: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🤖 AI Trading Sentinel - Test Suite")
    print("=====================================\n")
    
    # Check if server is running
    if not check_server_running():
        print("\n❌ Cannot proceed with tests. Please start the cloud_main.py server first.")
        sys.exit(1)
    
    # Login and get session ID
    session_id = test_login()
    
    if not session_id:
        print("\n❌ Login test failed. Cannot proceed with other tests.")
        sys.exit(1)
    
    # Run other tests and collect results
    results = {
        "Trade Execution": test_trade_execution(session_id),
        "Webhook": test_webhook(),
        "Sessions": test_sessions(),
        "Status": test_status()
    }
    
    # Print summary
    print("\n📋 Test Summary:")
    print("=====================================")
    all_passed = True
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        if not result:
            all_passed = False
        print(f"{test_name}: {status}")
    
    if all_passed:
        print("\n✅ All tests completed successfully!")
    else:
        print("\n⚠️ Some tests failed. Please check the logs above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()