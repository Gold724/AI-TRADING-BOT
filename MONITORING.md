# Trae AI Trading Bot Monitoring Guide

This guide explains how to set up and use the monitoring tools for the Trae AI Trading Bot.

## Table of Contents

- [Systemd Service Configuration](#systemd-service-configuration)
- [Health Check Scripts](#health-check-scripts)
- [Setting Up Scheduled Monitoring](#setting-up-scheduled-monitoring)
- [Slack Notifications](#slack-notifications)
- [Troubleshooting](#troubleshooting)

## Systemd Service Configuration

Two systemd service files are provided:

### Standard Python Service (`trae.service`)

This service runs the bot using Python directly:

```ini
[Unit]
Description=Trae AI Trading Bot
After=network.target

[Service]
User=root
WorkingDirectory=/root/ai-trading-sentinel
ExecStart=/root/ai-trading-sentinel/venv/bin/python main.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1
StandardOutput=journal
StandardError=journal
LogsDirectory=trae
RuntimeDirectory=trae
RuntimeDirectoryMode=0755
StartLimitIntervalSec=300
StartLimitBurst=5

[Install]
WantedBy=multi-user.target
```

### Gunicorn Service (`trae-gunicorn.service`)

This service runs the bot using Gunicorn for improved performance and reliability:

```ini
[Unit]
Description=Trae AI Trading Bot (Gunicorn)
After=network.target

[Service]
User=root
WorkingDirectory=/root/ai-trading-sentinel
ExecStart=/root/ai-trading-sentinel/venv/bin/gunicorn -w 2 -b 0.0.0.0:8000 main:app
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1
StandardOutput=journal
StandardError=journal
LogsDirectory=trae
RuntimeDirectory=trae
RuntimeDirectoryMode=0755
StartLimitIntervalSec=300
StartLimitBurst=5

[Install]
WantedBy=multi-user.target
```

### Installation

To install the service:

1. Copy the service file to the systemd directory:
   ```bash
   sudo cp trae.service /etc/systemd/system/
   ```

2. Reload systemd to recognize the new service:
   ```bash
   sudo systemctl daemon-reload
   ```

3. Enable the service to start on boot:
   ```bash
   sudo systemctl enable trae
   ```

4. Start the service:
   ```bash
   sudo systemctl start trae
   ```

### Viewing Logs

To view the service logs:

```bash
# View all logs
sudo journalctl -u trae

# Follow logs in real-time
sudo journalctl -u trae -f

# View logs since a specific time
sudo journalctl -u trae --since "2023-01-01"

# View only error logs
sudo journalctl -u trae -p err
```

## Health Check Scripts

Two health check scripts are provided to monitor the service status:

### PowerShell Script (`healthcheck.ps1`)

For Windows environments:

```powershell
# Basic usage
.\healthcheck.ps1 -SlackWebhookUrl "https://hooks.slack.com/services/XXX/YYY/ZZZ"

# With automatic restart on failure
.\healthcheck.ps1 -SlackWebhookUrl "https://hooks.slack.com/services/XXX/YYY/ZZZ" -RestartOnFailure

# With custom service name
.\healthcheck.ps1 -ServiceName "trae-gunicorn" -RestartOnFailure

# With custom retry parameters
.\healthcheck.ps1 -RestartOnFailure -MaxRetries 5 -RetryDelay 60
```

### Bash Script (`healthcheck.sh`)

For Linux environments:

```bash
# Basic usage
./healthcheck.sh --webhook-url "https://hooks.slack.com/services/XXX/YYY/ZZZ"

# With automatic restart on failure
./healthcheck.sh --webhook-url "https://hooks.slack.com/services/XXX/YYY/ZZZ" --restart

# With custom service name
./healthcheck.sh --service "trae-gunicorn" --restart

# With custom retry parameters
./healthcheck.sh --restart --max-retries 5 --retry-delay 60
```

## Setting Up Scheduled Monitoring

### Windows Task Scheduler

1. Open Task Scheduler
2. Click "Create Basic Task"
3. Name it "Trae Health Check" and click Next
4. Select "Daily" and click Next
5. Set the start time and click Next
6. Select "Start a program" and click Next
7. Browse to PowerShell.exe (usually in `C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe`)
8. In "Add arguments", enter:
   ```
   -ExecutionPolicy Bypass -File "C:\path\to\healthcheck.ps1" -RestartOnFailure
   ```
9. Click Next and then Finish

### Linux Cron Job

1. Open the crontab editor:
   ```bash
   crontab -e
   ```

2. Add a line to run the health check every 15 minutes:
   ```
   */15 * * * * /root/ai-trading-sentinel/healthcheck.sh --restart
   ```

3. Save and exit

## Slack Notifications

Both health check scripts and the GitHub Actions workflow use Slack notifications to alert you of any issues.

### Setting Up Slack Webhook

1. Go to [Slack API Apps](https://api.slack.com/apps)
2. Click "Create New App" and select "From scratch"
3. Name your app and select your workspace
4. Click on "Incoming Webhooks" and activate them
5. Click "Add New Webhook to Workspace"
6. Select the channel to post notifications to
7. Copy the webhook URL

### Configuring Notifications

- For the health check scripts, provide the webhook URL as a parameter
- For GitHub Actions, add the webhook URL as a repository secret named `SLACK_WEBHOOK_URL`

## Troubleshooting

### Service Won't Start

1. Check the service status:
   ```bash
   sudo systemctl status trae
   ```

2. Check for errors in the logs:
   ```bash
   sudo journalctl -u trae -p err
   ```

3. Verify the service file permissions:
   ```bash
   sudo chmod 644 /etc/systemd/system/trae.service
   ```

### Health Check Script Issues

1. Ensure the script has execute permissions (Linux):
   ```bash
   chmod +x healthcheck.sh
   ```

2. Check if the service name matches the installed service

3. Verify the Slack webhook URL is correct

### Slack Notifications Not Working

1. Verify the webhook URL is correct and active

2. Check network connectivity to Slack's servers

3. Look for error messages in the health check script output