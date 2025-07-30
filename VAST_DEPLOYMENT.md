# AI Trading Sentinel - Vast.ai Deployment Guide

## Overview

This guide explains how to deploy the AI Trading Sentinel to a Vast.ai instance using the automated deployment scripts. The deployment process handles:

1. Loading environment variables from `.env`
2. Establishing an SSH connection to your Vast.ai instance
3. Setting up the trading bot with proper authentication
4. Running the bot as a background daemon process

## Prerequisites

1. A running Vast.ai instance with SSH access
2. SSH key for authentication
3. GitHub repository with your AI Trading Sentinel code
4. Python 3.x installed on your local machine

## Environment Variables

The deployment script requires the following environment variables in your `.env` file:

| Variable | Description | Required | Default |
|----------|-------------|----------|--------|
| `VAST_INSTANCE_IP` | IP address of your Vast.ai instance | Yes | - |
| `SSH_USER` | SSH username for your Vast.ai instance | No | `vast` |
| `SSH_KEY_PATH` | Path to your SSH private key | Yes | - |
| `SSH_PORT` | SSH port for your Vast.ai instance | No | `22` |
| `GITHUB_REPO` | URL of your GitHub repository | Yes | - |
| `GITHUB_USERNAME` | Your GitHub username | Yes | - |
| `GITHUB_PAT` | Your GitHub Personal Access Token | Yes | - |
| `PROJECT_DIR` | Directory name for the project on the server | No | `ai-trading-sentinel` |

## Deployment Instructions

### Windows

1. Ensure your `.env` file is properly configured
2. Double-click the `deploy_to_vast.bat` file
3. Follow the on-screen instructions

### Linux/macOS

1. Ensure your `.env` file is properly configured
2. Make the deployment script executable:
   ```bash
   chmod +x deploy_to_vast.sh
   ```
3. Run the deployment script:
   ```bash
   ./deploy_to_vast.sh
   ```

### Manual Deployment

If you prefer to run the Python script directly:

```bash
python deploy_to_vast.py
```

## Monitoring the Bot

After deployment, the bot runs as a background process. To monitor its activity:

1. SSH into your Vast.ai instance:
   ```bash
   ssh -i <your-ssh-key> vast@<your-instance-ip>
   ```

2. View the log file:
   ```bash
   cd ai-trading-sentinel
   tail -f bot.log
   ```

## Troubleshooting

### Common Issues

1. **SSH Connection Failed**
   - Verify your Vast.ai instance is running
   - Check that your SSH key path is correct
   - Ensure your SSH key has the proper permissions (chmod 600)

2. **Git Clone Failed**
   - Verify your GitHub PAT has the correct permissions
   - Check that your repository URL is correct

3. **Python Environment Issues**
   - Ensure Python 3 is installed on your Vast.ai instance
   - Check that all dependencies in requirements.txt are available

### Checking Bot Status

To verify the bot is running on your Vast.ai instance:

```bash
ps aux | grep "[p]ython backend/main.py"
```

## Security Considerations

1. **Keep your `.env` file secure**
   - Never commit it to Git repositories
   - Use the pre-commit hook to prevent accidental commits

2. **Rotate credentials regularly**
   - GitHub PAT should be rotated periodically
   - Use the minimum required permissions for your PAT

3. **SSH Key Security**
   - Use a dedicated SSH key for Vast.ai deployments
   - Protect your private key with a strong passphrase

## Additional Resources

- [Vast.ai Documentation](https://vast.ai/docs/)
- [GitHub Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [SSH Key Generation Guide](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent)