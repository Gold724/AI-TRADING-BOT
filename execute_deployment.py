#!/usr/bin/env python3
"""
Bulenox Trading Bot - Deployment Execution Script
TRAE-SentinelOps v2.0.0 - Automated VPS Deployment Orchestrator

This script orchestrates the complete deployment of the Bulenox trading bot
to a Contabo VPS, including setup, configuration, and validation.
"""

import os
import sys
import json
import time
import subprocess
import paramiko
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import getpass
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('deployment_execution.log')
    ]
)
logger = logging.getLogger(__name__)

class ContaboDeploymentExecutor:
    """Automated deployment executor for Contabo VPS."""
    
    def __init__(self, config_file: str = 'contabo_deployment_config.json'):
        self.config_file = config_file
        self.config = self.load_config()
        self.ssh_client = None
        self.deployment_log = []
        
        # Deployment tracking
        self.start_time = datetime.now()
        self.current_step = 0
        self.total_steps = 12
        
    def load_config(self) -> Dict:
        """Load deployment configuration."""
        try:
            if Path(self.config_file).exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                logger.info(f"✅ Configuration loaded from {self.config_file}")
                return config
            else:
                logger.warning(f"⚠️ Config file {self.config_file} not found, using defaults")
                return self.get_default_config()
        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """Get default deployment configuration."""
        return {
            "deployment_info": {
                "project_name": "bulenox-trading-bot",
                "version": "2.0.0",
                "environment": "production"
            },
            "vps_connection": {
                "host": "",
                "port": 22,
                "username": "root",
                "key_file": ""
            },
            "github_repository": {
                "url": "",
                "branch": "main"
            },
            "environment_variables": {
                "BULENOX_USERNAME": "",
                "BULENOX_PASSWORD": "",
                "FLASK_SECRET_KEY": "",
                "ALERT_EMAIL": "",
                "SLACK_WEBHOOK_URL": ""
            }
        }
    
    def log_step(self, message: str, step_type: str = "info"):
        """Log deployment step with timestamp."""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "step": self.current_step,
            "message": message,
            "type": step_type
        }
        self.deployment_log.append(log_entry)
        
        if step_type == "error":
            logger.error(f"❌ Step {self.current_step}/{self.total_steps}: {message}")
        elif step_type == "warning":
            logger.warning(f"⚠️ Step {self.current_step}/{self.total_steps}: {message}")
        else:
            logger.info(f"✅ Step {self.current_step}/{self.total_steps}: {message}")
    
    def connect_ssh(self) -> bool:
        """Establish SSH connection to VPS."""
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            vps_config = self.config['vps_connection']
            
            # Connect using SSH key or password
            if vps_config.get('key_file') and Path(vps_config['key_file']).exists():
                self.ssh_client.connect(
                    hostname=vps_config['host'],
                    port=vps_config['port'],
                    username=vps_config['username'],
                    key_filename=vps_config['key_file'],
                    timeout=30
                )
            else:
                password = getpass.getpass(f"Enter password for {vps_config['username']}@{vps_config['host']}: ")
                self.ssh_client.connect(
                    hostname=vps_config['host'],
                    port=vps_config['port'],
                    username=vps_config['username'],
                    password=password,
                    timeout=30
                )
            
            self.log_step(f"Connected to VPS {vps_config['host']}")
            return True
            
        except Exception as e:
            self.log_step(f"Failed to connect to VPS: {e}", "error")
            return False
    
    def execute_remote_command(self, command: str, timeout: int = 300) -> Tuple[int, str, str]:
        """Execute command on remote VPS."""
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(command, timeout=timeout)
            
            # Wait for command to complete
            exit_status = stdout.channel.recv_exit_status()
            
            stdout_data = stdout.read().decode('utf-8')
            stderr_data = stderr.read().decode('utf-8')
            
            return exit_status, stdout_data, stderr_data
            
        except Exception as e:
            return -1, "", str(e)
    
    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload file to VPS."""
        try:
            sftp = self.ssh_client.open_sftp()
            sftp.put(local_path, remote_path)
            sftp.close()
            self.log_step(f"Uploaded {local_path} to {remote_path}")
            return True
        except Exception as e:
            self.log_step(f"Failed to upload {local_path}: {e}", "error")
            return False
    
    def prepare_environment_variables(self) -> str:
        """Prepare environment variables for deployment."""
        env_vars = []
        
        # Add GitHub repository
        if self.config['github_repository']['url']:
            env_vars.append(f"export GITHUB_REPO='{self.config['github_repository']['url']}'")
        
        # Add environment variables
        for key, value in self.config['environment_variables'].items():
            if value:
                env_vars.append(f"export {key}='{value}'")
        
        return ' && '.join(env_vars)
    
    def step_1_validate_prerequisites(self) -> bool:
        """Step 1: Validate deployment prerequisites."""
        self.current_step = 1
        self.log_step("Validating deployment prerequisites")
        
        # Check required configuration
        required_fields = [
            ('vps_connection', 'host'),
            ('github_repository', 'url'),
            ('environment_variables', 'BULENOX_USERNAME'),
            ('environment_variables', 'BULENOX_PASSWORD')
        ]
        
        missing_fields = []
        for section, field in required_fields:
            if not self.config.get(section, {}).get(field):
                missing_fields.append(f"{section}.{field}")
        
        if missing_fields:
            self.log_step(f"Missing required configuration: {missing_fields}", "error")
            return False
        
        # Check local files
        required_files = [
            'setup_contabo_vps.sh',
            'validate_deployment.py',
            'bulenox_ai_playwright_contracts.py'
        ]
        
        missing_files = []
        for file in required_files:
            if not Path(file).exists():
                missing_files.append(file)
        
        if missing_files:
            self.log_step(f"Missing required files: {missing_files}", "error")
            return False
        
        self.log_step("Prerequisites validation completed")
        return True
    
    def step_2_connect_vps(self) -> bool:
        """Step 2: Connect to VPS."""
        self.current_step = 2
        self.log_step("Connecting to VPS")
        
        if not self.connect_ssh():
            return False
        
        # Test connection
        exit_code, stdout, stderr = self.execute_remote_command('whoami && uname -a')
        if exit_code == 0:
            self.log_step(f"VPS connection verified: {stdout.strip()}")
            return True
        else:
            self.log_step(f"VPS connection test failed: {stderr}", "error")
            return False
    
    def step_3_upload_deployment_scripts(self) -> bool:
        """Step 3: Upload deployment scripts to VPS."""
        self.current_step = 3
        self.log_step("Uploading deployment scripts")
        
        files_to_upload = [
            ('setup_contabo_vps.sh', '/tmp/setup_contabo_vps.sh'),
            ('validate_deployment.py', '/tmp/validate_deployment.py')
        ]
        
        for local_file, remote_file in files_to_upload:
            if not self.upload_file(local_file, remote_file):
                return False
        
        # Make scripts executable
        exit_code, stdout, stderr = self.execute_remote_command('chmod +x /tmp/setup_contabo_vps.sh /tmp/validate_deployment.py')
        if exit_code != 0:
            self.log_step(f"Failed to make scripts executable: {stderr}", "error")
            return False
        
        self.log_step("Deployment scripts uploaded successfully")
        return True
    
    def step_4_prepare_environment(self) -> bool:
        """Step 4: Prepare environment variables."""
        self.current_step = 4
        self.log_step("Preparing environment variables")
        
        env_setup = self.prepare_environment_variables()
        if not env_setup:
            self.log_step("No environment variables to set", "warning")
            return True
        
        # Create environment setup script
        env_script = f"#!/bin/bash\n{env_setup}\n"
        
        # Write to temporary file and upload
        with open('/tmp/env_setup.sh', 'w') as f:
            f.write(env_script)
        
        if not self.upload_file('/tmp/env_setup.sh', '/tmp/env_setup.sh'):
            return False
        
        # Make executable
        exit_code, stdout, stderr = self.execute_remote_command('chmod +x /tmp/env_setup.sh')
        if exit_code != 0:
            self.log_step(f"Failed to make env script executable: {stderr}", "error")
            return False
        
        self.log_step("Environment variables prepared")
        return True
    
    def step_5_run_system_setup(self) -> bool:
        """Step 5: Run system setup script."""
        self.current_step = 5
        self.log_step("Running system setup (this may take 10-15 minutes)")
        
        # Source environment and run setup
        command = 'source /tmp/env_setup.sh && /tmp/setup_contabo_vps.sh'
        
        exit_code, stdout, stderr = self.execute_remote_command(command, timeout=1800)  # 30 minutes
        
        if exit_code == 0:
            self.log_step("System setup completed successfully")
            return True
        else:
            self.log_step(f"System setup failed: {stderr}", "error")
            # Log stdout for debugging
            if stdout:
                logger.info(f"Setup output: {stdout[-1000:]}...")  # Last 1000 chars
            return False
    
    def step_6_verify_services(self) -> bool:
        """Step 6: Verify services are running."""
        self.current_step = 6
        self.log_step("Verifying services")
        
        services_to_check = [
            'bulenox-trader',
            'nginx',
            'fail2ban'
        ]
        
        failed_services = []
        for service in services_to_check:
            exit_code, stdout, stderr = self.execute_remote_command(f'systemctl is-active {service}')
            if exit_code != 0 or stdout.strip() != 'active':
                failed_services.append(service)
        
        if failed_services:
            self.log_step(f"Services not running: {failed_services}", "warning")
            # Try to start failed services
            for service in failed_services:
                self.log_step(f"Attempting to start {service}")
                exit_code, stdout, stderr = self.execute_remote_command(f'systemctl start {service}')
                if exit_code == 0:
                    self.log_step(f"Successfully started {service}")
                else:
                    self.log_step(f"Failed to start {service}: {stderr}", "error")
        
        self.log_step("Service verification completed")
        return True
    
    def step_7_test_api_connectivity(self) -> bool:
        """Step 7: Test API connectivity."""
        self.current_step = 7
        self.log_step("Testing API connectivity")
        
        # Test health endpoint
        exit_code, stdout, stderr = self.execute_remote_command('curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health')
        
        if exit_code == 0 and stdout.strip() == '200':
            self.log_step("API health endpoint responding")
        else:
            self.log_step(f"API health endpoint not responding: {stderr}", "warning")
        
        # Test Nginx proxy
        exit_code, stdout, stderr = self.execute_remote_command('curl -s -o /dev/null -w "%{http_code}" http://localhost/health')
        
        if exit_code == 0 and stdout.strip() == '200':
            self.log_step("Nginx proxy working")
        else:
            self.log_step(f"Nginx proxy not working: {stderr}", "warning")
        
        return True
    
    def step_8_run_deployment_validation(self) -> bool:
        """Step 8: Run comprehensive deployment validation."""
        self.current_step = 8
        self.log_step("Running deployment validation")
        
        exit_code, stdout, stderr = self.execute_remote_command('cd /opt/trading-bot/src && python3 /tmp/validate_deployment.py')
        
        if exit_code == 0:
            self.log_step("Deployment validation passed")
            # Log validation summary
            if 'DEPLOYMENT READY' in stdout:
                self.log_step("✅ Bot is ready for production use!")
            return True
        else:
            self.log_step(f"Deployment validation failed: {stderr}", "error")
            # Log validation output for debugging
            if stdout:
                logger.info(f"Validation output: {stdout}")
            return False
    
    def step_9_setup_monitoring(self) -> bool:
        """Step 9: Setup monitoring and alerts."""
        self.current_step = 9
        self.log_step("Setting up monitoring")
        
        # Start monitoring service
        exit_code, stdout, stderr = self.execute_remote_command('systemctl start bulenox-trader-monitor')
        if exit_code == 0:
            self.log_step("Monitoring service started")
        else:
            self.log_step(f"Failed to start monitoring service: {stderr}", "warning")
        
        # Test monitoring commands
        exit_code, stdout, stderr = self.execute_remote_command('monitor-bot --report')
        if exit_code == 0:
            self.log_step("Monitoring commands working")
        else:
            self.log_step(f"Monitoring commands not working: {stderr}", "warning")
        
        return True
    
    def step_10_create_backup(self) -> bool:
        """Step 10: Create initial backup."""
        self.current_step = 10
        self.log_step("Creating initial backup")
        
        exit_code, stdout, stderr = self.execute_remote_command('/opt/trading-bot/backup.sh')
        if exit_code == 0:
            self.log_step("Initial backup created")
            return True
        else:
            self.log_step(f"Failed to create backup: {stderr}", "warning")
            return True  # Non-critical
    
    def step_11_security_hardening(self) -> bool:
        """Step 11: Apply security hardening."""
        self.current_step = 11
        self.log_step("Applying security hardening")
        
        security_commands = [
            'ufw reload',
            'fail2ban-client reload',
            'chmod 600 /opt/trading-bot/.env',
            'chown trader:trader /opt/trading-bot/.env'
        ]
        
        for command in security_commands:
            exit_code, stdout, stderr = self.execute_remote_command(command)
            if exit_code != 0:
                self.log_step(f"Security command failed: {command} - {stderr}", "warning")
        
        self.log_step("Security hardening completed")
        return True
    
    def step_12_final_verification(self) -> bool:
        """Step 12: Final verification and status report."""
        self.current_step = 12
        self.log_step("Running final verification")
        
        # Get system status
        exit_code, stdout, stderr = self.execute_remote_command('remote-mgmt status')
        if exit_code == 0:
            self.log_step("Final status check passed")
            logger.info(f"System Status:\n{stdout}")
        else:
            self.log_step(f"Final status check failed: {stderr}", "warning")
        
        # Get service logs
        exit_code, stdout, stderr = self.execute_remote_command('journalctl -u bulenox-trader --no-pager -n 20')
        if exit_code == 0 and stdout:
            logger.info(f"Recent service logs:\n{stdout}")
        
        self.log_step("Deployment completed successfully!")
        return True
    
    def execute_deployment(self) -> bool:
        """Execute complete deployment process."""
        logger.info("🚀 Starting Bulenox Trading Bot deployment to Contabo VPS")
        logger.info(f"📊 Total steps: {self.total_steps}")
        
        deployment_steps = [
            self.step_1_validate_prerequisites,
            self.step_2_connect_vps,
            self.step_3_upload_deployment_scripts,
            self.step_4_prepare_environment,
            self.step_5_run_system_setup,
            self.step_6_verify_services,
            self.step_7_test_api_connectivity,
            self.step_8_run_deployment_validation,
            self.step_9_setup_monitoring,
            self.step_10_create_backup,
            self.step_11_security_hardening,
            self.step_12_final_verification
        ]
        
        try:
            for step_func in deployment_steps:
                if not step_func():
                    self.log_step(f"Deployment failed at step {self.current_step}", "error")
                    return False
                
                # Small delay between steps
                time.sleep(2)
            
            # Calculate deployment time
            deployment_time = datetime.now() - self.start_time
            self.log_step(f"Deployment completed in {deployment_time}")
            
            return True
            
        except KeyboardInterrupt:
            self.log_step("Deployment interrupted by user", "error")
            return False
        except Exception as e:
            self.log_step(f"Deployment failed with exception: {e}", "error")
            return False
        finally:
            if self.ssh_client:
                self.ssh_client.close()
    
    def save_deployment_log(self, filename: str = 'deployment_log.json'):
        """Save deployment log to file."""
        try:
            log_data = {
                'deployment_info': {
                    'start_time': self.start_time.isoformat(),
                    'end_time': datetime.now().isoformat(),
                    'total_steps': self.total_steps,
                    'completed_steps': self.current_step
                },
                'configuration': self.config,
                'deployment_log': self.deployment_log
            }
            
            with open(filename, 'w') as f:
                json.dump(log_data, f, indent=2)
            
            logger.info(f"✅ Deployment log saved to {filename}")
        except Exception as e:
            logger.error(f"❌ Failed to save deployment log: {e}")
    
    def print_deployment_summary(self):
        """Print deployment summary."""
        print("\n" + "="*60)
        print("🎉 BULENOX TRADING BOT - DEPLOYMENT SUMMARY")
        print("="*60)
        
        deployment_time = datetime.now() - self.start_time
        print(f"\n⏱️  Deployment Time: {deployment_time}")
        print(f"📊 Steps Completed: {self.current_step}/{self.total_steps}")
        
        # Count log entries by type
        errors = len([log for log in self.deployment_log if log['type'] == 'error'])
        warnings = len([log for log in self.deployment_log if log['type'] == 'warning'])
        
        print(f"❌ Errors: {errors}")
        print(f"⚠️ Warnings: {warnings}")
        
        if self.current_step == self.total_steps and errors == 0:
            print("\n🎉 DEPLOYMENT SUCCESSFUL!")
            print("\n📋 Next Steps:")
            print("   1. Access your VPS and check service status")
            print("   2. Monitor logs: remote-mgmt logs --follow")
            print("   3. Test trading functionality")
            print("   4. Setup domain and SSL if needed")
        else:
            print("\n⚠️ DEPLOYMENT INCOMPLETE")
            print("\nPlease check the deployment log for details.")
        
        print("\n" + "="*60)

def main():
    """Main deployment function."""
    parser = argparse.ArgumentParser(description='Deploy Bulenox Trading Bot to Contabo VPS')
    parser.add_argument('--config', default='contabo_deployment_config.json', help='Configuration file')
    parser.add_argument('--dry-run', action='store_true', help='Validate configuration without deploying')
    
    args = parser.parse_args()
    
    try:
        executor = ContaboDeploymentExecutor(args.config)
        
        if args.dry_run:
            logger.info("🔍 Running configuration validation (dry-run mode)")
            if executor.step_1_validate_prerequisites():
                logger.info("✅ Configuration validation passed")
                return 0
            else:
                logger.error("❌ Configuration validation failed")
                return 1
        
        # Execute deployment
        success = executor.execute_deployment()
        
        # Save deployment log
        executor.save_deployment_log()
        
        # Print summary
        executor.print_deployment_summary()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        logger.info("\n⚠️ Deployment interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"❌ Deployment execution failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())