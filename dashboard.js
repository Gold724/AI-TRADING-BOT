// TRAE-SentinelOps Dashboard JavaScript

class TRAEDashboard {
    constructor() {
        this.wsConnection = null;
        this.apiUrl = 'http://localhost:5000';
        this.wsUrl = 'ws://localhost:8765';
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 5000;
        this.updateInterval = null;
        this.logBuffer = [];
        this.maxLogEntries = 100;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadSettings();
        this.connectWebSocket();
        this.startPeriodicUpdates();
        this.updateTimestamp();
        
        // Initialize dashboard
        this.addLog('info', 'Dashboard initialized successfully');
        this.updateConnectionStatus(false);
    }

    setupEventListeners() {
        // Control buttons
        document.getElementById('startBot').addEventListener('click', () => this.controlBot('start'));
        document.getElementById('stopBot').addEventListener('click', () => this.controlBot('stop'));
        document.getElementById('restartBot').addEventListener('click', () => this.controlBot('restart'));
        document.getElementById('refreshData').addEventListener('click', () => this.refreshAllData());
        
        // Log filters
        document.querySelectorAll('.log-filter').forEach(filter => {
            filter.addEventListener('click', (e) => this.filterLogs(e.target.dataset.level));
        });
        
        // Clear logs
        document.getElementById('clearLogs').addEventListener('click', () => this.clearLogs());
        
        // Connection modal
        document.getElementById('connectBtn').addEventListener('click', () => this.updateConnectionSettings());
        document.getElementById('cancelBtn').addEventListener('click', () => this.hideConnectionModal());
        
        // Connection status click to show modal
        document.getElementById('connectionStatus').addEventListener('click', () => this.showConnectionModal());
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));
        
        // Window events
        window.addEventListener('beforeunload', () => this.cleanup());
        window.addEventListener('focus', () => this.onWindowFocus());
        window.addEventListener('blur', () => this.onWindowBlur());
    }

    loadSettings() {
        const savedApiUrl = localStorage.getItem('trae_api_url');
        const savedWsUrl = localStorage.getItem('trae_ws_url');
        
        if (savedApiUrl) {
            this.apiUrl = savedApiUrl;
            document.getElementById('apiUrl').value = savedApiUrl;
        }
        
        if (savedWsUrl) {
            this.wsUrl = savedWsUrl;
            document.getElementById('wsUrl').value = savedWsUrl;
        }
    }

    saveSettings() {
        localStorage.setItem('trae_api_url', this.apiUrl);
        localStorage.setItem('trae_ws_url', this.wsUrl);
    }

    // WebSocket Connection Management
    connectWebSocket() {
        try {
            this.addLog('info', `Connecting to WebSocket: ${this.wsUrl}`);
            this.wsConnection = new WebSocket(this.wsUrl);
            
            this.wsConnection.onopen = () => {
                this.addLog('success', 'WebSocket connected successfully');
                this.updateConnectionStatus(true);
                this.reconnectAttempts = 0;
            };
            
            this.wsConnection.onmessage = (event) => {
                this.handleWebSocketMessage(event.data);
            };
            
            this.wsConnection.onclose = () => {
                this.addLog('warning', 'WebSocket connection closed');
                this.updateConnectionStatus(false);
                this.scheduleReconnect();
            };
            
            this.wsConnection.onerror = (error) => {
                this.addLog('error', `WebSocket error: ${error.message || 'Connection failed'}`);
                this.updateConnectionStatus(false);
            };
            
        } catch (error) {
            this.addLog('error', `Failed to create WebSocket connection: ${error.message}`);
            this.updateConnectionStatus(false);
        }
    }

    scheduleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            this.addLog('info', `Reconnecting in ${this.reconnectDelay/1000}s (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            setTimeout(() => {
                this.connectWebSocket();
            }, this.reconnectDelay);
        } else {
            this.addLog('error', 'Max reconnection attempts reached. Please check connection settings.');
        }
    }

    handleWebSocketMessage(data) {
        try {
            const message = JSON.parse(data);
            
            switch (message.type) {
                case 'system_status':
                    this.updateSystemStatus(message.data);
                    break;
                case 'service_status':
                    this.updateServiceStatus(message.data);
                    break;
                case 'trading_performance':
                    this.updateTradingPerformance(message.data);
                    break;
                case 'log_entry':
                    this.addLog(message.data.level, message.data.message, message.data.timestamp);
                    break;
                case 'alert':
                    this.addAlert(message.data);
                    break;
                case 'bot_status':
                    this.updateBotStatus(message.data);
                    break;
                default:
                    console.log('Unknown message type:', message.type);
            }
            
            this.updateTimestamp();
        } catch (error) {
            this.addLog('error', `Failed to parse WebSocket message: ${error.message}`);
        }
    }

    // API Communication
    async apiRequest(endpoint, method = 'GET', data = null) {
        try {
            const options = {
                method,
                headers: {
                    'Content-Type': 'application/json',
                },
            };
            
            if (data) {
                options.body = JSON.stringify(data);
            }
            
            const response = await fetch(`${this.apiUrl}${endpoint}`, options);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            this.addLog('error', `API request failed: ${error.message}`);
            throw error;
        }
    }

    // Bot Control Functions
    async controlBot(action) {
        try {
            this.addLog('info', `${action.charAt(0).toUpperCase() + action.slice(1)}ing trading bot...`);
            
            const response = await this.apiRequest(`/api/bot/${action}`, 'POST');
            
            if (response.success) {
                this.addLog('success', `Bot ${action} command executed successfully`);
            } else {
                this.addLog('error', `Bot ${action} failed: ${response.message}`);
            }
        } catch (error) {
            this.addLog('error', `Failed to ${action} bot: ${error.message}`);
        }
    }

    // Data Update Functions
    async refreshAllData() {
        this.addLog('info', 'Refreshing all dashboard data...');
        
        try {
            await Promise.all([
                this.fetchSystemStatus(),
                this.fetchServiceStatus(),
                this.fetchTradingPerformance(),
                this.fetchRecentLogs()
            ]);
            
            this.addLog('success', 'Dashboard data refreshed successfully');
        } catch (error) {
            this.addLog('error', `Failed to refresh data: ${error.message}`);
        }
    }

    async fetchSystemStatus() {
        try {
            const data = await this.apiRequest('/api/system/status');
            this.updateSystemStatus(data);
        } catch (error) {
            this.addLog('warning', 'Failed to fetch system status');
        }
    }

    async fetchServiceStatus() {
        try {
            const data = await this.apiRequest('/api/services/status');
            this.updateServiceStatus(data);
        } catch (error) {
            this.addLog('warning', 'Failed to fetch service status');
        }
    }

    async fetchTradingPerformance() {
        try {
            const data = await this.apiRequest('/api/trading/performance');
            this.updateTradingPerformance(data);
        } catch (error) {
            this.addLog('warning', 'Failed to fetch trading performance');
        }
    }

    async fetchRecentLogs() {
        try {
            const data = await this.apiRequest('/api/logs/recent');
            if (data.logs) {
                data.logs.forEach(log => {
                    this.addLog(log.level, log.message, log.timestamp, false);
                });
            }
        } catch (error) {
            this.addLog('warning', 'Failed to fetch recent logs');
        }
    }

    // UI Update Functions
    updateSystemStatus(data) {
        if (data.cpu !== undefined) {
            document.getElementById('cpuUsage').textContent = `${data.cpu.toFixed(1)}%`;
            document.getElementById('cpuProgress').style.width = `${data.cpu}%`;
        }
        
        if (data.memory !== undefined) {
            document.getElementById('memoryUsage').textContent = `${data.memory.toFixed(1)}%`;
            document.getElementById('memoryProgress').style.width = `${data.memory}%`;
        }
        
        if (data.disk !== undefined) {
            document.getElementById('diskUsage').textContent = `${data.disk.toFixed(1)}%`;
            document.getElementById('diskProgress').style.width = `${data.disk}%`;
        }
        
        if (data.network) {
            document.getElementById('networkStatus').textContent = data.network.status || 'Online';
            document.getElementById('networkUp').textContent = this.formatBytes(data.network.upload || 0) + '/s';
            document.getElementById('networkDown').textContent = this.formatBytes(data.network.download || 0) + '/s';
        }
    }

    updateServiceStatus(data) {
        const services = {
            'tradingBotService': data.trading_bot || 'unknown',
            'backendService': data.backend_api || 'unknown',
            'nginxService': data.nginx || 'unknown',
            'redisService': data.redis || 'unknown',
            'monitorService': data.monitor || 'unknown'
        };
        
        Object.entries(services).forEach(([elementId, status]) => {
            const element = document.getElementById(elementId);
            if (element) {
                const statusElement = element.querySelector('.service-status');
                const indicatorElement = element.querySelector('.service-indicator');
                
                statusElement.textContent = status.charAt(0).toUpperCase() + status.slice(1);
                
                indicatorElement.className = 'service-indicator';
                if (status === 'active' || status === 'running') {
                    indicatorElement.classList.add('active');
                } else if (status === 'inactive' || status === 'stopped') {
                    indicatorElement.classList.add('inactive');
                } else {
                    indicatorElement.classList.add('warning');
                }
            }
        });
    }

    updateTradingPerformance(data) {
        if (data.total_trades !== undefined) {
            document.getElementById('totalTrades').textContent = data.total_trades;
            document.getElementById('tradesChange').textContent = `+${data.trades_today || 0} today`;
        }
        
        if (data.success_rate !== undefined) {
            document.getElementById('successRate').textContent = `${data.success_rate.toFixed(1)}%`;
        }
        
        if (data.daily_pnl !== undefined) {
            const pnlElement = document.getElementById('dailyPnL');
            pnlElement.textContent = `$${data.daily_pnl.toFixed(2)}`;
            
            const changeElement = document.getElementById('pnlChange');
            changeElement.className = 'performance-change';
            if (data.daily_pnl > 0) {
                changeElement.classList.add('positive');
                changeElement.textContent = '↗ Profit';
            } else if (data.daily_pnl < 0) {
                changeElement.classList.add('negative');
                changeElement.textContent = '↘ Loss';
            } else {
                changeElement.textContent = '→ Break Even';
            }
        }
        
        if (data.last_trade) {
            document.getElementById('lastTrade').textContent = this.formatTime(data.last_trade);
        }
    }

    updateBotStatus(data) {
        // Update bot-specific status indicators
        const tradingService = document.getElementById('tradingBotService');
        if (tradingService && data.status) {
            const statusElement = tradingService.querySelector('.service-status');
            const indicatorElement = tradingService.querySelector('.service-indicator');
            
            statusElement.textContent = data.status;
            indicatorElement.className = 'service-indicator';
            
            if (data.status === 'running') {
                indicatorElement.classList.add('active');
            } else if (data.status === 'stopped') {
                indicatorElement.classList.add('inactive');
            } else {
                indicatorElement.classList.add('warning');
            }
        }
    }

    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connectionStatus');
        const iconElement = statusElement.querySelector('i');
        const textElement = statusElement.querySelector('span');
        
        if (connected) {
            statusElement.className = 'status-indicator';
            textElement.textContent = 'Connected';
            iconElement.className = 'fas fa-circle';
        } else {
            statusElement.className = 'status-indicator disconnected';
            textElement.textContent = 'Disconnected';
            iconElement.className = 'fas fa-circle';
        }
    }

    updateTimestamp() {
        const now = new Date();
        document.getElementById('updateTime').textContent = now.toLocaleTimeString();
    }

    // Logging Functions
    addLog(level, message, timestamp = null, addToBuffer = true) {
        const logEntry = {
            level,
            message,
            timestamp: timestamp || new Date().toLocaleTimeString()
        };
        
        if (addToBuffer) {
            this.logBuffer.unshift(logEntry);
            if (this.logBuffer.length > this.maxLogEntries) {
                this.logBuffer.pop();
            }
        }
        
        this.renderLogs();
    }

    renderLogs() {
        const logsContent = document.getElementById('logsContent');
        const activeFilter = document.querySelector('.log-filter.active').dataset.level;
        
        const filteredLogs = activeFilter === 'all' 
            ? this.logBuffer 
            : this.logBuffer.filter(log => log.level === activeFilter);
        
        logsContent.innerHTML = filteredLogs.map(log => `
            <div class="log-entry ${log.level}">
                <span class="log-time">${log.timestamp}</span>
                <span class="log-level ${log.level}">${log.level.toUpperCase()}</span>
                <span class="log-message">${this.escapeHtml(log.message)}</span>
            </div>
        `).join('');
        
        // Auto-scroll to top for new entries
        logsContent.scrollTop = 0;
    }

    filterLogs(level) {
        document.querySelectorAll('.log-filter').forEach(filter => {
            filter.classList.remove('active');
        });
        
        document.querySelector(`[data-level="${level}"]`).classList.add('active');
        this.renderLogs();
    }

    clearLogs() {
        this.logBuffer = [];
        this.renderLogs();
        this.addLog('info', 'Logs cleared');
    }

    // Alert Functions
    addAlert(alertData) {
        const alertsContainer = document.getElementById('alertsContainer');
        const noAlertsElement = alertsContainer.querySelector('.no-alerts');
        
        if (noAlertsElement) {
            noAlertsElement.style.display = 'none';
        }
        
        const alertElement = document.createElement('div');
        alertElement.className = `alert-item ${alertData.severity || 'warning'}`;
        alertElement.innerHTML = `
            <div class="alert-icon">
                <i class="fas fa-${this.getAlertIcon(alertData.severity)}"></i>
            </div>
            <div class="alert-content">
                <div class="alert-title">${alertData.title || 'Alert'}</div>
                <div class="alert-message">${this.escapeHtml(alertData.message)}</div>
            </div>
            <div class="alert-time">${new Date().toLocaleTimeString()}</div>
        `;
        
        alertsContainer.insertBefore(alertElement, alertsContainer.firstChild);
        
        // Auto-remove alert after 30 seconds for non-critical alerts
        if (alertData.severity !== 'critical') {
            setTimeout(() => {
                if (alertElement.parentNode) {
                    alertElement.remove();
                    
                    if (alertsContainer.children.length === 0) {
                        noAlertsElement.style.display = 'flex';
                    }
                }
            }, 30000);
        }
    }

    getAlertIcon(severity) {
        switch (severity) {
            case 'critical': return 'exclamation-triangle';
            case 'warning': return 'exclamation-circle';
            case 'info': return 'info-circle';
            default: return 'bell';
        }
    }

    // Modal Functions
    showConnectionModal() {
        document.getElementById('connectionModal').classList.add('show');
    }

    hideConnectionModal() {
        document.getElementById('connectionModal').classList.remove('show');
    }

    updateConnectionSettings() {
        const newApiUrl = document.getElementById('apiUrl').value.trim();
        const newWsUrl = document.getElementById('wsUrl').value.trim();
        
        if (newApiUrl && newWsUrl) {
            this.apiUrl = newApiUrl;
            this.wsUrl = newWsUrl;
            this.saveSettings();
            
            // Reconnect WebSocket with new URL
            if (this.wsConnection) {
                this.wsConnection.close();
            }
            
            this.reconnectAttempts = 0;
            this.connectWebSocket();
            
            this.hideConnectionModal();
            this.addLog('info', 'Connection settings updated');
        }
    }

    // Utility Functions
    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    formatTime(timestamp) {
        if (!timestamp) return 'Never';
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        if (diff < 60000) return 'Just now';
        if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
        return date.toLocaleDateString();
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Event Handlers
    handleKeyboardShortcuts(e) {
        if (e.ctrlKey || e.metaKey) {
            switch (e.key) {
                case 'r':
                    e.preventDefault();
                    this.refreshAllData();
                    break;
                case 'l':
                    e.preventDefault();
                    this.clearLogs();
                    break;
            }
        }
    }

    onWindowFocus() {
        // Resume updates when window gains focus
        if (!this.updateInterval) {
            this.startPeriodicUpdates();
        }
    }

    onWindowBlur() {
        // Optionally pause updates when window loses focus to save resources
        // Uncomment the next line if you want to pause updates
        // this.stopPeriodicUpdates();
    }

    startPeriodicUpdates() {
        this.updateInterval = setInterval(() => {
            if (this.wsConnection && this.wsConnection.readyState === WebSocket.OPEN) {
                // WebSocket is connected, data should come automatically
                this.updateTimestamp();
            } else {
                // Fallback to API polling when WebSocket is not available
                this.fetchSystemStatus();
                this.fetchServiceStatus();
            }
        }, 10000); // Update every 10 seconds
    }

    stopPeriodicUpdates() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }

    cleanup() {
        this.stopPeriodicUpdates();
        if (this.wsConnection) {
            this.wsConnection.close();
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.traeDashboard = new TRAEDashboard();
});

// Export for potential external use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TRAEDashboard;
}