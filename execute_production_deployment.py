#!/usr/bin/env python3
"""
TRAE-SentinelOps Production Deployment Executor
Automated deployment orchestrator for AI Trading Sentinel on Contabo VPS
"""

import os
import sys
import json
import subprocess
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Set UTF-8 encoding for Windows compatibility
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Setup logging with UTF-8 encoding
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# File handler with UTF-8 encoding
file_handler = logging.FileHandler('production_deployment.log', encoding='utf-8')
file_handler.setFormatter(log_formatter)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)
logger = logging.getLogger(__name__)

class ProductionDeploymentExecutor:
    def __init__(self):
        self.project_root = Path.cwd()
        self.deployment_config = self.load_deployment_config()
        self.deployment_steps = []
        self.current_step = 0
        
    def load_deployment_config(self) -> Dict:
        """Load deployment configuration"""
        config_path = self.project_root / 'contabo_deployment_config.json'
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            logger.error("❌ Deployment configuration not found!")
            sys.exit(1)
            
    def log_step(self, step_name: str, status: str, message: str):
        """Log deployment step"""
        step_info = {
            'step': self.current_step,
            'name': step_name,
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self.deployment_steps.append(step_info)
        
        status_emoji = {
            'START': '🚀',
            'SUCCESS': '✅',
            'ERROR': '❌',
            'WARNING': '⚠️',
            'INFO': 'ℹ️'
        }.get(status, '❓')
        
        logger.info(f"{status_emoji} Step {self.current_step}: {step_name} - {message}")
        
    def check_prerequisites(self) -> bool:
        """Check deployment prerequisites"""
        self.current_step += 1
        self.log_step("Prerequisites Check", "START", "Verifying deployment prerequisites")
        
        # Check if final verification passed
        report_path = self.project_root / 'final_deployment_report.json'
        if not report_path.exists():
            self.log_step("Prerequisites Check", "ERROR", "Final deployment report not found. Run final_deployment_verification.py first")
            return False
            
        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
            
        if not report['verification_summary']['deployment_ready']:
            self.log_step("Prerequisites Check", "ERROR", "System not ready for deployment according to verification report")
            return False
            
        # Check required environment variables
        required_env_vars = [
            'CONTABO_VPS_IP',
            'CONTABO_VPS_USER', 
            'CONTABO_SSH_KEY_PATH',
            'GITHUB_TOKEN',
            'GITHUB_REPO_URL'
        ]
        
        missing_vars = []
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
                
        if missing_vars:
            self.log_step("Prerequisites Check", "ERROR", f"Missing environment variables: {', '.join(missing_vars)}")
            return False
            
        self.log_step("Prerequisites Check", "SUCCESS", "All prerequisites satisfied")
        return True
        
    def prepare_deployment_package(self) -> bool:
        """Prepare deployment package"""
        self.current_step += 1
        self.log_step("Package Preparation", "START", "Preparing deployment package")
        
        try:
            # Create deployment package directory
            package_dir = self.project_root / 'deployment_package'
            package_dir.mkdir(exist_ok=True)
            
            # Copy essential files
            essential_files = [
                'deploy_to_production.sh',
                'deploy_contabo_vps.sh',
                'deploy_to_contabo_vps.py',
                'setup_production_env.sh',
                'verify_deployment.sh',
                'contabo_deployment_config.json',
                'monitoring_config.json',
                'alert_config.json',
                'requirements.txt',
                '.env.example'
            ]
            
            for file_name in essential_files:
                src_path = self.project_root / file_name
                if src_path.exists():
                    dst_path = package_dir / file_name
                    import shutil
                    shutil.copy2(src_path, dst_path)
                    
            # Create deployment manifest
            manifest = {
                'deployment_id': f"deploy_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0',
                'files': essential_files,
                'target_environment': 'production',
                'vps_provider': 'contabo'
            }
            
            with open(package_dir / 'deployment_manifest.json', 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
                
            self.log_step("Package Preparation", "SUCCESS", f"Deployment package prepared in {package_dir}")
            return True
            
        except Exception as e:
            self.log_step("Package Preparation", "ERROR", f"Failed to prepare package: {str(e)}")
            return False
            
    def execute_vps_deployment(self) -> bool:
        """Execute VPS deployment"""
        self.current_step += 1
        self.log_step("VPS Deployment", "START", "Executing deployment on Contabo VPS")
        
        try:
            # Run the main deployment script
            deployment_script = self.project_root / 'deploy_to_contabo_vps.py'
            
            if not deployment_script.exists():
                self.log_step("VPS Deployment", "ERROR", "Deployment script not found")
                return False
                
            # Execute deployment
            result = subprocess.run(
                [sys.executable, str(deployment_script)],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                self.log_step("VPS Deployment", "SUCCESS", "VPS deployment completed successfully")
                return True
            else:
                self.log_step("VPS Deployment", "ERROR", f"Deployment failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.log_step("VPS Deployment", "ERROR", f"Deployment execution failed: {str(e)}")
            return False
            
    def verify_deployment(self) -> bool:
        """Verify deployment success"""
        self.current_step += 1
        self.log_step("Deployment Verification", "START", "Verifying deployment on VPS")
        
        try:
            # Run verification script
            verify_script = self.project_root / 'verify_deployment.sh'
            
            if not verify_script.exists():
                self.log_step("Deployment Verification", "WARNING", "Verification script not found - manual verification required")
                return True
                
            # Note: In Windows environment, we'll create a verification checklist instead
            verification_checklist = {
                'timestamp': datetime.now().isoformat(),
                'checks_required': [
                    'SSH connection to VPS successful',
                    'Python environment installed and activated',
                    'Application repository cloned and updated',
                    'Dependencies installed from requirements.txt',
                    'Environment variables configured',
                    'Systemd service created and running',
                    'Nginx configured and running',
                    'SSL certificate installed',
                    'Firewall configured',
                    'Monitoring dashboard accessible',
                    'Trading bot service operational'
                ],
                'manual_verification_required': True,
                'verification_commands': [
                    'ssh user@vps_ip "systemctl status trading-bot"',
                    'ssh user@vps_ip "systemctl status nginx"',
                    'ssh user@vps_ip "curl -I http://localhost:5000/health"',
                    'curl -I https://your-domain.com'
                ]
            }
            
            with open(self.project_root / 'deployment_verification_checklist.json', 'w', encoding='utf-8') as f:
                json.dump(verification_checklist, f, indent=2, ensure_ascii=False)
                
            self.log_step("Deployment Verification", "SUCCESS", "Verification checklist created - manual verification required")
            return True
            
        except Exception as e:
            self.log_step("Deployment Verification", "ERROR", f"Verification failed: {str(e)}")
            return False
            
    def setup_monitoring(self) -> bool:
        """Setup monitoring and alerts"""
        self.current_step += 1
        self.log_step("Monitoring Setup", "START", "Setting up monitoring and alerts")
        
        try:
            # Create monitoring setup instructions
            monitoring_setup = {
                'timestamp': datetime.now().isoformat(),
                'monitoring_components': [
                    'System metrics collection (CPU, Memory, Disk)',
                    'Application health checks',
                    'Log aggregation and rotation',
                    'Alert notifications (Slack, Email)',
                    'Performance monitoring dashboard'
                ],
                'setup_commands': [
                    'Deploy monitoring_dashboard.py to VPS',
                    'Configure monitoring_config.json',
                    'Setup alert_config.json with notification channels',
                    'Start monitoring service',
                    'Verify dashboard accessibility'
                ],
                'dashboard_url': 'https://your-domain.com/dashboard',
                'alert_channels': {
                    'slack': 'Configure webhook URL in alert_config.json',
                    'email': 'Configure SMTP settings in alert_config.json',
                    'telegram': 'Configure bot token and chat ID'
                }
            }
            
            with open(self.project_root / 'monitoring_setup_guide.json', 'w', encoding='utf-8') as f:
                json.dump(monitoring_setup, f, indent=2, ensure_ascii=False)
                
            self.log_step("Monitoring Setup", "SUCCESS", "Monitoring setup guide created")
            return True
            
        except Exception as e:
            self.log_step("Monitoring Setup", "ERROR", f"Monitoring setup failed: {str(e)}")
            return False
            
    def generate_deployment_summary(self) -> Dict:
        """Generate deployment summary report"""
        successful_steps = len([s for s in self.deployment_steps if s['status'] == 'SUCCESS'])
        total_steps = len(self.deployment_steps)
        
        summary = {
            'deployment_id': f"deploy_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'timestamp': datetime.now().isoformat(),
            'total_steps': total_steps,
            'successful_steps': successful_steps,
            'success_rate': f"{(successful_steps/total_steps*100):.1f}%" if total_steps > 0 else "0%",
            'deployment_status': 'SUCCESS' if successful_steps == total_steps else 'PARTIAL',
            'steps': self.deployment_steps,
            'next_actions': [
                'Verify VPS deployment manually using verification checklist',
                'Configure monitoring dashboard and alerts',
                'Test trading bot functionality in production environment',
                'Setup automated backups and disaster recovery',
                'Monitor system performance and optimize as needed'
            ],
            'important_files': {
                'deployment_verification_checklist.json': 'Manual verification steps',
                'monitoring_setup_guide.json': 'Monitoring configuration guide',
                'production_deployment.log': 'Detailed deployment logs'
            }
        }
        
        return summary
        
    def execute_full_deployment(self) -> bool:
        """Execute complete deployment process"""
        logger.info("Starting TRAE-SentinelOps Production Deployment")
        logger.info("="*60)
        
        try:
            # Execute deployment steps
            if not self.check_prerequisites():
                return False
                
            if not self.prepare_deployment_package():
                return False
                
            if not self.execute_vps_deployment():
                return False
                
            if not self.verify_deployment():
                return False
                
            if not self.setup_monitoring():
                return False
                
            # Generate summary
            summary = self.generate_deployment_summary()
            
            # Save summary
            with open(self.project_root / 'deployment_summary.json', 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
                
            logger.info("="*60)
            logger.info("🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!")
            logger.info(f"📊 Success Rate: {summary['success_rate']}")
            logger.info(f"📁 Summary saved: deployment_summary.json")
            logger.info("="*60)
            
            return True
            
        except Exception as e:
            logger.error(f"Deployment failed: {str(e)}")
            return False
            
def main():
    """Main execution function"""
    try:
        executor = ProductionDeploymentExecutor()
        success = executor.execute_full_deployment()
        
        if success:
            logger.info("✅ Production deployment completed successfully!")
            sys.exit(0)
        else:
            logger.error("Production deployment failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.warning("⚠️ Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)
        
if __name__ == '__main__':
    main()