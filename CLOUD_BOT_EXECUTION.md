# Cloud Bot Execution & Verification

This guide explains how to automate the full backend boot, UI testing, and trade execution on your cloud Sentinel instance.

## Prerequisites

1. A VPS or cloud server with the AI Trading Sentinel installed
2. SSH access to the server
3. Python environment with required dependencies
4. Chrome and ChromeDriver installed

## Setup

1. Copy the `.env.template` file to `.env` and fill in your values:

```bash
cp .env.template .env
```

2. Edit the `.env` file with your specific configuration:
   - VPS connection details (IP, SSH user, SSH key path)
   - Chrome and ChromeDriver paths
   - Bulenox account credentials
   - API settings
   - Notification settings

## Execution Flow

The automated execution flow consists of four main steps:

### 1. Start Backend API

- Connects to your VPS using SSH
- Activates the Python virtual environment
- Launches `cloud_main.py` using `nohup` or `supervisord`
- Confirms the API is running by checking `/api/health` endpoint

### 2. Test Selenium Login & Trade Execution

- Runs `executor_bulenox.py` with `xvfb-run` in headless mode
- Uses the specified Chrome binary and ChromeDriver
- Logs the results and takes screenshots

### 3. Trigger Frontend Trade via API

- Sends a mock JSON POST request to the trade endpoint
- Example payload:
  ```json
  {
    "symbol": "GCZ25",
    "action": "BUY",
    "lots": 1,
    "broker": "BULENOX",
    "mode": "demo"
  }
  ```

### 4. Confirm Execution

- Verifies trade logs
- Checks for screenshots
- Validates status response
- Confirms logs and notifications

## Running the Scripts

### Linux

```bash
# Make the script executable
chmod +x run_full_check.sh

# Run the script
./run_full_check.sh
```

### Windows

```powershell
# Run the batch script
run_full_check.bat
```

### GitHub Actions

The `run_full_check.yml` file can be placed in your `.github/workflows/` directory to enable automated CI/CD checks.

To run manually:
1. Go to your GitHub repository
2. Click on the "Actions" tab
3. Select the "AI Trading Sentinel - Full System Check" workflow
4. Click "Run workflow"

## Troubleshooting

### Common Issues

1. **SSH Connection Failures**
   - Ensure your SSH key has the correct permissions (chmod 600)
   - Verify the server IP and SSH user are correct
   - Check that your SSH key is added to the server's authorized_keys

2. **Chrome/ChromeDriver Issues**
   - Ensure Chrome and ChromeDriver versions match
   - Verify the paths in the .env file are correct
   - For headless mode, ensure xvfb is installed on Linux

3. **API Connection Problems**
   - Check if the API is running on the server
   - Verify the port (5000) is open in the firewall
   - Ensure the API URL is correctly formatted

### Logs and Debugging

- Check the logs in the `logs/` directory
- Review screenshots in the `screenshots/` directory
- Enable DEBUG mode in the .env file for more verbose logging

## Extending the Scripts

You can extend the scripts to include additional functionality:

- Add more comprehensive test cases
- Implement additional API endpoint tests
- Enhance the notification system
- Add performance monitoring

## Security Considerations

- Never commit your `.env` file to version control
- Use SSH keys instead of passwords for server access
- Consider implementing API key authentication
- Rotate credentials regularly