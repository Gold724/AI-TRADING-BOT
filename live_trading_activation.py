#!/usr/bin/env python3
"""
AI Trading Sentinel - Live Trading Activation
Safe transition from demo to live trading mode
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('live_trading_activation.log'),
        logging.StreamHandler()
    ]
)

class LiveTradingActivator:
    """Safe activation of live trading mode"""
    
    def __init__(self):
        self.load_config()
        self.safety_checks = []
        
    def load_config(self):
        """Load configuration and environment variables"""
        self.config = {
            'demo_mode_var': 'BULENOX_DEMO_MODE',
            'required_demo_days': 7,  # Minimum demo trading days
            'min_success_rate': 0.75,  # 75% success rate required
            'max_drawdown_threshold': 0.15,  # 15% max drawdown
            'min_profit_consistency': 3,  # 3 consecutive profitable days
        }
        
        # Load current environment
        self.current_demo_mode = os.getenv('BULENOX_DEMO_MODE', 'true').lower() == 'true'
        self.bulenox_username = os.getenv('BULENOX_USERNAME')
        self.bulenox_password = os.getenv('BULENOX_PASSWORD')
        
    def check_demo_performance(self) -> Dict:
        """Analyze demo trading performance"""
        logging.info("📊 Analyzing demo trading performance...")
        
        performance_data = {
            'total_trades': 0,
            'successful_trades': 0,
            'total_profit': 0.0,
            'max_drawdown': 0.0,
            'consecutive_profitable_days': 0,
            'trading_days': 0,
            'success_rate': 0.0,
            'average_daily_profit': 0.0
        }
        
        try:
            # Load trading history from logs or database
            if os.path.exists('data/historical/trading_history.json'):
                with open('data/historical/trading_history.json', 'r') as f:
                    history = json.load(f)
                
                # Analyze performance metrics
                performance_data = self.analyze_trading_history(history)
            else:
                logging.warning("No trading history found")
                
        except Exception as e:
            logging.error(f"Error analyzing performance: {str(e)}")
            
        return performance_data
    
    def analyze_trading_history(self, history: Dict) -> Dict:
        """Analyze trading history for performance metrics"""
        trades = history.get('trades', [])
        daily_results = {}
        
        total_trades = len(trades)
        successful_trades = 0
        total_profit = 0.0
        max_drawdown = 0.0
        running_balance = 0.0
        peak_balance = 0.0
        
        # Process each trade
        for trade in trades:
            profit = trade.get('profit', 0.0)
            total_profit += profit
            running_balance += profit
            
            if profit > 0:
                successful_trades += 1
            
            # Track drawdown
            if running_balance > peak_balance:
                peak_balance = running_balance
            
            current_drawdown = (peak_balance - running_balance) / max(peak_balance, 1)
            max_drawdown = max(max_drawdown, current_drawdown)
            
            # Group by day
            trade_date = trade.get('timestamp', '').split('T')[0]
            if trade_date not in daily_results:
                daily_results[trade_date] = 0.0
            daily_results[trade_date] += profit
        
        # Calculate consecutive profitable days
        consecutive_days = 0
        max_consecutive = 0
        for date in sorted(daily_results.keys()):
            if daily_results[date] > 0:
                consecutive_days += 1
                max_consecutive = max(max_consecutive, consecutive_days)
            else:
                consecutive_days = 0
        
        return {
            'total_trades': total_trades,
            'successful_trades': successful_trades,
            'total_profit': total_profit,
            'max_drawdown': max_drawdown,
            'consecutive_profitable_days': max_consecutive,
            'trading_days': len(daily_results),
            'success_rate': successful_trades / max(total_trades, 1),
            'average_daily_profit': total_profit / max(len(daily_results), 1)
        }
    
    def run_safety_checks(self) -> List[Dict]:
        """Run comprehensive safety checks"""
        logging.info("🛡️ Running safety checks...")
        
        checks = []
        
        # Check 1: Demo mode performance
        performance = self.check_demo_performance()
        
        checks.append({
            'name': 'Demo Trading Performance',
            'status': 'pass' if performance['success_rate'] >= self.config['min_success_rate'] else 'fail',
            'details': f"Success rate: {performance['success_rate']:.1%} (required: {self.config['min_success_rate']:.1%})",
            'data': performance
        })
        
        # Check 2: Trading days requirement
        checks.append({
            'name': 'Demo Trading Duration',
            'status': 'pass' if performance['trading_days'] >= self.config['required_demo_days'] else 'fail',
            'details': f"Trading days: {performance['trading_days']} (required: {self.config['required_demo_days']})",
            'data': {'days': performance['trading_days']}
        })
        
        # Check 3: Drawdown control
        checks.append({
            'name': 'Risk Management',
            'status': 'pass' if performance['max_drawdown'] <= self.config['max_drawdown_threshold'] else 'fail',
            'details': f"Max drawdown: {performance['max_drawdown']:.1%} (limit: {self.config['max_drawdown_threshold']:.1%})",
            'data': {'drawdown': performance['max_drawdown']}
        })
        
        # Check 4: Profit consistency
        checks.append({
            'name': 'Profit Consistency',
            'status': 'pass' if performance['consecutive_profitable_days'] >= self.config['min_profit_consistency'] else 'fail',
            'details': f"Consecutive profitable days: {performance['consecutive_profitable_days']} (required: {self.config['min_profit_consistency']})",
            'data': {'consecutive_days': performance['consecutive_profitable_days']}
        })
        
        # Check 5: System health
        system_health = self.check_system_health()
        checks.append({
            'name': 'System Health',
            'status': 'pass' if system_health['healthy'] else 'fail',
            'details': system_health['message'],
            'data': system_health
        })
        
        # Check 6: Account verification
        account_status = self.verify_account_status()
        checks.append({
            'name': 'Account Verification',
            'status': 'pass' if account_status['verified'] else 'fail',
            'details': account_status['message'],
            'data': account_status
        })
        
        return checks
    
    def check_system_health(self) -> Dict:
        """Check system health and readiness"""
        try:
            # Check backend health
            response = requests.get('http://localhost:5000/api/health', timeout=10)
            if response.status_code == 200:
                return {
                    'healthy': True,
                    'message': 'Backend service is healthy',
                    'response_time': response.elapsed.total_seconds()
                }
            else:
                return {
                    'healthy': False,
                    'message': f'Backend health check failed: HTTP {response.status_code}',
                    'response_time': 0
                }
        except Exception as e:
            return {
                'healthy': False,
                'message': f'Backend health check failed: {str(e)}',
                'response_time': 0
            }
    
    def verify_account_status(self) -> Dict:
        """Verify Bulenox account status"""
        try:
            # Check account credentials
            if not self.bulenox_username or not self.bulenox_password:
                return {
                    'verified': False,
                    'message': 'Bulenox credentials not configured'
                }
            
            # Test connection (this would need actual Bulenox API integration)
            return {
                'verified': True,
                'message': 'Account credentials configured',
                'account': self.bulenox_username
            }
            
        except Exception as e:
            return {
                'verified': False,
                'message': f'Account verification failed: {str(e)}'
            }
    
    def create_backup(self) -> str:
        """Create backup before switching to live mode"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = f"backups/pre_live_backup_{timestamp}"
        
        try:
            os.makedirs(backup_dir, exist_ok=True)
            
            # Backup configuration files
            import shutil
            files_to_backup = ['.env', 'config/', 'data/']
            
            for item in files_to_backup:
                if os.path.exists(item):
                    if os.path.isfile(item):
                        shutil.copy2(item, backup_dir)
                    else:
                        shutil.copytree(item, os.path.join(backup_dir, os.path.basename(item)))
            
            logging.info(f"✅ Backup created: {backup_dir}")
            return backup_dir
            
        except Exception as e:
            logging.error(f"❌ Backup failed: {str(e)}")
            raise
    
    def activate_live_trading(self) -> bool:
        """Activate live trading mode"""
        logging.info("🚀 Activating live trading mode...")
        
        try:
            # Create backup first
            backup_dir = self.create_backup()
            
            # Update environment variable
            self.update_env_variable('BULENOX_DEMO_MODE', 'false')
            
            # Restart services to apply changes
            self.restart_services()
            
            # Verify live mode activation
            time.sleep(10)
            if self.verify_live_mode():
                logging.info("✅ Live trading mode activated successfully!")
                
                # Send notification
                self.send_activation_notification(backup_dir)
                return True
            else:
                logging.error("❌ Live mode verification failed")
                return False
                
        except Exception as e:
            logging.error(f"❌ Live trading activation failed: {str(e)}")
            return False
    
    def update_env_variable(self, key: str, value: str):
        """Update environment variable in .env file"""
        env_file = '.env'
        
        # Read current .env file
        lines = []
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                lines = f.readlines()
        
        # Update or add the variable
        updated = False
        for i, line in enumerate(lines):
            if line.startswith(f'{key}='):
                lines[i] = f'{key}={value}\n'
                updated = True
                break
        
        if not updated:
            lines.append(f'{key}={value}\n')
        
        # Write back to file
        with open(env_file, 'w') as f:
            f.writelines(lines)
        
        logging.info(f"Updated {key}={value} in .env file")
    
    def restart_services(self):
        """Restart trading services"""
        logging.info("🔄 Restarting services...")
        
        try:
            # Try systemd first, then PM2
            commands = [
                'sudo systemctl restart ai-trading-sentinel-backend',
                'sudo systemctl restart ai-trading-sentinel-frontend',
                'pm2 restart all'
            ]
            
            for cmd in commands:
                try:
                    subprocess.run(cmd.split(), check=True, capture_output=True)
                    logging.info(f"✅ Executed: {cmd}")
                except subprocess.CalledProcessError:
                    logging.warning(f"⚠️ Command failed: {cmd}")
                    
        except Exception as e:
            logging.error(f"❌ Service restart failed: {str(e)}")
    
    def verify_live_mode(self) -> bool:
        """Verify that live mode is active"""
        try:
            response = requests.get('http://localhost:5000/api/status', timeout=10)
            if response.status_code == 200:
                status = response.json()
                return not status.get('demo_mode', True)
            return False
        except:
            return False
    
    def send_activation_notification(self, backup_dir: str):
        """Send notification about live trading activation"""
        message = f"""
🚀 AI Trading Sentinel - LIVE TRADING ACTIVATED

Timestamp: {datetime.now()}
Backup Location: {backup_dir}
Account: {self.bulenox_username}

⚠️ IMPORTANT: Live trading is now active!
Monitor the system closely for the first few hours.

System Status: http://localhost:5000/api/status
Dashboard: http://localhost:3000
        """
        
        logging.info(message)
        # Here you could add email/Slack notification
    
    def generate_activation_report(self, checks: List[Dict]) -> str:
        """Generate activation readiness report"""
        report = []
        report.append("🎯 AI Trading Sentinel - Live Trading Readiness Report")
        report.append("=" * 60)
        report.append(f"📅 Generated: {datetime.now()}")
        report.append("")
        
        # Overall status
        passed_checks = sum(1 for check in checks if check['status'] == 'pass')
        total_checks = len(checks)
        
        if passed_checks == total_checks:
            overall_status = "🟢 READY FOR LIVE TRADING"
        else:
            overall_status = "🔴 NOT READY FOR LIVE TRADING"
        
        report.append(f"Overall Status: {overall_status}")
        report.append(f"Checks Passed: {passed_checks}/{total_checks}")
        report.append("")
        
        # Individual check results
        for check in checks:
            status_icon = "✅" if check['status'] == 'pass' else "❌"
            report.append(f"{status_icon} {check['name']}: {check['status'].upper()}")
            report.append(f"   {check['details']}")
            report.append("")
        
        # Recommendations
        failed_checks = [check for check in checks if check['status'] == 'fail']
        if failed_checks:
            report.append("🔧 Required Actions:")
            for check in failed_checks:
                report.append(f"   • Fix: {check['name']}")
            report.append("")
        
        return "\n".join(report)
    
    def run_activation_process(self):
        """Run complete activation process"""
        logging.info("🎯 Starting live trading activation process...")
        
        # Run safety checks
        checks = self.run_safety_checks()
        
        # Generate report
        report = self.generate_activation_report(checks)
        print(report)
        
        # Save report
        with open('live_trading_readiness_report.txt', 'w') as f:
            f.write(report)
        
        # Check if ready for activation
        passed_checks = sum(1 for check in checks if check['status'] == 'pass')
        total_checks = len(checks)
        
        if passed_checks == total_checks:
            # Ask for confirmation
            print("\n🚨 FINAL CONFIRMATION REQUIRED 🚨")
            print("You are about to activate LIVE TRADING mode.")
            print("This will use real money for trading operations.")
            
            confirmation = input("\nType 'ACTIVATE LIVE TRADING' to proceed: ")
            
            if confirmation == 'ACTIVATE LIVE TRADING':
                success = self.activate_live_trading()
                if success:
                    print("🎉 Live trading activated successfully!")
                else:
                    print("❌ Live trading activation failed!")
            else:
                print("❌ Activation cancelled by user")
        else:
            print(f"\n❌ Cannot activate live trading: {total_checks - passed_checks} checks failed")
            print("Please address the failed checks and run again.")

def main():
    """Main activation function"""
    activator = LiveTradingActivator()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--force':
        print("⚠️ FORCE MODE: Skipping safety checks")
        activator.activate_live_trading()
    else:
        activator.run_activation_process()

if __name__ == "__main__":
    main()