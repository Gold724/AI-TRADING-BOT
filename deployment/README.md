# TRAE AI Trading Sentinel - Deployment Guide

## Overview

This guide provides instructions for deploying TRAE AI Trading Sentinel in a production environment with 24/7 operation capabilities. The deployment is designed to be resilient, secure, and maintainable.

## Prerequisites

- Linux server (recommended: Contabo VPS or similar)
- Python 3.8+ installed
- Git installed
- Supervisor, PM2, or systemd for process management

## Installation Steps

### 1. Clone the Repository

```bash
mkdir -p /home/trae
cd /home/trae
git clone https://github.com/your-username/AI-Sentinel.git
cd AI-Sentinel
```

### 2. Set Up Python Environment

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
cp deployment/.env.example .env
# Edit .env file with your actual credentials and settings
nano .env
```

### 4. Set Up Process Management

Choose one of the following options:

#### Option A: Supervisor (Recommended)

```bash
sudo apt-get install supervisor
sudo cp deployment/supervisor_config.ini /etc/supervisor/conf.d/trae_sentinel.conf
# Edit the configuration file if needed
sudo nano /etc/supervisor/conf.d/trae_sentinel.conf
# Update environment variables
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start trae_sentinel
```

#### Option B: Systemd

```bash
sudo cp deployment/trae-sentinel.service /etc/systemd/system/
# Edit the service file if needed
sudo nano /etc/systemd/system/trae-sentinel.service
sudo systemctl daemon-reload
sudo systemctl enable trae-sentinel
sudo systemctl start trae-sentinel
```

#### Option C: PM2

```bash
sudo npm install pm2 -g
pm2 start deployment/ecosystem.config.js
pm2 save
pm2 startup
# Follow the instructions to set up PM2 to start on boot
```

### 5. Verify Deployment

```bash
# For Supervisor
sudo supervisorctl status trae_sentinel

# For Systemd
sudo systemctl status trae-sentinel

# For PM2
pm2 status
```

## Updating the System

```bash
cd /home/trae/AI-Sentinel
git pull

# Restart the service based on your process manager
# For Supervisor
sudo supervisorctl restart trae_sentinel

# For Systemd
sudo systemctl restart trae-sentinel

# For PM2
pm2 restart trae-sentinel
```

## Monitoring and Logs

### Log Locations

- Application logs: `/home/trae/AI-Sentinel/logs/`
- Supervisor logs: `/home/trae/AI-Sentinel/logs/supervisor_*.log`
- Systemd logs: `journalctl -u trae-sentinel`
- PM2 logs: `/home/trae/AI-Sentinel/logs/pm2_*.log`

### Monitoring Commands

```bash
# View real-time logs
tail -f /home/trae/AI-Sentinel/logs/trae.log

# Check heartbeat status
cat /home/trae/AI-Sentinel/logs/heartbeats.json | tail -n 100
```

## Security Considerations

1. **Environment Variables**: Never commit `.env` files to version control.
2. **File Permissions**: Restrict access to sensitive files:
   ```bash
   chmod 600 .env
   ```
3. **Regular Updates**: Keep the system and dependencies updated.
4. **Firewall**: Configure firewall to only allow necessary connections.

## Troubleshooting

### Common Issues

1. **Service won't start**:
   - Check logs for errors
   - Verify environment variables
   - Ensure correct file permissions

2. **Connection issues with brokers**:
   - Verify API credentials
   - Check network connectivity
   - Ensure firewall allows outbound connections

3. **High resource usage**:
   - Check for memory leaks
   - Monitor CPU and memory usage
   - Consider increasing server resources if needed

## Support

For assistance, please contact the TRAE AI support team or open an issue on the GitHub repository.