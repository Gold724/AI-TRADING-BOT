#!/usr/bin/env python3
"""
TradeBot Sentinel - Real-Time Monitoring Dashboard

Provides comprehensive real-time monitoring and visualization of:
- System performance metrics
- Trading activity and execution status
- Network interception and API calls
- Session health and browser status
- Automated recovery actions
- Performance optimizations

Features:
- Web-based dashboard with live updates
- Interactive charts and graphs
- Alert notifications
- Historical data analysis
- Export capabilities
- Mobile-responsive design

Author: TradeBot Sentinel Team
Version: 1.0.0
Date: 2024
"""

import asyncio
import logging
import json
import time
import threading
import sqlite3
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import psutil
import subprocess
from collections import deque, defaultdict
import statistics
import traceback
from contextlib import asynccontextmanager

# Web framework imports
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
import plotly.graph_objs as go
import plotly.utils
from werkzeug.serving import make_server

# Data processing
import pandas as pd
import numpy as np
from scipy import stats

@dataclass
class DashboardMetric:
    """Dashboard metric data point"""
    timestamp: str
    category: str
    name: str
    value: float
    unit: str
    status: str  # 'normal', 'warning', 'critical'
    context: Dict[str, Any]

@dataclass
class TradeEvent:
    """Trading event for dashboard"""
    timestamp: str
    event_type: str  # 'order_placed', 'order_filled', 'error', 'network_intercept'
    symbol: str
    amount: float
    price: float
    status: str
    details: Dict[str, Any]

@dataclass
class SystemAlert:
    """System alert for dashboard"""
    timestamp: str
    severity: str  # 'info', 'warning', 'error', 'critical'
    category: str
    message: str
    component: str
    resolved: bool
    resolution_time: Optional[str] = None

class RealtimeDashboard:
    """Advanced real-time monitoring dashboard"""
    
    def __init__(self, port: int = 5000, debug: bool = False):
        self.port = port
        self.debug = debug
        self.logger = self._setup_logging()
        
        # Flask app setup
        self.app = Flask(__name__, 
                        template_folder='dashboard_templates',
                        static_folder='dashboard_static')
        self.app.config['SECRET_KEY'] = 'tradebot_sentinel_dashboard_2024'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode='threading')
        
        # Data storage
        self.metrics_buffer: deque = deque(maxlen=1000)
        self.trade_events: deque = deque(maxlen=500)
        self.system_alerts: deque = deque(maxlen=200)
        self.performance_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self.data_collection_interval = 5  # seconds
        
        # Database connections
        self.db_files = {
            'performance': 'performance_metrics.db',
            'trades': 'trade_history.db',
            'system': 'system_health.db'
        }
        
        # Component status tracking
        self.component_status = {
            'login_automation': {'status': 'unknown', 'last_check': None},
            'trade_capture': {'status': 'unknown', 'last_check': None},
            'network_monitor': {'status': 'unknown', 'last_check': None},
            'session_manager': {'status': 'unknown', 'last_check': None},
            'performance_optimizer': {'status': 'unknown', 'last_check': None},
            'recovery_system': {'status': 'unknown', 'last_check': None}
        }
        
        # Setup routes and socket handlers
        self._setup_routes()
        self._setup_socket_handlers()
        
        # Create dashboard templates and static files
        self._create_dashboard_files()
        
        self.logger.info("🖥️ Real-time Dashboard initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('RealtimeDashboard')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.FileHandler('dashboard.log')
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def dashboard():
            """Main dashboard page"""
            return render_template('dashboard.html')
        
        @self.app.route('/api/metrics')
        def get_metrics():
            """Get current metrics"""
            try:
                recent_metrics = list(self.metrics_buffer)[-50:]  # Last 50 metrics
                return jsonify({
                    'success': True,
                    'metrics': [asdict(m) for m in recent_metrics],
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/trades')
        def get_trades():
            """Get recent trade events"""
            try:
                recent_trades = list(self.trade_events)[-20:]  # Last 20 trades
                return jsonify({
                    'success': True,
                    'trades': [asdict(t) for t in recent_trades],
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/alerts')
        def get_alerts():
            """Get system alerts"""
            try:
                recent_alerts = list(self.system_alerts)[-30:]  # Last 30 alerts
                return jsonify({
                    'success': True,
                    'alerts': [asdict(a) for a in recent_alerts],
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/status')
        def get_system_status():
            """Get overall system status"""
            try:
                status = self._get_comprehensive_status()
                return jsonify({
                    'success': True,
                    'status': status,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/performance-chart')
        def get_performance_chart():
            """Get performance chart data"""
            try:
                chart_data = self._generate_performance_chart()
                return jsonify({
                    'success': True,
                    'chart': chart_data,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/export/<data_type>')
        def export_data(data_type):
            """Export data as CSV"""
            try:
                if data_type == 'metrics':
                    data = [asdict(m) for m in self.metrics_buffer]
                elif data_type == 'trades':
                    data = [asdict(t) for t in self.trade_events]
                elif data_type == 'alerts':
                    data = [asdict(a) for a in self.system_alerts]
                else:
                    return jsonify({'success': False, 'error': 'Invalid data type'})
                
                # Convert to CSV
                if data:
                    df = pd.DataFrame(data)
                    csv_data = df.to_csv(index=False)
                    
                    return {
                        'success': True,
                        'csv_data': csv_data,
                        'filename': f'{data_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
                    }
                else:
                    return jsonify({'success': False, 'error': 'No data available'})
                    
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
    
    def _setup_socket_handlers(self):
        """Setup SocketIO event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            self.logger.info("Client connected to dashboard")
            emit('status', {'message': 'Connected to TradeBot Sentinel Dashboard'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            self.logger.info("Client disconnected from dashboard")
        
        @self.socketio.on('request_update')
        def handle_update_request():
            """Handle manual update request"""
            try:
                # Send latest data
                self._broadcast_updates()
            except Exception as e:
                emit('error', {'message': f'Update failed: {str(e)}'})
        
        @self.socketio.on('toggle_monitoring')
        def handle_toggle_monitoring():
            """Toggle monitoring on/off"""
            try:
                if self.monitoring_active:
                    self.stop_monitoring()
                    emit('status', {'message': 'Monitoring stopped'})
                else:
                    self.start_monitoring()
                    emit('status', {'message': 'Monitoring started'})
            except Exception as e:
                emit('error', {'message': f'Toggle failed: {str(e)}'})
    
    def _create_dashboard_files(self):
        """Create dashboard HTML templates and static files"""
        try:
            # Create directories
            Path('dashboard_templates').mkdir(exist_ok=True)
            Path('dashboard_static').mkdir(exist_ok=True)
            Path('dashboard_static/css').mkdir(exist_ok=True)
            Path('dashboard_static/js').mkdir(exist_ok=True)
            
            # Create main dashboard HTML
            dashboard_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TradeBot Sentinel - Real-Time Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <link href="{{ url_for('static', filename='css/dashboard.css') }}" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container-fluid">
            <span class="navbar-brand mb-0 h1">
                <i class="fas fa-robot"></i> TradeBot Sentinel Dashboard
            </span>
            <div class="d-flex">
                <span id="connection-status" class="badge bg-secondary me-2">Connecting...</span>
                <button id="toggle-monitoring" class="btn btn-sm btn-outline-light">
                    <i class="fas fa-play"></i> Start Monitoring
                </button>
            </div>
        </div>
    </nav>

    <div class="container-fluid mt-3">
        <!-- System Status Cards -->
        <div class="row mb-4">
            <div class="col-md-2">
                <div class="card text-center status-card" id="login-status">
                    <div class="card-body">
                        <i class="fas fa-sign-in-alt fa-2x mb-2"></i>
                        <h6>Login System</h6>
                        <span class="badge bg-secondary">Unknown</span>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card text-center status-card" id="trade-status">
                    <div class="card-body">
                        <i class="fas fa-chart-line fa-2x mb-2"></i>
                        <h6>Trade Capture</h6>
                        <span class="badge bg-secondary">Unknown</span>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card text-center status-card" id="network-status">
                    <div class="card-body">
                        <i class="fas fa-network-wired fa-2x mb-2"></i>
                        <h6>Network Monitor</h6>
                        <span class="badge bg-secondary">Unknown</span>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card text-center status-card" id="session-status">
                    <div class="card-body">
                        <i class="fas fa-clock fa-2x mb-2"></i>
                        <h6>Session Manager</h6>
                        <span class="badge bg-secondary">Unknown</span>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card text-center status-card" id="performance-status">
                    <div class="card-body">
                        <i class="fas fa-tachometer-alt fa-2x mb-2"></i>
                        <h6>Performance</h6>
                        <span class="badge bg-secondary">Unknown</span>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card text-center status-card" id="recovery-status">
                    <div class="card-body">
                        <i class="fas fa-shield-alt fa-2x mb-2"></i>
                        <h6>Recovery System</h6>
                        <span class="badge bg-secondary">Unknown</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Main Content -->
        <div class="row">
            <!-- Performance Chart -->
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-area"></i> System Performance</h5>
                    </div>
                    <div class="card-body">
                        <div id="performance-chart" style="height: 400px;"></div>
                    </div>
                </div>
            </div>

            <!-- System Metrics -->
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-info-circle"></i> Current Metrics</h5>
                    </div>
                    <div class="card-body" id="current-metrics">
                        <div class="text-center text-muted">
                            <i class="fas fa-spinner fa-spin"></i> Loading metrics...
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Trade Events and Alerts -->
        <div class="row mt-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header d-flex justify-content-between">
                        <h5><i class="fas fa-exchange-alt"></i> Recent Trades</h5>
                        <button class="btn btn-sm btn-outline-primary" onclick="exportData('trades')">
                            <i class="fas fa-download"></i> Export
                        </button>
                    </div>
                    <div class="card-body">
                        <div id="trade-events" style="max-height: 300px; overflow-y: auto;">
                            <div class="text-center text-muted">
                                <i class="fas fa-spinner fa-spin"></i> Loading trades...
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="col-md-6">
                <div class="card">
                    <div class="card-header d-flex justify-content-between">
                        <h5><i class="fas fa-exclamation-triangle"></i> System Alerts</h5>
                        <button class="btn btn-sm btn-outline-primary" onclick="exportData('alerts')">
                            <i class="fas fa-download"></i> Export
                        </button>
                    </div>
                    <div class="card-body">
                        <div id="system-alerts" style="max-height: 300px; overflow-y: auto;">
                            <div class="text-center text-muted">
                                <i class="fas fa-spinner fa-spin"></i> Loading alerts...
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="{{ url_for('static', filename='js/dashboard.js') }}"></script>
</body>
</html>
            '''
            
            with open('dashboard_templates/dashboard.html', 'w') as f:
                f.write(dashboard_html)
            
            # Create CSS file
            dashboard_css = '''
.status-card {
    transition: all 0.3s ease;
    border-left: 4px solid #6c757d;
}

.status-card.status-healthy {
    border-left-color: #28a745;
}

.status-card.status-warning {
    border-left-color: #ffc107;
}

.status-card.status-critical {
    border-left-color: #dc3545;
}

.status-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.metric-item {
    padding: 8px 0;
    border-bottom: 1px solid #eee;
}

.metric-item:last-child {
    border-bottom: none;
}

.trade-event {
    padding: 10px;
    margin-bottom: 8px;
    border-radius: 5px;
    border-left: 4px solid #007bff;
}

.trade-event.success {
    background-color: #d4edda;
    border-left-color: #28a745;
}

.trade-event.error {
    background-color: #f8d7da;
    border-left-color: #dc3545;
}

.alert-item {
    padding: 10px;
    margin-bottom: 8px;
    border-radius: 5px;
}

.alert-item.severity-info {
    background-color: #d1ecf1;
    border-left: 4px solid #17a2b8;
}

.alert-item.severity-warning {
    background-color: #fff3cd;
    border-left: 4px solid #ffc107;
}

.alert-item.severity-error {
    background-color: #f8d7da;
    border-left: 4px solid #dc3545;
}

.alert-item.severity-critical {
    background-color: #f5c6cb;
    border-left: 4px solid #721c24;
}

#connection-status.connected {
    background-color: #28a745 !important;
}

#connection-status.disconnected {
    background-color: #dc3545 !important;
}

.fade-in {
    animation: fadeIn 0.5s ease-in;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
            '''
            
            with open('dashboard_static/css/dashboard.css', 'w') as f:
                f.write(dashboard_css)
            
            # Create JavaScript file
            dashboard_js = '''
class DashboardManager {
    constructor() {
        this.socket = io();
        this.monitoringActive = false;
        this.setupSocketHandlers();
        this.setupEventHandlers();
        this.startDataRefresh();
    }

    setupSocketHandlers() {
        this.socket.on('connect', () => {
            console.log('Connected to dashboard');
            document.getElementById('connection-status').textContent = 'Connected';
            document.getElementById('connection-status').className = 'badge bg-success connected';
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from dashboard');
            document.getElementById('connection-status').textContent = 'Disconnected';
            document.getElementById('connection-status').className = 'badge bg-danger disconnected';
        });

        this.socket.on('metrics_update', (data) => {
            this.updateMetrics(data);
        });

        this.socket.on('trade_update', (data) => {
            this.updateTrades(data);
        });

        this.socket.on('alert_update', (data) => {
            this.updateAlerts(data);
        });

        this.socket.on('status_update', (data) => {
            this.updateSystemStatus(data);
        });
    }

    setupEventHandlers() {
        document.getElementById('toggle-monitoring').addEventListener('click', () => {
            this.toggleMonitoring();
        });
    }

    toggleMonitoring() {
        this.socket.emit('toggle_monitoring');
        this.monitoringActive = !this.monitoringActive;
        
        const button = document.getElementById('toggle-monitoring');
        if (this.monitoringActive) {
            button.innerHTML = '<i class="fas fa-stop"></i> Stop Monitoring';
            button.className = 'btn btn-sm btn-outline-danger';
        } else {
            button.innerHTML = '<i class="fas fa-play"></i> Start Monitoring';
            button.className = 'btn btn-sm btn-outline-light';
        }
    }

    startDataRefresh() {
        // Refresh data every 5 seconds
        setInterval(() => {
            this.refreshAllData();
        }, 5000);
        
        // Initial load
        this.refreshAllData();
    }

    async refreshAllData() {
        try {
            await Promise.all([
                this.loadMetrics(),
                this.loadTrades(),
                this.loadAlerts(),
                this.loadSystemStatus(),
                this.loadPerformanceChart()
            ]);
        } catch (error) {
            console.error('Data refresh failed:', error);
        }
    }

    async loadMetrics() {
        try {
            const response = await fetch('/api/metrics');
            const data = await response.json();
            if (data.success) {
                this.updateMetrics(data.metrics);
            }
        } catch (error) {
            console.error('Failed to load metrics:', error);
        }
    }

    async loadTrades() {
        try {
            const response = await fetch('/api/trades');
            const data = await response.json();
            if (data.success) {
                this.updateTrades(data.trades);
            }
        } catch (error) {
            console.error('Failed to load trades:', error);
        }
    }

    async loadAlerts() {
        try {
            const response = await fetch('/api/alerts');
            const data = await response.json();
            if (data.success) {
                this.updateAlerts(data.alerts);
            }
        } catch (error) {
            console.error('Failed to load alerts:', error);
        }
    }

    async loadSystemStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            if (data.success) {
                this.updateSystemStatus(data.status);
            }
        } catch (error) {
            console.error('Failed to load system status:', error);
        }
    }

    async loadPerformanceChart() {
        try {
            const response = await fetch('/api/performance-chart');
            const data = await response.json();
            if (data.success) {
                this.updatePerformanceChart(data.chart);
            }
        } catch (error) {
            console.error('Failed to load performance chart:', error);
        }
    }

    updateMetrics(metrics) {
        const container = document.getElementById('current-metrics');
        if (!metrics || metrics.length === 0) {
            container.innerHTML = '<div class="text-muted">No metrics available</div>';
            return;
        }

        // Get latest metrics by category
        const latestMetrics = {};
        metrics.forEach(metric => {
            if (!latestMetrics[metric.category] || 
                new Date(metric.timestamp) > new Date(latestMetrics[metric.category].timestamp)) {
                latestMetrics[metric.category] = metric;
            }
        });

        let html = '';
        Object.values(latestMetrics).forEach(metric => {
            const statusClass = metric.status === 'critical' ? 'text-danger' : 
                              metric.status === 'warning' ? 'text-warning' : 'text-success';
            
            html += `
                <div class="metric-item d-flex justify-content-between">
                    <span><strong>${metric.name}:</strong></span>
                    <span class="${statusClass}">${metric.value} ${metric.unit}</span>
                </div>
            `;
        });

        container.innerHTML = html;
    }

    updateTrades(trades) {
        const container = document.getElementById('trade-events');
        if (!trades || trades.length === 0) {
            container.innerHTML = '<div class="text-muted">No recent trades</div>';
            return;
        }

        let html = '';
        trades.slice(-10).reverse().forEach(trade => {
            const statusClass = trade.status === 'success' ? 'success' : 'error';
            const time = new Date(trade.timestamp).toLocaleTimeString();
            
            html += `
                <div class="trade-event ${statusClass} fade-in">
                    <div class="d-flex justify-content-between">
                        <strong>${trade.event_type}</strong>
                        <small>${time}</small>
                    </div>
                    <div>Symbol: ${trade.symbol} | Amount: ${trade.amount} | Price: ${trade.price}</div>
                    <small class="text-muted">${trade.status}</small>
                </div>
            `;
        });

        container.innerHTML = html;
    }

    updateAlerts(alerts) {
        const container = document.getElementById('system-alerts');
        if (!alerts || alerts.length === 0) {
            container.innerHTML = '<div class="text-muted">No recent alerts</div>';
            return;
        }

        let html = '';
        alerts.slice(-10).reverse().forEach(alert => {
            const time = new Date(alert.timestamp).toLocaleTimeString();
            const resolvedBadge = alert.resolved ? 
                '<span class="badge bg-success ms-2">Resolved</span>' : '';
            
            html += `
                <div class="alert-item severity-${alert.severity} fade-in">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <strong>${alert.category}</strong>${resolvedBadge}
                            <div>${alert.message}</div>
                            <small class="text-muted">${alert.component} - ${time}</small>
                        </div>
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
    }

    updateSystemStatus(status) {
        // Update component status cards
        Object.keys(status.components || {}).forEach(component => {
            const componentStatus = status.components[component];
            const card = document.getElementById(`${component.replace('_', '-')}-status`);
            
            if (card) {
                const badge = card.querySelector('.badge');
                const cardElement = card.querySelector('.card');
                
                // Update badge
                badge.textContent = componentStatus.status.charAt(0).toUpperCase() + 
                                  componentStatus.status.slice(1);
                
                // Update card styling
                cardElement.className = 'card text-center status-card';
                if (componentStatus.status === 'healthy') {
                    badge.className = 'badge bg-success';
                    cardElement.classList.add('status-healthy');
                } else if (componentStatus.status === 'warning') {
                    badge.className = 'badge bg-warning';
                    cardElement.classList.add('status-warning');
                } else if (componentStatus.status === 'critical') {
                    badge.className = 'badge bg-danger';
                    cardElement.classList.add('status-critical');
                } else {
                    badge.className = 'badge bg-secondary';
                }
            }
        });
    }

    updatePerformanceChart(chartData) {
        if (!chartData || !chartData.data) {
            return;
        }

        const layout = {
            title: 'System Performance Over Time',
            xaxis: { title: 'Time' },
            yaxis: { title: 'Value' },
            showlegend: true,
            margin: { t: 50, r: 50, b: 50, l: 50 }
        };

        Plotly.newPlot('performance-chart', chartData.data, layout, {
            responsive: true,
            displayModeBar: false
        });
    }
}

// Export function
function exportData(dataType) {
    fetch(`/api/export/${dataType}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const blob = new Blob([data.csv_data], { type: 'text/csv' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = data.filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            } else {
                alert('Export failed: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Export error:', error);
            alert('Export failed: ' + error.message);
        });
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new DashboardManager();
});
            '''
            
            with open('dashboard_static/js/dashboard.js', 'w') as f:
                f.write(dashboard_js)
            
            self.logger.info("✅ Dashboard files created successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to create dashboard files: {e}")
    
    def start_monitoring(self):
        """Start monitoring and data collection"""
        if self.monitoring_active:
            self.logger.warning("Dashboard monitoring already active")
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        self.logger.info("📊 Dashboard monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        self.logger.info("⏹️ Dashboard monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect system metrics
                metrics = self._collect_system_metrics()
                for metric in metrics:
                    self.metrics_buffer.append(metric)
                
                # Check component status
                self._update_component_status()
                
                # Load trade events from database
                self._load_trade_events()
                
                # Generate system alerts
                self._check_system_alerts()
                
                # Broadcast updates to connected clients
                self._broadcast_updates()
                
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
            
            time.sleep(self.data_collection_interval)
    
    def _collect_system_metrics(self) -> List[DashboardMetric]:
        """Collect current system metrics"""
        metrics = []
        timestamp = datetime.now().isoformat()
        
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Process metrics
            current_process = psutil.Process()
            process_memory = current_process.memory_info()
            
            # Create metric objects
            metrics.extend([
                DashboardMetric(
                    timestamp=timestamp,
                    category='system',
                    name='CPU Usage',
                    value=cpu_percent,
                    unit='%',
                    status='critical' if cpu_percent > 90 else 'warning' if cpu_percent > 80 else 'normal',
                    context={'type': 'cpu'}
                ),
                DashboardMetric(
                    timestamp=timestamp,
                    category='system',
                    name='Memory Usage',
                    value=memory.percent,
                    unit='%',
                    status='critical' if memory.percent > 90 else 'warning' if memory.percent > 80 else 'normal',
                    context={'type': 'memory'}
                ),
                DashboardMetric(
                    timestamp=timestamp,
                    category='system',
                    name='Disk Usage',
                    value=disk.percent,
                    unit='%',
                    status='critical' if disk.percent > 95 else 'warning' if disk.percent > 85 else 'normal',
                    context={'type': 'disk'}
                ),
                DashboardMetric(
                    timestamp=timestamp,
                    category='process',
                    name='Process Memory',
                    value=round(process_memory.rss / (1024**2), 1),
                    unit='MB',
                    status='warning' if process_memory.rss > 1024**3 else 'normal',
                    context={'type': 'process_memory'}
                )
            ])
            
        except Exception as e:
            self.logger.error(f"Metrics collection failed: {e}")
        
        return metrics
    
    def _update_component_status(self):
        """Update status of system components"""
        try:
            # Check if component processes/files exist
            components_to_check = {
                'login_automation': 'login_bulenox_playwright.py',
                'trade_capture': 'trae_trade_capture.py',
                'network_monitor': 'trade.sh',
                'session_manager': 'enhanced_session_manager.py',
                'performance_optimizer': 'performance_optimizer.py',
                'recovery_system': 'intelligent_recovery_system.py'
            }
            
            for component, filename in components_to_check.items():
                if Path(filename).exists():
                    # Check if there are recent log entries or activity
                    log_file = f"{component}.log"
                    if Path(log_file).exists():
                        # Check last modification time
                        mod_time = Path(log_file).stat().st_mtime
                        if time.time() - mod_time < 300:  # Active within 5 minutes
                            self.component_status[component]['status'] = 'healthy'
                        else:
                            self.component_status[component]['status'] = 'warning'
                    else:
                        self.component_status[component]['status'] = 'warning'
                else:
                    self.component_status[component]['status'] = 'critical'
                
                self.component_status[component]['last_check'] = datetime.now().isoformat()
        
        except Exception as e:
            self.logger.error(f"Component status update failed: {e}")
    
    def _load_trade_events(self):
        """Load recent trade events from database or logs"""
        try:
            # Try to load from trade history database
            if Path('trade_history.db').exists():
                conn = sqlite3.connect('trade_history.db')
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT timestamp, event_type, symbol, amount, price, status, details
                    FROM trade_events 
                    ORDER BY timestamp DESC 
                    LIMIT 20
                """)
                
                rows = cursor.fetchall()
                for row in rows:
                    trade_event = TradeEvent(
                        timestamp=row[0],
                        event_type=row[1],
                        symbol=row[2] or 'N/A',
                        amount=row[3] or 0.0,
                        price=row[4] or 0.0,
                        status=row[5] or 'unknown',
                        details=json.loads(row[6]) if row[6] else {}
                    )
                    
                    # Add if not already in buffer
                    if not any(t.timestamp == trade_event.timestamp for t in self.trade_events):
                        self.trade_events.append(trade_event)
                
                conn.close()
            
            # Also check for recent cURL executions
            if Path('trade.sh').exists():
                mod_time = Path('trade.sh').stat().st_mtime
                if time.time() - mod_time < 60:  # Modified within last minute
                    trade_event = TradeEvent(
                        timestamp=datetime.fromtimestamp(mod_time).isoformat(),
                        event_type='network_intercept',
                        symbol='DETECTED',
                        amount=0.0,
                        price=0.0,
                        status='success',
                        details={'source': 'cURL generation'}
                    )
                    
                    if not any(t.timestamp == trade_event.timestamp for t in self.trade_events):
                        self.trade_events.append(trade_event)
        
        except Exception as e:
            self.logger.error(f"Trade events loading failed: {e}")
    
    def _check_system_alerts(self):
        """Check for system alerts and issues"""
        try:
            timestamp = datetime.now().isoformat()
            
            # Check recent metrics for alerts
            if self.metrics_buffer:
                latest_metrics = list(self.metrics_buffer)[-5:]  # Last 5 metrics
                
                for metric in latest_metrics:
                    if metric.status == 'critical':
                        alert = SystemAlert(
                            timestamp=timestamp,
                            severity='critical',
                            category='performance',
                            message=f'{metric.name} is critically high: {metric.value}{metric.unit}',
                            component='system_monitor',
                            resolved=False
                        )
                        
                        # Add if not duplicate
                        if not any(a.message == alert.message and 
                                 abs((datetime.fromisoformat(a.timestamp) - 
                                     datetime.fromisoformat(alert.timestamp)).total_seconds()) < 60 
                                 for a in self.system_alerts):
                            self.system_alerts.append(alert)
            
            # Check component status for alerts
            for component, status_info in self.component_status.items():
                if status_info['status'] == 'critical':
                    alert = SystemAlert(
                        timestamp=timestamp,
                        severity='error',
                        category='component_failure',
                        message=f'{component.replace("_", " ").title()} is not responding',
                        component=component,
                        resolved=False
                    )
                    
                    # Add if not duplicate
                    if not any(a.component == alert.component and a.category == alert.category and
                             abs((datetime.fromisoformat(a.timestamp) - 
                                 datetime.fromisoformat(alert.timestamp)).total_seconds()) < 300
                             for a in self.system_alerts):
                        self.system_alerts.append(alert)
        
        except Exception as e:
            self.logger.error(f"System alerts check failed: {e}")
    
    def _broadcast_updates(self):
        """Broadcast updates to connected clients"""
        try:
            # Emit metrics update
            recent_metrics = list(self.metrics_buffer)[-10:]
            self.socketio.emit('metrics_update', [asdict(m) for m in recent_metrics])
            
            # Emit trade events update
            recent_trades = list(self.trade_events)[-10:]
            self.socketio.emit('trade_update', [asdict(t) for t in recent_trades])
            
            # Emit alerts update
            recent_alerts = list(self.system_alerts)[-10:]
            self.socketio.emit('alert_update', [asdict(a) for a in recent_alerts])
            
            # Emit status update
            status = self._get_comprehensive_status()
            self.socketio.emit('status_update', status)
            
        except Exception as e:
            self.logger.error(f"Broadcast update failed: {e}")
    
    def _get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            # Calculate overall health
            healthy_components = sum(1 for status in self.component_status.values() 
                                   if status['status'] == 'healthy')
            total_components = len(self.component_status)
            health_percentage = (healthy_components / total_components * 100) if total_components > 0 else 0
            
            # Get recent metrics summary
            recent_metrics = list(self.metrics_buffer)[-5:] if self.metrics_buffer else []
            critical_metrics = sum(1 for m in recent_metrics if m.status == 'critical')
            
            # Determine overall status
            if health_percentage >= 80 and critical_metrics == 0:
                overall_status = 'healthy'
            elif health_percentage >= 60 and critical_metrics <= 1:
                overall_status = 'warning'
            else:
                overall_status = 'critical'
            
            return {
                'overall_status': overall_status,
                'health_percentage': health_percentage,
                'components': self.component_status,
                'active_alerts': len([a for a in self.system_alerts if not a.resolved]),
                'recent_trades': len(self.trade_events),
                'monitoring_active': self.monitoring_active,
                'last_update': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Status generation failed: {e}")
            return {'error': str(e)}
    
    def _generate_performance_chart(self) -> Dict[str, Any]:
        """Generate performance chart data"""
        try:
            if not self.metrics_buffer:
                return {'data': [], 'message': 'No data available'}
            
            # Group metrics by type
            metrics_by_type = defaultdict(list)
            for metric in list(self.metrics_buffer)[-50:]:  # Last 50 metrics
                metrics_by_type[metric.name].append({
                    'timestamp': metric.timestamp,
                    'value': metric.value
                })
            
            # Create traces for each metric type
            traces = []
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
            
            for i, (metric_name, data_points) in enumerate(metrics_by_type.items()):
                if len(data_points) < 2:
                    continue
                
                # Sort by timestamp
                data_points.sort(key=lambda x: x['timestamp'])
                
                timestamps = [datetime.fromisoformat(dp['timestamp']) for dp in data_points]
                values = [dp['value'] for dp in data_points]
                
                trace = {
                    'x': timestamps,
                    'y': values,
                    'type': 'scatter',
                    'mode': 'lines+markers',
                    'name': metric_name,
                    'line': {'color': colors[i % len(colors)]}
                }
                traces.append(trace)
            
            return {'data': traces}
            
        except Exception as e:
            self.logger.error(f"Performance chart generation failed: {e}")
            return {'data': [], 'error': str(e)}
    
    def add_trade_event(self, event: TradeEvent):
        """Add a trade event to the dashboard"""
        self.trade_events.append(event)
        
        # Broadcast to connected clients
        self.socketio.emit('trade_update', [asdict(event)])
    
    def add_system_alert(self, alert: SystemAlert):
        """Add a system alert to the dashboard"""
        self.system_alerts.append(alert)
        
        # Broadcast to connected clients
        self.socketio.emit('alert_update', [asdict(alert)])
    
    def run(self, host: str = '0.0.0.0'):
        """Run the dashboard server"""
        try:
            self.logger.info(f"🚀 Starting TradeBot Sentinel Dashboard on {host}:{self.port}")
            
            # Start monitoring
            self.start_monitoring()
            
            print(f"\n🖥️ TradeBot Sentinel Dashboard")
            print(f"🌐 Access at: http://localhost:{self.port}")
            print(f"📊 Real-time monitoring active")
            print("="*50)
            
            # Run the Flask-SocketIO server
            self.socketio.run(
                self.app,
                host=host,
                port=self.port,
                debug=self.debug,
                use_reloader=False  # Disable reloader to prevent issues with threading
            )
            
        except Exception as e:
            self.logger.error(f"Dashboard server failed: {e}")
            raise
        finally:
            self.stop_monitoring()
    
    def shutdown(self):
        """Shutdown the dashboard"""
        try:
            self.logger.info("🛑 Shutting down dashboard")
            self.stop_monitoring()
            
        except Exception as e:
            self.logger.error(f"Dashboard shutdown failed: {e}")

# Example usage and testing
def main():
    """Main function for testing the dashboard"""
    dashboard = RealtimeDashboard(port=5000, debug=False)
    
    try:
        # Add some sample data for testing
        sample_trade = TradeEvent(
            timestamp=datetime.now().isoformat(),
            event_type='order_placed',
            symbol='BTCUSD',
            amount=0.1,
            price=45000.0,
            status='success',
            details={'source': 'test'}
        )
        dashboard.add_trade_event(sample_trade)
        
        sample_alert = SystemAlert(
            timestamp=datetime.now().isoformat(),
            severity='info',
            category='system_startup',
            message='TradeBot Sentinel Dashboard started successfully',
            component='dashboard',
            resolved=True
        )
        dashboard.add_system_alert(sample_alert)
        
        # Run the dashboard
        dashboard.run()
        
    except KeyboardInterrupt:
        print("\n⏹️ Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Dashboard error: {e}")
    finally:
        dashboard.shutdown()

if __name__ == "__main__":
    print("🤖 TradeBot Sentinel - Real-Time Monitoring Dashboard")
    print("📊 Comprehensive system monitoring and visualization")
    print("="*70)
    
    main()