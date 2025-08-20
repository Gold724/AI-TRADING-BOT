# 🔧 BACKEND SERVICE FIX - Correct Flask App Reference

## Problem Identified
The `module_fix.sh` script revealed:
- ❌ `backend_main.py` is missing from root directory
- ✅ Flask app found in `./backend/main.py` 
- ❌ Service failing with exit code 4 (NOPERMISSION) using `main:app`
- ✅ Correct reference should be `backend.main:app`

## Solution: Update Systemd Service

### Step 1: Stop Current Service
```bash
sudo systemctl stop trading-bot.service
```

### Step 2: Create Corrected Service File
```bash
sudo tee /etc/systemd/system/trading-bot.service > /dev/null <<EOF
[Unit]
Description=AI Trading Sentinel Backend (Flask + Gunicorn)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/ai-trading-sentinel
Environment=PYTHONPATH=/root/ai-trading-sentinel
Environment=PYTHONUNBUFFERED=1
ExecStart=/root/ai-trading-sentinel/venv/bin/gunicorn -w 2 -b 0.0.0.0:8080 backend.main:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### Step 3: Test Module Import
```bash
cd /root/ai-trading-sentinel
source venv/bin/activate
python -c "from backend.main import app; print('✅ SUCCESS: backend.main:app found')"
```

### Step 4: Restart Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable trading-bot.service
sudo systemctl start trading-bot.service
```

### Step 5: Verify Service
```bash
# Check service status
sudo systemctl status trading-bot.service --no-pager -l

# Test API endpoint
curl http://localhost:8080/api/health
curl http://localhost:8080/
```

## Expected Results
- ✅ Service status: `active (running)`
- ✅ API responds with JSON data
- ✅ No module import errors in logs
- ✅ Flask backend accessible on port 8080

## Key Fix
**Changed from:** `main:app` → **To:** `backend.main:app`

This correctly references the Flask app in the `backend/main.py` file.