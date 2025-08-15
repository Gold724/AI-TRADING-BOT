# Trae Auto-Scheduling & CI/CD Integration

This document explains how to set up automatic scheduling for Trae deployment using both cron jobs (Linux/macOS) and Task Scheduler (Windows), as well as GitHub Actions for CI/CD integration.

## Overview

The auto-scheduling system provides:

- Daily automatic redeployment at 3:00 AM UTC
- GitHub Actions integration for CI/CD pipeline
- Logging of deployment activities

## Linux/macOS Setup

### Using the Setup Script

1. Make the setup script executable:
   ```bash
   chmod +x setup_auto_scheduling.sh
   ```

2. Run the setup script:
   ```bash
   sudo ./setup_auto_scheduling.sh
   ```

3. Verify the cron job installation:
   ```bash
   crontab -l
   ```

### Manual Setup

1. Define deployment script location:
   ```bash
   DEPLOY_SCRIPT="/opt/trae/trae_deploy.sh"
   SSH_KEY="/root/.ssh/trae_vps"
   LOG_FILE="/var/log/trae_cron.log"
   ```

2. Install crontab job for daily auto-redeployment (3:00 AM UTC):
   ```bash
   ( crontab -l 2>/dev/null; echo "0 3 * * * /bin/bash $DEPLOY_SCRIPT --ssh-key $SSH_KEY >> $LOG_FILE 2>&1" ) | crontab -
   ```

3. Create log file with proper permissions:
   ```bash
   mkdir -p $(dirname "$LOG_FILE")
   touch "$LOG_FILE"
   chmod 644 "$LOG_FILE"
   ```

## Windows Setup

### Using the Setup Script

1. Run the PowerShell setup script as Administrator:
   ```powershell
   .\setup_auto_scheduling.ps1
   ```

2. Follow the prompts to configure:
   - Deployment script path
   - SSH key path
   - Log file location
   - Task Scheduler setup
   - GitHub Actions workflow

### Manual Setup

1. Open Task Scheduler
2. Create a new task with the following settings:
   - Name: TraeAutoDeployment
   - Trigger: Daily at 3:00 AM
   - Action: Start a program
   - Program/script: powershell.exe
   - Arguments: `-NoProfile -ExecutionPolicy Bypass -File "C:\path\to\trae_deploy.ps1" -SshKeyPath "C:\path\to\ssh_key" -LogPath "C:\path\to\logs\trae_scheduled_deploy.log"`

## GitHub Actions Setup

### Using the Setup Script

Both the Linux and Windows setup scripts will create the necessary GitHub Actions workflow file at `.github/workflows/trae_auto_deployment.yml`.

### Manual Setup

1. Create the directory structure:
   ```bash
   mkdir -p .github/workflows
   ```

2. Create the workflow file `.github/workflows/trae_auto_deployment.yml` with the following content:
   ```yaml
   name: Trae Auto Deployment

   on:
     push:
       branches:
         - main
     workflow_dispatch:
     schedule:
       # Run daily at 3:00 AM UTC
       - cron: '0 3 * * *'

   jobs:
     deploy:
       runs-on: ubuntu-latest

       steps:
       - name: Checkout code
         uses: actions/checkout@v3

       - name: Set up SSH key
         run: |
           mkdir -p ~/.ssh
           echo "${{ secrets.VPS_SSH_KEY }}" > ~/.ssh/id_rsa
           chmod 600 ~/.ssh/id_rsa
           ssh-keyscan ${{ secrets.CONTABO_VPS_IP || '161.97.112.146' }} >> ~/.ssh/known_hosts

       - name: Deploy via SSH
         run: |
           ssh ${{ secrets.CONTABO_USERNAME || 'root' }}@${{ secrets.CONTABO_VPS_IP || '161.97.112.146' }} 'bash /opt/trae/trae_deploy.sh --auto'
   ```

## GitHub Secrets Configuration

1. Go to your GitHub repository
2. Navigate to Settings > Secrets and variables > Actions
3. Add the following secrets:
   - `VPS_SSH_KEY`: The contents of your SSH private key file
   - `CONTABO_VPS_IP`: Your VPS IP address (default: 161.97.112.146)
   - `CONTABO_USERNAME`: Your VPS username (default: root)
   - `SLACK_WEBHOOK_URL`: (Optional) Your Slack webhook URL for notifications

## Security Notes

- Ensure your private key has proper permissions: `chmod 600 ~/.ssh/trae_vps` on Linux/macOS
- Make sure the deployment script is executable: `chmod +x /opt/trae/trae_deploy.sh`
- Store sensitive information only in GitHub Secrets, never in the repository code

## Troubleshooting

### Cron Job Issues

- Check cron logs: `grep CRON /var/log/syslog`
- Verify cron service is running: `systemctl status cron`
- Check deployment logs: `cat /var/log/trae_cron.log`

### Task Scheduler Issues

- Check the Task Scheduler history for the task
- Verify the deployment script path is correct
- Ensure PowerShell execution policy allows script execution

### GitHub Actions Issues

- Check the Actions tab in your GitHub repository
- Verify secrets are correctly configured
- Check SSH key permissions and format