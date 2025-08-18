#!/usr/bin/env python3
"""
Bulenox Trading Bot - Remote Management Interface
TRAE-SentinelOps v2.0.0 - Termius-Optimized VPS Management

This script provides easy remote management commands for the Bulenox trading bot
running on Contabo VPS, optimized for Termius SSH client usage.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

class RemoteManager:
    """Remote management interface for Bulenox trading bot"""
    
    def __init__(self):
        self.service_name = 'bulenox-trader'
        self.project_path = '/opt/trading-bot'
        self.log_path = '/var/log'
        self.config_path = f'{self.project_path}/config'
        
        # Color codes for terminal output
        self.colors = {
            'red': '\033[91m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'purple': '\033[95m',
            'cyan': '\033[96m',
            'white': '\033[97m',
            'bold': '\033[1m',
            'end': '\033[0m'
        }
    
    def print_colored(self, text: str, color: str = 'white', bold: bool = False):
        """Print colored text to terminal"""
        color_code = self.colors.get(color, self.colors['white'])
        bold_code = self.colors['bold'] if bold else ''
        end_code = self.colors['end']
        print(f"{bold_code}{color_code}{text}{end_code}")
    
    def print_header(self, title: str):
        """Print formatted header"""
        print("\n" + "="*60)
        self.print_colored(f"🤖 {title}", 'cyan', bold=True)
        print("="*60)
    
    def run_command(self, command: str, capture_output: bool = True, timeout: int = 30) -> tuple:
        """Run shell command and return result"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=capture_output,
                text=True,
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except Exception as e:
            return -1, "", str(e)
    
    def get_service_status(self) -> Dict:
        """Get detailed service status"""
        self.print_header("Service Status")
        
        # Check if service exists
        returncode, stdout, stderr = self.run_command(f"systemctl list-unit-files | grep {self.service_name}")
        
        if returncode != 0:
            self.print_colored(f"❌ Service {self.service_name} not found", 'red')
            return {'status': 'not_found'}
        
        # Get service status
        returncode, stdout, stderr = self.run_command(f"systemctl is-active {self.service_name}")
        active_status = stdout.strip()
        
        # Get detailed status
        returncode, status_output, stderr = self.run_command(f"systemctl status {self.service_name} --no-pager")
        
        # Get service uptime
        returncode, uptime_output, stderr = self.run_command(
            f"systemctl show {self.service_name} --property=ActiveEnterTimestamp --value"
        )
        
        status_info = {
            'active': active_status == 'active',
            'status': active_status,
            'details': status_output,
            'uptime': uptime_output.strip()
        }
        
        # Display status
        status_color = 'green' if status_info['active'] else 'red'
        status_emoji = '✅' if status_info['active'] else '❌'
        
        self.print_colored(f"{status_emoji} Service Status: {active_status}", status_color, bold=True)
        
        if status_info['uptime']:
            self.print_colored(f"⏰ Started: {status_info['uptime']}", 'blue')
        
        print("\n📋 Detailed Status:")
        print(status_output)
        
        return status_info
    
    def view_logs(self, lines: int = 50, follow: bool = False, service_only: bool = True):
        """View service logs"""
        self.print_header(f"Service Logs (Last {lines} lines)")
        
        if follow:
            self.print_colored("📡 Following logs in real-time (Ctrl+C to stop)...", 'yellow')
            command = f"journalctl -u {self.service_name} -f"
        else:
            command = f"journalctl -u {self.service_name} -n {lines} --no-pager"
        
        if service_only:
            self.run_command(command, capture_output=False)
        else:
            # Also show system logs
            self.print_colored("\n📋 System Logs:", 'cyan')
            self.run_command(f"tail -n {lines//2} /var/log/syslog", capture_output=False)
    
    def check_system_resources(self):
        """Check system resource usage"""
        self.print_header("System Resources")
        
        # CPU and Memory
        self.print_colored("💻 CPU & Memory Usage:", 'cyan', bold=True)
        self.run_command("top -bn1 | head -5", capture_output=False)
        
        print("\n")
        self.print_colored("💾 Memory Details:", 'cyan', bold=True)
        self.run_command("free -h", capture_output=False)
        
        print("\n")
        self.print_colored("💿 Disk Usage:", 'cyan', bold=True)
        self.run_command("df -h", capture_output=False)
        
        print("\n")
        self.print_colored("🌐 Network Connections:", 'cyan', bold=True)
        self.run_command("ss -tuln | grep -E ':(5000|5001|80|443)'", capture_output=False)
        
        # Process information
        print("\n")
        self.print_colored("🔍 Trading Bot Processes:", 'cyan', bold=True)
        self.run_command("ps aux | grep -E '(python|bulenox|trading)' | grep -v grep", capture_output=False)
    
    def restart_service(self, force: bool = False):
        """Restart the trading bot service"""
        self.print_header("Service Restart")
        
        if not force:
            response = input("⚠️  Are you sure you want to restart the trading bot? (y/N): ")
            if response.lower() != 'y':
                self.print_colored("❌ Restart cancelled", 'yellow')
                return
        
        self.print_colored("🔄 Stopping service...", 'yellow')
        returncode, stdout, stderr = self.run_command(f"systemctl stop {self.service_name}")
        
        if returncode == 0:
            self.print_colored("✅ Service stopped", 'green')
        else:
            self.print_colored(f"❌ Error stopping service: {stderr}", 'red')
            return
        
        # Wait a moment
        time.sleep(2)
        
        self.print_colored("🚀 Starting service...", 'yellow')
        returncode, stdout, stderr = self.run_command(f"systemctl start {self.service_name}")
        
        if returncode == 0:
            self.print_colored("✅ Service started successfully", 'green')
            
            # Check status after restart
            time.sleep(3)
            self.get_service_status()
        else:
            self.print_colored(f"❌ Error starting service: {stderr}", 'red')
    
    def update_code(self, branch: str = 'main'):
        """Update code from GitHub repository"""
        self.print_header("Code Update")
        
        if not os.path.exists(f"{self.project_path}/.git"):
            self.print_colored("❌ Git repository not found", 'red')
            return
        
        # Change to project directory
        os.chdir(self.project_path)
        
        self.print_colored(f"📥 Fetching latest changes from {branch} branch...", 'yellow')
        
        # Fetch latest changes
        returncode, stdout, stderr = self.run_command("git fetch origin")
        if returncode != 0:
            self.print_colored(f"❌ Error fetching: {stderr}", 'red')
            return
        
        # Check for changes
        returncode, stdout, stderr = self.run_command(f"git diff HEAD origin/{branch} --name-only")
        
        if not stdout.strip():
            self.print_colored("✅ Code is already up to date", 'green')
            return
        
        self.print_colored("📋 Files to be updated:", 'cyan')
        print(stdout)
        
        response = input("\n🔄 Proceed with update? (y/N): ")
        if response.lower() != 'y':
            self.print_colored("❌ Update cancelled", 'yellow')
            return
        
        # Stop service before update
        self.print_colored("🛑 Stopping service for update...", 'yellow')
        self.run_command(f"systemctl stop {self.service_name}")
        
        # Pull changes
        self.print_colored("📥 Pulling changes...", 'yellow')
        returncode, stdout, stderr = self.run_command(f"git pull origin {branch}")
        
        if returncode != 0:
            self.print_colored(f"❌ Error pulling changes: {stderr}", 'red')
            return
        
        # Update dependencies if requirements changed
        if 'requirements' in stdout:
            self.print_colored("📦 Updating dependencies...", 'yellow')
            self.run_command("pip install -r requirements.txt")
        
        # Restart service
        self.print_colored("🚀 Restarting service...", 'yellow')
        returncode, stdout, stderr = self.run_command(f"systemctl start {self.service_name}")
        
        if returncode == 0:
            self.print_colored("✅ Update completed successfully", 'green')
            time.sleep(3)
            self.get_service_status()
        else:
            self.print_colored(f"❌ Error restarting service: {stderr}", 'red')
    
    def backup_data(self):
        """Create backup of important data"""
        self.print_header("Data Backup")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = f"/tmp/trading_bot_backup_{timestamp}"
        
        self.print_colored(f"📦 Creating backup in {backup_dir}...", 'yellow')
        
        # Create backup directory
        os.makedirs(backup_dir, exist_ok=True)
        
        # Backup configuration files
        config_backup = f"{backup_dir}/config"
        self.run_command(f"cp -r {self.config_path} {config_backup}")
        
        # Backup logs
        logs_backup = f"{backup_dir}/logs"
        os.makedirs(logs_backup, exist_ok=True)
        self.run_command(f"cp {self.log_path}/trading-bot*.log {logs_backup}/ 2>/dev/null || true")
        self.run_command(f"journalctl -u {self.service_name} --no-pager > {logs_backup}/service.log")
        
        # Backup database/data files
        data_backup = f"{backup_dir}/data"
        os.makedirs(data_backup, exist_ok=True)
        self.run_command(f"cp {self.project_path}/*.json {data_backup}/ 2>/dev/null || true")
        self.run_command(f"cp {self.project_path}/*.db {data_backup}/ 2>/dev/null || true")
        
        # Create archive
        archive_name = f"/tmp/trading_bot_backup_{timestamp}.tar.gz"
        returncode, stdout, stderr = self.run_command(f"tar -czf {archive_name} -C /tmp trading_bot_backup_{timestamp}")
        
        if returncode == 0:
            # Get archive size
            returncode, size_output, stderr = self.run_command(f"ls -lh {archive_name} | awk '{{print $5}}'")
            size = size_output.strip()
            
            self.print_colored(f"✅ Backup created: {archive_name} ({size})", 'green')
            
            # Cleanup temporary directory
            self.run_command(f"rm -rf {backup_dir}")
            
            # Show backup location
            self.print_colored(f"📁 Backup location: {archive_name}", 'cyan')
            self.print_colored("💡 To download: scp user@server:{} ./".format(archive_name), 'blue')
        else:
            self.print_colored(f"❌ Backup failed: {stderr}", 'red')
    
    def check_trading_status(self):
        """Check trading bot specific status"""
        self.print_header("Trading Bot Status")
        
        # Check API health
        self.print_colored("🌐 API Health Check:", 'cyan', bold=True)
        returncode, stdout, stderr = self.run_command("curl -s http://localhost:5000/health || echo 'API not responding'")
        
        if returncode == 0 and stdout:
            try:
                import json
                health_data = json.loads(stdout)
                self.print_colored("✅ API is responding", 'green')
                print(json.dumps(health_data, indent=2))
            except:
                print(stdout)
        else:
            self.print_colored("❌ API not responding", 'red')
        
        # Check contract validation
        print("\n")
        self.print_colored("📋 Contract Validation:", 'cyan', bold=True)
        returncode, stdout, stderr = self.run_command(
            "curl -s -X POST http://localhost:5000/api/validate-contracts -H 'Content-Type: application/json' -d '{\"contract_sizes\": [1, 5, 10]}' || echo 'Validation endpoint not responding'"
        )
        
        if returncode == 0 and stdout:
            try:
                validation_data = json.loads(stdout)
                self.print_colored("✅ Contract validation working", 'green')
                print(json.dumps(validation_data, indent=2))
            except:
                print(stdout)
        else:
            self.print_colored("❌ Contract validation not responding", 'red')
        
        # Check recent trades
        print("\n")
        self.print_colored("📊 Recent Activity:", 'cyan', bold=True)
        self.run_command(f"journalctl -u {self.service_name} --since '1 hour ago' | grep -i 'trade\|contract\|position' | tail -10", capture_output=False)
    
    def emergency_stop(self):
        """Emergency stop all trading activities"""
        self.print_header("🚨 EMERGENCY STOP")
        
        self.print_colored("⚠️  This will immediately stop all trading activities!", 'red', bold=True)
        response = input("Type 'EMERGENCY' to confirm: ")
        
        if response != 'EMERGENCY':
            self.print_colored("❌ Emergency stop cancelled", 'yellow')
            return
        
        # Stop service immediately
        self.print_colored("🛑 Stopping trading service...", 'red', bold=True)
        self.run_command(f"systemctl stop {self.service_name}")
        
        # Disable service to prevent auto-restart
        self.print_colored("🔒 Disabling service auto-start...", 'red')
        self.run_command(f"systemctl disable {self.service_name}")
        
        # Kill any remaining processes
        self.print_colored("💀 Terminating any remaining processes...", 'red')
        self.run_command("pkill -f 'bulenox\|trading'")
        
        # Create emergency stop flag
        emergency_flag = f"{self.project_path}/EMERGENCY_STOP"
        with open(emergency_flag, 'w') as f:
            f.write(f"Emergency stop activated at {datetime.now().isoformat()}\n")
        
        self.print_colored("🚨 EMERGENCY STOP ACTIVATED", 'red', bold=True)
        self.print_colored(f"📁 Emergency flag created: {emergency_flag}", 'yellow')
        self.print_colored("💡 To resume: run 'remote-mgmt resume'", 'blue')
    
    def resume_trading(self):
        """Resume trading after emergency stop"""
        self.print_header("Resume Trading")
        
        emergency_flag = f"{self.project_path}/EMERGENCY_STOP"
        
        if not os.path.exists(emergency_flag):
            self.print_colored("✅ No emergency stop flag found", 'green')
        else:
            self.print_colored("🔍 Emergency stop flag detected", 'yellow')
            response = input("Remove emergency stop and resume trading? (y/N): ")
            
            if response.lower() != 'y':
                self.print_colored("❌ Resume cancelled", 'yellow')
                return
            
            # Remove emergency flag
            os.remove(emergency_flag)
            self.print_colored("✅ Emergency stop flag removed", 'green')
        
        # Enable and start service
        self.print_colored("🔓 Enabling service...", 'yellow')
        self.run_command(f"systemctl enable {self.service_name}")
        
        self.print_colored("🚀 Starting service...", 'yellow')
        returncode, stdout, stderr = self.run_command(f"systemctl start {self.service_name}")
        
        if returncode == 0:
            self.print_colored("✅ Trading resumed successfully", 'green')
            time.sleep(3)
            self.get_service_status()
        else:
            self.print_colored(f"❌ Error resuming trading: {stderr}", 'red')
    
    def show_quick_commands(self):
        """Show quick reference commands"""
        self.print_header("Quick Reference Commands")
        
        commands = [
            ("📊 Status", "remote-mgmt status"),
            ("📋 Logs", "remote-mgmt logs"),
            ("📋 Follow Logs", "remote-mgmt logs --follow"),
            ("💻 Resources", "remote-mgmt resources"),
            ("🔄 Restart", "remote-mgmt restart"),
            ("📥 Update", "remote-mgmt update"),
            ("📦 Backup", "remote-mgmt backup"),
            ("🎯 Trading Status", "remote-mgmt trading"),
            ("🚨 Emergency Stop", "remote-mgmt emergency-stop"),
            ("▶️  Resume", "remote-mgmt resume"),
        ]
        
        for desc, cmd in commands:
            self.print_colored(f"{desc:<20} {cmd}", 'cyan')
        
        print("\n" + "="*60)
        self.print_colored("💡 Direct systemctl commands:", 'yellow', bold=True)
        
        systemctl_commands = [
            ("Service Status", f"systemctl status {self.service_name}"),
            ("Start Service", f"systemctl start {self.service_name}"),
            ("Stop Service", f"systemctl stop {self.service_name}"),
            ("Restart Service", f"systemctl restart {self.service_name}"),
            ("View Logs", f"journalctl -u {self.service_name} -f"),
        ]
        
        for desc, cmd in systemctl_commands:
            self.print_colored(f"{desc:<20} {cmd}", 'blue')

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Bulenox Trading Bot Remote Management',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  remote-mgmt status              # Check service status
  remote-mgmt logs --follow       # Follow logs in real-time
  remote-mgmt restart --force     # Force restart without confirmation
  remote-mgmt update              # Update code from GitHub
  remote-mgmt emergency-stop      # Emergency stop all trading
        """
    )
    
    parser.add_argument('command', choices=[
        'status', 'logs', 'resources', 'restart', 'update', 'backup',
        'trading', 'emergency-stop', 'resume', 'help'
    ], help='Management command to execute')
    
    parser.add_argument('--lines', '-n', type=int, default=50,
                       help='Number of log lines to display (default: 50)')
    parser.add_argument('--follow', '-f', action='store_true',
                       help='Follow logs in real-time')
    parser.add_argument('--force', action='store_true',
                       help='Force action without confirmation')
    parser.add_argument('--branch', default='main',
                       help='Git branch for updates (default: main)')
    
    args = parser.parse_args()
    
    # Initialize manager
    manager = RemoteManager()
    
    # Execute command
    try:
        if args.command == 'status':
            manager.get_service_status()
        
        elif args.command == 'logs':
            manager.view_logs(lines=args.lines, follow=args.follow)
        
        elif args.command == 'resources':
            manager.check_system_resources()
        
        elif args.command == 'restart':
            manager.restart_service(force=args.force)
        
        elif args.command == 'update':
            manager.update_code(branch=args.branch)
        
        elif args.command == 'backup':
            manager.backup_data()
        
        elif args.command == 'trading':
            manager.check_trading_status()
        
        elif args.command == 'emergency-stop':
            manager.emergency_stop()
        
        elif args.command == 'resume':
            manager.resume_trading()
        
        elif args.command == 'help':
            manager.show_quick_commands()
        
    except KeyboardInterrupt:
        manager.print_colored("\n👋 Operation cancelled by user", 'yellow')
    except Exception as e:
        manager.print_colored(f"❌ Error: {e}", 'red')
        sys.exit(1)

if __name__ == '__main__':
    main()