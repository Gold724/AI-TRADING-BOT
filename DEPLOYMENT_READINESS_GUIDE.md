# 🚀 AI Trading Sentinel - Deployment Readiness Guide

## Overview
This guide will help you prepare for production deployment of the AI Trading Sentinel on your Contabo VPS. Follow these steps in order to ensure a successful deployment.

## 📋 Prerequisites Checklist

### ✅ Phase 1: VPS Setup (Contabo)

1. **Purchase Contabo VPS**
   - Recommended: VPS S (4 vCPU, 8GB RAM, 200GB SSD)
   - Operating System: Ubuntu 22.04 LTS
   - Location: Choose closest to your trading region

2. **Configure SSH Access**
   ```bash
   # Generate SSH key pair (if you don't have one)
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/contabo_key
   
   # Copy public key to VPS
   ssh-copy-id -i ~/.ssh/contabo_key.pub root@YOUR_VPS_IP
   ```

3. **Update .env Variables**
   ```env
   CONTABO_VPS_IP=YOUR_ACTUAL_VPS_IP
   CONTABO_VPS_USER=root
   CONTABO_SSH_KEY_PATH=C:\Users\Admin\.ssh\contabo_key
   ```

### ✅ Phase 2: GitHub Integration

1. **Create GitHub Personal Access Token**
   - Go to: https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Select scopes: `repo`, `workflow`, `admin:repo_hook`
   - Copy the token (starts with `ghp_`)

2. **Fork/Clone Repository**
   ```bash
   # If you haven't already, fork the repository
   # Then update .env with your repository URL
   ```

3. **Update .env Variables**
   ```env
   GITHUB_TOKEN=ghp_YOUR_ACTUAL_TOKEN_HERE
   GITHUB_REPO_URL=https://github.com/YOUR_USERNAME/ai-trading-sentinel.git
   ```

### ✅ Phase 3: Trading Platform Setup

1. **Bulenox Account Setup**
   - Register at: https://bulenox.projectx.com/login
   - Complete KYC verification
   - Fund your account (minimum $100 recommended for testing)
   - Enable API access in account settings

2. **Update .env Variables**
   ```env
   BULENOX_USERNAME=your_actual_username
   BULENOX_PASSWORD=your_actual_password
   ```

### ✅ Phase 4: Monitoring Setup (Optional but Recommended)

1. **Slack Webhook (Recommended)**
   - Create Slack workspace or use existing
   - Go to: https://api.slack.com/messaging/webhooks
   - Create new webhook for your channel
   - Copy webhook URL

2. **Update .env Variables**
   ```env
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/ACTUAL/WEBHOOK
   ```

## 🔧 Quick Setup Commands

### 1. Validate Current Configuration
```bash
python validate_environment.py
```

### 2. Test Prerequisites Only
```bash
python deploy_production.py --test-only
```

### 3. Run Full Deployment
```bash
python deploy_production.py --orchestrate
```

## 📊 Deployment Status Check

Run this command to see what's missing:
```bash
python validate_environment.py
```

**Expected Output (Ready for Deployment):**
```
✅ Environment Status: READY
✅ Required Variables: 10/10 configured
✅ VPS Connection: Available
✅ GitHub Integration: Configured
✅ Trading Platform: Credentials set
```

## 🚨 Common Issues & Solutions

### Issue 1: SSH Connection Failed
**Solution:**
```bash
# Test SSH connection manually
ssh -i ~/.ssh/contabo_key root@YOUR_VPS_IP

# If fails, check:
# 1. VPS IP is correct
# 2. SSH key path is correct
# 3. VPS is running
# 4. Firewall allows SSH (port 22)
```

### Issue 2: GitHub Token Invalid
**Solution:**
```bash
# Test GitHub token
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user

# If fails:
# 1. Regenerate token with correct scopes
# 2. Check token hasn't expired
# 3. Ensure repo access is granted
```

### Issue 3: Bulenox Login Failed
**Solution:**
- Verify credentials at: https://bulenox.projectx.com/login
- Check if account is verified and active
- Ensure 2FA is disabled or properly configured

## 🎯 Deployment Phases

### Phase 1: Prerequisites (5 minutes)
- ✅ Environment validation
- ✅ SSH connection test
- ✅ GitHub API test
- ✅ Dependencies check

### Phase 2: VPS Preparation (10 minutes)
- 🔄 System updates
- 🔄 Python 3.10+ installation
- 🔄 Node.js installation
- 🔄 Nginx installation

### Phase 3: Application Deployment (15 minutes)
- 🔄 Code deployment
- 🔄 Dependencies installation
- 🔄 Database setup
- 🔄 Service configuration

### Phase 4: Security & Monitoring (10 minutes)
- 🔄 SSL certificate setup
- 🔄 Firewall configuration
- 🔄 Health monitoring
- 🔄 Backup setup

### Phase 5: Verification (5 minutes)
- 🔄 Service health checks
- 🔄 API endpoint tests
- 🔄 Trading bot validation
- 🔄 Monitoring alerts test

## 📈 Post-Deployment

### Access Your Deployment
- **Web Interface:** `https://YOUR_VPS_IP`
- **API Endpoint:** `https://YOUR_VPS_IP/api`
- **Health Check:** `https://YOUR_VPS_IP/health`

### Monitor Your Bot
- **Logs:** `tail -f /var/log/trading-sentinel/app.log`
- **Status:** `systemctl status trading-sentinel`
- **Restart:** `systemctl restart trading-sentinel`

### Emergency Commands
```bash
# Stop trading bot immediately
sudo systemctl stop trading-sentinel

# Check system resources
htop
df -h

# View recent logs
journalctl -u trading-sentinel -f
```

## 🔒 Security Best Practices

1. **Never commit .env to version control**
2. **Use strong passwords (12+ characters)**
3. **Enable VPS firewall (UFW)**
4. **Regular security updates**
5. **Monitor access logs**
6. **Backup configuration regularly**

## 📞 Support & Troubleshooting

### Quick Diagnostics
```bash
# Full system health check
python health_check.py --full

# Network connectivity test
python deploy_production.py --test-only

# Trading platform connection test
python test_bulenox_connection.py
```

### Get Help
- **Documentation:** Check `docs/` folder
- **Logs:** Always include logs when reporting issues
- **Configuration:** Run `validate_environment.py` first

---

**Ready to Deploy?** Run: `python deploy_production.py --orchestrate`

**Need Help?** Run: `python validate_environment.py` to see what's missing.