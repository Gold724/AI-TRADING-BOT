#!/usr/bin/env python3
"""
Simple Production Monitoring Test for Bulenox Trading Bot
Windows-compatible version for testing
"""

import time
import json
import logging
import psutil
import requests
from datetime import datetime
from pathlib import Path

# Configure logging for Windows
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitoring_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SimpleMonitor:
    """Simple monitoring system for testing"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.metrics = []
    
    def collect_system_metrics(self):
        """Collect basic system metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('C:\\')
            
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / (1024**3)
            }
            
            self.metrics.append(metrics)
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return None
    
    def check_trading_bot_health(self):
        """Simulate trading bot health check"""
        try:
            # Simulate checking if bot process is running
            bot_processes = [p for p in psutil.process_iter(['pid', 'name']) 
                           if 'python' in p.info['name'].lower()]
            
            health_status = {
                'timestamp': datetime.now().isoformat(),
                'bot_running': len(bot_processes) > 0,
                'python_processes': len(bot_processes),
                'uptime_minutes': (datetime.now() - self.start_time).total_seconds() / 60
            }
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error checking bot health: {e}")
            return {'bot_running': False, 'error': str(e)}
    
    def simulate_trading_metrics(self):
        """Simulate trading performance metrics"""
        import random
        
        # Simulate some trading data
        trading_metrics = {
            'timestamp': datetime.now().isoformat(),
            'total_trades': random.randint(10, 50),
            'winning_trades': random.randint(6, 35),
            'daily_pnl': round(random.uniform(-50, 150), 2),
            'current_positions': random.randint(0, 5),
            'max_drawdown': round(random.uniform(5, 25), 2),
            'win_rate': round(random.uniform(0.6, 0.8), 3),
            'avg_contract_size': round(random.uniform(1.0, 10.0), 2)
        }
        
        return trading_metrics
    
    def check_risk_limits(self, trading_metrics):
        """Check if trading metrics are within risk limits"""
        alerts = []
        
        # Risk limit checks
        if trading_metrics['daily_pnl'] < -100:
            alerts.append(f"Daily loss limit exceeded: {trading_metrics['daily_pnl']}")
        
        if trading_metrics['max_drawdown'] > 20:
            alerts.append(f"Maximum drawdown exceeded: {trading_metrics['max_drawdown']}%")
        
        if trading_metrics['current_positions'] > 5:
            alerts.append(f"Too many concurrent positions: {trading_metrics['current_positions']}")
        
        if trading_metrics['avg_contract_size'] > 10:
            alerts.append(f"Contract size too large: {trading_metrics['avg_contract_size']}")
        
        return alerts
    
    def generate_monitoring_report(self):
        """Generate comprehensive monitoring report"""
        logger.info("Generating monitoring report...")
        
        # Collect all metrics
        system_metrics = self.collect_system_metrics()
        health_status = self.check_trading_bot_health()
        trading_metrics = self.simulate_trading_metrics()
        risk_alerts = self.check_risk_limits(trading_metrics)
        
        report = {
            'report_timestamp': datetime.now().isoformat(),
            'monitoring_duration_minutes': (datetime.now() - self.start_time).total_seconds() / 60,
            'system_metrics': system_metrics,
            'bot_health': health_status,
            'trading_performance': trading_metrics,
            'risk_alerts': risk_alerts,
            'overall_status': 'HEALTHY' if len(risk_alerts) == 0 else 'ALERT'
        }
        
        return report
    
    def run_monitoring_cycle(self, duration_minutes=2):
        """Run a complete monitoring cycle"""
        logger.info(f"Starting {duration_minutes}-minute monitoring cycle...")
        
        end_time = datetime.now().timestamp() + (duration_minutes * 60)
        cycle_count = 0
        
        while datetime.now().timestamp() < end_time:
            cycle_count += 1
            logger.info(f"Monitoring cycle {cycle_count}")
            
            # Collect metrics
            system_metrics = self.collect_system_metrics()
            if system_metrics:
                logger.info(f"CPU: {system_metrics['cpu_percent']:.1f}%, "
                          f"Memory: {system_metrics['memory_percent']:.1f}%, "
                          f"Disk: {system_metrics['disk_percent']:.1f}%")
            
            # Check bot health
            health = self.check_trading_bot_health()
            logger.info(f"Bot Status: {'Running' if health['bot_running'] else 'Stopped'}, "
                       f"Uptime: {health['uptime_minutes']:.1f} min")
            
            # Simulate trading check
            trading = self.simulate_trading_metrics()
            logger.info(f"Trading: {trading['total_trades']} trades, "
                       f"PnL: ${trading['daily_pnl']}, "
                       f"Win Rate: {trading['win_rate']:.1%}")
            
            # Check for alerts
            alerts = self.check_risk_limits(trading)
            if alerts:
                logger.warning(f"Risk Alerts: {', '.join(alerts)}")
            else:
                logger.info("All risk limits within acceptable ranges")
            
            # Wait before next cycle
            time.sleep(10)  # Check every 10 seconds
        
        # Generate final report
        final_report = self.generate_monitoring_report()
        
        # Save report
        report_file = f"monitoring_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(final_report, f, indent=2)
        
        logger.info(f"Monitoring cycle completed. Report saved to: {report_file}")
        return final_report

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Simple Production Monitoring Test')
    parser.add_argument('--duration', type=int, default=2, help='Monitoring duration in minutes')
    parser.add_argument('--test-mode', action='store_true', help='Run in test mode')
    
    args = parser.parse_args()
    
    logger.info("=== Bulenox Trading Bot - Production Monitoring Test ===")
    logger.info(f"Test Mode: {args.test_mode}")
    logger.info(f"Duration: {args.duration} minutes")
    
    monitor = SimpleMonitor()
    
    if args.test_mode:
        # Quick test mode
        logger.info("Running quick test...")
        
        # Test system metrics
        system_metrics = monitor.collect_system_metrics()
        logger.info(f"[OK] System metrics collected: CPU {system_metrics['cpu_percent']:.1f}%")
        
        # Test health check
        health = monitor.check_trading_bot_health()
        logger.info(f"[OK] Health check completed: {health['python_processes']} Python processes")
        
        # Test trading simulation
        trading = monitor.simulate_trading_metrics()
        logger.info(f"[OK] Trading metrics simulated: {trading['total_trades']} trades")
        
        # Test risk checks
        alerts = monitor.check_risk_limits(trading)
        logger.info(f"[OK] Risk checks completed: {len(alerts)} alerts")
        
        # Generate test report
        report = monitor.generate_monitoring_report()
        logger.info(f"[OK] Monitoring report generated: Status {report['overall_status']}")
        
        print("\n=== Test Results ===")
        print(f"System Status: OK")
        print(f"CPU Usage: {system_metrics['cpu_percent']:.1f}%")
        print(f"Memory Usage: {system_metrics['memory_percent']:.1f}%")
        print(f"Trading Status: {report['overall_status']}")
        print(f"Risk Alerts: {len(alerts)}")
        print("\n[SUCCESS] All monitoring systems operational!")
        
    else:
        # Full monitoring cycle
        report = monitor.run_monitoring_cycle(args.duration)
        
        print("\n=== Final Monitoring Report ===")
        print(f"Overall Status: {report['overall_status']}")
        print(f"Monitoring Duration: {report['monitoring_duration_minutes']:.1f} minutes")
        print(f"Risk Alerts: {len(report['risk_alerts'])}")
        
        if report['risk_alerts']:
            print("Alerts:")
            for alert in report['risk_alerts']:
                print(f"  - {alert}")

if __name__ == '__main__':
    main()