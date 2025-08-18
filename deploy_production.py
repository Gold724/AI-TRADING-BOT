#!/usr/bin/env python3
"""
🚀 AI Trading Sentinel - Production Deployment Script

This script deploys all three components to a VPS:
1. React Frontend (built and served via Nginx)
2. Flask Backend API (port 5000)
3. Bulenox Sentinel Control Panel (port 8090)

Usage:
    python3 deploy_production.py --domain your-domain.com --email your@email.com
"""

import os
import sys
import subprocess
import argparse
import json
from pathlib import Path

class ProductionDeployer:
    def __init__(self, domain, email, vps_user="root"):
        self.domain = domain
        self.email = email
        self.vps_user = vps_user
        self.app_dir = "/opt/ai-trading-sentinel"
        
    def run_command(self, cmd, check=True):
        """Execute shell command with error handling"""
        print(f"🔧 Running: {cmd}")
        try:
            result = subprocess.run(cmd, shell=True, check=check, 
                                  capture_output=True, text=True)
            if result.stdout:
                print(result.stdout)
            return result
        except subprocess.CalledProcessError as e:
            print(f"❌ Error: {e}")
            if e.stderr:
                print(f"Error output: {e.stderr}")
            if check:
                sys.exit(1)
            return e
    
    def setup_system(self):
        """Install system dependencies"""
        print("📦 Installing system dependencies...")
        
        commands = [
            "sudo apt update && sudo apt upgrade -y",
            "sudo apt install -y python3.10 python3-pip nodejs npm nginx git curl wget unzip",
            "sudo apt install -y chromium-browser xvfb",  # For headless browser
            "curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh",
            "sudo npm install -g pm2",
            "sudo ufw allow 22,80,443/tcp",
            "sudo ufw --force enable"
        ]
        
        for cmd in commands:
            self.run_command(cmd)
    
    def setup_app_directory(self):
        """Create and setup application directory"""
        print(f"📁 Setting up application directory: {self.app_dir}")
        
        commands = [
            f"sudo mkdir -p {self.app_dir}",
            f"sudo chown {self.vps_user}:{self.vps_user} {self.app_dir}",
            f"cd {self.app_dir} && git clone https://github.com/YOUR_USERNAME/ai-trading-sentinel.git ."
        ]
        
        for cmd in commands:
            self.run_command(cmd)
    
    def setup_python_environment(self):
        """Setup Python virtual environment and dependencies"""
        print("🐍 Setting up Python environment...")
        
        commands = [
            f"cd {self.app_dir} && python3 -m venv venv",
            f"cd {self.app_dir} && source venv/bin/activate && pip install --upgrade pip",
            f"cd {self.app_dir} && source venv/bin/activate && pip install -r requirements.txt",
            f"cd {self.app_dir} && source venv/bin/activate && pip install gunicorn"
        ]
        
        for cmd in commands:
            self.run_command(cmd)
    
    def setup_frontend(self):
        """Build React frontend for production"""
        print("⚛️ Building React frontend...")
        
        # Create production environment file for frontend
        frontend_env = f"""
VITE_API_URL=https://{self.domain}/api
VITE_WEBSOCKET_URL=wss://{self.domain}/ws
VITE_ENVIRONMENT=production
"""
        
        with open(f"{self.app_dir}/frontend/.env.production", "w") as f:
            f.write(frontend_env)
        
        commands = [
            f"cd {self.app_dir}/frontend && npm install",
            f"cd {self.app_dir}/frontend && npm run build"
        ]
        
        for cmd in commands:
            self.run_command(cmd)
    
    def setup_nginx(self):
        """Configure Nginx for all three services"""
        print("🌐 Configuring Nginx...")
        
        nginx_config = f"""
server {{
    listen 80;
    server_name {self.domain} www.{self.domain};
    return 301 https://$server_name$request_uri;
}}

server {{
    listen 443 ssl http2;
    server_name {self.domain} www.{self.domain};
    
    # SSL Configuration (will be added by Certbot)
    
    # Frontend (React build)
    location / {{
        root {self.app_dir}/frontend/dist;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {{
            expires 1y;
            add_header Cache-Control "public, immutable";
        }}
    }}
    
    # Backend API
    location /api/ {{
        proxy_pass http://127.0.0.1:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
    }}
    
    # Bulenox Sentinel Control Panel
    location /sentinel/ {{
        proxy_pass http://127.0.0.1:8090/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        rewrite ^/sentinel/(.*) /$1 break;
    }}
    
    # WebSocket support
    location /ws/ {{
        proxy_pass http://127.0.0.1:5000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }}
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
}}
"""
        
        # Write Nginx configuration
        with open(f"/etc/nginx/sites-available/{self.domain}", "w") as f:
            f.write(nginx_config)
        
        commands = [
            f"sudo ln -sf /etc/nginx/sites-available/{self.domain} /etc/nginx/sites-enabled/",
            "sudo rm -f /etc/nginx/sites-enabled/default",
            "sudo nginx -t",
            "sudo systemctl restart nginx"
        ]
        
        for cmd in commands:
            self.run_command(cmd)
    
    def setup_ssl(self):
        """Setup SSL certificates with Let's Encrypt"""
        print("🔒 Setting up SSL certificates...")
        
        commands = [
            "sudo apt install certbot python3-certbot-nginx -y",
            f"sudo certbot --nginx -d {self.domain} -d www.{self.domain} --email {self.email} --agree-tos --non-interactive",
            "sudo systemctl enable certbot.timer"
        ]
        
        for cmd in commands:
            self.run_command(cmd)
    
    def setup_pm2(self):
        """Configure PM2 for process management"""
        print("⚙️ Setting up PM2 process management...")
        
        pm2_config = {
            "apps": [
                {
                    "name": "ai-trading-backend",
                    "script": "backend_main.py",
                    "cwd": self.app_dir,
                    "interpreter": f"{self.app_dir}/venv/bin/python",
                    "env": {
                        "FLASK_ENV": "production",
                        "PORT": "5000",
                        "PYTHONPATH": self.app_dir
                    },
                    "instances": 1,
                    "autorestart": True,
                    "watch": False,
                    "max_memory_restart": "1G",
                    "error_file": "/var/log/ai-trading/backend-error.log",
                    "out_file": "/var/log/ai-trading/backend-out.log",
                    "log_file": "/var/log/ai-trading/backend-combined.log"
                },
                {
                    "name": "bulenox-sentinel",
                    "script": "bulenox_sentinel.py",
                    "cwd": self.app_dir,
                    "interpreter": f"{self.app_dir}/venv/bin/python",
                    "env": {
                        "PORT": "8090",
                        "PYTHONPATH": self.app_dir,
                        "DISPLAY": ":99"
                    },
                    "instances": 1,
                    "autorestart": True,
                    "watch": False,
                    "max_memory_restart": "2G",
                    "error_file": "/var/log/ai-trading/sentinel-error.log",
                    "out_file": "/var/log/ai-trading/sentinel-out.log",
                    "log_file": "/var/log/ai-trading/sentinel-combined.log"
                }
            ]
        }
        
        # Create log directory
        self.run_command("sudo mkdir -p /var/log/ai-trading")
        self.run_command(f"sudo chown {self.vps_user}:{self.vps_user} /var/log/ai-trading")
        
        # Write PM2 configuration
        with open(f"{self.app_dir}/ecosystem.config.json", "w") as f:
            json.dump(pm2_config, f, indent=2)
        
        # Start services with PM2
        commands = [
            f"cd {self.app_dir} && pm2 start ecosystem.config.json",
            "pm2 save",
            "pm2 startup"
        ]
        
        for cmd in commands:
            self.run_command(cmd)
    
    def setup_monitoring(self):
        """Setup monitoring and health checks"""
        print("📊 Setting up monitoring...")
        
        # Create health check script
        health_check_script = f"""
#!/usr/bin/env python3
import requests
import sys
from datetime import datetime

def check_services():
    services = {{
        'Frontend': 'https://{self.domain}',
        'Backend API': 'https://{self.domain}/api/health',
        'Sentinel': 'https://{self.domain}/sentinel'
    }}
    
    all_ok = True
    for name, url in services.items():
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ {{name}}: OK")
            else:
                print(f"⚠️ {{name}}: HTTP {{response.status_code}}")
                all_ok = False
        except Exception as e:
            print(f"❌ {{name}}: {{str(e)}}")
            all_ok = False
    
    if not all_ok:
        sys.exit(1)

if __name__ == "__main__":
    check_services()
"""
        
        with open(f"{self.app_dir}/health_check.py", "w") as f:
            f.write(health_check_script)
        
        self.run_command(f"chmod +x {self.app_dir}/health_check.py")
        
        # Add cron jobs
        cron_jobs = f"""
# Health check every 5 minutes
*/5 * * * * {self.app_dir}/venv/bin/python {self.app_dir}/health_check.py >> /var/log/ai-trading/health.log 2>&1

# SSL certificate renewal
0 12 * * * /usr/bin/certbot renew --quiet

# PM2 log rotation
0 0 * * * pm2 flush
"""
        
        # Install cron jobs
        self.run_command(f'echo "{cron_jobs}" | crontab -')
    
    def create_deployment_script(self):
        """Create automated deployment script for updates"""
        print("🔄 Creating deployment script...")
        
        deploy_script = f"""
#!/bin/bash
set -e

echo "🚀 Deploying AI Trading Sentinel..."

# Navigate to app directory
cd {self.app_dir}

# Pull latest changes
git pull origin main

# Update Python dependencies
source venv/bin/activate
pip install -r requirements.txt

# Build frontend
cd frontend
npm install
npm run build
cd ..

# Restart services
pm2 restart all

# Reload Nginx
sudo nginx -t && sudo systemctl reload nginx

echo "✅ Deployment complete!"
echo "🌐 Frontend: https://{self.domain}"
echo "🔧 API: https://{self.domain}/api"
echo "🎛️ Sentinel: https://{self.domain}/sentinel"
"""
        
        with open(f"{self.app_dir}/deploy.sh", "w") as f:
            f.write(deploy_script)
        
        self.run_command(f"chmod +x {self.app_dir}/deploy.sh")
    
    def deploy(self):
        """Run complete deployment process"""
        print(f"🚀 Starting production deployment for {self.domain}...")
        
        try:
            self.setup_system()
            self.setup_app_directory()
            self.setup_python_environment()
            self.setup_frontend()
            self.setup_nginx()
            self.setup_ssl()
            self.setup_pm2()
            self.setup_monitoring()
            self.create_deployment_script()
            
            print("\n" + "="*60)
            print("🎉 DEPLOYMENT SUCCESSFUL!")
            print("="*60)
            print(f"🌐 Main Dashboard: https://{self.domain}")
            print(f"🔧 Trading API: https://{self.domain}/api")
            print(f"🎛️ Sentinel Control: https://{self.domain}/sentinel")
            print(f"📊 Health Check: https://{self.domain}/api/health")
            print("\n📱 All interfaces are mobile-responsive!")
            print("\n🔧 Management Commands:")
            print(f"  - Check status: pm2 status")
            print(f"  - View logs: pm2 logs")
            print(f"  - Deploy updates: {self.app_dir}/deploy.sh")
            print(f"  - Health check: {self.app_dir}/health_check.py")
            
        except Exception as e:
            print(f"❌ Deployment failed: {e}")
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Deploy AI Trading Sentinel to production')
    parser.add_argument('--domain', required=True, help='Your domain name (e.g., trading.example.com)')
    parser.add_argument('--email', required=True, help='Email for SSL certificates')
    parser.add_argument('--user', default='root', help='VPS username (default: root)')
    
    args = parser.parse_args()
    
    deployer = ProductionDeployer(args.domain, args.email, args.user)
    deployer.deploy()

if __name__ == "__main__":
    main()