#!/usr/bin/env python3
"""
🚀 AI Trading Sentinel - Deployment Validator
TRAE-SentinelOps: Comprehensive validation for 5-step deployment process

This script validates each step of the deployment process:
1. VPS deployment validation
2. Credential configuration validation
3. System deployment validation
4. Monitoring system validation
5. Trading system validation
"""

import os
import sys
import json
import time
import requests
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    NC = '\033[0m'  # No Color
    BOLD = '\033[1m'

class DeploymentValidator:
    """Comprehensive deployment validation for AI Trading Sentinel"""
    
    def __init__(self, environment: str = "production"):
        self.environment = environment
        self.project_root = project_root
        self.results = {
            'step1_vps_deployment': {'status': 'pending', 'checks': [], 'score': 0},
            'step2_credentials': {'status': 'pending', 'checks': [], 'score': 0},
            'step3_system_validation': {'status': 'pending', 'checks': [], 'score': 0},
            'step4_monitoring': {'status': 'pending', 'checks': [], 'score': 0},
            'step5_trading': {'status': 'pending', 'checks': [], 'score': 0}
        }
        self.total_score = 0
        self.max_score = 0
        
    def log(self, message: str, color: str = Colors.BLUE):
        """Log message with timestamp and color"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"{color}[{timestamp}] {message}{Colors.NC}")
        
    def success(self, message: str):
        """Log success message"""
        print(f"{Colors.GREEN}✓ {message}{Colors.NC}")
        
    def warning(self, message: str):
        """Log warning message"""
        print(f"{Colors.YELLOW}⚠ {message}{Colors.NC}")
        
    def error(self, message: str):
        """Log error message"""
        print(f"{Colors.RED}✗ {message}{Colors.NC}")
        
    def header(self, title: str):
        """Print section header"""
        print(f"\n{Colors.PURPLE}{title}{Colors.NC}")
        print(f"{Colors.PURPLE}{'=' * len(title)}{Colors.NC}")
        
    def check_file_exists(self, file_path: str, description: str) -> bool:
        """Check if file exists"""
        exists = os.path.exists(file_path)
        if exists:
            self.success(f"{description}: {file_path}")
        else:
            self.error(f"{description} missing: {file_path}")
        return exists
        
    def check_command_available(self, command: str, description: str) -> bool:
        """Check if command is available"""
        try:
            subprocess.run([command, '--version'], 
                         capture_output=True, check=True, timeout=10)
            self.success(f"{description} is available")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            self.error(f"{description} not available")
            return False
            
    def check_service_running(self, service_name: str, description: str) -> bool:
        """Check if service is running (systemd)"""
        try:
            result = subprocess.run(['systemctl', 'is-active', service_name],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip() == 'active':
                self.success(f"{description} service is running")
                return True
            else:
                self.error(f"{description} service not running")
                return False
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            self.warning(f"Cannot check {description} service status (systemctl not available)")
            return False
            
    def check_url_accessible(self, url: str, description: str, timeout: int = 10) -> bool:
        """Check if URL is accessible"""
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                self.success(f"{description} accessible: {url}")
                return True
            else:
                self.error(f"{description} returned status {response.status_code}: {url}")
                return False
        except requests.RequestException as e:
            self.error(f"{description} not accessible: {url} ({str(e)})")
            return False
            
    def validate_step1_vps_deployment(self) -> Dict:
        """Step 1: Validate VPS deployment"""
        self.header("STEP 1: VPS Deployment Validation")
        
        checks = []
        score = 0
        
        # Check deployment script exists
        if self.check_file_exists("deploy/deploy-production.sh", "Production deployment script"):
            checks.append({"name": "Deployment script", "status": "pass", "weight": 2})
            score += 2
        else:
            checks.append({"name": "Deployment script", "status": "fail", "weight": 2})
            
        # Check system requirements
        system_checks = [
            ("python3", "Python 3", 3),
            ("node", "Node.js", 2),
            ("npm", "NPM", 2),
            ("git", "Git", 2),
            ("docker", "Docker", 2),
        ]
        
        for cmd, desc, weight in system_checks:
            if self.check_command_available(cmd, desc):
                checks.append({"name": desc, "status": "pass", "weight": weight})
                score += weight
            else:
                checks.append({"name": desc, "status": "fail", "weight": weight})
                
        # Check directory structure
        required_dirs = [
            "src", "scripts", "deploy", "logs", "config", "monitoring"
        ]
        
        for dir_name in required_dirs:
            if os.path.exists(dir_name):
                checks.append({"name": f"Directory {dir_name}", "status": "pass", "weight": 1})
                score += 1
            else:
                checks.append({"name": f"Directory {dir_name}", "status": "fail", "weight": 1})
                
        max_step_score = sum(check['weight'] for check in checks)
        status = "pass" if score >= max_step_score * 0.8 else "fail"
        
        self.results['step1_vps_deployment'] = {
            'status': status,
            'checks': checks,
            'score': score,
            'max_score': max_step_score
        }
        
        return self.results['step1_vps_deployment']
        
    def validate_step2_credentials(self) -> Dict:
        """Step 2: Validate credential configuration"""
        self.header("STEP 2: Credential Configuration Validation")
        
        checks = []
        score = 0
        
        # Check .env file exists
        env_file = ".env"
        if self.check_file_exists(env_file, ".env configuration file"):
            checks.append({"name": ".env file exists", "status": "pass", "weight": 3})
            score += 3
            
            # Load and validate .env content
            try:
                with open(env_file, 'r') as f:
                    env_content = f.read()
                    
                required_vars = [
                    ("SECRET_KEY", "Application secret key", 2),
                    ("JWT_SECRET", "JWT secret key", 2),
                    ("ENCRYPTION_KEY", "Encryption key", 2),
                    ("ENVIRONMENT", "Environment setting", 1),
                    ("DEBUG", "Debug setting", 1),
                    ("TRADING_ENABLED", "Trading enabled flag", 2),
                    ("BROKER_USERNAME", "Broker username", 3),
                    ("BROKER_PASSWORD", "Broker password", 3),
                    ("BROKER_URL", "Broker URL", 2),
                    ("DATABASE_URL", "Database URL", 2),
                    ("REDIS_URL", "Redis URL", 2)
                ]
                
                for var_name, desc, weight in required_vars:
                    if f"{var_name}=" in env_content:
                        # Check if not using default/placeholder values
                        if "your-" not in env_content.split(f"{var_name}=")[1].split('\n')[0].lower():
                            checks.append({"name": desc, "status": "pass", "weight": weight})
                            score += weight
                        else:
                            checks.append({"name": f"{desc} (placeholder)", "status": "warning", "weight": weight})
                            score += weight // 2
                    else:
                        checks.append({"name": desc, "status": "fail", "weight": weight})
                        
            except Exception as e:
                self.error(f"Error reading .env file: {e}")
                checks.append({"name": ".env file readable", "status": "fail", "weight": 2})
        else:
            checks.append({"name": ".env file exists", "status": "fail", "weight": 3})
            
        # Check .env.template exists
        if self.check_file_exists(".env.template", ".env template file"):
            checks.append({"name": ".env template", "status": "pass", "weight": 1})
            score += 1
        else:
            checks.append({"name": ".env template", "status": "fail", "weight": 1})
            
        max_step_score = sum(check['weight'] for check in checks)
        status = "pass" if score >= max_step_score * 0.7 else "fail"
        
        self.results['step2_credentials'] = {
            'status': status,
            'checks': checks,
            'score': score,
            'max_score': max_step_score
        }
        
        return self.results['step2_credentials']
        
    def validate_step3_system_validation(self) -> Dict:
        """Step 3: Validate system deployment"""
        self.header("STEP 3: System Deployment Validation")
        
        checks = []
        score = 0
        
        # Check main application files
        app_files = [
            ("main.py", "Main trading bot", 3),
            ("backend_main.py", "Backend API server", 3),
            ("requirements.txt", "Python dependencies", 2),
            ("package.json", "Node.js dependencies", 2),
            ("src/trading/bot.py", "Trading bot core", 3),
            ("src/api/routes.py", "API routes", 2),
            ("config/config.yaml", "Configuration file", 2)
        ]
        
        for file_path, desc, weight in app_files:
            if self.check_file_exists(file_path, desc):
                checks.append({"name": desc, "status": "pass", "weight": weight})
                score += weight
            else:
                checks.append({"name": desc, "status": "fail", "weight": weight})
                
        # Check Python packages installed
        try:
            import flask, redis, psycopg2, playwright, pandas, numpy
            self.success("Core Python packages installed")
            checks.append({"name": "Python packages", "status": "pass", "weight": 3})
            score += 3
        except ImportError as e:
            self.error(f"Missing Python packages: {e}")
            checks.append({"name": "Python packages", "status": "fail", "weight": 3})
            
        # Check log directories
        log_dirs = ["logs", "logs/trading", "logs/api", "logs/monitoring"]
        for log_dir in log_dirs:
            if os.path.exists(log_dir):
                checks.append({"name": f"Log directory {log_dir}", "status": "pass", "weight": 1})
                score += 1
            else:
                checks.append({"name": f"Log directory {log_dir}", "status": "fail", "weight": 1})
                
        max_step_score = sum(check['weight'] for check in checks)
        status = "pass" if score >= max_step_score * 0.8 else "fail"
        
        self.results['step3_system_validation'] = {
            'status': status,
            'checks': checks,
            'score': score,
            'max_score': max_step_score
        }
        
        return self.results['step3_system_validation']
        
    def validate_step4_monitoring(self) -> Dict:
        """Step 4: Validate monitoring system"""
        self.header("STEP 4: Monitoring System Validation")
        
        checks = []
        score = 0
        
        # Check monitoring configuration files
        monitoring_files = [
            ("docker-compose.monitoring.yml", "Monitoring stack config", 3),
            ("monitoring/prometheus/prometheus.yml", "Prometheus config", 2),
            ("monitoring/grafana/dashboards/trading-dashboard.json", "Grafana dashboard", 2),
            ("monitoring/alertmanager/alertmanager.yml", "Alertmanager config", 2),
            ("scripts/system-monitor.sh", "System monitor script", 2)
        ]
        
        for file_path, desc, weight in monitoring_files:
            if self.check_file_exists(file_path, desc):
                checks.append({"name": desc, "status": "pass", "weight": weight})
                score += weight
            else:
                checks.append({"name": desc, "status": "fail", "weight": weight})
                
        # Check if Docker Compose is available
        if self.check_command_available("docker-compose", "Docker Compose"):
            checks.append({"name": "Docker Compose", "status": "pass", "weight": 2})
            score += 2
        else:
            checks.append({"name": "Docker Compose", "status": "fail", "weight": 2})
            
        # Check monitoring services accessibility
        monitoring_urls = [
            ("http://localhost:3000", "Grafana", 3),
            ("http://localhost:9090", "Prometheus", 3),
            ("http://localhost:9093", "Alertmanager", 2),
            ("http://localhost:8080", "cAdvisor", 1),
            ("http://localhost:9100/metrics", "Node Exporter", 1)
        ]
        
        for url, desc, weight in monitoring_urls:
            if self.check_url_accessible(url, desc, timeout=5):
                checks.append({"name": f"{desc} service", "status": "pass", "weight": weight})
                score += weight
            else:
                checks.append({"name": f"{desc} service", "status": "fail", "weight": weight})
                
        max_step_score = sum(check['weight'] for check in checks)
        status = "pass" if score >= max_step_score * 0.6 else "fail"  # Lower threshold for monitoring
        
        self.results['step4_monitoring'] = {
            'status': status,
            'checks': checks,
            'score': score,
            'max_score': max_step_score
        }
        
        return self.results['step4_monitoring']
        
    def validate_step5_trading(self) -> Dict:
        """Step 5: Validate trading system"""
        self.header("STEP 5: Trading System Validation")
        
        checks = []
        score = 0
        
        # Check application services
        app_urls = [
            ("http://localhost:5000/api/health", "Backend API health", 3),
            ("http://localhost:5000/api/status", "Trading bot status", 3),
            ("http://localhost:3000", "Frontend interface", 2),
            ("http://localhost:5000/api/metrics", "API metrics", 2)
        ]
        
        for url, desc, weight in app_urls:
            if self.check_url_accessible(url, desc, timeout=10):
                checks.append({"name": desc, "status": "pass", "weight": weight})
                score += weight
            else:
                checks.append({"name": desc, "status": "fail", "weight": weight})
                
        # Check systemd services (if available)
        if self.environment == "production":
            services = [
                ("trae.service", "Main trading service", 3),
                ("trae-backend.service", "Backend API service", 2)
            ]
            
            for service, desc, weight in services:
                if self.check_service_running(service, desc):
                    checks.append({"name": desc, "status": "pass", "weight": weight})
                    score += weight
                else:
                    checks.append({"name": desc, "status": "fail", "weight": weight})
                    
        # Check trading configuration
        try:
            # Try to import and validate trading modules
            sys.path.append('src')
            from trading.bot import TradingBot
            from api.app import create_app
            
            self.success("Trading modules importable")
            checks.append({"name": "Trading modules", "status": "pass", "weight": 2})
            score += 2
        except ImportError as e:
            self.error(f"Trading modules import error: {e}")
            checks.append({"name": "Trading modules", "status": "fail", "weight": 2})
            
        # Check log files
        log_files = [
            "logs/main.log", "logs/backend.log", "logs/trading/trades.log"
        ]
        
        for log_file in log_files:
            if os.path.exists(log_file):
                checks.append({"name": f"Log file {log_file}", "status": "pass", "weight": 1})
                score += 1
            else:
                checks.append({"name": f"Log file {log_file}", "status": "warning", "weight": 1})
                
        max_step_score = sum(check['weight'] for check in checks)
        status = "pass" if score >= max_step_score * 0.7 else "fail"
        
        self.results['step5_trading'] = {
            'status': status,
            'checks': checks,
            'score': score,
            'max_score': max_step_score
        }
        
        return self.results['step5_trading']
        
    def generate_report(self) -> Dict:
        """Generate comprehensive validation report"""
        self.header("🚀 DEPLOYMENT VALIDATION REPORT")
        
        # Calculate overall scores
        total_score = sum(step['score'] for step in self.results.values())
        max_total_score = sum(step['max_score'] for step in self.results.values())
        overall_percentage = (total_score / max_total_score * 100) if max_total_score > 0 else 0
        
        # Determine overall status
        if overall_percentage >= 90:
            overall_status = "excellent"
            status_color = Colors.GREEN
        elif overall_percentage >= 80:
            overall_status = "good"
            status_color = Colors.GREEN
        elif overall_percentage >= 70:
            overall_status = "acceptable"
            status_color = Colors.YELLOW
        elif overall_percentage >= 60:
            overall_status = "needs_improvement"
            status_color = Colors.YELLOW
        else:
            overall_status = "critical"
            status_color = Colors.RED
            
        print(f"\n{status_color}Overall Status: {overall_status.upper()} ({overall_percentage:.1f}%){Colors.NC}")
        print(f"Total Score: {total_score}/{max_total_score}\n")
        
        # Step-by-step results
        step_names = {
            'step1_vps_deployment': 'Step 1: VPS Deployment',
            'step2_credentials': 'Step 2: Credential Configuration',
            'step3_system_validation': 'Step 3: System Validation',
            'step4_monitoring': 'Step 4: Monitoring Setup',
            'step5_trading': 'Step 5: Trading System'
        }
        
        for step_key, step_name in step_names.items():
            step_result = self.results[step_key]
            step_percentage = (step_result['score'] / step_result['max_score'] * 100) if step_result['max_score'] > 0 else 0
            
            if step_result['status'] == 'pass':
                color = Colors.GREEN
                symbol = "✓"
            else:
                color = Colors.RED
                symbol = "✗"
                
            print(f"{color}{symbol} {step_name}: {step_percentage:.1f}% ({step_result['score']}/{step_result['max_score']}){Colors.NC}")
            
            # Show failed checks
            failed_checks = [check for check in step_result['checks'] if check['status'] == 'fail']
            if failed_checks:
                for check in failed_checks[:3]:  # Show first 3 failures
                    print(f"    {Colors.RED}• {check['name']}{Colors.NC}")
                if len(failed_checks) > 3:
                    print(f"    {Colors.RED}• ... and {len(failed_checks) - 3} more{Colors.NC}")
                    
        # Recommendations
        print(f"\n{Colors.BLUE}📋 RECOMMENDATIONS:{Colors.NC}")
        
        if overall_percentage < 80:
            print(f"{Colors.YELLOW}• Fix critical issues before proceeding to production{Colors.NC}")
            
        if self.results['step2_credentials']['score'] < self.results['step2_credentials']['max_score'] * 0.8:
            print(f"{Colors.YELLOW}• Update broker credentials in .env file{Colors.NC}")
            
        if self.results['step4_monitoring']['score'] < self.results['step4_monitoring']['max_score'] * 0.6:
            print(f"{Colors.YELLOW}• Start monitoring stack: docker-compose -f docker-compose.monitoring.yml up -d{Colors.NC}")
            
        if self.results['step5_trading']['score'] < self.results['step5_trading']['max_score'] * 0.7:
            print(f"{Colors.YELLOW}• Start application services before enabling trading{Colors.NC}")
            
        # Next steps
        print(f"\n{Colors.BLUE}🎯 NEXT STEPS:{Colors.NC}")
        if overall_percentage >= 80:
            print(f"{Colors.GREEN}• System ready for production deployment{Colors.NC}")
            print(f"{Colors.GREEN}• Monitor system for 24 hours before enabling live trading{Colors.NC}")
            print(f"{Colors.GREEN}• Test with demo account first{Colors.NC}")
        else:
            print(f"{Colors.RED}• Fix validation issues before deployment{Colors.NC}")
            print(f"{Colors.RED}• Re-run validation after fixes{Colors.NC}")
            
        # Save report
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'environment': self.environment,
            'overall_status': overall_status,
            'overall_percentage': overall_percentage,
            'total_score': total_score,
            'max_total_score': max_total_score,
            'steps': self.results
        }
        
        report_file = f"logs/deployment_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs("logs", exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
            
        print(f"\n{Colors.BLUE}📄 Report saved: {report_file}{Colors.NC}")
        
        return report_data
        
    def run_full_validation(self) -> Dict:
        """Run complete 5-step validation process"""
        print(f"{Colors.PURPLE}")
        print("██████╗ ██████╗  █████╗ ███████╗    ███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗     ")
        print("╚══██╔══╝██╔══██╗██╔══██╗██╔════╝    ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║     ")
        print("   ██║   ██████╔╝███████║█████╗      ███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║     ")
        print("   ██║   ██╔══██╗██╔══██║██╔══╝      ╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║     ")
        print("   ██║   ██║  ██║██║  ██║███████╗    ███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗███████╗")
        print("   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝    ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝")
        print(f"{Colors.NC}")
        print(f"{Colors.BLUE}🚀 AI Trading Sentinel - 5-Step Deployment Validator{Colors.NC}")
        print(f"{Colors.BLUE}TRAE-SentinelOps: Comprehensive Production Validation{Colors.NC}")
        print(f"{Colors.BLUE}Environment: {self.environment.upper()}{Colors.NC}\n")
        
        # Run all validation steps
        self.validate_step1_vps_deployment()
        self.validate_step2_credentials()
        self.validate_step3_system_validation()
        self.validate_step4_monitoring()
        self.validate_step5_trading()
        
        # Generate final report
        return self.generate_report()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="AI Trading Sentinel - 5-Step Deployment Validator",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--environment', '-e',
        choices=['local', 'production', 'all'],
        default='production',
        help='Environment to validate (default: production)'
    )
    
    parser.add_argument(
        '--step', '-s',
        choices=['1', '2', '3', '4', '5', 'all'],
        default='all',
        help='Specific step to validate (default: all)'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output file for validation report (JSON format)'
    )
    
    args = parser.parse_args()
    
    # Create validator
    validator = DeploymentValidator(args.environment)
    
    try:
        if args.step == 'all':
            # Run full validation
            report = validator.run_full_validation()
        else:
            # Run specific step
            step_methods = {
                '1': validator.validate_step1_vps_deployment,
                '2': validator.validate_step2_credentials,
                '3': validator.validate_step3_system_validation,
                '4': validator.validate_step4_monitoring,
                '5': validator.validate_step5_trading
            }
            
            result = step_methods[args.step]()
            report = {'step_result': result}
            
        # Save custom output if specified
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n{Colors.BLUE}Report saved to: {args.output}{Colors.NC}")
            
        # Exit with appropriate code
        if 'overall_percentage' in report:
            exit_code = 0 if report['overall_percentage'] >= 80 else 1
        else:
            exit_code = 0 if report['step_result']['status'] == 'pass' else 1
            
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Validation interrupted by user{Colors.NC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Validation failed with error: {e}{Colors.NC}")
        sys.exit(1)

if __name__ == "__main__":
    main()