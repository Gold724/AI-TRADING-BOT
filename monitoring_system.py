# monitoring_system.py

import os
import json
import time
import logging
import threading
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Try to import components
try:
    from emergency_protocol import EmergencyProtocol
    from live_trading import LiveTrading
    from risk_control import RiskController
    from strategy_manager import StrategyManager
    from memory_engine import MemoryEngine
    from signal_router import SignalRouter
    
    ALL_IMPORTS_SUCCESSFUL = True
except ImportError as e:
    print(f"Import error: {e}")
    ALL_IMPORTS_SUCCESSFUL = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("monitoring.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("monitoring_system")

class MonitoringSystem:
    """Monitoring and alerting system for the live trading system"""
    
    def __init__(self, config_path: str = "config/monitoring_config.json"):
        """Initialize the monitoring system
        
        Args:
            config_path: Path to the configuration file
        """
        self.config = self._load_config(config_path)
        self.components = {}
        self.metrics = {}
        self.alerts = []
        self.running = False
        self.monitor_thread = None
        self.last_check_time = datetime.now()
        self.alert_cooldown = {}
        
        # Create monitoring data directory
        os.makedirs("data/monitoring", exist_ok=True)
        
        # Initialize metrics history
        self.metrics_history = {
            "timestamp": [],
            "account_balance": [],
            "equity": [],
            "open_trades": [],
            "daily_pnl": [],
            "win_rate": [],
            "system_cpu": [],
            "system_memory": [],
            "api_latency": []
        }
        
        logger.info("Monitoring system initialized")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from file
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Dict: Configuration
        """
        try:
            # Create default config if file doesn't exist
            if not os.path.exists(config_path):
                os.makedirs(os.path.dirname(config_path), exist_ok=True)
                default_config = {
                    "check_interval": 60,  # seconds
                    "metrics_save_interval": 300,  # seconds
                    "chart_update_interval": 3600,  # seconds
                    "alert_cooldown": 1800,  # seconds
                    "thresholds": {
                        "daily_drawdown": 5.0,  # percent
                        "consecutive_losses": 5,
                        "win_rate_min": 40.0,  # percent
                        "balance_drop": 10.0,  # percent
                        "cpu_usage": 90.0,  # percent
                        "memory_usage": 90.0,  # percent
                        "api_latency": 2000  # milliseconds
                    },
                    "notifications": {
                        "slack": {
                            "enabled": True,
                            "webhook_url": ""
                        },
                        "email": {
                            "enabled": False,
                            "smtp_server": "",
                            "smtp_port": 587,
                            "sender": "",
                            "recipient": "",
                            "username": "",
                            "password": ""
                        }
                    }
                }
                
                with open(config_path, "w") as f:
                    json.dump(default_config, f, indent=4)
                
                return default_config
            
            # Load config from file
            with open(config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            # Return default config
            return {
                "check_interval": 60,
                "metrics_save_interval": 300,
                "chart_update_interval": 3600,
                "alert_cooldown": 1800,
                "thresholds": {
                    "daily_drawdown": 5.0,
                    "consecutive_losses": 5,
                    "win_rate_min": 40.0,
                    "balance_drop": 10.0,
                    "cpu_usage": 90.0,
                    "memory_usage": 90.0,
                    "api_latency": 2000
                }
            }
    
    def initialize_components(self) -> bool:
        """Initialize all components
        
        Returns:
            bool: True if all components initialized successfully, False otherwise
        """
        try:
            logger.info("Initializing components...")
            
            # Initialize components
            self.components["emergency_protocol"] = EmergencyProtocol()
            self.components["live_trading"] = LiveTrading()
            self.components["risk_controller"] = RiskController()
            self.components["strategy_manager"] = StrategyManager()
            self.components["memory_engine"] = MemoryEngine()
            self.components["signal_router"] = SignalRouter()
            
            logger.info("All components initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            return False
    
    def start_monitoring(self):
        """Start the monitoring thread"""
        if self.running:
            logger.warning("Monitoring already running")
            return
        
        if not ALL_IMPORTS_SUCCESSFUL:
            logger.error("Cannot start monitoring due to import errors")
            return
        
        # Initialize components
        if not self.initialize_components():
            logger.error("Failed to initialize components")
            return
        
        # Connect to broker
        live_trading = self.components["live_trading"]
        if not live_trading.connect():
            logger.error("Failed to connect to broker")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        logger.info("Monitoring started")
    
    def stop_monitoring(self):
        """Stop the monitoring thread"""
        if not self.running:
            logger.warning("Monitoring not running")
            return
        
        self.running = False
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        
        # Disconnect from broker
        try:
            live_trading = self.components["live_trading"]
            live_trading.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting from broker: {e}")
        
        logger.info("Monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        last_metrics_save = datetime.now()
        last_chart_update = datetime.now()
        
        while self.running:
            try:
                # Check all metrics
                self._check_all_metrics()
                
                # Save metrics history
                if (datetime.now() - last_metrics_save).total_seconds() >= self.config.get("metrics_save_interval", 300):
                    self._save_metrics_history()
                    last_metrics_save = datetime.now()
                
                # Update charts
                if (datetime.now() - last_chart_update).total_seconds() >= self.config.get("chart_update_interval", 3600):
                    self._generate_charts()
                    last_chart_update = datetime.now()
                
                # Sleep until next check
                time.sleep(self.config.get("check_interval", 60))
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(10)  # Sleep for a short time before retrying
    
    def _check_all_metrics(self):
        """Check all metrics and generate alerts if necessary"""
        try:
            # Get current time
            current_time = datetime.now()
            
            # Check if emergency protocol is active
            emergency_protocol = self.components["emergency_protocol"]
            is_emergency = emergency_protocol.is_emergency_active()
            emergency_status, emergency_message = emergency_protocol.get_emergency_status()
            
            # Get trading metrics
            live_trading = self.components["live_trading"]
            account_info = live_trading.get_account_info()
            trading_stats = live_trading.get_trading_stats()
            active_orders = live_trading.get_active_orders()
            daily_pnl = live_trading.get_daily_pnl()
            
            # Get system metrics
            system_metrics = self._get_system_metrics()
            
            # Update metrics
            self.metrics = {
                "timestamp": current_time.isoformat(),
                "account": account_info,
                "trading": trading_stats,
                "active_orders": len(active_orders),
                "daily_pnl": daily_pnl,
                "system": system_metrics,
                "emergency": {
                    "active": is_emergency,
                    "status": emergency_status,
                    "message": emergency_message
                }
            }
            
            # Update metrics history
            self._update_metrics_history()
            
            # Check for alert conditions
            self._check_alert_conditions()
            
            # Update last check time
            self.last_check_time = current_time
        except Exception as e:
            logger.error(f"Error checking metrics: {e}")
    
    def _get_system_metrics(self) -> Dict:
        """Get system metrics
        
        Returns:
            Dict: System metrics
        """
        try:
            import psutil
            
            # Get CPU and memory usage
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # Get network stats
            net_io = psutil.net_io_counters()
            
            # Check API latency
            api_latency = self._check_api_latency()
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "disk_percent": disk_percent,
                "network": {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv
                },
                "api_latency": api_latency
            }
        except ImportError:
            logger.warning("psutil not installed, cannot get system metrics")
            return {
                "cpu_percent": 0,
                "memory_percent": 0,
                "disk_percent": 0,
                "network": {
                    "bytes_sent": 0,
                    "bytes_recv": 0
                },
                "api_latency": 0
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {
                "cpu_percent": 0,
                "memory_percent": 0,
                "disk_percent": 0,
                "network": {
                    "bytes_sent": 0,
                    "bytes_recv": 0
                },
                "api_latency": 0
            }
    
    def _check_api_latency(self) -> float:
        """Check API latency
        
        Returns:
            float: API latency in milliseconds
        """
        try:
            # Get broker adapter from live trading
            live_trading = self.components["live_trading"]
            
            # Measure time to get account info
            start_time = time.time()
            live_trading.get_account_info()
            end_time = time.time()
            
            # Calculate latency in milliseconds
            latency = (end_time - start_time) * 1000
            
            return latency
        except Exception as e:
            logger.error(f"Error checking API latency: {e}")
            return 0
    
    def _update_metrics_history(self):
        """Update metrics history"""
        try:
            # Get values from metrics
            timestamp = datetime.now()
            account_balance = self.metrics.get("account", {}).get("balance", 0)
            equity = self.metrics.get("account", {}).get("equity", 0)
            open_trades = self.metrics.get("active_orders", 0)
            daily_pnl = self.metrics.get("daily_pnl", 0)
            win_rate = self.metrics.get("trading", {}).get("win_rate", 0)
            system_cpu = self.metrics.get("system", {}).get("cpu_percent", 0)
            system_memory = self.metrics.get("system", {}).get("memory_percent", 0)
            api_latency = self.metrics.get("system", {}).get("api_latency", 0)
            
            # Update history
            self.metrics_history["timestamp"].append(timestamp)
            self.metrics_history["account_balance"].append(account_balance)
            self.metrics_history["equity"].append(equity)
            self.metrics_history["open_trades"].append(open_trades)
            self.metrics_history["daily_pnl"].append(daily_pnl)
            self.metrics_history["win_rate"].append(win_rate)
            self.metrics_history["system_cpu"].append(system_cpu)
            self.metrics_history["system_memory"].append(system_memory)
            self.metrics_history["api_latency"].append(api_latency)
            
            # Limit history size (keep last 1000 entries)
            max_history = 1000
            if len(self.metrics_history["timestamp"]) > max_history:
                for key in self.metrics_history:
                    self.metrics_history[key] = self.metrics_history[key][-max_history:]
        except Exception as e:
            logger.error(f"Error updating metrics history: {e}")
    
    def _save_metrics_history(self):
        """Save metrics history to file"""
        try:
            # Convert to DataFrame
            df = pd.DataFrame(self.metrics_history)
            
            # Save to CSV
            file_path = os.path.join("data", "monitoring", "metrics_history.csv")
            df.to_csv(file_path, index=False)
            
            logger.info(f"Metrics history saved to {file_path}")
        except Exception as e:
            logger.error(f"Error saving metrics history: {e}")
    
    def _generate_charts(self):
        """Generate monitoring charts"""
        try:
            # Create DataFrame from metrics history
            df = pd.DataFrame(self.metrics_history)
            
            # Convert timestamp to datetime if it's not already
            if not isinstance(df["timestamp"][0], datetime):
                df["timestamp"] = pd.to_datetime(df["timestamp"])
            
            # Create charts directory
            charts_dir = os.path.join("data", "monitoring", "charts")
            os.makedirs(charts_dir, exist_ok=True)
            
            # Generate account balance and equity chart
            plt.figure(figsize=(12, 6))
            plt.plot(df["timestamp"], df["account_balance"], label="Account Balance")
            plt.plot(df["timestamp"], df["equity"], label="Equity")
            plt.title("Account Balance and Equity")
            plt.xlabel("Time")
            plt.ylabel("Amount")
            plt.legend()
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(os.path.join(charts_dir, "account_balance.png"))
            plt.close()
            
            # Generate daily PnL chart
            plt.figure(figsize=(12, 6))
            plt.plot(df["timestamp"], df["daily_pnl"])
            plt.title("Daily Profit and Loss")
            plt.xlabel("Time")
            plt.ylabel("PnL")
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(os.path.join(charts_dir, "daily_pnl.png"))
            plt.close()
            
            # Generate win rate chart
            plt.figure(figsize=(12, 6))
            plt.plot(df["timestamp"], df["win_rate"])
            plt.title("Win Rate")
            plt.xlabel("Time")
            plt.ylabel("Win Rate (%)")
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(os.path.join(charts_dir, "win_rate.png"))
            plt.close()
            
            # Generate system metrics chart
            plt.figure(figsize=(12, 6))
            plt.plot(df["timestamp"], df["system_cpu"], label="CPU Usage")
            plt.plot(df["timestamp"], df["system_memory"], label="Memory Usage")
            plt.title("System Resource Usage")
            plt.xlabel("Time")
            plt.ylabel("Usage (%)")
            plt.legend()
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(os.path.join(charts_dir, "system_resources.png"))
            plt.close()
            
            # Generate API latency chart
            plt.figure(figsize=(12, 6))
            plt.plot(df["timestamp"], df["api_latency"])
            plt.title("API Latency")
            plt.xlabel("Time")
            plt.ylabel("Latency (ms)")
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(os.path.join(charts_dir, "api_latency.png"))
            plt.close()
            
            logger.info(f"Charts generated in {charts_dir}")
        except Exception as e:
            logger.error(f"Error generating charts: {e}")
    
    def _check_alert_conditions(self):
        """Check for alert conditions"""
        try:
            # Get thresholds from config
            thresholds = self.config.get("thresholds", {})
            
            # Check daily drawdown
            daily_pnl = self.metrics.get("daily_pnl", 0)
            account_balance = self.metrics.get("account", {}).get("balance", 0)
            
            if account_balance > 0:
                daily_drawdown_percent = abs(daily_pnl) / account_balance * 100 if daily_pnl < 0 else 0
                
                if daily_drawdown_percent >= thresholds.get("daily_drawdown", 5.0):
                    self._create_alert(
                        "Daily Drawdown Alert",
                        f"Daily drawdown of {daily_drawdown_percent:.2f}% exceeds threshold of {thresholds.get('daily_drawdown', 5.0)}%",
                        "high"
                    )
            
            # Check consecutive losses
            consecutive_losses = self._get_consecutive_losses()
            
            if consecutive_losses >= thresholds.get("consecutive_losses", 5):
                self._create_alert(
                    "Consecutive Losses Alert",
                    f"Consecutive losses of {consecutive_losses} exceeds threshold of {thresholds.get('consecutive_losses', 5)}",
                    "high"
                )
            
            # Check win rate
            win_rate = self.metrics.get("trading", {}).get("win_rate", 0)
            
            if win_rate < thresholds.get("win_rate_min", 40.0):
                self._create_alert(
                    "Win Rate Alert",
                    f"Win rate of {win_rate:.2f}% is below threshold of {thresholds.get('win_rate_min', 40.0)}%",
                    "medium"
                )
            
            # Check balance drop
            if len(self.metrics_history["account_balance"]) > 1:
                previous_balance = self.metrics_history["account_balance"][-2]
                current_balance = self.metrics_history["account_balance"][-1]
                
                if previous_balance > 0:
                    balance_drop_percent = (previous_balance - current_balance) / previous_balance * 100 if current_balance < previous_balance else 0
                    
                    if balance_drop_percent >= thresholds.get("balance_drop", 10.0):
                        self._create_alert(
                            "Balance Drop Alert",
                            f"Balance drop of {balance_drop_percent:.2f}% exceeds threshold of {thresholds.get('balance_drop', 10.0)}%",
                            "high"
                        )
            
            # Check system metrics
            cpu_usage = self.metrics.get("system", {}).get("cpu_percent", 0)
            memory_usage = self.metrics.get("system", {}).get("memory_percent", 0)
            api_latency = self.metrics.get("system", {}).get("api_latency", 0)
            
            if cpu_usage >= thresholds.get("cpu_usage", 90.0):
                self._create_alert(
                    "CPU Usage Alert",
                    f"CPU usage of {cpu_usage:.2f}% exceeds threshold of {thresholds.get('cpu_usage', 90.0)}%",
                    "medium"
                )
            
            if memory_usage >= thresholds.get("memory_usage", 90.0):
                self._create_alert(
                    "Memory Usage Alert",
                    f"Memory usage of {memory_usage:.2f}% exceeds threshold of {thresholds.get('memory_usage', 90.0)}%",
                    "medium"
                )
            
            if api_latency >= thresholds.get("api_latency", 2000):
                self._create_alert(
                    "API Latency Alert",
                    f"API latency of {api_latency:.2f}ms exceeds threshold of {thresholds.get('api_latency', 2000)}ms",
                    "medium"
                )
            
            # Check emergency protocol
            if self.metrics.get("emergency", {}).get("active", False):
                status = self.metrics.get("emergency", {}).get("status", "")
                message = self.metrics.get("emergency", {}).get("message", "")
                
                self._create_alert(
                    "Emergency Protocol Alert",
                    f"Emergency protocol is active: {status} - {message}",
                    "critical"
                )
        except Exception as e:
            logger.error(f"Error checking alert conditions: {e}")
    
    def _get_consecutive_losses(self) -> int:
        """Get the number of consecutive losses
        
        Returns:
            int: Number of consecutive losses
        """
        try:
            # Get order history from live trading
            live_trading = self.components["live_trading"]
            order_history = live_trading.get_order_history(limit=100)
            
            # Count consecutive losses
            consecutive_losses = 0
            
            for order in order_history:
                profit = order.get("profit", 0)
                
                if profit < 0:
                    consecutive_losses += 1
                else:
                    break
            
            return consecutive_losses
        except Exception as e:
            logger.error(f"Error getting consecutive losses: {e}")
            return 0
    
    def _create_alert(self, title: str, message: str, severity: str):
        """Create an alert
        
        Args:
            title: Alert title
            message: Alert message
            severity: Alert severity (low, medium, high, critical)
        """
        try:
            # Check if alert is in cooldown
            current_time = datetime.now()
            cooldown_key = f"{title}_{severity}"
            
            if cooldown_key in self.alert_cooldown:
                last_alert_time = self.alert_cooldown[cooldown_key]
                cooldown_period = self.config.get("alert_cooldown", 1800)  # Default: 30 minutes
                
                if (current_time - last_alert_time).total_seconds() < cooldown_period:
                    logger.info(f"Alert '{title}' is in cooldown, skipping")
                    return
            
            # Create alert
            alert = {
                "id": len(self.alerts) + 1,
                "timestamp": current_time.isoformat(),
                "title": title,
                "message": message,
                "severity": severity
            }
            
            # Add to alerts list
            self.alerts.append(alert)
            
            # Update cooldown
            self.alert_cooldown[cooldown_key] = current_time
            
            # Log alert
            log_message = f"ALERT [{severity.upper()}]: {title} - {message}"
            
            if severity == "critical":
                logger.critical(log_message)
            elif severity == "high":
                logger.error(log_message)
            elif severity == "medium":
                logger.warning(log_message)
            else:
                logger.info(log_message)
            
            # Send notifications
            self._send_alert_notifications(alert)
            
            # Save alerts to file
            self._save_alerts()
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
    
    def _send_alert_notifications(self, alert: Dict):
        """Send alert notifications
        
        Args:
            alert: Alert data
        """
        try:
            # Get notification config
            notifications = self.config.get("notifications", {})
            
            # Send Slack notification
            slack_config = notifications.get("slack", {})
            
            if slack_config.get("enabled", False) and slack_config.get("webhook_url"):
                self._send_slack_notification(alert, slack_config["webhook_url"])
            
            # Send email notification
            email_config = notifications.get("email", {})
            
            if email_config.get("enabled", False) and email_config.get("recipient"):
                self._send_email_notification(alert, email_config)
        except Exception as e:
            logger.error(f"Error sending alert notifications: {e}")
    
    def _send_slack_notification(self, alert: Dict, webhook_url: str):
        """Send Slack notification
        
        Args:
            alert: Alert data
            webhook_url: Slack webhook URL
        """
        try:
            # Create Slack message
            severity_emoji = {
                "low": ":information_source:",
                "medium": ":warning:",
                "high": ":rotating_light:",
                "critical": ":sos:"
            }
            
            emoji = severity_emoji.get(alert["severity"], ":information_source:")
            
            message = {
                "text": f"{emoji} *{alert['title']}*",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"{emoji} *{alert['title']}*\n{alert['message']}"
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Severity:* {alert['severity'].upper()} | *Time:* {alert['timestamp']}"
                            }
                        ]
                    }
                ]
            }
            
            # Send to Slack
            response = requests.post(
                webhook_url,
                json=message,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                logger.error(f"Error sending Slack notification: {response.text}")
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
    
    def _send_email_notification(self, alert: Dict, email_config: Dict):
        """Send email notification
        
        Args:
            alert: Alert data
            email_config: Email configuration
        """
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Create email message
            msg = MIMEMultipart()
            msg["From"] = email_config["sender"]
            msg["To"] = email_config["recipient"]
            msg["Subject"] = f"[{alert['severity'].upper()}] {alert['title']}"
            
            body = f"{alert['message']}\n\nSeverity: {alert['severity'].upper()}\nTime: {alert['timestamp']}"
            msg.attach(MIMEText(body, "plain"))
            
            # Send email
            server = smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"])
            server.starttls()
            server.login(email_config["username"], email_config["password"])
            server.send_message(msg)
            server.quit()
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
    
    def _save_alerts(self):
        """Save alerts to file"""
        try:
            # Save to JSON
            file_path = os.path.join("data", "monitoring", "alerts.json")
            
            with open(file_path, "w") as f:
                json.dump(self.alerts, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving alerts: {e}")
    
    def get_metrics(self) -> Dict:
        """Get current metrics
        
        Returns:
            Dict: Current metrics
        """
        return self.metrics
    
    def get_alerts(self, limit: int = 100, severity: Optional[str] = None) -> List[Dict]:
        """Get alerts
        
        Args:
            limit: Maximum number of alerts to return
            severity: Filter by severity (low, medium, high, critical)
            
        Returns:
            List[Dict]: Alerts
        """
        # Filter by severity if specified
        if severity:
            filtered_alerts = [alert for alert in self.alerts if alert["severity"] == severity]
        else:
            filtered_alerts = self.alerts
        
        # Sort by timestamp (newest first) and limit
        return sorted(
            filtered_alerts,
            key=lambda a: a["timestamp"],
            reverse=True
        )[:limit]
    
    def get_metrics_history(self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> Dict:
        """Get metrics history
        
        Args:
            start_time: Start time filter
            end_time: End time filter
            
        Returns:
            Dict: Metrics history
        """
        try:
            # Convert to DataFrame for easier filtering
            df = pd.DataFrame(self.metrics_history)
            
            # Apply time filters if specified
            if start_time or end_time:
                # Convert timestamp to datetime if it's not already
                if not isinstance(df["timestamp"][0], datetime):
                    df["timestamp"] = pd.to_datetime(df["timestamp"])
                
                if start_time:
                    df = df[df["timestamp"] >= start_time]
                
                if end_time:
                    df = df[df["timestamp"] <= end_time]
            
            # Convert back to dict
            return df.to_dict(orient="list")
        except Exception as e:
            logger.error(f"Error getting metrics history: {e}")
            return self.metrics_history
    
    def get_system_status(self) -> Dict:
        """Get system status summary
        
        Returns:
            Dict: System status
        """
        try:
            # Get latest metrics
            latest_metrics = self.metrics
            
            # Check emergency protocol
            emergency_active = latest_metrics.get("emergency", {}).get("active", False)
            emergency_status = latest_metrics.get("emergency", {}).get("status", "")
            
            # Get trading stats
            trading_stats = latest_metrics.get("trading", {})
            
            # Get system metrics
            system_metrics = latest_metrics.get("system", {})
            
            # Determine overall status
            if emergency_active:
                overall_status = "critical"
            elif trading_stats.get("win_rate", 0) < 40 or latest_metrics.get("daily_pnl", 0) < 0:
                overall_status = "warning"
            else:
                overall_status = "normal"
            
            return {
                "timestamp": datetime.now().isoformat(),
                "overall_status": overall_status,
                "emergency": {
                    "active": emergency_active,
                    "status": emergency_status
                },
                "trading": {
                    "active_orders": latest_metrics.get("active_orders", 0),
                    "daily_pnl": latest_metrics.get("daily_pnl", 0),
                    "win_rate": trading_stats.get("win_rate", 0),
                    "total_trades": trading_stats.get("total_trades", 0)
                },
                "system": {
                    "cpu_percent": system_metrics.get("cpu_percent", 0),
                    "memory_percent": system_metrics.get("memory_percent", 0),
                    "api_latency": system_metrics.get("api_latency", 0)
                },
                "alerts": len(self.get_alerts(limit=10))
            }
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "unknown",
                "error": str(e)
            }

# Main function to run the monitoring system
def main():
    """Main function to run the monitoring system"""
    logger.info("Starting monitoring system")
    
    # Create monitoring system instance
    monitoring_system = MonitoringSystem()
    
    # Start monitoring
    monitoring_system.start_monitoring()
    
    try:
        # Keep running until interrupted
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping monitoring system")
        monitoring_system.stop_monitoring()

# Run the monitoring system if this script is executed directly
if __name__ == "__main__":
    main()