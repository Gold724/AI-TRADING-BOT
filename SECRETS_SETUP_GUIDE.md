# 🔐 AI Trading Sentinel - Secrets Management Guide

## Overview
This guide helps you securely configure all required environment variables for production deployment.

## 🚨 Security Best Practices

1. **Never commit `.env` files to version control**
2. **Use strong, unique passwords for all accounts**
3. **Enable 2FA on all external services**
4. **Regularly rotate API keys and tokens**
5. **Use SSH key authentication for VPS access**

## 📋 Required Setup Steps

### 1. VPS Configuration

```bash
# Generate SSH key pair (run on your local machine)
ssh-keygen -t rsa -b 4096 -f ~/.ssh/contabo_key

# Copy public key to VPS
ssh-copy-id -i ~/.ssh/contabo_key.pub root@YOUR_VPS_IP
```

**Environment Variables:**
- `CONTABO_VPS_IP`: Your Contabo VPS IP address
- `CONTABO_VPS_USER`: Usually 'root' or your custom user
- `CONTABO_SSH_KEY_PATH`: Path to your SSH private key

### 2. GitHub Integration

1. Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Select scopes: `repo`, `workflow`
4. Copy the generated token (starts with `ghp_`)

**Environment Variables:**
- `GITHUB_TOKEN`: Your GitHub personal access token
- `GITHUB_REPO_URL`: Your repository URL

### 3. Trading Platform

1. Create account on [Bulenox](https://bulenox.projectx.com/login)
2. Verify your account and complete KYC if required
3. Note your login credentials

**Environment Variables:**
- `BULENOX_USERNAME`: Your Bulenox username
- `BULENOX_PASSWORD`: Your Bulenox password

### 4. Monitoring Setup

#### Slack Notifications
1. Go to [Slack API](https://api.slack.com/messaging/webhooks)
2. Create a new webhook for your workspace
3. Copy the webhook URL

**Environment Variables:**
- `SLACK_WEBHOOK_URL`: Your Slack webhook URL

#### Optional: Email Notifications
For Gmail SMTP:
1. Enable 2-factor authentication
2. Generate an app password
3. Use `smtp.gmail.com` as server

#### Optional: Telegram Notifications
1. Create a bot via [@BotFather](https://t.me/botfather)
2. Get your chat ID from [@userinfobot](https://t.me/userinfobot)

## 🔧 Configuration Commands

```bash
# Generate secure .env file with defaults
python setup_secrets.py --generate

# Validate environment configuration
python validate_environment.py

# Test VPS connection
python setup_secrets.py --test-vps

# Test GitHub integration
python setup_secrets.py --test-github
```

## 🚀 Deployment Readiness Checklist

- [ ] VPS accessible via SSH key
- [ ] GitHub token has required permissions
- [ ] Bulenox credentials verified
- [ ] Slack webhook configured
- [ ] All required environment variables set
- [ ] Environment validation passes

## 🔍 Troubleshooting

### SSH Connection Issues
```bash
# Test SSH connection
ssh -i ~/.ssh/contabo_key root@YOUR_VPS_IP

# Fix permissions
chmod 600 ~/.ssh/contabo_key
```

### GitHub Token Issues
- Ensure token has `repo` and `workflow` scopes
- Check token expiration date
- Verify repository access

### Trading Platform Issues
- Verify account is active and verified
- Check for any account restrictions
- Ensure correct login URL: https://bulenox.projectx.com/login

## 📞 Support

If you encounter issues:
1. Run `python validate_environment.py` for diagnostics
2. Check the generated `environment_validation_report.json`
3. Review logs in the `logs/` directory

---
**TRAE-SentinelOps** - Automated Production Deployment System
