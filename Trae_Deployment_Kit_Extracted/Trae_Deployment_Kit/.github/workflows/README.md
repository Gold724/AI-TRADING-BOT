# GitHub Actions Workflows

This directory contains GitHub Actions workflow files for automating the deployment of the Trae AI Trading Sentinel.

## Available Workflows

### deploy.yml

This workflow handles the continuous integration and deployment (CI/CD) process for the Trae AI Trading Sentinel. It is triggered on pushes to the main branch or can be manually triggered via the GitHub Actions interface.

#### Features

- Automated testing of backend and frontend code
- Secure deployment to a VPS using SSH
- Environment variable management
- Slack notifications for deployment status

#### Required Secrets

To use this workflow, you need to set up the following secrets in your GitHub repository settings:

- `SSH_PRIVATE_KEY`: Your SSH private key for accessing the VPS
- `KNOWN_HOSTS`: The SSH known hosts entry for your VPS
- `VPS_USER`: Username for your VPS
- `VPS_IP`: IP address of your VPS
- `API_KEY`: Your API key for the trading platform
- `API_SECRET`: Your API secret for the trading platform
- `BROKER_URL`: URL for your broker
- `ADMIN_USERNAME`: Admin username for the application
- `ADMIN_PASSWORD`: Admin password for the application
- `SLACK_WEBHOOK_URL`: Webhook URL for Slack notifications

#### Usage

1. Copy this directory to your repository's `.github/workflows/` directory
2. Set up the required secrets in your GitHub repository settings
3. Push to the main branch or manually trigger the workflow