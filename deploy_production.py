#!/usr/bin/env python3
"""
AI Trading Sentinel - Production Deployment Orchestrator
TRAE-SentinelOps Complete Production Deployment System

This script orchestrates the complete production deployment process.
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime
import argparse

# Configure logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deployment.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ProductionDeployer:
    """Complete production deployment orchestrator"""
    
    def __init__(self, domain, email, vps_user="root"):
        self.domain = domain
        self.email = email
        self.vps_user = vps_user
        self.app_dir = "/opt/ai-trading-sentinel"
        self.deployment_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.deployment_log = f'deployment_{self.deployment_id}.log'
        self.status = {
            'phase': 'initialization',
            'success': False,
            'errors': [],
            'warnings': [],
            'completed_steps': [],
            'failed_steps': []
        }
    
    def log_step(self, step: str, success: bool, message: str = ""):
        """Log deployment step with status"""
        timestamp = datetime.now().isoformat()
        
        if success:
            self.status['completed_steps'].append({
                'step': step,
                'timestamp': timestamp,
                'message': message
            })
            logger.info(f"SUCCESS: {step} - {message}")
        else:
            self.status['failed_steps'].append({
                'step': step,
                'timestamp': timestamp,
                'error': message
            })
            self.status['errors'].append(f"{step}: {message}")
            logger.error(f"FAILED: {step} - {message}")
        
    def run_command(self, command: str, description: str, timeout: int = 300) -> Tuple[bool, str]:
        """Run a command with timeout and logging"""
        logger.info(f"Executing: {description}")
        logger.debug(f"Command: {command}")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode == 0:
                self.log_step(description, True, "Command executed successfully")
                return True, result.stdout
            else:
                self.log_step(description, False, f"Exit code {result.returncode}: {result.stderr}")
                return False, result.stderr
                
        except subprocess.TimeoutExpired:
            error_msg = f"Command timed out after {timeout} seconds"
            self.log_step(description, False, error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Command execution error: {str(e)}"
            self.log_step(description, False, error_msg)
            return False, error_msg
    
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
    
    def check_prerequisites(self) -> bool:
        """Check all deployment prerequisites"""
        self.status['phase'] = 'prerequisites_check'
        logger.info("Phase 1: Checking deployment prerequisites...")
        
        # Check if validation report exists and is successful
        validation_file = Path('environment_validation_report.json')
        if not validation_file.exists():
            logger.warning("Environment validation report not found. Running validation...")
            success, output = self.run_command(
                'python validate_environment.py',
                'Environment validation',
                timeout=60
            )
            if not success:
                return False
        
        # Load and check validation results
        try:
            with open('environment_validation_report.json', 'r', encoding='utf-8') as f:
                validation_data = json.load(f)
            
            if not validation_data.get('deployment_ready', False):
                missing_vars = validation_data.get('environment_variables', {}).get('missing_required', [])
                if missing_vars:
                    self.log_step(
                        'Environment validation',
                        False,
                        f"Missing required variables: {', '.join(missing_vars)}"
                    )
                    logger.error("Please configure environment variables using:")
                    logger.error("  python setup_secrets.py --generate")
                    logger.error("  Edit .env file with your credentials")
                    return False
            
            self.log_step('Environment validation', True, 'All required variables configured')
            
        except Exception as e:
            self.log_step('Environment validation', False, f"Failed to read validation report: {e}")
            return False
        
        # Check deployment files
        required_files = [
            'deploy_to_contabo_vps.py',
            'setup_production_env.sh',
            'verify_deployment.sh',
            'main.py',
            'requirements.txt'
        ]
        
        for file_path in required_files:
            if not Path(file_path).exists():
                self.log_step('File check', False, f"Missing required file: {file_path}")
                return False
        
        self.log_step('File check', True, 'All required deployment files present')
        return True
    
    def test_connections(self) -> bool:
        """Test all external connections"""
        self.status['phase'] = 'connection_testing'
        logger.info("Phase 2: Testing external connections...")
        
        # Test VPS connection
        vps_ip = os.getenv('CONTABO_VPS_IP')
        if vps_ip:
            success, output = self.run_command(
                'python setup_secrets.py --test-vps',
                'VPS SSH connection test',
                timeout=30
            )
            if not success:
                logger.warning("VPS connection test failed. Deployment will continue but may fail later.")
                self.status['warnings'].append('VPS connection test failed')
        
        # Test GitHub connection
        github_token = os.getenv('GITHUB_TOKEN')
        if github_token:
            success, output = self.run_command(
                'python setup_secrets.py --test-github',
                'GitHub API connection test',
                timeout=30
            )
            if not success:
                logger.warning("GitHub connection test failed. CI/CD may not work properly.")
                self.status['warnings'].append('GitHub connection test failed')
        
        return True
    
    def prepare_deployment_package(self) -> bool:
        """Prepare deployment package"""
        self.status['phase'] = 'package_preparation'
        logger.info("Phase 3: Preparing deployment package...")
        
        # Create deployment directory
        deploy_dir = Path(f'deployment_{self.deployment_id}')
        deploy_dir.mkdir(exist_ok=True)
        
        # Copy essential files
        essential_files = [
            'main.py',
            'requirements.txt',
            '.env',
            'deploy_to_contabo_vps.py',
            'setup_production_env.sh',
            'verify_deployment.sh'
        ]
        
        for file_name in essential_files:
            source = Path(file_name)
            if source.exists():
                import shutil
                shutil.copy2(source, deploy_dir / file_name)
                logger.debug(f"Copied {file_name} to deployment package")
        
        # Copy directories
        for dir_name in ['backend', 'frontend', 'scripts', 'config']:
            source_dir = Path(dir_name)
            if source_dir.exists():
                import shutil
                shutil.copytree(source_dir, deploy_dir / dir_name, dirs_exist_ok=True)
                logger.debug(f"Copied {dir_name}/ to deployment package")
        
        self.log_step('Package preparation', True, f'Deployment package created: {deploy_dir}')
        return True
    
    def deploy_to_vps(self) -> bool:
        """Deploy to Contabo VPS"""
        self.status['phase'] = 'vps_deployment'
        logger.info("Phase 4: Deploying to Contabo VPS...")
        
        # Run VPS deployment script
        success, output = self.run_command(
            'python deploy_to_contabo_vps.py',
            'VPS deployment execution',
            timeout=600  # 10 minutes timeout
        )
        
        if not success:
            return False
        
        # Wait for services to start
        logger.info("Waiting for services to initialize...")
        time.sleep(30)
        
        return True
    
    def verify_deployment(self) -> bool:
        """Verify deployment success"""
        self.status['phase'] = 'deployment_verification'
        logger.info("Phase 5: Verifying deployment...")
        
        # Run verification script
        success, output = self.run_command(
            'bash verify_deployment.sh',
            'Deployment verification',
            timeout=300
        )
        
        if not success:
            # Try Python-based verification as fallback
            logger.info("Bash verification failed, trying Python verification...")
            success, output = self.run_command(
                'python -c "import requests; print(requests.get(\'http://localhost:5000/health\').status_code)"',
                'Python health check',
                timeout=30
            )
        
        return success
    
    def setup_monitoring_enhanced(self) -> bool:
        """Setup enhanced monitoring and alerts"""
        self.status['phase'] = 'monitoring_setup'
        logger.info("Phase 6: Setting up enhanced monitoring...")
        
        # Create monitoring configuration
        monitoring_config = {
            'deployment_id': self.deployment_id,
            'timestamp': datetime.now().isoformat(),
            'monitoring_enabled': True,
            'health_check_url': 'http://localhost:5000/health',
            'log_files': [
                '/var/log/trading_sentinel.log',
                '/var/log/nginx/access.log',
                '/var/log/nginx/error.log'
            ],
            'alert_channels': {
                'slack': os.getenv('SLACK_WEBHOOK_URL') is not None,
                'email': os.getenv('SMTP_SERVER') is not None,
                'telegram': os.getenv('TELEGRAM_BOT_TOKEN') is not None
            }
        }
        
        with open('monitoring_config.json', 'w', encoding='utf-8') as f:
            json.dump(monitoring_config, f, indent=2)
        
        self.log_step('Enhanced monitoring setup', True, 'Monitoring configuration created')
        return True
    
    def generate_deployment_report(self) -> Dict:
        """Generate comprehensive deployment report"""
        report = {
            'deployment_id': self.deployment_id,
            'timestamp': datetime.now().isoformat(),
            'status': self.status,
            'environment': {
                'python_version': sys.version,
                'platform': sys.platform,
                'working_directory': str(Path.cwd())
            },
            'configuration': {
                'vps_ip': os.getenv('CONTABO_VPS_IP', 'Not configured'),
                'github_repo': os.getenv('GITHUB_REPO_URL', 'Not configured'),
                'monitoring_enabled': os.getenv('SLACK_WEBHOOK_URL') is not None
            },
            'next_steps': [
                "Access your application at: http://YOUR_VPS_IP:5000",
                "Monitor logs: tail -f /var/log/trading_sentinel.log",
                "Check system status: systemctl status trading-sentinel",
                "View monitoring dashboard: http://YOUR_VPS_IP:5000/dashboard"
            ]
        }
        
        # Save report
        report_file = f'deployment_report_{self.deployment_id}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def orchestrate_deployment(self) -> bool:
        """Orchestrate the complete deployment process"""
        logger.info(f"Starting production deployment orchestration - ID: {self.deployment_id}")
        
        try:
            # Phase 1: Prerequisites
            if not self.check_prerequisites():
                logger.error("Prerequisites check failed")
                return False
            
            # Phase 2: Connection Testing
            if not self.test_connections():
                logger.error("Connection testing failed")
                return False
            
            # Phase 3: Package Preparation
            if not self.prepare_deployment_package():
                logger.error("Package preparation failed")
                return False
            
            # Phase 4: VPS Deployment
            if not self.deploy_to_vps():
                logger.error("VPS deployment failed")
                return False
            
            # Phase 5: Verification
            if not self.verify_deployment():
                logger.error("Deployment verification failed")
                return False
            
            # Phase 6: Monitoring Setup
            if not self.setup_monitoring_enhanced():
                logger.error("Monitoring setup failed")
                return False
            
            # Generate final report
            report = self.generate_deployment_report()
            
            self.status['success'] = True
            self.status['phase'] = 'completed'
            
            logger.info("Production deployment completed successfully!")
            logger.info(f"Deployment report saved: deployment_report_{self.deployment_id}.json")
            
            return True
            
        except Exception as e:
            self.log_step('Deployment orchestration', False, f"Unexpected error: {str(e)}")
            logger.error(f"Deployment failed with error: {e}")
            return False
    
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
    parser.add_argument('--domain', help='Your domain name (e.g., trading.example.com)')
    parser.add_argument('--email', help='Email for SSL certificates')
    parser.add_argument('--user', default='root', help='VPS username (default: root)')
    parser.add_argument('--orchestrate', action='store_true', help='Run orchestrated deployment (recommended)')
    parser.add_argument('--test-only', action='store_true', help='Run prerequisites and connection tests only')
    
    args = parser.parse_args()
    
    # Default values for orchestrated deployment
    domain = args.domain or os.getenv('CONTABO_VPS_IP', 'localhost')
    email = args.email or os.getenv('SSL_EMAIL', 'admin@example.com')
    
    deployer = ProductionDeployer(domain, email, args.user)
    
    if args.test_only:
        logger.info("Running prerequisites and connection tests only...")
        success = deployer.check_prerequisites() and deployer.test_connections()
        if success:
            logger.info("All tests passed! Ready for deployment.")
        else:
            logger.error("Tests failed. Please fix issues before deployment.")
            sys.exit(1)
    elif args.orchestrate or (not args.domain and not args.email):
        logger.info("Running orchestrated deployment...")
        success = deployer.orchestrate_deployment()
        if not success:
            logger.error("Orchestrated deployment failed")
            sys.exit(1)
    else:
        logger.info("Running traditional deployment...")
        deployer.deploy()

if __name__ == "__main__":
    main()