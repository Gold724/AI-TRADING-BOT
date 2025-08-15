# Trae AI Trading Sentinel Deployment Kit

This document provides instructions for deploying the Trae AI Trading Sentinel to a Contabo VPS using the provided deployment tools, setting up the cloud control panel, and configuring the system for optimal performance and security.

## Deployment Options

There are three main deployment approaches available:

1. **Local Execution** - Run deployment scripts from your local machine
2. **GitHub Actions** - Automated deployment triggered by code pushes
3. **Manual VPS Setup** - Direct setup on the VPS using systemd

### Prerequisites

- A Contabo VPS with Ubuntu 22.04 installed
- SSH access to your VPS
- Your project pushed to GitHub
- `.env.example` file committed to your repository
- Python 3.8 or higher
- Required Python packages (see `requirements.txt`)

## New Features

### Cloud Control Panel

The cloud control panel provides a web interface for managing your trading system:

1. Start the control panel API:
   ```bash
   python3 api/control_panel_api.py
   ```

2. Access the dashboard at `http://your-server-ip:5000` or `https://your-domain.com` if HTTPS is configured.

3. The dashboard allows you to:
   - View trading statistics and account balances
   - Execute manual trades
   - Toggle Dreamer Mode (simulation)
   - Start/stop the TRAE AI Agent
   - View logs and monitor system status

### Dreamer Mode (Simulation)

Dreamer Mode allows you to simulate trades without real execution:

1. Enable Dreamer Mode through the control panel or via command line:
   ```bash
   python3 main.py --liveops --dreamer
   ```

2. All trade executions will be simulated with realistic responses.

3. Simulation results are stored in the data directory and can be viewed in the control panel.

### TRAE AI Agent

The TRAE AI Agent analyzes market data and generates trading signals:

1. Configure the AI Agent:
   ```bash
   # Edit the configuration file
   nano trae_ai_config.json
   ```

2. Start the AI Agent:
   ```bash
   python3 trae_ai.py --start
   ```

3. The AI Agent will analyze markets based on your configuration and generate signals.

### Scheduled Auto-Runs & Logs

Configure the system to run automatically at specific times:

1. Set up auto-scheduling:
   ```bash
   python3 setup_liveops_scheduler.py
   ```

2. This will configure cron jobs (Linux/macOS) or Task Scheduler tasks (Windows) to:
   - Start the system at market open times
   - Create daily log files
   - Generate performance reports

### Secure Endpoints

To secure your API endpoints:

1. Generate API keys and configure JWT authentication:
   ```bash
   python3 setup_liveops_security.py
   ```

2. For secure HTTPS connections:
   ```bash
   python3 setup_https.py --domain yourdomain.com --email your@email.com
   ```
   Or for self-signed certificates:
   ```bash
   python3 setup_https.py --domain localhost --self-signed
   ```

### Tiered Licensing Model

The TRAE AI Trading Sentinel supports a tiered licensing model:

1. Set up licensing:
   ```bash
   python3 setup_licensing.py
   ```

2. Available tiers:
   - **Free Tier**: Signals only, no execution
   - **Standard Tier**: Manual execution via dashboard
   - **Pro Tier**: Auto execution with webhooks
   - **Elite Tier**: Stealth mode with secure AI-assisted trading

## 1. Local Execution

Use the provided deployment scripts to deploy directly from your local machine.

### Windows (PowerShell)

```powershell
./trae_deploy.ps1 -VpsIp "your-vps-ip" -VpsUser "ubuntu" -SshKeyPath "path/to/private_key" -EnvFilePath ".env"
```

Optional parameters:
- `-NotifySlack` - Enable Slack notifications
- `-SlackWebhookUrl "your-webhook-url"` - Slack webhook URL for notifications

### Linux/macOS (Bash)

```bash
./trae_deploy.sh --vps-ip "your-vps-ip" --vps-user "ubuntu" --ssh-key "path/to/private_key" --env ".env"
```

Optional parameters:
- `--notify-slack` - Enable Slack notifications
- `--slack-webhook "your-webhook-url"` - Slack webhook URL for notifications

The deployment scripts will:
- Transfer project files to the VPS
- Set up Python virtual environment
- Install dependencies
- Configure systemd service
- Start the trading bot

## 2. GitHub Actions

The repository includes a GitHub Actions workflow file (`.github/workflows/deploy.yml`) that automatically tests and deploys the application when code is pushed to the main branch.

### Setup

1. Add the following secrets to your GitHub repository:

   - `SSH_PRIVATE_KEY` - Your SSH private key for VPS access
   - `KNOWN_HOSTS` - SSH known hosts entry for your VPS
   - `CONTABO_USERNAME` - Username for VPS login (default: "root")
   - `CONTABO_VPS_IP` - IP address of your Contabo VPS (default: "161.97.112.146")
   - `CONTABO_SSH_PORT` - SSH port for your VPS (default: "22")
   - `API_KEY` - Your trading API key
   - `API_SECRET` - Your trading API secret
   - `BROKER_URL` - URL for your broker API
   - `ADMIN_USERNAME` - Admin username for the application
   - `ADMIN_PASSWORD` - Admin password for the application
   - `SLACK_WEBHOOK_URL` - (Optional) Slack webhook URL for notifications

2. Push to the main branch or manually trigger the workflow from the GitHub Actions tab.

## 3. Manual VPS Setup

You can also set up the application directly on your VPS using systemd.

1. Copy the `trae.service` file to your VPS:

   ```bash
   scp trae.service username@your-vps-ip:~/
   ```

2. SSH into your VPS and move the service file to the systemd directory:

   ```bash
   sudo mv ~/trae.service /etc/systemd/system/
   ```

3. Enable and start the service:

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable trae
   sudo systemctl start trae
   ```

4. Check the service status:

   ```bash
   sudo systemctl status trae
   ```

## Monitoring and Logs

To monitor your bot and view logs:

```bash
# View service status
sudo systemctl status trae

# View logs in real-time
sudo journalctl -u trae -f
```

## Updating the Bot

To update your bot with the latest code:

```bash
cd ~/ai-trading-sentinel
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart trae
```

## Slack Notifications

The deployment kit includes support for Slack notifications. To use this feature:

1. Create a Slack app and webhook URL in your Slack workspace
2. Add the webhook URL to your deployment configuration:
   - For local deployment scripts: Use the `-NotifySlack` and `-SlackWebhookUrl` parameters
   - For GitHub Actions: Add the `SLACK_WEBHOOK_URL` secret
   - For manual setup: Use the included `notify_slack.py` script

```bash
# Send a notification manually
python notify_slack.py --webhook-url "your-webhook-url" --message "Deployment completed" --status "success"
```

## Troubleshooting

### Service Not Starting

If the service fails to start:

```bash
# Check for errors in the service
sudo journalctl -u trae -e

# Verify environment variables
cat .env

# Test running the bot manually
source venv/bin/activate
python main.py
```

### Deployment Script Issues

If the deployment scripts fail:

1. Check SSH connectivity to your VPS
2. Verify that your SSH key has the correct permissions
3. Ensure your `.env` file contains all required variables
4. Check for any firewall rules that might block SSH or rsync

## Security Considerations

- Use SSH key authentication instead of passwords
- Store sensitive information in environment variables, not in code
- Regularly update your system: `sudo apt update && sudo apt upgrade -y`
- Consider setting up a firewall: `sudo ufw enable`
- Regularly rotate API keys and credentials
- Monitor your VPS for unusual activity

## Additional Resources

- [Contabo VPS Documentation](https://contabo.com/en/product-docs/)
- [Systemd Service Documentation](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)







(crontab -l 2>/dev/null; echo "0 0 * * * ~/backup-trading-bot.sh") | crontab -
```