# 🚀 AI Trading Sentinel - Manual VPS Deployment Guide

## Prerequisites
- Access to VPS via Termius or SSH client
- VPS IP: `185.244.214.70`
- Backend already running on port 5000

## Step 1: Upload Files to VPS

### Option A: Using SCP from Windows
```bash
# Upload frontend deployment
scp frontend-deployment.tar.gz root@185.244.214.70:/root/

# Upload Nginx config
scp nginx-frontend.conf root@185.244.214.70:/root/

# Upload monitoring setup script
scp monitoring_setup.sh root@185.244.214.70:/root/

# Upload verification script
scp verify_deployment.sh root@185.244.214.70:/root/
```

### Option B: Manual File Transfer via Termius
1. Open Termius and connect to your VPS
2. Use Termius file transfer feature to upload:
   - `frontend-deployment.tar.gz`
   - `nginx-frontend.conf`
   - `monitoring_setup.sh`
   - `verify_deployment.sh`

## Step 2: Execute Commands on VPS

Connect to your VPS via Termius and run these commands:

### 2.1 Extract Frontend Files
```bash
# Navigate to root directory
cd /root

# Create backup of existing web files
sudo mkdir -p /var/www/html/backup
sudo cp -r /var/www/html/* /var/www/html/backup/ 2>/dev/null || true

# Extract frontend files
sudo tar -xzf frontend-deployment.tar.gz -C /var/www/html/

# Set proper permissions
sudo chown -R www-data:www-data /var/www/html/
sudo chmod -R 755 /var/www/html/

echo "✅ Frontend files extracted successfully"
```

### 2.2 Configure Nginx
```bash
# Copy Nginx configuration
sudo cp nginx-frontend.conf /etc/nginx/sites-available/ai-trading-sentinel

# Enable the site
sudo ln -sf /etc/nginx/sites-available/ai-trading-sentinel /etc/nginx/sites-enabled/

# Remove default site if exists
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx

echo "✅ Nginx configured successfully"
```

### 2.3 Setup 24/7 Monitoring
```bash
# Make monitoring script executable
chmod +x monitoring_setup.sh

# Run monitoring setup
sudo ./monitoring_setup.sh

echo "✅ Monitoring system configured successfully"
```

### 2.4 Verify Deployment
```bash
# Make verification script executable
chmod +x verify_deployment.sh

# Run deployment verification
./verify_deployment.sh

echo "✅ Deployment verification completed"
```

### 2.5 Final Status Check
```bash
# Check all services
echo "=== Service Status ==="
sudo systemctl status nginx
sudo systemctl status ai-trading-backend
sudo systemctl status monitoring-dashboard

echo "=== Port Status ==="
sudo netstat -tlnp | grep -E ':(80|5000|8080)'

echo "=== Test Endpoints ==="
curl -s http://localhost/ | head -10
curl -s http://localhost/api/health
curl -s http://localhost:8080/
```

## Step 3: Access Your Application

After successful deployment, access your application at:

- **Frontend**: http://185.244.214.70/
- **Backend API**: http://185.244.214.70/api/
- **Monitoring Dashboard**: http://185.244.214.70:8080/

## Troubleshooting

### If Nginx fails to start:
```bash
sudo nginx -t
sudo journalctl -u nginx -f
```

### If backend is not accessible:
```bash
sudo systemctl status ai-trading-backend
sudo journalctl -u ai-trading-backend -f
```

### If monitoring dashboard fails:
```bash
sudo systemctl status monitoring-dashboard
sudo journalctl -u monitoring-dashboard -f
```

### Check firewall:
```bash
sudo ufw status
sudo ufw allow 80/tcp
sudo ufw allow 8080/tcp
```

## Manual Commands Summary

Copy and paste these commands one by one in Termius:

```bash
# 1. Extract frontend
cd /root
sudo mkdir -p /var/www/html/backup
sudo cp -r /var/www/html/* /var/www/html/backup/ 2>/dev/null || true
sudo tar -xzf frontend-deployment.tar.gz -C /var/www/html/
sudo chown -R www-data:www-data /var/www/html/
sudo chmod -R 755 /var/www/html/

# 2. Configure Nginx
sudo cp nginx-frontend.conf /etc/nginx/sites-available/ai-trading-sentinel
sudo ln -sf /etc/nginx/sites-available/ai-trading-sentinel /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx

# 3. Setup monitoring
chmod +x monitoring_setup.sh
sudo ./monitoring_setup.sh

# 4. Verify deployment
chmod +x verify_deployment.sh
./verify_deployment.sh

# 5. Final check
sudo systemctl status nginx ai-trading-backend monitoring-dashboard
```

## Success Indicators

✅ Nginx status: active (running)
✅ Backend status: active (running)  
✅ Monitoring status: active (running)
✅ Frontend accessible at http://185.244.214.70/
✅ API accessible at http://185.244.214.70/api/health
✅ Monitoring accessible at http://185.244.214.70:8080/

---

**Note**: Execute these commands directly on your VPS through Termius for reliable deployment.