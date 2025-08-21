# 🚀 Windows to Contabo Deployment Guide

## Current Situation
You're on Windows trying to run Linux commands. The deployment needs to happen on your actual Contabo VPS server, not locally on Windows.

## ⚠️ Important Note
The commands in `MANUAL_DEPLOYMENT.md` are for **Linux servers only**. You cannot run `sudo`, `systemctl`, or `journalctl` on Windows.

## 🎯 Correct Deployment Process

### Option 1: Direct SSH to Contabo (Recommended)

1. **Connect to your Contabo server via SSH:**
   ```cmd
   ssh root@161.97.112.146
   ```
   
2. **If SSH fails, try these alternatives:**
   - Use PuTTY (Windows SSH client)
   - Use Windows Terminal with OpenSSH
   - Access via Contabo web console

3. **Once connected to Contabo, run these commands:**
   ```bash
   # Quick deployment (copy-paste all at once)
   curl -sSL https://raw.githubusercontent.com/your-repo/ai-trading-sentinel/main/deploy_local.sh | bash
   
   # OR manual step-by-step:
   apt update -y
   apt install -y python3 python3-pip python3-venv git curl wget
   mkdir -p /opt/ai-trading-sentinel
   cd /opt/ai-trading-sentinel
   
   # Create the application
   cat > main.py << 'EOF'
   #!/usr/bin/env python3
   import logging
   import time
   import os
   
   logging.basicConfig(level=logging.INFO)
   logger = logging.getLogger(__name__)
   
   def main():
       logger.info("🚀 AI Trading Sentinel Starting...")
       counter = 0
       while True:
           counter += 1
           logger.info(f"💓 Heartbeat #{counter} - System OK")
           time.sleep(30)
   
   if __name__ == "__main__":
       main()
   EOF
   
   # Setup service
   python3 -m venv venv
   ./venv/bin/pip install flask requests psutil
   
   # Create systemd service
   cat > /etc/systemd/system/trae.service << 'EOF'
   [Unit]
   Description=AI Trading Sentinel
   After=network.target
   
   [Service]
   Type=simple
   User=root
   WorkingDirectory=/opt/ai-trading-sentinel
   ExecStart=/opt/ai-trading-sentinel/venv/bin/python main.py
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   EOF
   
   # Start the service
   systemctl daemon-reload
   systemctl enable trae
   systemctl start trae
   
   # Check status
   systemctl status trae
   journalctl -u trae -f
   ```

### Option 2: Upload Files via SCP/SFTP

1. **Upload deployment script from Windows:**
   ```cmd
   scp deploy_local.sh root@161.97.112.146:/tmp/
   ```

2. **SSH to Contabo and run:**
   ```bash
   chmod +x /tmp/deploy_local.sh
   /tmp/deploy_local.sh
   ```

### Option 3: Use Windows Subsystem for Linux (WSL)

1. **Install WSL on Windows:**
   ```cmd
   wsl --install
   ```

2. **From WSL, connect to Contabo:**
   ```bash
   ssh root@161.97.112.146
   ```

## 🔧 Troubleshooting SSH Connection

If you can't connect to `161.97.112.146`:

1. **Check if server is reachable:**
   ```cmd
   ping 161.97.112.146
   telnet 161.97.112.146 22
   ```

2. **Try different SSH methods:**
   ```cmd
   # With password
   ssh -o PreferredAuthentications=password root@161.97.112.146
   
   # With key
   ssh -i your_key.pem root@161.97.112.146
   
   # Different port
   ssh -p 2222 root@161.97.112.146
   ```

3. **Use Contabo Control Panel:**
   - Log into Contabo dashboard
   - Access server via web console
   - Run deployment commands directly

## 🎯 What You Should Do Now

1. **Stop trying Linux commands on Windows**
2. **Connect to your actual Contabo server** (161.97.112.146)
3. **Run the deployment commands on the Contabo server**
4. **Verify the service is running on Contabo**

## ✅ Success Indicators (On Contabo Server)

- `systemctl status trae` shows "active (running)"
- `journalctl -u trae -f` shows heartbeat messages
- Service automatically restarts if it crashes
- Logs are being written to `/opt/ai-trading-sentinel/logs/`

## 🚨 Common Mistakes to Avoid

❌ **Don't run Linux commands on Windows**  
❌ **Don't expect `sudo` to work on Windows**  
❌ **Don't try to install systemd on Windows**  

✅ **Do connect to your Contabo server first**  
✅ **Do run deployment commands on the Linux server**  
✅ **Do verify the service is running on Contabo**  

---

**Next Step**: Connect to your Contabo server and run the deployment there, not on your local Windows machine.