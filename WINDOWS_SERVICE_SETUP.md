# Trae AI Trading Bot - Windows Service Setup

This guide explains how to set up the Trae AI Trading Bot as a Windows service, which allows it to run automatically at system startup and restart on failure.

## Prerequisites

1. Windows operating system
2. Administrator privileges
3. Python environment set up with all dependencies installed

## Option 1: Using the Setup Script (Recommended)

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

## Using the Health Check Script

Once the service is set up, you can use the provided health check script to monitor its status:

```powershell
.\healthcheck.ps1 -ServiceName "trae" -SlackWebhookUrl "your-slack-webhook-url" -RestartOnFailure
```

Parameters:
- `-ServiceName`: The name of the service to monitor (default: "trae")
- `-SlackWebhookUrl`: Your Slack webhook URL for notifications
- `-RestartOnFailure`: Automatically restart the service if it's not running
- `-MaxRetries`: Maximum number of restart attempts (default: 3)
- `-RetryDelay`: Delay between restart attempts in seconds (default: 30)

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

### Service Fails to Start

1. Check the service logs in the configured log directory
2. Verify that all dependencies are installed
3. Ensure the Python path and main script path are correct
4. Check Windows Event Viewer for additional error details

### Administrator Privileges Required

Both the setup script and manual service creation require administrator privileges. If you see an error about administrator privileges, make sure to:

1. Right-click on PowerShell and select "Run as Administrator"
2. Navigate to your project directory
3. Run the setup script again

### Uninstalling the Service

To remove the service:

1. Open PowerShell as Administrator
2. Stop the service: `Stop-Service -Name "trae"`
3. Delete the service: `sc.exe delete trae`