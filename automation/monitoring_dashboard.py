#!/usr/bin/env python3
"""
TradeBot Sentinel Pro - Monitoring Dashboard Module
Real-time monitoring dashboard with CLI and web interface for trade tracking
"""

import asyncio
import json
import logging
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import os
import sys
from collections import defaultdict, deque

# Web interface imports (optional)
try:
    from flask import Flask, render_template, jsonify, request
    from flask_socketio import SocketIO, emit
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    logging.warning("Flask not available, web interface disabled")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/monitoring_dashboard.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class DashboardMetrics:
    """Dashboard metrics data structure"""
    timestamp: str
    active_trades: int
    pending_trades: int
    completed_trades: int
    success_rate: float
    total_volume: float
    daily_pnl: float
    system_status: str
    last_trade_time: Optional[str]
    error_count: int
    network_requests: int

@dataclass
class TradeAlert:
    """Trade alert data structure"""
    id: str
    timestamp: str
    type: str  # success, failure, warning, info
    message: str
    trade_id: Optional[str]
    symbol: Optional[str]
    amount: Optional[float]

class MonitoringDashboard:
    """Real-time monitoring dashboard for TradeBot Sentinel Pro"""
    
    def __init__(self, config_path: str = "automation/config/dashboard.json"):
        self.config_path = Path(config_path)
        self.config = self.load_config()
        self.db_path = Path("logs/trades.db")
        self.metrics_history: deque = deque(maxlen=1000)  # Keep last 1000 metrics
        self.alerts: deque = deque(maxlen=100)  # Keep last 100 alerts
        self.running = False
        self.update_interval = self.config.get('update_interval_seconds', 5)
        
        # Web interface setup
        self.app = None
        self.socketio = None
        if FLASK_AVAILABLE and self.config.get('enable_web_interface', True):
            self.setup_web_interface()
        
        # CLI interface setup
        self.cli_enabled = self.config.get('enable_cli_interface', True)
        
        logger.info("MonitoringDashboard initialized")
    
    def load_config(self) -> Dict[str, Any]:
        """Load dashboard configuration"""
        default_config = {
            "update_interval_seconds": 5,
            "enable_web_interface": True,
            "enable_cli_interface": True,
            "web_port": 5000,
            "web_host": "127.0.0.1",
            "max_alerts": 100,
            "max_metrics_history": 1000,
            "alert_thresholds": {
                "error_rate_percent": 10,
                "response_time_seconds": 30,
                "daily_loss_threshold": 1000
            },
            "display_settings": {
                "refresh_rate_ms": 1000,
                "chart_timeframe_hours": 24,
                "show_debug_info": False
            }
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    default_config.update(config)
                    logger.info(f"Dashboard configuration loaded from {self.config_path}")
            except Exception as e:
                logger.error(f"Error loading dashboard config: {e}, using defaults")
        else:
            # Create default config file
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"Default dashboard configuration created at {self.config_path}")
        
        return default_config
    
    def setup_web_interface(self):
        """Setup Flask web interface"""
        try:
            self.app = Flask(__name__, template_folder='templates')
            self.app.config['SECRET_KEY'] = 'tradebot_sentinel_pro_dashboard'
            self.socketio = SocketIO(self.app, cors_allowed_origins="*")
            
            # Create templates directory
            templates_dir = Path('automation/templates')
            templates_dir.mkdir(parents=True, exist_ok=True)
            
            # Create dashboard template if it doesn't exist
            dashboard_template = templates_dir / 'dashboard.html'
            if not dashboard_template.exists():
                self.create_dashboard_template(dashboard_template)
            
            # Setup routes
            self.setup_web_routes()
            
            logger.info("Web interface setup complete")
            
        except Exception as e:
            logger.error(f"Error setting up web interface: {e}")
            self.app = None
            self.socketio = None
    
    def create_dashboard_template(self, template_path: Path):
        """Create HTML template for dashboard"""
        html_content = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TradeBot Sentinel Pro - Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #1a1a1a;
            color: #ffffff;
        }
        .dashboard-container {
            max-width: 1400px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .metric-card {
            background: #2d2d2d;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        .metric-label {
            color: #cccccc;
            margin-top: 5px;
        }
        .charts-container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }
        .chart-card {
            background: #2d2d2d;
            padding: 20px;
            border-radius: 10px;
        }
        .alerts-container {
            background: #2d2d2d;
            padding: 20px;
            border-radius: 10px;
            max-height: 400px;
            overflow-y: auto;
        }
        .alert-item {
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            border-left: 4px solid;
        }
        .alert-success { border-left-color: #28a745; background: rgba(40, 167, 69, 0.1); }
        .alert-warning { border-left-color: #ffc107; background: rgba(255, 193, 7, 0.1); }
        .alert-error { border-left-color: #dc3545; background: rgba(220, 53, 69, 0.1); }
        .alert-info { border-left-color: #17a2b8; background: rgba(23, 162, 184, 0.1); }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-online { background-color: #28a745; }
        .status-offline { background-color: #dc3545; }
        .status-warning { background-color: #ffc107; }
    </style>
</head>
<body>
    <div class="dashboard-container">
        <div class="header">
            <h1>🤖 TradeBot Sentinel Pro Dashboard</h1>
            <p>Real-time monitoring and analytics</p>
            <div>
                <span class="status-indicator" id="statusIndicator"></span>
                <span id="systemStatus">Connecting...</span>
            </div>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value" id="activeTrades">0</div>
                <div class="metric-label">Active Trades</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="pendingTrades">0</div>
                <div class="metric-label">Pending Trades</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="completedTrades">0</div>
                <div class="metric-label">Completed Trades</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="successRate">0%</div>
                <div class="metric-label">Success Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="totalVolume">$0</div>
                <div class="metric-label">Total Volume</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="dailyPnl">$0</div>
                <div class="metric-label">Daily P&L</div>
            </div>
        </div>
        
        <div class="charts-container">
            <div class="chart-card">
                <h3>Trade Volume Over Time</h3>
                <canvas id="volumeChart" width="400" height="200"></canvas>
            </div>
            <div class="chart-card">
                <h3>Success Rate Trend</h3>
                <canvas id="successChart" width="400" height="200"></canvas>
            </div>
        </div>
        
        <div class="alerts-container">
            <h3>Recent Alerts</h3>
            <div id="alertsList"></div>
        </div>
    </div>
    
    <script>
        const socket = io();
        let volumeChart, successChart;
        
        // Initialize charts
        function initCharts() {
            const volumeCtx = document.getElementById('volumeChart').getContext('2d');
            volumeChart = new Chart(volumeCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Volume',
                        data: [],
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { labels: { color: '#ffffff' } } },
                    scales: {
                        x: { ticks: { color: '#ffffff' } },
                        y: { ticks: { color: '#ffffff' } }
                    }
                }
            });
            
            const successCtx = document.getElementById('successChart').getContext('2d');
            successChart = new Chart(successCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Success Rate %',
                        data: [],
                        borderColor: '#28a745',
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { labels: { color: '#ffffff' } } },
                    scales: {
                        x: { ticks: { color: '#ffffff' } },
                        y: { ticks: { color: '#ffffff' }, min: 0, max: 100 }
                    }
                }
            });
        }
        
        // Update metrics display
        function updateMetrics(metrics) {
            document.getElementById('activeTrades').textContent = metrics.active_trades;
            document.getElementById('pendingTrades').textContent = metrics.pending_trades;
            document.getElementById('completedTrades').textContent = metrics.completed_trades;
            document.getElementById('successRate').textContent = metrics.success_rate.toFixed(1) + '%';
            document.getElementById('totalVolume').textContent = '$' + metrics.total_volume.toLocaleString();
            document.getElementById('dailyPnl').textContent = '$' + metrics.daily_pnl.toLocaleString();
            
            // Update system status
            const statusIndicator = document.getElementById('statusIndicator');
            const systemStatus = document.getElementById('systemStatus');
            
            if (metrics.system_status === 'online') {
                statusIndicator.className = 'status-indicator status-online';
                systemStatus.textContent = 'System Online';
            } else if (metrics.system_status === 'warning') {
                statusIndicator.className = 'status-indicator status-warning';
                systemStatus.textContent = 'System Warning';
            } else {
                statusIndicator.className = 'status-indicator status-offline';
                systemStatus.textContent = 'System Offline';
            }
        }
        
        // Update charts
        function updateCharts(metrics) {
            const time = new Date(metrics.timestamp).toLocaleTimeString();
            
            // Volume chart
            volumeChart.data.labels.push(time);
            volumeChart.data.datasets[0].data.push(metrics.total_volume);
            if (volumeChart.data.labels.length > 20) {
                volumeChart.data.labels.shift();
                volumeChart.data.datasets[0].data.shift();
            }
            volumeChart.update('none');
            
            // Success rate chart
            successChart.data.labels.push(time);
            successChart.data.datasets[0].data.push(metrics.success_rate);
            if (successChart.data.labels.length > 20) {
                successChart.data.labels.shift();
                successChart.data.datasets[0].data.shift();
            }
            successChart.update('none');
        }
        
        // Update alerts
        function updateAlerts(alerts) {
            const alertsList = document.getElementById('alertsList');
            alertsList.innerHTML = '';
            
            alerts.forEach(alert => {
                const alertDiv = document.createElement('div');
                alertDiv.className = `alert-item alert-${alert.type}`;
                alertDiv.innerHTML = `
                    <div><strong>${new Date(alert.timestamp).toLocaleString()}</strong></div>
                    <div>${alert.message}</div>
                    ${alert.symbol ? `<div><small>Symbol: ${alert.symbol}, Amount: ${alert.amount}</small></div>` : ''}
                `;
                alertsList.appendChild(alertDiv);
            });
        }
        
        // Socket event handlers
        socket.on('connect', function() {
            console.log('Connected to dashboard');
        });
        
        socket.on('metrics_update', function(data) {
            updateMetrics(data.metrics);
            updateCharts(data.metrics);
        });
        
        socket.on('alerts_update', function(data) {
            updateAlerts(data.alerts);
        });
        
        // Initialize on page load
        document.addEventListener('DOMContentLoaded', function() {
            initCharts();
        });
    </script>
</body>
</html>
        '''
        
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Dashboard template created at {template_path}")
    
    def setup_web_routes(self):
        """Setup Flask routes"""
        @self.app.route('/')
        def dashboard():
            return render_template('dashboard.html')
        
        @self.app.route('/api/metrics')
        def get_metrics():
            metrics = self.get_current_metrics()
            return jsonify(metrics)
        
        @self.app.route('/api/alerts')
        def get_alerts():
            alerts = [asdict(alert) for alert in list(self.alerts)]
            return jsonify(alerts)
        
        @self.app.route('/api/trades')
        def get_trades():
            trades = self.get_recent_trades()
            return jsonify(trades)
        
        @self.socketio.on('connect')
        def handle_connect():
            logger.info('Client connected to dashboard')
            # Send initial data
            metrics = self.get_current_metrics()
            alerts = [asdict(alert) for alert in list(self.alerts)]
            emit('metrics_update', {'metrics': asdict(metrics)})
            emit('alerts_update', {'alerts': alerts})
    
    def get_current_metrics(self) -> DashboardMetrics:
        """Get current dashboard metrics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get trade counts
                cursor = conn.execute("""
                    SELECT 
                        COUNT(CASE WHEN status = 'executing' THEN 1 END) as active,
                        COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
                        COUNT(CASE WHEN status = 'success' THEN 1 END) as completed,
                        COUNT(*) as total,
                        SUM(CASE WHEN status = 'success' THEN amount ELSE 0 END) as volume
                    FROM trades
                    WHERE date(timestamp) = date('now')
                """)
                
                row = cursor.fetchone()
                active_trades = row[0] if row[0] else 0
                pending_trades = row[1] if row[1] else 0
                completed_trades = row[2] if row[2] else 0
                total_trades = row[3] if row[3] else 0
                total_volume = row[4] if row[4] else 0.0
                
                # Calculate success rate
                success_rate = (completed_trades / total_trades * 100) if total_trades > 0 else 0
                
                # Get last trade time
                cursor = conn.execute(
                    "SELECT timestamp FROM trades ORDER BY timestamp DESC LIMIT 1"
                )
                last_trade_row = cursor.fetchone()
                last_trade_time = last_trade_row[0] if last_trade_row else None
                
                # Get error count
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM trades WHERE status = 'failed' AND date(timestamp) = date('now')"
                )
                error_count = cursor.fetchone()[0]
                
                # Determine system status
                system_status = "online"
                if error_count > 5:
                    system_status = "warning"
                elif not self.running:
                    system_status = "offline"
                
                # Count network requests (from logs/curls directory)
                curls_dir = Path('logs/curls')
                network_requests = len(list(curls_dir.glob('*.sh'))) if curls_dir.exists() else 0
                
                return DashboardMetrics(
                    timestamp=datetime.now().isoformat(),
                    active_trades=active_trades,
                    pending_trades=pending_trades,
                    completed_trades=completed_trades,
                    success_rate=success_rate,
                    total_volume=total_volume,
                    daily_pnl=0.0,  # TODO: Calculate actual P&L
                    system_status=system_status,
                    last_trade_time=last_trade_time,
                    error_count=error_count,
                    network_requests=network_requests
                )
                
        except Exception as e:
            logger.error(f"Error getting current metrics: {e}")
            return DashboardMetrics(
                timestamp=datetime.now().isoformat(),
                active_trades=0,
                pending_trades=0,
                completed_trades=0,
                success_rate=0.0,
                total_volume=0.0,
                daily_pnl=0.0,
                system_status="offline",
                last_trade_time=None,
                error_count=0,
                network_requests=0
            )
    
    def get_recent_trades(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent trades from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT id, symbol, action, amount, price, order_type, strategy, 
                           timestamp, status, attempts, execution_time, last_error
                    FROM trades 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (limit,))
                
                trades = []
                for row in cursor.fetchall():
                    trades.append({
                        'id': row[0],
                        'symbol': row[1],
                        'action': row[2],
                        'amount': row[3],
                        'price': row[4],
                        'order_type': row[5],
                        'strategy': row[6],
                        'timestamp': row[7],
                        'status': row[8],
                        'attempts': row[9],
                        'execution_time': row[10],
                        'last_error': row[11]
                    })
                
                return trades
                
        except Exception as e:
            logger.error(f"Error getting recent trades: {e}")
            return []
    
    def add_alert(self, alert_type: str, message: str, trade_id: Optional[str] = None, 
                  symbol: Optional[str] = None, amount: Optional[float] = None):
        """Add new alert to the dashboard"""
        alert = TradeAlert(
            id=f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]}",
            timestamp=datetime.now().isoformat(),
            type=alert_type,
            message=message,
            trade_id=trade_id,
            symbol=symbol,
            amount=amount
        )
        
        self.alerts.appendleft(alert)  # Add to front
        
        # Emit to web clients if available
        if self.socketio:
            alerts = [asdict(alert) for alert in list(self.alerts)]
            self.socketio.emit('alerts_update', {'alerts': alerts})
        
        logger.info(f"Alert added: {alert_type} - {message}")
    
    def display_cli_dashboard(self):
        """Display CLI dashboard"""
        if not self.cli_enabled:
            return
        
        try:
            # Clear screen
            os.system('cls' if os.name == 'nt' else 'clear')
            
            # Get current metrics
            metrics = self.get_current_metrics()
            
            # Display header
            print("\n" + "="*80)
            print("🤖 TRADEBOT SENTINEL PRO - MONITORING DASHBOARD")
            print("="*80)
            print(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"System Status: {metrics.system_status.upper()}")
            print("="*80)
            
            # Display metrics
            print("\n📊 TRADING METRICS:")
            print("-"*40)
            print(f"Active Trades:     {metrics.active_trades:>10}")
            print(f"Pending Trades:    {metrics.pending_trades:>10}")
            print(f"Completed Trades:  {metrics.completed_trades:>10}")
            print(f"Success Rate:      {metrics.success_rate:>9.1f}%")
            print(f"Total Volume:      ${metrics.total_volume:>9,.2f}")
            print(f"Daily P&L:         ${metrics.daily_pnl:>9,.2f}")
            print(f"Network Requests:  {metrics.network_requests:>10}")
            print(f"Error Count:       {metrics.error_count:>10}")
            
            # Display recent alerts
            print("\n🚨 RECENT ALERTS:")
            print("-"*40)
            recent_alerts = list(self.alerts)[:5]  # Show last 5 alerts
            if recent_alerts:
                for alert in recent_alerts:
                    timestamp = datetime.fromisoformat(alert.timestamp).strftime('%H:%M:%S')
                    print(f"[{timestamp}] {alert.type.upper()}: {alert.message}")
            else:
                print("No recent alerts")
            
            # Display recent trades
            print("\n💼 RECENT TRADES:")
            print("-"*80)
            recent_trades = self.get_recent_trades(5)
            if recent_trades:
                print(f"{'ID':<15} {'Symbol':<8} {'Action':<6} {'Amount':<10} {'Status':<10} {'Time':<19}")
                print("-"*80)
                for trade in recent_trades:
                    trade_time = datetime.fromisoformat(trade['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                    print(f"{trade['id'][:14]:<15} {trade['symbol']:<8} {trade['action']:<6} "
                          f"{trade['amount']:<10.2f} {trade['status']:<10} {trade_time}")
            else:
                print("No recent trades")
            
            print("\n" + "="*80)
            print("Press Ctrl+C to exit dashboard")
            print("="*80)
            
        except Exception as e:
            logger.error(f"Error displaying CLI dashboard: {e}")
    
    async def start_monitoring(self):
        """Start monitoring dashboard"""
        self.running = True
        logger.info("Monitoring dashboard started")
        
        # Start web interface if enabled
        if self.app and self.socketio:
            web_thread = threading.Thread(
                target=lambda: self.socketio.run(
                    self.app, 
                    host=self.config.get('web_host', '127.0.0.1'),
                    port=self.config.get('web_port', 5000),
                    debug=False
                )
            )
            web_thread.daemon = True
            web_thread.start()
            logger.info(f"Web dashboard started at http://{self.config.get('web_host', '127.0.0.1')}:{self.config.get('web_port', 5000)}")
        
        # Main monitoring loop
        while self.running:
            try:
                # Get current metrics
                metrics = self.get_current_metrics()
                self.metrics_history.appendleft(metrics)
                
                # Update web clients
                if self.socketio:
                    self.socketio.emit('metrics_update', {'metrics': asdict(metrics)})
                
                # Display CLI dashboard
                if self.cli_enabled:
                    self.display_cli_dashboard()
                
                # Check for alerts
                await self.check_alert_conditions(metrics)
                
                await asyncio.sleep(self.update_interval)
                
            except KeyboardInterrupt:
                logger.info("Dashboard interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)
    
    async def check_alert_conditions(self, metrics: DashboardMetrics):
        """Check for alert conditions and generate alerts"""
        try:
            thresholds = self.config.get('alert_thresholds', {})
            
            # Check error rate
            if metrics.completed_trades > 0:
                error_rate = (metrics.error_count / metrics.completed_trades) * 100
                if error_rate > thresholds.get('error_rate_percent', 10):
                    self.add_alert('warning', f'High error rate detected: {error_rate:.1f}%')
            
            # Check system status
            if metrics.system_status == 'offline':
                self.add_alert('error', 'System is offline')
            elif metrics.system_status == 'warning':
                self.add_alert('warning', 'System status warning')
            
            # Check for new trades
            if metrics.last_trade_time:
                last_trade = datetime.fromisoformat(metrics.last_trade_time)
                if datetime.now() - last_trade < timedelta(minutes=1):
                    self.add_alert('info', 'New trade detected')
            
        except Exception as e:
            logger.error(f"Error checking alert conditions: {e}")
    
    async def stop_monitoring(self):
        """Stop monitoring dashboard"""
        self.running = False
        logger.info("Monitoring dashboard stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get dashboard status"""
        return {
            'running': self.running,
            'web_interface_enabled': self.app is not None,
            'cli_interface_enabled': self.cli_enabled,
            'metrics_history_count': len(self.metrics_history),
            'alerts_count': len(self.alerts),
            'update_interval': self.update_interval
        }