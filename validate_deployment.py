#!/usr/bin/env python3
"""
Bulenox Trading Bot - Deployment Validation Script
TRAE-SentinelOps v2.0.0 - Production Readiness Checker

This script validates that the Bulenox trading bot deployment
is properly configured and ready for production use.
"""

import os
import sys
import json
import time
import requests
import subprocess
import socket
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('deployment_validation.log')
    ]
)
logger = logging.getLogger(__name__)

class DeploymentValidator:
    """Comprehensive deployment validation for Bulenox trading bot."""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'validation_results': {},
            'overall_status': 'unknown',
            'critical_issues': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Configuration
        self.deploy_path = '/opt/trading-bot'
        self.service_name = 'bulenox-trader'
        self.api_port = 5000
        self.websocket_port = 5001
        self.required_files = [
            'bulenox_ai_playwright_contracts.py',
            'monitor_trading_bot.py',
            'remote_management.py',
            'requirements.txt',
            '.env'
        ]
        
    def run_command(self, command: str) -> Tuple[int, str, str]:
        """Execute shell command and return result."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, '', 'Command timed out'
        except Exception as e:
            return -1, '', str(e)
    
    def check_system_requirements(self) -> Dict:
        """Validate system requirements and dependencies."""
        logger.info("Checking system requirements...")
        
        checks = {
            'python_version': False,
            'nodejs_version': False,
            'playwright_installed': False,
            'nginx_running': False,
            'firewall_configured': False,
            'fail2ban_active': False
        }
        
        # Check Python version
        code, stdout, stderr = self.run_command('python3 --version')
        if code == 0 and 'Python 3.' in stdout:
            version = stdout.strip().split()[1]
            if version >= '3.10':
                checks['python_version'] = True
                logger.info(f"✅ Python version: {version}")
            else:
                logger.warning(f"⚠️ Python version {version} < 3.10")
        else:
            logger.error("❌ Python 3.10+ not found")
        
        # Check Node.js version
        code, stdout, stderr = self.run_command('node --version')
        if code == 0 and stdout.strip().startswith('v'):
            version = stdout.strip()
            checks['nodejs_version'] = True
            logger.info(f"✅ Node.js version: {version}")
        else:
            logger.error("❌ Node.js not found")
        
        # Check Playwright
        code, stdout, stderr = self.run_command('python3 -c "import playwright; print(playwright.__version__)"')
        if code == 0:
            checks['playwright_installed'] = True
            logger.info(f"✅ Playwright installed: {stdout.strip()}")
        else:
            logger.error("❌ Playwright not installed")
        
        # Check Nginx
        code, stdout, stderr = self.run_command('systemctl is-active nginx')
        if code == 0 and stdout.strip() == 'active':
            checks['nginx_running'] = True
            logger.info("✅ Nginx is running")
        else:
            logger.error("❌ Nginx is not running")
        
        # Check UFW firewall
        code, stdout, stderr = self.run_command('ufw status')
        if code == 0 and 'Status: active' in stdout:
            checks['firewall_configured'] = True
            logger.info("✅ UFW firewall is active")
        else:
            logger.warning("⚠️ UFW firewall not active")
        
        # Check Fail2ban
        code, stdout, stderr = self.run_command('systemctl is-active fail2ban')
        if code == 0 and stdout.strip() == 'active':
            checks['fail2ban_active'] = True
            logger.info("✅ Fail2ban is active")
        else:
            logger.warning("⚠️ Fail2ban not active")
        
        return checks
    
    def check_file_structure(self) -> Dict:
        """Validate deployment file structure."""
        logger.info("Checking file structure...")
        
        checks = {
            'deploy_directory': False,
            'source_files': False,
            'virtual_environment': False,
            'environment_file': False,
            'log_directories': False,
            'backup_directory': False
        }
        
        # Check deployment directory
        if Path(self.deploy_path).exists():
            checks['deploy_directory'] = True
            logger.info(f"✅ Deploy directory exists: {self.deploy_path}")
        else:
            logger.error(f"❌ Deploy directory missing: {self.deploy_path}")
            return checks
        
        # Check source files
        src_path = Path(self.deploy_path) / 'src'
        if src_path.exists():
            missing_files = []
            for file in self.required_files:
                if not (src_path / file).exists():
                    missing_files.append(file)
            
            if not missing_files:
                checks['source_files'] = True
                logger.info("✅ All required source files present")
            else:
                logger.error(f"❌ Missing files: {missing_files}")
        else:
            logger.error("❌ Source directory missing")
        
        # Check virtual environment
        venv_path = src_path / 'venv'
        if venv_path.exists() and (venv_path / 'bin' / 'python').exists():
            checks['virtual_environment'] = True
            logger.info("✅ Virtual environment configured")
        else:
            logger.error("❌ Virtual environment missing")
        
        # Check environment file
        env_file = Path(self.deploy_path) / '.env'
        if env_file.exists():
            checks['environment_file'] = True
            logger.info("✅ Environment file exists")
            
            # Check file permissions
            stat = env_file.stat()
            if oct(stat.st_mode)[-3:] == '600':
                logger.info("✅ Environment file has secure permissions")
            else:
                logger.warning("⚠️ Environment file permissions not secure")
        else:
            logger.error("❌ Environment file missing")
        
        # Check log directories
        log_dirs = ['/var/log', f'{self.deploy_path}/logs']
        all_exist = all(Path(d).exists() for d in log_dirs)
        if all_exist:
            checks['log_directories'] = True
            logger.info("✅ Log directories exist")
        else:
            logger.warning("⚠️ Some log directories missing")
        
        # Check backup directory
        backup_dir = Path(self.deploy_path) / 'backups'
        if backup_dir.exists():
            checks['backup_directory'] = True
            logger.info("✅ Backup directory exists")
        else:
            logger.warning("⚠️ Backup directory missing")
        
        return checks
    
    def check_services(self) -> Dict:
        """Validate systemd services."""
        logger.info("Checking services...")
        
        checks = {
            'trading_service': False,
            'monitoring_service': False,
            'service_enabled': False,
            'service_logs': False
        }
        
        # Check trading service
        code, stdout, stderr = self.run_command(f'systemctl is-active {self.service_name}')
        if code == 0 and stdout.strip() == 'active':
            checks['trading_service'] = True
            logger.info(f"✅ Trading service {self.service_name} is active")
        else:
            logger.error(f"❌ Trading service {self.service_name} not active")
        
        # Check monitoring service
        monitor_service = f'{self.service_name}-monitor'
        code, stdout, stderr = self.run_command(f'systemctl is-active {monitor_service}')
        if code == 0 and stdout.strip() == 'active':
            checks['monitoring_service'] = True
            logger.info(f"✅ Monitoring service {monitor_service} is active")
        else:
            logger.warning(f"⚠️ Monitoring service {monitor_service} not active")
        
        # Check if services are enabled
        code, stdout, stderr = self.run_command(f'systemctl is-enabled {self.service_name}')
        if code == 0 and stdout.strip() == 'enabled':
            checks['service_enabled'] = True
            logger.info(f"✅ Service {self.service_name} is enabled")
        else:
            logger.warning(f"⚠️ Service {self.service_name} not enabled")
        
        # Check service logs
        code, stdout, stderr = self.run_command(f'journalctl -u {self.service_name} --no-pager -n 10')
        if code == 0 and stdout:
            checks['service_logs'] = True
            logger.info("✅ Service logs accessible")
        else:
            logger.warning("⚠️ Service logs not accessible")
        
        return checks
    
    def check_network_connectivity(self) -> Dict:
        """Validate network connectivity and ports."""
        logger.info("Checking network connectivity...")
        
        checks = {
            'api_port_open': False,
            'websocket_port_open': False,
            'nginx_proxy': False,
            'external_connectivity': False,
            'ssl_certificate': False
        }
        
        # Check API port
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('localhost', self.api_port))
            if result == 0:
                checks['api_port_open'] = True
                logger.info(f"✅ API port {self.api_port} is open")
            else:
                logger.error(f"❌ API port {self.api_port} not accessible")
            sock.close()
        except Exception as e:
            logger.error(f"❌ Error checking API port: {e}")
        
        # Check WebSocket port
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('localhost', self.websocket_port))
            if result == 0:
                checks['websocket_port_open'] = True
                logger.info(f"✅ WebSocket port {self.websocket_port} is open")
            else:
                logger.warning(f"⚠️ WebSocket port {self.websocket_port} not accessible")
            sock.close()
        except Exception as e:
            logger.warning(f"⚠️ Error checking WebSocket port: {e}")
        
        # Check Nginx proxy
        try:
            response = requests.get('http://localhost/health', timeout=10)
            if response.status_code == 200:
                checks['nginx_proxy'] = True
                logger.info("✅ Nginx proxy working")
            else:
                logger.warning(f"⚠️ Nginx proxy returned status {response.status_code}")
        except Exception as e:
            logger.warning(f"⚠️ Nginx proxy not accessible: {e}")
        
        # Check external connectivity
        try:
            response = requests.get('https://httpbin.org/ip', timeout=10)
            if response.status_code == 200:
                checks['external_connectivity'] = True
                logger.info("✅ External connectivity working")
            else:
                logger.warning("⚠️ External connectivity issues")
        except Exception as e:
            logger.warning(f"⚠️ External connectivity failed: {e}")
        
        # Check SSL certificate
        code, stdout, stderr = self.run_command('certbot certificates')
        if code == 0 and 'Found the following certs' in stdout:
            checks['ssl_certificate'] = True
            logger.info("✅ SSL certificate configured")
        else:
            logger.info("ℹ️ SSL certificate not configured (optional)")
        
        return checks
    
    def check_api_endpoints(self) -> Dict:
        """Validate API endpoints and functionality."""
        logger.info("Checking API endpoints...")
        
        checks = {
            'health_endpoint': False,
            'status_endpoint': False,
            'api_response_time': False,
            'contract_validation': False
        }
        
        base_url = f'http://localhost:{self.api_port}'
        
        # Check health endpoint
        try:
            start_time = time.time()
            response = requests.get(f'{base_url}/health', timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                checks['health_endpoint'] = True
                logger.info("✅ Health endpoint responding")
                
                if response_time < 2.0:
                    checks['api_response_time'] = True
                    logger.info(f"✅ API response time: {response_time:.2f}s")
                else:
                    logger.warning(f"⚠️ Slow API response: {response_time:.2f}s")
            else:
                logger.error(f"❌ Health endpoint returned {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Health endpoint error: {e}")
        
        # Check status endpoint
        try:
            response = requests.get(f'{base_url}/api/status', timeout=10)
            if response.status_code == 200:
                checks['status_endpoint'] = True
                logger.info("✅ Status endpoint responding")
            else:
                logger.warning(f"⚠️ Status endpoint returned {response.status_code}")
        except Exception as e:
            logger.warning(f"⚠️ Status endpoint error: {e}")
        
        # Check contract validation
        try:
            test_data = {'contract_size': 1.5}
            response = requests.post(
                f'{base_url}/api/validate-contract',
                json=test_data,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if 'validated_size' in data:
                    checks['contract_validation'] = True
                    logger.info("✅ Contract validation working")
                else:
                    logger.warning("⚠️ Contract validation response invalid")
            else:
                logger.warning(f"⚠️ Contract validation returned {response.status_code}")
        except Exception as e:
            logger.warning(f"⚠️ Contract validation error: {e}")
        
        return checks
    
    def check_environment_config(self) -> Dict:
        """Validate environment configuration."""
        logger.info("Checking environment configuration...")
        
        checks = {
            'env_file_readable': False,
            'required_vars_set': False,
            'credentials_configured': False,
            'security_settings': False
        }
        
        env_file = Path(self.deploy_path) / '.env'
        
        if not env_file.exists():
            logger.error("❌ Environment file not found")
            return checks
        
        try:
            with open(env_file, 'r') as f:
                env_content = f.read()
            
            checks['env_file_readable'] = True
            logger.info("✅ Environment file readable")
            
            # Check required variables
            required_vars = [
                'BULENOX_USERNAME',
                'BULENOX_PASSWORD',
                'FLASK_SECRET_KEY',
                'ENVIRONMENT'
            ]
            
            missing_vars = []
            for var in required_vars:
                if f'{var}=' not in env_content or f'{var}=' in env_content and not env_content.split(f'{var}=')[1].split('\n')[0].strip():
                    missing_vars.append(var)
            
            if not missing_vars:
                checks['required_vars_set'] = True
                logger.info("✅ All required environment variables set")
            else:
                logger.error(f"❌ Missing environment variables: {missing_vars}")
            
            # Check credentials
            if 'BULENOX_USERNAME=' in env_content and 'BULENOX_PASSWORD=' in env_content:
                username_line = [line for line in env_content.split('\n') if line.startswith('BULENOX_USERNAME=')]
                password_line = [line for line in env_content.split('\n') if line.startswith('BULENOX_PASSWORD=')]
                
                if username_line and password_line:
                    username = username_line[0].split('=', 1)[1].strip()
                    password = password_line[0].split('=', 1)[1].strip()
                    
                    if username and password and username != 'your_username' and password != 'your_password':
                        checks['credentials_configured'] = True
                        logger.info("✅ Bulenox credentials configured")
                    else:
                        logger.error("❌ Bulenox credentials not properly configured")
            
            # Check security settings
            security_vars = ['HEADLESS_MODE=true', 'RISK_MANAGEMENT_ENABLED=true', 'EMERGENCY_STOP_ENABLED=true']
            security_ok = all(var in env_content for var in security_vars)
            
            if security_ok:
                checks['security_settings'] = True
                logger.info("✅ Security settings configured")
            else:
                logger.warning("⚠️ Some security settings not configured")
        
        except Exception as e:
            logger.error(f"❌ Error reading environment file: {e}")
        
        return checks
    
    def check_monitoring_setup(self) -> Dict:
        """Validate monitoring and logging setup."""
        logger.info("Checking monitoring setup...")
        
        checks = {
            'log_rotation': False,
            'cron_jobs': False,
            'backup_script': False,
            'monitoring_commands': False
        }
        
        # Check log rotation
        logrotate_file = f'/etc/logrotate.d/{self.service_name}'
        if Path(logrotate_file).exists():
            checks['log_rotation'] = True
            logger.info("✅ Log rotation configured")
        else:
            logger.warning("⚠️ Log rotation not configured")
        
        # Check cron jobs
        code, stdout, stderr = self.run_command('crontab -l')
        if code == 0 and (self.service_name in stdout or 'trading-bot' in stdout):
            checks['cron_jobs'] = True
            logger.info("✅ Cron jobs configured")
        else:
            logger.warning("⚠️ Cron jobs not configured")
        
        # Check backup script
        backup_script = Path(self.deploy_path) / 'backup.sh'
        if backup_script.exists() and backup_script.is_file():
            checks['backup_script'] = True
            logger.info("✅ Backup script exists")
        else:
            logger.warning("⚠️ Backup script missing")
        
        # Check monitoring commands
        monitor_cmd = Path('/usr/local/bin/monitor-bot')
        remote_cmd = Path('/usr/local/bin/remote-mgmt')
        
        if monitor_cmd.exists() and remote_cmd.exists():
            checks['monitoring_commands'] = True
            logger.info("✅ Monitoring commands available")
        else:
            logger.warning("⚠️ Monitoring commands not available")
        
        return checks
    
    def generate_report(self) -> Dict:
        """Generate comprehensive validation report."""
        logger.info("Generating validation report...")
        
        # Run all validation checks
        self.results['validation_results'] = {
            'system_requirements': self.check_system_requirements(),
            'file_structure': self.check_file_structure(),
            'services': self.check_services(),
            'network_connectivity': self.check_network_connectivity(),
            'api_endpoints': self.check_api_endpoints(),
            'environment_config': self.check_environment_config(),
            'monitoring_setup': self.check_monitoring_setup()
        }
        
        # Calculate overall status
        total_checks = 0
        passed_checks = 0
        critical_failed = 0
        
        critical_checks = [
            'system_requirements.python_version',
            'system_requirements.playwright_installed',
            'file_structure.deploy_directory',
            'file_structure.source_files',
            'file_structure.environment_file',
            'services.trading_service',
            'network_connectivity.api_port_open',
            'environment_config.required_vars_set',
            'environment_config.credentials_configured'
        ]
        
        for category, checks in self.results['validation_results'].items():
            for check, status in checks.items():
                total_checks += 1
                if status:
                    passed_checks += 1
                else:
                    check_path = f'{category}.{check}'
                    if check_path in critical_checks:
                        critical_failed += 1
                        self.results['critical_issues'].append(check_path)
                    else:
                        self.results['warnings'].append(check_path)
        
        # Determine overall status
        if critical_failed == 0:
            if passed_checks / total_checks >= 0.9:
                self.results['overall_status'] = 'excellent'
            elif passed_checks / total_checks >= 0.8:
                self.results['overall_status'] = 'good'
            else:
                self.results['overall_status'] = 'acceptable'
        else:
            self.results['overall_status'] = 'critical_issues'
        
        # Add recommendations
        if self.results['critical_issues']:
            self.results['recommendations'].append(
                "Fix critical issues before deploying to production"
            )
        
        if self.results['warnings']:
            self.results['recommendations'].append(
                "Address warnings to improve system reliability"
            )
        
        if not self.results['validation_results']['network_connectivity']['ssl_certificate']:
            self.results['recommendations'].append(
                "Consider setting up SSL certificate for production use"
            )
        
        if not self.results['validation_results']['monitoring_setup']['cron_jobs']:
            self.results['recommendations'].append(
                "Setup automated monitoring and backup cron jobs"
            )
        
        # Calculate success rate
        success_rate = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
        self.results['success_rate'] = round(success_rate, 2)
        self.results['total_checks'] = total_checks
        self.results['passed_checks'] = passed_checks
        
        return self.results
    
    def save_report(self, filename: str = 'deployment_validation_report.json'):
        """Save validation report to file."""
        try:
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2)
            logger.info(f"✅ Validation report saved to {filename}")
        except Exception as e:
            logger.error(f"❌ Failed to save report: {e}")
    
    def print_summary(self):
        """Print validation summary to console."""
        print("\n" + "="*60)
        print("🚀 BULENOX TRADING BOT - DEPLOYMENT VALIDATION REPORT")
        print("="*60)
        
        # Overall status
        status_emoji = {
            'excellent': '🟢',
            'good': '🟡',
            'acceptable': '🟠',
            'critical_issues': '🔴'
        }
        
        print(f"\n📊 Overall Status: {status_emoji.get(self.results['overall_status'], '❓')} {self.results['overall_status'].upper()}")
        print(f"📈 Success Rate: {self.results['success_rate']}% ({self.results['passed_checks']}/{self.results['total_checks']} checks passed)")
        
        # Critical issues
        if self.results['critical_issues']:
            print(f"\n🚨 Critical Issues ({len(self.results['critical_issues'])}):"))
            for issue in self.results['critical_issues']:
                print(f"   ❌ {issue}")
        
        # Warnings
        if self.results['warnings']:
            print(f"\n⚠️  Warnings ({len(self.results['warnings'])}):"))
            for warning in self.results['warnings']:
                print(f"   ⚠️ {warning}")
        
        # Recommendations
        if self.results['recommendations']:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(self.results['recommendations'], 1):
                print(f"   {i}. {rec}")
        
        # Category breakdown
        print(f"\n📋 Category Breakdown:")
        for category, checks in self.results['validation_results'].items():
            passed = sum(1 for status in checks.values() if status)
            total = len(checks)
            percentage = (passed / total * 100) if total > 0 else 0
            
            status_icon = "✅" if percentage == 100 else "⚠️" if percentage >= 80 else "❌"
            print(f"   {status_icon} {category.replace('_', ' ').title()}: {passed}/{total} ({percentage:.0f}%)")
        
        print("\n" + "="*60)
        
        if self.results['overall_status'] == 'critical_issues':
            print("🚨 DEPLOYMENT NOT READY - Fix critical issues before production use")
        elif self.results['overall_status'] in ['excellent', 'good']:
            print("🎉 DEPLOYMENT READY - Bot is ready for production use!")
        else:
            print("⚠️ DEPLOYMENT NEEDS ATTENTION - Address warnings for optimal performance")
        
        print("="*60 + "\n")

def main():
    """Main validation function."""
    print("🔍 Starting Bulenox Trading Bot deployment validation...")
    
    validator = DeploymentValidator()
    
    try:
        # Generate validation report
        report = validator.generate_report()
        
        # Save report
        validator.save_report()
        
        # Print summary
        validator.print_summary()
        
        # Exit with appropriate code
        if report['overall_status'] == 'critical_issues':
            sys.exit(1)
        else:
            sys.exit(0)
    
    except KeyboardInterrupt:
        logger.info("\n⚠️ Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Validation failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()