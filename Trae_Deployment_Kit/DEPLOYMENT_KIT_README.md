# Trae AI Trading Sentinel - Comprehensive Deployment Kit

## Overview

This comprehensive deployment kit contains all the necessary files and scripts to deploy the Trae AI Trading Sentinel to various environments, including VPS servers, local development environments, and Docker containers.

## Contents

### Core Deployment Files

- `trae_deploy.ps1` - PowerShell script for Windows deployment
- `trae_deploy.sh` - Bash script for Linux/macOS deployment
- `trae.service` - Systemd service configuration file
- `notify_slack.py` - Python script for sending Slack notifications
- `.env.template` - Template for environment variables
- `.env.example` - Comprehensive example of environment variables

### Docker Deployment Files

- `docker-compose.yml` - Main Docker Compose configuration
- `docker-compose.override.yml` - Development override configuration
- `docker-compose.sentinel.yml` - Sentinel bot specific configuration
- `Dockerfile.backend` - Backend container configuration
- `Dockerfile.frontend` - Frontend container configuration
- `Dockerfile.sentinel` - Sentinel bot container configuration

### Remote UI Management Scripts

- `start_remote_ui_dev.ps1` - PowerShell script to start remote UI in development mode
- `start_remote_ui_dev.sh` - Bash script to start remote UI in development mode
- `stop_remote_ui.ps1` - PowerShell script to stop remote UI
- `stop_remote_ui.sh` - Bash script to stop remote UI
- `check_remote_ui_status.ps1` - PowerShell script to check remote UI status
- `check_remote_ui_status.bat` - Batch script to check remote UI status

### Ubuntu Deployment

- `deploy_ubuntu.sh` - Script for deploying on Ubuntu servers

### GitHub Actions Workflow

- `.github/workflows/deploy.yml` - GitHub Actions workflow for CI/CD
- `.github/workflows/README.md` - Documentation for GitHub Actions workflow

### Documentation

- `README.md` - Main documentation file
- `QUICK_START.md` - Quick start guide
- `TROUBLESHOOTING.md` - Troubleshooting guide
- `FILES.md` - List of all components
- `CONTABO_DEPLOYMENT.md` - Contabo VPS specific deployment instructions
- `DEPLOYMENT_KIT_README.md` - This file

## Deployment Options

### 1. VPS Deployment (Recommended for Production)

Use the provided deployment scripts to deploy directly to a VPS:

#### Windows (PowerShell)

```powershell
./trae_deploy.ps1 -VpsIp "your-vps-ip" -VpsUser "ubuntu" -SshKeyPath "path/to/private_key" -EnvFilePath ".env"
```

#### Linux/macOS (Bash)

```bash
./trae_deploy.sh --vps-ip "your-vps-ip" --vps-user "ubuntu" --ssh-key "path/to/private_key" --env ".env"
```

### 2. Docker Deployment (Recommended for Development)

Use Docker Compose to run the application in containers:

```bash
# Start the full system (backend and frontend)
docker-compose up -d

# Start only the sentinel bot
docker-compose -f docker-compose.sentinel.yml up -d

# Start in development mode
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d
```

### 3. Ubuntu Direct Deployment

For deploying directly on an Ubuntu server without Docker:

```bash
chmod +x deploy_ubuntu.sh
./deploy_ubuntu.sh
```

### 4. GitHub Actions CI/CD

To use the GitHub Actions workflow for automated deployments:

1. Copy the `.github/workflows/deploy.yml` file to your repository's `.github/workflows/` directory
2. Set up the required secrets in your GitHub repository settings

## Getting Started

1. Copy this entire deployment kit to your project
2. Create a `.env` file based on `.env.example` or `.env.template`
3. Choose your preferred deployment method from the options above
4. Follow the specific instructions for your chosen deployment method

## Troubleshooting

If you encounter issues during deployment, refer to the `TROUBLESHOOTING.md` file for common issues and solutions.

## Security Considerations

- Never commit your `.env` file with real credentials to version control
- Use SSH key authentication instead of passwords for VPS access
- Regularly update your system and dependencies
- Consider setting up a firewall on your VPS
- Regularly rotate API keys and credentials