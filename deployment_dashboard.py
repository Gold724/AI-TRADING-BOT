#!/usr/bin/env python3
"""
AI Trading Sentinel - Deployment Status Dashboard
TRAE-SentinelOps Status Monitor

Real-time deployment readiness dashboard and system status monitor.
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

class DeploymentDashboard:
    def __init__(self):
        self.project_root = Path.cwd()
        self.env_file = self.project_root / '.env'
        self.status = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'UNKNOWN',
            'readiness_score': 0,
            'components': {},
            'next_steps': [],
            'warnings': [],
            'errors': []
        }
    
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self):
        """Print dashboard header"""
        print("\n" + "="*80)
        print("🚀 AI Trading Sentinel - Deployment Status Dashboard")
        print("   TRAE-SentinelOps Real-Time Monitor")
        print("="*80)
        print(f"📅 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
    
    def check_environment_variables(self) -> Tuple[int, List[str]]:
        """Check environment variables status"""
        required_vars = [
            'CONTABO_VPS_IP', 'CONTABO_VPS_USER', 'CONTABO_SSH_KEY_PATH',
            'GITHUB_TOKEN', 'GITHUB_REPO_URL',
            'BULENOX_USERNAME', 'BULENOX_PASSWORD',
            'FLASK_SECRET_KEY', 'JWT_SECRET_KEY'
        ]
        
        missing_vars = []
        configured_vars = 0
        
        if not self.env_file.exists():
            return 0, required_vars
        
        env_vars = {}
        try:
            with open(self.env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key] = value
        except Exception as e:
            self.status['errors'].append(f"Error reading .env file: {e}")
            return 0, required_vars
        
        for var in required_vars:
            value = env_vars.get(var, '')
            if not value or value.startswith('YOUR_') or value.startswith('your_'):
                missing_vars.append(var)
            else:
                configured_vars += 1
        
        return configured_vars, missing_vars
    
    def check_ssh_key(self) -> bool:
        """Check if SSH key exists"""
        try:
            with open(self.env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('CONTABO_SSH_KEY_PATH='):
                        ssh_path = line.split('=', 1)[1].strip()
                        return Path(ssh_path).exists()
        except:
            pass
        return False
    
    def check_dependencies(self) -> Tuple[int, List[str]]:
        """Check Python dependencies"""
        required_packages = [
            'flask', 'requests', 'selenium', 'playwright', 
            'schedule', 'python-telegram-bot', 'curlconverter'
        ]
        
        installed = []
        missing = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                installed.append(package)
            except ImportError:
                missing.append(package)
        
        return len(installed), missing
    
    def check_files_structure(self) -> Tuple[int, List[str]]:
        """Check critical files exist"""
        critical_files = [
            'app.py', 'bulenox_sentinel.py', 'deploy_production.py',
            'requirements.txt', 'package.json', '.env.template'
        ]
        
        existing = []
        missing = []
        
        for file_name in critical_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                existing.append(file_name)
            else:
                missing.append(file_name)
        
        return len(existing), missing
    
    def test_github_connection(self) -> bool:
        """Test GitHub API connection"""
        try:
            with open(self.env_file, 'r', encoding='utf-8') as f:
                github_token = None
                for line in f:
                    if line.startswith('GITHUB_TOKEN='):
                        github_token = line.split('=', 1)[1].strip()
                        break
            
            if not github_token or github_token.startswith('ghp_YOUR'):
                return False
            
            import requests
            headers = {'Authorization': f'token {github_token}'}
            response = requests.get('https://api.github.com/user', headers=headers, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            self.status['warnings'].append(f"GitHub connection test failed: {e}")
            return False
    
    def run_system_checks(self):
        """Run all system checks"""
        total_score = 0
        max_score = 100
        
        # Environment Variables (40 points)
        env_configured, env_missing = self.check_environment_variables()
        env_total = 9  # Total required vars
        env_score = (env_configured / env_total) * 40 if env_total > 0 else 0
        total_score += env_score
        
        self.status['components']['environment'] = {
            'status': 'READY' if env_configured == env_total else 'PARTIAL' if env_configured > 0 else 'NOT_READY',
            'score': env_score,
            'configured': env_configured,
            'total': env_total,
            'missing': env_missing
        }
        
        # SSH Key (15 points)
        ssh_exists = self.check_ssh_key()
        ssh_score = 15 if ssh_exists else 0
        total_score += ssh_score
        
        self.status['components']['ssh_key'] = {
            'status': 'READY' if ssh_exists else 'NOT_READY',
            'score': ssh_score,
            'exists': ssh_exists
        }
        
        # Dependencies (20 points)
        deps_installed, deps_missing = self.check_dependencies()
        deps_total = deps_installed + len(deps_missing)
        deps_score = (deps_installed / deps_total) * 20 if deps_total > 0 else 0
        total_score += deps_score
        
        self.status['components']['dependencies'] = {
            'status': 'READY' if len(deps_missing) == 0 else 'PARTIAL' if deps_installed > 0 else 'NOT_READY',
            'score': deps_score,
            'installed': deps_installed,
            'total': deps_total,
            'missing': deps_missing
        }
        
        # File Structure (15 points)
        files_exist, files_missing = self.check_files_structure()
        files_total = files_exist + len(files_missing)
        files_score = (files_exist / files_total) * 15 if files_total > 0 else 0
        total_score += files_score
        
        self.status['components']['files'] = {
            'status': 'READY' if len(files_missing) == 0 else 'PARTIAL' if files_exist > 0 else 'NOT_READY',
            'score': files_score,
            'existing': files_exist,
            'total': files_total,
            'missing': files_missing
        }
        
        # GitHub Connection (10 points)
        github_ok = self.test_github_connection()
        github_score = 10 if github_ok else 0
        total_score += github_score
        
        self.status['components']['github'] = {
            'status': 'READY' if github_ok else 'NOT_READY',
            'score': github_score,
            'connected': github_ok
        }
        
        # Overall Status
        self.status['readiness_score'] = round(total_score, 1)
        
        if total_score >= 90:
            self.status['overall_status'] = 'READY'
        elif total_score >= 60:
            self.status['overall_status'] = 'PARTIAL'
        else:
            self.status['overall_status'] = 'NOT_READY'
    
    def generate_next_steps(self):
        """Generate next steps based on current status"""
        steps = []
        
        # Environment variables
        env_component = self.status['components'].get('environment', {})
        if env_component.get('status') != 'READY':
            missing = env_component.get('missing', [])
            if missing:
                steps.append(f"🔧 Configure missing environment variables: {', '.join(missing[:3])}{'...' if len(missing) > 3 else ''}")
                steps.append("   Run: python configure_deployment.py --interactive")
        
        # SSH Key
        ssh_component = self.status['components'].get('ssh_key', {})
        if not ssh_component.get('exists', False):
            steps.append("🔑 Generate SSH key for VPS access")
            steps.append("   Run: ssh-keygen -t rsa -b 4096 -f ~/.ssh/contabo_key")
        
        # Dependencies
        deps_component = self.status['components'].get('dependencies', {})
        if deps_component.get('status') != 'READY':
            missing = deps_component.get('missing', [])
            if missing:
                steps.append(f"📦 Install missing dependencies: {', '.join(missing[:3])}{'...' if len(missing) > 3 else ''}")
                steps.append("   Run: pip install -r requirements.txt")
        
        # GitHub
        github_component = self.status['components'].get('github', {})
        if not github_component.get('connected', False):
            steps.append("🐙 Fix GitHub token or connection")
            steps.append("   Check token at: https://github.com/settings/tokens")
        
        # Ready to deploy
        if self.status['overall_status'] == 'READY':
            steps.append("🚀 System is ready! Run deployment test:")
            steps.append("   python deploy_production.py --test-only")
            steps.append("🎯 If tests pass, deploy to production:")
            steps.append("   python deploy_production.py --orchestrate")
        
        self.status['next_steps'] = steps
    
    def print_status_bar(self, label: str, current: int, total: int, width: int = 30):
        """Print a progress bar"""
        if total == 0:
            percentage = 0
        else:
            percentage = (current / total) * 100
        
        filled = int((current / total) * width) if total > 0 else 0
        bar = '█' * filled + '░' * (width - filled)
        
        status_icon = "✅" if current == total else "⚠️" if current > 0 else "❌"
        print(f"{status_icon} {label:20} [{bar}] {current}/{total} ({percentage:5.1f}%)")
    
    def print_dashboard(self):
        """Print the complete dashboard"""
        self.clear_screen()
        self.print_header()
        
        # Overall Status
        status_color = {
            'READY': '🟢',
            'PARTIAL': '🟡', 
            'NOT_READY': '🔴',
            'UNKNOWN': '⚪'
        }
        
        print(f"\n📊 OVERALL STATUS: {status_color.get(self.status['overall_status'], '⚪')} {self.status['overall_status']}")
        print(f"📈 Readiness Score: {self.status['readiness_score']}/100")
        
        # Component Status
        print("\n" + "─"*80)
        print("📋 COMPONENT STATUS")
        print("─"*80)
        
        # Environment Variables
        env = self.status['components'].get('environment', {})
        self.print_status_bar("Environment Vars", env.get('configured', 0), env.get('total', 9))
        
        # SSH Key
        ssh = self.status['components'].get('ssh_key', {})
        self.print_status_bar("SSH Key", 1 if ssh.get('exists') else 0, 1)
        
        # Dependencies
        deps = self.status['components'].get('dependencies', {})
        self.print_status_bar("Dependencies", deps.get('installed', 0), deps.get('total', 7))
        
        # Files
        files = self.status['components'].get('files', {})
        self.print_status_bar("Critical Files", files.get('existing', 0), files.get('total', 6))
        
        # GitHub
        github = self.status['components'].get('github', {})
        self.print_status_bar("GitHub Connection", 1 if github.get('connected') else 0, 1)
        
        # Next Steps
        if self.status['next_steps']:
            print("\n" + "─"*80)
            print("🎯 NEXT STEPS")
            print("─"*80)
            for step in self.status['next_steps'][:8]:  # Show max 8 steps
                print(step)
        
        # Warnings and Errors
        if self.status['warnings']:
            print("\n" + "─"*80)
            print("⚠️  WARNINGS")
            print("─"*80)
            for warning in self.status['warnings'][:3]:
                print(f"⚠️  {warning}")
        
        if self.status['errors']:
            print("\n" + "─"*80)
            print("❌ ERRORS")
            print("─"*80)
            for error in self.status['errors'][:3]:
                print(f"❌ {error}")
        
        # Quick Actions
        print("\n" + "─"*80)
        print("⚡ QUICK ACTIONS")
        print("─"*80)
        print("🔧 Configure:     python configure_deployment.py --interactive")
        print("🧪 Validate:      python validate_environment.py")
        print("🧪 Test Deploy:   python deploy_production.py --test-only")
        print("🚀 Deploy:        python deploy_production.py --orchestrate")
        print("📊 Refresh:       python deployment_dashboard.py --watch")
        
        print("\n" + "="*80)
    
    def save_status_report(self):
        """Save status to JSON file"""
        report_file = self.project_root / 'deployment_status_report.json'
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.status, f, indent=2, default=str)
            print(f"\n💾 Status report saved to: {report_file}")
        except Exception as e:
            print(f"\n❌ Failed to save status report: {e}")
    
    def run_once(self):
        """Run dashboard once"""
        self.run_system_checks()
        self.generate_next_steps()
        self.print_dashboard()
        self.save_status_report()
    
    def run_watch_mode(self, interval: int = 30):
        """Run dashboard in watch mode"""
        try:
            while True:
                self.run_once()
                print(f"\n🔄 Refreshing in {interval} seconds... (Press Ctrl+C to exit)")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\n👋 Dashboard stopped by user.")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Trading Sentinel Deployment Dashboard')
    parser.add_argument('--watch', '-w', action='store_true',
                       help='Run in watch mode (auto-refresh)')
    parser.add_argument('--interval', '-i', type=int, default=30,
                       help='Refresh interval in seconds (default: 30)')
    parser.add_argument('--json', '-j', action='store_true',
                       help='Output status as JSON only')
    
    args = parser.parse_args()
    
    dashboard = DeploymentDashboard()
    
    if args.json:
        dashboard.run_system_checks()
        dashboard.generate_next_steps()
        print(json.dumps(dashboard.status, indent=2, default=str))
    elif args.watch:
        dashboard.run_watch_mode(args.interval)
    else:
        dashboard.run_once()

if __name__ == '__main__':
    main()