# Trae AI Trading Bot - Windows Service Setup

This guide explains multiple methods to set up the Trae AI Trading Bot for 24/7 operation on Windows, including service installation and alternative methods that don't require administrator privileges.

## Prerequisites

1. Windows operating system
2. Python environment set up with all dependencies installed
3. Administrator privileges (only for Option 1 and 2)

## Option 1: PowerShell Service Manager (No Admin Required) - RECOMMENDED

This is the easiest method that doesn't require administrator privileges and provides comprehensive monitoring.

### Using run_bot_service.ps1

1. **Start the bot service:**
   ```powershell
   .\run_bot_service.ps1 -Action Start
   ```

2. **Check service status:**
   ```powershell
   .\run_bot_service.ps1 -Action Status
   ```

3. **Stop the service:**
   ```powershell
   .\run_bot_service.ps1 -Action Stop
   ```

4. **View logs:**
   ```powershell
   .\run_bot_service.ps1 -Action Logs
   ```

5. **Install startup task (runs at Windows startup):**
   ```powershell
   .\run_bot_service.ps1 -Action InstallStartup
   ```

### Using health_monitor.ps1

For advanced monitoring and health checks:

1. **Start monitoring:**
   ```powershell
   .\health_monitor.ps1 -Action Start
   ```

2. **Check health status:**
   ```powershell
   .\health_monitor.ps1 -Action Status
   ```

3. **Generate health report:**
   ```powershell
   .\health_monitor.ps1 -Action Report
   ```

## Option 2: Simple Batch File Method

For the simplest approach, use the provided batch file:

1. **Double-click** `run_bot_service.bat` to start the bot with auto-restart
2. **Close the window** to stop the bot
3. **Add to Windows Startup folder** for automatic startup:
   - Press `Win + R`, type `shell:startup`, press Enter
   - Copy `run_bot_service.bat` to this folder

## Option 3: Using the Setup Script (Requires Admin)

We've provided a PowerShell script that automates the service setup process.

### Steps:

1. Open PowerShell as Administrator:
   - Right-click on PowerShell and select "Run as Administrator"
   - Navigate to the project directory: `cd path\to\ai-trading-sentinel`

2. Run the setup script:
   ```powershell
   .\setup_windows_service.ps1
   ```

### Advanced Options:

The script supports several parameters for customization:

```powershell
.\setup_windows_service.ps1 -ServiceName "trae-custom" -DisplayName "My Trae Bot"
```

Available parameters:

- `-ServiceName`: Name of the Windows service (default: "trae")
- `-DisplayName`: Display name in Windows Services (default: "Trae AI Trading Bot")
- `-Description`: Service description (default: "AI Trading Bot service for automated trading")
- `-WorkingDirectory`: Bot's working directory (default: current directory)
- `-PythonPath`: Path to Python executable (default: "venv\Scripts\python.exe" in working directory)
- `-MainScript`: Path to main script (default: "main.py" in working directory)
- `-LogPath`: Directory for service logs (default: "logs" in working directory)

## Option 2: Manual Setup using SC Command

You can also use the built-in Windows SC command to create the service.

### Steps:

1. Open Command Prompt as Administrator
2. Run the following commands:

```cmd
sc.exe create trae binPath= "C:\path\to\python.exe C:\path\to\main.py" DisplayName= "Trae AI Trading Bot" start= auto
sc.exe description trae "AI Trading Bot service for automated trading"
sc.exe failure trae reset= 86400 actions= restart/30000/restart/60000/restart/120000
```

## Configuration Options

### Environment Variables

Both PowerShell scripts support these environment variables:
- `TRAE_LOG_LEVEL`: Set logging level (DEBUG, INFO, WARNING, ERROR)
- `TRAE_MAX_RESTARTS`: Maximum restart attempts (default: 5)
- `TRAE_RESTART_DELAY`: Delay between restarts in seconds (default: 30)
- `TRAE_HEALTH_CHECK_INTERVAL`: Health check frequency in seconds (default: 60)

### Health Monitoring Thresholds

The health monitor uses these default thresholds:
- **CPU Usage**: 80% (warning), 95% (critical)
- **Memory Usage**: 80% (warning), 95% (critical)
- **Disk Space**: 85% (warning), 95% (critical)
- **Log File Size**: 50MB (warning), 100MB (critical)
- **Error Rate**: 10 errors/hour (warning), 50 errors/hour (critical)

### Slack Notifications

To enable Slack alerts, set the webhook URL:
```powershell
$env:SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
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
   -ExecutionPolicy Bypass -File "C:\path\to\healthcheck.ps1" -ServiceName "trae" -SlackWebhookUrl "your-slack-webhook-url" -RestartOnFailure
   ```
9. Click Next and then Finish

## Troubleshooting

### Bot Fails to Start

1. **Check logs**: Use `.\run_bot_service.ps1 -Action Logs` to view recent logs
2. **Verify Python environment**: Ensure `venv\Scripts\python.exe` exists
3. **Check dependencies**: Run `pip install -r requirements.txt`
4. **Test manually**: Run `python main.py` to check for errors

### Performance Issues

1. **Check system resources**: Use `.\health_monitor.ps1 -Action Status`
2. **Review error logs**: Look for patterns in `logs\trae_service.log`
3. **Adjust thresholds**: Modify health monitoring limits if needed

### PowerShell Execution Policy

If you get execution policy errors:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Startup Task Issues

1. **Check Task Scheduler**: Open Task Scheduler and look for "TRAE Bot Service"
2. **Verify paths**: Ensure all file paths in the task are correct
3. **Test manually**: Run the startup command manually first

### Removing Services/Tasks

**Remove startup task:**
```powershell
Unregister-ScheduledTask -TaskName "TRAE Bot Service" -Confirm:$false
```

**Remove Windows service (if installed):**
```powershell
Stop-Service -Name "trae" -ErrorAction SilentlyContinue
sc.exe delete trae
```

## Performance Optimization

### System Requirements
- **RAM**: Minimum 4GB, Recommended 8GB+
- **CPU**: 2+ cores recommended
- **Disk**: 1GB free space for logs and data
- **Network**: Stable internet connection

### Optimization Tips

1. **Log Rotation**: Logs are automatically rotated when they exceed 10MB
2. **Resource Monitoring**: Health monitor tracks CPU, memory, and disk usage
3. **Auto-Restart**: Bot automatically restarts on crashes with exponential backoff
4. **Error Handling**: Comprehensive error logging and recovery mechanisms

## Security Best Practices

1. **Environment Variables**: Store sensitive data in `.env` file, not in scripts
2. **File Permissions**: Ensure log directory has appropriate write permissions
3. **Network Security**: Use HTTPS for all external API calls
4. **Regular Updates**: Keep Python and dependencies updated
5. **Monitoring**: Enable health monitoring to detect anomalies