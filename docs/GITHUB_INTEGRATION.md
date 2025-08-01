# GitHub Integration for AI Trading Sentinel

## Overview

The AI Trading Sentinel now includes GitHub integration for automatic updates and version control. This feature allows the trading system to stay up-to-date with the latest code changes, bug fixes, and improvements without manual intervention.

## Features

- **Automatic Update Checking**: Periodically checks for updates from the GitHub repository
- **Automatic Update Pulling**: Can automatically pull updates when detected
- **Automatic Restart**: Can restart the system after updates to apply changes
- **Slack Notifications**: Sends notifications about update status via Slack
- **Launcher Scripts**: Includes Windows PowerShell and Linux/Mac Bash scripts for easy startup

## Configuration

### Environment Variables

The GitHub integration is configured through the following environment variables in your `.env` file:

```
GITHUB_REPO=ai-trading-sentinel
GITHUB_USERNAME=your-username
GITHUB_PAT=your-personal-access-token
GITHUB_CHECK_INTERVAL_MINUTES=60
AUTO_UPDATE_GITHUB=false
RESTART_AFTER_UPDATE=false
```

### Variable Descriptions

- **GITHUB_REPO**: The name of your GitHub repository
- **GITHUB_USERNAME**: Your GitHub username
- **GITHUB_PAT**: Your GitHub Personal Access Token (PAT)
- **GITHUB_CHECK_INTERVAL_MINUTES**: How often to check for updates (in minutes)
- **AUTO_UPDATE_GITHUB**: Whether to automatically pull updates when detected (true/false)
- **RESTART_AFTER_UPDATE**: Whether to automatically restart after pulling updates (true/false)

## Creating a GitHub Personal Access Token (PAT)

1. Go to your GitHub account settings
2. Select "Developer settings" from the sidebar
3. Click on "Personal access tokens" and then "Tokens (classic)"
4. Click "Generate new token" and select "Generate new token (classic)"
5. Give your token a descriptive name (e.g., "AI Trading Sentinel")
6. Select the following scopes:
   - `repo` (Full control of private repositories)
   - `workflow` (if you use GitHub Actions)
7. Click "Generate token"
8. Copy the token immediately (you won't be able to see it again)
9. Paste it into your `.env` file as the `GITHUB_PAT` value

## Launcher Scripts

The system includes launcher scripts that handle GitHub updates and automatic restarts:

### Windows PowerShell Script

```powershell
.\start-sentinel-with-autoupdate.ps1
```

This script:
1. Checks if Python is installed
2. Creates a default `.env` file if one doesn't exist
3. Prompts you to configure GitHub integration if not already set up
4. Asks if you want to enable debug mode
5. Launches the sentinel with auto-update support

### Linux/Mac Bash Script

```bash
chmod +x start-sentinel-with-autoupdate.sh
./start-sentinel-with-autoupdate.sh
```

This script provides the same functionality as the Windows script but for Linux/Mac systems.

## How Auto-Updates Work

1. The system periodically checks for updates based on the `GITHUB_CHECK_INTERVAL_MINUTES` setting
2. When updates are detected, the system can automatically pull them from GitHub
3. If `RESTART_AFTER_UPDATE` is enabled, the system will restart to apply the updates
4. All update activities are logged and reported via Slack notifications

## Update Process

1. **Check for Updates**: The system compares the local repository with the remote repository
2. **Detect Changes**: If new commits are detected, the system logs this information
3. **Pull Updates** (if `AUTO_UPDATE_GITHUB=true`): The system pulls the latest changes
4. **Restart** (if `RESTART_AFTER_UPDATE=true`): The system restarts to apply the changes

## Logs and Notifications

All GitHub integration activities are logged to:
- The console
- The log files in the `logs` directory
- Slack (if configured)

## Troubleshooting

### GitHub Integration Issues

If GitHub integration is not working:

1. **Verify Credentials**: Check your GitHub username and PAT in the `.env` file
2. **Check Permissions**: Ensure your PAT has the necessary permissions (repo access)
3. **Check Connectivity**: Ensure your system can connect to GitHub
4. **Check Logs**: Look for GitHub-related error messages in the logs
5. **Repository Access**: Ensure you have access to the specified repository

### Common Error Messages

- **Authentication Failed**: Check your GitHub username and PAT
- **Repository Not Found**: Check the repository name and your access to it
- **Network Error**: Check your internet connection
- **Git Not Found**: Ensure Git is installed on your system

## Security Considerations

1. **PAT Security**: Your GitHub PAT is sensitive information. Never share it or commit it to a public repository.
2. **Automatic Updates**: Be cautious when enabling automatic updates in production environments. Consider testing updates in a staging environment first.
3. **Repository Access**: Use a PAT with the minimum necessary permissions.

## Advanced Configuration

### Custom Update Checks

You can manually trigger an update check by running:

```python
python -c "from utils.github_integration import check_for_updates; print(check_for_updates())"
```

### Manual Updates

You can manually pull updates by running:

```python
python -c "from utils.github_integration import pull_updates; print(pull_updates())"
```

### Disabling Auto-Updates Temporarily

To temporarily disable auto-updates without changing your `.env` file, you can run the sentinel with:

```bash
python heartbeat.py --no-github-updates
```

or using the launcher script:

```bash
./start-sentinel-with-autoupdate.sh --no-github-updates
```