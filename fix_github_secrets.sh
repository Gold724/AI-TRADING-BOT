#!/bin/bash

# Fix GitHub Secrets - SLACK_WEBHOOK_URL Issue
# This script provides solutions for the missing SLACK_WEBHOOK_URL secret

echo "🔧 Fixing GitHub Actions SLACK_WEBHOOK_URL Issue..."
echo "==========================================="

# Solution 1: Add SLACK_WEBHOOK_URL to GitHub Secrets (Recommended)
echo "📋 SOLUTION 1: Add SLACK_WEBHOOK_URL to GitHub Repository Secrets"
echo "--------------------------------------------------------------"
echo "1. Go to: https://github.com/Gold724/AI-TRADING-BOT/settings/secrets/actions"
echo "2. Click 'New repository secret'"
echo "3. Name: SLACK_WEBHOOK_URL"
echo "4. Value: Your Slack webhook URL (e.g., https://hooks.slack.com/services/...)"
echo ""
echo "To get a Slack webhook URL:"
echo "- Go to https://api.slack.com/apps"
echo "- Create new app or select existing"
echo "- Go to 'Incoming Webhooks' and activate"
echo "- Add webhook to workspace and copy URL"
echo ""

# Solution 2: Update workflow to handle missing secrets gracefully
echo "📋 SOLUTION 2: Update Workflow Files (Backup Solution)"
echo "----------------------------------------------------"

# Create updated workflow that handles missing secrets
cat > .github/workflows/ci_cd_pipeline_fixed.yml << 'EOF'
name: CI/CD Pipeline

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
          python-version: '3.10'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install flake8 black isort
          pip install -r requirements.txt
          
      - name: Lint with flake8
        run: |
          # stop the build if there are Python syntax errors or undefined names
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
          # exit-zero treats all errors as warnings
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
          python-version: '3.10'
          
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
          CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d. -f1)
          wget -q "https://chromedriver.storage.googleapis.com/$(wget -q -O - https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION})/chromedriver_linux64.zip"
          unzip chromedriver_linux64.zip
          sudo mv chromedriver /usr/local/bin/
          sudo chmod +x /usr/local/bin/chromedriver
          
      - name: Run tests
        run: |
          pytest --cov=. --cov-report=xml
          
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: false
          
      - name: Notify Slack on Test Completion
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          fields: repo,message,commit,author,action,eventName,ref,workflow
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
        if: always() && secrets.SLACK_WEBHOOK_URL != '' && secrets.SLACK_WEBHOOK_URL != null

  deploy:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/master'
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          
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
          
      - name: Notify Slack on Deployment
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          fields: repo,message,commit,author,action,eventName,ref,workflow
          text: 'Deployment to production completed :rocket:'
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
        if: always() && secrets.SLACK_WEBHOOK_URL != '' && secrets.SLACK_WEBHOOK_URL != null
        
      - name: Send Email Notification
        uses: dawidd6/action-send-mail@v3
        with:
          server_address: ${{ secrets.SMTP_SERVER }}
          server_port: ${{ secrets.SMTP_PORT }}
          username: ${{ secrets.EMAIL_USERNAME }}
          password: ${{ secrets.EMAIL_PASSWORD }}
          subject: TraeAI Deployment ${{ job.status }}
          body: |
            Deployment of TraeAI to production ${{ job.status }}.
            
            Commit: ${{ github.event.head_commit.message }}
            Author: ${{ github.event.head_commit.author.name }}
            Repository: ${{ github.repository }}
            
            See details: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
          to: ${{ secrets.EMAIL_RECIPIENT }}
          from: TraeAI CI/CD <${{ secrets.EMAIL_USERNAME }}>
        if: always() && secrets.EMAIL_RECIPIENT != '' && secrets.EMAIL_RECIPIENT != null
EOF

echo "✅ Created fixed workflow: .github/workflows/ci_cd_pipeline_fixed.yml"
echo ""

# Solution 3: Create a minimal workflow without Slack
echo "📋 SOLUTION 3: Create Minimal Workflow (No Slack)"
echo "-----------------------------------------------"

cat > .github/workflows/ci_cd_minimal.yml << 'EOF'
name: CI/CD Pipeline (Minimal)

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
          python-version: '3.10'
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
          python-version: '3.10'
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
          CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d. -f1)
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
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/master'
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
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
EOF

echo "✅ Created minimal workflow: .github/workflows/ci_cd_minimal.yml"
echo ""

# Create GitHub secrets setup script
echo "📋 SOLUTION 4: GitHub Secrets Setup Script"
echo "------------------------------------------"

cat > setup_github_secrets.md << 'EOF'
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
EOF

echo "✅ Created setup guide: setup_github_secrets.md"
echo ""

# Summary
echo "🎯 SUMMARY & NEXT STEPS"
echo "======================="
echo "1. ✅ RECOMMENDED: Add SLACK_WEBHOOK_URL to GitHub Secrets"
echo "   → Go to: https://github.com/Gold724/AI-TRADING-BOT/settings/secrets/actions"
echo ""
echo "2. 🔄 ALTERNATIVE: Replace current workflow with fixed version"
echo "   → Copy .github/workflows/ci_cd_pipeline_fixed.yml to replace current"
echo ""
echo "3. 🚀 MINIMAL: Use workflow without Slack notifications"
echo "   → Copy .github/workflows/ci_cd_minimal.yml to replace current"
echo ""
echo "4. 📖 GUIDE: Follow setup_github_secrets.md for complete setup"
echo ""
echo "✅ All solutions created successfully!"
echo "Choose the approach that best fits your needs."