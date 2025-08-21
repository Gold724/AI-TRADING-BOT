# 🔐 SSH Access & Deployment Guide for AI Trading Sentinel

## Current Status
✅ **Connected to Contabo VPS**: `root@vmi2736801`  
❌ **Target Server Access**: `161.97.112.146` - Authentication Failed

## 🚨 SSH Authentication Solutions

### Option 1: SSH Key-Based Authentication (Recommended)
```bash
# Generate SSH key pair on your VPS
ssh-keygen -t rsa -b 4096 -C "trae-deployment@contabo"

# Copy public key to target server
ssh-copy-id root@161.97.112.146

# Or manually add key if ssh-copy-id fails
cat ~/.ssh/id_rsa.pub
# Copy output and add to target server's ~/.ssh/authorized_keys
```

### Option 2: Password Reset (If you have console access)
```bash
# Contact Contabo support for console access to reset password
# Or use Contabo control panel to reset root password
```

### Option 3: Alternative User Account
```bash
# Try connecting with different user (if available)
ssh ubuntu@161.97.112.146
ssh admin@161.97.112.146
ssh user@161.97.112.146
```

## 🚀 Direct Deployment on Current VPS

**Since you're already on a Contabo VPS, you can deploy directly here:**

### Step 1: System Preparation
```bash
# Update system
apt update && apt upgrade -y

# Install required packages
apt install -y python3 python3-pip nodejs npm git docker.io docker-compose

# Start Docker
systemctl start docker
systemctl enable docker
```

### Step 2: Clone Repository
```bash
# Clone the AI Trading Sentinel
git clone https://github.com/your-username/ai-trading-sentinel.git
cd ai-trading-sentinel

# Make scripts executable
chmod +x deploy/deploy-production.sh
chmod +x quick-deploy.sh
```

### Step 3: Run Production Deployment
```bash
# Execute the production deployment
./deploy/deploy-production.sh

# Or run the quick deploy (will use localhost)
./quick-deploy.sh localhost
```

### Step 4: Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit with your credentials
nano .env
```

### Step 5: Start Services
```bash
# Start the trading bot
python3 main.py --production

# In another terminal, start the backend
python3 backend_main.py
```

## 🔧 SSH Troubleshooting Commands

### Check SSH Configuration
```bash
# Check SSH service status
systemctl status ssh

# View SSH logs
journalctl -u ssh -f

# Test SSH connection with verbose output
ssh -v root@161.97.112.146
```

### Network Connectivity Tests
```bash
# Test basic connectivity
ping 161.97.112.146

# Check if SSH port is open
nmap -p 22 161.97.112.146

# Test with telnet
telnet 161.97.112.146 22
```

## 🛡️ Security Best Practices

### 1. SSH Key Setup
```bash
# Generate secure SSH key
ssh-keygen -t ed25519 -C "trae-bot@$(hostname)"

# Set proper permissions
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_ed25519.pub
```

### 2. SSH Configuration
```bash
# Edit SSH config for easier access
nano ~/.ssh/config

# Add this configuration:
Host trae-server
    HostName 161.97.112.146
    User root
    IdentityFile ~/.ssh/id_ed25519
    Port 22
    ServerAliveInterval 60
```

### 3. Firewall Configuration
```bash
# Configure UFW firewall
ufw allow ssh
ufw allow 5000/tcp  # Backend API
ufw allow 3000/tcp  # Frontend (if needed)
ufw allow 9090/tcp  # Prometheus
ufw allow 3001/tcp  # Grafana
ufw enable
```

## 📊 Deployment Validation

### Quick Health Check
```bash
# Run the deployment validator
python3 deployment_validator.py --step 1

# Check running services
systemctl status trae
systemctl status docker

# Verify ports
netstat -tlnp | grep -E ':(5000|3000|9090|3001)'
```

### Service Status Commands
```bash
# Check all services
systemctl list-units --type=service --state=running | grep -E '(trae|docker|nginx)'

# View logs
journalctl -u trae -f
tail -f /var/log/trae/trading.log
```

## 🔄 Alternative Deployment Methods

### Method 1: Docker Deployment
```bash
# Build and run with Docker
docker-compose up -d

# Check container status
docker ps
docker logs trae-bot
```

### Method 2: Manual Installation
```bash
# Install Python dependencies
pip3 install -r requirements.txt

# Install Node.js dependencies
npm install

# Build frontend
npm run build
```

## 📞 Support & Next Steps

### If SSH Access Fails:
1. **Contact Contabo Support**: support@contabo.com
2. **Request Console Access**: To reset root password
3. **Deploy Locally**: Use current VPS as deployment target

### If Deployment Succeeds:
1. **Access URLs**:
   - Backend API: `http://your-vps-ip:5000`
   - Grafana: `http://your-vps-ip:3001`
   - Prometheus: `http://your-vps-ip:9090`

2. **Enable Trading**:
   ```bash
   # Start with paper trading first
   curl -X POST http://localhost:5000/api/trading/start
   ```

3. **Monitor Logs**:
   ```bash
   tail -f logs/trading.log
   tail -f logs/system.log
   ```

## 🎯 Immediate Action Plan

1. **Try SSH key authentication** (most secure)
2. **If that fails, deploy on current VPS** (vmi2736801)
3. **Contact Contabo support** for target server access
4. **Validate deployment** using provided scripts
5. **Start with paper trading** before live trading

---

**🚀 Ready to Deploy!** Choose the method that works best for your current access level.