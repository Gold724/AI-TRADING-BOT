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
        print(f"❌ Could not connect to {API_BASE}")
        return False
    except Exception as e:
        print(f"❌ Error checking server: {str(e)}")
        return False

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

def main():
    """Run the login test"""
    print("🤖 AI Trading Sentinel - Login Test")
    print("===================================\n")
    
    # Check if server is running
    if not check_server_running():
        print("\n❌ Cannot proceed with test. Please start the cloud_main.py server first.")
        sys.exit(1)
    
    # Run login test
    session_id = test_login()
    
    if session_id:
        print(f"\n✅ Login test successful! Session ID: {session_id}")
    else:
        print("\n❌ Login test failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()