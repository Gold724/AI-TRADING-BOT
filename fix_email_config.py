#!/usr/bin/env python3
"""
Quick Email Configuration Fix for AI Trading Sentinel
This script helps fix the .env file with proper email settings.
"""

import os
import re
from pathlib import Path

def fix_email_config():
    """Fix the email configuration in .env file"""
    
    print("AI Trading Sentinel - Email Configuration Fix")
    print("=" * 50)
    
    # Find .env file
    env_file = Path('.env')
    if not env_file.exists():
        print("ERROR: .env file not found!")
        return False
    
    # Read current .env content
    with open(env_file, 'r') as f:
        content = f.read()
    
    print("Current Email Configuration:")
    print("-" * 30)
    
    # Extract current email settings
    email_notifications = re.search(r'EMAIL_NOTIFICATIONS=(.+)', content)
    email_username = re.search(r'EMAIL_USERNAME=(.+)', content)
    email_password = re.search(r'EMAIL_PASSWORD=(.+)', content)
    
    if email_notifications:
        print(f"EMAIL_NOTIFICATIONS: {email_notifications.group(1)}")
    if email_username:
        print(f"EMAIL_USERNAME: {email_username.group(1)}")
    if email_password:
        print(f"EMAIL_PASSWORD: {email_password.group(1)}")
    
    print("\nIssues Found:")
    issues = []
    
    # Check EMAIL_NOTIFICATIONS
    if not email_notifications or email_notifications.group(1).strip().lower() != 'true':
        issues.append("EMAIL_NOTIFICATIONS is not set to 'true'")
    
    # Check EMAIL_PASSWORD length
    if not email_password or len(email_password.group(1).strip()) != 16:
        issues.append("EMAIL_PASSWORD is not 16 characters (Gmail App Password required)")
    
    # Check if using placeholder
    if email_password and 'your-16-char-app-password' in email_password.group(1):
        issues.append("EMAIL_PASSWORD still contains placeholder text")
    
    for i, issue in enumerate(issues, 1):
        print(f"{i}. {issue}")
    
    if not issues:
        print("SUCCESS: No issues found! Email configuration looks good.")
        return True
    
    print("\nQuick Fix Options:")
    print("1. Generate Gmail App Password (Recommended)")
    print("2. Use Outlook/Hotmail (Alternative)")
    print("3. Disable email notifications")
    
    choice = input("\nChoose option (1-3): ").strip()
    
    if choice == '1':
        print("\nGmail App Password Setup:")
        print("1. Go to: https://myaccount.google.com/apppasswords")
        print("2. Sign in to your Gmail account")
        print("3. Click 'Generate' and select 'Other (Custom name)'")
        print("4. Enter 'AI Trading Bot' as the name")
        print("5. Copy the 16-character password (no spaces)")
        
        app_password = input("\nEnter your 16-character App Password: ").strip().replace(' ', '')
        
        if len(app_password) == 16:
            # Update .env file
            content = re.sub(r'EMAIL_PASSWORD=.+', f'EMAIL_PASSWORD={app_password}', content)
            content = re.sub(r'EMAIL_NOTIFICATIONS=.+', 'EMAIL_NOTIFICATIONS=true', content)
            
            with open(env_file, 'w') as f:
                f.write(content)
            
            print("SUCCESS: Email configuration updated successfully!")
            return True
        else:
            print("ERROR: Invalid App Password length. Must be exactly 16 characters.")
            return False
    
    elif choice == '2':
        print("\nOutlook Setup:")
        email = input("Enter your Outlook/Hotmail email: ").strip()
        password = input("Enter your Outlook password: ").strip()
        
        # Update for Outlook
        content = re.sub(r'SMTP_SERVER=.+', 'SMTP_SERVER=smtp-mail.outlook.com', content)
        content = re.sub(r'SMTP_PORT=.+', 'SMTP_PORT=587', content)
        content = re.sub(r'EMAIL_USERNAME=.+', f'EMAIL_USERNAME={email}', content)
        content = re.sub(r'EMAIL_PASSWORD=.+', f'EMAIL_PASSWORD={password}', content)
        content = re.sub(r'EMAIL_NOTIFICATIONS=.+', 'EMAIL_NOTIFICATIONS=true', content)
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        print("SUCCESS: Outlook configuration updated successfully!")
        return True
    
    elif choice == '3':
        # Disable email notifications
        content = re.sub(r'EMAIL_NOTIFICATIONS=.+', 'EMAIL_NOTIFICATIONS=false', content)
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        print("SUCCESS: Email notifications disabled.")
        return True
    
    else:
        print("ERROR: Invalid choice.")
        return False

def test_email_after_fix():
    """Test email configuration after fix"""
    print("\nTesting Email Configuration...")
    
    try:
        # Import and run the email test
        import subprocess
        result = subprocess.run(['python', 'test_email_config_simple.py'], 
                              capture_output=True, text=True, cwd='.')
        
        print("Test Output:")
        print(result.stdout)
        
        if result.stderr:
            print("Errors:")
            print(result.stderr)
        
        return result.returncode == 0
    
    except Exception as e:
        print(f"ERROR running test: {e}")
        return False

if __name__ == '__main__':
    try:
        # Change to script directory
        os.chdir(Path(__file__).parent)
        
        success = fix_email_config()
        
        if success:
            print("\n" + "=" * 50)
            # Create simple test first
            print("Creating simple email test...")
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")