import os
import sys
import json
import time
import argparse
import threading
import webbrowser
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_from_directory
from werkzeug.serving import make_server

# Import Fibonacci strategy modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.executor_fibonacci import FibonacciExecutor

# Initialize Flask app
app = Flask(__name__, template_folder='templates')

# Global variables
server = None
server_thread = None
active_trades = []
history_file = "logs/fibonacci_trades.json"
signals_file = "sample_fibonacci_signals.json"

# Create templates directory if it doesn't exist
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'), exist_ok=True)

# Create HTML template for the dashboard
html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fibonacci Strategy Dashboard</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #121212;
            color: #e0e0e0;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            background-color: #1e1e1e;
            padding: 20px;
            border-bottom: 1px solid #333;
            margin-bottom: 20px;
        }
        h1, h2, h3 {
            color: #bb86fc;
        }
        .card {
            background-color: #1e1e1e;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
        }
        .full-width {
            grid-column: 1 / -1;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #333;
        }
        th {
            background-color: #2d2d2d;
            color: #bb86fc;
        }
        tr:hover {
            background-color: #2a2a2a;
        }
        .status-success {
            color: #00e676;
        }
        .status-failure {
            color: #ff5252;
        }
        .btn {
            background-color: #bb86fc;
            color: #121212;
            border: none;
            padding: 10px 15px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
            transition: background-color 0.3s;
        }
        .btn:hover {
            background-color: #a370f7;
        }
        .btn-secondary {
            background-color: #2d2d2d;
            color: #e0e0e0;
        }
        .btn-secondary:hover {
            background-color: #3d3d3d;
        }
        .btn-danger {
            background-color: #cf6679;
        }
        .btn-danger:hover {
            background-color: #b55464;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            color: #bb86fc;
        }
        input, select {
            width: 100%;
            padding: 10px;
            border-radius: 4px;
            border: 1px solid #333;
            background-color: #2d2d2d;
            color: #e0e0e0;
        }
        .tabs {
            display: flex;
            margin-bottom: 20px;
            border-bottom: 1px solid #333;
        }
        .tab {
            padding: 10px 20px;
            cursor: pointer;
            background-color: #1e1e1e;
            color: #e0e0e0;
            border: none;
            border-bottom: 2px solid transparent;
        }
        .tab.active {
            border-bottom: 2px solid #bb86fc;
            color: #bb86fc;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .metrics {
            display: flex;
            justify-content: space-between;
            margin-bottom: 20px;
        }
        .metric {
            background-color: #2d2d2d;
            padding: 15px;
            border-radius: 8px;
            flex: 1;
            margin-right: 10px;
            text-align: center;
        }
        .metric:last-child {
            margin-right: 0;
        }
        .metric h3 {
            margin: 0;
            font-size: 14px;
            color: #e0e0e0;
        }
        .metric p {
            margin: 10px 0 0;
            font-size: 24px;
            font-weight: bold;
            color: #bb86fc;
        }
        .chart-container {
            height: 300px;
            margin-top: 20px;
        }
        .refresh-btn {
            float: right;
            margin-bottom: 10px;
        }
        .modal {
            display: none;
            position: fixed;
            z-index: 1;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            overflow: auto;
            background-color: rgba(0,0,0,0.7);
        }
        .modal-content {
            background-color: #1e1e1e;
            margin: 10% auto;
            padding: 20px;
            border-radius: 8px;
            width: 60%;
            max-width: 600px;
        }
        .close {
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        .close:hover {
            color: #bb86fc;
        }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>🧠 AI Trading Sentinel - Fibonacci Strategy Dashboard</h1>
        </div>
    </header>

    <div class="container">
        <div class="tabs">
            <button class="tab active" onclick="openTab(event, 'dashboard')">Dashboard</button>
            <button class="tab" onclick="openTab(event, 'signals')">Signals</button>
            <button class="tab" onclick="openTab(event, 'history')">Trade History</button>
            <button class="tab" onclick="openTab(event, 'analytics')">Analytics</button>
            <button class="tab" onclick="openTab(event, 'settings')">Settings</button>
        </div>

        <!-- Dashboard Tab -->
        <div id="dashboard" class="tab-content active">
            <button class="btn refresh-btn" onclick="refreshData()">↻ Refresh</button>
            
            <div class="metrics">
                <div class="metric">
                    <h3>Active Trades</h3>
                    <p id="active-trades-count">0</p>
                </div>
                <div class="metric">
                    <h3>Total Trades</h3>
                    <p id="total-trades-count">0</p>
                </div>
                <div class="metric">
                    <h3>Success Rate</h3>
                    <p id="success-rate">0%</p>
                </div>
                <div class="metric">
                    <h3>Profit/Loss</h3>
                    <p id="total-pnl">$0.00</p>
                </div>
            </div>

            <div class="grid">
                <div class="card full-width">
                    <h2>Active Fibonacci Trades</h2>
                    <table id="active-trades-table">
                        <thead>
                            <tr>
                                <th>Symbol</th>
                                <th>Side</th>
                                <th>Quantity</th>
                                <th>Entry</th>
                                <th>Current Level</th>
                                <th>Next Target</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="active-trades-body">
                            <tr>
                                <td colspan="8" style="text-align: center;">No active trades</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div class="card">
                    <h2>Quick Trade</h2>
                    <form id="quick-trade-form">
                        <div class="form-group">
                            <label for="symbol">Symbol</label>
                            <input type="text" id="symbol" name="symbol" required>
                        </div>
                        <div class="form-group">
                            <label for="side">Side</label>
                            <select id="side" name="side" required>
                                <option value="buy">Buy</option>
                                <option value="sell">Sell</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="quantity">Quantity</label>
                            <input type="number" id="quantity" name="quantity" step="0.01" required>
                        </div>
                        <div class="form-group">
                            <label for="entry">Entry Price</label>
                            <input type="number" id="entry" name="entry" step="0.0001" required>
                        </div>
                        <div class="form-group">
                            <label for="fib_low">Fibonacci Low</label>
                            <input type="number" id="fib_low" name="fib_low" step="0.0001" required>
                        </div>
                        <div class="form-group">
                            <label for="fib_high">Fibonacci High</label>
                            <input type="number" id="fib_high" name="fib_high" step="0.0001" required>
                        </div>
                        <div class="form-group">
                            <label for="stop_loss">Stop Loss (Optional)</label>
                            <input type="number" id="stop_loss" name="stop_loss" step="0.0001">
                        </div>
                        <div class="form-group">
                            <label for="take_profit">Take Profit (Optional)</label>
                            <input type="number" id="take_profit" name="take_profit" step="0.0001">
                        </div>
                        <div class="form-group">
                            <label for="stealth_level">Stealth Level</label>
                            <select id="stealth_level" name="stealth_level" required>
                                <option value="1">Low (1)</option>
                                <option value="2" selected>Medium (2)</option>
                                <option value="3">High (3)</option>
                            </select>
                        </div>
                        <button type="submit" class="btn">Execute Trade</button>
                    </form>
                </div>

                <div class="card">
                    <h2>Recent Activity</h2>
                    <div id="recent-activity">
                        <p>No recent activity</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Signals Tab -->
        <div id="signals" class="tab-content">
            <div class="card">
                <h2>Available Signals</h2>
                <button class="btn" onclick="document.getElementById('add-signal-modal').style.display='block'">Add New Signal</button>
                <table id="signals-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Symbol</th>
                            <th>Side</th>
                            <th>Entry</th>
                            <th>Fib Range</th>
                            <th>Description</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="signals-body">
                        <tr>
                            <td colspan="7" style="text-align: center;">Loading signals...</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Trade History Tab -->
        <div id="history" class="tab-content">
            <div class="card">
                <h2>Trade History</h2>
                <table id="history-table">
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>Symbol</th>
                            <th>Side</th>
                            <th>Quantity</th>
                            <th>Price</th>
                            <th>Action</th>
                            <th>Fib Level</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody id="history-body">
                        <tr>
                            <td colspan="8" style="text-align: center;">Loading history...</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Analytics Tab -->
        <div id="analytics" class="tab-content">
            <div class="card">
                <h2>Performance Metrics</h2>
                <div class="chart-container" id="performance-chart">
                    <p>Loading performance data...</p>
                </div>
            </div>

            <div class="grid">
                <div class="card">
                    <h2>Trades by Symbol</h2>
                    <div class="chart-container" id="symbol-chart">
                        <p>Loading symbol data...</p>
                    </div>
                </div>

                <div class="card">
                    <h2>Trades by Fibonacci Level</h2>
                    <div class="chart-container" id="fib-level-chart">
                        <p>Loading Fibonacci level data...</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Settings Tab -->
        <div id="settings" class="tab-content">
            <div class="card">
                <h2>Dashboard Settings</h2>
                <form id="settings-form">
                    <div class="form-group">
                        <label for="history-file">Trade History File</label>
                        <input type="text" id="history-file" name="history-file" value="logs/fibonacci_trades.json">
                    </div>
                    <div class="form-group">
                        <label for="signals-file">Signals File</label>
                        <input type="text" id="signals-file" name="signals-file" value="sample_fibonacci_signals.json">
                    </div>
                    <div class="form-group">
                        <label for="refresh-interval">Auto Refresh Interval (seconds)</label>
                        <input type="number" id="refresh-interval" name="refresh-interval" value="30" min="5">
                    </div>
                    <button type="submit" class="btn">Save Settings</button>
                </form>
            </div>

            <div class="card">
                <h2>Tools</h2>
                <div class="form-group">
                    <button class="btn" onclick="window.location.href='/generate-report'">Generate Report</button>
                    <button class="btn btn-secondary" onclick="window.location.href='/visualize'">Visualize Data</button>
                    <button class="btn btn-secondary" onclick="window.location.href='/simulate'">Run Simulation</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Add Signal Modal -->
    <div id="add-signal-modal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="document.getElementById('add-signal-modal').style.display='none'">&times;</span>
            <h2>Add New Signal</h2>
            <form id="add-signal-form">
                <div class="form-group">
                    <label for="modal-symbol">Symbol</label>
                    <input type="text" id="modal-symbol" name="symbol" required>
                </div>
                <div class="form-group">
                    <label for="modal-side">Side</label>
                    <select id="modal-side" name="side" required>
                        <option value="buy">Buy</option>
                        <option value="sell">Sell</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="modal-quantity">Quantity</label>
                    <input type="number" id="modal-quantity" name="quantity" step="0.01" required>
                </div>
                <div class="form-group">
                    <label for="modal-entry">Entry Price</label>
                    <input type="number" id="modal-entry" name="entry" step="0.0001" required>
                </div>
                <div class="form-group">
                    <label for="modal-fib_low">Fibonacci Low</label>
                    <input type="number" id="modal-fib_low" name="fib_low" step="0.0001" required>
                </div>
                <div class="form-group">
                    <label for="modal-fib_high">Fibonacci High</label>
                    <input type="number" id="modal-fib_high" name="fib_high" step="0.0001" required>
                </div>
                <div class="form-group">
                    <label for="modal-stop_loss">Stop Loss (Optional)</label>
                    <input type="number" id="modal-stop_loss" name="stop_loss" step="0.0001">
                </div>
                <div class="form-group">
                    <label for="modal-take_profit">Take Profit (Optional)</label>
                    <input type="number" id="modal-take_profit" name="take_profit" step="0.0001">
                </div>
                <div class="form-group">
                    <label for="modal-stealth_level">Stealth Level</label>
                    <select id="modal-stealth_level" name="stealth_level" required>
                        <option value="1">Low (1)</option>
                        <option value="2" selected>Medium (2)</option>
                        <option value="3">High (3)</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="modal-description">Description</label>
                    <input type="text" id="modal-description" name="description" required>
                </div>
                <button type="submit" class="btn">Add Signal</button>
            </form>
        </div>
    </div>

    <script>
        // Tab functionality
        function openTab(evt, tabName) {
            var i, tabcontent, tablinks;
            tabcontent = document.getElementsByClassName("tab-content");
            for (i = 0; i < tabcontent.length; i++) {
                tabcontent[i].className = tabcontent[i].className.replace(" active", "");
            }
            tablinks = document.getElementsByClassName("tab");
            for (i = 0; i < tablinks.length; i++) {
                tablinks[i].className = tablinks[i].className.replace(" active", "");
            }
            document.getElementById(tabName).className += " active";
            evt.currentTarget.className += " active";
            
            // Load data for the selected tab
            if (tabName === 'signals') {
                loadSignals();
            } else if (tabName === 'history') {
                loadTradeHistory();
            } else if (tabName === 'analytics') {
                loadAnalytics();
            }
        }

        // Refresh dashboard data
        function refreshData() {
            loadActiveTrades();
            loadRecentActivity();
            updateMetrics();
        }

        // Load active trades
        function loadActiveTrades() {
            fetch('/api/active-trades')
                .then(response => response.json())
                .then(data => {
                    const tableBody = document.getElementById('active-trades-body');
                    tableBody.innerHTML = '';
                    
                    if (data.length === 0) {
                        tableBody.innerHTML = '<tr><td colspan="8" style="text-align: center;">No active trades</td></tr>';
                        return;
                    }
                    
                    data.forEach(trade => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${trade.symbol}</td>
                            <td>${trade.side}</td>
                            <td>${trade.quantity}</td>
                            <td>${trade.entry}</td>
                            <td>${trade.current_level || 'N/A'}</td>
                            <td>${trade.next_target || 'N/A'}</td>
                            <td class="status-${trade.status === 'active' ? 'success' : 'failure'}">${trade.status}</td>
                            <td>
                                <button class="btn btn-secondary" onclick="viewTrade(${trade.id})">View</button>
                                <button class="btn btn-danger" onclick="closeTrade(${trade.id})">Close</button>
                            </td>
                        `;
                        tableBody.appendChild(row);
                    });
                    
                    document.getElementById('active-trades-count').textContent = data.length;
                })
                .catch(error => console.error('Error loading active trades:', error));
        }

        // Load signals
        function loadSignals() {
            fetch('/api/signals')
                .then(response => response.json())
                .then(data => {
                    const tableBody = document.getElementById('signals-body');
                    tableBody.innerHTML = '';
                    
                    if (data.length === 0) {
                        tableBody.innerHTML = '<tr><td colspan="7" style="text-align: center;">No signals available</td></tr>';
                        return;
                    }
                    
                    data.forEach((signal, index) => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${index}</td>
                            <td>${signal.symbol}</td>
                            <td>${signal.side}</td>
                            <td>${signal.entry}</td>
                            <td>${signal.fib_low} - ${signal.fib_high}</td>
                            <td>${signal.description || 'N/A'}</td>
                            <td>
                                <button class="btn" onclick="executeSignal(${index})">Execute</button>
                                <button class="btn btn-secondary" onclick="editSignal(${index})">Edit</button>
                                <button class="btn btn-danger" onclick="deleteSignal(${index})">Delete</button>
                            </td>
                        `;
                        tableBody.appendChild(row);
                    });
                })
                .catch(error => console.error('Error loading signals:', error));
        }

        // Load trade history
        function loadTradeHistory() {
            fetch('/api/trade-history')
                .then(response => response.json())
                .then(data => {
                    const tableBody = document.getElementById('history-body');
                    tableBody.innerHTML = '';
                    
                    if (data.length === 0) {
                        tableBody.innerHTML = '<tr><td colspan="8" style="text-align: center;">No trade history available</td></tr>';
                        return;
                    }
                    
                    data.forEach(trade => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${trade.timestamp}</td>
                            <td>${trade.symbol}</td>
                            <td>${trade.side}</td>
                            <td>${trade.quantity}</td>
                            <td>${trade.price || 'N/A'}</td>
                            <td>${trade.action || 'trade'}</td>
                            <td>${trade.fib_level || 'N/A'}</td>
                            <td class="status-${trade.success ? 'success' : 'failure'}">${trade.success ? 'Success' : 'Failed'}</td>
                        `;
                        tableBody.appendChild(row);
                    });
                    
                    document.getElementById('total-trades-count').textContent = data.length;
                    
                    // Calculate success rate
                    const successCount = data.filter(trade => trade.success).length;
                    const successRate = data.length > 0 ? (successCount / data.length * 100).toFixed(1) : 0;
                    document.getElementById('success-rate').textContent = `${successRate}%`;
                })
                .catch(error => console.error('Error loading trade history:', error));
        }

        // Load recent activity
        function loadRecentActivity() {
            fetch('/api/recent-activity')
                .then(response => response.json())
                .then(data => {
                    const activityDiv = document.getElementById('recent-activity');
                    activityDiv.innerHTML = '';
                    
                    if (data.length === 0) {
                        activityDiv.innerHTML = '<p>No recent activity</p>';
                        return;
                    }
                    
                    data.forEach(activity => {
                        const p = document.createElement('p');
                        p.innerHTML = `<strong>${activity.timestamp}</strong>: ${activity.message}`;
                        activityDiv.appendChild(p);
                    });
                })
                .catch(error => console.error('Error loading recent activity:', error));
        }

        // Update metrics
        function updateMetrics() {
            fetch('/api/metrics')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('total-pnl').textContent = `$${data.total_pnl.toFixed(2)}`;
                    // Other metrics are updated by their respective functions
                })
                .catch(error => console.error('Error loading metrics:', error));
        }

        // Load analytics
        function loadAnalytics() {
            // This would be implemented with a charting library like Chart.js
            // For now, we'll just show placeholder text
            document.getElementById('performance-chart').innerHTML = '<p>Performance chart would be displayed here</p>';
            document.getElementById('symbol-chart').innerHTML = '<p>Symbol distribution chart would be displayed here</p>';
            document.getElementById('fib-level-chart').innerHTML = '<p>Fibonacci level distribution chart would be displayed here</p>';
        }

        // Execute signal
        function executeSignal(index) {
            if (confirm('Are you sure you want to execute this signal?')) {
                fetch(`/api/execute-signal/${index}`, { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('Signal execution started successfully!');
                            refreshData();
                        } else {
                            alert(`Error: ${data.message}`);
                        }
                    })
                    .catch(error => console.error('Error executing signal:', error));
            }
        }

        // View trade details
        function viewTrade(id) {
            alert(`View trade details for ID: ${id} (Not implemented in this demo)`); 
        }

        // Close trade
        function closeTrade(id) {
            if (confirm('Are you sure you want to close this trade?')) {
                fetch(`/api/close-trade/${id}`, { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('Trade closed successfully!');
                            refreshData();
                        } else {
                            alert(`Error: ${data.message}`);
                        }
                    })
                    .catch(error => console.error('Error closing trade:', error));
            }
        }

        // Edit signal
        function editSignal(index) {
            alert(`Edit signal with index: ${index} (Not implemented in this demo)`);
        }

        // Delete signal
        function deleteSignal(index) {
            if (confirm('Are you sure you want to delete this signal?')) {
                fetch(`/api/delete-signal/${index}`, { method: 'DELETE' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('Signal deleted successfully!');
                            loadSignals();
                        } else {
                            alert(`Error: ${data.message}`);
                        }
                    })
                    .catch(error => console.error('Error deleting signal:', error));
            }
        }

        // Form submission handlers
        document.getElementById('quick-trade-form').addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const data = {};
            for (let [key, value] of formData.entries()) {
                data[key] = value;
            }
            
            fetch('/api/execute-trade', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Trade execution started successfully!');
                    this.reset();
                    refreshData();
                } else {
                    alert(`Error: ${data.message}`);
                }
            })
            .catch(error => console.error('Error executing trade:', error));
        });

        document.getElementById('add-signal-form').addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const data = {};
            for (let [key, value] of formData.entries()) {
                data[key] = value;
            }
            
            fetch('/api/add-signal', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Signal added successfully!');
                    document.getElementById('add-signal-modal').style.display = 'none';
                    this.reset();
                    loadSignals();
                } else {
                    alert(`Error: ${data.message}`);
                }
            })
            .catch(error => console.error('Error adding signal:', error));
        });

        document.getElementById('settings-form').addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const data = {};
            for (let [key, value] of formData.entries()) {
                data[key] = value;
            }
            
            fetch('/api/update-settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Settings updated successfully!');
                    refreshData();
                } else {
                    alert(`Error: ${data.message}`);
                }
            })
            .catch(error => console.error('Error updating settings:', error));
        });

        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            refreshData();
            
            // Set up auto-refresh
            setInterval(refreshData, 30000); // 30 seconds
        });
    </script>
</body>
</html>
"""

# Create HTML template file
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates', 'dashboard.html'), 'w') as f:
    f.write(html_template)

# Load trade history
def load_trade_history(file_path=history_file):
    """Load trade history from the logs file"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                history = json.load(f)
            return history
        return []
    except Exception as e:
        print(f"Error loading trade history: {e}")
        return []

# Load signals
def load_signals(file_path=signals_file):
    """Load sample signals from JSON file"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                signals = json.load(f)
            return signals
        return []
    except Exception as e:
        print(f"Error loading signals: {e}")
        return []

# Save signals
def save_signals(signals, file_path=signals_file):
    """Save signals to a JSON file"""
    try:
        with open(file_path, 'w') as f:
            json.dump(signals, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving signals: {e}")
        return False

# Calculate metrics
def calculate_metrics(trades):
    """Calculate performance metrics from trade history"""
    if not trades:
        return {
            "total_trades": 0,
            "successful_trades": 0,
            "success_rate": 0,
            "total_pnl": 0
        }
    
    successful_trades = sum(1 for trade in trades if trade.get("success", False))
    success_rate = (successful_trades / len(trades)) * 100 if trades else 0
    
    # Simple PnL calculation (would be more complex in a real system)
    total_pnl = 0
    for trade in trades:
        if trade.get("action") == "entry" or trade.get("action") == "reentry":
            # Deduct from PnL for entries
            total_pnl -= trade.get("quantity", 0) * trade.get("price", 0) if trade.get("price") else 0
        elif trade.get("action") == "partial_exit" or trade.get("action") == "take_profit" or trade.get("action") == "stop_loss":
            # Add to PnL for exits
            total_pnl += trade.get("quantity", 0) * trade.get("price", 0) if trade.get("price") else 0
    
    return {
        "total_trades": len(trades),
        "successful_trades": successful_trades,
        "success_rate": success_rate,
        "total_pnl": total_pnl
    }

# Flask routes
@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/active-trades')
def get_active_trades():
    return jsonify(active_trades)

@app.route('/api/trade-history')
def get_trade_history():
    trades = load_trade_history()
    return jsonify(trades)

@app.route('/api/signals')
def get_signals():
    signals = load_signals()
    return jsonify(signals)

@app.route('/api/recent-activity')
def get_recent_activity():
    trades = load_trade_history()
    # Get the 5 most recent trades
    recent_trades = sorted(trades, key=lambda x: x.get("timestamp", ""), reverse=True)[:5]
    
    activity = []
    for trade in recent_trades:
        timestamp = trade.get("timestamp", "")
        symbol = trade.get("symbol", "Unknown")
        side = trade.get("side", "Unknown")
        action = trade.get("action", "trade")
        success = trade.get("success", False)
        
        message = f"{symbol} {side} {action} - {'Successful' if success else 'Failed'}"
        activity.append({"timestamp": timestamp, "message": message})
    
    return jsonify(activity)

@app.route('/api/metrics')
def get_metrics():
    trades = load_trade_history()
    metrics = calculate_metrics(trades)
    return jsonify(metrics)

@app.route('/api/execute-trade', methods=['POST'])
def execute_trade():
    data = request.json
    
    # Validate required fields
    required_fields = ["symbol", "side", "quantity", "entry", "fib_low", "fib_high"]
    for field in required_fields:
        if field not in data:
            return jsonify({"success": False, "message": f"Missing required field: {field}"})
    
    # Create signal dictionary
    signal = {
        "symbol": data["symbol"],
        "side": data["side"],
        "quantity": float(data["quantity"]),
        "entry": float(data["entry"]),
        "fib_low": float(data["fib_low"]),
        "fib_high": float(data["fib_high"]),
        "direction": "long" if data["side"].lower() == "buy" else "short"
    }
    
    # Add optional fields
    if "stop_loss" in data and data["stop_loss"]:
        signal["stopLoss"] = float(data["stop_loss"])
    if "take_profit" in data and data["take_profit"]:
        signal["takeProfit"] = float(data["take_profit"])
    if "stealth_level" in data:
        signal["stealth_level"] = int(data["stealth_level"])
    
    # Execute trade in a separate thread
    def execute_fibonacci_trade(signal):
        try:
            # Create executor
            executor = FibonacciExecutor(
                signal=signal,
                stopLoss=signal.get("stopLoss"),
                takeProfit=signal.get("takeProfit"),
                stealth_level=signal.get("stealth_level", 2)
            )
            
            # Execute trade
            success = executor.execute_trade()
            
            # Update active trades
            if success:
                global active_trades
                trade_id = len(active_trades) + 1
                active_trades.append({
                    "id": trade_id,
                    "symbol": signal["symbol"],
                    "side": signal["side"],
                    "quantity": signal["quantity"],
                    "entry": signal["entry"],
                    "current_level": "Entry",
                    "next_target": executor.fib_targets[0] if executor.fib_targets else None,
                    "status": "active"
                })
        except Exception as e:
            print(f"Error executing Fibonacci trade: {e}")
    
    # Start execution thread
    thread = threading.Thread(target=execute_fibonacci_trade, args=(signal,))
    thread.daemon = True
    thread.start()
    
    return jsonify({"success": True, "message": "Trade execution started"})

@app.route('/api/execute-signal/<int:index>', methods=['POST'])
def execute_signal(index):
    signals = load_signals()
    
    if index < 0 or index >= len(signals):
        return jsonify({"success": False, "message": "Invalid signal index"})
    
    signal = signals[index]
    
    # Execute trade in a separate thread
    def execute_fibonacci_trade(signal):
        try:
            # Create executor
            executor = FibonacciExecutor(
                signal=signal,
                stopLoss=signal.get("stopLoss"),
                takeProfit=signal.get("takeProfit"),
                stealth_level=signal.get("stealth_level", 2)
            )
            
            # Execute trade
            success = executor.execute_trade()
            
            # Update active trades
            if success:
                global active_trades
                trade_id = len(active_trades) + 1
                active_trades.append({
                    "id": trade_id,
                    "symbol": signal["symbol"],
                    "side": signal["side"],
                    "quantity": signal["quantity"],
                    "entry": signal["entry"],
                    "current_level": "Entry",
                    "next_target": executor.fib_targets[0] if executor.fib_targets else None,
                    "status": "active"
                })
        except Exception as e:
            print(f"Error executing Fibonacci trade: {e}")
    
    # Start execution thread
    thread = threading.Thread(target=execute_fibonacci_trade, args=(signal,))
    thread.daemon = True
    thread.start()
    
    return jsonify({"success": True, "message": "Signal execution started"})

@app.route('/api/close-trade/<int:id>', methods=['POST'])
def close_trade(id):
    global active_trades
    
    # Find trade by ID
    trade = next((t for t in active_trades if t["id"] == id), None)
    
    if not trade:
        return jsonify({"success": False, "message": "Trade not found"})
    
    # Remove trade from active trades
    active_trades = [t for t in active_trades if t["id"] != id]
    
    # In a real implementation, you would also close the actual trade
    # through the broker interface
    
    return jsonify({"success": True, "message": "Trade closed successfully"})

@app.route('/api/add-signal', methods=['POST'])
def add_signal():
    data = request.json
    
    # Validate required fields
    required_fields = ["symbol", "side", "quantity", "entry", "fib_low", "fib_high", "description"]
    for field in required_fields:
        if field not in data:
            return jsonify({"success": False, "message": f"Missing required field: {field}"})
    
    # Create signal dictionary
    signal = {
        "symbol": data["symbol"],
        "side": data["side"],
        "quantity": float(data["quantity"]),
        "entry": float(data["entry"]),
        "fib_low": float(data["fib_low"]),
        "fib_high": float(data["fib_high"]),
        "direction": "long" if data["side"].lower() == "buy" else "short",
        "description": data["description"]
    }
    
    # Add optional fields
    if "stop_loss" in data and data["stop_loss"]:
        signal["stopLoss"] = float(data["stop_loss"])
    if "take_profit" in data and data["take_profit"]:
        signal["takeProfit"] = float(data["take_profit"])
    if "stealth_level" in data:
        signal["stealth_level"] = int(data["stealth_level"])
    
    # Load existing signals
    signals = load_signals()
    
    # Add new signal
    signals.append(signal)
    
    # Save signals
    if save_signals(signals):
        return jsonify({"success": True, "message": "Signal added successfully"})
    else:
        return jsonify({"success": False, "message": "Error saving signal"})

@app.route('/api/delete-signal/<int:index>', methods=['DELETE'])
def delete_signal(index):
    signals = load_signals()
    
    if index < 0 or index >= len(signals):
        return jsonify({"success": False, "message": "Invalid signal index"})
    
    # Remove signal
    signals.pop(index)
    
    # Save signals
    if save_signals(signals):
        return jsonify({"success": True, "message": "Signal deleted successfully"})
    else:
        return jsonify({"success": False, "message": "Error deleting signal"})

@app.route('/api/update-settings', methods=['POST'])
def update_settings():
    data = request.json
    
    global history_file, signals_file
    
    # Update settings
    if "history-file" in data:
        history_file = data["history-file"]
    if "signals-file" in data:
        signals_file = data["signals-file"]
    
    return jsonify({"success": True, "message": "Settings updated successfully"})

@app.route('/generate-report')
def generate_report():
    # In a real implementation, this would generate a report
    # For now, we'll just redirect to the dashboard
    return "<script>alert('Report generation would be implemented here'); window.location.href='/';</script>"

@app.route('/visualize')
def visualize():
    # In a real implementation, this would visualize the data
    # For now, we'll just redirect to the dashboard
    return "<script>alert('Data visualization would be implemented here'); window.location.href='/';</script>"

@app.route('/simulate')
def simulate():
    # In a real implementation, this would run a simulation
    # For now, we'll just redirect to the dashboard
    return "<script>alert('Simulation would be implemented here'); window.location.href='/';</script>"

def start_server(host='127.0.0.1', port=5001, open_browser=True):
    """Start the Flask server"""
    global server, server_thread
    
    # Create server
    server = make_server(host, port, app)
    
    # Start server in a separate thread
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    print(f"\n🚀 Fibonacci Strategy Dashboard running at http://{host}:{port}")
    print("Press Ctrl+C to stop the server")
    
    # Open browser if requested
    if open_browser:
        webbrowser.open(f"http://{host}:{port}")

def stop_server():
    """Stop the Flask server"""
    global server
    if server:
        server.shutdown()
        print("\n⏹️ Server stopped")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Fibonacci Strategy Dashboard")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Server host")
    parser.add_argument("--port", type=int, default=5001, help="Server port")
    parser.add_argument("--history", type=str, default="logs/fibonacci_trades.json", help="Trade history file")
    parser.add_argument("--signals", type=str, default="sample_fibonacci_signals.json", help="Signals file")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    
    args = parser.parse_args()
    
    global history_file, signals_file
    history_file = args.history
    signals_file = args.signals
    
    try:
        # Start server
        start_server(args.host, args.port, not args.no_browser)
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # Stop server
        stop_server()
    except Exception as e:
        print(f"Error: {e}")
        stop_server()

if __name__ == "__main__":
    main()