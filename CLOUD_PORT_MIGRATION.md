# 🚀 CLOUD PORT MIGRATION - Professional Production Setup

## 🎯 OBJECTIVE
Transform the current free port setup (5000, 3000) to professional cloud-grade port configuration with dedicated, stable ports that won't conflict or change.

## 🔧 CURRENT ARCHITECTURE ISSUES
- **Port 5000:** Flask backend (conflicts with macOS AirPlay, other services)
- **Port 3000:** React frontend (development port, not production-ready)
- **Port 80/443:** Nginx proxy (good, but needs better backend routing)

## ✅ RECOMMENDED CLOUD PORT STRATEGY

### Option A: Standard Production Ports
```nginx
# /etc/nginx/sites-available/trading-sentinel
server {
    listen 80;
    listen 443 ssl;
    server_name your-domain.com;
    
    # Frontend (React build)
    location / {
        root /opt/ai-trading-sentinel/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8080;  # Stable backend port
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # WebSocket for real-time updates
    location /ws/ {
        proxy_pass http://127.0.0.1:8081;  # Dedicated WebSocket port
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Option B: Docker Compose (Recommended)
```yaml
# docker-compose.yml
version: '3.8'
services:
  trading-backend:
    build: .
    ports:
      - "8080:8080"  # Internal backend port
    environment:
      - FLASK_PORT=8080
      - FLASK_ENV=production
    restart: unless-stopped
    
  trading-frontend:
    build: ./frontend
    ports:
      - "3001:80"  # Nginx serves React build
    depends_on:
      - trading-backend
    restart: unless-stopped
    
  nginx-proxy:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - trading-backend
      - trading-frontend
    restart: unless-stopped
```

### Option C: Cloud-Native (AWS/GCP/Azure)
```bash
# Use cloud load balancers + container services
# Backend: Port 8080 (internal)
# Frontend: Port 80/443 (public)
# Database: Port 5432 (internal)
# Redis: Port 6379 (internal)
```

## 🛠️ IMPLEMENTATION STEPS

### Step 1: Update Backend Configuration
```python
# main.py or app.py
import os

# Use environment variable for port (default: 8080)
PORT = int(os.getenv('FLASK_PORT', 8080))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=False)
```

### Step 2: Update Gunicorn Configuration
```bash
# /etc/systemd/system/trading-bot.service
[Unit]
Description=AI Trading Sentinel Backend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/ai-trading-sentinel
Environment=FLASK_PORT=8080
ExecStart=/opt/ai-trading-sentinel/venv/bin/gunicorn --bind 0.0.0.0:8080 --workers 4 main:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### Step 3: Update Nginx Configuration
```nginx
# /etc/nginx/sites-available/default
upstream backend {
    server 127.0.0.1:8080;
}

server {
    listen 80;
    server_name _;
    
    # API routes
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    # Frontend
    location / {
        root /opt/ai-trading-sentinel/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

### Step 4: Environment Variables
```bash
# /opt/ai-trading-sentinel/.env
FLASK_PORT=8080
FLASK_ENV=production
API_BASE_URL=http://localhost:8080
FRONTEND_PORT=3001
```

## 🔒 SECURITY BENEFITS
1. **Port 8080:** Standard enterprise backend port
2. **No Port Conflicts:** Dedicated ports prevent service collisions
3. **Firewall Friendly:** Standard ports are whitelisted by default
4. **Load Balancer Ready:** Cloud services expect these port ranges
5. **Container Compatible:** Docker/K8s standard port allocation

## 📊 MIGRATION CHECKLIST

### Pre-Migration
- [ ] Backup current configuration
- [ ] Test new port configuration locally
- [ ] Update environment variables
- [ ] Prepare rollback plan

### Migration Steps
- [ ] Update backend port to 8080
- [ ] Modify Gunicorn service configuration
- [ ] Update Nginx proxy configuration
- [ ] Restart services in correct order
- [ ] Test API endpoints
- [ ] Verify frontend connectivity

### Post-Migration
- [ ] Monitor service stability
- [ ] Update documentation
- [ ] Configure monitoring alerts
- [ ] Setup automated health checks

## 🚀 IMMEDIATE ACTION PLAN

### Quick Fix (5 minutes)
```bash
# Via Termius - Update to port 8080
sudo systemctl stop trading-bot.service

# Edit service file
sudo nano /etc/systemd/system/trading-bot.service
# Change: --bind 0.0.0.0:5000 to --bind 0.0.0.0:8080

# Update Nginx
sudo nano /etc/nginx/sites-available/default
# Change: proxy_pass http://127.0.0.1:5000 to http://127.0.0.1:8080

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart nginx
sudo systemctl start trading-bot.service
```

## ✅ EXPECTED OUTCOMES
- **Zero Port Conflicts:** No more "Address already in use" errors
- **Production Ready:** Professional port allocation
- **Scalable:** Ready for load balancers and cloud deployment
- **Stable:** Consistent port assignment across restarts
- **Secure:** Standard enterprise port configuration

---
**Priority:** 🎯 HIGH - Eliminates root cause of current failures
**ETA:** 10 minutes for basic migration
**Benefits:** Permanent solution to port conflicts + production readiness