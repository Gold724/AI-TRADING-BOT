# 🖥️ AI Trading Sentinel - VNC Management Commands

## VNC Access Setup

### Initial VNC Connection
```bash
# Connect to your Contabo VPS via VNC
# Use Contabo dashboard VNC console or VNC client
# Default VNC port: 5901
vnc://YOUR_VPS_IP:5901
```

### VNC Authentication
- **Username:** root (or your VPS user)
- **VNC Password:** Set during VPS setup
- **Desktop Environment:** Ubuntu Desktop/XFCE

## 📋 Daily Management Commands (via VNC Terminal)

### Check Bot Status
```bash
# Open terminal in VNC session
cd /root/ai-trading-sentinel
pm2 status
```

### View Trading Logs
```bash
# View recent logs
pm2 logs --lines 50

# View specific service logs
pm2 logs backend --lines 30
pm2 logs frontend --lines 30
```

### Restart Services
```bash
# Restart all services
pm2 restart all

# Restart specific service
pm2 restart backend
pm2 restart frontend
```

### Update Code from GitHub
```bash
# Navigate to project directory
cd /root/ai-trading-sentinel

# Pull latest changes
git pull origin main

# Restart services after update
pm2 restart all
```

### System Health Checks
```bash
# Check system resources
htop

# Check disk space
df -h

# Check memory usage
free -h

# Check network connectivity
ping google.com
```

### Service Management
```bash
# Start services
pm2 start ecosystem.config.js

# Stop all services
pm2 stop all

# Delete all services
pm2 delete all

# Save PM2 configuration
pm2 save

# Setup PM2 startup
pm2 startup
```

### Environment Management
```bash
# Edit environment variables
nano /root/ai-trading-sentinel/.env

# Reload environment after changes
pm2 restart all
```

### Nginx Web Server
```bash
# Check Nginx status
sudo systemctl status nginx

# Restart Nginx
sudo systemctl restart nginx

# View Nginx logs
sudo tail -f /var/log/nginx/error.log
```

### Trading Bot Specific Commands
```bash
# Check if bot is logged into broker
cat /root/ai-trading-sentinel/logs/login.log

# View trade execution logs
cat /root/ai-trading-sentinel/logs/trades.log

# Check risk management status
cat /root/ai-trading-sentinel/logs/risk.log
```

## 🚨 Emergency Commands

### Force Stop Everything
```bash
# Kill all PM2 processes
pm2 kill

# Stop Nginx
sudo systemctl stop nginx

# Check what's using port 80
sudo netstat -tlnp | grep :80
```

### System Recovery
```bash
# Restart system services
sudo systemctl daemon-reload

# Restart networking
sudo systemctl restart networking

# Reboot system (last resort)
sudo reboot
```

### Backup Important Data
```bash
# Backup .env file
cp /root/ai-trading-sentinel/.env /root/backup/.env.backup

# Backup trading logs
cp -r /root/ai-trading-sentinel/logs /root/backup/logs_backup

# Backup configuration
cp /root/ai-trading-sentinel/config/* /root/backup/config_backup/
```

## 📱 Access Your Bot (via VNC Browser)

### Open Web Browser in VNC Session
```bash
# Open Firefox/Chrome in VNC desktop
firefox http://localhost &
# or
chromium-browser http://localhost &
```

### Bot Interface URLs
- **Main Dashboard:** `http://localhost` or `http://YOUR_VPS_IP`
- **API Endpoints:** `http://localhost/api`
- **Trading Panel:** `http://localhost/sentinel`
- **Health Check:** `http://localhost/health`

## 🔧 VNC-Specific Advantages

✅ **Visual Interface** - Full desktop environment  
✅ **Browser Access** - Test web interface directly  
✅ **File Manager** - Easy file navigation and editing  
✅ **Multiple Terminals** - Run multiple commands simultaneously  
✅ **Screen Sharing** - Share session with team members  
✅ **Persistent Session** - Desktop remains active after disconnect  

## 📊 Monitoring Dashboard (VNC)

### System Monitor
```bash
# Install system monitor (if not present)
sudo apt install gnome-system-monitor

# Launch system monitor
gnome-system-monitor &
```

### Trading Performance Monitor
```bash
# Real-time log monitoring
tail -f /root/ai-trading-sentinel/logs/trades.log

# Performance metrics
watch -n 5 'pm2 monit'
```

## 🔄 Automated Tasks (Cron Jobs)

### Setup Automated Health Checks
```bash
# Edit crontab
crontab -e

# Add health check every 5 minutes
*/5 * * * * cd /root/ai-trading-sentinel && python health_check.py

# Add daily log rotation
0 0 * * * cd /root/ai-trading-sentinel && python rotate_logs.py
```

## 🆘 Troubleshooting via VNC

### If Bot Won't Start
1. **Check logs:** `pm2 logs`
2. **Verify .env:** `cat /root/ai-trading-sentinel/.env`
3. **Check dependencies:** `pip list`
4. **Test browser:** `python test_browser.py`

### If Web Interface Not Accessible
1. **Check Nginx:** `sudo systemctl status nginx`
2. **Check ports:** `sudo netstat -tlnp | grep :80`
3. **Check firewall:** `sudo ufw status`
4. **Test locally:** Open browser in VNC to `http://localhost`

### If Trading Not Working
1. **Check broker login:** `cat logs/login.log`
2. **Verify credentials:** Check `.env` file
3. **Test connection:** `python test_broker_connection.py`
4. **Check risk settings:** `cat config/risk_management.json`

---

## 🎯 VNC Best Practices

✅ **Keep VNC session active** for continuous monitoring  
✅ **Use multiple terminal tabs** for different tasks  
✅ **Bookmark bot URLs** in VNC browser  
✅ **Save important commands** in desktop text files  
✅ **Regular screenshots** of trading performance  
✅ **Monitor system resources** via desktop widgets  

**🖥️ Your AI Trading Sentinel is now fully manageable via VNC with visual desktop access!**