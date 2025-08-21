/**
 * AI Trading Sentinel Dashboard JavaScript
 * Handles real-time monitoring, controls, and UI interactions
 */

class TradingDashboard {
    constructor() {
        this.socket = null;
        this.charts = {};
        this.isConnected = false;
        this.updateInterval = null;
        this.retryCount = 0;
        this.maxRetries = 5;
        this.retryDelay = 5000;
        
        // Configuration
        this.config = {
            maxDataPoints: 50,
            updateFrequency: 2000,
            chartColors: {
                cpu: '#3498db',
                memory: '#e74c3c',
                disk: '#f39c12',
                network: '#27ae60'
            },
            alertSounds: {
                critical: '/static/sounds/critical.mp3',
                warning: '/static/sounds/warning.mp3',
                success: '/static/sounds/success.mp3'
            }
        };
        
        this.init();
    }
    
    /**
     * Initialize the dashboard
     */
    init() {
        this.setupEventListeners();
        this.initializeSocket();
        this.initializeCharts();
        this.startPeriodicUpdates();
        this.setupKeyboardShortcuts();
        
        console.log('Trading Dashboard initialized');
    }
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Emergency stop button
        const emergencyBtn = document.getElementById('emergencyStop');
        if (emergencyBtn) {
            emergencyBtn.addEventListener('click', () => this.handleEmergencyStop());
        }
        
        // Trading control buttons
        document.querySelectorAll('[data-trading-action]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.target.dataset.tradingAction;
                this.controlTrading(action);
            });
        });
        
        // Log service selector
        const logService = document.getElementById('logService');
        if (logService) {
            logService.addEventListener('change', () => this.loadLogs());
        }
        
        // Refresh buttons
        document.querySelectorAll('[data-refresh]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const target = e.target.dataset.refresh;
                this.refreshSection(target);
            });
        });
        
        // Window events
        window.addEventListener('beforeunload', () => this.cleanup());
        window.addEventListener('focus', () => this.handleWindowFocus());
        window.addEventListener('blur', () => this.handleWindowBlur());
        
        // Visibility change
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.handleWindowBlur();
            } else {
                this.handleWindowFocus();
            }
        });
    }
    
    /**
     * Initialize Socket.IO connection
     */
    initializeSocket() {
        try {
            this.socket = io({
                transports: ['websocket', 'polling'],
                timeout: 10000,
                reconnection: true,
                reconnectionAttempts: this.maxRetries,
                reconnectionDelay: this.retryDelay
            });
            
            this.socket.on('connect', () => this.handleSocketConnect());
            this.socket.on('disconnect', () => this.handleSocketDisconnect());
            this.socket.on('connect_error', (error) => this.handleSocketError(error));
            this.socket.on('reconnect', () => this.handleSocketReconnect());
            
            // Data event handlers
            this.socket.on('status_update', (data) => this.handleStatusUpdate(data));
            this.socket.on('alert_update', (data) => this.handleAlertUpdate(data));
            this.socket.on('trading_update', (data) => this.handleTradingUpdate(data));
            this.socket.on('system_metrics', (data) => this.handleSystemMetrics(data));
            
        } catch (error) {
            console.error('Socket initialization error:', error);
            this.showNotification('Failed to initialize connection', 'error');
        }
    }
    
    /**
     * Handle socket connection
     */
    handleSocketConnect() {
        this.isConnected = true;
        this.retryCount = 0;
        this.updateConnectionStatus(true);
        this.showNotification('Connected to monitoring server', 'success');
        
        // Request initial data
        this.socket.emit('request_update');
        
        console.log('Socket connected');
    }
    
    /**
     * Handle socket disconnection
     */
    handleSocketDisconnect() {
        this.isConnected = false;
        this.updateConnectionStatus(false);
        this.showNotification('Disconnected from server', 'warning');
        
        console.log('Socket disconnected');
    }
    
    /**
     * Handle socket error
     */
    handleSocketError(error) {
        console.error('Socket error:', error);
        this.retryCount++;
        
        if (this.retryCount >= this.maxRetries) {
            this.showNotification('Connection failed after multiple attempts', 'error');
        }
    }
    
    /**
     * Handle socket reconnection
     */
    handleSocketReconnect() {
        this.showNotification('Reconnected to server', 'success');
        this.socket.emit('request_update');
    }
    
    /**
     * Update connection status indicator
     */
    updateConnectionStatus(connected) {
        const statusEl = document.getElementById('connectionStatus');
        if (!statusEl) return;
        
        if (connected) {
            statusEl.className = 'connection-status connected';
            statusEl.innerHTML = '<i class="fas fa-wifi"></i> Connected';
        } else {
            statusEl.className = 'connection-status disconnected';
            statusEl.innerHTML = '<i class="fas fa-wifi"></i> Disconnected';
        }
    }
    
    /**
     * Initialize charts
     */
    initializeCharts() {
        this.initPerformanceChart();
        this.initTradingChart();
        this.initNetworkChart();
    }
    
    /**
     * Initialize performance chart
     */
    initPerformanceChart() {
        const ctx = document.getElementById('performanceChart');
        if (!ctx) return;
        
        this.charts.performance = new Chart(ctx.getContext('2d'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'CPU %',
                        data: [],
                        borderColor: this.config.chartColors.cpu,
                        backgroundColor: this.hexToRgba(this.config.chartColors.cpu, 0.1),
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Memory %',
                        data: [],
                        borderColor: this.config.chartColors.memory,
                        backgroundColor: this.hexToRgba(this.config.chartColors.memory, 0.1),
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Disk %',
                        data: [],
                        borderColor: this.config.chartColors.disk,
                        backgroundColor: this.hexToRgba(this.config.chartColors.disk, 0.1),
                        tension: 0.4,
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Usage %'
                        },
                        min: 0,
                        max: 100
                    }
                },
                plugins: {
                    legend: {
                        position: 'top'
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.8)',
                        titleColor: 'white',
                        bodyColor: 'white',
                        borderColor: 'rgba(255,255,255,0.2)',
                        borderWidth: 1
                    }
                },
                animation: {
                    duration: 750
                }
            }
        });
    }
    
    /**
     * Initialize trading chart
     */
    initTradingChart() {
        const ctx = document.getElementById('tradingChart');
        if (!ctx) return;
        
        this.charts.trading = new Chart(ctx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['Successful', 'Failed', 'Pending'],
                datasets: [{
                    data: [0, 0, 0],
                    backgroundColor: [
                        this.config.chartColors.network,
                        this.config.chartColors.memory,
                        this.config.chartColors.disk
                    ],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    /**
     * Initialize network chart
     */
    initNetworkChart() {
        const ctx = document.getElementById('networkChart');
        if (!ctx) return;
        
        this.charts.network = new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['Sent', 'Received'],
                datasets: [{
                    label: 'Network Traffic (MB)',
                    data: [0, 0],
                    backgroundColor: [
                        this.config.chartColors.cpu,
                        this.config.chartColors.network
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    /**
     * Handle status update from server
     */
    handleStatusUpdate(data) {
        try {
            if (data.system_status) {
                this.updateSystemStatus(data.system_status);
            }
            
            if (data.trading_status) {
                this.updateTradingStatus(data.trading_status);
            }
            
            if (data.services) {
                this.updateServices(data.services);
            }
            
            if (data.uptime) {
                this.updateUptime(data.uptime);
            }
            
            if (data.last_update) {
                this.updateLastUpdateTime(data.last_update);
            }
            
        } catch (error) {
            console.error('Error handling status update:', error);
        }
    }
    
    /**
     * Handle system metrics update
     */
    handleSystemMetrics(data) {
        try {
            if (data.cpu) {
                this.updateCpuMetrics(data.cpu);
            }
            
            if (data.memory) {
                this.updateMemoryMetrics(data.memory);
            }
            
            if (data.disk) {
                this.updateDiskMetrics(data.disk);
            }
            
            if (data.network) {
                this.updateNetworkMetrics(data.network);
            }
            
            // Update performance chart
            this.updatePerformanceChart(data);
            
        } catch (error) {
            console.error('Error handling metrics update:', error);
        }
    }
    
    /**
     * Handle alert update
     */
    handleAlertUpdate(data) {
        try {
            this.updateAlerts(data.alerts || []);
            
            // Play sound for new alerts
            if (data.new_alert) {
                this.playAlertSound(data.new_alert.severity);
            }
            
        } catch (error) {
            console.error('Error handling alert update:', error);
        }
    }
    
    /**
     * Handle trading update
     */
    handleTradingUpdate(data) {
        try {
            if (data.statistics) {
                this.updateTradingStatistics(data.statistics);
            }
            
            if (data.recent_trades) {
                this.updateRecentTrades(data.recent_trades);
            }
            
        } catch (error) {
            console.error('Error handling trading update:', error);
        }
    }
    
    /**
     * Update system status
     */
    updateSystemStatus(status) {
        const statusEl = document.getElementById('systemStatus');
        const textEl = document.getElementById('systemStatusText');
        
        if (statusEl && textEl) {
            const indicator = statusEl.querySelector('.status-indicator');
            if (indicator) {
                indicator.className = `status-indicator status-${status}`;
            }
            textEl.textContent = this.capitalizeFirst(status);
        }
    }
    
    /**
     * Update trading status
     */
    updateTradingStatus(status) {
        const statusEl = document.getElementById('tradingStatus');
        const textEl = document.getElementById('tradingStatusText');
        
        if (statusEl && textEl) {
            const indicator = statusEl.querySelector('.status-indicator');
            if (indicator) {
                let statusClass = 'unknown';
                if (status === 'active') statusClass = 'healthy';
                else if (status === 'stopped') statusClass = 'warning';
                else if (status === 'error') statusClass = 'critical';
                
                indicator.className = `status-indicator status-${statusClass}`;
            }
            textEl.textContent = this.capitalizeFirst(status);
        }
    }
    
    /**
     * Update CPU metrics
     */
    updateCpuMetrics(cpu) {
        const percent = Math.round(cpu.percent || 0);
        
        this.updateProgressBar('cpu', percent);
        this.updateMetricText('cpuPercent', `${percent}%`);
    }
    
    /**
     * Update memory metrics
     */
    updateMemoryMetrics(memory) {
        const percent = Math.round(memory.percent || 0);
        
        this.updateProgressBar('memory', percent);
        this.updateMetricText('memoryPercent', `${percent}%`);
    }
    
    /**
     * Update disk metrics
     */
    updateDiskMetrics(disk) {
        const percent = Math.round(disk.percent || 0);
        
        this.updateProgressBar('disk', percent);
        this.updateMetricText('diskPercent', `${percent}%`);
    }
    
    /**
     * Update network metrics
     */
    updateNetworkMetrics(network) {
        if (this.charts.network && network.bytes_sent !== undefined && network.bytes_recv !== undefined) {
            const sentMB = (network.bytes_sent / 1024 / 1024).toFixed(2);
            const recvMB = (network.bytes_recv / 1024 / 1024).toFixed(2);
            
            this.charts.network.data.datasets[0].data = [sentMB, recvMB];
            this.charts.network.update('none');
        }
    }
    
    /**
     * Update progress bar
     */
    updateProgressBar(type, percent) {
        const progressEl = document.getElementById(`${type}Progress`);
        if (progressEl) {
            progressEl.style.width = `${percent}%`;
            progressEl.className = `progress-bar ${this.getProgressBarClass(percent)}`;
        }
    }
    
    /**
     * Update metric text
     */
    updateMetricText(elementId, text) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = text;
        }
    }
    
    /**
     * Get progress bar class based on percentage
     */
    getProgressBarClass(percent) {
        if (percent >= 90) return 'bg-danger';
        if (percent >= 70) return 'bg-warning';
        return 'bg-success';
    }
    
    /**
     * Update performance chart
     */
    updatePerformanceChart(metrics) {
        if (!this.charts.performance) return;
        
        const now = new Date().toLocaleTimeString();
        const chart = this.charts.performance;
        
        // Add new data point
        chart.data.labels.push(now);
        chart.data.datasets[0].data.push(metrics.cpu ? metrics.cpu.percent : 0);
        chart.data.datasets[1].data.push(metrics.memory ? metrics.memory.percent : 0);
        chart.data.datasets[2].data.push(metrics.disk ? metrics.disk.percent : 0);
        
        // Remove old data points
        if (chart.data.labels.length > this.config.maxDataPoints) {
            chart.data.labels.shift();
            chart.data.datasets.forEach(dataset => dataset.data.shift());
        }
        
        chart.update('none');
    }
    
    /**
     * Update services status
     */
    updateServices(services) {
        const grid = document.getElementById('servicesGrid');
        if (!grid) return;
        
        grid.innerHTML = '';
        
        for (const [serviceName, serviceData] of Object.entries(services)) {
            const serviceEl = this.createServiceElement(serviceName, serviceData);
            grid.appendChild(serviceEl);
        }
    }
    
    /**
     * Create service element
     */
    createServiceElement(name, data) {
        const serviceEl = document.createElement('div');
        serviceEl.className = 'service-item fade-in';
        
        const status = data.status || 'unknown';
        let statusClass = 'secondary';
        let statusIcon = 'question';
        
        if (status === 'active' || status === 'healthy') {
            statusClass = 'success';
            statusIcon = 'check';
            serviceEl.classList.add('healthy');
        } else if (status === 'inactive' || status === 'unhealthy') {
            statusClass = 'danger';
            statusIcon = 'times';
            serviceEl.classList.add('critical');
        } else if (status === 'warning') {
            statusClass = 'warning';
            statusIcon = 'exclamation';
            serviceEl.classList.add('warning');
        }
        
        serviceEl.innerHTML = `
            <div>
                <h6 class="mb-1">${name}</h6>
                <small class="text-muted">${this.capitalizeFirst(status)}</small>
                ${data.uptime ? `<br><small class="text-info">Uptime: ${data.uptime}</small>` : ''}
            </div>
            <div>
                <span class="badge bg-${statusClass}">
                    <i class="fas fa-${statusIcon}"></i>
                </span>
            </div>
        `;
        
        return serviceEl;
    }
    
    /**
     * Update alerts
     */
    updateAlerts(alerts) {
        const alertsList = document.getElementById('alertsList');
        const alertBadge = document.getElementById('alertBadge');
        
        if (alertBadge) {
            alertBadge.textContent = alerts.length;
            alertBadge.className = `badge ${alerts.length > 0 ? 'bg-danger' : 'bg-secondary'}`;
        }
        
        if (!alertsList) return;
        
        if (alerts.length === 0) {
            alertsList.innerHTML = `
                <div class="text-center text-muted">
                    <i class="fas fa-check-circle fa-3x mb-3 text-success"></i>
                    <p>No active alerts</p>
                </div>
            `;
            return;
        }
        
        alertsList.innerHTML = '';
        alerts.forEach(alert => {
            const alertEl = this.createAlertElement(alert);
            alertsList.appendChild(alertEl);
        });
    }
    
    /**
     * Create alert element
     */
    createAlertElement(alert) {
        const alertEl = document.createElement('div');
        alertEl.className = `alert-item alert-${alert.severity} fade-in`;
        
        const timeAgo = this.getTimeAgo(new Date(alert.timestamp));
        
        alertEl.innerHTML = `
            <div class="d-flex justify-content-between align-items-start">
                <div class="flex-grow-1">
                    <div class="d-flex align-items-center mb-2">
                        <i class="fas fa-${this.getAlertIcon(alert.severity)} me-2"></i>
                        <strong>${alert.type.toUpperCase()}</strong>
                    </div>
                    <p class="mb-1">${alert.message}</p>
                    <small class="text-muted">
                        <i class="fas fa-clock me-1"></i>${timeAgo}
                    </small>
                </div>
                <div class="ms-3">
                    <span class="badge bg-${this.getSeverityBadgeClass(alert.severity)}">
                        ${alert.severity}
                    </span>
                    <button class="btn btn-sm btn-outline-secondary ms-2" 
                            onclick="dashboard.dismissAlert('${alert.id}')">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `;
        
        return alertEl;
    }
    
    /**
     * Get alert icon based on severity
     */
    getAlertIcon(severity) {
        const icons = {
            critical: 'exclamation-triangle',
            warning: 'exclamation-circle',
            info: 'info-circle',
            success: 'check-circle'
        };
        return icons[severity] || 'question-circle';
    }
    
    /**
     * Get severity badge class
     */
    getSeverityBadgeClass(severity) {
        const classes = {
            critical: 'danger',
            warning: 'warning',
            info: 'info',
            success: 'success'
        };
        return classes[severity] || 'secondary';
    }
    
    /**
     * Control trading bot
     */
    async controlTrading(action) {
        if (!this.isConnected) {
            this.showNotification('Not connected to server', 'error');
            return;
        }
        
        try {
            const response = await fetch('/api/trading/control', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ action: action })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification(`Trading bot ${action} successful`, 'success');
                this.playAlertSound('success');
            } else {
                this.showNotification(`Trading bot ${action} failed: ${data.error}`, 'error');
            }
            
        } catch (error) {
            this.showNotification(`Error: ${error.message}`, 'error');
        }
    }
    
    /**
     * Handle emergency stop
     */
    async handleEmergencyStop() {
        const confirmed = await this.showConfirmDialog(
            'Emergency Stop',
            'Are you sure you want to perform an emergency stop? This will halt all trading activities immediately.',
            'danger'
        );
        
        if (!confirmed) return;
        
        try {
            const response = await fetch('/api/emergency/stop', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Emergency stop completed', 'success');
                this.playAlertSound('critical');
            } else {
                this.showNotification(`Emergency stop failed: ${data.error}`, 'error');
            }
            
        } catch (error) {
            this.showNotification(`Error: ${error.message}`, 'error');
        }
    }
    
    /**
     * Load service logs
     */
    async loadLogs() {
        const service = document.getElementById('logService')?.value || 'trading-bot';
        const container = document.getElementById('logsContainer');
        
        if (!container) return;
        
        try {
            const response = await fetch(`/api/logs/${service}?lines=100`);
            const data = await response.json();
            
            if (data.success) {
                container.innerHTML = `<pre class="mb-0">${this.escapeHtml(data.logs)}</pre>`;
                container.scrollTop = container.scrollHeight;
            } else {
                container.innerHTML = `<div class="text-danger">Error loading logs: ${data.error}</div>`;
            }
            
        } catch (error) {
            container.innerHTML = `<div class="text-danger">Error: ${error.message}</div>`;
        }
    }
    
    /**
     * Refresh specific section
     */
    refreshSection(section) {
        switch (section) {
            case 'logs':
                this.loadLogs();
                break;
            case 'status':
                if (this.socket) {
                    this.socket.emit('request_update');
                }
                break;
            case 'metrics':
                if (this.socket) {
                    this.socket.emit('request_metrics');
                }
                break;
            default:
                console.warn('Unknown refresh section:', section);
        }
    }
    
    /**
     * Setup keyboard shortcuts
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + R: Refresh
            if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
                e.preventDefault();
                this.refreshSection('status');
            }
            
            // Ctrl/Cmd + E: Emergency stop
            if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
                e.preventDefault();
                this.handleEmergencyStop();
            }
            
            // Ctrl/Cmd + L: Load logs
            if ((e.ctrlKey || e.metaKey) && e.key === 'l') {
                e.preventDefault();
                this.loadLogs();
            }
        });
    }
    
    /**
     * Start periodic updates
     */
    startPeriodicUpdates() {
        this.updateInterval = setInterval(() => {
            if (this.isConnected && this.socket) {
                this.socket.emit('request_metrics');
            }
        }, this.config.updateFrequency);
    }
    
    /**
     * Handle window focus
     */
    handleWindowFocus() {
        if (this.socket && this.isConnected) {
            this.socket.emit('request_update');
        }
    }
    
    /**
     * Handle window blur
     */
    handleWindowBlur() {
        // Reduce update frequency when window is not focused
    }
    
    /**
     * Play alert sound
     */
    playAlertSound(type) {
        try {
            const audio = new Audio(this.config.alertSounds[type]);
            audio.volume = 0.3;
            audio.play().catch(() => {
                // Ignore audio play errors (user interaction required)
            });
        } catch (error) {
            // Ignore audio errors
        }
    }
    
    /**
     * Show notification
     */
    showNotification(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `alert alert-${this.getBootstrapAlertClass(type)} alert-dismissible fade show slide-in-right`;
        notification.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            z-index: 1050;
            min-width: 300px;
            max-width: 400px;
        `;
        
        notification.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-${this.getNotificationIcon(type)} me-2"></i>
                <span class="flex-grow-1">${message}</span>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, duration);
    }
    
    /**
     * Show confirmation dialog
     */
    showConfirmDialog(title, message, type = 'warning') {
        return new Promise((resolve) => {
            const modal = document.createElement('div');
            modal.className = 'modal fade';
            modal.innerHTML = `
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header bg-${type} text-white">
                            <h5 class="modal-title">
                                <i class="fas fa-${this.getNotificationIcon(type)} me-2"></i>
                                ${title}
                            </h5>
                        </div>
                        <div class="modal-body">
                            <p>${message}</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-${type}" id="confirmBtn">Confirm</button>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
            
            modal.querySelector('#confirmBtn').addEventListener('click', () => {
                resolve(true);
                bsModal.hide();
            });
            
            modal.addEventListener('hidden.bs.modal', () => {
                resolve(false);
                modal.remove();
            });
        });
    }
    
    /**
     * Dismiss alert
     */
    dismissAlert(alertId) {
        if (this.socket) {
            this.socket.emit('dismiss_alert', { alert_id: alertId });
        }
    }
    
    /**
     * Update uptime display
     */
    updateUptime(uptime) {
        const element = document.getElementById('systemUptime');
        if (element) {
            element.textContent = uptime;
        }
    }
    
    /**
     * Update last update time
     */
    updateLastUpdateTime(timestamp) {
        const element = document.getElementById('lastUpdate');
        if (element) {
            const time = new Date(timestamp).toLocaleTimeString();
            element.textContent = `Last update: ${time}`;
        }
    }
    
    /**
     * Update trading statistics
     */
    updateTradingStatistics(stats) {
        const elements = {
            totalTrades: document.getElementById('totalTrades'),
            successRate: document.getElementById('successRate'),
            totalProfitLoss: document.getElementById('totalProfitLoss'),
            lastTradeTime: document.getElementById('lastTradeTime')
        };
        
        if (elements.totalTrades) {
            elements.totalTrades.textContent = stats.total_trades || 0;
        }
        
        if (elements.successRate) {
            const rate = stats.total_trades > 0 ? 
                ((stats.successful_trades / stats.total_trades) * 100).toFixed(1) : 0;
            elements.successRate.textContent = `${rate}%`;
        }
        
        if (elements.totalProfitLoss) {
            const pnl = stats.total_profit_loss || 0;
            elements.totalProfitLoss.textContent = `$${pnl.toFixed(2)}`;
            elements.totalProfitLoss.className = pnl >= 0 ? 'text-success' : 'text-danger';
        }
        
        if (elements.lastTradeTime) {
            const lastTrade = stats.last_trade_time ? 
                new Date(stats.last_trade_time).toLocaleString() : '--';
            elements.lastTradeTime.textContent = lastTrade;
        }
        
        // Update trading chart
        if (this.charts.trading) {
            this.charts.trading.data.datasets[0].data = [
                stats.successful_trades || 0,
                stats.failed_trades || 0,
                stats.pending_trades || 0
            ];
            this.charts.trading.update('none');
        }
    }
    
    /**
     * Utility functions
     */
    capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }
    
    getTimeAgo(date) {
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins} minutes ago`;
        
        const diffHours = Math.floor(diffMins / 60);
        if (diffHours < 24) return `${diffHours} hours ago`;
        
        const diffDays = Math.floor(diffHours / 24);
        return `${diffDays} days ago`;
    }
    
    hexToRgba(hex, alpha) {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    getBootstrapAlertClass(type) {
        const classes = {
            success: 'success',
            error: 'danger',
            warning: 'warning',
            info: 'info'
        };
        return classes[type] || 'info';
    }
    
    getNotificationIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-triangle',
            warning: 'exclamation-circle',
            info: 'info-circle',
            danger: 'exclamation-triangle'
        };
        return icons[type] || 'info-circle';
    }
    
    /**
     * Cleanup resources
     */
    cleanup() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        
        if (this.socket) {
            this.socket.disconnect();
        }
        
        // Cleanup charts
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
    }
}

// Initialize dashboard when DOM is loaded
let dashboard;
document.addEventListener('DOMContentLoaded', function() {
    dashboard = new TradingDashboard();
    
    // Make dashboard globally accessible for debugging
    window.dashboard = dashboard;
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TradingDashboard;
}