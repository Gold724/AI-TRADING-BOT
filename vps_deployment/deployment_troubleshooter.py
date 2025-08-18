#!/usr/bin/env python3
"""
AI Trading Sentinel - VPS Deployment Troubleshooter
Automatically diagnoses and fixes common deployment issues
"""

import os
import sys
import subprocess
import json
from pathlib import Path
import argparse
from datetime import datetime

class DeploymentTroubleshooter:
    def __init__(self, vps_host=None, vps_user="root", ssh_port=22, ssh_key=None):
        self.vps_host = vps_host
        self.vps_user = vps_user
        self.ssh_port = ssh_port
        self.ssh_key = ssh_key
        self.remote_dir = "/root/AI-TRADING-BOT"
        self.issues_found = []
        self.fixes_applied = []
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp and level"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        symbols = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌", "FIX": "🔧"}
        symbol = symbols.get(level, "ℹ️")
        print(f"[{timestamp}] {symbol} {message}")
        
    def run_ssh_command(self, command, capture_output=True):
        """Execute SSH command on remote VPS"""
        ssh_cmd = ["ssh"]
        
        if self.ssh_key:
            ssh_cmd.extend(["-i", self.ssh_key])
        if self.ssh_port != 22:
            ssh_cmd.extend(["-p", str(self.ssh_port)])
            
        ssh_cmd.extend([f"{self.vps_user}@{self.vps_host}", command])
        
        try:
            if capture_output:
                result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=30)
                return result.returncode == 0, result.stdout, result.stderr
            else:
                result = subprocess.run(ssh_cmd, timeout=30)
                return result.returncode == 0, "", ""
        except subprocess.TimeoutExpired:
            return False, "", "SSH command timed out"
        except Exception as e:
            return False, "", str(e)
            
    def check_ssh_connectivity(self):
        """Test SSH connection to VPS"""
        self.log("Testing SSH connectivity...")
        
        success, stdout, stderr = self.run_ssh_command("echo 'SSH test successful'")
        
        if success:
            self.log("SSH connection successful", "SUCCESS")
            return True
        else:
            self.log(f"SSH connection failed: {stderr}", "ERROR")
            self.issues_found.append("SSH connectivity issue")
            self.suggest_ssh_fixes()
            return False
            
    def suggest_ssh_fixes(self):
        """Suggest SSH troubleshooting steps"""
        self.log("SSH Troubleshooting suggestions:", "FIX")
        print("  1. Verify VPS IP address and port")
        print("  2. Check if SSH service is running on VPS")
        print("  3. Verify username (usually 'root' for VPS)")
        print("  4. Check firewall settings on VPS")
        print("  5. Try: ssh -v user@host for verbose output")
        
    def check_remote_directory(self):
        """Check if remote directory exists and has correct permissions"""
        self.log("Checking remote directory structure...")
        
        success, stdout, stderr = self.run_ssh_command(f"test -d {self.remote_dir}")
        
        if not success:
            self.log(f"Remote directory {self.remote_dir} does not exist", "ERROR")
            self.issues_found.append("Missing remote directory")
            self.fix_remote_directory()
        else:
            self.log(f"Remote directory {self.remote_dir} exists", "SUCCESS")
            
        # Check permissions
        success, stdout, stderr = self.run_ssh_command(f"ls -la {self.remote_dir}")
        if success:
            self.log("Directory contents:", "INFO")
            print(stdout)
        
    def fix_remote_directory(self):
        """Create remote directory with correct permissions"""
        self.log(f"Creating remote directory {self.remote_dir}...", "FIX")
        
        success, stdout, stderr = self.run_ssh_command(f"mkdir -p {self.remote_dir}")
        
        if success:
            self.log("Remote directory created successfully", "SUCCESS")
            self.fixes_applied.append("Created remote directory")
        else:
            self.log(f"Failed to create remote directory: {stderr}", "ERROR")
            
    def check_python_installation(self):
        """Verify Python installation and version"""
        self.log("Checking Python installation...")
        
        # Check Python 3
        success, stdout, stderr = self.run_ssh_command("python3 --version")
        
        if success:
            version = stdout.strip()
            self.log(f"Python found: {version}", "SUCCESS")
            
            # Check if version is 3.8+
            try:
                version_parts = version.split()[1].split('.')
                major, minor = int(version_parts[0]), int(version_parts[1])
                if major >= 3 and minor >= 8:
                    self.log("Python version is compatible", "SUCCESS")
                else:
                    self.log("Python version is too old (need 3.8+)", "WARNING")
                    self.issues_found.append("Old Python version")
            except:
                self.log("Could not parse Python version", "WARNING")
        else:
            self.log("Python 3 not found", "ERROR")
            self.issues_found.append("Python 3 not installed")
            self.suggest_python_installation()
            
    def suggest_python_installation(self):
        """Suggest Python installation steps"""
        self.log("Python installation suggestions:", "FIX")
        print("  Ubuntu/Debian: apt update && apt install python3 python3-pip")
        print("  CentOS/RHEL: yum install python3 python3-pip")
        print("  Or use: dnf install python3 python3-pip")
        
    def check_pip_packages(self):
        """Check if required pip packages are installed"""
        self.log("Checking pip packages...")
        
        required_packages = ['playwright', 'requests', 'python-dotenv']
        missing_packages = []
        
        for package in required_packages:
            success, stdout, stderr = self.run_ssh_command(f"python3 -c 'import {package}'")
            
            if success:
                self.log(f"Package {package} is installed", "SUCCESS")
            else:
                self.log(f"Package {package} is missing", "ERROR")
                missing_packages.append(package)
                
        if missing_packages:
            self.issues_found.append(f"Missing packages: {', '.join(missing_packages)}")
            self.fix_pip_packages(missing_packages)
            
    def fix_pip_packages(self, missing_packages):
        """Install missing pip packages"""
        self.log("Installing missing pip packages...", "FIX")
        
        # Try to install from requirements.txt first
        success, stdout, stderr = self.run_ssh_command(
            f"cd {self.remote_dir} && pip3 install -r requirements.txt"
        )
        
        if success:
            self.log("Packages installed from requirements.txt", "SUCCESS")
            self.fixes_applied.append("Installed pip packages")
        else:
            # Install individual packages
            for package in missing_packages:
                success, stdout, stderr = self.run_ssh_command(f"pip3 install {package}")
                if success:
                    self.log(f"Installed {package}", "SUCCESS")
                else:
                    self.log(f"Failed to install {package}: {stderr}", "ERROR")
                    
    def check_playwright_browsers(self):
        """Check if Playwright browsers are installed"""
        self.log("Checking Playwright browsers...")
        
        success, stdout, stderr = self.run_ssh_command(
            f"cd {self.remote_dir} && python3 -c 'from playwright.sync_api import sync_playwright; p = sync_playwright().start(); p.chromium.launch(); p.stop()'"
        )
        
        if success:
            self.log("Playwright browsers are installed", "SUCCESS")
        else:
            self.log("Playwright browsers not installed", "ERROR")
            self.issues_found.append("Missing Playwright browsers")
            self.fix_playwright_browsers()
            
    def fix_playwright_browsers(self):
        """Install Playwright browsers"""
        self.log("Installing Playwright browsers...", "FIX")
        
        success, stdout, stderr = self.run_ssh_command(
            f"cd {self.remote_dir} && python3 -m playwright install"
        )
        
        if success:
            self.log("Playwright browsers installed successfully", "SUCCESS")
            self.fixes_applied.append("Installed Playwright browsers")
        else:
            self.log(f"Failed to install Playwright browsers: {stderr}", "ERROR")
            
    def check_core_files(self):
        """Check if all core trading files are present"""
        self.log("Checking core trading files...")
        
        required_files = [
            'tradebot_sentinel_advanced_pro.py',
            'login_bulenox_playwright.py',
            'endpoint_validator.py',
            'requirements.txt',
            'vps_environment_check.py'
        ]
        
        missing_files = []
        
        for file in required_files:
            success, stdout, stderr = self.run_ssh_command(f"test -f {self.remote_dir}/{file}")
            
            if success:
                self.log(f"File {file} exists", "SUCCESS")
            else:
                self.log(f"File {file} is missing", "ERROR")
                missing_files.append(file)
                
        if missing_files:
            self.issues_found.append(f"Missing files: {', '.join(missing_files)}")
            self.suggest_file_copy(missing_files)
            
    def suggest_file_copy(self, missing_files):
        """Suggest how to copy missing files"""
        self.log("File copy suggestions:", "FIX")
        for file in missing_files:
            if file in ['tradebot_sentinel_advanced_pro.py', 'login_bulenox_playwright.py', 'endpoint_validator.py']:
                print(f"  scp trading_scripts/{file} {self.vps_user}@{self.vps_host}:{self.remote_dir}/")
            elif file in ['requirements.txt', 'vps_environment_check.py']:
                print(f"  scp utilities/{file} {self.vps_user}@{self.vps_host}:{self.remote_dir}/")
            else:
                print(f"  scp {file} {self.vps_user}@{self.vps_host}:{self.remote_dir}/")
                
    def check_file_permissions(self):
        """Check and fix file permissions"""
        self.log("Checking file permissions...")
        
        success, stdout, stderr = self.run_ssh_command(
            f"find {self.remote_dir} -name '*.py' -o -name '*.sh' | xargs ls -la"
        )
        
        if success:
            self.log("Current file permissions:", "INFO")
            print(stdout)
            
            # Fix permissions
            success, stdout, stderr = self.run_ssh_command(
                f"chmod +x {self.remote_dir}/*.py {self.remote_dir}/*.sh 2>/dev/null || true"
            )
            
            if success:
                self.log("File permissions updated", "SUCCESS")
                self.fixes_applied.append("Fixed file permissions")
            
    def check_environment_variables(self):
        """Check if environment variables are set"""
        self.log("Checking environment variables...")
        
        success, stdout, stderr = self.run_ssh_command(f"test -f {self.remote_dir}/.env")
        
        if success:
            self.log(".env file exists", "SUCCESS")
            
            # Check if it has required variables
            success, stdout, stderr = self.run_ssh_command(
                f"cd {self.remote_dir} && grep -E '^BULENOX_(USERNAME|PASSWORD)=' .env"
            )
            
            if success:
                lines = stdout.strip().split('\n')
                if len(lines) >= 2:
                    self.log("Required environment variables are set", "SUCCESS")
                else:
                    self.log("Some environment variables are missing", "WARNING")
                    self.suggest_env_setup()
            else:
                self.log("Environment variables not properly set", "WARNING")
                self.suggest_env_setup()
        else:
            self.log(".env file does not exist", "ERROR")
            self.issues_found.append("Missing .env file")
            self.suggest_env_setup()
            
    def suggest_env_setup(self):
        """Suggest environment variable setup"""
        self.log("Environment setup suggestions:", "FIX")
        print(f"  1. SSH to VPS: ssh {self.vps_user}@{self.vps_host}")
        print(f"  2. Navigate: cd {self.remote_dir}")
        print("  3. Create .env: echo 'BULENOX_USERNAME=your_username' > .env")
        print("  4. Add password: echo 'BULENOX_PASSWORD=your_password' >> .env")
        print("  5. Secure file: chmod 600 .env")
        
    def run_comprehensive_check(self):
        """Run all diagnostic checks"""
        self.log("Starting comprehensive deployment check...", "INFO")
        
        if not self.vps_host:
            self.log("VPS host not specified. Use --host parameter.", "ERROR")
            return False
            
        checks = [
            self.check_ssh_connectivity,
            self.check_remote_directory,
            self.check_python_installation,
            self.check_pip_packages,
            self.check_playwright_browsers,
            self.check_core_files,
            self.check_file_permissions,
            self.check_environment_variables
        ]
        
        for check in checks:
            try:
                check()
            except Exception as e:
                self.log(f"Check failed with error: {e}", "ERROR")
                
        self.generate_report()
        
    def generate_report(self):
        """Generate final diagnostic report"""
        self.log("\n" + "="*60, "INFO")
        self.log("DEPLOYMENT DIAGNOSTIC REPORT", "INFO")
        self.log("="*60, "INFO")
        
        if self.issues_found:
            self.log(f"Issues Found ({len(self.issues_found)}):", "ERROR")
            for i, issue in enumerate(self.issues_found, 1):
                print(f"  {i}. {issue}")
        else:
            self.log("No issues found!", "SUCCESS")
            
        if self.fixes_applied:
            self.log(f"\nFixes Applied ({len(self.fixes_applied)}):", "SUCCESS")
            for i, fix in enumerate(self.fixes_applied, 1):
                print(f"  {i}. {fix}")
                
        self.log("\nNext Steps:", "INFO")
        if self.issues_found:
            print("  1. Address the issues listed above")
            print("  2. Re-run this troubleshooter")
            print("  3. Test deployment manually")
        else:
            print("  1. Set up environment variables (.env file)")
            print("  2. Test trading script: python3 tradebot_sentinel_advanced_pro.py")
            print("  3. Monitor logs for any runtime issues")
            
        self.log("="*60, "INFO")

def main():
    parser = argparse.ArgumentParser(description='AI Trading Sentinel VPS Deployment Troubleshooter')
    parser.add_argument('--host', required=True, help='VPS IP address or hostname')
    parser.add_argument('--user', default='root', help='SSH username (default: root)')
    parser.add_argument('--port', type=int, default=22, help='SSH port (default: 22)')
    parser.add_argument('--key', help='SSH private key file path')
    parser.add_argument('--dir', default='/root/AI-TRADING-BOT', help='Remote directory path')
    
    args = parser.parse_args()
    
    troubleshooter = DeploymentTroubleshooter(
        vps_host=args.host,
        vps_user=args.user,
        ssh_port=args.port,
        ssh_key=args.key
    )
    
    troubleshooter.remote_dir = args.dir
    troubleshooter.run_comprehensive_check()

if __name__ == "__main__":
    main()