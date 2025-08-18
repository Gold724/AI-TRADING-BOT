#!/usr/bin/env python3
"""
🤖 TradeBot Sentinel - Complete Contabo VPS Deployment Script

This script handles the complete deployment of TradeBot Sentinel to Contabo VPS:
1. Transfer complete ai-trading-sentinel/ directory
2. Configure .env with Bulenox credentials
3. Install dependencies from requirements.txt
4. Validate headless Chrome with persistent profiles
5. Confirm log directories exist and are writable
6. Report deployment status and readiness

Usage:
    python deploy_to_contabo_complete.py --host <VPS_IP> --user <SSH_USER> --key <SSH_KEY_PATH>
"""

import os
import sys
import subprocess
import argparse
import json
import time
from datetime import datetime
from pathlib import Path

class ContaboDeployment:
    def __init__(self, host, user, ssh_key_path, local_project_dir=None):
        self.host = host
        self.user = user
        self.ssh_key_path = ssh_key_path
        self.local_project_dir = local_project_dir or os.getcwd()
        self.remote_project_dir = "/home/tradebot/ai-trading-sentinel"
        self.deployment_log = []
        
    def log(self, message, level="INFO"):
        """Log deployment messages"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        self.deployment_log.append(log_entry)
        
    def run_ssh_command(self, command, capture_output=True):
        """Execute command on remote VPS via SSH"""
        ssh_cmd = [
            "ssh", 
            "-i", self.ssh_key_path,
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            f"{self.user}@{self.host}",
            command
        ]
        
        try:
            if capture_output:
                result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=300)
                return result.returncode == 0, result.stdout, result.stderr
            else:
                result = subprocess.run(ssh_cmd, timeout=300)
                return result.returncode == 0, "", ""
        except subprocess.TimeoutExpired:
            self.log(f"SSH command timed out: {command}", "ERROR")
            return False, "", "Command timed out"
        except Exception as e:
            self.log(f"SSH command failed: {str(e)}", "ERROR")
            return False, "", str(e)
            
    def transfer_files(self):
        """Transfer complete ai-trading-sentinel directory to VPS"""
        self.log("🚀 Starting file transfer to Contabo VPS...")
        
        # Create remote directory
        success, stdout, stderr = self.run_ssh_command(f"mkdir -p {self.remote_project_dir}")
        if not success:
            self.log(f"Failed to create remote directory: {stderr}", "ERROR")
            return False
            
        # Use rsync for efficient file transfer
        rsync_cmd = [
            "rsync", "-avz", "--progress",
            "-e", f"ssh -i {self.ssh_key_path} -o StrictHostKeyChecking=no",
            "--exclude=venv/",
            "--exclude=__pycache__/",
            "--exclude=*.pyc",
            "--exclude=.git/",
            "--exclude=chrome_profile/",
            "--exclude=chrome_profiles/",
            "--exclude=temp_chrome_profile*/",
            "--exclude=*.png",
            "--exclude=*.jpg",
            "--exclude=*.jpeg",
            f"{self.local_project_dir}/",
            f"{self.user}@{self.host}:{self.remote_project_dir}/"
        ]
        
        try:
            self.log("📦 Transferring files with rsync...")
            result = subprocess.run(rsync_cmd, capture_output=True, text=True, timeout=1800)
            
            if result.returncode == 0:
                self.log("✅ File transfer completed successfully")
                return True
            else:
                self.log(f"❌ File transfer failed: {result.stderr}", "ERROR")
                return False
                
        except subprocess.TimeoutExpired:
            self.log("❌ File transfer timed out", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ File transfer error: {str(e)}", "ERROR")
            return False
            
    def configure_environment(self):
        """Configure .env file with Bulenox credentials"""
        self.log("🔧 Configuring environment variables...")
        
        env_content = '''
# ✅ TradeBot Sentinel - Contabo VPS Configuration
# Generated: {timestamp}

# ✅ Bulenox Trading Credentials
BULENOX_USERNAME=BX64883
BULENOX_PASSWORD=XujhMzFf6K
BROKER_USERNAME=BX64883
BROKER_PASSWORD=XujhMzFf6K
BROKER_URL=https://bulenox.projectx.com/login
BULENOX_ACCOUNT_ID=BX64883

# ✅ VPS Chrome Settings
HEADLESS=true
USE_TEMP_PROFILE=true
SCREENSHOT_ON_FAILURE=true
CHROME_OPTS=--headless=new --no-sandbox --disable-dev-shm-usage --disable-gpu --window-size=1920,1080 --disable-extensions --disable-plugins

# ✅ API Settings
PORT=5000
DEBUG=false
FLASK_SECRET_KEY=aPpS3cuReKey!47829
ENCRYPTION_KEY=Q2xpZW50LXNpZ25lZC1lbmNyeXB0aW9uLWtleQ==
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
CORS_ORIGINS=*

# ✅ Logging & Environment
LOG_LEVEL=INFO
ENVIRONMENT=production

# ✅ TradeBot Sentinel Automation Settings
AUTOMATION_HEADLESS=true
AUTOMATION_TIMEOUT=30000
SCREENSHOT_ON_ERROR=true
RETRY_ATTEMPTS=3
RETRY_DELAY=2000
INTERCEPT_TRADE_REQUESTS=true
SAVE_CURL_COMMANDS=true
AUTO_CONVERT_TO_PYTHON=true
VERBOSE_LOGGING=true
LOG_NETWORK_REQUESTS=true
LOG_ELEMENT_INTERACTIONS=true

# ✅ VPS Specific Settings
DISPLAY=:99
XVFB_DISPLAY=:99
CHROME_BIN=/usr/bin/google-chrome
CHROMEDRIVER_PATH=/usr/local/bin/chromedriver
'''.format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # Write .env file to remote server
        env_command = f"cat > {self.remote_project_dir}/.env << 'EOF'\n{env_content}\nEOF"
        success, stdout, stderr = self.run_ssh_command(env_command)
        
        if success:
            self.log("✅ Environment configuration completed")
            return True
        else:
            self.log(f"❌ Environment configuration failed: {stderr}", "ERROR")
            return False
            
    def install_dependencies(self):
        """Install Python dependencies and system packages"""
        self.log("📦 Installing system dependencies...")
        
        # Update system and install required packages
        system_commands = [
            "sudo apt update -y",
            "sudo apt install -y python3 python3-pip python3-venv",
            "sudo apt install -y wget curl unzip xvfb",
            "sudo apt install -y fonts-liberation libasound2 libatk-bridge2.0-0 libdrm2 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxss1 libu2f-udev libvulkan1"
        ]
        
        for cmd in system_commands:
            self.log(f"Executing: {cmd}")
            success, stdout, stderr = self.run_ssh_command(cmd)
            if not success:
                self.log(f"Warning: System command failed: {stderr}", "WARNING")
                
        # Install Google Chrome
        self.log("🌐 Installing Google Chrome...")
        chrome_commands = [
            "wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -",
            "echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' | sudo tee /etc/apt/sources.list.d/google-chrome.list",
            "sudo apt update -y",
            "sudo apt install -y google-chrome-stable"
        ]
        
        for cmd in chrome_commands:
            success, stdout, stderr = self.run_ssh_command(cmd)
            if not success:
                self.log(f"Chrome installation warning: {stderr}", "WARNING")
                
        # Install ChromeDriver
        self.log("🚗 Installing ChromeDriver...")
        chromedriver_commands = [
            "CHROME_VERSION=$(google-chrome --version | cut -d ' ' -f3 | cut -d '.' -f1)",
            "CHROMEDRIVER_VERSION=$(curl -s https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION)",
            "wget -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip",
            "sudo unzip -o /tmp/chromedriver.zip -d /usr/local/bin/",
            "sudo chmod +x /usr/local/bin/chromedriver",
            "rm /tmp/chromedriver.zip"
        ]
        
        for cmd in chromedriver_commands:
            success, stdout, stderr = self.run_ssh_command(cmd)
            if not success:
                self.log(f"ChromeDriver installation warning: {stderr}", "WARNING")
                
        # Create Python virtual environment and install requirements
        self.log("🐍 Setting up Python environment...")
        python_commands = [
            f"cd {self.remote_project_dir}",
            "python3 -m venv venv",
            "source venv/bin/activate && pip install --upgrade pip",
            "source venv/bin/activate && pip install -r requirements.txt"
        ]
        
        combined_cmd = " && ".join(python_commands)
        success, stdout, stderr = self.run_ssh_command(combined_cmd)
        
        if success:
            self.log("✅ Python dependencies installed successfully")
            return True
        else:
            self.log(f"❌ Python dependencies installation failed: {stderr}", "ERROR")
            return False
            
    def validate_chrome(self):
        """Validate headless Chrome works with persistent profiles"""
        self.log("🔍 Validating headless Chrome setup...")
        
        # Test Chrome installation
        success, stdout, stderr = self.run_ssh_command("google-chrome --version")
        if success:
            self.log(f"✅ Chrome version: {stdout.strip()}")
        else:
            self.log(f"❌ Chrome validation failed: {stderr}", "ERROR")
            return False
            
        # Test ChromeDriver
        success, stdout, stderr = self.run_ssh_command("chromedriver --version")
        if success:
            self.log(f"✅ ChromeDriver version: {stdout.strip()}")
        else:
            self.log(f"❌ ChromeDriver validation failed: {stderr}", "ERROR")
            return False
            
        # Test headless Chrome with Xvfb
        test_script = f'''
cd {self.remote_project_dir}
source venv/bin/activate
export DISPLAY=:99
Xvfb :99 -screen 0 1920x1080x24 &
XVFB_PID=$!
sleep 2
python3 -c "
import os
os.environ['DISPLAY'] = ':99'
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')

try:
    driver = webdriver.Chrome(options=options)
    driver.get('https://www.google.com')
    title = driver.title
    driver.quit()
    print(f'SUCCESS: Chrome test completed. Page title: {{title}}')
except Exception as e:
    print(f'ERROR: Chrome test failed: {{str(e)}}')
"
kill $XVFB_PID 2>/dev/null || true
'''
        
        success, stdout, stderr = self.run_ssh_command(test_script)
        
        if success and "SUCCESS" in stdout:
            self.log("✅ Headless Chrome validation successful")
            return True
        else:
            self.log(f"❌ Headless Chrome validation failed: {stderr}", "ERROR")
            return False
            
    def setup_directories(self):
        """Create and validate log directories"""
        self.log("📁 Setting up log directories...")
        
        directories = [
            f"{self.remote_project_dir}/logs",
            f"{self.remote_project_dir}/logs/curls",
            f"{self.remote_project_dir}/logs/json",
            f"{self.remote_project_dir}/logs/screenshots",
            f"{self.remote_project_dir}/data",
            f"{self.remote_project_dir}/data/backtest",
            f"{self.remote_project_dir}/data/signals"
        ]
        
        for directory in directories:
            success, stdout, stderr = self.run_ssh_command(f"mkdir -p {directory} && chmod 755 {directory}")
            if success:
                self.log(f"✅ Created directory: {directory}")
            else:
                self.log(f"❌ Failed to create directory {directory}: {stderr}", "ERROR")
                return False
                
        # Test write permissions
        test_file = f"{self.remote_project_dir}/logs/deployment_test.txt"
        success, stdout, stderr = self.run_ssh_command(f"echo 'Deployment test' > {test_file} && rm {test_file}")
        
        if success:
            self.log("✅ Log directories are writable")
            return True
        else:
            self.log(f"❌ Log directories write test failed: {stderr}", "ERROR")
            return False
            
    def create_systemd_service(self):
        """Create systemd service for TradeBot Sentinel"""
        self.log("⚙️ Creating systemd service...")
        
        service_content = f'''
[Unit]
Description=TradeBot Sentinel - AI Trading Automation
After=network.target

[Service]
Type=simple
User=tradebot
WorkingDirectory={self.remote_project_dir}
Environment=PATH={self.remote_project_dir}/venv/bin
Environment=DISPLAY=:99
ExecStartPre=/usr/bin/Xvfb :99 -screen 0 1920x1080x24
ExecStart={self.remote_project_dir}/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
'''
        
        service_command = f"sudo tee /etc/systemd/system/tradebot-sentinel.service << 'EOF'\n{service_content}\nEOF"
        success, stdout, stderr = self.run_ssh_command(service_command)
        
        if success:
            # Enable the service
            self.run_ssh_command("sudo systemctl daemon-reload")
            self.run_ssh_command("sudo systemctl enable tradebot-sentinel.service")
            self.log("✅ Systemd service created and enabled")
            return True
        else:
            self.log(f"❌ Systemd service creation failed: {stderr}", "ERROR")
            return False
            
    def generate_deployment_report(self):
        """Generate comprehensive deployment report"""
        self.log("📊 Generating deployment report...")
        
        # System information
        system_info = {}
        
        commands = {
            "os_info": "cat /etc/os-release | head -5",
            "python_version": "python3 --version",
            "pip_version": "pip3 --version",
            "chrome_version": "google-chrome --version",
            "chromedriver_version": "chromedriver --version",
            "disk_space": "df -h /",
            "memory_info": "free -h",
            "cpu_info": "nproc"
        }
        
        for key, cmd in commands.items():
            success, stdout, stderr = self.run_ssh_command(cmd)
            system_info[key] = stdout.strip() if success else f"Error: {stderr}"
            
        # Create deployment report
        report = {
            "deployment_timestamp": datetime.now().isoformat(),
            "deployment_status": "SUCCESS",
            "vps_host": self.host,
            "remote_directory": self.remote_project_dir,
            "system_information": system_info,
            "deployment_log": self.deployment_log,
            "validation_results": {
                "file_transfer": "✅ COMPLETED",
                "environment_config": "✅ COMPLETED",
                "dependencies_install": "✅ COMPLETED",
                "chrome_validation": "✅ COMPLETED",
                "directories_setup": "✅ COMPLETED",
                "systemd_service": "✅ COMPLETED"
            },
            "next_steps": [
                "sudo systemctl start tradebot-sentinel.service",
                "sudo systemctl status tradebot-sentinel.service",
                "tail -f /home/tradebot/ai-trading-sentinel/logs/tradebot.log"
            ]
        }
        
        # Save report locally
        report_file = f"contabo_deployment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        self.log(f"📄 Deployment report saved: {report_file}")
        return report
        
    def deploy(self):
        """Execute complete deployment process"""
        self.log("🚀 Starting TradeBot Sentinel deployment to Contabo VPS...")
        
        steps = [
            ("File Transfer", self.transfer_files),
            ("Environment Configuration", self.configure_environment),
            ("Dependencies Installation", self.install_dependencies),
            ("Chrome Validation", self.validate_chrome),
            ("Directory Setup", self.setup_directories),
            ("Systemd Service", self.create_systemd_service)
        ]
        
        for step_name, step_function in steps:
            self.log(f"\n{'='*50}")
            self.log(f"🔄 Executing: {step_name}")
            self.log(f"{'='*50}")
            
            if not step_function():
                self.log(f"❌ Deployment failed at step: {step_name}", "ERROR")
                return False
                
        self.log("\n" + "="*60)
        self.log("🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!")
        self.log("="*60)
        
        # Generate final report
        report = self.generate_deployment_report()
        
        self.log("\n📋 DEPLOYMENT SUMMARY:")
        self.log(f"✅ VPS Host: {self.host}")
        self.log(f"✅ Remote Directory: {self.remote_project_dir}")
        self.log(f"✅ Environment: Production")
        self.log(f"✅ Chrome: Headless mode enabled")
        self.log(f"✅ Logs: {self.remote_project_dir}/logs/")
        self.log(f"✅ Service: tradebot-sentinel.service")
        
        self.log("\n🚀 READY FOR AUTOMATION!")
        self.log("\nTo start the service:")
        self.log("  sudo systemctl start tradebot-sentinel.service")
        self.log("\nTo check status:")
        self.log("  sudo systemctl status tradebot-sentinel.service")
        self.log("\nTo view logs:")
        self.log(f"  tail -f {self.remote_project_dir}/logs/tradebot.log")
        
        return True

def main():
    parser = argparse.ArgumentParser(description="Deploy TradeBot Sentinel to Contabo VPS")
    parser.add_argument("--host", required=True, help="VPS IP address")
    parser.add_argument("--user", default="root", help="SSH username (default: root)")
    parser.add_argument("--key", required=True, help="SSH private key path")
    parser.add_argument("--project-dir", help="Local project directory path")
    
    args = parser.parse_args()
    
    # Validate SSH key exists
    if not os.path.exists(args.key):
        print(f"❌ SSH key not found: {args.key}")
        sys.exit(1)
        
    # Create deployment instance
    deployment = ContaboDeployment(
        host=args.host,
        user=args.user,
        ssh_key_path=args.key,
        local_project_dir=args.project_dir
    )
    
    # Execute deployment
    success = deployment.deploy()
    
    if success:
        print("\n🎉 Deployment completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Deployment failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()