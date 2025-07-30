# AI Trading Sentinel - Remote UI Deployment Guide

## Overview

This guide explains how to deploy the AI Trading Sentinel with a remote user interface that allows you to control your trading bot from anywhere. The deployment process sets up both the backend API and frontend UI on a Vast.ai instance, enabling remote monitoring and control of your trading operations.

## Prerequisites

1. A Vast.ai account with an active instance running Ubuntu 20.04 or newer
2. SSH access to your Vast.ai instance
3. A GitHub Personal Access Token (PAT) with repo scope
4. The AI Trading Sentinel repository cloned to your local machine

## Configuration

Before deployment, ensure your `.env` file contains the following variables:

```
# Vast.ai Connection Details
VAST_INSTANCE_IP=your_instance_ip
SSH_USER=vast
SSH_KEY_PATH=/path/to/your/ssh/key
SSH_PORT=22

# GitHub Integration
GITHUB_REPO=https://github.com/username/ai-trading-sentinel.git
GITHUB_USERNAME=your_github_username
GITHUB_PAT=your_github_personal_access_token

# Bulenox Credentials
BULENOX_USERNAME=your_bulenox_username
BULENOX_PASSWORD=your_bulenox_password
BULENOX_ACCOUNT_ID=your_bulenox_account_id

# Flask API Settings
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
CORS_ORIGINS=*

# Cloud Execution Settings
HEADLESS=true
USE_TEMP_PROFILE=true
SCREENSHOT_ON_FAILURE=true
```

## Deployment Options

The deployment script supports several options:

1. **Full Deployment**: Deploy both the backend API and frontend UI
2. **Backend Only**: Deploy only the backend API for programmatic access
3. **Frontend Only**: Deploy only the frontend UI (assumes backend is already running)
4. **Dry Run**: Validate your configuration without making any changes

## Deployment Steps

### Windows

1. Open a command prompt in the project directory
2. Run the deployment batch file:
   ```
   deploy_remote_ui.bat
   ```
3. Select the desired deployment option (1-4)

### Linux/Mac

1. Open a terminal in the project directory
2. Make the deployment script executable:
   ```
   chmod +x deploy_remote_ui.sh
   ```
3. Run the deployment script:
   ```
   ./deploy_remote_ui.sh
   ```
4. Select the desired deployment option (1-4)

### Manual Deployment

You can also run the Python script directly with specific options:

```
python deploy_remote_ui.py [--dry-run] [--frontend-only] [--backend-only]
```

## Accessing the Remote UI

After successful deployment:

1. The backend API will be available at: `http://<your-vast-ip>:5000`
2. The frontend UI will be available at: `http://<your-vast-ip>:3000`

You can also connect your local frontend to the remote API:

1. Open the frontend in your browser: `http://localhost:3000`
2. In the Quick Actions panel, set the API Endpoint to: `http://<your-vast-ip>:5000`

## Remote Control Features

The remote UI provides the following capabilities:

1. **Bot Status Monitoring**: View the current status of your trading bot
2. **Strategy Selection**: Change trading strategies remotely
3. **Trade Execution**: Execute manual trades from anywhere
4. **Log Viewing**: Monitor application logs in real-time

## Troubleshooting

### Connection Issues

- Verify your Vast.ai instance is running
- Check that ports 5000 and 3000 are open in your instance's firewall
- Ensure your SSH key has the correct permissions

### Deployment Failures

- Check the deployment logs for specific error messages
- Verify your GitHub PAT has the correct permissions
- Ensure your `.env` file contains all required variables

### Runtime Errors

- Check the application logs using: `tail -f cloud_api.log` and `tail -f frontend.log`
- Verify Chrome is installed and configured correctly on your Vast.ai instance
- Check that your Bulenox credentials are correct

## Security Considerations

- The remote UI is configured with CORS set to `*` for development purposes
- For production use, restrict CORS to specific origins
- Consider implementing authentication for the API endpoints
- Keep your `.env` file secure and excluded from Git commits