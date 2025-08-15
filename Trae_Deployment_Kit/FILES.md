# Trae AI Trading Sentinel - Deployment Kit Files

This document provides an overview of all files included in the Trae AI Trading Sentinel Deployment Kit.

## Core Deployment Scripts

- `trae_deploy.ps1` - PowerShell script for Windows deployment
- `trae_deploy.sh` - Bash script for Linux/macOS deployment
- `trae.service` - Systemd service configuration file
- `notify_slack.py` - Python script for sending Slack notifications
- `.env.template` - Template for environment variables
- `.env.example` - Comprehensive example of environment variables

## Docker Deployment Files

- `docker-compose.yml` - Main Docker Compose configuration
- `docker-compose.override.yml` - Development override configuration
- `docker-compose.sentinel.yml` - Sentinel bot specific configuration
- `Dockerfile.backend` - Backend container configuration
- `Dockerfile.frontend` - Frontend container configuration
- `Dockerfile.sentinel` - Sentinel bot container configuration

## Remote UI Management Scripts

- `start_remote_ui_dev.ps1` - PowerShell script to start remote UI in development mode
- `start_remote_ui_dev.sh` - Bash script to start remote UI in development mode
- `stop_remote_ui.ps1` - PowerShell script to stop remote UI
- `stop_remote_ui.sh` - Bash script to stop remote UI
- `check_remote_ui_status.ps1` - PowerShell script to check remote UI status
- `check_remote_ui_status.bat` - Batch script to check remote UI status

## Ubuntu Deployment

- `deploy_ubuntu.sh` - Script for deploying on Ubuntu servers

## GitHub Actions Workflow

- `.github/workflows/deploy.yml` - GitHub Actions workflow for CI/CD
- `.github/workflows/README.md` - Documentation for GitHub Actions workflow

## Documentation

- `README.md` - Main documentation file
- `QUICK_START.md` - Quick start guide
- `TROUBLESHOOTING.md` - Troubleshooting guide
- `FILES.md` - This file listing all components
- `CONTABO_DEPLOYMENT.md` - Contabo VPS specific deployment instructions
- `DEPLOYMENT_KIT_README.md` - Comprehensive deployment kit overview

## Usage

To use the deployment kit:

1. Extract the `Trae_Deployment_Kit.zip` file
2. Follow the instructions in `DEPLOYMENT_KIT_README.md` for your specific deployment scenario
3. Refer to `TROUBLESHOOTING.md` if you encounter any issues