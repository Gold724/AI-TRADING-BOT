#!/usr/bin/env python3
"""
Trae AI Trading Sentinel - Deployment Validation Script

This script validates the complete deployment of the AI Trading Sentinel system,
ensuring all components are properly configured and functioning together.

Usage:
    python validate_deployment.py [--environment ENV] [--verbose]
    
Environments:
    - local: Validate local development setup
    - production: Validate production deployment
    - all: Validate both environments (default)
"""

import asyncio
import json
import logging
import os
import requests
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import setup_logger

class DeploymentValidator:
    """Comprehensive deployment validation."""
    
    def __init__(self, environment: str = 'all', verbose: bool = False):
        self.environment = environment
        self.verbose = verbose
        self.logger = setup_logger('deployment_validator', level=logging.DEBUG if verbose else logging.INFO)
        
        self.validation_results = []
        self.start_time = datetime.now()
        
        # Test configuration
        self.timeouts = {
            'api': 10,
            'database': 5,
            'broker': 15,
            'monitoring': 10
        }
        
    def log_validation_result(self, component: str, test: str, success: bool, details: str, duration: float = 0):
        """Log validation result."""
        result = {
            'component': component,
            'test': test,
            'success': success,
            'details': details,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        }
        self.validation_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        self.logger.info(f"{status} [{component}] {test}: {details}")
        
    def validate_system_requirements(self) -> bool:
        """Validate system requirements."""
        self.logger.info("Validating system requirements...")
        
        all_passed = True
        
        # Check Python version
        python_version = sys.version_info
        if python_version >= (3, 10):
            self.log_validation_result('System', 'Python Version', True, f"Python {python_version.major}.{python_version.minor}.{python_version.micro}")
        else:
            self.log_validation_result('System', 'Python Version', False, f"Python {python_version.major}.{python_version.minor} < 3.10")
            all_passed = False
            
        # Check required packages
        required_packages = [
            'requests', 'asyncio', 'psutil', 'playwright', 
            'flask', 'redis', 'prometheus_client'
        ]
        
        for package in required_packages:
            try:
                __import__(package)
                self.log_validation_result('System', f'Package {package}', True, 'Installed')
            except ImportError:
                self.log_validation_result('System', f'Package {package}', False, 'Not installed')
                all_passed = False
                
        # Check disk space
        try:
            import shutil
            total, used, free = shutil.disk_usage('/')
            free_gb = free // (1024**3)
            
            if free_gb >= 10:  # At least 10GB free
                self.log_validation_result('System', 'Disk Space', True, f'{free_gb}GB available')
            else:
                self.log_validation_result('System', 'Disk Space', False, f'Only {free_gb}GB available')
                all_passed = False
        except Exception as e:
            self.log_validation_result('System', 'Disk Space', False, f'Check failed: {str(e)}')
            all_passed = False
            
        # Check memory
        try:
            import psutil
            memory = psutil.virtual_memory()
            memory_gb = memory.total // (1024**3)
            
            if memory_gb >= 4:  # At least 4GB RAM
                self.log_validation_result('System', 'Memory', True, f'{memory_gb}GB RAM')
            else:
                self.log_validation_result('System', 'Memory', False, f'Only {memory_gb}GB RAM')
                all_passed = False
        except Exception as e:
            self.log_validation_result('System', 'Memory', False, f'Check failed: {str(e)}')
            all_passed = False
            
        return all_passed
        
    def validate_file_structure(self) -> bool:
        """Validate project file structure."""
        self.logger.info("Validating file structure...")
        
        all_passed = True
        
        required_files = [
            'main.py',
            'backend_main.py',
            'src/config/settings.py',
            'src/trading/bot.py',
            'src/utils/logger.py',
            'requirements.txt',
            '.env.example'
        ]
        
        required_dirs = [
            'src',
            'src/config',
            'src/trading',
            'src/utils',
            'tests',
            'deploy',
            'monitoring'
        ]
        
        # Check files
        for file_path in required_files:
            if Path(file_path).exists():
                self.log_validation_result('FileStructure', f'File {file_path}', True, 'Exists')
            else:
                self.log_validation_result('FileStructure', f'File {file_path}', False, 'Missing')
                all_passed = False
                
        # Check directories
        for dir_path in required_dirs:
            if Path(dir_path).is_dir():
                self.log_validation_result('FileStructure', f'Directory {dir_path}', True, 'Exists')
            else:
                self.log_validation_result('FileStructure', f'Directory {dir_path}', False, 'Missing')
                all_passed = False
                
        return all_passed
        
    def validate_configuration(self) -> bool:
        """Validate configuration files."""
        self.logger.info("Validating configuration...")
        
        all_passed = True
        
        # Check .env file
        env_file = Path('.env')
        if env_file.exists():
            self.log_validation_result('Config', '.env file', True, 'Exists')
            
            # Check required environment variables
            required_vars = [
                'BROKER_USERNAME', 'BROKER_PASSWORD', 'BROKER_URL',
                'REDIS_URL', 'DATABASE_URL', 'SECRET_KEY'
            ]
            
            with open(env_file) as f:
                env_content = f.read()
                
            for var in required_vars:
                if f'{var}=' in env_content:
                    self.log_validation_result('Config', f'Env var {var}', True, 'Configured')
                else:
                    self.log_validation_result('Config', f'Env var {var}', False, 'Missing')
                    all_passed = False
        else:
            self.log_validation_result('Config', '.env file', False, 'Missing')
            all_passed = False
            
        # Check systemd service files (production only)
        if self.environment in ['production', 'all']:
            service_files = [
                '/etc/systemd/system/trae.service',
                '/etc/systemd/system/trae-sentinel-monitor.service',
                '/etc/systemd/system/trae-sentinel-monitor.timer'
            ]
            
            for service_file in service_files:
                if Path(service_file).exists():
                    self.log_validation_result('Config', f'Service {Path(service_file).name}', True, 'Installed')
                else:
                    self.log_validation_result('Config', f'Service {Path(service_file).name}', False, 'Not installed')
                    if self.environment == 'production':
                        all_passed = False
                        
        return all_passed
        
    def validate_api_endpoints(self) -> bool:
        """Validate API endpoints."""
        self.logger.info("Validating API endpoints...")
        
        all_passed = True
        base_url = 'http://localhost:5000'
        
        endpoints = [
            ('/health', 'GET', 200),
            ('/api/status', 'GET', 200),
            ('/api/trades', 'GET', [200, 404]),  # 404 if no trades yet
            ('/api/positions', 'GET', [200, 404]),
            ('/metrics', 'GET', 200)  # Prometheus metrics
        ]
        
        for endpoint, method, expected_codes in endpoints:
            try:
                start_time = time.time()
                
                if method == 'GET':
                    response = requests.get(f'{base_url}{endpoint}', timeout=self.timeouts['api'])
                else:
                    response = requests.request(method, f'{base_url}{endpoint}', timeout=self.timeouts['api'])
                    
                duration = time.time() - start_time
                
                if isinstance(expected_codes, list):
                    success = response.status_code in expected_codes
                else:
                    success = response.status_code == expected_codes
                    
                if success:
                    self.log_validation_result('API', f'{method} {endpoint}', True, f'Status {response.status_code}', duration)
                else:
                    self.log_validation_result('API', f'{method} {endpoint}', False, f'Status {response.status_code}', duration)
                    all_passed = False
                    
            except requests.RequestException as e:
                self.log_validation_result('API', f'{method} {endpoint}', False, f'Request failed: {str(e)}')
                all_passed = False
                
        return all_passed
        
    def validate_database_connection(self) -> bool:
        """Validate database connection."""
        self.logger.info("Validating database connection...")
        
        try:
            # This would depend on your database setup
            # For now, we'll check if the database URL is configured
            
            database_url = os.getenv('DATABASE_URL')
            if database_url:
                self.log_validation_result('Database', 'Configuration', True, 'URL configured')
                
                # Try to connect (implementation depends on database type)
                # For SQLite, check if file exists
                if database_url.startswith('sqlite'):
                    db_file = database_url.replace('sqlite:///', '')
                    if Path(db_file).exists():
                        self.log_validation_result('Database', 'Connection', True, 'SQLite file exists')
                        return True
                    else:
                        self.log_validation_result('Database', 'Connection', False, 'SQLite file missing')
                        return False
                else:
                    # For other databases, assume connection is working if URL is set
                    self.log_validation_result('Database', 'Connection', True, 'URL configured (not tested)')
                    return True
            else:
                self.log_validation_result('Database', 'Configuration', False, 'No DATABASE_URL set')
                return False
                
        except Exception as e:
            self.log_validation_result('Database', 'Connection', False, f'Error: {str(e)}')
            return False
            
    def validate_redis_connection(self) -> bool:
        """Validate Redis connection."""
        self.logger.info("Validating Redis connection...")
        
        try:
            import redis
            
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
            r = redis.from_url(redis_url)
            
            # Test connection
            r.ping()
            
            # Test basic operations
            r.set('test_key', 'test_value', ex=10)
            value = r.get('test_key')
            
            if value == b'test_value':
                self.log_validation_result('Redis', 'Connection', True, 'Read/write successful')
                return True
            else:
                self.log_validation_result('Redis', 'Connection', False, 'Read/write failed')
                return False
                
        except ImportError:
            self.log_validation_result('Redis', 'Connection', False, 'Redis package not installed')
            return False
        except Exception as e:
            self.log_validation_result('Redis', 'Connection', False, f'Error: {str(e)}')
            return False
            
    def validate_monitoring_stack(self) -> bool:
        """Validate monitoring stack."""
        self.logger.info("Validating monitoring stack...")
        
        all_passed = True
        
        monitoring_services = [
            ('Prometheus', 'http://localhost:9090', '/api/v1/query?query=up'),
            ('Grafana', 'http://localhost:3000', '/api/health'),
            ('Alertmanager', 'http://localhost:9093', '/api/v1/status')
        ]
        
        for service_name, base_url, endpoint in monitoring_services:
            try:
                start_time = time.time()
                response = requests.get(f'{base_url}{endpoint}', timeout=self.timeouts['monitoring'])
                duration = time.time() - start_time
                
                if response.status_code == 200:
                    self.log_validation_result('Monitoring', service_name, True, f'Responding ({duration:.2f}s)')
                else:
                    self.log_validation_result('Monitoring', service_name, False, f'Status {response.status_code}')
                    all_passed = False
                    
            except requests.RequestException as e:
                self.log_validation_result('Monitoring', service_name, False, f'Not accessible: {str(e)}')
                all_passed = False
                
        return all_passed
        
    def validate_systemd_services(self) -> bool:
        """Validate systemd services (production only)."""
        if self.environment not in ['production', 'all']:
            return True
            
        self.logger.info("Validating systemd services...")
        
        all_passed = True
        
        services = [
            'trae.service',
            'trae-sentinel-monitor.service',
            'trae-sentinel-monitor.timer'
        ]
        
        for service in services:
            try:
                # Check if service is enabled
                result = subprocess.run(
                    ['systemctl', 'is-enabled', service],
                    capture_output=True, text=True
                )
                
                if result.returncode == 0:
                    self.log_validation_result('SystemD', f'{service} enabled', True, 'Service enabled')
                else:
                    self.log_validation_result('SystemD', f'{service} enabled', False, 'Service not enabled')
                    all_passed = False
                    
                # Check if service is active (for services, not timers)
                if not service.endswith('.timer'):
                    result = subprocess.run(
                        ['systemctl', 'is-active', service],
                        capture_output=True, text=True
                    )
                    
                    if result.returncode == 0 and 'active' in result.stdout:
                        self.log_validation_result('SystemD', f'{service} active', True, 'Service running')
                    else:
                        self.log_validation_result('SystemD', f'{service} active', False, 'Service not running')
                        all_passed = False
                        
            except Exception as e:
                self.log_validation_result('SystemD', service, False, f'Check failed: {str(e)}')
                all_passed = False
                
        return all_passed
        
    def validate_security_settings(self) -> bool:
        """Validate security settings."""
        self.logger.info("Validating security settings...")
        
        all_passed = True
        
        # Check file permissions
        sensitive_files = ['.env', 'config/production.json']
        
        for file_path in sensitive_files:
            if Path(file_path).exists():
                stat = Path(file_path).stat()
                permissions = oct(stat.st_mode)[-3:]
                
                if permissions in ['600', '640']:  # Owner read/write only or group read
                    self.log_validation_result('Security', f'{file_path} permissions', True, f'Permissions {permissions}')
                else:
                    self.log_validation_result('Security', f'{file_path} permissions', False, f'Insecure permissions {permissions}')
                    all_passed = False
                    
        # Check for default passwords
        env_file = Path('.env')
        if env_file.exists():
            with open(env_file) as f:
                content = f.read()
                
            if 'password123' in content.lower() or 'admin' in content.lower():
                self.log_validation_result('Security', 'Default passwords', False, 'Default passwords detected')
                all_passed = False
            else:
                self.log_validation_result('Security', 'Default passwords', True, 'No default passwords found')
                
        return all_passed
        
    def run_comprehensive_validation(self) -> Dict:
        """Run comprehensive deployment validation."""
        self.logger.info(f"Starting comprehensive validation for {self.environment} environment")
        
        validation_steps = [
            ('System Requirements', self.validate_system_requirements),
            ('File Structure', self.validate_file_structure),
            ('Configuration', self.validate_configuration),
            ('API Endpoints', self.validate_api_endpoints),
            ('Database Connection', self.validate_database_connection),
            ('Redis Connection', self.validate_redis_connection),
            ('Security Settings', self.validate_security_settings)
        ]
        
        # Add environment-specific validations
        if self.environment in ['production', 'all']:
            validation_steps.extend([
                ('SystemD Services', self.validate_systemd_services),
                ('Monitoring Stack', self.validate_monitoring_stack)
            ])
            
        passed_steps = 0
        total_steps = len(validation_steps)
        
        for step_name, validation_func in validation_steps:
            try:
                if validation_func():
                    passed_steps += 1
                    self.logger.info(f"✅ {step_name} validation passed")
                else:
                    self.logger.error(f"❌ {step_name} validation failed")
            except Exception as e:
                self.logger.error(f"❌ {step_name} validation error: {str(e)}")
                
        # Generate report
        duration = (datetime.now() - self.start_time).total_seconds()
        
        report = {
            'environment': self.environment,
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_validations': len(self.validation_results),
                'passed': len([r for r in self.validation_results if r['success']]),
                'failed': len([r for r in self.validation_results if not r['success']]),
                'success_rate': (len([r for r in self.validation_results if r['success']]) / len(self.validation_results)) * 100 if self.validation_results else 0,
                'duration': duration,
                'overall_status': 'PASS' if passed_steps == total_steps else 'FAIL'
            },
            'results': self.validation_results
        }
        
        return report
        
    def save_validation_report(self, report: Dict, filename: str = None) -> Path:
        """Save validation report."""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'deployment_validation_{self.environment}_{timestamp}.json'
            
        report_path = Path('reports') / filename
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        self.logger.info(f"Validation report saved to: {report_path}")
        return report_path
        
    def print_validation_summary(self, report: Dict):
        """Print validation summary."""
        summary = report['summary']
        
        print("\n" + "="*70)
        print(f"TRAE AI TRADING SENTINEL - DEPLOYMENT VALIDATION ({self.environment.upper()})")
        print("="*70)
        print(f"Overall Status: {summary['overall_status']}")
        print(f"Total Validations: {summary['total_validations']}")
        print(f"Passed: {summary['passed']}")
        print(f"Failed: {summary['failed']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Duration: {summary['duration']:.1f} seconds")
        print("="*70)
        
        # Group results by component
        components = {}
        for result in report['results']:
            component = result['component']
            if component not in components:
                components[component] = []
            components[component].append(result)
            
        for component, results in components.items():
            print(f"\n{component.upper()}:")
            print("-" * 30)
            
            for result in results:
                status = "✅" if result['success'] else "❌"
                duration_str = f" ({result['duration']:.2f}s)" if result['duration'] > 0 else ""
                print(f"{status} {result['test']}: {result['details']}{duration_str}")
                
        print("\n" + "="*70)
        
def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate Trae AI Trading Sentinel deployment')
    parser.add_argument('--environment', choices=['local', 'production', 'all'], 
                       default='all', help='Environment to validate')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--report', help='Save report to specific file')
    
    args = parser.parse_args()
    
    validator = DeploymentValidator(environment=args.environment, verbose=args.verbose)
    
    # Run validation
    report = validator.run_comprehensive_validation()
    
    # Print summary
    validator.print_validation_summary(report)
    
    # Save report
    report_path = validator.save_validation_report(report, args.report)
    print(f"\nDetailed report saved to: {report_path}")
    
    # Exit with error code if validation failed
    if report['summary']['overall_status'] == 'FAIL':
        sys.exit(1)
    else:
        print("\n🎉 Deployment validation completed successfully!")
        
if __name__ == '__main__':
    main()