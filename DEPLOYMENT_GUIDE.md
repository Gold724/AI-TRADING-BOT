# TRAE AI Trading Bot - Deployment Guide

This guide provides step-by-step instructions for deploying the TRAE AI Trading Bot with Adaptive Intelligence on both Linux and Windows systems.

## Linux Deployment

### Prerequisites

- Linux server with systemd (Ubuntu, Debian, CentOS, etc.)
- Root or sudo access
- Python 3.8+ installed
- Git (to clone the repository if needed)

### Automatic Deployment

The easiest way to deploy the TRAE AI Trading Bot on Linux is to use the provided deployment script:

```bash
# Make the script executable
chmod +x deploy_adaptive_intelligence.sh

# Run as root
sudo ./deploy_adaptive_intelligence.sh
```

This script will automatically:
1. Copy the trae-bot.service file to /etc/systemd/system/
2. Reload the systemd daemon
3. Enable the trae-bot service
4. Start the trae-bot service
5. Set up the cron jobs for Adaptive Intelligence

### Manual Deployment

If you prefer to deploy manually, follow these steps:

1. Copy the service file to systemd:
   ```bash
   sudo cp trae-bot.service /etc/systemd/system/
   ```

2. Reload the systemd daemon:
   ```bash
   sudo systemctl daemon-reload
   ```

3. Enable the service to start on boot:
   ```bash
   sudo systemctl enable trae-bot
   ```

4. Start the service:
   ```bash
   sudo systemctl start trae-bot
   ```

5. Set up the cron jobs:
   ```bash
   chmod +x setup_adaptive_intelligence_cron.sh
   ./setup_adaptive_intelligence_cron.sh
   ```

### Verifying Deployment

To verify that the deployment was successful:

1. Check the service status:
   ```bash
   sudo systemctl status trae-bot
   ```

2. Check the logs:
   ```bash
   tail -f /root/AI-TRADING-BOT/trae_output.log
   ```

3. Verify cron jobs:
   ```bash
   crontab -l | grep activate_adaptive_intelligence
   ```

## Windows Deployment

### Prerequisites

- Windows 10/11 or Windows Server 2016+
- Administrator access
- Python 3.8+ installed and added to PATH
- PowerShell 5.0+ (included in Windows 10+)

### Automatic Deployment

The easiest way to deploy on Windows is to use the provided batch file:

1. Right-click on `deploy_adaptive_intelligence.bat`
2. Select "Run as administrator"

Alternatively, you can run the PowerShell script directly:

1. Open PowerShell as Administrator
2. Navigate to the project directory
3. Run:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\deploy_adaptive_intelligence.ps1
   ```

The deployment script will:
1. Check for Python installation
2. Activate the virtual environment if present
3. Set up scheduled tasks for Adaptive Intelligence
4. Test the Adaptive Intelligence activation
5. Verify the deployment

### Manual Deployment

If you prefer to deploy manually:

1. Set up scheduled tasks:
   ```powershell
   # Run as Administrator
   .\setup_adaptive_intelligence_tasks.ps1
   ```

2. Test the Adaptive Intelligence system:
   ```powershell
   .\activate_adaptive_intelligence.ps1 -mode initialize
   ```

### Verifying Deployment

To verify that the deployment was successful:

1. Check scheduled tasks:
   ```powershell
   Get-ScheduledTask | Where-Object {$_.TaskName -like "*TRAE*"} | Format-Table TaskName,State
   ```

2. Check the logs directory for log files

## Troubleshooting

### Linux

- **Service fails to start**: Check the logs with `journalctl -u trae-bot`
- **Cron jobs not running**: Verify cron service is running with `systemctl status cron`
- **Permission issues**: Ensure all scripts have execute permission with `chmod +x *.sh`

### Windows

- **PowerShell execution policy**: If scripts won't run, use `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
- **Scheduled tasks not running**: Check Task Scheduler for error details
- **Python not found**: Ensure Python is in your PATH environment variable

## Additional Resources

For more information about the Adaptive Intelligence System, refer to the [ADAPTIVE_INTELLIGENCE_SYSTEM.md](ADAPTIVE_INTELLIGENCE_SYSTEM.md) documentation.