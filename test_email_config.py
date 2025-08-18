#!/usr/bin/env python3
"""
Email Configuration Test Script for AI Trading Sentinel
Tests Gmail SMTP connection with App Password
"""

import smtplib
import os
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

try:
    from dotenv import load_dotenv
except ImportError:
    print("❌ python-dotenv not installed. Run: pip install python-dotenv")
    sys.exit(1)

def load_email_config():
    """Load email configuration from .env file"""
    load_dotenv()
    
    config = {
        'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
        'smtp_port': int(os.getenv('SMTP_PORT', 587)),
        'email_username': os.getenv('EMAIL_USERNAME'),
        'email_password': os.getenv('EMAIL_PASSWORD'),
        'email_to': os.getenv('EMAIL_TO'),
        'notifications_enabled': os.getenv('EMAIL_NOTIFICATIONS', 'false').lower() == 'true'
    }
    
    return config

def validate_config(config):
    """Validate email configuration"""
    errors = []
    
    if not config['notifications_enabled']:
        errors.append("EMAIL_NOTIFICATIONS is not set to 'true'")
    
    if not config['email_username']:
        errors.append("EMAIL_USERNAME is not set")
    
    if not config['email_password']:
        errors.append("EMAIL_PASSWORD is not set (App Password required)")
    
    if not config['email_to']:
        errors.append("EMAIL_TO is not set")
    
    if config['email_password'] and len(config['email_password']) != 16:
        errors.append("EMAIL_PASSWORD should be 16 characters (Gmail App Password)")
    
    return errors

def test_smtp_connection(config):
    """Test SMTP server connection"""
    try:
        print(f"🔗 Connecting to {config['smtp_server']}:{config['smtp_port']}...")
        server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
        server.starttls()
        print("✅ SMTP connection established")
        
        print(f"🔐 Authenticating as {config['email_username']}...")
        server.login(config['email_username'], config['email_password'])
        print("✅ SMTP authentication successful")
        
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("💡 Check your Gmail App Password. Regular passwords don't work!")
        return False
    except smtplib.SMTPConnectError as e:
        print(f"❌ Connection failed: {e}")
        print("💡 Check internet connection and SMTP settings")
        return False
    except Exception as e:
        print(f"❌ SMTP test failed: {e}")
        return False

def send_test_email(config):
    """Send a test email"""
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = config['email_username']
        msg['To'] = config['email_to']
        msg['Subject'] = "🤖 AI Trading Sentinel - Email Test Successful"
        
        # Email body
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        body = f"""
🎉 Congratulations! Your AI Trading Sentinel email notifications are working correctly.

📧 Test Details:
• From: {config['email_username']}
• To: {config['email_to']}
• SMTP Server: {config['smtp_server']}:{config['smtp_port']}
• Timestamp: {timestamp}

🔔 You will now receive notifications for:
• Critical system alerts
• Trading execution updates
• Risk management warnings
• Daily performance reports

🛡️ Security Note: This email was sent using a secure Gmail App Password.

---
AI Trading Sentinel - Automated Email Test
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        print(f"📧 Sending test email to {config['email_to']}...")
        server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
        server.starttls()
        server.login(config['email_username'], config['email_password'])
        
        text = msg.as_string()
        server.sendmail(config['email_username'], config['email_to'], text)
        server.quit()
        
        print("✅ Test email sent successfully!")
        print(f"📬 Check your inbox: {config['email_to']}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send test email: {e}")
        return False

def main():
    """Main test function"""
    print("🤖 AI Trading Sentinel - Email Configuration Test")
    print("=" * 50)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("💡 Create .env file with email configuration first")
        print("📖 See GMAIL_APP_PASSWORD_GUIDE.md for instructions")
        return False
    
    # Load configuration
    print("📁 Loading email configuration from .env...")
    config = load_email_config()
    
    # Validate configuration
    print("🔍 Validating configuration...")
    errors = validate_config(config)
    
    if errors:
        print("❌ Configuration errors found:")
        for error in errors:
            print(f"   • {error}")
        print("\n💡 Fix these issues in your .env file and try again")
        return False
    
    print("✅ Configuration validation passed")
    
    # Test SMTP connection
    print("\n🔗 Testing SMTP connection...")
    if not test_smtp_connection(config):
        return False
    
    # Send test email
    print("\n📧 Sending test email...")
    if not send_test_email(config):
        return False
    
    print("\n🎉 All tests passed! Email notifications are ready.")
    print("\n📋 Next Steps:")
    print("   1. Check your email inbox for the test message")
    print("   2. Start your AI Trading Sentinel bot")
    print("   3. Monitor email alerts during trading")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)