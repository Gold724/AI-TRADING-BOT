#!/usr/bin/env python3
"""
AI Trading Sentinel - Deployment Scripts Testing
TRAE-SentinelOps: Comprehensive validation of cloud deployment infrastructure

This script tests all deployment components:
- Bash deployment scripts syntax and functionality
- Python deployment scripts
- Configuration files validation
- CI/CD pipeline configuration
- Environment setup scripts
- Monitoring and verification scripts

Author: TRAE-SentinelOps
Version: 1.0.0
Date: 2025-01-17
"""

import os
import sys
import json
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deployment_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DeploymentTester')

class DeploymentScriptTester:
    """Test suite for deployment scripts and configurations"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.test_results = []
        self.passed_tests = 0
        self.failed_tests = 0
        self.warnings = 0
        
    def log_test_result(self, test_name: str, status: str, message: str, details: str = ""):
        """Log test result with status"""
        result = {
            'test_name': test_name,
            'status': status,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        
        self.test_results.append(result)
        
        if status == 'PASS':
            self.passed_tests += 1
            logger.info(f"✅ {test_name}: {message}")
        elif status == 'FAIL':
            self.failed_tests += 1
            logger.error(f"❌ {test_name}: {message}")
        elif status == 'WARN':
            self.warnings += 1
            logger.warning(f"⚠️  {test_name}: {message}")
            
    def test_file_exists(self, file_path: str, description: str = "") -> bool:
        """Test if a file exists"""
        full_path = self.project_root / file_path
        test_name = f"File Exists: {file_path}"
        
        if full_path.exists():
            self.log_test_result(test_name, 'PASS', f"File found: {description}")
            return True
        else:
            self.log_test_result(test_name, 'FAIL', f"File missing: {description}")
            return False
            
    def test_bash_script_syntax(self, script_path: str) -> bool:
        """Test bash script syntax using bash -n"""
        full_path = self.project_root / script_path
        test_name = f"Bash Syntax: {script_path}"
        
        if not full_path.exists():
            self.log_test_result(test_name, 'FAIL', "Script file not found")
            return False
            
        try:
            # Test syntax on Windows using WSL or Git Bash if available
            result = subprocess.run(
                ['bash', '-n', str(full_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.log_test_result(test_name, 'PASS', "Syntax is valid")
                return True
            else:
                self.log_test_result(test_name, 'FAIL', f"Syntax error: {result.stderr}")
                return False
                
        except FileNotFoundError:
            self.log_test_result(test_name, 'WARN', "Bash not available for syntax check")
            return False
        except subprocess.TimeoutExpired:
            self.log_test_result(test_name, 'FAIL', "Syntax check timed out")
            return False
        except Exception as e:
            self.log_test_result(test_name, 'FAIL', f"Error checking syntax: {str(e)}")
            return False
            
    def test_python_script_syntax(self, script_path: str) -> bool:
        """Test Python script syntax"""
        full_path = self.project_root / script_path
        test_name = f"Python Syntax: {script_path}"
        
        if not full_path.exists():
            self.log_test_result(test_name, 'FAIL', "Script file not found")
            return False
            
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                code = f.read()
                
            compile(code, str(full_path), 'exec')
            self.log_test_result(test_name, 'PASS', "Syntax is valid")
            return True
            
        except SyntaxError as e:
            self.log_test_result(test_name, 'FAIL', f"Syntax error: {str(e)}")
            return False
        except Exception as e:
            self.log_test_result(test_name, 'FAIL', f"Error checking syntax: {str(e)}")
            return False
            
    def test_json_config_validity(self, config_path: str) -> bool:
        """Test JSON configuration file validity"""
        full_path = self.project_root / config_path
        test_name = f"JSON Config: {config_path}"
        
        if not full_path.exists():
            self.log_test_result(test_name, 'FAIL', "Config file not found")
            return False
            
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                json.load(f)
            self.log_test_result(test_name, 'PASS', "JSON is valid")
            return True
            
        except json.JSONDecodeError as e:
            self.log_test_result(test_name, 'FAIL', f"JSON error: {str(e)}")
            return False
        except Exception as e:
            self.log_test_result(test_name, 'FAIL', f"Error reading config: {str(e)}")
            return False
            
    def test_deployment_script_completeness(self, script_path: str) -> bool:
        """Test if deployment script has required functions"""
        full_path = self.project_root / script_path
        test_name = f"Script Completeness: {script_path}"
        
        if not full_path.exists():
            self.log_test_result(test_name, 'FAIL', "Script file not found")
            return False
            
        required_functions = [
            'setup_system_dependencies',
            'setup_python_environment', 
            'setup_nginx',
            'setup_firewall',
            'create_systemd_service'
        ]
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            missing_functions = []
            for func in required_functions:
                if func not in content:
                    missing_functions.append(func)
                    
            if not missing_functions:
                self.log_test_result(test_name, 'PASS', "All required functions present")
                return True
            else:
                self.log_test_result(test_name, 'WARN', f"Missing functions: {', '.join(missing_functions)}")
                return False
                
        except Exception as e:
            self.log_test_result(test_name, 'FAIL', f"Error reading script: {str(e)}")
            return False
            
    def test_github_actions_workflow(self, workflow_path: str) -> bool:
        """Test GitHub Actions workflow configuration"""
        full_path = self.project_root / workflow_path
        test_name = f"GitHub Actions: {workflow_path}"
        
        if not full_path.exists():
            self.log_test_result(test_name, 'FAIL', "Workflow file not found")
            return False
            
        try:
            import yaml
            with open(full_path, 'r', encoding='utf-8') as f:
                workflow = yaml.safe_load(f)
                
            # Check required workflow components
            required_keys = ['name', 'on', 'jobs']
            missing_keys = [key for key in required_keys if key not in workflow]
            
            if not missing_keys:
                self.log_test_result(test_name, 'PASS', "Workflow structure is valid")
                return True
            else:
                self.log_test_result(test_name, 'FAIL', f"Missing keys: {', '.join(missing_keys)}")
                return False
                
        except ImportError:
            self.log_test_result(test_name, 'WARN', "PyYAML not available for workflow validation")
            return False
        except Exception as e:
            self.log_test_result(test_name, 'FAIL', f"Error validating workflow: {str(e)}")
            return False
            
    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run all deployment tests"""
        logger.info("🚀 Starting comprehensive deployment script testing...")
        
        # Test deployment scripts existence
        deployment_scripts = [
            ('deploy_to_production.sh', 'Main production deployment script'),
            ('deploy_contabo_vps.sh', 'Contabo VPS specific deployment'),
            ('deploy_to_contabo_vps.py', 'Python deployment automation'),
            ('setup_production_env.sh', 'Production environment setup'),
            ('verify_deployment.sh', 'Deployment verification script')
        ]
        
        for script, description in deployment_scripts:
            self.test_file_exists(script, description)
            
        # Test bash script syntax
        bash_scripts = [
            'deploy_to_production.sh',
            'deploy_contabo_vps.sh', 
            'setup_production_env.sh',
            'verify_deployment.sh'
        ]
        
        for script in bash_scripts:
            self.test_bash_script_syntax(script)
            
        # Test Python script syntax
        python_scripts = [
            'deploy_to_contabo_vps.py',
            'validate_production_system.py',
            'monitoring_dashboard.py'
        ]
        
        for script in python_scripts:
            self.test_python_script_syntax(script)
            
        # Test configuration files
        config_files = [
            'contabo_deployment_config.json',
            'monitoring_config.json',
            'alert_config.json'
        ]
        
        for config in config_files:
            self.test_json_config_validity(config)
            
        # Test deployment script completeness
        for script in bash_scripts:
            self.test_deployment_script_completeness(script)
            
        # Test GitHub Actions workflow
        self.test_github_actions_workflow('.github/workflows/deploy-production.yml')
        
        # Test critical files
        critical_files = [
            ('PRODUCTION_DEPLOYMENT_CHECKLIST.md', 'Production deployment guide'),
            ('dashboard.html', 'Monitoring dashboard template'),
            ('dashboard.css', 'Dashboard styling'),
            ('dashboard.js', 'Dashboard JavaScript')
        ]
        
        for file_path, description in critical_files:
            self.test_file_exists(file_path, description)
            
        return self.generate_test_report()
        
    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_tests = len(self.test_results)
        
        report = {
            'test_summary': {
                'total_tests': total_tests,
                'passed': self.passed_tests,
                'failed': self.failed_tests,
                'warnings': self.warnings,
                'success_rate': f"{(self.passed_tests / total_tests * 100):.1f}%" if total_tests > 0 else "0%"
            },
            'test_results': self.test_results,
            'recommendations': self.generate_recommendations(),
            'timestamp': datetime.now().isoformat()
        }
        
        # Save report to file
        report_file = self.project_root / 'deployment_test_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
            
        logger.info(f"📊 Test Report Generated: {report_file}")
        return report
        
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        if self.failed_tests > 0:
            recommendations.append("Fix failed tests before deployment")
            
        if self.warnings > 0:
            recommendations.append("Review warnings and consider improvements")
            
        # Check for specific issues
        failed_tests = [r for r in self.test_results if r['status'] == 'FAIL']
        
        if any('Bash Syntax' in r['test_name'] for r in failed_tests):
            recommendations.append("Install Git Bash or WSL for proper bash script testing")
            
        if any('GitHub Actions' in r['test_name'] for r in failed_tests):
            recommendations.append("Install PyYAML: pip install pyyaml")
            
        if not recommendations:
            recommendations.append("All tests passed! Ready for deployment.")
            
        return recommendations
        
    def print_summary(self):
        """Print test summary"""
        total = len(self.test_results)
        print("\n" + "="*60)
        print("🔍 DEPLOYMENT SCRIPTS TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(f"⚠️  Warnings: {self.warnings}")
        
        if total > 0:
            success_rate = (self.passed_tests / total) * 100
            print(f"Success Rate: {success_rate:.1f}%")
            
        print("\n📋 RECOMMENDATIONS:")
        for i, rec in enumerate(self.generate_recommendations(), 1):
            print(f"{i}. {rec}")
            
        print("="*60)

def main():
    """Main test execution"""
    print("🚀 AI Trading Sentinel - Deployment Scripts Testing")
    print("TRAE-SentinelOps: Validating cloud deployment infrastructure")
    print("="*60)
    
    tester = DeploymentScriptTester()
    report = tester.run_comprehensive_tests()
    tester.print_summary()
    
    # Exit with appropriate code
    if tester.failed_tests > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()