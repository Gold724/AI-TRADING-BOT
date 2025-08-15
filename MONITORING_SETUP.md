# Trae AI Trading Bot - Monitoring, Alerts & Failsafe Setup

This document outlines the monitoring, alerting, and failsafe mechanisms implemented for the Trae AI Trading Bot.

## 1. Health Check Endpoint

The Trae backend includes a health check endpoint at `/api/health` that returns the current status of the application.

### Testing the Health Check

You can test the health check endpoint using the provided test script:

```bash
python test_health_check.py --url http://<your-vps-ip>:5000/api/health
```

Or using curl:

```bash
curl http://<your-vps-ip>:5000/api/health
```

Expected response:

```json
{
  "status": "ok",
  "timestamp": "2023-07-30T13:45:30.123456"
}
```

## 2. Uptime Monitoring

Uptime monitoring is implemented using GitHub Actions, which checks the health of the application every hour.

### GitHub Actions Workflow

The uptime monitoring workflow is defined in `.github/workflows/uptime_monitoring.yml` and performs the following actions:

1. Runs every hour via a cron schedule
2. Checks the `/api/health` endpoint
3. Sends Slack notifications on success or failure
4. Attempts to restart the service if the health check fails

### Manual Triggering

You can manually trigger the uptime check from the GitHub Actions tab in your repository.

## 3. Slack/Telegram Alerts

Slack notifications are integrated into:

1. The deployment script (`trae_deploy.sh`)
2. GitHub Actions workflows for deployment and uptime monitoring
3. Health check scripts

### Setting Up Slack Notifications

1. Create a Slack webhook URL from your Slack workspace
2. Add the webhook URL to your GitHub repository secrets as `SLACK_WEBHOOK_URL`
3. For local scripts, provide the webhook URL as a parameter:

```bash
./trae_deploy.sh --notify-slack --slack-webhook "https://hooks.slack.com/services/..."
```

## 4. Auto-Restart on Crash

The application is configured as a systemd service with automatic restart capabilities.

### Systemd Service Configuration

The `trae.service` file includes the following settings:

```ini
[Service]
ExecStart=/root/ai-trading-sentinel/venv/bin/python main.py
Restart=always
RestartSec=10
```

This ensures that if the application crashes, systemd will automatically restart it after 10 seconds.

### Managing the Service

```bash
# Check service status
sudo systemctl status trae

# Restart the service manually
sudo systemctl restart trae

# View service logs
sudo journalctl -u trae
```

## 5. Continuous Self-Test (CI/CD QA)

The deployment workflow includes a health check after deployment to verify that the application is functioning correctly.

### Test Scripts

Two test scripts are provided for testing the application:

1. `test_health_check.py` - Tests the health check endpoint
2. `test_trae_connection.py` - Tests the connection to the Trae API and verifies that it's functioning correctly

### Running the Tests

```bash
# Test the health check endpoint
python test_health_check.py

# Test the connection to the Trae API
python test_trae_connection.py --host <your-vps-ip>
```

## Troubleshooting

### Health Check Failures

If the health check fails, check the following:

1. Is the Trae service running? Check with `sudo systemctl status trae`
2. Is the port accessible? Check with `curl http://localhost:5000/api/health`
3. Are there any errors in the logs? Check with `sudo journalctl -u trae -p err`

### Slack Notification Issues

1. Verify the webhook URL is correct
2. Check network connectivity to Slack's servers
3. Look for error messages in the script output

### Service Not Auto-Restarting

1. Verify the service configuration with `sudo systemctl cat trae`
2. Check if systemd is running with `systemctl --version`
3. Check for any startup errors with `sudo journalctl -u trae -b`