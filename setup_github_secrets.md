# GitHub Secrets Setup Guide

## Required Secrets for AI Trading Bot

### 1. Slack Notifications (Optional)
- **SLACK_WEBHOOK_URL**: Your Slack webhook URL
  - Get from: https://api.slack.com/apps
  - Format: `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX`

### 2. VPS Deployment (Required)
- **CONTABO_VPS_IP**: Your Contabo VPS IP address (e.g., `161.97.112.146`)
- **CONTABO_VPS_PASSWORD**: Your VPS root password
- **CONTABO_SSH_PORT**: SSH port (usually `22`)

### 3. Email Notifications (Optional)
- **SMTP_SERVER**: SMTP server (e.g., `smtp.gmail.com`)
- **SMTP_PORT**: SMTP port (e.g., `587`)
- **EMAIL_USERNAME**: Your email address
- **EMAIL_PASSWORD**: Your email app password
- **EMAIL_RECIPIENT**: Notification recipient email

### 4. Trading Bot (Required)
- **BROKER_USERNAME**: Your broker username
- **BROKER_PASSWORD**: Your broker password
- **GITHUB_TOKEN**: GitHub personal access token

## How to Add Secrets

1. Go to your repository: https://github.com/Gold724/AI-TRADING-BOT
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret with the exact name and value

## Testing

After adding secrets, test the workflow:
```bash
# Trigger workflow manually
gh workflow run "CI/CD Pipeline" --repo Gold724/AI-TRADING-BOT

# Or push a commit to main branch
git add .
git commit -m "Test CI/CD pipeline"
git push origin main
```
