# Fix GitHub Secrets - SLACK_WEBHOOK_URL Issue
# PowerShell script for Windows environment

Write-Host "🔧 Fixing GitHub Actions SLACK_WEBHOOK_URL Issue..." -ForegroundColor Cyan
Write-Host "==========================================="

# Solution 1: Add SLACK_WEBHOOK_URL to GitHub Secrets (Recommended)
Write-Host "📋 SOLUTION 1: Add SLACK_WEBHOOK_URL to GitHub Repository Secrets" -ForegroundColor Yellow
Write-Host "--------------------------------------------------------------"
Write-Host "1. Go to: https://github.com/Gold724/AI-TRADING-BOT/settings/secrets/actions"
Write-Host "2. Click 'New repository secret'"
Write-Host "3. Name: SLACK_WEBHOOK_URL"
Write-Host "4. Value: Your Slack webhook URL (e.g., https://hooks.slack.com/services/...)"
Write-Host ""
Write-Host "To get a Slack webhook URL:"
Write-Host "- Go to https://api.slack.com/apps"
Write-Host "- Create new app or select existing"
Write-Host "- Go to 'Incoming Webhooks' and activate"
Write-Host "- Add webhook to workspace and copy URL"
Write-Host ""

# Solution 2: Update current workflow to handle missing secrets gracefully
Write-Host "📋 SOLUTION 2: Update Current Workflow (Quick Fix)" -ForegroundColor Yellow
Write-Host "------------------------------------------------"

# Update the existing workflow file
$workflowPath = ".github\workflows\ci_cd_pipeline.yml"

if (Test-Path $workflowPath) {
    Write-Host "Updating existing workflow file..." -ForegroundColor Green
    
    # Read current content
    $content = Get-Content $workflowPath -Raw
    
    # Replace the problematic Slack notification conditions
    $updatedContent = $content -replace 
        "if: always\(\) && secrets\.SLACK_WEBHOOK_URL != ''", 
        "if: always() && secrets.SLACK_WEBHOOK_URL != '' && secrets.SLACK_WEBHOOK_URL != null"
    
    # Write updated content
    $updatedContent | Set-Content $workflowPath -Encoding UTF8
    
    Write-Host "✅ Updated workflow file with better secret handling" -ForegroundColor Green
} else {
    Write-Host "⚠️  Workflow file not found at $workflowPath" -ForegroundColor Red
}

# Solution 3: Create GitHub CLI commands for secret management
Write-Host "📋 SOLUTION 3: GitHub CLI Commands" -ForegroundColor Yellow
Write-Host "--------------------------------"

$ghCommands = @"
# Install GitHub CLI if not already installed
# Download from: https://cli.github.com/

# Login to GitHub
gh auth login

# Add SLACK_WEBHOOK_URL secret (replace with your actual webhook URL)
gh secret set SLACK_WEBHOOK_URL --body "https://hooks.slack.com/services/YOUR/WEBHOOK/URL" --repo Gold724/AI-TRADING-BOT

# Add other required secrets
gh secret set CONTABO_VPS_IP --body "161.97.112.146" --repo Gold724/AI-TRADING-BOT
gh secret set CONTABO_VPS_PASSWORD --body "YOUR_VPS_PASSWORD" --repo Gold724/AI-TRADING-BOT
gh secret set CONTABO_SSH_PORT --body "22" --repo Gold724/AI-TRADING-BOT

# List all secrets to verify
gh secret list --repo Gold724/AI-TRADING-BOT

# Test the workflow
gh workflow run "CI/CD Pipeline" --repo Gold724/AI-TRADING-BOT
"@

$ghCommands | Out-File -FilePath "github_cli_commands.txt" -Encoding UTF8
Write-Host "✅ Created GitHub CLI commands: github_cli_commands.txt" -ForegroundColor Green

# Solution 4: Create a temporary workflow without Slack
Write-Host "📋 SOLUTION 4: Create Temporary Workflow (No Slack)" -ForegroundColor Yellow
Write-Host "--------------------------------------------------"

# Ensure .github/workflows directory exists
$workflowDir = ".github\workflows"
if (!(Test-Path $workflowDir)) {
    New-Item -ItemType Directory -Path $workflowDir -Force | Out-Null
}

$minimalWorkflow = @'
name: CI/CD Pipeline (No Slack)

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]
  workflow_dispatch:

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ''3.10''
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install flake8 black isort
          pip install -r requirements.txt
      - name: Lint with flake8
        run: |
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
          flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
      - name: Check formatting with black
        run: black --check .
      - name: Check imports with isort
        run: isort --check-only --profile black .

  test:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ''3.10''
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pytest pytest-cov
          pip install -r requirements.txt
      - name: Install Chrome and ChromeDriver
        run: |
          wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
          echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
          sudo apt-get update
          sudo apt-get install -y google-chrome-stable
          CHROME_VERSION=$(google-chrome --version | awk ''{print $3}'' | cut -d. -f1)
          wget -q "https://chromedriver.storage.googleapis.com/$(wget -q -O - https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION})/chromedriver_linux64.zip"
          unzip chromedriver_linux64.zip
          sudo mv chromedriver /usr/local/bin/
          sudo chmod +x /usr/local/bin/chromedriver
      - name: Run tests
        run: pytest --cov=. --cov-report=xml
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: false

  deploy:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == ''refs/heads/main'' || github.ref == ''refs/heads/master''
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ''3.10''
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install paramiko
      - name: Deploy to Contabo VPS
        env:
          VPS_IP: ${{ secrets.CONTABO_VPS_IP }}
          VPS_PASSWORD: ${{ secrets.CONTABO_VPS_PASSWORD }}
          SSH_PORT: ${{ secrets.CONTABO_SSH_PORT }}
        run: |
          python deploy_to_contabo.py --ip "$VPS_IP" --password "$VPS_PASSWORD" --port "$SSH_PORT" --env-file .env.example
      - name: Deployment Success
        run: echo "✅ Deployment completed successfully without Slack notifications"
'@

$minimalWorkflow | Out-File -FilePath "$workflowDir\ci_cd_no_slack.yml" -Encoding UTF8
Write-Host "✅ Created minimal workflow: .github/workflows/ci_cd_no_slack.yml" -ForegroundColor Green

# Create comprehensive setup guide
Write-Host "📋 SOLUTION 5: Complete Setup Guide" -ForegroundColor Yellow
Write-Host "----------------------------------"

$setupGuide = @'
# GitHub Secrets Setup Guide for AI Trading Bot

## 🚨 IMMEDIATE FIX for SLACK_WEBHOOK_URL Error

### Option A: Add the Secret (Recommended)
1. Go to: https://github.com/Gold724/AI-TRADING-BOT/settings/secrets/actions
2. Click "New repository secret"
3. Name: `SLACK_WEBHOOK_URL`
4. Value: `https://hooks.slack.com/services/YOUR/WEBHOOK/URL`
5. Click "Add secret"

### Option B: Disable Slack Notifications (Quick Fix)
1. Replace current workflow with `ci_cd_no_slack.yml`
2. Commit and push changes
3. Workflow will run without Slack dependencies

## 📋 Required GitHub Secrets

### Core Deployment Secrets
- `CONTABO_VPS_IP`: 161.97.112.146
- `CONTABO_VPS_PASSWORD`: Your VPS root password
- `CONTABO_SSH_PORT`: 22

### Trading Bot Secrets
- `BROKER_USERNAME`: Your broker login
- `BROKER_PASSWORD`: Your broker password
- `GITHUB_TOKEN`: Personal access token for GitHub API

### Optional Notification Secrets
- `SLACK_WEBHOOK_URL`: Slack webhook for notifications
- `EMAIL_USERNAME`: SMTP email username
- `EMAIL_PASSWORD`: SMTP email password
- `EMAIL_RECIPIENT`: Notification recipient email
- `SMTP_SERVER`: SMTP server (e.g., smtp.gmail.com)
- `SMTP_PORT`: SMTP port (e.g., 587)

## 🔧 How to Get Slack Webhook URL

1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name your app (e.g., "AI Trading Bot")
4. Select your workspace
5. Go to "Incoming Webhooks" in left sidebar
6. Toggle "Activate Incoming Webhooks" to On
7. Click "Add New Webhook to Workspace"
8. Select channel and authorize
9. Copy the webhook URL (starts with https://hooks.slack.com/services/...)

## 🧪 Testing

```bash
# Test workflow manually
gh workflow run "CI/CD Pipeline" --repo Gold724/AI-TRADING-BOT

# Or push a test commit
git add .
git commit -m "Fix: Update CI/CD pipeline"
git push origin main
```

## 🔍 Troubleshooting

### Error: "Specify secrets.SLACK_WEBHOOK_URL"
- **Cause**: Secret not set in repository
- **Fix**: Add the secret or use workflow without Slack

### Error: "Bad credentials"
- **Cause**: Invalid GitHub token or VPS credentials
- **Fix**: Update secrets with correct values

### Error: "Connection refused"
- **Cause**: VPS not accessible or wrong IP/port
- **Fix**: Verify VPS IP, port, and firewall settings

## 📞 Support

If issues persist:
1. Check GitHub Actions logs
2. Verify all required secrets are set
3. Test VPS connectivity manually
4. Review workflow syntax
'@

$setupGuide | Out-File -FilePath "GITHUB_SECRETS_SETUP.md" -Encoding UTF8
Write-Host "✅ Created setup guide: GITHUB_SECRETS_SETUP.md" -ForegroundColor Green

# Summary and recommendations
Write-Host ""
Write-Host "🎯 SUMMARY & RECOMMENDATIONS" -ForegroundColor Cyan
Write-Host "============================="
Write-Host "1. 🚀 QUICKEST FIX: Add SLACK_WEBHOOK_URL secret to GitHub" -ForegroundColor Green
Write-Host "   → https://github.com/Gold724/AI-TRADING-BOT/settings/secrets/actions"
Write-Host ""
Write-Host "2. 🔄 ALTERNATIVE: Use ci_cd_no_slack.yml workflow" -ForegroundColor Yellow
Write-Host "   → Removes Slack dependency entirely"
Write-Host ""
Write-Host "3. 📖 COMPLETE GUIDE: Follow GITHUB_SECRETS_SETUP.md" -ForegroundColor Blue
Write-Host "   → Comprehensive setup for all secrets"
Write-Host ""
Write-Host "4. 🧪 TEST: Run workflow after applying fix" -ForegroundColor Magenta
Write-Host "   → Verify CI/CD pipeline works correctly"
Write-Host ""
Write-Host "✅ All solutions created successfully!" -ForegroundColor Green
Write-Host "Choose the approach that best fits your immediate needs."