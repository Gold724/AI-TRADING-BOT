#!/usr/bin/env python3
"""
VPS Monitoring Script for AI Trading Sentinel
Monitors deployment status and system health on Contabo VPS
"""

import subprocess
import json
import sys
import os
from datetime import datetime
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv
try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False

# Load environment variables from .env file
load_dotenv()

class VPSMonitor:
    def __init__(self):
        self.vps_host = os.getenv('CONTABO_VPS_IP', os.getenv('VPS_HOST', 'your-contabo-ip'))
        self.vps_user = os.getenv('CONTABO_USERNAME', os.getenv('VPS_USER', 'root'))
        self.ssh_key_path = os.getenv('SSH_KEY_PATH', './trae_deploy_key')
        self.vps_password = os.getenv('CONTABO_PASSWORD', os.getenv('VPS_PASSWORD', ''))
        self.ssh_port = int(os.getenv('CONTABO_SSH_PORT', os.getenv('SSH_PORT', '22')))
        self.slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
        
    def run_ssh_command(self, command: str) -> Dict[str, Any]:
        """Execute SSH command on VPS and return result"""
        try:
            # Use paramiko for password authentication if available
            if PARAMIKO_AVAILABLE and self.vps_password:
                return self._run_paramiko_command(command)
            else:
                # Fallback to subprocess SSH
                ssh_cmd = [
                    'ssh',
                    '-i', self.ssh_key_path,
                    '-p', str(self.ssh_port),
                    '-o', 'StrictHostKeyChecking=no',
                    '-o', 'ConnectTimeout=30',
                    f'{self.vps_user}@{self.vps_host}',
                    command
                ]
                
                result = subprocess.run(
                    ssh_cmd,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                return {
                    'success': result.returncode == 0,
                    'stdout': result.stdout.strip(),
                    'stderr': result.stderr.strip(),
                    'returncode': result.returncode
                }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'stdout': '',
                'stderr': 'SSH command timed out',
                'returncode': -1
            }
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': f'SSH command failed: {str(e)}',
                'returncode': -1
            }
    
    def _run_paramiko_command(self, command: str) -> Dict[str, Any]:
        """Execute SSH command using paramiko with password authentication"""
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect with password
            client.connect(
                hostname=self.vps_host,
                port=self.ssh_port,
                username=self.vps_user,
                password=self.vps_password,
                timeout=30
            )
            
            # Execute command
            stdin, stdout, stderr = client.exec_command(command, timeout=60)
            
            # Get results
            stdout_data = stdout.read().decode('utf-8').strip()
            stderr_data = stderr.read().decode('utf-8').strip()
            exit_status = stdout.channel.recv_exit_status()
            
            client.close()
            
            return {
                'success': exit_status == 0,
                'stdout': stdout_data,
                'stderr': stderr_data,
                'returncode': exit_status
            }
            
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': f'Paramiko SSH failed: {str(e)}',
                'returncode': -1
            }
    
    def check_vps_connectivity(self) -> bool:
        """Test basic SSH connectivity to VPS"""
        print("🔍 Testing VPS connectivity...")
        result = self.run_ssh_command('echo "VPS_CONNECTED"')
        
        if result['success'] and 'VPS_CONNECTED' in result['stdout']:
            print("✅ VPS connectivity: OK")
            return True
        else:
            print(f"❌ VPS connectivity failed: {result['stderr']}")
            return False
    
    def check_bot_installation(self) -> Dict[str, Any]:
        """Verify bot files and dependencies are installed"""
        print("🔍 Checking bot installation...")
        
        checks = {
            'project_directory': 'ls -la /root/ai-trading-sentinel/',
            'python_version': 'python3 --version',
            'pip_packages': 'pip3 list | grep -E "(playwright|requests|flask)"',
            'systemd_service': 'systemctl status trae.service --no-pager',
            'bot_process': 'ps aux | grep -E "(main.py|trading)" | grep -v grep',
            'log_files': 'ls -la /root/ai-trading-sentinel/logs/ 2>/dev/null || echo "No logs directory"'
        }
        
        results = {}
        for check_name, command in checks.items():
            print(f"  Checking {check_name}...")
            result = self.run_ssh_command(command)
            results[check_name] = {
                'success': result['success'],
                'output': result['stdout'][:500],  # Limit output length
                'error': result['stderr'][:200] if result['stderr'] else None
            }
            
            if result['success']:
                print(f"  ✅ {check_name}: OK")
            else:
                print(f"  ❌ {check_name}: {result['stderr'][:100]}")
        
        return results
    
    def check_system_health(self) -> Dict[str, Any]:
        """Monitor system resources and health"""
        print("🔍 Checking system health...")
        
        health_checks = {
            'disk_usage': 'df -h /',
            'memory_usage': 'free -h',
            'cpu_load': 'uptime',
            'network_status': 'ping -c 3 8.8.8.8',
            'docker_status': 'docker ps 2>/dev/null || echo "Docker not running"',
            'nginx_status': 'systemctl status nginx --no-pager 2>/dev/null || echo "Nginx not configured"'
        }
        
        results = {}
        for check_name, command in health_checks.items():
            result = self.run_ssh_command(command)
            results[check_name] = {
                'success': result['success'],
                'output': result['stdout'][:300],
                'error': result['stderr'][:200] if result['stderr'] else None
            }
        
        return results
    
    def check_trading_logs(self) -> Dict[str, Any]:
        """Check recent trading activity and logs"""
        print("🔍 Checking trading logs...")
        
        log_commands = {
            'recent_logs': 'tail -50 /root/ai-trading-sentinel/logs/trading.log 2>/dev/null || echo "No trading logs"',
            'error_logs': 'tail -20 /root/ai-trading-sentinel/logs/error.log 2>/dev/null || echo "No error logs"',
            'systemd_logs': 'journalctl -u trae.service --no-pager -n 20 2>/dev/null || echo "No systemd logs"',
            'last_trades': 'ls -la /root/ai-trading-sentinel/data/trades/ 2>/dev/null || echo "No trades directory"'
        }
        
        results = {}
        for log_name, command in log_commands.items():
            result = self.run_ssh_command(command)
            results[log_name] = {
                'success': result['success'],
                'output': result['stdout'][-1000:],  # Last 1000 chars
                'error': result['stderr'][:200] if result['stderr'] else None
            }
        
        return results
    
    def send_slack_notification(self, message: str, status: str = "info") -> bool:
        """Send notification to Slack"""
        if not self.slack_webhook:
            return False
        
        colors = {
            "success": "#36a64f",
            "warning": "#ff9500", 
            "error": "#ff0000",
            "info": "#0099cc"
        }
        
        payload = {
            "attachments": [{
                "color": colors.get(status, "#0099cc"),
                "title": "🤖 AI Trading Sentinel - VPS Monitor",
                "text": message,
                "footer": "TRAE-SentinelOps",
                "ts": int(datetime.now().timestamp())
            }]
        }
        
        try:
            response = requests.post(self.slack_webhook, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Slack notification failed: {e}")
            return False
    
    def generate_report(self, connectivity: bool, installation: Dict, health: Dict, logs: Dict) -> str:
        """Generate comprehensive monitoring report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        report = f"""
🤖 **AI Trading Sentinel VPS Monitor Report**
📅 **Timestamp:** {timestamp}
🖥️ **VPS Host:** {self.vps_host}

**🔗 CONNECTIVITY STATUS**
{'✅ Connected' if connectivity else '❌ Connection Failed'}

**📦 BOT INSTALLATION STATUS**
"""
        
        for check, result in installation.items():
            status = "✅" if result['success'] else "❌"
            report += f"{status} {check.replace('_', ' ').title()}\n"
            if not result['success'] and result['error']:
                report += f"   Error: {result['error'][:100]}\n"
        
        report += "\n**💻 SYSTEM HEALTH**\n"
        for check, result in health.items():
            status = "✅" if result['success'] else "❌"
            report += f"{status} {check.replace('_', ' ').title()}\n"
        
        report += "\n**📊 TRADING ACTIVITY**\n"
        for log_type, result in logs.items():
            if result['success'] and result['output'] and "No " not in result['output']:
                report += f"✅ {log_type.replace('_', ' ').title()}: Active\n"
            else:
                report += f"⚠️ {log_type.replace('_', ' ').title()}: No recent activity\n"
        
        return report
    
    def run_full_monitor(self) -> Dict[str, Any]:
        """Run complete VPS monitoring suite"""
        print("🚀 Starting VPS monitoring...")
        print(f"Target: {self.vps_user}@{self.vps_host}")
        print("-" * 50)
        
        # Run all checks
        connectivity = self.check_vps_connectivity()
        installation = self.check_bot_installation() if connectivity else {}
        health = self.check_system_health() if connectivity else {}
        logs = self.check_trading_logs() if connectivity else {}
        
        # Generate report
        report = self.generate_report(connectivity, installation, health, logs)
        
        # Determine overall status
        if not connectivity:
            status = "error"
            summary = "❌ VPS connection failed"
        elif not any(result['success'] for result in installation.values()):
            status = "error" 
            summary = "❌ Bot installation issues detected"
        elif all(result['success'] for result in installation.values()):
            status = "success"
            summary = "✅ All systems operational"
        else:
            status = "warning"
            summary = "⚠️ Some issues detected"
        
        # Send Slack notification
        slack_message = f"{summary}\n\n{report[:1000]}..."
        self.send_slack_notification(slack_message, status)
        
        print("\n" + "=" * 50)
        print("📋 MONITORING REPORT")
        print("=" * 50)
        print(report)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'connectivity': connectivity,
            'installation': installation,
            'health': health,
            'logs': logs,
            'status': status,
            'summary': summary
        }

def main():
    """Main monitoring function"""
    monitor = VPSMonitor()
    
    try:
        results = monitor.run_full_monitor()
        
        # Save results to file
        output_file = f"vps_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Results saved to: {output_file}")
        
        # Exit with appropriate code
        if results['status'] == 'error':
            sys.exit(1)
        elif results['status'] == 'warning':
            sys.exit(2)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n⚠️ Monitoring interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Monitoring failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()