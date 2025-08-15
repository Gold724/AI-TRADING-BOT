# Trae AI Trading Sentinel - Deployment Kit

## Overview

This deployment kit contains scripts and configuration files to automate the deployment of the Trae AI Trading Sentinel to various environments, including your Contabo VPS (IP: 161.97.112.146). For Contabo-specific instructions, see [CONTABO_DEPLOYMENT.md](./CONTABO_DEPLOYMENT.md).

This kit is pre-configured for deployment to a Contabo VPS (IP: 161.97.112.146) using root user access on port 22.

The kit includes:

1. **PowerShell Deployment Script** - For Windows users deploying to VPS
2. **Bash Deployment Script** - For Linux/macOS users deploying to VPS
3. **GitHub Actions Workflow** - For CI/CD automated deployments
4. **Systemd Service Configuration** - For running the bot as a system service
5. **Slack Notification Integration** - For deployment status alerts

## Quick Start

### Windows Deployment

```powershell
# Run the PowerShell deployment script with defaults (Contabo VPS: 161.97.112.146)
.\trae_deploy.ps1

# Or with custom parameters
.\trae_deploy.ps1 -VpsIp "161.97.112.146" -VpsUser "root" -SshPort "22" -SshKeyPath "path\to\key" -NotifySlack -SlackWebhookUrl "your-webhook-url"
```

### Linux/macOS Deployment

```bash
# Make the script executable
chmod +x trae_deploy.sh

# Run the deployment script with defaults (Contabo VPS: 161.97.112.146)
./trae_deploy.sh

# Or with custom parameters
./trae_deploy.sh --vps-ip "161.97.112.146" --vps-user "root" --ssh-port "22" --ssh-key "path/to/key" --notify-slack --slack-webhook "your-webhook-url"
```

### GitHub Actions CI/CD

To use the GitHub Actions workflow for automated deployments:

1. Copy the `deploy.yml` file to your repository's `.github/workflows/` directory
2. Set up the required secrets in your GitHub repository settings:
   - `SSH_PRIVATE_KEY` - Your SSH private key for the VPS
   - `KNOWN_HOSTS` - The SSH known hosts entry for your VPS
   - `CONTABO_USERNAME` - Username for your VPS (default: root)
   - `CONTABO_VPS_IP` - IP address of your VPS (default: 161.97.112.146)
   - `CONTABO_SSH_PORT` - SSH port for your VPS (default: 22)
   - `ENV_FILE` - Base64-encoded content of your .env file
   - `SLACK_WEBHOOK_URL` - (Optional) Webhook URL for Slack notifications
   - Other secrets required by your application (API keys, credentials, etc.)

Note: The workflow is already configured with default values for your Contabo VPS (IP: 161.97.112.146).

## Deployment Scripts

### trae_deploy.ps1 (Windows)

PowerShell script for deploying from Windows machines.

**Parameters:**

- `VpsIp` (Required) - IP address of your VPS
- `VpsUser` (Required) - SSH username for your VPS
- `SshKeyPath` (Optional) - Path to your SSH private key
- `EnvFilePath` (Optional) - Path to your environment file
- `NotifySlack` (Optional) - Enable Slack notifications
- `SlackWebhookUrl` (Optional) - Webhook URL for Slack notifications

### trae_deploy.sh (Linux/macOS)

Bash script for deploying from Linux or macOS machines.

**Parameters:**

- `--vps-ip` (Required) - IP address of your VPS
- `--vps-user` (Required) - SSH username for your VPS
- `--ssh-key` (Optional) - Path to your SSH private key
- `--env` (Optional) - Path to your environment file
- `--notify-slack` (Optional) - Enable Slack notifications
- `--slack-webhook` (Optional) - Webhook URL for Slack notifications

## Systemd Service

The `trae.service` file configures the bot to run as a system service on Linux servers.

**Features:**

- Automatic startup on boot
- Automatic restart on failure
- Proper logging
- Environment variable configuration

### Installation

```bash
sudo cp trae.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable trae
sudo systemctl start trae
```

## Slack Notifications

Both deployment scripts include Slack notification capabilities. To use this feature:

1. Create a Slack app and enable Incoming Webhooks
2. Generate a webhook URL for your desired Slack channel
3. Provide the webhook URL to the deployment script

## Security Considerations

1. **SSH Key Security**
   - Use a dedicated SSH key for deployments
   - Protect your private key with a strong passphrase
   - Set proper file permissions (chmod 600)

2. **Environment Variables**
   - Never commit sensitive environment variables to Git
   - Use secure methods to transfer your .env file

3. **GitHub Secrets**
   - Regularly rotate your GitHub PAT and other secrets
   - Use the minimum required permissions

## Troubleshooting

### Common Issues

1. **SSH Connection Failed**
   - Verify your VPS is running and accessible
   - Check that your SSH key path is correct
   - Ensure your SSH key has the proper permissions

2. **Service Won't Start**
   - Check the service logs: `sudo journalctl -u trae`
   - Verify that all dependencies are installed
   - Check that your environment variables are correctly set

3. **Deployment Script Errors**
   - Run with verbose logging enabled
   - Check for network connectivity issues
   - Verify that all required parameters are provided

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Systemd Service Documentation](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [Slack API Documentation](https://api.slack.com/messaging/webhooks)