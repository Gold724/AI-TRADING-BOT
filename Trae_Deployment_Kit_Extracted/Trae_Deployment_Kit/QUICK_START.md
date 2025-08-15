# Trae AI Trading Sentinel - Quick Start Guide

This guide provides quick instructions for deploying the Trae AI Trading Sentinel using the deployment kit.

## Prerequisites

- SSH access to your VPS
- Python 3.8+ installed on your local machine
- Node.js and npm installed on your local machine (for frontend development)
- Git installed on your local machine

## Deployment Steps

### 1. Prepare Environment Variables

Copy the `.env.template` file to `.env` and fill in your credentials:

```bash
cp .env.template .env
# Edit .env with your favorite text editor
```

### 2. Deploy Using Windows PowerShell

```powershell
.\trae_deploy.ps1 -VpsIp "your-vps-ip" -VpsUser "your-username" -SshKeyPath "path\to\key" -EnvFilePath ".env" -NotifySlack -SlackWebhookUrl "your-webhook-url"
```

### 3. Deploy Using Linux/macOS Bash

```bash
chmod +x trae_deploy.sh
./trae_deploy.sh --vps-ip "your-vps-ip" --vps-user "your-username" --ssh-key "path/to/key" --env ".env" --notify-slack --slack-webhook "your-webhook-url"
```

### 4. Deploy Using GitHub Actions

1. Copy `deploy.yml` to your repository's `.github/workflows/` directory
2. Set up the required secrets in your GitHub repository settings
3. Push to the main branch or manually trigger the workflow

## Verifying Deployment

After deployment, you can verify that the service is running:

```bash
ssh your-username@your-vps-ip "sudo systemctl status trae"
```

## Monitoring Logs

To view the service logs:

```bash
ssh your-username@your-vps-ip "sudo journalctl -u trae -f"
```

## Troubleshooting

If you encounter issues during deployment:

1. Check the deployment script output for errors
2. Verify that all environment variables are correctly set
3. Check the service logs for runtime errors
4. Ensure that your VPS has sufficient resources

## Getting Help

If you need further assistance, please refer to the full documentation in the `README.md` file or open an issue in the GitHub repository.