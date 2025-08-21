#!/usr/bin/env python3
"""
AI Trading Sentinel - Production Deployment Automation
Comprehensive deployment orchestration for Contabo VPS
"""

import os
import sys
import json
import time
import shutil
import subprocess
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import paramiko
import yaml
from dotenv import load_dotenv

class ProductionDeployer:
    """Automated production deployment orchestrator"""
    
    def __init__(self, config_file: str = None):
        self.project_root = Path(__file__).parent.parent
        self.config_file = config_file or self.project_root / "contabo_deployment_config.json"
        
        # Load environment variables
        load_dotenv(self.project_root / ".env")
        
        # Load deployment configuration
        self.config = self._load_config()
        
        # VPS connection details
        self.vps_host = os.getenv('CONTABO_VPS_IP')
        self.vps_user = os.getenv('CONTABO_USERNAME', 'root')
        self.vps_password = os.getenv('CONTABO_PASSWORD')
        self.ssh_key_path = os.getenv('CONTABO_SSH_KEY_PATH')
        
        # Deployment paths
        self.remote_app_dir = "/opt/ai-trading-sentinel"
        self.remote_backup_dir = "/opt/backups"
        self.remote_logs_dir = "/var/log/ai-trading-sentinel"
        
        # Services
        self.services = ['trading-api', 'trading-bot', 'trading-monitor', 'nginx']
        
        # SSH client
        self.ssh_client = None
        
        print(f"🚀 Production Deployer initialized")
        print(f"📁 Project root: {self.project_root}")
        print(f"🖥️  Target VPS: {self.vps_host}")
    
    def _load_config(self) -> Dict:
        """Load deployment configuration"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️  Configuration file not found: {self.config_file}")
            return self._get_default_config()
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing configuration: {e}")
            sys.exit(1)
    
    def _get_default_config(self) -> Dict:
        """Get default deployment configuration"""
        return {
            "deployment": {
                "app_directory": "/opt/ai-trading-sentinel",
                "backup_directory": "/opt/backups",
                "logs_directory": "/var/log/ai-trading-sentinel",
                "user": "trading",
                "group": "trading"
            },
            "services": {
                "api": {
                    "name": "trading-api",
                    "port": 5000,
                    "health_endpoint": "/api/health"
                },
                "bot": {
                    "name": "trading-bot",
                    "port": 5001,
                    "health_endpoint": "/status"
                },
                "monitor": {
                    "name": "trading-monitor",
                    "port": 5002,
                    "health_endpoint": "/health"
                }
            },
            "monitoring": {
                "prometheus_port": 9090,
                "grafana_port": 3001,
                "alertmanager_port": 9093
            }
        }
    
    def connect_ssh(self) -> bool:
        """Establish SSH connection to VPS"""
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if self.ssh_key_path and os.path.exists(self.ssh_key_path):
                print(f"🔑 Connecting with SSH key: {self.ssh_key_path}")
                self.ssh_client.connect(
                    hostname=self.vps_host,
                    username=self.vps_user,
                    key_filename=self.ssh_key_path,
                    timeout=30
                )
            elif self.vps_password:
                print(f"🔐 Connecting with password authentication")
                self.ssh_client.connect(
                    hostname=self.vps_host,
                    username=self.vps_user,
                    password=self.vps_password,
                    timeout=30
                )
            else:
                print("❌ No SSH credentials provided")
                return False
            
            print(f"✅ SSH connection established to {self.vps_host}")
            return True
            
        except Exception as e:
            print(f"❌ SSH connection failed: {e}")
            return False
    
    def execute_remote_command(self, command: str, sudo: bool = False) -> Tuple[int, str, str]:
        """Execute command on remote VPS"""
        if not self.ssh_client:
            raise Exception("SSH connection not established")
        
        if sudo:
            command = f"sudo {command}"
        
        print(f"🔧 Executing: {command}")
        
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(command, timeout=300)
            
            exit_code = stdout.channel.recv_exit_status()
            stdout_text = stdout.read().decode('utf-8')
            stderr_text = stderr.read().decode('utf-8')
            
            if exit_code == 0:
                print(f"✅ Command completed successfully")
                if stdout_text.strip():
                    print(f"📤 Output: {stdout_text.strip()[:200]}...")
            else:
                print(f"❌ Command failed with exit code {exit_code}")
                if stderr_text.strip():
                    print(f"📤 Error: {stderr_text.strip()[:200]}...")
            
            return exit_code, stdout_text, stderr_text
            
        except Exception as e:
            print(f"❌ Command execution failed: {e}")
            return 1, "", str(e)
    
    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload file to VPS"""
        try:
            sftp = self.ssh_client.open_sftp()
            
            # Create remote directory if it doesn't exist
            remote_dir = os.path.dirname(remote_path)
            try:
                sftp.stat(remote_dir)
            except FileNotFoundError:
                self.execute_remote_command(f"mkdir -p {remote_dir}", sudo=True)
            
            print(f"📤 Uploading {local_path} -> {remote_path}")
            sftp.put(local_path, remote_path)
            sftp.close()
            
            print(f"✅ File uploaded successfully")
            return True
            
        except Exception as e:
            print(f"❌ File upload failed: {e}")
            return False
    
    def create_deployment_package(self) -> str:
        """Create deployment package"""
        print("\n📦 Creating deployment package...")
        
        package_dir = self.project_root / "deployment-package"
        package_file = self.project_root / "ai-trading-sentinel-deployment.tar.gz"
        
        # Clean up previous package
        if package_dir.exists():
            shutil.rmtree(package_dir)
        if package_file.exists():
            package_file.unlink()
        
        # Create package directory
        package_dir.mkdir()
        
        # Copy application files
        files_to_copy = [
            "*.py",
            "requirements.txt",
            ".env.production.template",
            "src/",
            "templates/",
            "static/",
            "monitoring/",
            "scripts/"
        ]
        
        for pattern in files_to_copy:
            try:
                if pattern.endswith("/"):
                    # Directory
                    src_dir = self.project_root / pattern.rstrip("/")
                    if src_dir.exists():
                        shutil.copytree(src_dir, package_dir / pattern.rstrip("/"))
                        print(f"✅ Copied directory: {pattern}")
                else:
                    # Files
                    for file_path in self.project_root.glob(pattern):
                        if file_path.is_file():
                            shutil.copy2(file_path, package_dir)
                            print(f"✅ Copied file: {file_path.name}")
            except Exception as e:
                print(f"⚠️  Could not copy {pattern}: {e}")
        
        # Copy frontend build if exists
        frontend_dist = self.project_root / "frontend" / "dist"
        if frontend_dist.exists():
            shutil.copytree(frontend_dist, package_dir / "frontend")
            print(f"✅ Copied frontend build")
        
        # Create version info
        version_info = {
            "version": self._get_git_commit_hash(),
            "branch": self._get_git_branch(),
            "build_date": datetime.utcnow().isoformat() + "Z",
            "build_host": os.uname().nodename if hasattr(os, 'uname') else "unknown"
        }
        
        with open(package_dir / "version.json", 'w') as f:
            json.dump(version_info, f, indent=2)
        
        # Create deployment archive
        print(f"📦 Creating deployment archive...")
        shutil.make_archive(
            str(package_file.with_suffix('')),
            'gztar',
            package_dir
        )
        
        # Cleanup package directory
        shutil.rmtree(package_dir)
        
        print(f"✅ Deployment package created: {package_file}")
        print(f"📊 Package size: {package_file.stat().st_size / 1024 / 1024:.2f} MB")
        
        return str(package_file)
    
    def _get_git_commit_hash(self) -> str:
        """Get current git commit hash"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except:
            return "unknown"
    
    def _get_git_branch(self) -> str:
        """Get current git branch"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except:
            return "unknown"
    
    def backup_current_deployment(self) -> bool:
        """Backup current deployment"""
        print("\n💾 Creating backup of current deployment...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{self.remote_backup_dir}/ai-trading-sentinel_{timestamp}"
        
        # Create backup directory
        exit_code, _, _ = self.execute_remote_command(f"mkdir -p {self.remote_backup_dir}", sudo=True)
        if exit_code != 0:
            print(f"❌ Failed to create backup directory")
            return False
        
        # Check if current deployment exists
        exit_code, _, _ = self.execute_remote_command(f"test -d {self.remote_app_dir}")
        if exit_code != 0:
            print(f"ℹ️  No existing deployment to backup")
            return True
        
        # Create backup
        exit_code, _, _ = self.execute_remote_command(
            f"cp -r {self.remote_app_dir} {backup_path}",
            sudo=True
        )
        
        if exit_code == 0:
            print(f"✅ Backup created: {backup_path}")
            
            # Keep only last 5 backups
            self.execute_remote_command(
                f"ls -t {self.remote_backup_dir}/ai-trading-sentinel_* | tail -n +6 | xargs -r rm -rf",
                sudo=True
            )
            
            return True
        else:
            print(f"❌ Backup failed")
            return False
    
    def stop_services(self) -> bool:
        """Stop all services"""
        print("\n🛑 Stopping services...")
        
        success = True
        for service in self.services:
            exit_code, _, _ = self.execute_remote_command(f"systemctl stop {service}", sudo=True)
            if exit_code == 0:
                print(f"✅ Stopped {service}")
            else:
                print(f"⚠️  Could not stop {service} (may not be running)")
        
        # Wait for services to stop
        time.sleep(5)
        
        return success
    
    def deploy_application(self, package_path: str) -> bool:
        """Deploy application to VPS"""
        print("\n🚀 Deploying application...")
        
        remote_package_path = f"/tmp/ai-trading-sentinel-deployment.tar.gz"
        
        # Upload deployment package
        if not self.upload_file(package_path, remote_package_path):
            return False
        
        # Create application directory
        exit_code, _, _ = self.execute_remote_command(f"mkdir -p {self.remote_app_dir}", sudo=True)
        if exit_code != 0:
            print(f"❌ Failed to create application directory")
            return False
        
        # Extract deployment package
        exit_code, _, _ = self.execute_remote_command(
            f"cd {self.remote_app_dir} && tar -xzf {remote_package_path}",
            sudo=True
        )
        
        if exit_code != 0:
            print(f"❌ Failed to extract deployment package")
            return False
        
        # Set up Python virtual environment
        venv_path = f"{self.remote_app_dir}/venv"
        exit_code, _, _ = self.execute_remote_command(
            f"cd {self.remote_app_dir} && python3 -m venv {venv_path}",
            sudo=True
        )
        
        if exit_code != 0:
            print(f"❌ Failed to create virtual environment")
            return False
        
        # Install Python dependencies
        exit_code, _, _ = self.execute_remote_command(
            f"cd {self.remote_app_dir} && {venv_path}/bin/pip install --upgrade pip",
            sudo=True
        )
        
        exit_code, _, _ = self.execute_remote_command(
            f"cd {self.remote_app_dir} && {venv_path}/bin/pip install -r requirements.txt",
            sudo=True
        )
        
        if exit_code != 0:
            print(f"❌ Failed to install Python dependencies")
            return False
        
        # Set up environment file
        env_file = f"{self.remote_app_dir}/.env"
        template_file = f"{self.remote_app_dir}/.env.production.template"
        
        # Check if .env exists, if not copy from template
        exit_code, _, _ = self.execute_remote_command(f"test -f {env_file}")
        if exit_code != 0:
            self.execute_remote_command(f"cp {template_file} {env_file}", sudo=True)
            print(f"ℹ️  Created .env from template - please update with production values")
        
        # Set permissions
        user = self.config['deployment']['user']
        group = self.config['deployment']['group']
        
        self.execute_remote_command(f"chown -R {user}:{group} {self.remote_app_dir}", sudo=True)
        self.execute_remote_command(f"chmod +x {self.remote_app_dir}/scripts/*.py", sudo=True)
        self.execute_remote_command(f"chmod +x {self.remote_app_dir}/scripts/*.sh", sudo=True)
        
        # Cleanup
        self.execute_remote_command(f"rm -f {remote_package_path}", sudo=True)
        
        print(f"✅ Application deployed successfully")
        return True
    
    def setup_systemd_services(self) -> bool:
        """Setup systemd services"""
        print("\n⚙️  Setting up systemd services...")
        
        # Copy service files
        service_files = [
            "trading-api.service",
            "trading-bot.service",
            "trading-monitor.service"
        ]
        
        for service_file in service_files:
            local_path = self.project_root / "scripts" / service_file
            remote_path = f"/etc/systemd/system/{service_file}"
            
            if local_path.exists():
                if self.upload_file(str(local_path), f"/tmp/{service_file}"):
                    self.execute_remote_command(f"mv /tmp/{service_file} {remote_path}", sudo=True)
                    print(f"✅ Installed {service_file}")
            else:
                print(f"⚠️  Service file not found: {service_file}")
        
        # Reload systemd
        self.execute_remote_command("systemctl daemon-reload", sudo=True)
        
        return True
    
    def start_services(self) -> bool:
        """Start all services"""
        print("\n🚀 Starting services...")
        
        success = True
        for service in self.services:
            # Enable service
            self.execute_remote_command(f"systemctl enable {service}", sudo=True)
            
            # Start service
            exit_code, _, _ = self.execute_remote_command(f"systemctl start {service}", sudo=True)
            
            if exit_code == 0:
                print(f"✅ Started {service}")
            else:
                print(f"❌ Failed to start {service}")
                success = False
        
        return success
    
    def verify_deployment(self) -> bool:
        """Verify deployment health"""
        print("\n🔍 Verifying deployment...")
        
        # Wait for services to start
        print(f"⏳ Waiting for services to start...")
        time.sleep(30)
        
        # Check service status
        all_healthy = True
        for service in self.services:
            exit_code, stdout, _ = self.execute_remote_command(f"systemctl is-active {service}")
            
            if exit_code == 0 and "active" in stdout:
                print(f"✅ {service} is active")
            else:
                print(f"❌ {service} is not active")
                all_healthy = False
        
        # Check API endpoints
        if self.vps_host:
            api_endpoints = [
                f"http://{self.vps_host}/api/health",
                f"http://{self.vps_host}/"
            ]
            
            for endpoint in api_endpoints:
                try:
                    response = requests.get(endpoint, timeout=10)
                    if response.status_code == 200:
                        print(f"✅ {endpoint} is responding")
                    else:
                        print(f"⚠️  {endpoint} returned status {response.status_code}")
                        all_healthy = False
                except Exception as e:
                    print(f"❌ {endpoint} is not accessible: {e}")
                    all_healthy = False
        
        return all_healthy
    
    def setup_monitoring(self) -> bool:
        """Setup monitoring infrastructure"""
        print("\n📊 Setting up monitoring...")
        
        # Run monitoring setup script
        monitoring_script = f"{self.remote_app_dir}/scripts/setup_monitoring.py"
        
        exit_code, _, _ = self.execute_remote_command(
            f"cd {self.remote_app_dir} && python3 {monitoring_script}",
            sudo=True
        )
        
        if exit_code == 0:
            print(f"✅ Monitoring setup completed")
            return True
        else:
            print(f"⚠️  Monitoring setup had issues - check logs")
            return False
    
    def send_deployment_notification(self, success: bool, deployment_info: Dict):
        """Send deployment notification"""
        webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        if not webhook_url:
            print("ℹ️  No Slack webhook configured")
            return
        
        status = "✅ SUCCESS" if success else "❌ FAILED"
        color = "good" if success else "danger"
        
        payload = {
            "attachments": [{
                "color": color,
                "title": "AI Trading Sentinel Deployment",
                "text": f"{status} - Production deployment completed",
                "fields": [
                    {"title": "Environment", "value": "Production", "short": True},
                    {"title": "Version", "value": deployment_info.get('version', 'unknown'), "short": True},
                    {"title": "Branch", "value": deployment_info.get('branch', 'unknown'), "short": True},
                    {"title": "Host", "value": self.vps_host, "short": True}
                ]
            }]
        }
        
        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            if response.status_code == 200:
                print(f"✅ Deployment notification sent")
            else:
                print(f"⚠️  Failed to send notification: {response.status_code}")
        except Exception as e:
            print(f"❌ Notification failed: {e}")
    
    def cleanup(self):
        """Cleanup resources"""
        if self.ssh_client:
            self.ssh_client.close()
            print(f"🔌 SSH connection closed")
    
    def deploy(self) -> bool:
        """Execute full deployment process"""
        print("\n" + "="*60)
        print("🚀 AI TRADING SENTINEL - PRODUCTION DEPLOYMENT")
        print("="*60)
        
        deployment_info = {
            "start_time": datetime.utcnow().isoformat() + "Z",
            "version": self._get_git_commit_hash(),
            "branch": self._get_git_branch()
        }
        
        try:
            # Pre-deployment checks
            if not self.vps_host:
                print("❌ VPS host not configured")
                return False
            
            # Connect to VPS
            if not self.connect_ssh():
                return False
            
            # Create deployment package
            package_path = self.create_deployment_package()
            
            # Backup current deployment
            if not self.backup_current_deployment():
                print("⚠️  Backup failed - continuing anyway")
            
            # Stop services
            self.stop_services()
            
            # Deploy application
            if not self.deploy_application(package_path):
                print("❌ Application deployment failed")
                return False
            
            # Setup systemd services
            self.setup_systemd_services()
            
            # Start services
            if not self.start_services():
                print("❌ Service startup failed")
                return False
            
            # Setup monitoring
            self.setup_monitoring()
            
            # Verify deployment
            if not self.verify_deployment():
                print("⚠️  Deployment verification had issues")
            
            deployment_info["end_time"] = datetime.utcnow().isoformat() + "Z"
            deployment_info["success"] = True
            
            # Send notification
            self.send_deployment_notification(True, deployment_info)
            
            print("\n🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!")
            print(f"🌐 Application URL: http://{self.vps_host}")
            print(f"📊 Monitoring: http://{self.vps_host}:3001 (Grafana)")
            
            return True
            
        except Exception as e:
            print(f"\n❌ DEPLOYMENT FAILED: {e}")
            deployment_info["end_time"] = datetime.utcnow().isoformat() + "Z"
            deployment_info["success"] = False
            deployment_info["error"] = str(e)
            
            self.send_deployment_notification(False, deployment_info)
            return False
            
        finally:
            self.cleanup()

def main():
    """Main deployment function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Trading Sentinel Production Deployment')
    parser.add_argument('--config', help='Deployment configuration file')
    parser.add_argument('--dry-run', action='store_true', help='Perform dry run without actual deployment')
    parser.add_argument('--skip-backup', action='store_true', help='Skip backup creation')
    parser.add_argument('--skip-monitoring', action='store_true', help='Skip monitoring setup')
    
    args = parser.parse_args()
    
    # Initialize deployer
    deployer = ProductionDeployer(args.config)
    
    if args.dry_run:
        print("🧪 DRY RUN MODE - No actual changes will be made")
        # Perform validation checks only
        success = deployer.connect_ssh()
        deployer.cleanup()
        sys.exit(0 if success else 1)
    
    # Execute deployment
    success = deployer.deploy()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()