# 🚨 EXEC ERROR 203 - GUNICORN PATH ISSUE

## 🔍 **DIAGNOSIS**

Your logs show:
- ❌ **Exit Code 203/EXEC**: Command cannot be executed
- ❌ **Process Failed**: `/root/ai-trading-sentinel/venv/bin/gunicorn` not found or not executable
- ❌ **Service Auto-Restarting**: Continuously failing

## 🎯 **ROOT CAUSE**

The issue is likely one of these:
1. **Virtual environment path wrong**
2. **Gunicorn not installed in venv**
3. **main.py file missing or incorrect**
4. **Working directory wrong**

## 🚀 **DIAGNOSTIC COMMANDS**

Run these via Termius SSH to identify the exact issue:

### 1. 🔍 **CHECK FILE PATHS**
```bash
# Check if virtual environment exists
ls -la /root/ai-trading-sentinel/venv/
ls -la /root/ai-trading-sentinel/venv/bin/

# Check if gunicorn is installed
/root/ai-trading-sentinel/venv/bin/pip list | grep gunicorn

# Check if main.py exists
ls -la /root/ai-trading-sentinel/main.py

# Check current working directory
pwd
ls -la /root/ai-trading-sentinel/
```

### 2. 🛠️ **INSTALL MISSING DEPENDENCIES**
```bash
# Navigate to project directory
cd /root/ai-trading-sentinel

# Activate virtual environment
source venv/bin/activate

# Install gunicorn if missing
pip install gunicorn

# Verify installation
which gunicorn
gunicorn --version
```

### 3. 🧪 **TEST MANUAL EXECUTION**
```bash
# Try running gunicorn manually
cd /root/ai-trading-sentinel
source venv/bin/activate
gunicorn -w 2 -b 0.0.0.0:8080 main:app

# If that fails, try with python -m
python -m gunicorn -w 2 -b 0.0.0.0:8080 main:app
```

### 4. 🔧 **ALTERNATIVE SERVICE CONFIGURATION**

If gunicorn path is different, update the service:

```bash
# Find correct gunicorn path
find /root -name "gunicorn" 2>/dev/null

# Or use python -m approach
sudo tee /etc/systemd/system/trading-bot.service > /dev/null << 'EOF'
[Unit]
Description=AI Trading Sentinel Backend (Flask + Gunicorn)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/ai-trading-sentinel
ExecStart=/root/ai-trading-sentinel/venv/bin/python -m gunicorn -w 2 -b 0.0.0.0:8080 main:app
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart trading-bot.service
sudo systemctl status trading-bot.service --no-pager
```

### 5. 🔍 **CHECK MAIN.PY CONTENT**
```bash
# Verify main.py has the correct Flask app
head -20 /root/ai-trading-sentinel/main.py

# Look for 'app = ' line
grep -n "app = " /root/ai-trading-sentinel/main.py
```

## 🎯 **EXPECTED FIXES**

### ✅ **If Virtual Environment Missing:**
```bash
cd /root/ai-trading-sentinel
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

### ✅ **If Gunicorn Missing:**
```bash
source /root/ai-trading-sentinel/venv/bin/activate
pip install gunicorn flask
```

### ✅ **If main.py Wrong:**
Ensure main.py contains:
```python
from flask import Flask
app = Flask(__name__)

@app.route('/api/status')
def status():
    return {'status': 'ok'}

if __name__ == '__main__':
    app.run()
```

## 🚨 **IMMEDIATE ACTION**

1. **Run diagnostic commands** to identify missing components
2. **Install missing dependencies** (likely gunicorn)
3. **Update service file** with correct paths
4. **Test manual execution** before service restart
5. **Report results** for next steps

---
**🎯 GOAL**: Fix the EXEC error by ensuring all paths and dependencies are correct