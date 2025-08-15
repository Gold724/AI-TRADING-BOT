# Contabo VPS Deployment Guide for Trae AI Trading Sentinel

## Overview

This guide provides specific instructions for deploying the Trae AI Trading Sentinel to your Contabo VPS (IP: 161.97.112.146) using SSH access as root user on port 22.

## Quick Start

### Option 1: Deploy from Windows

```powershell
# Run the PowerShell deployment script
.\trae_deploy.ps1
```

The script will use the default VPS IP (161.97.112.146), username (root), and SSH port (22).

To customize the deployment:

```powershell
.\trae_deploy.ps1 -VpsIp "161.97.112.146" -VpsUser "root" -SshPort "22" -SshKeyPath "path\to\key" -NotifySlack -SlackWebhookUrl "your-webhook-url"
```

### Option 2: Deploy from Linux/macOS

```bash
# Make the script executable
chmod +x trae_deploy.sh

# Run the deployment script
```bash
./trae_deploy.sh
```

The script will use the default VPS IP (161.97.112.146), username (root), and SSH port (22).

To customize the deployment:

```bash
./trae_deploy.sh --vps-ip "161.97.112.146" --vps-user "root" --ssh-port "22" --ssh-key "path/to/key" --notify-slack --slack-webhook "your-webhook-url"
```

### Option 3: GitHub Actions CI/CD

The GitHub Actions workflow is already configured to deploy to your Contabo VPS (IP: 161.97.112.146) when changes are pushed to the `main` branch.

To use this workflow:

1. Ensure the following secrets are set in your GitHub repository settings:
   - `SSH_PRIVATE_KEY` - Your SSH private key for the VPS
   - `KNOWN_HOSTS` - The SSH known hosts entry for your VPS
   - `CONTABO_USERNAME` - Username for your VPS (default: root)
   - `CONTABO_VPS_IP` - IP address of your VPS (default: 161.97.112.146)
   - `CONTABO_SSH_PORT` - SSH port for your VPS (default: 22)
   - `SLACK_WEBHOOK_URL` - (Optional) Webhook URL for Slack notifications
   - Other secrets required by your application (API keys, credentials, etc.)

## Systemd Service

The deployment scripts will automatically set up a systemd service to run the Trae AI Trading Sentinel as a background service on your VPS. The service is configured to run as the root user.

To manually manage the service:

```bash
# Start the service
systemctl start trae

# Stop the service
systemctl stop trae

# Restart the service
systemctl restart trae

# Check the service status
systemctl status trae

# View logs
journalctl -u trae -f
```

## Troubleshooting

### SSH Connection Issues

- Verify your SSH key is correctly added to the VPS
- Check that your VPS IP is correct (161.97.112.146)
- Confirm you're using the correct username (root)
- Verify you're connecting on the correct port (22)
- Ensure your VPS firewall allows SSH connections

### Deployment Script Errors

- Check that all required parameters are provided
- Verify your SSH key path is correct
- Ensure you have proper permissions to execute the script

### Service Not Starting

- Check service logs: `journalctl -u trae -f`
- Verify the Python environment is correctly set up
- Check that all required dependencies are installed

### For Additional Help

If you encounter issues not covered here, please open an issue in the GitHub repository or contact the development team.