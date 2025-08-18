#!/usr/bin/env python3
"""
AI Trading Sentinel - Performance Monitor
Real-time monitoring of bot performance, logs, and health checks
"""

import os
import sys
import time
import json
import psutil
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("performance_monitor")

class PerformanceMonitor:
    """Monitor AI Trading Sentinel performance and health"""
    
    def __init__(self):
        self.log_dir = Path("logs")
        self.data_dir = Path("data")
        self.trading_log = self.log_dir / "trading.log"
        self.trae_log = self.log_dir / "trae.log"
        self.monitor_log = self.log_dir / "monitor.log"
        
        # Ensure directories exist
        self.log_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)
        
        # Performance metrics
        self.metrics = {
            "start_time": datetime.now(),
            "total_trades": 0,
            "successful_trades": 0,
            "failed_trades": 0,
            "total_profit": 0.0,
            "uptime_seconds": 0,
            "memory_usage_mb": 0,
            "cpu_usage_percent": 0,
            "last_trade_time": None,
            "last_error_time": None,
            "health_status": "unknown"
        }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system performance metrics"""
        try:
            # Get current process
            process = psutil.Process(os.getpid())
            
            # Memory usage
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            # CPU usage
            cpu_percent = process.cpu_percent(interval=1)
            
            # System metrics
            system_memory = psutil.virtual_memory()
            system_cpu = psutil.cpu_percent(interval=1)
            
            return {
                "process_memory_mb": round(memory_mb, 2),
                "process_cpu_percent": round(cpu_percent, 2),
                "system_memory_percent": round(system_memory.percent, 2),
                "system_cpu_percent": round(system_cpu, 2),
                "system_memory_available_gb": round(system_memory.available / 1024 / 1024 / 1024, 2)
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}
    
    def check_log_files(self) -> Dict[str, Any]:
        """Check log files for recent activity and errors"""
        log_status = {}
        
        for log_file in [self.trading_log, self.trae_log, self.monitor_log]:
            if log_file.exists():
                try:
                    # Get file size
                    size_mb = log_file.stat().st_size / 1024 / 1024
                    
                    # Get last modified time
                    last_modified = datetime.fromtimestamp(log_file.stat().st_mtime)
                    
                    # Count recent errors (last 10 minutes)
                    recent_errors = 0
                    recent_warnings = 0
                    
                    try:
                        with open(log_file, 'r', encoding='utf-8') as f:
                            lines = f.readlines()[-100:]  # Check last 100 lines
                            
                        cutoff_time = datetime.now() - timedelta(minutes=10)
                        
                        for line in lines:
                            if 'ERROR' in line:
                                try:
                                    # Extract timestamp from log line
                                    timestamp_str = line.split(' - ')[0]
                                    log_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                                    if log_time > cutoff_time:
                                        recent_errors += 1
                                except:
                                    pass
                            elif 'WARNING' in line:
                                try:
                                    timestamp_str = line.split(' - ')[0]
                                    log_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                                    if log_time > cutoff_time:
                                        recent_warnings += 1
                                except:
                                    pass
                    except Exception as e:
                        logger.warning(f"Could not analyze {log_file}: {e}")
                    
                    log_status[log_file.name] = {
                        "size_mb": round(size_mb, 2),
                        "last_modified": last_modified.isoformat(),
                        "recent_errors": recent_errors,
                        "recent_warnings": recent_warnings,
                        "exists": True
                    }
                except Exception as e:
                    log_status[log_file.name] = {
                        "error": str(e),
                        "exists": True
                    }
            else:
                log_status[log_file.name] = {
                    "exists": False
                }
        
        return log_status
    
    def check_trading_performance(self) -> Dict[str, Any]:
        """Analyze trading performance from logs"""
        performance = {
            "total_trades": 0,
            "successful_trades": 0,
            "failed_trades": 0,
            "last_trade_time": None,
            "recent_trades": []
        }
        
        if not self.trading_log.exists():
            return performance
        
        try:
            with open(self.trading_log, 'r', encoding='utf-8') as f:
                lines = f.readlines()[-200:]  # Check last 200 lines
            
            for line in lines:
                if 'Trade executed' in line or 'TRADE_EXECUTED' in line:
                    performance["total_trades"] += 1
                    performance["successful_trades"] += 1
                    
                    # Extract timestamp
                    try:
                        timestamp_str = line.split(' - ')[0]
                        trade_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                        performance["last_trade_time"] = trade_time.isoformat()
                        
                        # Add to recent trades if within last hour
                        if trade_time > datetime.now() - timedelta(hours=1):
                            performance["recent_trades"].append({
                                "time": trade_time.isoformat(),
                                "status": "success",
                                "details": line.strip()
                            })
                    except:
                        pass
                
                elif 'Trade failed' in line or 'TRADE_FAILED' in line:
                    performance["total_trades"] += 1
                    performance["failed_trades"] += 1
                    
                    # Extract timestamp
                    try:
                        timestamp_str = line.split(' - ')[0]
                        trade_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                        
                        # Add to recent trades if within last hour
                        if trade_time > datetime.now() - timedelta(hours=1):
                            performance["recent_trades"].append({
                                "time": trade_time.isoformat(),
                                "status": "failed",
                                "details": line.strip()
                            })
                    except:
                        pass
        
        except Exception as e:
            logger.error(f"Error analyzing trading performance: {e}")
        
        return performance
    
    def get_health_status(self) -> str:
        """Determine overall health status"""
        log_status = self.check_log_files()
        trading_perf = self.check_trading_performance()
        
        # Check for critical issues
        total_recent_errors = sum(log.get("recent_errors", 0) for log in log_status.values())
        
        if total_recent_errors > 10:
            return "critical"
        elif total_recent_errors > 5:
            return "warning"
        elif trading_perf["total_trades"] > 0 and trading_perf["failed_trades"] / trading_perf["total_trades"] > 0.5:
            return "warning"
        else:
            return "healthy"
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        system_metrics = self.get_system_metrics()
        log_status = self.check_log_files()
        trading_performance = self.check_trading_performance()
        health_status = self.get_health_status()
        
        uptime = datetime.now() - self.metrics["start_time"]
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "uptime_hours": round(uptime.total_seconds() / 3600, 2),
            "health_status": health_status,
            "system_metrics": system_metrics,
            "log_status": log_status,
            "trading_performance": trading_performance,
            "environment": {
                "python_version": sys.version,
                "working_directory": os.getcwd(),
                "environment_mode": os.getenv("ENVIRONMENT", "unknown")
            }
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any]):
        """Save performance report to file"""
        try:
            report_file = self.log_dir / f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Performance report saved to {report_file}")
        except Exception as e:
            logger.error(f"Error saving performance report: {e}")
    
    def print_summary(self, report: Dict[str, Any]):
        """Print performance summary to console"""
        print("\n" + "="*80)
        print("🤖 AI TRADING SENTINEL - PERFORMANCE MONITOR")
        print("="*80)
        
        # Health Status
        status_emoji = {
            "healthy": "✅",
            "warning": "⚠️",
            "critical": "❌",
            "unknown": "❓"
        }
        
        print(f"\n📊 HEALTH STATUS: {status_emoji.get(report['health_status'], '❓')} {report['health_status'].upper()}")
        print(f"⏱️  UPTIME: {report['uptime_hours']} hours")
        print(f"🕐 TIMESTAMP: {report['timestamp']}")
        
        # System Metrics
        if report['system_metrics']:
            sys_metrics = report['system_metrics']
            print(f"\n💻 SYSTEM PERFORMANCE:")
            print(f"   Memory Usage: {sys_metrics.get('process_memory_mb', 0)} MB")
            print(f"   CPU Usage: {sys_metrics.get('process_cpu_percent', 0)}%")
            print(f"   System Memory: {sys_metrics.get('system_memory_percent', 0)}%")
            print(f"   System CPU: {sys_metrics.get('system_cpu_percent', 0)}%")
        
        # Trading Performance
        trading = report['trading_performance']
        print(f"\n📈 TRADING PERFORMANCE:")
        print(f"   Total Trades: {trading['total_trades']}")
        print(f"   Successful: {trading['successful_trades']}")
        print(f"   Failed: {trading['failed_trades']}")
        
        if trading['total_trades'] > 0:
            success_rate = (trading['successful_trades'] / trading['total_trades']) * 100
            print(f"   Success Rate: {success_rate:.1f}%")
        
        if trading['last_trade_time']:
            print(f"   Last Trade: {trading['last_trade_time']}")
        
        # Recent Activity
        if trading['recent_trades']:
            print(f"\n🔄 RECENT TRADES ({len(trading['recent_trades'])})")
            for trade in trading['recent_trades'][-5:]:  # Show last 5
                status_icon = "✅" if trade['status'] == 'success' else "❌"
                print(f"   {status_icon} {trade['time']} - {trade['status']}")
        
        # Log Status
        print(f"\n📝 LOG FILES:")
        for log_name, log_info in report['log_status'].items():
            if log_info.get('exists', False):
                size = log_info.get('size_mb', 0)
                errors = log_info.get('recent_errors', 0)
                warnings = log_info.get('recent_warnings', 0)
                
                status_icon = "❌" if errors > 5 else "⚠️" if errors > 0 or warnings > 0 else "✅"
                print(f"   {status_icon} {log_name}: {size} MB (Errors: {errors}, Warnings: {warnings})")
            else:
                print(f"   ❓ {log_name}: Not found")
        
        print("\n" + "="*80)
    
    def monitor_continuous(self, interval_seconds: int = 60):
        """Run continuous monitoring"""
        logger.info(f"Starting continuous monitoring (interval: {interval_seconds}s)")
        
        try:
            while True:
                report = self.generate_report()
                self.print_summary(report)
                
                # Save report every 10 minutes
                if datetime.now().minute % 10 == 0:
                    self.save_report(report)
                
                time.sleep(interval_seconds)
        
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Error in continuous monitoring: {e}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Trading Sentinel Performance Monitor")
    parser.add_argument("--continuous", "-c", action="store_true", help="Run continuous monitoring")
    parser.add_argument("--interval", "-i", type=int, default=60, help="Monitoring interval in seconds (default: 60)")
    parser.add_argument("--save-report", "-s", action="store_true", help="Save report to file")
    
    args = parser.parse_args()
    
    monitor = PerformanceMonitor()
    
    if args.continuous:
        monitor.monitor_continuous(args.interval)
    else:
        # Single report
        report = monitor.generate_report()
        monitor.print_summary(report)
        
        if args.save_report:
            monitor.save_report(report)

if __name__ == "__main__":
    main()