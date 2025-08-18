#!/usr/bin/env python3
"""
Simple Email Configuration Test for AI Trading Sentinel
Windows-compatible version without Unicode characters
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime

def load_env_config():
    """Load email configuration from .env file"""
    config = {}
    env_file = Path('.env')
    
    if not env_file.exists():
        print("ERROR: .env file not found!")
        return None
    
    try:
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
        return config
    except Exception as e:
        print(f"ERROR reading .env file: {e}")
        return None

def validate_email_config(config):
    """Validate email configuration"""
    print("Validating Email Configuration...")
    print("-" * 40)
    
    issues = []
    
    # Check required fields
    required_fields = {
        'EMAIL_NOTIFICATIONS': 'true',
        'EMAIL_USERNAME': None,
        'EMAIL_PASSWORD': None,
        'SMTP_SERVER': None,
        'SMTP_PORT': None
    }
    
    for field, expected_value in required_fields.items():
        if field not in config:
            issues.append(f"Missing {field}")
        elif expected_value and config[field].lower() != expected_value:
            issues.append(f"{field} should be '{expected_value}', got '{config[field]}'")
        elif field == 'EMAIL_PASSWORD' and len(config[field]) != 16:
            issues.append(f"EMAIL_PASSWORD should be 16 characters (Gmail App Password), got {len(config[field])} characters")
        elif field == 'EMAIL_PASSWORD' and 'your-16-char-app-password' in config[field]:
            issues.append("EMAIL_PASSWORD still contains placeholder text")
    
    # Print validation results
    for field in required_fields:
        if field in config:
            if field == 'EMAIL_PASSWORD':
                masked = '*' * len(config[field])
                print(f"{field}: {masked} ({len(config[field])} chars)")
            else:
                print(f"{field}: {config[field]}")
        else:
            print(f"{field}: MISSING")
    
    if issues:
        print("\nISSUES FOUND:")
        for i, issue in enumerate(issues, 1):
            print(f"{i}. {issue}")
        return False
    else:
        print("\nSUCCESS: All email settings are valid!")
        return True

def test_smtp_connection(config):
    """Test SMTP server connection"""
    print("\nTesting SMTP Connection...")
    print("-" * 30)
    
    try:
        smtp_server = config.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(config.get('SMTP_PORT', 587))
        username = config.get('EMAIL_USERNAME')
        password = config.get('EMAIL_PASSWORD')
        
        print(f"Connecting to {smtp_server}:{smtp_port}...")
        
        # Create SMTP connection
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        
        print("Authenticating...")
        server.login(username, password)
        
        print("SUCCESS: SMTP connection and authentication successful!")
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"ERROR: Authentication failed - {e}")
        print("Check your EMAIL_USERNAME and EMAIL_PASSWORD")
        if 'gmail.com' in smtp_server:
            print("For Gmail, make sure you're using an App Password, not your regular password")
        return False
    except Exception as e:
        print(f"ERROR: Connection failed - {e}")
        return False

def send_test_email(config):
    """Send a test email"""
    print("\nSending Test Email...")
    print("-" * 25)
    
    try:
        smtp_server = config.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(config.get('SMTP_PORT', 587))
        username = config.get('EMAIL_USERNAME')
        password = config.get('EMAIL_PASSWORD')
        to_email = config.get('EMAIL_TO', username)
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = username
        msg['To'] = to_email
        msg['Subject'] = "AI Trading Sentinel - Email Test"
        
        body = f"""
Hello!

This is a test email from your AI Trading Sentinel bot.

Configuration Details:
- SMTP Server: {smtp_server}:{smtp_port}
- From: {username}
- To: {to_email}
- Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

If you received this email, your email notifications are working correctly!

Best regards,
AI Trading Sentinel
"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(username, password)
        
        text = msg.as_string()
        server.sendmail(username, to_email, text)
        server.quit()
        
        print(f"SUCCESS: Test email sent to {to_email}")
        print("Check your inbox for the test message!")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to send test email - {e}")
        return False

def main():
    """Main test function"""
    print("AI Trading Sentinel - Email Configuration Test")
    print("=" * 50)
    
    # Load configuration
    config = load_env_config()
    if not config:
        return False
    
    # Check if email notifications are enabled
    if config.get('EMAIL_NOTIFICATIONS', '').lower() != 'true':
        print("Email notifications are disabled (EMAIL_NOTIFICATIONS != true)")
        print("To enable, set EMAIL_NOTIFICATIONS=true in your .env file")
        return False
    
    # Validate configuration
    if not validate_email_config(config):
        print("\nFIX REQUIRED: Please update your .env file and try again.")
        print("Run: python fix_email_config.py")
        return False
    
    # Test SMTP connection
    if not test_smtp_connection(config):
        return False
    
    # Send test email
    if not send_test_email(config):
        return False
    
    print("\n" + "=" * 50)
    print("SUCCESS: All email tests passed!")
    print("Your AI Trading Sentinel is ready to send notifications.")
    return True

if __name__ == '__main__':
    try:
        success = main()
        exit_code = 0 if success else 1
        exit(exit_code)
    except KeyboardInterrupt:
        print("\nTest cancelled by user.")
        exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        exit(1)