# Deployment Guide for AI Trading Sentinel

## Contabo VPS Deployment (Ubuntu 22.04)

This guide walks you through deploying the AI Trading Sentinel bot on a Contabo VPS running Ubuntu 22.04.

### Prerequisites

- A Contabo VPS with Ubuntu 22.04 installed
- SSH access to your VPS
- Your project pushed to GitHub
- `.env.example` file committed to your repository

### Manual Deployment

#### 1. Connect to your VPS

```bash
ssh root@your_vps_ip -p your_ssh_port
```

#### 2. Clone the repository

```bash
git clone https://github.com/your-username/ai-trading-sentinel.git
cd ai-trading-sentinel
```

#### 3. Run the setup script

```bash
chmod +x deploy_contabo_setup.sh
./deploy_contabo_setup.sh
```

This script will:
- Update system packages
- Install Python, pip, and git
- Install Chrome and ChromeDriver
- Create a Python virtual environment
- Install project dependencies
- Set up environment variables
- Create a systemd service for auto-start

#### 4. Configure your environment variables

```bash
cp .env.example .env
nano .env
```

Update all placeholder values with your actual credentials and settings.

#### 5. Start the service

```bash
sudo systemctl start ai-trading-sentinel
sudo systemctl enable ai-trading-sentinel
```

#### 6. Verify the service is running

```bash
sudo systemctl status ai-trading-sentinel
```

### Automated Deployment via GitHub Actions

For automated deployments using GitHub Actions:

1. Set up the required GitHub Secrets in your repository:
   - `CONTABO_VPS_IP`: Your VPS IP address
   - `CONTABO_VPS_PASSWORD`: Your VPS password
   - `CONTABO_SSH_PORT`: Your SSH port (usually 22)

2. Push changes to your main branch to trigger the CI/CD pipeline

3. The GitHub Actions workflow will:
   - Run linting and tests
   - Deploy to your Contabo VPS if all tests pass

### Monitoring and Logs

To monitor your bot and view logs:

```bash
# View service status
sudo systemctl status ai-trading-sentinel

# View logs in real-time
sudo journalctl -u ai-trading-sentinel -f
```

### Updating the Bot

To update your bot with the latest code:

```bash
cd ~/ai-trading-sentinel
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart ai-trading-sentinel
```

### Troubleshooting

#### Chrome/Selenium Issues

If you encounter issues with Chrome or Selenium:

```bash
# Check Chrome version
google-chrome --version

# Check ChromeDriver version
chromedriver --version

# Reinstall ChromeDriver if needed
CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d. -f1)
wget -q "https://chromedriver.storage.googleapis.com/$(wget -q -O - https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION})/chromedriver_linux64.zip"
unzip chromedriver_linux64.zip
sudo mv chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
```

#### Service Not Starting

If the service fails to start:

```bash
# Check for errors in the service
sudo journalctl -u ai-trading-sentinel -e

# Verify environment variables
cat .env

# Test running the bot manually
source venv/bin/activate
python cloud_main.py
```

### Security Considerations

- Regularly update your system: `sudo apt update && sudo apt upgrade -y`
- Consider setting up a firewall: `sudo ufw enable`
- Use strong passwords and consider key-based SSH authentication
- Regularly rotate API keys and credentials
- Monitor your VPS for unusual activity

### Backup Strategy

Set up regular backups of your configuration and data:

```bash
# Create a backup script
cat > ~/backup-trading-bot.sh << 'EOL'
#!/bin/bash
BACKUP_DIR=~/backups/$(date +%Y-%m-%d)
mkdir -p $BACKUP_DIR
cp ~/ai-trading-sentinel/.env $BACKUP_DIR/
cp -r ~/ai-trading-sentinel/logs $BACKUP_DIR/
cp -r ~/ai-trading-sentinel/data $BACKUP_DIR/
EOL

chmod +x ~/backup-trading-bot.sh

# Add to crontab to run daily
(crontab -l 2>/dev/null; echo "0 0 * * * ~/backup-trading-bot.sh") | crontab -
```