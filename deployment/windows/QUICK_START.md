# 🚀 TradeBot Sentinel - Windows Quick Start

## ⚡ 5-Minute Setup

### Step 1: Run as Administrator

**Option A: Using Batch File (Easiest)**
```
1. Double-click: deployment\windows\run-as-admin.bat
2. Click "Yes" when Windows asks for permission
3. Follow the setup wizard
```

**Option B: Manual PowerShell**
```
1. Right-click on PowerShell icon
2. Select "Run as Administrator"
3. Navigate to: cd "C:\Users\Admin\Downloads\ai-trading-sentinel\deployment\windows"
4. Run: .\setup-windows-deployment.ps1
```

### Step 2: Configure Trading Credentials

```powershell
# Edit environment file
notepad ..\..\env.example
# Save as .env with your trading platform details
```

### Step 3: Verify Installation

```powershell
# Run verification (as Administrator)
.\verify-windows-deployment.ps1
```

### Step 4: Install as Windows Service

```powershell
# Install service (as Administrator)
.\service-wrapper.ps1 install

# Start service
.\service-wrapper.ps1 start

# Check status
.\service-wrapper.ps1 status
```

### Step 5: Start Monitoring

```powershell
# Start health monitoring
.\health-monitor-windows.ps1 start -Daemon
```

## 🎯 What Each Script Does

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `run-as-admin.bat` | Launch PowerShell as Admin | First time setup |
| `setup-windows-deployment.ps1` | Install dependencies & setup | Initial deployment |
| `verify-windows-deployment.ps1` | Check if everything works | After setup/changes |
| `service-wrapper.ps1` | Manage Windows service | Start/stop/install service |
| `health-monitor-windows.ps1` | Monitor system health | Ongoing monitoring |

## 🔧 Common Commands

```powershell
# Service Management
.\service-wrapper.ps1 start     # Start TradeBot
.\service-wrapper.ps1 stop      # Stop TradeBot
.\service-wrapper.ps1 restart   # Restart TradeBot
.\service-wrapper.ps1 status    # Check status
.\service-wrapper.ps1 logs      # View logs

# Health Monitoring
.\health-monitor-windows.ps1 status      # Check monitor status
.\health-monitor-windows.ps1 test-alert  # Test alerts

# Verification
.\verify-windows-deployment.ps1          # Full system check
.\verify-windows-deployment.ps1 -SkipBrowser  # Skip browser tests
```

## 🚨 Troubleshooting

### "Execution Policy" Error
```powershell
# Run this first:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### "Access Denied" Error
```
1. Right-click PowerShell → "Run as Administrator"
2. Or use run-as-admin.bat
```

### Service Won't Start
```powershell
# Check what's wrong:
.\service-wrapper.ps1 logs
.\verify-windows-deployment.ps1
```

### Python Not Found
```powershell
# Install Python from: https://python.org/downloads/
# Make sure to check "Add to PATH" during installation
```

## 📊 Monitoring Dashboard

Once running, access the web interface at:
- **Local**: http://localhost:8000
- **API**: http://localhost:8000/api/status
- **Logs**: Check `logs/` folder

## 🔒 Security Notes

- Always run setup scripts as Administrator
- Keep your `.env` file secure (contains trading credentials)
- Monitor the `logs/` folder for any issues
- Use Windows Firewall to restrict access if needed

## 📞 Need Help?

1. **Check Logs**: `logs/tradebot.log`
2. **Run Verification**: `.\verify-windows-deployment.ps1`
3. **View Service Status**: `.\service-wrapper.ps1 status`
4. **Test System**: `.\health-monitor-windows.ps1 test-alert`

---

**Ready to Trade! 🚀📈**

*Remember: Always test with small amounts first!*