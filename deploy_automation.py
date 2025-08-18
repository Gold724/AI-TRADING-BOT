#!/usr/bin/env python3
"""
AI Trading Sentinel - Deployment Automation Script
Automated deployment, scaling, and management for cloud infrastructure
"""

import os
import sys
import json
import time
import logging
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

try:
    import paramiko
    import boto3
    import requests
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Install with: pip install paramiko boto3 requests python-dotenv")
    sys.exit(1)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deployment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ServerConfig:
    """Server configuration for deployment"""
    name: str
    host: str
    user: str
    key_path: str
    port: int = 22
    app_dir: str = "/opt/ai-trading-sentinel"
    environment: str = "production"
    
class DeploymentManager:
    """Manages deployment operations across multiple cloud providers"""
    
    def __init__(self, config_file: str = "deployment_config.json"):
        self.config_file = config_file
        self.servers = self._load_server_configs()
        self.deployment_history = []
        
    def _load_server_configs(self) -> Dict[str, ServerConfig]:
        """Load server configurations from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                    
                servers = {}
                for name, config in config_data.get('servers', {}).items():
                    servers[name] = ServerConfig(**config)
                return servers
            else:
                logger.warning(f"Config file {self.config_file} not found. Using environment variables.")
                return self._load_from_env()
        except Exception as e:
            logger.error(f"Failed to load server configs: {e}")
            return {}
    
    def _load_from_env(self) -> Dict[str, ServerConfig]:
        """Load server configurations from environment variables"""
        servers = {}
        
        # Contabo VPS
        if os.getenv('CONTABO_HOST'):
            servers['contabo'] = ServerConfig(
                name='contabo',
                host=os.getenv('CONTABO_HOST'),
                user=os.getenv('CONTABO_USER', 'trader'),
                key_path=os.getenv('CONTABO_SSH_KEY', '~/.ssh/id_rsa'),
                environment='production'
            )
        
        # DigitalOcean
        if os.getenv('DO_HOST'):
            servers['digitalocean'] = ServerConfig(
                name='digitalocean',
                host=os.getenv('DO_HOST'),
                user=os.getenv('DO_USER', 'trader'),
                key_path=os.getenv('DO_SSH_KEY', '~/.ssh/id_rsa'),
                environment='production'
            )
        
        # AWS EC2
        if os.getenv('AWS_HOST'):
            servers['aws'] = ServerConfig(
                name='aws',
                host=os.getenv('AWS_HOST'),
                user=os.getenv('AWS_USER', 'ubuntu'),
                key_path=os.getenv('AWS_SSH_KEY', '~/.ssh/aws-key.pem'),
                environment='production'
            )
        
        # Staging server
        if os.getenv('STAGING_HOST'):
            servers['staging'] = ServerConfig(
                name='staging',
                host=os.getenv('STAGING_HOST'),
                user=os.getenv('STAGING_USER', 'trader'),
                key_path=os.getenv('STAGING_SSH_KEY', '~/.ssh/id_rsa'),
                environment='staging'
            )
        
        return servers
    
    def create_ssh_connection(self, server: ServerConfig) -> paramiko.SSHClient:
        """Create SSH connection to server"""
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Expand user path
            key_path = os.path.expanduser(server.key_path)
            
            ssh.connect(
                hostname=server.host,
                username=server.user,
                key_filename=key_path,
                port=server.port,
                timeout=30
            )
            
            logger.info(f"✅ Connected to {server.name} ({server.host})")
            return ssh
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to {server.name}: {e}")
            raise
    
    def execute_command(self, ssh: paramiko.SSHClient, command: str, 
                       timeout: int = 300) -> Tuple[int, str, str]:
        """Execute command on remote server"""
        try:
            logger.info(f"Executing: {command}")
            stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
            
            exit_code = stdout.channel.recv_exit_status()
            stdout_text = stdout.read().decode('utf-8')
            stderr_text = stderr.read().decode('utf-8')
            
            if exit_code == 0:
                logger.info(f"✅ Command successful")
                if stdout_text.strip():
                    logger.debug(f"Output: {stdout_text.strip()}")
            else:
                logger.error(f"❌ Command failed (exit code: {exit_code})")
                if stderr_text.strip():
                    logger.error(f"Error: {stderr_text.strip()}")
            
            return exit_code, stdout_text, stderr_text
            
        except Exception as e:
            logger.error(f"❌ Command execution failed: {e}")
            return 1, "", str(e)
    
    def check_server_health(self, server_name: str) -> bool:
        """Check if server is healthy and bot is running"""
        if server_name not in self.servers:
            logger.error(f"Server {server_name} not found in configuration")
            return False
        
        server = self.servers[server_name]
        
        try:
            ssh = self.create_ssh_connection(server)
            
            # Check system health
            commands = [
                "systemctl is-active ai-trading-sentinel",
                "curl -f http://localhost/health",
                "df -h | grep -E '(/$|/opt)'",
                "free -m",
                "uptime"
            ]
            
            health_status = True
            
            for cmd in commands:
                exit_code, stdout, stderr = self.execute_command(ssh, cmd)
                if exit_code != 0 and "systemctl" in cmd:
                    logger.warning(f"Service check failed on {server_name}")
                    health_status = False
                elif exit_code != 0 and "curl" in cmd:
                    logger.warning(f"Health endpoint check failed on {server_name}")
                    health_status = False
            
            ssh.close()
            
            if health_status:
                logger.info(f"✅ {server_name} is healthy")
            else:
                logger.warning(f"⚠️ {server_name} has health issues")
            
            return health_status
            
        except Exception as e:
            logger.error(f"❌ Health check failed for {server_name}: {e}")
            return False
    
    def deploy_to_server(self, server_name: str, branch: str = "main", 
                        force: bool = False) -> bool:
        """Deploy application to specific server"""
        if server_name not in self.servers:
            logger.error(f"Server {server_name} not found in configuration")
            return False
        
        server = self.servers[server_name]
        deployment_id = f"{server_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        logger.info(f"🚀 Starting deployment {deployment_id} to {server_name}")
        
        try:
            ssh = self.create_ssh_connection(server)
            
            # Pre-deployment checks
            if not force:
                logger.info("Running pre-deployment checks...")
                exit_code, _, _ = self.execute_command(ssh, "systemctl is-active ai-trading-sentinel")
                if exit_code != 0:
                    logger.warning("Service is not running. Proceeding with deployment.")
            
            # Create backup
            logger.info("Creating backup...")
            backup_cmd = f"cd {server.app_dir} && tar -czf /tmp/backup-{deployment_id}.tar.gz ."
            self.execute_command(ssh, backup_cmd)
            
            # Update code
            logger.info(f"Updating code from {branch} branch...")
            update_commands = [
                f"cd {server.app_dir}",
                "git fetch origin",
                f"git checkout {branch}",
                f"git pull origin {branch}",
                "source venv/bin/activate && pip install -r requirements.txt"
            ]
            
            for cmd in update_commands:
                exit_code, stdout, stderr = self.execute_command(ssh, cmd)
                if exit_code != 0:
                    logger.error(f"Update failed at step: {cmd}")
                    # Restore backup
                    restore_cmd = f"cd {server.app_dir} && tar -xzf /tmp/backup-{deployment_id}.tar.gz"
                    self.execute_command(ssh, restore_cmd)
                    ssh.close()
                    return False
            
            # Update configuration
            logger.info("Updating configuration...")
            config_update_cmd = f"cd {server.app_dir} && python deploy_automation.py --update-config --environment={server.environment}"
            self.execute_command(ssh, config_update_cmd)
            
            # Restart services
            logger.info("Restarting services...")
            restart_commands = [
                "systemctl daemon-reload",
                "systemctl restart ai-trading-sentinel",
                "systemctl restart nginx",
                "sleep 10"  # Wait for services to start
            ]
            
            for cmd in restart_commands:
                exit_code, stdout, stderr = self.execute_command(ssh, cmd)
                if exit_code != 0 and "systemctl" in cmd:
                    logger.error(f"Service restart failed: {cmd}")
                    ssh.close()
                    return False
            
            # Post-deployment verification
            logger.info("Running post-deployment verification...")
            verification_commands = [
                "systemctl is-active ai-trading-sentinel",
                "curl -f http://localhost/health",
                f"cd {server.app_dir} && python health_check.py --quick"
            ]
            
            verification_passed = True
            for cmd in verification_commands:
                exit_code, stdout, stderr = self.execute_command(ssh, cmd)
                if exit_code != 0:
                    logger.error(f"Verification failed: {cmd}")
                    verification_passed = False
            
            ssh.close()
            
            if verification_passed:
                logger.info(f"✅ Deployment {deployment_id} completed successfully")
                self.deployment_history.append({
                    'id': deployment_id,
                    'server': server_name,
                    'branch': branch,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'success'
                })
                return True
            else:
                logger.error(f"❌ Deployment {deployment_id} failed verification")
                return False
                
        except Exception as e:
            logger.error(f"❌ Deployment {deployment_id} failed: {e}")
            return False
    
    def rollback_deployment(self, server_name: str, backup_id: str = None) -> bool:
        """Rollback to previous deployment"""
        if server_name not in self.servers:
            logger.error(f"Server {server_name} not found in configuration")
            return False
        
        server = self.servers[server_name]
        
        try:
            ssh = self.create_ssh_connection(server)
            
            # Find latest backup if not specified
            if not backup_id:
                exit_code, stdout, stderr = self.execute_command(
                    ssh, "ls -t /tmp/backup-*.tar.gz | head -1"
                )
                if exit_code == 0 and stdout.strip():
                    backup_file = stdout.strip()
                else:
                    logger.error("No backup found for rollback")
                    ssh.close()
                    return False
            else:
                backup_file = f"/tmp/backup-{backup_id}.tar.gz"
            
            logger.info(f"Rolling back {server_name} using {backup_file}")
            
            # Stop services
            self.execute_command(ssh, "systemctl stop ai-trading-sentinel")
            
            # Restore backup
            restore_commands = [
                f"cd {server.app_dir}",
                f"tar -xzf {backup_file}"
            ]
            
            for cmd in restore_commands:
                exit_code, stdout, stderr = self.execute_command(ssh, cmd)
                if exit_code != 0:
                    logger.error(f"Rollback failed at: {cmd}")
                    ssh.close()
                    return False
            
            # Restart services
            restart_commands = [
                "systemctl start ai-trading-sentinel",
                "systemctl restart nginx",
                "sleep 10"
            ]
            
            for cmd in restart_commands:
                self.execute_command(ssh, cmd)
            
            # Verify rollback
            exit_code, stdout, stderr = self.execute_command(
                ssh, "systemctl is-active ai-trading-sentinel"
            )
            
            ssh.close()
            
            if exit_code == 0:
                logger.info(f"✅ Rollback completed successfully for {server_name}")
                return True
            else:
                logger.error(f"❌ Rollback verification failed for {server_name}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Rollback failed for {server_name}: {e}")
            return False
    
    def scale_deployment(self, target_servers: List[str], branch: str = "main") -> Dict[str, bool]:
        """Deploy to multiple servers in parallel"""
        logger.info(f"🚀 Starting scaled deployment to {len(target_servers)} servers")
        
        results = {}
        
        # Sequential deployment for safety
        for server_name in target_servers:
            logger.info(f"Deploying to {server_name}...")
            results[server_name] = self.deploy_to_server(server_name, branch)
            
            if not results[server_name]:
                logger.error(f"Deployment to {server_name} failed. Stopping scaled deployment.")
                break
            
            # Wait between deployments
            time.sleep(5)
        
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        
        logger.info(f"📊 Scaled deployment completed: {successful}/{total} successful")
        
        return results
    
    def monitor_deployments(self, interval: int = 300) -> None:
        """Monitor all deployed servers continuously"""
        logger.info(f"🔍 Starting deployment monitoring (interval: {interval}s)")
        
        while True:
            try:
                for server_name in self.servers:
                    health_status = self.check_server_health(server_name)
                    
                    if not health_status:
                        logger.warning(f"⚠️ Health issue detected on {server_name}")
                        # Could trigger alerts here
                
                logger.info(f"💤 Sleeping for {interval} seconds...")
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Monitoring error: {e}")
                time.sleep(60)  # Wait before retrying
    
    def generate_deployment_report(self) -> str:
        """Generate deployment status report"""
        report = ["\n📋 AI Trading Sentinel - Deployment Report"]
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Server status
        report.append("🖥️ Server Status:")
        for server_name, server in self.servers.items():
            health = "✅ Healthy" if self.check_server_health(server_name) else "❌ Issues"
            report.append(f"  {server_name}: {health} ({server.host})")
        
        report.append("")
        
        # Recent deployments
        report.append("🚀 Recent Deployments:")
        recent_deployments = sorted(
            self.deployment_history[-10:], 
            key=lambda x: x['timestamp'], 
            reverse=True
        )
        
        for deployment in recent_deployments:
            status_icon = "✅" if deployment['status'] == 'success' else "❌"
            report.append(
                f"  {status_icon} {deployment['id']} - {deployment['server']} "
                f"({deployment['branch']}) - {deployment['timestamp']}"
            )
        
        return "\n".join(report)

def main():
    """Main deployment automation function"""
    parser = argparse.ArgumentParser(description="AI Trading Sentinel Deployment Automation")
    parser.add_argument('--config', default='deployment_config.json', help='Configuration file')
    parser.add_argument('--server', help='Target server name')
    parser.add_argument('--branch', default='main', help='Git branch to deploy')
    parser.add_argument('--force', action='store_true', help='Force deployment')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Deploy command
    deploy_parser = subparsers.add_parser('deploy', help='Deploy to server(s)')
    deploy_parser.add_argument('--all', action='store_true', help='Deploy to all servers')
    
    # Health check command
    health_parser = subparsers.add_parser('health', help='Check server health')
    health_parser.add_argument('--all', action='store_true', help='Check all servers')
    
    # Rollback command
    rollback_parser = subparsers.add_parser('rollback', help='Rollback deployment')
    rollback_parser.add_argument('--backup-id', help='Specific backup ID to restore')
    
    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Monitor deployments')
    monitor_parser.add_argument('--interval', type=int, default=300, help='Check interval in seconds')
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate deployment report')
    
    # Scale command
    scale_parser = subparsers.add_parser('scale', help='Scale deployment to multiple servers')
    scale_parser.add_argument('servers', nargs='+', help='List of server names')
    
    args = parser.parse_args()
    
    # Initialize deployment manager
    dm = DeploymentManager(args.config)
    
    if not dm.servers:
        logger.error("No servers configured. Please check your configuration.")
        sys.exit(1)
    
    # Execute commands
    if args.command == 'deploy':
        if args.all:
            results = dm.scale_deployment(list(dm.servers.keys()), args.branch)
            success_count = sum(1 for success in results.values() if success)
            logger.info(f"Deployment completed: {success_count}/{len(results)} successful")
        elif args.server:
            success = dm.deploy_to_server(args.server, args.branch, args.force)
            sys.exit(0 if success else 1)
        else:
            logger.error("Please specify --server or --all")
            sys.exit(1)
    
    elif args.command == 'health':
        if args.all:
            for server_name in dm.servers:
                dm.check_server_health(server_name)
        elif args.server:
            healthy = dm.check_server_health(args.server)
            sys.exit(0 if healthy else 1)
        else:
            logger.error("Please specify --server or --all")
            sys.exit(1)
    
    elif args.command == 'rollback':
        if not args.server:
            logger.error("Please specify --server for rollback")
            sys.exit(1)
        success = dm.rollback_deployment(args.server, args.backup_id)
        sys.exit(0 if success else 1)
    
    elif args.command == 'monitor':
        dm.monitor_deployments(args.interval)
    
    elif args.command == 'report':
        print(dm.generate_deployment_report())
    
    elif args.command == 'scale':
        results = dm.scale_deployment(args.servers, args.branch)
        success_count = sum(1 for success in results.values() if success)
        logger.info(f"Scaled deployment completed: {success_count}/{len(results)} successful")
        sys.exit(0 if success_count == len(results) else 1)
    
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()