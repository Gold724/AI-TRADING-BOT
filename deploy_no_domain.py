#!/usr/bin/env python3
"""
🚀 AI Trading Sentinel - No Domain Deployment
Deploy directly to Contabo VPS using IP address
Requires: GitHub repo, Contabo VPS, Termius SSH access
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

class NoDomainDeployer:
    def __init__(self):
        self.project_root = Path.cwd()
        
    def create_ip_deployment_script(self, vps_ip, github_repo):
        """Create deployment script for IP-based access"""
        
        deploy_script = f'''#!/bin/bash
# 🚀 AI Trading Sentinel - IP Deployment Script
# Run this on your Contabo VPS

set -e

VPS_IP="{vps_ip}"
GITHUB_REPO="{github_repo}"
APP_DIR="/opt/ai-trading-sentinel"

echo "🚀 Starting AI Trading Sentinel deployment on $VPS_IP"

# 1. System Updates
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# 2. Install Dependencies
echo "🔧 Installing dependencies..."
sudo apt install -y python3 python3-pip python3-venv nodejs npm nginx git curl wget

# Install PM2 for process management
sudo npm install -g pm2

# 3. Clone Repository
echo "📥 Cloning repository..."
if [ -d "$APP_DIR" ]; then
    echo "Directory exists, pulling latest changes..."
    cd $APP_DIR
    git pull origin main
else
    sudo git clone $GITHUB_REPO $APP_DIR
    sudo chown -R $USER:$USER $APP_DIR
    cd $APP_DIR
fi

# 4. Python Environment Setup
echo "🐍 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Install additional production dependencies
pip install gunicorn supervisor

# 5. Frontend Build
echo "⚛️ Building React frontend..."
cd frontend
npm install
npm run build
cd ..

# 6. Create Production Environment
echo "🔐 Setting up environment..."
cp .env .env.production

# Update environment for production
cat >> .env.production << EOF

# Production Settings
FLASK_ENV=production
FLASK_DEBUG=False
VPS_IP=$VPS_IP
API_URL=http://$VPS_IP:5000
FRONTEND_URL=http://$VPS_IP:3000
SENTINEL_URL=http://$VPS_IP:8090
EOF

# 7. Configure Nginx
echo "🌐 Configuring Nginx..."
sudo tee /etc/nginx/sites-available/trading-sentinel << EOF
server {{
    listen 80;
    server_name $VPS_IP;
    
    # Frontend (React build)
    location / {{
        root $APP_DIR/frontend/dist;
        try_files \$uri \$uri/ /index.html;
        
        # CORS headers
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Authorization";
    }}
    
    # Backend API
    location /api/ {{
        proxy_pass http://127.0.0.1:5000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # CORS
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Authorization";
    }}
    
    # Sentinel Control Panel
    location /sentinel/ {{
        proxy_pass http://127.0.0.1:8090/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }}
    
    # WebSocket support
    location /ws {{
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }}
}}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/trading-sentinel /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

# 8. Create PM2 Ecosystem
echo "⚙️ Setting up PM2 processes..."
cat > ecosystem.config.js << EOF
module.exports = {{
  apps: [
    {{
      name: 'trading-backend',
      script: 'venv/bin/gunicorn',
      args: '--bind 127.0.0.1:5000 --workers 2 backend_main:app',
      cwd: '$APP_DIR',
      env: {{
        PYTHONPATH: '$APP_DIR',
        FLASK_ENV: 'production'
      }},
      restart_delay: 5000,
      max_restarts: 10
    }},
    {{
      name: 'trading-sentinel',
      script: 'venv/bin/python',
      args: 'bulenox_sentinel.py',
      cwd: '$APP_DIR',
      env: {{
        PYTHONPATH: '$APP_DIR',
        DISPLAY: ':99'
      }},
      restart_delay: 5000,
      max_restarts: 10
    }}
  ]
}};
EOF

# 9. Install Xvfb for headless browser
echo "🖥️ Installing virtual display..."
sudo apt install -y xvfb

# Create Xvfb service
sudo tee /etc/systemd/system/xvfb.service << EOF
[Unit]
Description=X Virtual Frame Buffer Service
After=network.target

[Service]
ExecStart=/usr/bin/Xvfb :99 -screen 0 1920x1080x24
Restart=on-failure
User=root

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable xvfb
sudo systemctl start xvfb

# 10. Configure Firewall
echo "🔒 Configuring firewall..."
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# 11. Start Services
echo "🚀 Starting services..."
pm2 start ecosystem.config.js
pm2 save
pm2 startup

# 12. Create Update Script
echo "📝 Creating update script..."
cat > update.sh << 'EOF'
#!/bin/bash
cd /opt/ai-trading-sentinel
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
cd frontend && npm install && npm run build && cd ..
pm2 restart all
echo "✅ Update complete!"
EOF
chmod +x update.sh

# 13. Setup Monitoring
echo "📊 Setting up monitoring..."
cat > health_check.sh << 'EOF'
#!/bin/bash
# Check if services are running
if ! pm2 list | grep -q "online"; then
    echo "⚠️ Services down, restarting..."
    pm2 restart all
fi

# Check if Nginx is running
if ! systemctl is-active --quiet nginx; then
    echo "⚠️ Nginx down, restarting..."
    sudo systemctl restart nginx
fi
EOF
chmod +x health_check.sh

# Add to crontab
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/ai-trading-sentinel/health_check.sh") | crontab -

echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo "═══════════════════════════════════════"
echo "📱 Access URLs:"
echo "   Main Dashboard: http://$VPS_IP"
echo "   API Endpoints:  http://$VPS_IP/api"
echo "   Trading Panel:  http://$VPS_IP/sentinel"
echo ""
echo "🔧 Management Commands:"
echo "   View logs:      pm2 logs"
echo "   Restart:        pm2 restart all"
echo "   Update:         ./update.sh"
echo "   Health check:   ./health_check.sh"
echo ""
echo "💡 Next Steps:"
echo "   1. Test all URLs above"
echo "   2. Configure your .env credentials"
echo "   3. Start trading!"
echo "═══════════════════════════════════════"
'''
        
        script_file = self.project_root / "deploy_vps.sh"
        with open(script_file, "w", encoding="utf-8") as f:
            f.write(deploy_script)
        
        # Make executable
        os.chmod(script_file, 0o755)
        
        return script_file
    
    def create_termius_commands(self, vps_ip, ssh_user="root"):
        """Create Termius SSH commands for easy management"""
        
        commands = f'''# 🔧 Termius SSH Commands for AI Trading Sentinel

## Initial Connection
```bash
ssh {ssh_user}@{vps_ip}
```

## Deployment Commands
```bash
# 1. Upload deployment script
scp deploy_vps.sh {ssh_user}@{vps_ip}:~/

# 2. Run deployment
ssh {ssh_user}@{vps_ip} "chmod +x deploy_vps.sh && ./deploy_vps.sh"
```

## Daily Management Commands
```bash
# Check status
ssh {ssh_user}@{vps_ip} "pm2 status"

# View logs
ssh {ssh_user}@{vps_ip} "pm2 logs --lines 50"

# Restart services
ssh {ssh_user}@{vps_ip} "pm2 restart all"

# Update application
ssh {ssh_user}@{vps_ip} "cd /opt/ai-trading-sentinel && ./update.sh"

# Check system resources
ssh {ssh_user}@{vps_ip} "htop"

# View Nginx logs
ssh {ssh_user}@{vps_ip} "sudo tail -f /var/log/nginx/access.log"
```

## Emergency Commands
```bash
# Stop all services
ssh {ssh_user}@{vps_ip} "pm2 stop all"

# Restart Nginx
ssh {ssh_user}@{vps_ip} "sudo systemctl restart nginx"

# Check disk space
ssh {ssh_user}@{vps_ip} "df -h"

# Check memory usage
ssh {ssh_user}@{vps_ip} "free -h"
```

## File Transfer
```bash
# Upload .env file
scp .env {ssh_user}@{vps_ip}:/opt/ai-trading-sentinel/.env.production

# Download logs
scp {ssh_user}@{vps_ip}:/opt/ai-trading-sentinel/logs/* ./logs/
```
'''
        
        commands_file = self.project_root / "TERMIUS_COMMANDS.md"
        with open(commands_file, "w", encoding="utf-8") as f:
            f.write(commands)
        
        return commands_file
    
    def create_github_workflow(self):
        """Create GitHub Actions workflow for auto-deployment"""
        
        workflow = '''name: Deploy to VPS

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Deploy to VPS
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: ${{ secrets.VPS_IP }}
        username: ${{ secrets.VPS_USER }}
        key: ${{ secrets.VPS_SSH_KEY }}
        script: |
          cd /opt/ai-trading-sentinel
          git pull origin main
          source venv/bin/activate
          pip install -r requirements.txt
          cd frontend && npm install && npm run build && cd ..
          pm2 restart all
          echo "✅ Deployment complete!"
'''
        
        # Create .github/workflows directory
        workflow_dir = self.project_root / ".github" / "workflows"
        workflow_dir.mkdir(parents=True, exist_ok=True)
        
        workflow_file = workflow_dir / "deploy.yml"
        with open(workflow_file, "w", encoding="utf-8") as f:
            f.write(workflow)
        
        return workflow_file
    
    def create_env_template(self):
        """Create production environment template"""
        
        env_template = '''# 🚀 AI Trading Sentinel - Production Environment
# Copy this to .env.production on your VPS

# ═══════════════════════════════════════
# 🏢 BROKER CREDENTIALS (from your .env)
# ═══════════════════════════════════════
BULENOX_USERNAME=your_bulenox_username
BULENOX_PASSWORD=your_bulenox_password
BULENOX_LOGIN_URL=https://bulenox.projectx.com/login

# ═══════════════════════════════════════
# 🌐 PRODUCTION SETTINGS
# ═══════════════════════════════════════
FLASK_ENV=production
FLASK_DEBUG=False
PYTHONPATH=/opt/ai-trading-sentinel

# ═══════════════════════════════════════
# 🔗 API ENDPOINTS (will be set by deploy script)
# ═══════════════════════════════════════
VPS_IP=YOUR_VPS_IP
API_URL=http://YOUR_VPS_IP:5000
FRONTEND_URL=http://YOUR_VPS_IP:3000
SENTINEL_URL=http://YOUR_VPS_IP:8090

# ═══════════════════════════════════════
# 📊 TRADING CONFIGURATION
# ═══════════════════════════════════════
TRADING_MODE=LIVE
RISK_LEVEL=MEDIUM
MAX_DRAWDOWN=0.05
PROFIT_TARGET=0.02

# ═══════════════════════════════════════
# 🔒 SECURITY
# ═══════════════════════════════════════
SECRET_KEY=your_secret_key_here
JWT_SECRET=your_jwt_secret_here

# ═══════════════════════════════════════
# 📱 NOTIFICATIONS (optional)
# ═══════════════════════════════════════
SLACK_WEBHOOK_URL=
EMAIL_SMTP_SERVER=
EMAIL_USERNAME=
EMAIL_PASSWORD=
'''
        
        env_file = self.project_root / ".env.production.template"
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(env_template)
        
        return env_file

def main():
    parser = argparse.ArgumentParser(description='Deploy AI Trading Sentinel without domain')
    parser.add_argument('--vps-ip', required=True, help='Your Contabo VPS IP address')
    parser.add_argument('--github-repo', required=True, help='Your GitHub repository URL')
    parser.add_argument('--ssh-user', default='root', help='SSH username (default: root)')
    
    args = parser.parse_args()
    
    deployer = NoDomainDeployer()
    
    print("🚀 Creating deployment files for IP-based access...")
    
    # Create deployment script
    script_file = deployer.create_ip_deployment_script(args.vps_ip, args.github_repo)
    print(f"✅ Created deployment script: {script_file}")
    
    # Create Termius commands
    commands_file = deployer.create_termius_commands(args.vps_ip, args.ssh_user)
    print(f"✅ Created Termius commands: {commands_file}")
    
    # Create GitHub workflow
    workflow_file = deployer.create_github_workflow()
    print(f"✅ Created GitHub workflow: {workflow_file}")
    
    # Create environment template
    env_file = deployer.create_env_template()
    print(f"✅ Created environment template: {env_file}")
    
    print("\n" + "="*60)
    print("🎉 NO-DOMAIN DEPLOYMENT READY!")
    print("="*60)
    print(f"📱 Your bot will be accessible at:")
    print(f"   Main Dashboard: http://{args.vps_ip}")
    print(f"   API Endpoints:  http://{args.vps_ip}/api")
    print(f"   Trading Panel:  http://{args.vps_ip}/sentinel")
    print("\n📋 Next Steps:")
    print("   1. Upload deploy_vps.sh to your VPS")
    print("   2. Run the deployment script")
    print("   3. Copy your .env credentials to VPS")
    print("   4. Start trading!")
    print("\n💡 Use TERMIUS_COMMANDS.md for easy SSH management")
    print("="*60)

if __name__ == "__main__":
    main()