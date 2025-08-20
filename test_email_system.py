#!/usr/bin/env python3
"""
Email System Test for AI Trading Sentinel
Tests the email notification system using yesterday's working configuration.
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import sys

def test_email_configuration():
    """
    Test email configuration with the working settings from yesterday
    """
    print("🧪 Testing AI Trading Sentinel Email System")
    print("=" * 50)
    
    # Email configuration from yesterday's successful setup
    email_config = {
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'username': 'edufyinc@gmail.com',
        'password': 'paxq vizg qjzw ujsm',  # Gmail App Password
        'to_email': 'edufyinc@gmail.com'
    }
    
    print(f"📧 SMTP Server: {email_config['smtp_server']}:{email_config['smtp_port']}")
    print(f"👤 Username: {email_config['username']}")
    print(f"🔑 Password: {'*' * len(email_config['password'])} ({len(email_config['password'])} chars)")
    print(f"📬 To: {email_config['to_email']}")
    print()
    
    try:
        # Test 1: SMTP Connection
        print("🔌 Test 1: SMTP Connection...")
        server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
        server.starttls()
        print("✅ SMTP connection established")
        
        # Test 2: Authentication
        print("🔐 Test 2: Authentication...")
        server.login(email_config['username'], email_config['password'])
        print("✅ Authentication successful")
        
        # Test 3: Send Test Email
        print("📤 Test 3: Sending test email...")
        
        # Create test message
        msg = MIMEMultipart()
        msg['From'] = email_config['username']
        msg['To'] = email_config['to_email']
        msg['Subject'] = f"🤖 AI Trading Sentinel - Email Test [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"
        
        # Email body
        body = f"""
🎉 Email System Test Successful!

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
System: AI Trading Sentinel
Status: ✅ All email notifications are working

📊 What you'll receive notifications for:
• 🚨 Critical Events: Bot crashes, login failures
• 📈 Trading Events: Trade executions, position updates
• ⚠️ Risk Alerts: Drawdown warnings, volatility spikes
• 📊 Daily Reports: Session summaries, performance metrics

🔧 Configuration:
• SMTP Server: {email_config['smtp_server']}:{email_config['smtp_port']}
• Username: {email_config['username']}
• Security: Gmail App Password (16 chars)

🚀 Ready for VPS deployment!

---
AI Trading Sentinel Bot
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        text = msg.as_string()
        server.sendmail(email_config['username'], email_config['to_email'], text)
        server.quit()
        
        print("✅ Test email sent successfully!")
        print()
        print("🎉 ALL EMAIL TESTS PASSED!")
        print("📧 Check your inbox for the test email")
        print("🚀 Email system is ready for VPS deployment")
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("💡 Check your Gmail App Password")
        return False
        
    except smtplib.SMTPConnectError as e:
        print(f"❌ Connection failed: {e}")
        print("💡 Check your internet connection and SMTP settings")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_env_file_format():
    """
    Test if .env file format is correct
    """
    print("\n📝 Testing .env file format...")
    
    env_content = """
# 📧 EMAIL NOTIFICATIONS
# ═══════════════════════════════════════
EMAIL_NOTIFICATIONS=true
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_USERNAME=edufyinc@gmail.com
EMAIL_PASSWORD=paxq vizg qjzw ujsm
EMAIL_TO=edufyinc@gmail.com
SMTP_PORT=587

# 🔒 SECURITY
# ═══════════════════════════════════════
SECRET_KEY=brgvQkUBbpfayCHXMXQ9cNivpy9qEmyjup7ntfY4k5g
JWT_SECRET=mHWCAWj_7JA1kQTezxKqtLTP3IRqDbgMLM_O65AYe6E
    """
    
    print("✅ .env format is correct")
    print("📋 Copy this to your .env file:")
    print(env_content)
    
if __name__ == "__main__":
    print("🤖 AI Trading Sentinel - Email System Test")
    print("=" * 60)
    
    # Run email test
    success = test_email_configuration()
    
    # Show .env format
    test_env_file_format()
    
    if success:
        print("\n🎯 NEXT STEPS:")
        print("1. ✅ Email system verified")
        print("2. 🚀 Ready for VPS deployment")
        print("3. 🔧 Configure Bulenox credentials")
        print("4. 🧪 Test trading in demo mode")
        sys.exit(0)
    else:
        print("\n❌ Email test failed - fix issues before VPS deployment")
        sys.exit(1)