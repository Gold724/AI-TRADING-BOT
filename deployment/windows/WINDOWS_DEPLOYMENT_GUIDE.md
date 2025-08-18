# TradeBot Sentinel - Windows Deployment Guide

## 🚀 Quick Start for Windows

This guide will help you deploy TradeBot Sentinel on Windows using PowerShell scripts and native Windows services.

## 📋 Prerequisites

### System Requirements
- **OS**: Windows 10/11 or Windows Server 2019/2022
- **RAM**: 4GB+ (8GB recommended)
- **Storage**: 10GB+ free space
- **CPU**: 2+ cores recommended
- **Network**: Stable internet connection

### Required Software
1. **Python 3.8+** - [Download from python.org](https://www.python.org/downloads/)
2. **Git** - [Download from git-scm.com](https://git-scm.com/download/win)
3. **PowerShell 5.1+** (included with Windows)
4. **NSSM** (optional, for better service management) - [Download from nssm.cc](https://nssm.cc/download)

### Optional Tools
- **Docker Desktop** - For containerized deployment
- **WSL2** - For Linux-like environment
- **Visual Studio Code** - For development

## 🛠️ Installation Steps

### Step 1: Clone the Repository

```powershell
# Open PowerShell as Administrator
cd C:\Users\$env:USERNAME\Downloads
git clone https://github.com/your-username/ai-trading-sentinel.git
cd ai-trading-sentinel
```

### Step 2: Run Windows Setup Script

```powershell
# Navigate to Windows deployment directory
cd deployment\windows

# Run the setup script
.\setup-windows-deployment.ps1
```

This script will:
- Check system requirements
- Install Python dependencies
- Set up virtual environment
- Configure basic settings
- Offer WSL2/Docker setup options

### Step 3: Configure Environment

```powershell
# Copy and edit environment file
cp .env.example .env
notepad .env
```

Configure your trading credentials:
```env
# Trading Platform Configuration
TRADING_PLATFORM=your_platform
TRADING_USERNAME=your_username
TRADING_PASSWORD=your_password

# API Configuration
API_HOST=localhost
API_PORT=8000

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/tradebot.log

# Security
SECRET_KEY=your_secret_key_here
```

### Step 4: Verify Installation

```powershell
# Run verification script
.\verify-windows-deployment.ps1
```

This will check:
- Python environment
- Required packages
- Project files
- Browser setup
- API endpoints
- System resources

## 🔧 Service Management

### Option 1: Using NSSM (Recommended)

#### Install NSSM
1. Download NSSM from [nssm.cc](https://nssm.cc/download)
2. Extract to `C:\nssm` or add to PATH
3. Verify installation: `nssm version`

#### Install TradeBot as Service

```powershell
# Install service using NSSM
.\service-wrapper.ps1 install -UseNSSM

# Start the service
.\service-wrapper.ps1 start

# Check status
.\service-wrapper.ps1 status
```

### Option 2: Using Task Scheduler

```powershell
# Install as scheduled task
.\service-wrapper.ps1 install -UseTaskScheduler

# Start the task
.\service-wrapper.ps1 start
```

### Service Management Commands

```powershell
# Start service
.\service-wrapper.ps1 start

# Stop service
.\service-wrapper.ps1 stop

# Restart service
.\service-wrapper.ps1 restart

# Check status
.\service-wrapper.ps1 status

# View logs
.\service-wrapper.ps1 logs

# Remove service
.\service-wrapper.ps1 remove
```

## 📊 Monitoring and Health Checks

### Start Health Monitor

```powershell
# Start monitoring in background
.\health-monitor-windows.ps1 start -Daemon

# Check monitoring status
.\health-monitor-windows.ps1 status

# Test alerts
.\health-monitor-windows.ps1 test-alert
```

### Configure Alerts

Create `health-config.json`:
```json
{
  "thresholds": {
    "cpu_percent": 80,
    "memory_percent": 85,
    "disk_percent": 90,
    "api_timeout_seconds": 30,
    "max_failed_trades": 5,
    "error_rate_percent": 10
  },
  "alerts": {
    "slack_webhook": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
    "email_smtp": "smtp.gmail.com",
    "email_from": "alerts@yourcompany.com",
    "email_to": "admin@yourcompany.com",
    "cooldown_minutes": 15
  },
  "monitoring": {
    "check_interval": 60,
    "log_retention_days": 7,
    "enable_performance_counters": true,
    "enable_api_checks": true,
    "enable_process_monitoring": true
  }
}
```

## 🐳 Docker Deployment (Alternative)

### Prerequisites
- Docker Desktop for Windows
- WSL2 enabled

### Build and Run

```powershell
# Build Docker image
docker build -t tradebot-sentinel .

# Run container
docker run -d --name tradebot-sentinel `
  -p 8000:8000 `
  -v ${PWD}/logs:/app/logs `
  -v ${PWD}/.env:/app/.env `
  --restart unless-stopped `
  tradebot-sentinel

# Check logs
docker logs -f tradebot-sentinel
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'
services:
  tradebot:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/app/logs
      - ./.env:/app/.env
    restart: unless-stopped
    environment:
      - PYTHONUNBUFFERED=1
```

```powershell
# Start with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## 🔒 Security Configuration

### Windows Firewall

```powershell
# Allow TradeBot through firewall
New-NetFirewallRule -DisplayName "TradeBot Sentinel" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow

# Block external access (optional)
New-NetFirewallRule -DisplayName "TradeBot Sentinel Local Only" -Direction Inbound -Protocol TCP -LocalPort 8000 -RemoteAddress LocalSubnet -Action Allow
```

### User Account Control

```powershell
# Create dedicated user for service (optional)
net user tradebotuser /add /passwordreq:yes
net localgroup "Log on as a service" tradebotuser /add
```

### Environment Security

```powershell
# Set secure permissions on .env file
icacls .env /grant:r "$env:USERNAME:(R)" /inheritance:r
icacls .env /remove "Users"
```

## 📁 Directory Structure

```
ai-trading-sentinel/
├── deployment/
│   └── windows/
│       ├── setup-windows-deployment.ps1
│       ├── verify-windows-deployment.ps1
│       ├── health-monitor-windows.ps1
│       ├── service-wrapper.ps1
│       └── WINDOWS_DEPLOYMENT_GUIDE.md
├── logs/
│   ├── tradebot.log
│   ├── service.log
│   └── health-monitor.log
├── venv/
├── main.py
├── requirements.txt
├── .env
└── docker-compose.yml
```

## 🚨 Troubleshooting

### Common Issues

#### Python Not Found
```powershell
# Check Python installation
python --version

# Add Python to PATH if needed
$env:PATH += ";C:\Python39;C:\Python39\Scripts"
```

#### Service Won't Start
```powershell
# Check service logs
.\service-wrapper.ps1 logs

# Test manual execution
python main.py

# Check permissions
Get-Acl .env
```

#### Browser Automation Issues
```powershell
# Install Playwright browsers
playwright install chromium

# Test browser manually
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); browser = p.chromium.launch(); browser.close(); p.stop()"
```

#### Port Already in Use
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process (replace PID)
Stop-Process -Id <PID> -Force
```

### Log Locations

- **Application Logs**: `logs/tradebot.log`
- **Service Logs**: `logs/service.log`
- **Health Monitor**: `logs/health-monitor-YYYYMMDD.log`
- **Windows Event Log**: Event Viewer → Windows Logs → Application

### Performance Monitoring

```powershell
# Check system performance
Get-Counter "\Processor(_Total)\% Processor Time"
Get-Counter "\Memory\Available MBytes"

# Monitor TradeBot process
Get-Process python | Where-Object {$_.CommandLine -like "*main.py*"}
```

## 🔄 Updates and Maintenance

### Update TradeBot

```powershell
# Stop service
.\service-wrapper.ps1 stop

# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Start service
.\service-wrapper.ps1 start
```

### Backup Configuration

```powershell
# Create backup
$backupDir = "backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
New-Item -ItemType Directory $backupDir
Copy-Item .env, logs, health-config.json $backupDir -Recurse

# Compress backup
Compress-Archive -Path $backupDir -DestinationPath "$backupDir.zip"
```

### Log Rotation

```powershell
# Manual log rotation
Get-ChildItem logs\*.log | Where-Object {$_.Length -gt 10MB} | ForEach-Object {
    $newName = $_.BaseName + "-" + (Get-Date -Format "yyyyMMdd") + $_.Extension
    Rename-Item $_.FullName $newName
}
```

## 📞 Support

### Getting Help

1. **Check Logs**: Always check application and service logs first
2. **Run Verification**: Use `verify-windows-deployment.ps1` to diagnose issues
3. **Test Components**: Test individual components (Python, browser, API)
4. **Check Documentation**: Review this guide and inline script help

### Useful Commands

```powershell
# Show help for any script
.\script-name.ps1 -h

# Enable verbose output
.\script-name.ps1 -Verbose

# Test prerequisites
.\service-wrapper.ps1 test

# Generate verification report
.\verify-windows-deployment.ps1 > verification-report.txt
```

## 🎯 Next Steps

1. **Complete Setup**: Follow all installation steps
2. **Configure Trading**: Set up your trading platform credentials
3. **Test Functionality**: Run verification and test trades
4. **Setup Monitoring**: Configure health monitoring and alerts
5. **Schedule Backups**: Set up regular configuration backups
6. **Monitor Performance**: Keep an eye on system resources and logs

## 📚 Additional Resources

- [Python Windows Installation Guide](https://docs.python.org/3/using/windows.html)
- [NSSM Documentation](https://nssm.cc/usage)
- [PowerShell Documentation](https://docs.microsoft.com/en-us/powershell/)
- [Docker Desktop for Windows](https://docs.docker.com/desktop/windows/)
- [Windows Task Scheduler](https://docs.microsoft.com/en-us/windows/win32/taskschd/task-scheduler-start-page)

---

**Happy Trading! 🚀📈**

*Remember to always test in a safe environment before deploying to production trading accounts.*