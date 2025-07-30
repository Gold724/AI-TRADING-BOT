# AI Trading Sentinel - Deployment Guide

## Overview

This repository contains scripts to automate the deployment of the AI Trading Sentinel to a Vast.ai instance. The deployment process handles:

1. Loading environment variables from `.env`
2. Establishing an SSH connection to your Vast.ai instance
3. Setting up the trading bot with proper authentication
4. Running the bot as a background daemon process

## Quick Start

### Windows

```bash
# Run the deployment script
python deploy_to_vast.py

# Or use the batch file
deploy_to_vast.bat
```

### Linux/macOS

```bash
# Make the script executable
chmod +x deploy_to_vast.sh

# Run the deployment script
./deploy_to_vast.sh
```

## Dry Run Mode

To validate your configuration without actually connecting to the server, use the `--dry-run` flag:

```bash
python deploy_to_vast.py --dry-run
```

This will check your environment variables, SSH key, and display the commands that would be executed on the server.

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

## Deployment Files

- `deploy_to_vast.py` - Main Python deployment script
- `deploy_to_vast.bat` - Windows batch file for easy deployment
- `deploy_to_vast.sh` - Linux/macOS shell script for easy deployment
- `VAST_DEPLOYMENT.md` - Detailed deployment documentation

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

If you encounter issues during deployment, check the following:

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

## Additional Resources

- [Vast.ai Documentation](https://vast.ai/docs/)
- [GitHub Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [SSH Key Generation Guide](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent)