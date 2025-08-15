# Trae AI Trading Sentinel - Comprehensive Deployment Kit

## Overview

This comprehensive deployment kit contains all the necessary files and scripts to deploy the Trae AI Trading Sentinel to various environments, including VPS servers, local development environments, and Docker containers.

The kit includes:

1. **VPS Deployment Scripts** - For deploying to remote servers
2. **Docker Deployment Files** - For containerized deployment
3. **Remote UI Management Scripts** - For managing the UI components
4. **GitHub Actions Workflow** - For CI/CD automated deployments
5. **Systemd Service Configuration** - For running the bot as a system service
6. **Slack Notification Integration** - For deployment status alerts

## Quick Start

### VPS Deployment

#### Windows (PowerShell)

```powershell
# Run the PowerShell deployment script
.\trae_deploy.ps1 -VpsIp "your-vps-ip" -VpsUser "root" -SshPort "22" -SshKeyPath "path\to\key" -NotifySlack -SlackWebhookUrl "your-webhook-url"
```

#### Linux/macOS (Bash)

```bash
# Make the script executable
chmod +x trae_deploy.sh

# Run the deployment script
./trae_deploy.sh --vps-ip "your-vps-ip" --vps-user "root" --ssh-port "22" --ssh-key "path/to/key" --notify-slack --slack-webhook "your-webhook-url"
```

### Docker Deployment

```bash
# Start the full system (backend and frontend)
docker-compose up -d

# Start only the sentinel bot
docker-compose -f docker-compose.sentinel.yml up -d

# Start in development mode
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d
```

### Remote UI Management

#### Start Remote UI (Development Mode)

**Windows:**
```powershell
.\start_remote_ui_dev.ps1
```

**Linux/macOS:**
```bash
./start_remote_ui_dev.sh
```

#### Stop Remote UI

**Windows:**
```powershell
.\stop_remote_ui.ps1
```

**Linux/macOS:**
```bash
./stop_remote_ui.sh
```

#### Check Remote UI Status

**Windows:**
```powershell
.\check_remote_ui_status.ps1
```

**Linux/macOS:**
```bash
./check_remote_ui_status.sh
```

### GitHub Actions CI/CD

To use the GitHub Actions workflow for automated deployments:

1. Copy the `deploy.yml` file to your repository's `.github/workflows/` directory
2. Set up the required secrets in your GitHub repository settings

## Detailed Documentation

- For a complete list of all files included in this kit, see [FILES.md](./FILES.md)
- For a comprehensive overview of the deployment kit, see [DEPLOYMENT_KIT_README.md](./DEPLOYMENT_KIT_README.md)
- For quick start instructions, see [QUICK_START.md](./QUICK_START.md)
- For troubleshooting common issues, see [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- For Contabo VPS specific deployment, see [CONTABO_DEPLOYMENT.md](./CONTABO_DEPLOYMENT.md)

## Environment Configuration

Before deployment, create a `.env` file based on the provided `.env.example` or `.env.template`:

```bash
cp .env.example .env
# Edit the .env file with your actual values
```

## Security Considerations

- Use SSH key authentication instead of passwords
- Store sensitive information in environment variables, not in code
- Regularly update your system and dependencies
- Consider setting up a firewall on your VPS
- Regularly rotate API keys and credentials
- Monitor your VPS for unusual activity