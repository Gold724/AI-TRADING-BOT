# 🚀 AI Trading Sentinel - Service Installation Guide

## Overview
This guide provides step-by-step instructions for installing the AI Trading Sentinel as a Windows service for 24/7 operation.

## Prerequisites

### 1. Administrator Privileges Required
- **IMPORTANT**: Service installation requires administrator privileges
- Right-click Command Prompt or PowerShell and select "Run as administrator"

### 2. System Requirements
- Windows 10/11 or Windows Server 2016+
- Python 3.8+ with virtual environment
- At least 4GB RAM (8GB recommended)
- 2GB free disk space
- Stable internet connection

## Installation Methods

### Method 1: Automated Installation (Recommended)

#### Step 1: Run as Administrator
```powershell
# Open PowerShell as Administrator
# Navigate to project directory
cd "C:\Users\Admin\Downloads\ai-trading-sentinel"

# Run service installation
.\deploy_windows.ps1 -Service
```

#### Step 2: Verify Installation
```powershell
# Check service status
Get-Service -Name "AITradingSentinel" -ErrorAction SilentlyContinue

# Start service if not running
Start-Service -Name "AITradingSentinel"

# Check service status
Get-Service -Name "AITradingSentinel"
```

### Method 2: Manual Installation

#### Step 1: Install Python Service Wrapper
```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install pywin32 for Windows service support
pip install pywin32

# Install service wrapper
pip install python-windows-service
```

#### Step 2: Create Service Script
Create `service_wrapper.py`:

```python
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import os
import time
import logging
from pathlib import Path

class AITradingSentinelService(win32serviceutil.ServiceFramework):
    _svc_name_ = "AITradingSentinel"
    _svc_display_name_ = "AI Trading Sentinel Bot"
    _svc_description_ = "Automated trading bot for financial markets"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.is_alive = True
        
        # Setup logging
        log_path = Path(__file__).parent / "logs" / "service.log"
        log_path.parent.mkdir(exist_ok=True)
        
        logging.basicConfig(
            filename=str(log_path),
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('AITradingSentinelService')
    
    def SvcStop(self):
        self.logger.info("Service stop requested")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_alive = False
    
    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        self.logger.info("AI Trading Sentinel Service started")
        self.main()
    
    def main(self):
        """Main service loop"""
        try:
            # Change to script directory
            script_dir = Path(__file__).parent
            os.chdir(script_dir)
            
            # Import and run main bot
            sys.path.insert(0, str(script_dir))
            
            while self.is_alive:
                try:
                    # Import main module
                    import main
                    
                    # Run the bot
                    self.logger.info("Starting trading bot main loop")
                    main.main()
                    
                except Exception as e:
                    self.logger.error(f"Error in main loop: {e}")
                    time.sleep(30)  # Wait before retry
                
                # Check if service should stop
                if win32event.WaitForSingleObject(self.hWaitStop, 5000) == win32event.WAIT_OBJECT_0:
                    break
        
        except Exception as e:
            self.logger.error(f"Service error: {e}")
            servicemanager.LogErrorMsg(f"Service error: {e}")

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(AITradingSentinelService)
```

#### Step 3: Install Service
```powershell
# Install the service
python service_wrapper.py install

# Start the service
python service_wrapper.py start

# Check status
python service_wrapper.py status
```

### Method 3: Using NSSM (Non-Sucking Service Manager)

#### Step 1: Download NSSM
1. Download NSSM from: https://nssm.cc/download
2. Extract to `C:\nssm`
3. Add `C:\nssm\win64` to PATH

#### Step 2: Create Service
```powershell
# Create service with NSSM
nssm install AITradingSentinel

# Configure service
nssm set AITradingSentinel Application "C:\Users\Admin\Downloads\ai-trading-sentinel\venv\Scripts\python.exe"
nssm set AITradingSentinel AppParameters "main.py"
nssm set AITradingSentinel AppDirectory "C:\Users\Admin\Downloads\ai-trading-sentinel"
nssm set AITradingSentinel DisplayName "AI Trading Sentinel"
nssm set AITradingSentinel Description "Automated AI Trading Bot"

# Set startup type
nssm set AITradingSentinel Start SERVICE_AUTO_START

# Configure logging
nssm set AITradingSentinel AppStdout "C:\Users\Admin\Downloads\ai-trading-sentinel\logs\service_stdout.log"
nssm set AITradingSentinel AppStderr "C:\Users\Admin\Downloads\ai-trading-sentinel\logs\service_stderr.log"

# Start service
nssm start AITradingSentinel
```

## Service Management

### Start/Stop/Restart Service
```powershell
# Start service
Start-Service -Name "AITradingSentinel"

# Stop service
Stop-Service -Name "AITradingSentinel"

# Restart service
Restart-Service -Name "AITradingSentinel"

# Check status
Get-Service -Name "AITradingSentinel"
```

### View Service Logs
```powershell
# View service logs
Get-Content "C:\Users\Admin\Downloads\ai-trading-sentinel\logs\service.log" -Tail 50

# Monitor logs in real-time
Get-Content "C:\Users\Admin\Downloads\ai-trading-sentinel\logs\service.log" -Wait
```

### Service Configuration
```powershell
# Set service to start automatically
Set-Service -Name "AITradingSentinel" -StartupType Automatic

# Set service recovery options
sc.exe failure AITradingSentinel reset= 86400 actions= restart/60000/restart/60000/restart/60000
```

## Monitoring and Maintenance

### Health Checks
```powershell
# Run health check
python health_check.py

# Performance monitoring
python monitor_performance.py

# Continuous monitoring
python monitor_performance.py --continuous --interval 300
```

### Log Rotation
Create `rotate_logs.ps1`:
```powershell
# Log rotation script
$LogDir = "C:\Users\Admin\Downloads\ai-trading-sentinel\logs"
$MaxSize = 100MB
$MaxFiles = 10

Get-ChildItem $LogDir -Filter "*.log" | ForEach-Object {
    if ($_.Length -gt $MaxSize) {
        $BaseName = $_.BaseName
        $Extension = $_.Extension
        
        # Rotate existing files
        for ($i = $MaxFiles; $i -gt 1; $i--) {
            $OldFile = "$LogDir\$BaseName.$($i-1)$Extension"
            $NewFile = "$LogDir\$BaseName.$i$Extension"
            
            if (Test-Path $OldFile) {
                Move-Item $OldFile $NewFile -Force
            }
        }
        
        # Move current log to .1
        Move-Item $_.FullName "$LogDir\$BaseName.1$Extension" -Force
        
        # Restart service to create new log
        Restart-Service -Name "AITradingSentinel" -Force
    }
}
```

### Scheduled Tasks
```powershell
# Create scheduled task for log rotation
$Action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File C:\Users\Admin\Downloads\ai-trading-sentinel\rotate_logs.ps1"
$Trigger = New-ScheduledTaskTrigger -Daily -At "02:00AM"
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName "AITradingSentinel-LogRotation" -Action $Action -Trigger $Trigger -Settings $Settings -User "SYSTEM"
```

## Troubleshooting

### Common Issues

#### Service Won't Start
1. Check Windows Event Viewer
2. Verify Python path and virtual environment
3. Check file permissions
4. Ensure all dependencies are installed

#### Service Crashes
1. Check service logs
2. Run health check
3. Verify .env configuration
4. Check system resources

#### Performance Issues
1. Monitor CPU and memory usage
2. Check log file sizes
3. Verify network connectivity
4. Review trading platform status

### Diagnostic Commands
```powershell
# Check service details
Get-WmiObject -Class Win32_Service -Filter "Name='AITradingSentinel'"

# View Windows Event Logs
Get-EventLog -LogName Application -Source "AITradingSentinel" -Newest 10

# Check process information
Get-Process -Name "python" | Where-Object {$_.Path -like "*ai-trading-sentinel*"}

# Network connectivity test
Test-NetConnection -ComputerName "bulenox.com" -Port 443
```

## Security Considerations

### File Permissions
```powershell
# Set secure permissions on .env file
icacls ".env" /grant:r "SYSTEM:F" /grant:r "Administrators:F" /inheritance:r

# Set permissions on logs directory
icacls "logs" /grant "SYSTEM:F" /grant "Administrators:F" /grant "Users:R"
```

### Service Account
- Run service under dedicated service account
- Grant minimal required permissions
- Use strong passwords
- Enable audit logging

## Backup and Recovery

### Configuration Backup
```powershell
# Create backup script
$BackupDir = "C:\Backups\AITradingSentinel\$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $BackupDir -Force

# Backup configuration
Copy-Item ".env" $BackupDir
Copy-Item "*.py" $BackupDir
Copy-Item "logs\*.log" $BackupDir
Copy-Item "data\*" $BackupDir -Recurse
```

### Service Recovery
```powershell
# Export service configuration
sc.exe qc AITradingSentinel > service_config_backup.txt

# Remove and reinstall service if needed
sc.exe delete AITradingSentinel
# Then reinstall using one of the methods above
```

## Performance Optimization

### System Tuning
1. Disable Windows Defender real-time scanning for project directory
2. Set high performance power plan
3. Increase virtual memory if needed
4. Configure Windows Update to avoid automatic restarts

### Service Optimization
```powershell
# Set service priority
wmic process where name="python.exe" CALL setpriority "above normal"

# Configure service recovery
sc.exe failure AITradingSentinel reset= 0 actions= restart/5000/restart/10000/restart/30000
```

## Next Steps

1. **Test Service**: Verify service starts and runs correctly
2. **Monitor Performance**: Use monitoring tools to track performance
3. **Setup Alerts**: Configure email/SMS alerts for critical events
4. **Schedule Maintenance**: Plan regular maintenance windows
5. **Document Changes**: Keep track of configuration changes

## Support

For issues or questions:
1. Check logs in `logs/` directory
2. Run health check: `python health_check.py`
3. Review this guide
4. Check Windows Event Viewer
5. Contact system administrator

---

**⚠️ Important Notes:**
- Always test in development environment first
- Keep backups of configuration files
- Monitor service performance regularly
- Update dependencies periodically
- Follow security best practices