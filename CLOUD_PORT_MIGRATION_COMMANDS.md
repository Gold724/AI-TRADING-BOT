# 🚀 CLOUD PORT MIGRATION - Immediate Commands

## **CRITICAL: Execute via Termius SSH**

### **🎯 PROBLEM IDENTIFIED**
- **Current Issue:** `trading-bot.service` failing with "Address already in use" on port 5000
- **Root Cause:** Port 5000 conflicts with system services (macOS AirPlay, etc.)
- **Solution:** Migrate to enterprise-standard port 8080

### **📋 IMMEDIATE MIGRATION STEPS**

#### **Step 1: Stop Conflicting Services**
```bash
# Kill any process using port 5000
sudo lsof -ti:5000 | xargs sudo kill -9 2>/dev/null || true

# Stop current services
sudo systemctl stop trading-bot.service 2>/dev/null || true
sudo systemctl stop trae.service 2>/dev/null || true
```

#### **Step 2: Update Service Configuration**
```bash
# Create new trading-bot service with port 8080
sudo tee /etc/systemd/system/trading-bot.service > /dev/null << 'EOF'
[Unit]
Description=AI Trading Sentinel Backend (Flask + Gunicorn)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/ai-trading-sentinel
ExecStart=/root/ai-trading-sentinel/venv/bin/gunicorn -w 2 -b 0.0.0.0:8080 main:app
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1
StandardOutput=journal
StandardError=journal
LogsDirectory=trae
RuntimeDirectory=trae
RuntimeDirectoryMode=0755
StartLimitIntervalSec=300
StartLimitBurst=5

[Install]
WantedBy=multi-user.target
EOF
```

#### **Step 3: Update Nginx Configuration**
```bash
# Update Nginx to proxy to port 8080
sudo tee /etc/nginx/sites-available/default > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;

    # Frontend (if exists)
    location / {
        try_files $uri $uri/ @backend;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8080/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # Fallback to backend for all other requests
    location @backend {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
```

#### **Step 4: Reload and Start Services**
```bash
# Reload systemd configuration
sudo systemctl daemon-reload

# Test Nginx configuration
sudo nginx -t

# Restart services
sudo systemctl restart nginx
sudo systemctl enable trading-bot.service
sudo systemctl start trading-bot.service
```

#### **Step 5: Verify Migration Success**
```bash
# Check service status
sudo systemctl status nginx trading-bot.service --no-pager

# Check port binding
sudo netstat -tlnp | grep :8080

# Test API endpoint
curl -I http://localhost:8080/
curl -I http://localhost/api/
```

### **🔍 TROUBLESHOOTING**

#### **If trading-bot.service fails:**
```bash
# Check logs
sudo journalctl -u trading-bot.service -f --no-pager -n 20

# Manual test
cd /root/ai-trading-sentinel
source venv/bin/activate
python main.py
```

#### **If Nginx fails:**
```bash
# Check Nginx logs
sudo tail -f /var/log/nginx/error.log

# Test configuration
sudo nginx -t
```

### **✅ SUCCESS INDICATORS**
- `sudo systemctl status trading-bot.service` shows **active (running)**
- `sudo netstat -tlnp | grep :8080` shows Gunicorn listening
- `curl -I http://localhost:8080/` returns **HTTP 200 OK**
- `curl -I http://localhost/api/` returns **HTTP 200 OK** (via Nginx proxy)

### **🎯 EXTERNAL VERIFICATION**
After successful migration, test from your local machine:
```powershell
# Test direct API access (replace YOUR_VPS_IP)
Invoke-WebRequest -Uri "http://YOUR_VPS_IP:8080/" -Method HEAD
Invoke-WebRequest -Uri "http://YOUR_VPS_IP/api/" -Method HEAD
```

### **📊 MIGRATION BENEFITS**
- ✅ **Zero Port Conflicts:** Port 8080 is enterprise-standard
- ✅ **Production Ready:** Cloud services expect this port range
- ✅ **Scalable:** Load balancer compatible
- ✅ **Container Ready:** Docker/K8s standard allocation
- ✅ **Firewall Friendly:** Standard web application port

---

**🚨 EXECUTE THESE COMMANDS IN ORDER VIA TERMIUS SSH**