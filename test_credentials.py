#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText

load_dotenv()

def test_bulenox_credentials():
    """Test Bulenox login credentials"""
    username = os.getenv('BULENOX_USERNAME')
    password = os.getenv('BULENOX_PASSWORD')
    url = os.getenv('BULENOX_URL')
    
    if not all([username, password, url]):
        print("❌ Bulenox credentials missing")
        return False
    
    print(f"✅ Bulenox credentials configured for: {username}")
    return True

def test_slack_webhook():
    """Test Slack webhook"""
    webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    
    if not webhook_url:
        print("❌ Slack webhook URL missing")
        return False
    
    try:
        payload = {
            "text": "🧪 AI Trading Sentinel - Credential Test",
            "username": "TradingBot",
            "icon_emoji": ":white_check_mark:"
        }
        response = requests.post(webhook_url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print("✅ Slack webhook working")
            return True
        else:
            print(f"❌ Slack webhook failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Slack webhook error: {e}")
        return False

def test_email_credentials():
    """Test email SMTP credentials"""
    if os.getenv('EMAIL_ALERTS') != 'true':
        print("📧 Email alerts disabled")
        return True
    
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    username = os.getenv('EMAIL_USERNAME')
    password = os.getenv('EMAIL_PASSWORD')
    
    if not all([smtp_server, username, password]):
        print("❌ Email credentials missing")
        return False
    
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(username, password)
        server.quit()
        print("✅ Email SMTP credentials working")
        return True
    except Exception as e:
        print(f"❌ Email SMTP error: {e}")
        return False

def test_api_security():
    """Test API security configuration"""
    jwt_secret = os.getenv('JWT_SECRET_KEY')
    api_key = os.getenv('API_KEY')
    
    if not jwt_secret or len(jwt_secret) < 32:
        print("❌ JWT secret key missing or too short")
        return False
    
    if not api_key or len(api_key) < 16:
        print("❌ API key missing or too short")
        return False
    
    print("✅ API security tokens configured")
    return True

if __name__ == "__main__":
    print("🔐 Testing AI Trading Sentinel Credentials")
    print("=" * 50)
    
    tests = [
        test_bulenox_credentials,
        test_slack_webhook,
        test_email_credentials,
        test_api_security
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All credentials configured successfully!")
        exit(0)
    else:
        print("⚠️  Some credentials need attention")
        exit(1)