# 🚀 AI Trading Sentinel - VPS Deployment Instructions

## 📋 Pre-Deployment Checklist

### ✅ Local Environment Ready
- [x] All 12 core files validated and packaged
- [x] Trading scripts: `tradebot_sentinel_advanced_pro.py`, `login_bulenox_playwright.py`, `endpoint_validator.py`
- [x] Cross-platform launchers: `.sh`, `.ps1`, `.bat`
- [x] Utilities and configuration files ready
- [x] Deployment automation scripts created

### 🔧 VPS Requirements
- Ubuntu/Debian Linux VPS (Contambo VPS)
- SSH access with key authentication
- Python 3.8+ installed
- Root or sudo access
- Internet connectivity for package installation

## 🚀 Quick Deployment (3 Steps)

### Step 1: Configure VPS Connection
```bash
# Edit deploy_to_vps.sh
VPS_HOST="your-contambo-vps-ip"  # Replace with actual IP
VPS_USER="root"                  # Or your username
VPS_DIR="/root/AI-TRADING-BOT"   # Target directory
```

### Step 2: Deploy to VPS
```bash
# From the vps_deployment directory
chmod +x deploy_to_vps.sh
./deploy_to_vps.sh
```

### Step 3: Verify Deployment
```bash
# SSH to your VPS and run
ssh root@your-vps-ip
cd /root/AI-TRADING-BOT
python3 vps_environment_check.py
```

## 🔍 Manual Deployment (Alternative)

If automated deployment fails, follow these manual steps:

### 1. Create Directory Structure
```bash
ssh root@your-vps-ip
mkdir -p /root/AI-TRADING-BOT
```

### 2. Copy Files
```bash
# From local vps_deployment directory
scp -r trading_scripts/* root@your-vps-ip:/root/AI-TRADING-BOT/
scp -r launchers/* root@your-vps-ip:/root/AI-TRADING-BOT/
scp -r utilities/* root@your-vps-ip:/root/AI-TRADING-BOT/
scp -r config_files/* root@your-vps-ip:/root/AI-TRADING-BOT/
scp vps_environment_check.py root@your-vps-ip:/root/AI-TRADING-BOT/
```

### 3. Set Permissions
```bash
ssh root@your-vps-ip "chmod +x /root/AI-TRADING-BOT/*.py /root/AI-TRADING-BOT/*.sh"
```

### 4. Install Dependencies
```bash
ssh root@your-vps-ip "cd /root/AI-TRADING-BOT && pip3 install -r requirements.txt"
ssh root@your-vps-ip "cd /root/AI-TRADING-BOT && python3 -m playwright install"
```

## ⚙️ Environment Configuration

### Set Trading Credentials
```bash
# On VPS, create .env file
echo "BULENOX_USERNAME=your_username" > /root/AI-TRADING-BOT/.env
echo "BULENOX_PASSWORD=your_password" >> /root/AI-TRADING-BOT/.env
chmod 600 /root/AI-TRADING-BOT/.env
```

### Verify Environment
```bash
cd /root/AI-TRADING-BOT
python3 vps_environment_check.py
```

## 🎯 Testing Deployment

### Test Core Trading Script
```bash
# Test headless mode (recommended for VPS)
cd /root/AI-TRADING-BOT
python3 tradebot_sentinel_advanced_pro.py --headless
```

### Test Full Trading Workflow
```bash
# Use the bash launcher for complete workflow
cd /root/AI-TRADING-BOT
./live_trading_launcher.sh
```

## 📊 Deployment Verification

### ✅ Success Indicators
- [ ] All 12 files copied successfully
- [ ] Python dependencies installed
- [ ] Playwright browsers installed
- [ ] Environment variables set
- [ ] Core script runs without errors
- [ ] Network interception working
- [ ] cURL capture functional

### 🔧 Troubleshooting

**Permission Denied:**
```bash
chmod +x /root/AI-TRADING-BOT/*.py /root/AI-TRADING-BOT/*.sh
```

**Missing Dependencies:**
```bash
pip3 install --upgrade pip
pip3 install -r requirements.txt
python3 -m playwright install
```

**Browser Issues:**
```bash
python3 -m playwright install-deps
```

## 🚀 Production Launch

Once deployment is verified:

### Option 1: Direct Execution
```bash
cd /root/AI-TRADING-BOT
python3 tradebot_sentinel_advanced_pro.py --headless
```

### Option 2: Full Workflow (Recommended)
```bash
cd /root/AI-TRADING-BOT
./live_trading_launcher.sh
```

### Option 3: Background Process
```bash
cd /root/AI-TRADING-BOT
nohup ./live_trading_launcher.sh > trading.log 2>&1 &
```

## 📁 File Structure on VPS

```
/root/AI-TRADING-BOT/
├── tradebot_sentinel_advanced_pro.py    # Main trading bot
├── tradebot_sentinel_playwright.py      # Alternative version
├── login_bulenox_playwright.py          # Login automation
├── endpoint_validator.py                # Endpoint validation
├── live_trading_launcher.sh             # Bash launcher
├── live_trading_launcher.ps1            # PowerShell launcher
├── live_trading_launcher.bat            # Batch launcher
├── curl_to_python.py                    # cURL converter
├── requirements.txt                      # Dependencies
├── verify_setup.py                      # Setup verification
├── vps_environment_check.py             # Environment checker
├── secrets.json                         # Configuration
├── .env                                 # Environment variables
└── logs/                                # Generated logs
```

## 🎉 Deployment Complete!

Your AI Trading Sentinel is now ready for production on the Contambo VPS. The system includes:

- ✅ **Automated Login**: Secure authentication with environment variables
- ✅ **Network Interception**: Captures all trading requests
- ✅ **cURL Generation**: Saves trade commands for analysis
- ✅ **Python Conversion**: Auto-converts cURL to Python requests
- ✅ **Cross-Platform**: Works on Linux, Windows, macOS
- ✅ **Auto-Restart**: Continuous operation with error recovery
- ✅ **Comprehensive Logging**: Full audit trail of all operations

**Next Steps:**
1. Set your trading credentials in `.env`
2. Run `./live_trading_launcher.sh` to start trading
3. Monitor logs in the `logs/` directory
4. Use `vps_environment_check.py` for health checks

**Support:** All scripts include verbose logging and error handling for easy troubleshooting.