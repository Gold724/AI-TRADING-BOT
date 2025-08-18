# Gmail App Password Setup Guide for AI Trading Sentinel

## Overview
The AI Trading Sentinel uses Gmail's SMTP server to send email notifications for trading alerts, system status, and critical events. For security, Gmail requires an "App Password" instead of your regular Gmail password.

## Prerequisites
- Gmail account (edufyinc@gmail.com or your trading email)
- 2-Factor Authentication (2FA) must be enabled on your Gmail account

## Step-by-Step Guide

### Step 1: Enable 2-Factor Authentication (if not already enabled)

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Sign in with your Gmail credentials
3. Under "Signing in to Google", click on "2-Step Verification"
4. Follow the setup process to enable 2FA using:
   - Phone number (SMS or call)
   - Google Authenticator app
   - Backup codes

### Step 2: Generate App Password

1. **Access App Passwords:**
   - Go to [Google Account Security](https://myaccount.google.com/security)
   - Click on "2-Step Verification"
   - Scroll down and click on "App passwords"

2. **Create New App Password:**
   - Select "Mail" from the "Select app" dropdown
   - Select "Other (Custom name)" from the "Select device" dropdown
   - Enter: `AI Trading Sentinel Bot`
   - Click "Generate"

3. **Copy the Generated Password:**
   - Google will display a 16-character password (e.g., `abcd efgh ijkl mnop`)
   - **IMPORTANT:** Copy this password immediately - you won't see it again!
   - Remove spaces when copying (e.g., `abcdefghijklmnop`)

### Step 3: Configure .env File

Update your `.env` file with the App Password:

```bash
# Email Notifications
EMAIL_NOTIFICATIONS=true
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=edufyinc@gmail.com
EMAIL_PASSWORD=paxq vizg qjzw ujsm  # Your 16-character App Password (no spaces)
EMAIL_TO=edufyinc@gmail.com
```

### Step 4: Test Email Configuration

Create a test script to verify email functionality:

```python
# test_email.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

def test_email():
    try:
        # Email configuration
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = int(os.getenv('SMTP_PORT'))
        email_username = os.getenv('EMAIL_USERNAME')
        email_password = os.getenv('EMAIL_PASSWORD')
        email_to = os.getenv('EMAIL_TO')
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = email_username
        msg['To'] = email_to
        msg['Subject'] = "AI Trading Sentinel - Email Test"
        
        body = "This is a test email from your AI Trading Sentinel bot. Email notifications are working correctly!"
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email_username, email_password)
        text = msg.as_string()
        server.sendmail(email_username, email_to, text)
        server.quit()
        
        print("✅ Email test successful! Check your inbox.")
        return True
        
    except Exception as e:
        print(f"❌ Email test failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_email()
```

## Security Best Practices

### 1. App Password Security
- **Never share** your App Password
- **Store securely** in `.env` file (never commit to Git)
- **Regenerate** if compromised
- **Use unique** App Passwords for different applications

### 2. Email Account Security
- Use a **dedicated Gmail account** for trading notifications
- Enable **account recovery** options
- Monitor **security activity** regularly
- Consider using **G Suite/Workspace** for business use

### 3. Environment Variables
```bash
# Secure .env configuration
EMAIL_USERNAME=your-trading-email@gmail.com
EMAIL_PASSWORD=your-16-char-app-password
EMAIL_TO=your-alerts-email@domain.com

# Optional: Multiple recipients
EMAIL_TO=alert1@domain.com,alert2@domain.com,alert3@domain.com
```

## Troubleshooting

### Common Issues

1. **"Authentication failed" error:**
   - Verify 2FA is enabled
   - Regenerate App Password
   - Check username/password in `.env`

2. **"Less secure app access" error:**
   - This is outdated - use App Passwords instead
   - Never enable "Less secure app access"

3. **"SMTP connection failed":**
   - Check internet connection
   - Verify SMTP settings: `smtp.gmail.com:587`
   - Ensure firewall allows SMTP traffic

4. **Email not received:**
   - Check spam/junk folder
   - Verify recipient email address
   - Test with different email provider

### VNC Environment Testing

If using VNC deployment, test email in the VNC session:

```bash
# In VNC terminal
cd /opt/ai-trading-sentinel
python3 test_email.py
```

## Email Notification Types

The AI Trading Sentinel sends these email types:

### 1. Critical Alerts
- System crashes or failures
- Login authentication errors
- Risk management triggers
- Emergency stop conditions

### 2. Trading Events
- Successful trade executions
- Failed trade attempts
- Position updates
- Profit/loss summaries

### 3. System Status
- Daily health reports
- Performance metrics
- Configuration changes
- Maintenance notifications

### 4. Risk Management
- Drawdown warnings
- Volatility alerts
- Spread threshold breaches
- Account balance changes

## Alternative Email Providers

If Gmail doesn't work, consider these alternatives:

### Outlook/Hotmail
```bash
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
```

### Yahoo Mail
```bash
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
```

### Custom SMTP (Recommended for Production)
```bash
SMTP_SERVER=mail.yourdomain.com
SMTP_PORT=587
```

## Quick Reference

### Generate App Password (Quick Steps)
1. [Google Account Security](https://myaccount.google.com/security) → 2-Step Verification → App passwords
2. Select "Mail" → "Other (Custom name)" → "AI Trading Sentinel Bot"
3. Copy 16-character password (remove spaces)
4. Update `.env` file: `EMAIL_PASSWORD=your-app-password`
5. Test with `python3 test_email.py`

### Emergency Contact
- **VNC Access:** IP 5.189.145.177:63162
- **Support:** Check logs in `/opt/ai-trading-sentinel/logs/`
- **Backup:** Use Slack notifications if email fails

---

**⚠️ Security Reminder:** Never commit your `.env` file to Git. Always use App Passwords, never your regular Gmail password.

**✅ Success Indicator:** You should receive a test email within 30 seconds of running the test script.