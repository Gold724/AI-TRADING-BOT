# 🖥️ AI Trading Sentinel - VNC Access Guide

## VNC Connection Setup

### Option 1: Contabo Dashboard VNC
1. Login to Contabo dashboard
2. Navigate to your VPS
3. Click "VNC Console" button
4. Access desktop environment directly

### Option 2: VNC Client
```bash
# Connect using VNC client (RealVNC, TightVNC, etc.)
vnc://YOUR_VPS_IP:5901
```

## Essential Commands (Run in VNC Terminal)

### Check Bot Status
```bash
cd /root/ai-trading-sentinel
pm2 status
```

### View Recent Logs
```bash
pm2 logs --lines 50
```

### Restart All Services
```bash
pm2 restart all
```

### Update Code from GitHub
```bash
cd /root/ai-trading-sentinel && git pull origin main && pm2 restart all
```

### Check System Resources
```bash
htop
```

### View Trading Logs
```bash
tail -f /root/ai-trading-sentinel/logs/trades.log
```

## Emergency Commands (VNC Terminal)

### Force Kill All Processes
```bash
pm2 kill
```

### Restart System
```bash
sudo reboot
```

### Check Disk Space
```bash
df -h
```

## File Management (VNC Desktop)

### Edit Environment Variables
```bash
# Use nano in terminal or GUI text editor
nano /root/ai-trading-sentinel/.env
# OR use GUI file manager + text editor
```

### Backup Important Files
```bash
cp /root/ai-trading-sentinel/.env /root/backup/.env.backup
```

### View Configuration
```bash
cat /root/ai-trading-sentinel/config/trading_config.json
```

## VNC Access Benefits

✅ **Visual Desktop** - Full Ubuntu desktop environment  
✅ **Browser Access** - Test web interface directly on VPS  
✅ **GUI Applications** - Use graphical tools and editors  
✅ **File Manager** - Easy drag-and-drop file management  
✅ **Multiple Terminals** - Run several commands simultaneously  
✅ **Screen Persistence** - Desktop remains active after disconnect
