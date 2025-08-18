#!/usr/bin/env python3
"""
deploy_contabo_playwright.py
Contabo VPS deployment script for Playwright-based Bulenox trading bot

Features:
- Automated VPS setup with Ubuntu 22.04/24.04
- Playwright browser installation
- Contract-based trading configuration
- Systemd service setup for 24/7 operation
- Nginx reverse proxy for web interface
- SSL certificate setup
- Monitoring and logging
- Auto-restart on failures

Author: TRAE-SentinelOps
Version: 2.0.0 (Playwright Migration)
Date: 2025-01-17
"""

import os
import sys
import json
import time
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ContaboDeployment')

class ContaboPlaywrightDeployer:
    """Contabo VPS deployment manager for Playwright Bulenox bot"""
    
    def __init__(self, vps_ip: str, ssh_key_path: str, domain: Optional[str] = None):
        self.vps_ip = vps_ip
        self.ssh_key_path = ssh_key_path
        self.domain = domain
        self.ssh_user = "root"  # Contabo default
        
        # Deployment configuration
        self.app_dir = "/opt/ai-trading-sentinel"
        self.service_name = "bulenox-trading-bot"
        self.web_port = 5000
        self.nginx_port = 80
        self.ssl_port = 443
        
        # Required environment variables
        self.required_env_vars = [
            'BULENOX_USERNAME',
            'BULENOX_PASSWORD',
            'GITHUB_TOKEN',  # For private repo access
            'FLASK_SECRET_KEY',
            'WEBHOOK_SECRET'
        ]
        
    def run_ssh_command(self, command: str, capture_output: bool = True) -> subprocess.CompletedProcess:
        """Run command on VPS via SSH"""
        ssh_cmd = [
            'ssh',
            '-i', self.ssh_key_path,
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            f'{self.ssh_user}@{self.vps_ip}',
            command
        ]
        
        logger.info(f"🔧 Running: {command}")
        
        try:
            result = subprocess.run(
                ssh_cmd,
                capture_output=capture_output,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                logger.error(f"❌ Command failed: {result.stderr}")
            else:
                logger.info("✅ Command completed successfully")
                
            return result
            
        except subprocess.TimeoutExpired:
            logger.error("❌ Command timed out")
            raise
        except Exception as e:
            logger.error(f"❌ SSH command error: {e}")
            raise
            
    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload file to VPS via SCP"""
        scp_cmd = [
            'scp',
            '-i', self.ssh_key_path,
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            local_path,
            f'{self.ssh_user}@{self.vps_ip}:{remote_path}'
        ]
        
        logger.info(f"📤 Uploading: {local_path} → {remote_path}")
        
        try:
            result = subprocess.run(scp_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ File uploaded successfully")
                return True
            else:
                logger.error(f"❌ Upload failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Upload error: {e}")
            return False
            
    def setup_system_dependencies(self) -> bool:
        """Install system dependencies on VPS"""
        logger.info("🔧 Setting up system dependencies...")
        
        commands = [
            # Update system
            "apt update && apt upgrade -y",
            
            # Install essential packages
            "apt install -y curl wget git vim htop unzip software-properties-common",
            
            # Install Python 3.11
            "add-apt-repository ppa:deadsnakes/ppa -y",
            "apt update",
            "apt install -y python3.11 python3.11-venv python3.11-dev python3-pip",
            
            # Install Node.js (for frontend)
            "curl -fsSL https://deb.nodesource.com/setup_20.x | bash -",
            "apt install -y nodejs",
            
            # Install Nginx
            "apt install -y nginx",
            
            # Install Docker (optional)
            "apt install -y docker.io docker-compose",
            "systemctl enable docker",
            "systemctl start docker",
            
            # Install monitoring tools
            "apt install -y htop iotop nethogs fail2ban ufw",
            
            # Configure firewall
            "ufw allow ssh",
            "ufw allow 80/tcp",
            "ufw allow 443/tcp",
            "ufw --force enable",
        ]
        
        for cmd in commands:
            try:
                result = self.run_ssh_command(cmd)
                if result.returncode != 0:
                    logger.warning(f"⚠️  Command may have issues: {cmd}")
            except Exception as e:
                logger.error(f"❌ Failed to run: {cmd} - {e}")
                return False
                
        logger.info("✅ System dependencies installed")
        return True
        
    def setup_playwright_dependencies(self) -> bool:
        """Install Playwright and browser dependencies"""
        logger.info("🎭 Setting up Playwright dependencies...")
        
        commands = [
            # Install browser dependencies
            "apt install -y libnss3-dev libatk-bridge2.0-dev libdrm-dev libxkbcommon-dev libxcomposite-dev libxdamage-dev libxrandr-dev libgbm-dev libxss-dev libasound2-dev",
            
            # Install additional dependencies for headless browsers
            "apt install -y libgtk-3-dev libx11-xcb-dev libxcb-dri3-dev",
            
            # Install fonts
            "apt install -y fonts-liberation fonts-noto-color-emoji fonts-noto-cjk",
            
            # Create app directory
            f"mkdir -p {self.app_dir}",
            f"cd {self.app_dir}",
        ]
        
        for cmd in commands:
            try:
                result = self.run_ssh_command(cmd)
                if result.returncode != 0:
                    logger.warning(f"⚠️  Command may have issues: {cmd}")
            except Exception as e:
                logger.error(f"❌ Failed to run: {cmd} - {e}")
                return False
                
        logger.info("✅ Playwright dependencies installed")
        return True
        
    def deploy_application(self, github_repo: str, branch: str = "main") -> bool:
        """Deploy application from GitHub"""
        logger.info(f"🚀 Deploying application from {github_repo}...")
        
        commands = [
            # Clone or update repository
            f"cd {self.app_dir}",
            f"if [ -d '.git' ]; then git pull origin {branch}; else git clone -b {branch} {github_repo} .; fi",
            
            # Create Python virtual environment
            "python3.11 -m venv venv",
            "source venv/bin/activate",
            
            # Install Python dependencies
            "pip install --upgrade pip",
            "pip install -r requirements.txt",
            
            # Install Playwright
            "pip install playwright",
            "playwright install",
            "playwright install-deps",
            
            # Set permissions
            f"chown -R www-data:www-data {self.app_dir}",
            f"chmod +x {self.app_dir}/*.py",
        ]
        
        for cmd in commands:
            try:
                result = self.run_ssh_command(cmd)
                if result.returncode != 0 and "git pull" not in cmd:
                    logger.warning(f"⚠️  Command may have issues: {cmd}")
            except Exception as e:
                logger.error(f"❌ Failed to run: {cmd} - {e}")
                return False
                
        logger.info("✅ Application deployed")
        return True
        
    def create_environment_file(self, env_vars: Dict[str, str]) -> bool:
        """Create .env file on VPS"""
        logger.info("🔐 Creating environment configuration...")
        
        # Validate required variables
        missing_vars = [var for var in self.required_env_vars if var not in env_vars]
        if missing_vars:
            logger.error(f"❌ Missing required environment variables: {missing_vars}")
            return False
            
        # Create .env content
        env_content = []
        for key, value in env_vars.items():
            env_content.append(f"{key}={value}")
            
        # Add deployment-specific variables
        env_content.extend([
            f"DEPLOYMENT_MODE=production",
            f"VPS_IP={self.vps_ip}",
            f"APP_DIR={self.app_dir}",
            f"WEB_PORT={self.web_port}",
            "PLAYWRIGHT_HEADLESS=true",
            "BULENOX_CONTRACT_MODE=true",  # Ensure contract mode
            "LOG_LEVEL=INFO",
        ])
        
        if self.domain:
            env_content.append(f"DOMAIN={self.domain}")
            
        # Write to temporary file and upload
        temp_env_file = "/tmp/trading_bot.env"
        try:
            with open(temp_env_file, 'w') as f:
                f.write('\n'.join(env_content))
                
            # Upload to VPS
            if self.upload_file(temp_env_file, f"{self.app_dir}/.env"):
                # Set secure permissions
                self.run_ssh_command(f"chmod 600 {self.app_dir}/.env")
                self.run_ssh_command(f"chown www-data:www-data {self.app_dir}/.env")
                
                # Clean up local temp file
                os.remove(temp_env_file)
                
                logger.info("✅ Environment file created")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to create environment file: {e}")
            return False
            
    def create_systemd_service(self) -> bool:
        """Create systemd service for 24/7 operation"""
        logger.info("⚙️  Creating systemd service...")
        
        service_content = f"""[Unit]
Description=Bulenox Trading Bot (Playwright)
After=network.target
Wants=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory={self.app_dir}
Environment=PATH={self.app_dir}/venv/bin
ExecStart={self.app_dir}/venv/bin/python bulenox_ai_playwright_contracts.py --headless
Restart=always
RestartSec=10
KillMode=mixed
TimeoutStopSec=30

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier={self.service_name}

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths={self.app_dir}

# Resource limits
LimitNOFILE=65536
MemoryMax=2G
CPUQuota=200%

[Install]
WantedBy=multi-user.target
"""
        
        # Write service file
        temp_service_file = "/tmp/trading_bot.service"
        try:
            with open(temp_service_file, 'w') as f:
                f.write(service_content)
                
            # Upload and install service
            if self.upload_file(temp_service_file, f"/etc/systemd/system/{self.service_name}.service"):
                commands = [
                    "systemctl daemon-reload",
                    f"systemctl enable {self.service_name}",
                    f"systemctl start {self.service_name}",
                ]
                
                for cmd in commands:
                    result = self.run_ssh_command(cmd)
                    if result.returncode != 0:
                        logger.error(f"❌ Service setup failed: {cmd}")
                        return False
                        
                # Clean up
                os.remove(temp_service_file)
                
                logger.info("✅ Systemd service created and started")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to create service: {e}")
            return False
            
    def setup_nginx_proxy(self) -> bool:
        """Setup Nginx reverse proxy for web interface"""
        logger.info("🌐 Setting up Nginx reverse proxy...")
        
        server_name = self.domain if self.domain else self.vps_ip
        
        nginx_config = f"""server {{
    listen 80;
    server_name {server_name};
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    # Static files
    location /static/ {{
        alias {self.app_dir}/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }}
    
    # API endpoints
    location /api/ {{
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://127.0.0.1:{self.web_port};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }}
    
    # Main application
    location / {{
        proxy_pass http://127.0.0.1:{self.web_port};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
    
    # Health check
    location /health {{
        access_log off;
        return 200 "healthy\\n";
        add_header Content-Type text/plain;
    }}
}}
"""
        
        # Write nginx config
        temp_nginx_file = "/tmp/trading_bot_nginx.conf"
        try:
            with open(temp_nginx_file, 'w') as f:
                f.write(nginx_config)
                
            # Upload and configure
            if self.upload_file(temp_nginx_file, "/etc/nginx/sites-available/trading-bot"):
                commands = [
                    "ln -sf /etc/nginx/sites-available/trading-bot /etc/nginx/sites-enabled/",
                    "rm -f /etc/nginx/sites-enabled/default",
                    "nginx -t",
                    "systemctl reload nginx",
                ]
                
                for cmd in commands:
                    result = self.run_ssh_command(cmd)
                    if result.returncode != 0:
                        logger.error(f"❌ Nginx setup failed: {cmd}")
                        return False
                        
                # Clean up
                os.remove(temp_nginx_file)
                
                logger.info("✅ Nginx proxy configured")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to setup Nginx: {e}")
            return False
            
    def setup_ssl_certificate(self) -> bool:
        """Setup SSL certificate with Let's Encrypt"""
        if not self.domain:
            logger.info("⚠️  No domain provided, skipping SSL setup")
            return True
            
        logger.info("🔒 Setting up SSL certificate...")
        
        commands = [
            "apt install -y certbot python3-certbot-nginx",
            f"certbot --nginx -d {self.domain} --non-interactive --agree-tos --email admin@{self.domain}",
            "systemctl enable certbot.timer",
        ]
        
        for cmd in commands:
            try:
                result = self.run_ssh_command(cmd)
                if result.returncode != 0:
                    logger.warning(f"⚠️  SSL command may have issues: {cmd}")
            except Exception as e:
                logger.error(f"❌ SSL setup error: {e}")
                return False
                
        logger.info("✅ SSL certificate configured")
        return True
        
    def setup_monitoring(self) -> bool:
        """Setup monitoring and logging"""
        logger.info("📊 Setting up monitoring...")
        
        # Create log rotation config
        logrotate_config = f"""{self.app_dir}/logs/*.log {{
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload {self.service_name}
    endscript
}}
"""
        
        # Create monitoring script
        monitor_script = f"""#!/bin/bash
# Trading bot health monitor

SERVICE_NAME="{self.service_name}"
LOG_FILE="{self.app_dir}/logs/monitor.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# Check if service is running
if ! systemctl is-active --quiet $SERVICE_NAME; then
    echo "[$DATE] ERROR: Service $SERVICE_NAME is not running, restarting..." >> $LOG_FILE
    systemctl restart $SERVICE_NAME
    sleep 10
    
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo "[$DATE] INFO: Service $SERVICE_NAME restarted successfully" >> $LOG_FILE
    else
        echo "[$DATE] CRITICAL: Failed to restart service $SERVICE_NAME" >> $LOG_FILE
    fi
fi

# Check disk space
DISK_USAGE=$(df {self.app_dir} | awk 'NR==2 {{print $5}}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
    echo "[$DATE] WARNING: Disk usage is $DISK_USAGE%" >> $LOG_FILE
fi

# Check memory usage
MEM_USAGE=$(free | awk 'NR==2{{printf "%.0f", $3*100/$2}}')
if [ $MEM_USAGE -gt 90 ]; then
    echo "[$DATE] WARNING: Memory usage is $MEM_USAGE%" >> $LOG_FILE
fi
"""
        
        try:
            # Write files
            temp_logrotate = "/tmp/trading_bot_logrotate"
            temp_monitor = "/tmp/trading_bot_monitor.sh"
            
            with open(temp_logrotate, 'w') as f:
                f.write(logrotate_config)
            with open(temp_monitor, 'w') as f:
                f.write(monitor_script)
                
            # Upload files
            if (self.upload_file(temp_logrotate, "/etc/logrotate.d/trading-bot") and
                self.upload_file(temp_monitor, "/usr/local/bin/trading-bot-monitor.sh")):
                
                commands = [
                    "chmod +x /usr/local/bin/trading-bot-monitor.sh",
                    f"mkdir -p {self.app_dir}/logs",
                    f"chown -R www-data:www-data {self.app_dir}/logs",
                    # Add cron job for monitoring
                    "(crontab -l 2>/dev/null; echo '*/5 * * * * /usr/local/bin/trading-bot-monitor.sh') | crontab -",
                ]
                
                for cmd in commands:
                    self.run_ssh_command(cmd)
                    
                # Clean up
                os.remove(temp_logrotate)
                os.remove(temp_monitor)
                
                logger.info("✅ Monitoring configured")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to setup monitoring: {e}")
            return False
            
    def deploy_full_stack(self, github_repo: str, env_vars: Dict[str, str], 
                          branch: str = "main") -> bool:
        """Complete deployment process"""
        logger.info("🚀 Starting full stack deployment...")
        logger.info("=" * 60)
        
        deployment_steps = [
            ("System Dependencies", self.setup_system_dependencies),
            ("Playwright Dependencies", self.setup_playwright_dependencies),
            ("Application Deployment", lambda: self.deploy_application(github_repo, branch)),
            ("Environment Configuration", lambda: self.create_environment_file(env_vars)),
            ("Systemd Service", self.create_systemd_service),
            ("Nginx Proxy", self.setup_nginx_proxy),
            ("SSL Certificate", self.setup_ssl_certificate),
            ("Monitoring Setup", self.setup_monitoring),
        ]
        
        for step_name, step_func in deployment_steps:
            logger.info(f"📋 Step: {step_name}")
            try:
                if not step_func():
                    logger.error(f"❌ Deployment failed at step: {step_name}")
                    return False
                logger.info(f"✅ Step completed: {step_name}")
            except Exception as e:
                logger.error(f"❌ Step crashed: {step_name} - {e}")
                return False
                
        logger.info("=" * 60)
        logger.info("🎉 Deployment completed successfully!")
        logger.info(f"🌐 Access your bot at: http://{self.vps_ip}")
        if self.domain:
            logger.info(f"🌐 Or at: https://{self.domain}")
        logger.info(f"📊 Monitor service: systemctl status {self.service_name}")
        logger.info(f"📋 View logs: journalctl -u {self.service_name} -f")
        
        return True
        
    def get_deployment_status(self) -> Dict[str, Any]:
        """Get current deployment status"""
        logger.info("📊 Checking deployment status...")
        
        status = {
            'timestamp': datetime.now().isoformat(),
            'vps_ip': self.vps_ip,
            'services': {},
            'system': {},
            'application': {}
        }
        
        try:
            # Check service status
            result = self.run_ssh_command(f"systemctl is-active {self.service_name}")
            status['services']['trading_bot'] = result.stdout.strip() if result.returncode == 0 else 'inactive'
            
            result = self.run_ssh_command("systemctl is-active nginx")
            status['services']['nginx'] = result.stdout.strip() if result.returncode == 0 else 'inactive'
            
            # Check system resources
            result = self.run_ssh_command("free -m | awk 'NR==2{printf \"%.0f\", $3*100/$2}'")
            if result.returncode == 0:
                status['system']['memory_usage_percent'] = int(result.stdout.strip())
                
            result = self.run_ssh_command(f"df {self.app_dir} | awk 'NR==2 {{print $5}}' | sed 's/%//'")
            if result.returncode == 0:
                status['system']['disk_usage_percent'] = int(result.stdout.strip())
                
            # Check application
            result = self.run_ssh_command(f"ls -la {self.app_dir}/.env")
            status['application']['env_file_exists'] = result.returncode == 0
            
            result = self.run_ssh_command(f"ls -la {self.app_dir}/bulenox_ai_playwright_contracts.py")
            status['application']['main_script_exists'] = result.returncode == 0
            
        except Exception as e:
            logger.error(f"❌ Status check error: {e}")
            status['error'] = str(e)
            
        return status


def main():
    """Main deployment function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deploy Bulenox Trading Bot to Contabo VPS')
    parser.add_argument('--vps-ip', required=True, help='VPS IP address')
    parser.add_argument('--ssh-key', required=True, help='Path to SSH private key')
    parser.add_argument('--github-repo', required=True, help='GitHub repository URL')
    parser.add_argument('--domain', help='Domain name for SSL')
    parser.add_argument('--branch', default='main', help='Git branch to deploy')
    parser.add_argument('--env-file', help='Path to environment variables file')
    parser.add_argument('--status-only', action='store_true', help='Only check deployment status')
    
    args = parser.parse_args()
    
    # Create deployer
    deployer = ContaboPlaywrightDeployer(
        vps_ip=args.vps_ip,
        ssh_key_path=args.ssh_key,
        domain=args.domain
    )
    
    if args.status_only:
        # Just check status
        status = deployer.get_deployment_status()
        print(json.dumps(status, indent=2))
        return
        
    # Load environment variables
    env_vars = {}
    if args.env_file:
        try:
            with open(args.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key] = value
        except Exception as e:
            logger.error(f"❌ Failed to load env file: {e}")
            sys.exit(1)
    else:
        # Get from environment
        for var in deployer.required_env_vars:
            value = os.getenv(var)
            if value:
                env_vars[var] = value
            else:
                logger.error(f"❌ Missing environment variable: {var}")
                sys.exit(1)
                
    # Deploy
    try:
        success = deployer.deploy_full_stack(
            github_repo=args.github_repo,
            env_vars=env_vars,
            branch=args.branch
        )
        
        if success:
            logger.info("🎉 Deployment completed successfully!")
            sys.exit(0)
        else:
            logger.error("💥 Deployment failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("👋 Deployment interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ Deployment crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()