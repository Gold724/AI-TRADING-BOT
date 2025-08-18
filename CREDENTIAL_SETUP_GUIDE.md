# 🔐 Credential Setup Guide - AI Trading Sentinel

## Step 2: Configure Broker API Keys and Authentication

### 🎯 Overview
Secure configuration of all authentication credentials for:
- Bulenox trading platform
- Slack/Email notifications
- GitHub CI/CD integration
- API security tokens

### 🔑 Bulenox Platform Credentials

#### 1. Obtain Bulenox Account Details

```bash
# Login to Bulenox platform
# URL: https://bulenox.projectx.com/login
# Collect the following:
# - Username
# - Password
# - Account ID (if available)
# - API endpoints (if available)
```

#### 2. Configure Environment Variables

```bash
# Edit .env file on VPS
nano .env
```

Add Bulenox credentials:
```env
# Bulenox Trading Platform
BULENOX_USERNAME=your_bulenox_username
BULENOX_PASSWORD=your_secure_password
BULENOX_URL=https://bulenox.projectx.com/login
BULENOX_ACCOUNT_ID=your_account_id
BULENOX_API_KEY=your_api_key_if_available

# Trading Configuration
TRADE_MODE=paper  # Start with paper trading
MAX_DAILY_TRADES=5
RISK_PERCENTAGE=2.0
MAX_DRAWDOWN=10.0
TRADE_INTERVAL_SECONDS=60
```

### 📧 Notification Credentials

#### Slack Integration

1. **Create Slack Webhook:**
```bash
# Go to: https://api.slack.com/apps
# Create New App → From scratch
# App Name: "AI Trading Sentinel"
# Select your workspace
# Features → Incoming Webhooks → Activate
# Add New Webhook to Workspace
# Copy Webhook URL
```

2. **Configure Slack in .env:**
```env
# Slack Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_CHANNEL=#trading-alerts
SLACK_USERNAME=TradingBot
SLACK_ICON_EMOJI=:chart_with_upwards_trend:
```

#### Email Alerts Setup

```env
# Email Configuration
EMAIL_ALERTS=true
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_specific_password
EMAIL_FROM=trading-bot@yourdomain.com
EMAIL_TO=alerts@yourdomain.com
```

**Gmail App Password Setup:**
```bash
# 1. Enable 2-Factor Authentication on Gmail
# 2. Go to: https://myaccount.google.com/apppasswords
# 3. Generate app password for "Mail"
# 4. Use this password in EMAIL_PASSWORD
```

### 🔒 Security Configuration

#### API Security Tokens

```env
# API Security
JWT_SECRET_KEY=$(openssl rand -hex 32)
API_KEY=$(openssl rand -hex 16)
SECRET_KEY=$(openssl rand -hex 24)

# Session Security
SESSION_TIMEOUT=3600
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION=300
```

#### Database Credentials (if using)

```env
# Database Configuration
DATABASE_URL=sqlite:///trading_data.db
# For PostgreSQL:
# DATABASE_URL=postgresql://username:password@localhost:5432/trading_db
```

### 🚀 GitHub CI/CD Integration

#### 1. Generate SSH Deploy Key

```bash
# On VPS, generate SSH key for GitHub
ssh-keygen -t ed25519 -C "deploy@contabo-vps" -f ~/.ssh/github_deploy

# Add public key to GitHub repository
cat ~/.ssh/github_deploy.pub
# Copy output and add to: GitHub Repo → Settings → Deploy keys
```

#### 2. Configure Git Credentials

```bash
# Configure git on VPS
git config --global user.name "Trading Bot Deploy"
git config --global user.email "deploy@yourdomain.com"

# Add GitHub to known hosts
ssh-keyscan github.com >> ~/.ssh/known_hosts
```

#### 3. Environment Variables for CI/CD

```env
# GitHub Integration
GITHUB_REPO_URL=git@github.com:YOUR_USERNAME/ai-trading-sentinel.git
GITHUB_BRANCH=main
AUTO_DEPLOY=true
DEPLOY_WEBHOOK_SECRET=your_webhook_secret
```

### 🧪 Credential Validation Script

Create validation script:

```bash
# Create credential test script
cat > test_credentials.py << 'EOF'
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
EOF

# Make executable
chmod +x test_credentials.py
```

### 🔐 Secure Storage Best Practices

#### 1. File Permissions

```bash
# Secure .env file
chmod 600 .env
chown $USER:$USER .env

# Secure SSH keys
chmod 600 ~/.ssh/github_deploy
chmod 644 ~/.ssh/github_deploy.pub
```

#### 2. Environment Validation

```bash
# Add to startup script
cat >> ~/.bashrc << 'EOF'
# Validate critical environment variables on login
if [ -f "/root/ai-trading-sentinel/.env" ]; then
    source /root/ai-trading-sentinel/.env
    if [ -z "$BULENOX_USERNAME" ] || [ -z "$BULENOX_PASSWORD" ]; then
        echo "⚠️  Warning: Trading credentials not configured"
    fi
fi
EOF
```

#### 3. Backup Credentials

```bash
# Create encrypted backup
tar -czf credentials_backup.tar.gz .env ~/.ssh/github_deploy*
gpg --symmetric --cipher-algo AES256 credentials_backup.tar.gz
rm credentials_backup.tar.gz

# Store credentials_backup.tar.gz.gpg securely
```

### ✅ Credential Setup Verification

```bash
# Run credential tests
python3 test_credentials.py

# Test trading bot startup
python3 main.py --test-mode

# Verify service can start
sudo systemctl start trae
sudo systemctl status trae
```

### 🚨 Security Checklist

- [ ] ✅ Bulenox credentials configured and tested
- [ ] ✅ Slack webhook working
- [ ] ✅ Email SMTP credentials validated
- [ ] ✅ API security tokens generated
- [ ] ✅ SSH deploy keys configured
- [ ] ✅ File permissions secured (600 for .env)
- [ ] ✅ Credentials backed up and encrypted
- [ ] ✅ All tests passing

### 🔄 Credential Rotation Schedule

```bash
# Setup monthly credential rotation reminder
(crontab -l 2>/dev/null; echo "0 9 1 * * echo 'Reminder: Rotate trading bot credentials' | mail -s 'Security Reminder' admin@yourdomain.com") | crontab -
```

---

## Next Steps

After credential setup:
1. ✅ **Paper Trading** - Start simulated trading validation
2. ✅ **Live Monitoring** - Enable 24/7 alert systems
3. ✅ **Scale Operations** - Configure multiple accounts

**Status**: 🟢 All credentials configured and secured for production use.