#!/usr/bin/env python3
"""
Final Deployment Verification Script for TRAE-SentinelOps
Comprehensive validation of all deployment components before production deployment.
"""

import os
import sys
import json
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('final_deployment_verification.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class FinalDeploymentVerifier:
    def __init__(self):
        self.project_root = Path.cwd()
        self.verification_results = []
        self.critical_files = [
            # Core deployment scripts
            'deploy_to_production.sh',
            'deploy_contabo_vps.sh', 
            'deploy_to_contabo_vps.py',
            'setup_production_env.sh',
            'verify_deployment.sh',
            
            # Configuration files
            'contabo_deployment_config.json',
            'monitoring_config.json',
            'alert_config.json',
            
            # Python scripts
            'validate_production_system.py',
            'monitoring_dashboard.py',
            'test_deployment_scripts.py',
            
            # Frontend dashboard
            'dashboard.html',
            'dashboard.css', 
            'dashboard.js',
            
            # Documentation
            'PRODUCTION_DEPLOYMENT_CHECKLIST.md',
            'CONTABO_VPS_SETUP_GUIDE.md',
            'DEPLOYMENT_SUMMARY.md',
            
            # CI/CD
            '.github/workflows/deploy-production.yml'
        ]
        
        self.core_application_files = [
            'main.py',
            'trading_bot.py',
            'bulenox_trader.py',
            'requirements.txt',
            '.env.example'
        ]
        
    def add_result(self, category: str, test_name: str, status: str, message: str, details: str = ""):
        """Add a verification result"""
        result = {
            'category': category,
            'test_name': test_name,
            'status': status,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.verification_results.append(result)
        
        # Log the result
        status_emoji = {
            'PASS': '✅',
            'FAIL': '❌', 
            'WARN': '⚠️',
            'INFO': 'ℹ️'
        }.get(status, '❓')
        
        logger.info(f"{status_emoji} [{category}] {test_name}: {message}")
        
    def verify_file_structure(self) -> bool:
        """Verify all critical files exist"""
        logger.info("🔍 Verifying deployment file structure...")
        all_files_exist = True
        
        # Check critical deployment files
        for file_path in self.critical_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                file_size = full_path.stat().st_size
                self.add_result(
                    'File Structure', 
                    f'Critical File: {file_path}',
                    'PASS',
                    f'File exists ({file_size:,} bytes)'
                )
            else:
                self.add_result(
                    'File Structure',
                    f'Critical File: {file_path}', 
                    'FAIL',
                    'File missing - required for deployment'
                )
                all_files_exist = False
                
        # Check core application files
        for file_path in self.core_application_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                self.add_result(
                    'Application Files',
                    f'Core File: {file_path}',
                    'PASS', 
                    'Application file exists'
                )
            else:
                self.add_result(
                    'Application Files',
                    f'Core File: {file_path}',
                    'WARN',
                    'Application file missing - may affect functionality'
                )
                
        return all_files_exist
        
    def verify_configuration_files(self) -> bool:
        """Verify JSON configuration files are valid"""
        logger.info("🔧 Verifying configuration files...")
        all_configs_valid = True
        
        config_files = [
            'contabo_deployment_config.json',
            'monitoring_config.json', 
            'alert_config.json'
        ]
        
        for config_file in config_files:
            config_path = self.project_root / config_file
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                    
                    # Validate specific configuration requirements
                    if config_file == 'contabo_deployment_config.json':
                        required_keys = ['deployment', 'vps_connection', 'environment']
                        missing_keys = [key for key in required_keys if key not in config_data]
                        if missing_keys:
                            self.add_result(
                                'Configuration',
                                f'Config Validation: {config_file}',
                                'WARN',
                                f'Missing keys: {missing_keys}'
                            )
                        else:
                            self.add_result(
                                'Configuration',
                                f'Config Validation: {config_file}',
                                'PASS',
                                'All required keys present'
                            )
                    
                    elif config_file == 'monitoring_config.json':
                        if 'monitoring' in config_data and 'system_metrics' in config_data['monitoring']:
                            self.add_result(
                                'Configuration',
                                f'Config Validation: {config_file}',
                                'PASS',
                                'Monitoring configuration is complete'
                            )
                        else:
                            self.add_result(
                                'Configuration', 
                                f'Config Validation: {config_file}',
                                'WARN',
                                'Monitoring configuration may be incomplete'
                            )
                    
                    elif config_file == 'alert_config.json':
                        if 'alerting' in config_data and 'alert_rules' in config_data:
                            self.add_result(
                                'Configuration',
                                f'Config Validation: {config_file}',
                                'PASS',
                                'Alert configuration is complete'
                            )
                        else:
                            self.add_result(
                                'Configuration',
                                f'Config Validation: {config_file}',
                                'WARN', 
                                'Alert configuration may be incomplete'
                            )
                            
                except json.JSONDecodeError as e:
                    self.add_result(
                        'Configuration',
                        f'Config Validation: {config_file}',
                        'FAIL',
                        f'Invalid JSON: {str(e)}'
                    )
                    all_configs_valid = False
                except Exception as e:
                    self.add_result(
                        'Configuration',
                        f'Config Validation: {config_file}',
                        'FAIL',
                        f'Error reading config: {str(e)}'
                    )
                    all_configs_valid = False
            else:
                self.add_result(
                    'Configuration',
                    f'Config Validation: {config_file}',
                    'FAIL',
                    'Configuration file missing'
                )
                all_configs_valid = False
                
        return all_configs_valid
        
    def verify_python_scripts(self) -> bool:
        """Verify Python scripts have valid syntax"""
        logger.info("🐍 Verifying Python script syntax...")
        all_scripts_valid = True
        
        python_scripts = [
            'deploy_to_contabo_vps.py',
            'validate_production_system.py',
            'monitoring_dashboard.py',
            'test_deployment_scripts.py',
            'final_deployment_verification.py'
        ]
        
        for script in python_scripts:
            script_path = self.project_root / script
            if script_path.exists():
                try:
                    # Check syntax by compiling
                    with open(script_path, 'r', encoding='utf-8') as f:
                        source_code = f.read()
                    
                    compile(source_code, script_path, 'exec')
                    self.add_result(
                        'Python Scripts',
                        f'Syntax Check: {script}',
                        'PASS',
                        'Python syntax is valid'
                    )
                    
                except SyntaxError as e:
                    self.add_result(
                        'Python Scripts',
                        f'Syntax Check: {script}',
                        'FAIL',
                        f'Syntax error: {str(e)}'
                    )
                    all_scripts_valid = False
                except Exception as e:
                    self.add_result(
                        'Python Scripts',
                        f'Syntax Check: {script}',
                        'WARN',
                        f'Could not verify: {str(e)}'
                    )
            else:
                self.add_result(
                    'Python Scripts',
                    f'Syntax Check: {script}',
                    'WARN',
                    'Script file not found'
                )
                
        return all_scripts_valid
        
    def verify_deployment_readiness(self) -> bool:
        """Verify deployment readiness indicators"""
        logger.info("🚀 Verifying deployment readiness...")
        
        # Check if requirements.txt exists and has content
        requirements_path = self.project_root / 'requirements.txt'
        if requirements_path.exists():
            with open(requirements_path, 'r') as f:
                requirements_content = f.read().strip()
            if requirements_content:
                req_count = len([line for line in requirements_content.split('\n') if line.strip() and not line.startswith('#')])
                self.add_result(
                    'Deployment Readiness',
                    'Requirements File',
                    'PASS',
                    f'Requirements file contains {req_count} packages'
                )
            else:
                self.add_result(
                    'Deployment Readiness',
                    'Requirements File',
                    'WARN',
                    'Requirements file is empty'
                )
        else:
            self.add_result(
                'Deployment Readiness',
                'Requirements File',
                'FAIL',
                'Requirements file missing'
            )
            
        # Check for .env.example
        env_example_path = self.project_root / '.env.example'
        if env_example_path.exists():
            self.add_result(
                'Deployment Readiness',
                'Environment Template',
                'PASS',
                'Environment template exists for configuration'
            )
        else:
            self.add_result(
                'Deployment Readiness',
                'Environment Template',
                'WARN',
                'No .env.example found - may complicate deployment'
            )
            
        # Check for main application entry point
        main_files = ['main.py', 'app.py', 'run.py']
        main_found = False
        for main_file in main_files:
            if (self.project_root / main_file).exists():
                self.add_result(
                    'Deployment Readiness',
                    'Application Entry Point',
                    'PASS',
                    f'Main application file found: {main_file}'
                )
                main_found = True
                break
                
        if not main_found:
            self.add_result(
                'Deployment Readiness',
                'Application Entry Point',
                'WARN',
                'No clear application entry point found'
            )
            
        return True
        
    def verify_security_considerations(self) -> bool:
        """Verify security-related configurations"""
        logger.info("🔒 Verifying security considerations...")
        
        # Check for .env in .gitignore
        gitignore_path = self.project_root / '.gitignore'
        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                gitignore_content = f.read()
            if '.env' in gitignore_content:
                self.add_result(
                    'Security',
                    'Environment File Protection',
                    'PASS',
                    '.env files are properly ignored by git'
                )
            else:
                self.add_result(
                    'Security',
                    'Environment File Protection',
                    'WARN',
                    '.env not found in .gitignore - potential security risk'
                )
        else:
            self.add_result(
                'Security',
                'Environment File Protection',
                'WARN',
                'No .gitignore found - consider adding one'
            )
            
        # Check for hardcoded secrets in Python files
        python_files = list(self.project_root.glob('*.py'))
        secrets_found = False
        
        suspicious_patterns = [
            'password=',
            'api_key=',
            'secret=',
            'token=',
            'key="',
            "key='"
        ]
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                
                for pattern in suspicious_patterns:
                    if pattern in content and 'os.getenv' not in content:
                        secrets_found = True
                        break
                        
            except Exception:
                continue
                
        if secrets_found:
            self.add_result(
                'Security',
                'Hardcoded Secrets Check',
                'WARN',
                'Potential hardcoded secrets found - review code'
            )
        else:
            self.add_result(
                'Security',
                'Hardcoded Secrets Check',
                'PASS',
                'No obvious hardcoded secrets detected'
            )
            
        return True
        
    def generate_deployment_report(self) -> Dict[str, Any]:
        """Generate comprehensive deployment report"""
        # Calculate statistics
        total_tests = len(self.verification_results)
        passed_tests = len([r for r in self.verification_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.verification_results if r['status'] == 'FAIL'])
        warning_tests = len([r for r in self.verification_results if r['status'] == 'WARN'])
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Determine deployment readiness
        deployment_ready = failed_tests == 0
        
        # Generate recommendations
        recommendations = []
        if failed_tests > 0:
            recommendations.append(f"🚨 CRITICAL: Fix {failed_tests} failed test(s) before deployment")
        if warning_tests > 0:
            recommendations.append(f"⚠️ Review {warning_tests} warning(s) and address if necessary")
        if success_rate >= 90:
            recommendations.append("✅ System appears ready for deployment")
        elif success_rate >= 75:
            recommendations.append("⚠️ System mostly ready - address warnings before deployment")
        else:
            recommendations.append("❌ System not ready for deployment - significant issues detected")
            
        # Add specific recommendations based on results
        categories_with_failures = set()
        for result in self.verification_results:
            if result['status'] == 'FAIL':
                categories_with_failures.add(result['category'])
                
        if 'File Structure' in categories_with_failures:
            recommendations.append("📁 Ensure all critical deployment files are present")
        if 'Configuration' in categories_with_failures:
            recommendations.append("🔧 Fix configuration file issues before deployment")
        if 'Python Scripts' in categories_with_failures:
            recommendations.append("🐍 Fix Python syntax errors in deployment scripts")
            
        report = {
            'verification_summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'warnings': warning_tests,
                'success_rate': f"{success_rate:.1f}%",
                'deployment_ready': deployment_ready
            },
            'test_results': self.verification_results,
            'recommendations': recommendations,
            'deployment_checklist': {
                'critical_files_present': failed_tests == 0,
                'configurations_valid': len([r for r in self.verification_results if r['category'] == 'Configuration' and r['status'] == 'FAIL']) == 0,
                'scripts_syntactically_correct': len([r for r in self.verification_results if r['category'] == 'Python Scripts' and r['status'] == 'FAIL']) == 0,
                'security_considerations_addressed': len([r for r in self.verification_results if r['category'] == 'Security' and r['status'] == 'FAIL']) == 0
            },
            'next_steps': [
                "1. Review and address any failed tests",
                "2. Consider addressing warnings for optimal deployment", 
                "3. Test deployment scripts in staging environment",
                "4. Prepare production environment variables",
                "5. Execute deployment using deploy_to_production.sh",
                "6. Monitor system using dashboard and alerts"
            ],
            'timestamp': datetime.now().isoformat()
        }
        
        return report
        
    def run_comprehensive_verification(self) -> Dict[str, Any]:
        """Run all verification checks"""
        logger.info("🔍 Starting comprehensive deployment verification...")
        
        # Run all verification steps
        self.verify_file_structure()
        self.verify_configuration_files()
        self.verify_python_scripts()
        self.verify_deployment_readiness()
        self.verify_security_considerations()
        
        # Generate final report
        report = self.generate_deployment_report()
        
        # Save report to file
        report_file = self.project_root / 'final_deployment_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        logger.info(f"📊 Final deployment report saved: {report_file}")
        
        return report
        
    def print_summary(self, report: Dict[str, Any]):
        """Print verification summary"""
        summary = report['verification_summary']
        
        print("\n" + "="*60)
        print("🚀 FINAL DEPLOYMENT VERIFICATION SUMMARY")
        print("="*60)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"✅ Passed: {summary['passed']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"⚠️  Warnings: {summary['warnings']}")
        print(f"Success Rate: {summary['success_rate']}")
        print(f"Deployment Ready: {'✅ YES' if summary['deployment_ready'] else '❌ NO'}")
        
        print("\n📋 RECOMMENDATIONS:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"{i}. {rec}")
            
        print("\n🎯 NEXT STEPS:")
        for step in report['next_steps']:
            print(f"   {step}")
            
        print("="*60)
        
def main():
    """Main execution function"""
    try:
        verifier = FinalDeploymentVerifier()
        report = verifier.run_comprehensive_verification()
        verifier.print_summary(report)
        
        # Exit with appropriate code
        if report['verification_summary']['deployment_ready']:
            logger.info("🎉 System is ready for deployment!")
            sys.exit(0)
        else:
            logger.warning("⚠️ System requires attention before deployment")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Verification failed: {str(e)}")
        sys.exit(1)
        
if __name__ == '__main__':
    main()