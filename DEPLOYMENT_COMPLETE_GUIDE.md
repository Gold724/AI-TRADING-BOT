# 🚀 AI Trading Sentinel - Complete Cloud Deployment Guide

## Overview

This guide provides everything you need to deploy your AI Trading Sentinel to the cloud for 24/7 operation, independent of your local machine. The system will automatically:

- ✅ Run continuously on cloud infrastructure
- ✅ Auto-restart on failures
- ✅ Auto-update from GitHub
- ✅ Monitor health and performance
- ✅ Handle network issues gracefully
- ✅ Provide web dashboard access
- ✅ Generate detailed logs and reports

## 📋 Prerequisites

### Required Tools
- **Contabo VPS** (or any cloud provider)
- **GitHub Account** (for code repository)
- **Termius** (for SSH management)
- **SSH Key Pair** (for secure access)

### Local Requirements
- Git installed
- SSH client (OpenSSH or Git Bash)
- PowerShell (Windows) or Bash (Linux/Mac)

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Your Laptop   │    │   GitHub Repo   │    │   Contabo VPS   │
│                 │    │                 │    │                 │
│ • Development   │───▶│ • Source Code   │───▶│ • Production    │
│ • Testing       │    │ • Auto-updates  │    │ • 24/7 Trading  │
│ • Monitoring    │    │ • Version Ctrl  │    │ • Monitoring    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                               ┌───────▼───────┐
                                               │  Docker Stack │
                                               │               │
                                               │ • Trading Bot │
                                               │ • Dashboard   │
                                               │ • Redis Cache │
                                               │ • Nginx Proxy │
                                               └───────────────┘
```

## 🚀 Quick Start Deployment

### Step 1: Prepare Your Repository

1. **Create GitHub Repository**
   ```bash
   # Create new repository on GitHub
   # Clone to your local machine
   git clone https://github.com/yourusername/ai-trading-sentinel.git
   cd ai-trading-sentinel
   
   # Add all files and push
   git add .
   git commit -m "Initial AI Trading Sentinel setup"
   git push origin main
   ```

2. **Update Repository URL**
   - Edit `deploy_to_cloud.sh` or `deploy_to_cloud.ps1`
   - Replace `https://github.com/yourusername/ai-trading-sentinel.git` with your actual repo URL

### Step 2: Setup Contabo VPS

1. **Order VPS from Contabo**
   - Go to [Contabo.com](https://contabo.com)
   - Choose VPS plan (minimum 2GB RAM recommended)
   - Select Ubuntu 20.04 or 22.04 LTS
   - Note down IP address and root password

2. **Configure SSH Access**
   ```bash
   # Generate SSH key pair (if you don't have one)
   ssh-keygen -t rsa -b 4096 -C "your-email@example.com"
   
   # Copy public key to VPS
   ssh-copy-id root@YOUR_VPS_IP
   ```

### Step 3: Deploy Using Automated Script

#### For Windows Users:
```powershell
# Run PowerShell as Administrator
.\deploy_to_cloud.ps1 -VpsHost "YOUR_VPS_IP" -GitRepo "https://github.com/yourusername/ai-trading-sentinel.git"
```

#### For Linux/Mac Users:
```bash
# Make script executable
chmod +x deploy_to_cloud.sh

# Run deployment
./deploy_to_cloud.sh
```

### Step 4: Verify Deployment

1. **Check Services**
   ```bash
   ssh root@YOUR_VPS_IP
   cd ai-trading-sentinel
   docker-compose ps
   ```

2. **Access Dashboard**
   - Open browser: `http://YOUR_VPS_IP:3000`
   - Trading interface: `http://YOUR_VPS_IP:8080`

3. **Monitor Logs**
   ```bash
   docker-compose logs -f trading-bot
   ```

## 🔧 Manual Deployment (Advanced)

If you prefer manual control or the automated script fails:

### 1. VPS Environment Setup

```bash
# Connect to VPS
ssh root@YOUR_VPS_IP

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install additional tools
apt install -y git htop screen tmux ufw fail2ban
```

### 2. Security Configuration

```bash
# Configure firewall
ufw enable
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8080/tcp
ufw allow 3000/tcp

# Configure Fail2Ban
systemctl enable fail2ban
systemctl start fail2ban
```

### 3. Application Deployment

```bash
# Clone repository
git clone https://github.com/yourusername/ai-trading-sentinel.git
cd ai-trading-sentinel

# Create environment file
cat > .env << EOF
BULENOX_USERNAME=BX64883
BULENOX_PASSWORD=XujhMzFf6K
ENVIRONMENT=production
HEADLESS=true
LOG_LEVEL=INFO
REDIS_PASSWORD=$(openssl rand -hex 16)
DASHBOARD_SECRET=$(openssl rand -hex 16)
TZ=UTC
EOF

# Set secure permissions
chmod 600 .env

# Build and start services
docker-compose build
docker-compose up -d
```

### 4. Monitoring Setup

```bash
# Create monitoring script
cat > monitor_trading_bot.sh << 'EOF'
#!/bin/bash

# Check container health
if ! docker-compose ps | grep -q "Up"; then
    echo "⚠️ Restarting containers..."
    docker-compose restart
fi

# Check application health
if ! curl -f http://localhost:8080/health >/dev/null 2>&1; then
    echo "⚠️ Restarting trading bot..."
    docker-compose restart trading-bot
fi

# Cleanup old files
find logs/ -name "*.log" -mtime +7 -delete 2>/dev/null || true
find screenshots/ -name "*.png" -mtime +3 -delete 2>/dev/null || true

echo "✅ Health check completed at $(date)"
EOF

chmod +x monitor_trading_bot.sh

# Setup cron job
(crontab -l 2>/dev/null; echo "*/5 * * * * /root/ai-trading-sentinel/monitor_trading_bot.sh >> /root/ai-trading-sentinel/logs/monitor.log 2>&1") | crontab -
```

### 5. Auto-Update Setup

```bash
# Create auto-update script
cat > auto_update.sh << 'EOF'
#!/bin/bash
set -e

cd /root/ai-trading-sentinel

echo "🔍 Checking for updates..."
git fetch origin

LATEST_COMMIT=$(git rev-parse origin/main)
CURRENT_COMMIT=$(git rev-parse HEAD)

if [ "$LATEST_COMMIT" != "$CURRENT_COMMIT" ]; then
    echo "📥 New updates found, deploying..."
    
    # Pull updates
    git pull origin main
    
    # Rebuild and restart
    docker-compose build --no-cache
    docker-compose up -d
    
    echo "✅ Update completed successfully!"
else
    echo "✅ Already up to date!"
fi
EOF

chmod +x auto_update.sh

# Setup cron job for auto-updates
(crontab -l 2>/dev/null; echo "0 */6 * * * /root/ai-trading-sentinel/auto_update.sh >> /root/ai-trading-sentinel/logs/update.log 2>&1") | crontab -
```

## 📱 Mobile Management with Termius

### Setup Termius App

1. **Download Termius**
   - iOS: [App Store](https://apps.apple.com/app/termius/id549039908)
   - Android: [Google Play](https://play.google.com/store/apps/details?id=com.server.auditor.ssh.client)

2. **Add Your VPS**
   ```
   Host: YOUR_VPS_IP
   Username: root
   Authentication: SSH Key
   Port: 22
   ```

3. **Quick Commands Setup**
   - Status Check: `cd ai-trading-sentinel && docker-compose ps`
   - View Logs: `cd ai-trading-sentinel && docker-compose logs -f --tail=50 trading-bot`
   - Restart Bot: `cd ai-trading-sentinel && docker-compose restart trading-bot`
   - Update System: `cd ai-trading-sentinel && ./auto_update.sh`

## 🔍 Monitoring and Maintenance

### Health Monitoring

1. **Automated Health Checks**
   - Runs every 5 minutes
   - Checks container status
   - Verifies application health
   - Auto-restarts on failures

2. **Manual Health Check**
   ```bash
   ssh root@YOUR_VPS_IP
   cd ai-trading-sentinel
   ./monitor_trading_bot.sh
   ```

### Log Management

1. **View Real-time Logs**
   ```bash
   docker-compose logs -f trading-bot
   ```

2. **Check Specific Logs**
   ```bash
   # Application logs
   tail -f logs/trading_bot.log
   
   # Monitor logs
   tail -f logs/monitor.log
   
   # Update logs
   tail -f logs/update.log
   ```

### Performance Monitoring

1. **System Resources**
   ```bash
   htop
   df -h
   docker stats
   ```

2. **Application Metrics**
   - Dashboard: `http://YOUR_VPS_IP:3000`
   - Health endpoint: `http://YOUR_VPS_IP:8080/health`

## 🚨 Troubleshooting

### Common Issues

1. **Container Won't Start**
   ```bash
   # Check logs
   docker-compose logs trading-bot
   
   # Rebuild container
   docker-compose build --no-cache trading-bot
   docker-compose up -d
   ```

2. **Login Issues**
   ```bash
   # Check credentials in .env file
   cat .env | grep BULENOX
   
   # Update credentials if needed
   nano .env
   docker-compose restart trading-bot
   ```

3. **Network Issues**
   ```bash
   # Check firewall
   ufw status
   
   # Test connectivity
   curl -I http://localhost:8080
   ```

4. **High Resource Usage**
   ```bash
   # Check resource usage
   docker stats
   
   # Restart services
   docker-compose restart
   ```

### Emergency Procedures

1. **Complete System Restart**
   ```bash
   cd ai-trading-sentinel
   docker-compose down
   docker system prune -f
   docker-compose up -d
   ```

2. **Rollback to Previous Version**
   ```bash
   git log --oneline -10
   git reset --hard COMMIT_HASH
   docker-compose build --no-cache
   docker-compose up -d
   ```

## 💰 Cost Optimization

### Contabo VPS Pricing
- **VPS S**: €4.99/month (2GB RAM, 50GB SSD) - Minimum recommended
- **VPS M**: €8.99/month (4GB RAM, 100GB SSD) - Recommended for production
- **VPS L**: €14.99/month (8GB RAM, 200GB SSD) - High-performance trading

### Resource Optimization

1. **Memory Usage**
   ```bash
   # Monitor memory
   free -h
   docker stats --no-stream
   
   # Optimize if needed
   echo 'vm.swappiness=10' >> /etc/sysctl.conf
   ```

2. **Storage Cleanup**
   ```bash
   # Clean Docker
   docker system prune -f
   
   # Clean logs
   find logs/ -name "*.log" -mtime +7 -delete
   ```

## 🔒 Security Best Practices

### SSH Security
```bash
# Disable password authentication
echo "PasswordAuthentication no" >> /etc/ssh/sshd_config
systemctl restart ssh

# Change default SSH port (optional)
sed -i 's/#Port 22/Port 2222/' /etc/ssh/sshd_config
systemctl restart ssh
ufw allow 2222/tcp
ufw delete allow ssh
```

### Application Security
```bash
# Set secure file permissions
chmod 600 .env
chown root:root .env

# Regular security updates
apt update && apt upgrade -y
```

## 📊 Success Metrics

After deployment, you should see:

✅ **Uptime**: 99.9% availability
✅ **Auto-Recovery**: Automatic restart on failures
✅ **Auto-Updates**: Latest code deployed every 6 hours
✅ **Monitoring**: Health checks every 5 minutes
✅ **Logging**: Comprehensive logs and screenshots
✅ **Performance**: Low latency trade execution
✅ **Security**: Hardened VPS with firewall protection

## 🆘 Support and Maintenance

### Regular Maintenance Tasks

1. **Weekly**
   - Check system resources
   - Review trading logs
   - Verify auto-updates working

2. **Monthly**
   - Update VPS system packages
   - Review security logs
   - Backup configuration files

3. **Quarterly**
   - Review and optimize performance
   - Update trading strategies
   - Security audit

### Getting Help

1. **Check Logs First**
   ```bash
   docker-compose logs trading-bot
   tail -f logs/trading_bot.log
   ```

2. **System Status**
   ```bash
   ./monitor_trading_bot.sh
   docker-compose ps
   ```

3. **Emergency Contact**
   - Keep VPS provider contact info handy
   - Document all configuration changes
   - Maintain backup of SSH keys

---

## 🎉 Congratulations!

Your AI Trading Sentinel is now running 24/7 in the cloud! 🚀

**What happens now:**
- Your bot trades automatically even when your laptop is off
- System auto-updates from GitHub every 6 hours
- Health monitoring ensures maximum uptime
- You can monitor and control everything from your phone via Termius
- All trades and activities are logged for analysis

**Next Steps:**
1. Monitor the first 24 hours closely
2. Set up mobile alerts via Termius
3. Review trading performance daily
4. Optimize strategies based on results

**Remember:** Your trading bot is now independent of your local machine and will continue operating 24/7 in the cloud! 💪