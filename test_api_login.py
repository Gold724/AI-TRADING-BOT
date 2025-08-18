#!/usr/bin/env python3
"""
API-based credential validation test for Bulenox
Based on the successful login documented in LOGIN_FIX_SUCCESS.md
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_api_login():
    """Test login using the API endpoint that was documented as working"""
    
    # Get credentials from environment
    username = os.getenv('BULENOX_USERNAME')
    password = os.getenv('BULENOX_PASSWORD')
    
    if not username or not password:
        print("❌ Missing credentials in .env file")
        return False
    
    print(f"🔐 Testing API login for user: {username}")
    
    # Login endpoint from LOGIN_FIX_SUCCESS.md
    login_url = "https://userapi.bulenox.projectx.com/Login"
    
    # Headers from successful login capture
    headers = {
        "content-type": "application/json",
        "accept": "application/json",
        "x-app-type": "px-desktop",
        "x-app-version": "1.20.8",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "referer": "https://bulenox.projectx.com/"
    }
    
    # Login payload (userName not username - this was the key fix)
    payload = {
        "userName": username,
        "password": password
    }
    
    try:
        print("📡 Sending login request...")
        response = requests.post(login_url, headers=headers, json=payload, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                print(f"✅ Login successful!")
                print(f"📋 Response data: {json.dumps(response_data, indent=2)}")
                
                # Check if we got a token
                if 'token' in response_data or 'access_token' in response_data:
                    token = response_data.get('token') or response_data.get('access_token')
                    print(f"🔑 Bearer token received: {token[:50]}...")
                    return True
                else:
                    print("⚠️ Login successful but no token in response")
                    return True
                    
            except json.JSONDecodeError:
                print(f"✅ Login successful (non-JSON response)")
                print(f"📄 Response text: {response.text[:200]}...")
                return True
                
        else:
            print(f"❌ Login failed with status {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_account_info_with_existing_token():
    """Test account info using existing bearer token from trade.sh"""
    
    print("\n🔍 Testing account info with existing token...")
    
    # Read token from trade.sh file
    try:
        with open('trade.sh', 'r') as f:
            content = f.read()
            
        # Extract bearer token
        import re
        token_match = re.search(r'Bearer ([^\s\'"]+)', content)
        if not token_match:
            print("❌ No bearer token found in trade.sh")
            return False
            
        token = token_match.group(1)
        print(f"🔑 Using token: {token[:50]}...")
        
        # Test account info endpoint
        url = "https://userapi.bulenox.projectx.com/Layouts"
        headers = {
            "authorization": f"Bearer {token}",
            "content-type": "application/json",
            "accept": "application/json",
            "x-app-type": "px-desktop",
            "referer": "https://bulenox.projectx.com/"
        }
        
        response = requests.post(url, headers=headers, timeout=30)
        print(f"📊 Account Info Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Account info retrieved successfully!")
            print(f"📋 Response length: {len(response.text)} characters")
            return True
        else:
            print(f"❌ Account info failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing account info: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Bulenox API Credential Test")
    print("=" * 50)
    
    # Test 1: Fresh login
    login_success = test_api_login()
    
    # Test 2: Existing token validation
    token_success = test_account_info_with_existing_token()
    
    print("\n📊 Test Results:")
    print(f"   API Login: {'✅ PASS' if login_success else '❌ FAIL'}")
    print(f"   Token Test: {'✅ PASS' if token_success else '❌ FAIL'}")
    
    if login_success or token_success:
        print("\n🎉 Credentials are working! The bot should be able to authenticate.")
    else:
        print("\n⚠️ Credential issues detected. Check username/password or network connectivity.")