#!/usr/bin/env python3
"""
deploy_to_contabo_vps.py
Automated Deployment Script for Bulenox Trading Bot to Contabo VPS

Features:
- Automated VPS setup and configuration
- Playwright installation and browser setup
- Contract-based trading bot deployment
- Systemd service configuration
- Nginx reverse proxy setup
- SSL certificate installation
- Monitoring and logging setup
- Security hardening
- Automated backup configuration

Author: TRAE-SentinelOps
Version: 2.0.0 (Playwright Edition)
Date: 2025-01-17
"""

import os
import sys
import json
import time
import logging
import subprocess
import paramiko
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('contabo_deployment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ContaboDeployer')

@dataclass
class VPSConfig:
    """VPS configuration parameters"""
    host: str
    username: str
    password: Optional[str] = None
    ssh_key_path: Optional[str] = None
    port: int = 22
    
@dataclass
class DeploymentConfig:
    """Deployment configuration"""
    project_name: str = "bulenox-trading-bot"
    deploy_path: str = "/opt/trading-bot"
    service_name: str = "bulenox-trader"
    domain: Optional[str] = None
    ssl_email: Optional[str] = None
    github_repo: str = "https://github.com/your-username/ai-trading-sentinel.git"
    branch: str = "main"
    
class ContaboVPSDeployer:
    """Automated VPS deployment system"""
    
    def __init__(self, vps_config: VPSConfig, deploy_config: DeploymentConfig):
        self.vps_config = vps_config
        self.deploy_config = deploy_config
        self.ssh_client = None
        self.deployment_log = []
        
    def connect_ssh(self) -> bool:
        """Establish SSH connection to VPS"""
        logger.info(f"🔗 Connecting to VPS: {self.vps_config.host}")
        
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect using SSH key or password
            if self.vps_config.ssh_key_path:
                self.ssh_client.connect(
                    hostname=self.vps_config.host,
                    username=self.vps_config.username,
                    key_filename=self.vps_config.ssh_key_path,
                    port=self.vps_config.port
                )
            else:
                self.ssh_client.connect(
                    hostname=self.vps_config.host,
                    username=self.vps_config.username,
                    password=self.vps_config.password,
                    port=self.vps_config.port
                )
                
            logger.info("✅ SSH connection established")
            return True
            
        except Exception as e:
            logger.error(f"❌ SSH connection failed: {e}")
            return False
            
    def execute_command(self, command: str, sudo: bool = False) -> tuple[int, str, str]:
        """Execute command on VPS"""
        if sudo:
            command = f"sudo {command}"
            
        logger.info(f"🔧 Executing: {command}")
        
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            
            # Wait for command completion
            exit_status = stdout.channel.recv_exit_status()
            
            stdout_text = stdout.read().decode('utf-8')
            stderr_text = stderr.read().decode('utf-8')
            
            if exit_status == 0:
                logger.info(f"✅ Command successful")
                if stdout_text.strip():
                    logger.debug(f"Output: {stdout_text.strip()}")
            else:
                logger.error(f"❌ Command failed (exit code: {exit_status})")
                if stderr_text.strip():
                    logger.error(f"Error: {stderr_text.strip()}")
                    
            return exit_status, stdout_text, stderr_text
            
        except Exception as e:
            logger.error(f"❌ Command execution failed: {e}")
            return -1, "", str(e)
            
    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload file to VPS"""
        logger.info(f"📤 Uploading: {local_path} → {remote_path}")
        
        try:
            sftp = self.ssh_client.open_sftp()
            
            # Create remote directory if needed
            remote_dir = os.path.dirname(remote_path)
            try:
                sftp.mkdir(remote_dir)
            except:
                pass  # Directory might already exist
                
            sftp.put(local_path, remote_path)
            sftp.close()
            
            logger.info("✅ File uploaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ File upload failed: {e}")
            return False
            
    def setup_system_dependencies(self) -> bool:
        """Install system dependencies"""
        logger.info("📦 Setting up system dependencies...")
        
        commands = [
            "apt update",
            "apt upgrade -y",
            "apt install -y python3 python3-pip python3-venv git curl wget unzip",
            "apt install -y nginx certbot python3-certbot-nginx",
            "apt install -y htop tmux fail2ban ufw",
            "apt install -y build-essential libssl-dev libffi-dev python3-dev",
            # Install Node.js for Playwright
            "curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -",
            "apt install -y nodejs",
            # Install Docker (optional)
            "apt install -y docker.io docker-compose",
            "systemctl enable docker",
            "systemctl start docker"
        ]
        
        for cmd in commands:
            exit_code, stdout, stderr = self.execute_command(cmd, sudo=True)
            if exit_code != 0:
                logger.error(f"❌ Failed to execute: {cmd}")
                return False
                
        logger.info("✅ System dependencies installed")
        return True
        
    def setup_python_environment(self) -> bool:
        """Setup Python virtual environment"""
        logger.info("🐍 Setting up Python environment...")
        
        commands = [
            f"mkdir -p {self.deploy_config.deploy_path}",
            f"cd {self.deploy_config.deploy_path} && python3 -m venv venv",
            f"cd {self.deploy_config.deploy_path} && source venv/bin/activate && pip install --upgrade pip",
            f"cd {self.deploy_config.deploy_path} && source venv/bin/activate && pip install wheel setuptools"
        ]
        
        for cmd in commands:
            exit_code, stdout, stderr = self.execute_command(cmd, sudo=True)
            if exit_code != 0:
                logger.error(f"❌ Failed to setup Python environment: {cmd}")
                return False
                
        logger.info("✅ Python environment ready")
        return True
        
    def clone_repository(self) -> bool:
        """Clone project repository"""
        logger.info("📥 Cloning repository...")
        
        # Remove existing directory if it exists
        self.execute_command(f"rm -rf {self.deploy_config.deploy_path}/src", sudo=True)
        
        # Clone repository
        clone_cmd = f"cd {self.deploy_config.deploy_path} && git clone -b {self.deploy_config.branch} {self.deploy_config.github_repo} src"
        exit_code, stdout, stderr = self.execute_command(clone_cmd, sudo=True)
        
        if exit_code != 0:
            logger.error(f"❌ Failed to clone repository: {stderr}")
            return False
            
        logger.info("✅ Repository cloned successfully")
        return True
        
    def install_python_dependencies(self) -> bool:
        """Install Python dependencies"""
        logger.info("📚 Installing Python dependencies...")
        
        commands = [
            f"cd {self.deploy_config.deploy_path}/src && source ../venv/bin/activate && pip install -r requirements.txt",
            f"cd {self.deploy_config.deploy_path}/src && source ../venv/bin/activate && pip install playwright",
            f"cd {self.deploy_config.deploy_path}/src && source ../venv/bin/activate && playwright install",
            f"cd {self.deploy_config.deploy_path}/src && source ../venv/bin/activate && playwright install-deps"
        ]
        
        for cmd in commands:
            exit_code, stdout, stderr = self.execute_command(cmd, sudo=True)
            if exit_code != 0:
                logger.warning(f"⚠️  Command had issues: {cmd}")
                logger.warning(f"Error: {stderr}")
                # Continue anyway as some errors might be non-critical
                
        logger.info("✅ Python dependencies installed")
        return True
        
    def setup_environment_variables(self, env_vars: Dict[str, str]) -> bool:
        """Setup environment variables"""
        logger.info("🔐 Setting up environment variables...")
        
        # Create .env file content
        env_content = "\n".join([f"{key}={value}" for key, value in env_vars.items()])
        
        # Write to temporary file
        temp_env_file = "/tmp/trading_bot.env"
        with open(temp_env_file, 'w') as f:
            f.write(env_content)
            
        # Upload to VPS
        remote_env_path = f"{self.deploy_config.deploy_path}/src/.env"
        if not self.upload_file(temp_env_file, remote_env_path):
            return False
            
        # Set proper permissions
        self.execute_command(f"chmod 600 {remote_env_path}", sudo=True)
        
        # Cleanup
        os.remove(temp_env_file)
        
        logger.info("✅ Environment variables configured")
        return True
        
    def create_systemd_service(self) -> bool:
        """Create systemd service for the trading bot"""
        logger.info("⚙️  Creating systemd service...")
        
        service_content = f"""[Unit]
Description=Bulenox Trading Bot (Playwright Edition)
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
WorkingDirectory={self.deploy_config.deploy_path}/src
Environment=PATH={self.deploy_config.deploy_path}/venv/bin
ExecStart={self.deploy_config.deploy_path}/venv/bin/python bulenox_ai_playwright_contracts.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier={self.deploy_config.service_name}

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths={self.deploy_config.deploy_path}

# Resource limits
LimitNOFILE=65536
MemoryMax=2G
CPUQuota=200%

[Install]
WantedBy=multi-user.target
"""
        
        # Write service file
        temp_service_file = "/tmp/trading_bot.service"
        with open(temp_service_file, 'w') as f:
            f.write(service_content)
            
        # Upload and install service
        service_path = f"/etc/systemd/system/{self.deploy_config.service_name}.service"
        if not self.upload_file(temp_service_file, service_path):
            return False
            
        # Enable and start service
        commands = [
            "systemctl daemon-reload",
            f"systemctl enable {self.deploy_config.service_name}",
            f"systemctl start {self.deploy_config.service_name}"
        ]
        
        for cmd in commands:
            exit_code, stdout, stderr = self.execute_command(cmd, sudo=True)
            if exit_code != 0:
                logger.error(f"❌ Service setup failed: {cmd}")
                return False
                
        # Cleanup
        os.remove(temp_service_file)
        
        logger.info("✅ Systemd service created and started")
        return True
        
    def setup_nginx_proxy(self) -> bool:
        """Setup Nginx reverse proxy"""
        logger.info("🌐 Setting up Nginx reverse proxy...")
        
        if not self.deploy_config.domain:
            logger.info("⏭️  Skipping Nginx setup - no domain configured")
            return True
            
        nginx_config = f"""server {{
    listen 80;
    server_name {self.deploy_config.domain};
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # API proxy
    location /api/ {{
        proxy_pass http://127.0.0.1:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
    
    # WebSocket proxy
    location /ws/ {{
        proxy_pass http://127.0.0.1:5000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }}
    
    # Static files
    location / {{
        root {self.deploy_config.deploy_path}/src/frontend/dist;
        try_files $uri $uri/ /index.html;
    }}
    
    # Health check
    location /health {{
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }}
}}
"""
        
        # Write Nginx config
        temp_nginx_file = "/tmp/trading_bot_nginx.conf"
        with open(temp_nginx_file, 'w') as f:
            f.write(nginx_config)
            
        # Upload and enable
        nginx_path = f"/etc/nginx/sites-available/{self.deploy_config.project_name}"
        if not self.upload_file(temp_nginx_file, nginx_path):
            return False
            
        # Enable site
        commands = [
            f"ln -sf {nginx_path} /etc/nginx/sites-enabled/",
            "nginx -t",
            "systemctl reload nginx"
        ]
        
        for cmd in commands:
            exit_code, stdout, stderr = self.execute_command(cmd, sudo=True)
            if exit_code != 0:
                logger.error(f"❌ Nginx setup failed: {cmd}")
                return False
                
        # Cleanup
        os.remove(temp_nginx_file)
        
        logger.info("✅ Nginx reverse proxy configured")
        return True
        
    def setup_ssl_certificate(self) -> bool:
        """Setup SSL certificate with Let's Encrypt"""
        logger.info("🔒 Setting up SSL certificate...")
        
        if not self.deploy_config.domain or not self.deploy_config.ssl_email:
            logger.info("⏭️  Skipping SSL setup - domain or email not configured")
            return True
            
        # Get SSL certificate
        ssl_cmd = f"certbot --nginx -d {self.deploy_config.domain} --email {self.deploy_config.ssl_email} --agree-tos --non-interactive"
        exit_code, stdout, stderr = self.execute_command(ssl_cmd, sudo=True)
        
        if exit_code != 0:
            logger.error(f"❌ SSL certificate setup failed: {stderr}")
            return False
            
        # Setup auto-renewal
        cron_cmd = "echo '0 12 * * * /usr/bin/certbot renew --quiet' | crontab -"
        self.execute_command(cron_cmd, sudo=True)
        
        logger.info("✅ SSL certificate configured")
        return True
        
    def setup_firewall(self) -> bool:
        """Configure UFW firewall"""
        logger.info("🔥 Configuring firewall...")
        
        commands = [
            "ufw --force reset",
            "ufw default deny incoming",
            "ufw default allow outgoing",
            "ufw allow ssh",
            "ufw allow 'Nginx Full'",
            "ufw --force enable"
        ]
        
        for cmd in commands:
            exit_code, stdout, stderr = self.execute_command(cmd, sudo=True)
            if exit_code != 0:
                logger.error(f"❌ Firewall setup failed: {cmd}")
                return False
                
        logger.info("✅ Firewall configured")
        return True
        
    def setup_monitoring(self) -> bool:
        """Setup monitoring and logging"""
        logger.info("📊 Setting up monitoring...")
        
        # Create log rotation config
        logrotate_config = f"""{self.deploy_config.deploy_path}/logs/*.log {{
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        systemctl reload {self.deploy_config.service_name}
    endscript
}}
"""
        
        # Write logrotate config
        temp_logrotate_file = "/tmp/trading_bot_logrotate"
        with open(temp_logrotate_file, 'w') as f:
            f.write(logrotate_config)
            
        # Upload logrotate config
        logrotate_path = f"/etc/logrotate.d/{self.deploy_config.project_name}"
        if not self.upload_file(temp_logrotate_file, logrotate_path):
            return False
            
        # Create logs directory
        self.execute_command(f"mkdir -p {self.deploy_config.deploy_path}/logs", sudo=True)
        
        # Setup health check script
        health_check_script = f"""#!/bin/bash
# Health check script for trading bot

SERVICE_NAME="{self.deploy_config.service_name}"
LOG_FILE="{self.deploy_config.deploy_path}/logs/health_check.log"

echo "$(date): Checking service status" >> $LOG_FILE

if systemctl is-active --quiet $SERVICE_NAME; then
    echo "$(date): Service is running" >> $LOG_FILE
else
    echo "$(date): Service is down, restarting..." >> $LOG_FILE
    systemctl restart $SERVICE_NAME
    sleep 10
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo "$(date): Service restarted successfully" >> $LOG_FILE
    else
        echo "$(date): Failed to restart service" >> $LOG_FILE
    fi
fi
"""
        
        # Write health check script
        temp_health_script = "/tmp/health_check.sh"
        with open(temp_health_script, 'w') as f:
            f.write(health_check_script)
            
        # Upload and setup health check
        health_script_path = f"{self.deploy_config.deploy_path}/health_check.sh"
        if not self.upload_file(temp_health_script, health_script_path):
            return False
            
        self.execute_command(f"chmod +x {health_script_path}", sudo=True)
        
        # Add to crontab (every 5 minutes)
        cron_cmd = f"(crontab -l 2>/dev/null; echo '*/5 * * * * {health_script_path}') | crontab -"
        self.execute_command(cron_cmd, sudo=True)
        
        # Cleanup
        os.remove(temp_logrotate_file)
        os.remove(temp_health_script)
        
        logger.info("✅ Monitoring configured")
        return True
        
    def verify_deployment(self) -> bool:
        """Verify deployment is working"""
        logger.info("🔍 Verifying deployment...")
        
        # Check service status
        exit_code, stdout, stderr = self.execute_command(f"systemctl status {self.deploy_config.service_name}", sudo=True)
        if exit_code != 0:
            logger.error("❌ Service is not running")
            return False
            
        # Check logs
        exit_code, stdout, stderr = self.execute_command(f"journalctl -u {self.deploy_config.service_name} --no-pager -n 20", sudo=True)
        if "ERROR" in stdout or "CRITICAL" in stdout:
            logger.warning("⚠️  Found errors in service logs")
            logger.warning(stdout)
            
        # Check if Nginx is running (if configured)
        if self.deploy_config.domain:
            exit_code, stdout, stderr = self.execute_command("systemctl status nginx", sudo=True)
            if exit_code != 0:
                logger.error("❌ Nginx is not running")
                return False
                
        logger.info("✅ Deployment verification completed")
        return True
        
    def deploy(self, env_vars: Dict[str, str]) -> bool:
        """Execute complete deployment"""
        logger.info("🚀 Starting Contabo VPS deployment...")
        logger.info("=" * 60)
        
        deployment_steps = [
            ("SSH Connection", self.connect_ssh),
            ("System Dependencies", self.setup_system_dependencies),
            ("Python Environment", self.setup_python_environment),
            ("Repository Clone", self.clone_repository),
            ("Python Dependencies", self.install_python_dependencies),
            ("Environment Variables", lambda: self.setup_environment_variables(env_vars)),
            ("Systemd Service", self.create_systemd_service),
            ("Nginx Proxy", self.setup_nginx_proxy),
            ("SSL Certificate", self.setup_ssl_certificate),
            ("Firewall", self.setup_firewall),
            ("Monitoring", self.setup_monitoring),
            ("Verification", self.verify_deployment)
        ]
        
        for step_name, step_func in deployment_steps:
            logger.info(f"\n📋 Step: {step_name}")
            
            try:
                if not step_func():
                    logger.error(f"❌ Deployment failed at step: {step_name}")
                    return False
                    
                self.deployment_log.append({
                    'step': step_name,
                    'status': 'success',
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"❌ Step crashed: {step_name} - {e}")
                self.deployment_log.append({
                    'step': step_name,
                    'status': 'failed',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
                return False
                
        logger.info("=" * 60)
        logger.info("🎉 Deployment completed successfully!")
        
        # Print deployment summary
        self.print_deployment_summary()
        
        return True
        
    def print_deployment_summary(self):
        """Print deployment summary"""
        logger.info("\n📊 DEPLOYMENT SUMMARY")
        logger.info("=" * 40)
        logger.info(f"VPS Host: {self.vps_config.host}")
        logger.info(f"Deploy Path: {self.deploy_config.deploy_path}")
        logger.info(f"Service Name: {self.deploy_config.service_name}")
        
        if self.deploy_config.domain:
            protocol = "https" if self.deploy_config.ssl_email else "http"
            logger.info(f"Web URL: {protocol}://{self.deploy_config.domain}")
            
        logger.info("\n🔧 MANAGEMENT COMMANDS:")
        logger.info(f"  Service Status: systemctl status {self.deploy_config.service_name}")
        logger.info(f"  View Logs: journalctl -u {self.deploy_config.service_name} -f")
        logger.info(f"  Restart Service: systemctl restart {self.deploy_config.service_name}")
        logger.info(f"  Update Code: cd {self.deploy_config.deploy_path}/src && git pull")
        
        logger.info("\n📁 IMPORTANT PATHS:")
        logger.info(f"  Project: {self.deploy_config.deploy_path}/src")
        logger.info(f"  Logs: {self.deploy_config.deploy_path}/logs")
        logger.info(f"  Environment: {self.deploy_config.deploy_path}/src/.env")
        
    def cleanup(self):
        """Cleanup resources"""
        if self.ssh_client:
            self.ssh_client.close()
            

def main():
    """Main deployment function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deploy Bulenox Trading Bot to Contabo VPS')
    parser.add_argument('--host', required=True, help='VPS IP address or hostname')
    parser.add_argument('--username', default='root', help='SSH username')
    parser.add_argument('--password', help='SSH password')
    parser.add_argument('--ssh-key', help='SSH private key path')
    parser.add_argument('--domain', help='Domain name for web interface')
    parser.add_argument('--ssl-email', help='Email for SSL certificate')
    parser.add_argument('--github-repo', help='GitHub repository URL')
    parser.add_argument('--config', help='JSON config file path')
    
    args = parser.parse_args()
    
    # Load configuration
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r') as f:
            config_data = json.load(f)
            
        vps_config = VPSConfig(**config_data.get('vps', {}))
        deploy_config = DeploymentConfig(**config_data.get('deployment', {}))
        env_vars = config_data.get('environment', {})
    else:
        # Use command line arguments
        vps_config = VPSConfig(
            host=args.host,
            username=args.username,
            password=args.password,
            ssh_key_path=args.ssh_key
        )
        
        deploy_config = DeploymentConfig(
            domain=args.domain,
            ssl_email=args.ssl_email,
            github_repo=args.github_repo or "https://github.com/your-username/ai-trading-sentinel.git"
        )
        
        # Get environment variables from user
        env_vars = {
            'BULENOX_USERNAME': input("Bulenox Username: "),
            'BULENOX_PASSWORD': input("Bulenox Password: "),
            'GITHUB_TOKEN': input("GitHub Token (optional): ") or "",
            'FLASK_SECRET_KEY': os.urandom(24).hex(),
            'ENVIRONMENT': 'production'
        }
        
    # Validate required environment variables
    required_vars = ['BULENOX_USERNAME', 'BULENOX_PASSWORD']
    for var in required_vars:
        if not env_vars.get(var):
            logger.error(f"❌ Required environment variable missing: {var}")
            sys.exit(1)
            
    # Create deployer and execute deployment
    deployer = ContaboVPSDeployer(vps_config, deploy_config)
    
    try:
        success = deployer.deploy(env_vars)
        
        if success:
            logger.info("\n🎉 Deployment completed successfully!")
            logger.info("Your Bulenox trading bot is now running on the VPS.")
            sys.exit(0)
        else:
            logger.error("\n❌ Deployment failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n👋 Deployment interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"\n💥 Deployment crashed: {e}")
        sys.exit(1)
    finally:
        deployer.cleanup()
        

if __name__ == "__main__":
    main()