# Contabo VPS Deployment Guide for AI Trading Sentinel

This guide provides step-by-step instructions for deploying the AI Trading Sentinel system on a Contabo VPS. We offer both manual and automated deployment options.

## 🚀 Prerequisites

- A Contabo VPS with Ubuntu installed
- SSH access to your VPS
- Your AI Trading Sentinel codebase (either from GitHub or local)

## 🔐 Connecting to Your VPS

From your local terminal (Linux/macOS) or PowerShell (Windows):

```bash
ssh root@YOUR_VPS_IP
# Enter your password when prompted
```

Example:
```bash
ssh root@161.97.112.146
# Enter password: YourPassword
```

## 🛠️ Deployment Options

### Option 1: Automated Deployment (Recommended)

We've provided automated deployment scripts that handle everything for you:

#### Windows Users:

```bash
deploy_to_contabo.bat
```

#### Linux/macOS Users:

```bash
./deploy_to_contabo.sh
```

These scripts will:
- Connect to your VPS via SSH
- Upload all necessary files
- Install dependencies
- Configure the environment
- Start the trading sentinel in a persistent tmux session

### Option 2: Manual Setup

If you prefer to set up manually, follow these steps:

1. Upload the setup script to your VPS:

```bash
# On your VPS
nano sentinel_vps_setup.sh
# Paste the script content, then press CTRL+X, Y, Enter to save
```

2. Make the script executable and run it:

```bash
chmod +x sentinel_vps_setup.sh
./sentinel_vps_setup.sh
```

The script will:
- Update Ubuntu
- Install Python, pip, git
- Install Google Chrome & ChromeDriver (for Selenium)
- Clone your repository (you'll need to modify the script with your actual repo URL)
- Set up the project directory

## ⚙️ Configuration

After running the setup script:

1. Configure your environment variables:

```bash
cd ai-trading-sentinel
nano .env
```

Add your configuration:
```
BULENOX_USERNAME=your_username
BULENOX_PASSWORD=your_password
SLACK_WEBHOOK_URL=your_slack_webhook_url
MAX_DAILY_TRADES=5
TRADE_INTERVAL_SECONDS=60
SIGNAL_SOURCE=webhook
```

2. (Optional) Upload your Chrome profile data if you have it:

**Using Automated Deployment:**
The deployment scripts will prompt you to upload a Chrome profile. Simply provide the path to your Chrome profile directory when prompted.

**Manual Upload:**
```bash
# From your local machine, compress your Chrome profile
tar -czvf chrome_profile.tar.gz /path/to/chrome/profile

# Use SCP to upload to your VPS
scp chrome_profile.tar.gz root@YOUR_VPS_IP:/root/ai-trading-sentinel/

# On your VPS, extract the profile
cd ai-trading-sentinel
tar -xzvf chrome_profile.tar.gz
```

**Chrome Profile Locations:**
- Windows: `C:\Users\YourUsername\AppData\Local\Google\Chrome\User Data\Default`
- macOS: `~/Library/Application Support/Google/Chrome/Default`
- Linux: `~/.config/google-chrome/Default`

## 🚀 Running the Trading Sentinel

Start the heartbeat monitor:

```bash
python3 heartbeat.py
```

For persistent operation, use `tmux` or `screen`:

```bash
# Install tmux
apt install -y tmux

# Create a new session
tmux new -s trading_sentinel

# Run your script
python3 heartbeat.py

# Detach from the session (press Ctrl+B, then D)
```

To reattach to the session later:

```bash
tmux attach -t trading_sentinel
```

## 🔄 Updating Your Deployment

To update your code on the VPS:

```bash
cd ai-trading-sentinel
git pull
```

If you've made local changes, you may need to reset first:

```bash
git reset --hard
git pull
```

## 📊 Monitoring

Check the logs for any issues:

```bash
cat logs/heartbeat.log
```

You should also receive notifications via Slack if configured correctly.

## 🛡️ Security Considerations

- Consider setting up a non-root user for running the application
- Use SSH keys instead of password authentication
- Keep your .env file secure and never commit it to version control
- Regularly update your system with `apt update && apt upgrade`

## 🆘 Troubleshooting

- If Chrome fails to start, check if it's installed correctly: `google-chrome --version`
- If ChromeDriver fails, verify it matches your Chrome version
- Check the logs for specific error messages
- Ensure your VPS has enough memory (at least 2GB recommended)

---

For more detailed information, refer to the main [README.md](./README.md) and [HEARTBEAT_MONITORING.md](./HEARTBEAT_MONITORING.md) files.