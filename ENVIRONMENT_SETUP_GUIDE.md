# 🔐 AI Trading Sentinel - Environment Variables & Secrets Management

## Production Environment Configuration Guide

**TRAE-SentinelOps** - Secure deployment configuration for 24/7 trading operations

---

## 📋 Required Environment Variables

### 🚀 VPS Deployment Configuration

```bash
# Contabo VPS Connection
export CONTABO_VPS_IP="your.vps.ip.address"          # Your Contabo VPS IP
export CONTABO_VPS_USER="ubuntu"                     # VPS username (usually ubuntu)
export CONTABO_SSH_KEY_PATH="/path/to/ssh/key"       # SSH private key path
export CONTABO_VPS_PORT="22"                         # SSH port (default: 22)

# GitHub Repository Configuration
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"       # GitHub Personal Access Token
export GITHUB_REPO_URL="https://github.com/username/ai-trading-sentinel.git"
export GITHUB_BRANCH="main"                          # Deployment branch
```

### 🔑 Trading Platform Credentials

```bash
# Bulenox Trading Platform
export BULENOX_USERNAME="your_trading_username"
export BULENOX_PASSWORD="your_secure_password"
export BULENOX_API_URL="https://bulenox.projectx.com/login"
export BULENOX_TRADING_MODE="live"                   # live or demo

# Trading Configuration
export TRADING_ACCOUNT_ID="your_account_id"
export TRADING_BALANCE_THRESHOLD="1000"              # Minimum balance
export TRADING_MAX_RISK_PERCENT="2"                  # Max risk per trade (%)
export TRADING_STOP_LOSS_PERCENT="1"                 # Stop loss (%)
export TRADING_TAKE_PROFIT_PERCENT="3"               # Take profit (%)
```

### 📊 Monitoring & Alerts

```bash
# Slack Notifications
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/xxx/xxx/xxx"
export SLACK_CHANNEL="#trading-alerts"
export SLACK_USERNAME="TRAE-SentinelOps"

# Email Alerts
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USERNAME="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
export ALERT_EMAIL_TO="alerts@yourcompany.com"

# Telegram Notifications
export TELEGRAM_BOT_TOKEN="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
export TELEGRAM_CHAT_ID="-1001234567890"
```

### 🌐 Web Application Configuration

```bash
# Flask Backend
export FLASK_ENV="production"
export FLASK_SECRET_KEY="your-super-secret-flask-key-here"
export FLASK_HOST="0.0.0.0"
export FLASK_PORT="5000"

# Database Configuration
export DATABASE_URL="sqlite:///trading_bot.db"
export REDIS_URL="redis://localhost:6379/0"

# Frontend Configuration
export VITE_API_URL="https://your-domain.com/api"
export VITE_WEBSOCKET_URL="wss://your-domain.com/ws"
export VITE_ENVIRONMENT="production"
```

### 🔒 Security Configuration

```bash
# JWT Configuration
export JWT_SECRET_KEY="your-jwt-secret-key-here"
export JWT_ACCESS_TOKEN_EXPIRES="3600"               # 1 hour
export JWT_REFRESH_TOKEN_EXPIRES="2592000"           # 30 days

# API Security
export API_RATE_LIMIT="100"                          # Requests per minute
export API_CORS_ORIGINS="https://your-domain.com"
export API_ALLOWED_IPS="127.0.0.1,your.vps.ip"

# SSL/TLS Configuration
export SSL_CERT_PATH="/etc/ssl/certs/trading-bot.crt"
export SSL_KEY_PATH="/etc/ssl/private/trading-bot.key"
export DOMAIN_NAME="your-domain.com"
```

---

## 🛠️ Environment Setup Methods

### Method 1: Local Development (.env file)

1. **Create `.env` file in project root:**

```bash
# Copy template
cp .env.template .env

# Edit with your values
nano .env
```

2. **Example `.env` file:**

```env
# VPS Configuration
CONTABO_VPS_IP=192.168.1.100
CONTABO_VPS_USER=ubuntu
CONTABO_SSH_KEY_PATH=/home/user/.ssh/contabo_key

# Trading Credentials
BULENOX_USERNAME=trader123
BULENOX_PASSWORD=SecurePass123!

# Monitoring
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX

# Security
FLASK_SECRET_KEY=super-secret-key-change-this-in-production
JWT_SECRET_KEY=jwt-secret-key-change-this-too
```

### Method 2: Production VPS (systemd environment)

1. **Create environment file:**

```bash
sudo mkdir -p /etc/trading-bot
sudo nano /etc/trading-bot/environment
```

2. **Add variables:**

```bash
CONTABO_VPS_IP=your.vps.ip
BULENOX_USERNAME=your_username
BULENOX_PASSWORD=your_password
SLACK_WEBHOOK_URL=your_webhook_url
FLASK_SECRET_KEY=your_secret_key
```

3. **Secure the file:**

```bash
sudo chmod 600 /etc/trading-bot/environment
sudo chown root:root /etc/trading-bot/environment
```

### Method 3: GitHub Actions Secrets

1. **Go to GitHub Repository → Settings → Secrets and variables → Actions**

2. **Add Repository Secrets:**

```
CONTABO_VPS_IP
CONTABO_VPS_USER
CONTABO_SSH_KEY
BULENOX_USERNAME
BULENOX_PASSWORD
SLACK_WEBHOOK_URL
FLASK_SECRET_KEY
JWT_SECRET_KEY
```

### Method 4: Docker Environment

1. **Create docker-compose.yml with env_file:**

```yaml
version: '3.8'
services:
  trading-bot:
    build: .
    env_file:
      - .env.production
    environment:
      - FLASK_ENV=production
```

---

## 🔐 Security Best Practices

### 1. SSH Key Management

```bash
# Generate SSH key for VPS access
ssh-keygen -t ed25519 -f ~/.ssh/contabo_trading_bot -C "trading-bot@contabo"

# Copy public key to VPS
ssh-copy-id -i ~/.ssh/contabo_trading_bot.pub ubuntu@your.vps.ip

# Test connection
ssh -i ~/.ssh/contabo_trading_bot ubuntu@your.vps.ip
```

### 2. Password Security

```bash
# Generate secure passwords
openssl rand -base64 32  # For Flask secret key
openssl rand -base64 24  # For JWT secret key

# Use environment-specific passwords
# Development: Simple passwords for testing
# Production: Complex, unique passwords
```

### 3. API Token Security

```bash
# GitHub Personal Access Token
# Scope: repo, workflow, write:packages
# Expiration: Set appropriate expiration date

# Slack Webhook URL
# Create app-specific webhook
# Restrict to specific channels
```

### 4. File Permissions

```bash
# Secure environment files
chmod 600 .env
chmod 600 /etc/trading-bot/environment

# Secure SSH keys
chmod 600 ~/.ssh/contabo_trading_bot
chmod 644 ~/.ssh/contabo_trading_bot.pub
```

---

## 🚀 Quick Setup Commands

### For Windows (PowerShell)

```powershell
# Set environment variables for current session
$env:CONTABO_VPS_IP = "your.vps.ip"
$env:CONTABO_VPS_USER = "ubuntu"
$env:CONTABO_SSH_KEY_PATH = "C:\Users\YourUser\.ssh\contabo_key"
$env:BULENOX_USERNAME = "your_username"
$env:BULENOX_PASSWORD = "your_password"

# Run deployment
python execute_production_deployment.py
```

### For Linux/macOS (Bash)

```bash
# Export environment variables
export CONTABO_VPS_IP="your.vps.ip"
export CONTABO_VPS_USER="ubuntu"
export CONTABO_SSH_KEY_PATH="~/.ssh/contabo_key"
export BULENOX_USERNAME="your_username"
export BULENOX_PASSWORD="your_password"

# Run deployment
python3 execute_production_deployment.py
```

### Environment Validation Script

```bash
# Create validation script
cat > validate_env.py << 'EOF'
#!/usr/bin/env python3
import os

required_vars = [
    'CONTABO_VPS_IP',
    'CONTABO_VPS_USER', 
    'CONTABO_SSH_KEY_PATH',
    'BULENOX_USERNAME',
    'BULENOX_PASSWORD'
]

missing = [var for var in required_vars if not os.getenv(var)]

if missing:
    print(f"❌ Missing environment variables: {', '.join(missing)}")
    exit(1)
else:
    print("✅ All required environment variables are set")
EOF

# Run validation
python3 validate_env.py
```

---

## 📊 Environment Templates

### Development Environment (.env.development)

```env
# Development Configuration
FLASK_ENV=development
FLASK_DEBUG=true
TRADING_MODE=demo
LOG_LEVEL=DEBUG

# Local Services
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=sqlite:///dev_trading_bot.db

# Mock Credentials (for testing)
BULENOX_USERNAME=demo_user
BULENOX_PASSWORD=demo_pass
```

### Staging Environment (.env.staging)

```env
# Staging Configuration
FLASK_ENV=staging
TRADING_MODE=demo
LOG_LEVEL=INFO

# Staging VPS
CONTABO_VPS_IP=staging.your-domain.com
VITE_API_URL=https://staging-api.your-domain.com

# Test Credentials
BULENOX_USERNAME=staging_user
BULENOX_PASSWORD=staging_secure_pass
```

### Production Environment (.env.production)

```env
# Production Configuration
FLASK_ENV=production
TRADING_MODE=live
LOG_LEVEL=WARNING

# Production VPS
CONTABO_VPS_IP=production.your-domain.com
VITE_API_URL=https://api.your-domain.com

# Live Credentials (use secure values)
BULENOX_USERNAME=live_trading_user
BULENOX_PASSWORD=super_secure_production_password
```

---

## 🔧 Troubleshooting

### Common Issues

1. **SSH Connection Failed**
```bash
# Check SSH key permissions
ls -la ~/.ssh/contabo_key
chmod 600 ~/.ssh/contabo_key

# Test SSH connection
ssh -i ~/.ssh/contabo_key -v ubuntu@your.vps.ip
```

2. **Environment Variables Not Loading**
```bash
# Check if .env file exists
ls -la .env

# Verify environment variables
env | grep CONTABO
env | grep BULENOX
```

3. **GitHub Token Issues**
```bash
# Test GitHub token
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user

# Check token permissions
# Ensure repo, workflow, write:packages scopes
```

### Validation Commands

```bash
# Test VPS connection
ssh -i $CONTABO_SSH_KEY_PATH $CONTABO_VPS_USER@$CONTABO_VPS_IP "echo 'Connection successful'"

# Test Slack webhook
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Test from TRAE-SentinelOps"}' \
  $SLACK_WEBHOOK_URL

# Validate trading credentials (mock test)
python -c "import os; print('✅ Trading creds set' if os.getenv('BULENOX_USERNAME') else '❌ Missing creds')"
```

---

## 📞 Support & Next Steps

### After Environment Setup

1. **Validate Configuration:**
   ```bash
   python validate_env.py
   ```

2. **Run Deployment:**
   ```bash
   python execute_production_deployment.py
   ```

3. **Monitor Deployment:**
   ```bash
   tail -f deployment.log
   ```

### Production Checklist

- [ ] SSH key-based authentication configured
- [ ] All environment variables set and validated
- [ ] Slack/email notifications configured
- [ ] Trading credentials verified
- [ ] SSL certificates ready (if using custom domain)
- [ ] Firewall rules configured
- [ ] Backup strategy implemented

---

**🎯 Ready for Production Deployment!**

Once all environment variables are configured, run:
```bash
python execute_production_deployment.py
```

*TRAE-SentinelOps will handle the rest automatically!* 🚀