
# 🤖 TradeBot Sentinel - Contabo VPS Deployment Instructions

Generated: 2025-08-13 19:27:47

## 📋 Deployment Steps

### 1. 📦 Transfer Files to VPS

```bash
# Option A: Using SCP (if you have SSH access)
scp -r ai-trading-sentinel/ root@YOUR_VPS_IP:/home/tradebot/

# Option B: Using rsync (recommended)
rsync -avz --progress ai-trading-sentinel/ root@YOUR_VPS_IP:/home/tradebot/ai-trading-sentinel/

# Option C: Manual upload via FTP/SFTP client
# Upload the entire ai-trading-sentinel directory to /home/tradebot/
```

### 2. 🔧 Setup VPS Environment

```bash
# SSH into your VPS
ssh root@YOUR_VPS_IP

# Run the setup script
cd /home/tradebot/ai-trading-sentinel
chmod +x setup_vps.sh
./setup_vps.sh
```

### 3. ⚙️ Configure Environment

```bash
# Copy the .env file (already configured with Bulenox credentials)
cp deployment_package/.env /home/tradebot/ai-trading-sentinel/.env

# Verify configuration
cat /home/tradebot/ai-trading-sentinel/.env
```

### 4. 🚀 Install and Start Service

```bash
# Copy systemd service file
sudo cp deployment_package/tradebot-sentinel.service /etc/systemd/system/

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable tradebot-sentinel.service
sudo systemctl start tradebot-sentinel.service

# Check service status
sudo systemctl status tradebot-sentinel.service
```

### 5. 📊 Monitor and Verify

```bash
# View real-time logs
tail -f /home/tradebot/ai-trading-sentinel/logs/tradebot.log

# Check error logs
tail -f /home/tradebot/ai-trading-sentinel/logs/tradebot_error.log

# Verify directories
ls -la /home/tradebot/ai-trading-sentinel/logs/
ls -la /home/tradebot/ai-trading-sentinel/logs/curls/
ls -la /home/tradebot/ai-trading-sentinel/logs/json/
```

## ✅ Verification Checklist

- [ ] Files transferred to VPS
- [ ] .env file configured with Bulenox credentials:
  - BULENOX_USERNAME=BX64883
  - BULENOX_PASSWORD=XujhMzFf6K
- [ ] Dependencies installed from requirements.txt
- [ ] Headless Chrome working with persistent profiles
- [ ] Log directories exist and are writable:
  - /home/tradebot/ai-trading-sentinel/logs/
  - /home/tradebot/ai-trading-sentinel/logs/curls/
  - /home/tradebot/ai-trading-sentinel/logs/json/
- [ ] Systemd service running
- [ ] Automation ready for trade execution

## 🔧 Troubleshooting

### Chrome Issues
```bash
# Test Chrome manually
export DISPLAY=:99
Xvfb :99 -screen 0 1920x1080x24 &
google-chrome --headless --no-sandbox --disable-gpu --dump-dom https://www.google.com
```

### Permission Issues
```bash
# Fix permissions
sudo chown -R root:root /home/tradebot/ai-trading-sentinel
chmod -R 755 /home/tradebot/ai-trading-sentinel/logs
```

### Service Issues
```bash
# Restart service
sudo systemctl restart tradebot-sentinel.service

# View detailed logs
journalctl -u tradebot-sentinel.service -f
```

## 🎯 Ready for Automation!

Once deployment is complete, TradeBot Sentinel will be ready to:
- ✅ Login to Bulenox platform automatically
- ✅ Intercept and capture trade requests
- ✅ Generate cURL commands and Python code
- ✅ Execute trades via API
- ✅ Log all activities for monitoring

## 📞 Support

If you encounter any issues during deployment, check:
1. System logs: `journalctl -u tradebot-sentinel.service`
2. Application logs: `/home/tradebot/ai-trading-sentinel/logs/tradebot.log`
3. Chrome/Selenium logs in the application output

---

**TradeBot Sentinel** - Automated Trading Intelligence
