# 🔧 SYSTEMD SERVICE FIX - CORRECT FLASK APP REFERENCE

## Root Cause
The `trading-bot.service` is referencing `main:app` instead of `backend_main:app`.

## IMMEDIATE FIX COMMANDS

### 1. Stop Current Service
```bash
sudo systemctl stop trading-bot.service
sudo systemctl disable trading-bot.service
```

### 2. Create Correct Service File
```bash
sudo tee /etc/systemd/system/trading-bot.service > /dev/null <<EOF
[Unit]
Description=AI Trading Sentinel Backend (Flask + Gunicorn)
After=network.target

[Service]
Type=notify
User=root
Group=root
WorkingDirectory=/root/ai-trading-sentinel
Environment=PATH=/root/ai-trading-sentinel/venv/bin
ExecStart=/root/ai-trading-sentinel/venv/bin/gunicorn -w 2 -b 0.0.0.0:8080 backend_main:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### 3. Reload and Start Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable trading-bot.service
sudo systemctl start trading-bot.service
```

### 4. Verify Success
```bash
sudo systemctl status trading-bot.service
curl http://localhost:8080/api/status
```

## Expected Success Output
- Service status: `active (running)`
- No "Failed to find attribute 'app'" errors
- API returns JSON response: `{"status": "running", ...}`

## If Still Failing
```bash
# Check service logs
sudo journalctl -u trading-bot.service -f

# Test manual execution
cd /root/ai-trading-sentinel
source venv/bin/activate
gunicorn -w 1 -b 0.0.0.0:8080 backend_main:app
```