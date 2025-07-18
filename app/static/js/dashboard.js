/**
 * Enterprise Real-time Dashboard JavaScript
 * WebSocket integration and dynamic chart management
 */

class EnterpriseRealTimeDashboard {
    constructor() {
        this.socket = null;
        this.charts = {};
        this.isConnected = false;
        this.updateInterval = null;
        this.dataBuffer = {
            costTrend: [],
            metrics: {},
            alerts: [],
            recommendations: []
        };
        
        this.config = {
            maxDataPoints: 50,
            updateInterval: 2000,
            chartAnimations: true,
            autoRefresh: true
        };

        this.init();
    }

    /**
     * Initialize the dashboard
     */
    init() {
        this.setupEventListeners();
        this.initializeCharts();
        this.connectWebSocket();
        this.startPeriodicUpdates();
        
        console.log('Enterprise Dashboard initialized');
    }

    /**
     * Setup event listeners for user interactions
     */
    setupEventListeners() {
        // Refresh button
        document.addEventListener('click', (e) => {
            if (e.target.id === 'refreshDashboard') {
                this.refreshAllData();
            }
        });

        // Chart resize handler
        window.addEventListener('resize', () => {
            Object.values(this.charts).forEach(chart => {
                if (chart && typeof chart.resize === 'function') {
                    chart.resize();
                }
            });
        });

        // Visibility change handler for performance
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseUpdates();
            } else {
                this.resumeUpdates();
            }
        });
    }

    /**
     * Initialize all dashboard charts
     */
    initializeCharts() {
        this.initializeCostTrendChart();
        this.initializeProviderDistributionChart();
        this.initializeUtilizationChart();
        this.initializeOptimizationChart();
        this.initializeRegionalChart();
    }

    /**
     * Initialize the main cost trend chart
     */
    initializeCostTrendChart() {
        const ctx = document.getElementById('costTrendChart');
        if (!ctx) return;

        this.charts.costTrend = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Total Cost',
                        data: [],
                        borderColor: '#2563eb',
                        backgroundColor: 'rgba(37, 99, 235, 0.1)',
                        tension: 0.4,
                        fill: true,
                        pointRadius: 3,
                        pointHoverRadius: 6
                    },
                    {
                        label: 'Lambda Cost',
                        data: [],
                        borderColor: '#059669',
                        backgroundColor: 'rgba(5, 150, 105, 0.1)',
                        tension: 0.4,
                        pointRadius: 2
                    },
                    {
                        label: 'VM Cost',
                        data: [],
                        borderColor: '#d97706',
                        backgroundColor: 'rgba(217, 119, 6, 0.1)',
                        tension: 0.4,
                        pointRadius: 2
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
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 20
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: 'white',
                        bodyColor: 'white',
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': $' + 
                                       context.parsed.y.toLocaleString();
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'minute',
                            displayFormats: {
                                minute: 'HH:mm'
                            }
                        },
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        },
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    }
                },
                animation: {
                    duration: this.config.chartAnimations ? 750 : 0
                }
            }
        });
    }

    /**
     * Initialize provider distribution chart
     */
    initializeProviderDistributionChart() {
        const ctx = document.getElementById('providerChart');
        if (!ctx) return;

        this.charts.provider = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['AWS', 'Google Cloud', 'Azure', 'Oracle Cloud', 'Sakura Cloud'],
                datasets: [{
                    data: [0, 0, 0, 0, 0],
                    backgroundColor: [
                        '#ff9900',
                        '#4285f4',
                        '#00bcf2',
                        '#f80000',
                        '#ff6b6b'
                    ],
                    borderWidth: 2,
                    borderColor: 'white'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 15,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const percentage = ((context.parsed / context.dataset.data.reduce((a, b) => a + b, 0)) * 100).toFixed(1);
                                return context.label + ': $' + context.parsed.toLocaleString() + ' (' + percentage + '%)';
                            }
                        }
                    }
                }
            }
        });
    }

    /**
     * Initialize resource utilization chart
     */
    initializeUtilizationChart() {
        const ctx = document.getElementById('utilizationChart');
        if (!ctx) return;

        this.charts.utilization = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['CPU', 'Memory', 'Storage', 'Network', 'Database'],
                datasets: [{
                    label: 'Utilization %',
                    data: [0, 0, 0, 0, 0],
                    backgroundColor: [
                        '#2563eb',
                        '#059669',
                        '#d97706',
                        '#dc2626',
                        '#7c3aed'
                    ],
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });
    }

    /**
     * Initialize optimization opportunities chart
     */
    initializeOptimizationChart() {
        const ctx = document.getElementById('optimizationChart');
        if (!ctx) return;

        this.charts.optimization = new Chart(ctx, {
            type: 'horizontalBar',
            data: {
                labels: ['Reserved Instances', 'Right-sizing', 'Spot Instances', 'Storage Optimization', 'Region Migration'],
                datasets: [{
                    label: 'Potential Savings ($)',
                    data: [0, 0, 0, 0, 0],
                    backgroundColor: '#059669',
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }

    /**
     * Initialize regional cost distribution chart
     */
    initializeRegionalChart() {
        const ctx = document.getElementById('regionalChart');
        if (!ctx) return;

        this.charts.regional = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['US East', 'US West', 'EU West', 'Asia Pacific', 'Canada'],
                datasets: [{
                    label: 'Cost Distribution',
                    data: [0, 0, 0, 0, 0],
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    pointBackgroundColor: '#2563eb'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value;
                            }
                        }
                    }
                }
            }
        });
    }

    /**
     * Connect to WebSocket for real-time updates
     */
    connectWebSocket() {
        try {
            // Initialize Socket.IO connection
            this.socket = io({
                autoConnect: true,
                reconnection: true,
                reconnectionDelay: 1000,
                reconnectionAttempts: 5
            });

            this.setupWebSocketEvents();
            
        } catch (error) {
            console.error('WebSocket connection failed:', error);
            this.handleConnectionError();
        }
    }

    /**
     * Setup WebSocket event handlers
     */
    setupWebSocketEvents() {
        this.socket.on('connect', () => {
            console.log('Connected to WebSocket server');
            this.isConnected = true;
            this.updateConnectionStatus(true);
            this.logActivity('Connected to real-time data stream');
            
            // Subscribe to specific data channels
            this.socket.emit('subscribe', {
                channels: ['cost_updates', 'alerts', 'metrics', 'recommendations']
            });
        });

        this.socket.on('disconnect', (reason) => {
            console.log('Disconnected from WebSocket:', reason);
            this.isConnected = false;
            this.updateConnectionStatus(false);
            this.logActivity('Disconnected from server: ' + reason);
        });

        this.socket.on('connect_error', (error) => {
            console.error('WebSocket connection error:', error);
            this.handleConnectionError();
        });

        // Data event handlers
        this.socket.on('cost_update', (data) => this.handleCostUpdate(data));
        this.socket.on('metrics_update', (data) => this.handleMetricsUpdate(data));
        this.socket.on('alert', (data) => this.handleAlert(data));
        this.socket.on('recommendation', (data) => this.handleRecommendation(data));
        this.socket.on('provider_update', (data) => this.handleProviderUpdate(data));
        this.socket.on('utilization_update', (data) => this.handleUtilizationUpdate(data));
    }

    /**
     * Handle cost update from server
     */
    handleCostUpdate(data) {
        const timestamp = new Date();
        
        // Update cost trend chart
        this.addDataPoint('costTrend', {
            time: timestamp,
            total: data.total_cost || 0,
            lambda: data.lambda_cost || 0,
            vm: data.vm_cost || 0
        });

        // Update metric cards
        this.updateMetricCard('totalCost', data.total_cost, data.total_cost_change);
        this.updateMetricCard('costSavings', data.cost_savings, data.cost_savings_change);
        
        this.logActivity(`Cost update: Total $${data.total_cost?.toLocaleString() || '0'}`);
    }

    /**
     * Handle metrics update from server
     */
    handleMetricsUpdate(data) {
        if (data.active_resources !== undefined) {
            this.updateMetricCard('activeResources', data.active_resources, data.active_resources_change);
        }
        
        if (data.optimization_score !== undefined) {
            this.updateMetricCard('optimizationScore', data.optimization_score + '%', data.optimization_score_change);
        }

        this.logActivity('Metrics updated');
    }

    /**
     * Handle alert from server
     */
    handleAlert(alertData) {
        this.addAlert(alertData);
        this.logActivity(`Alert: ${alertData.message}`);
        
        // Show browser notification if supported
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification('Cost Alert', {
                body: alertData.message,
                icon: '/static/images/alert-icon.png'
            });
        }
    }

    /**
     * Handle recommendation from server
     */
    handleRecommendation(recommendation) {
        this.addRecommendation(recommendation);
        this.logActivity(`New recommendation: ${recommendation.title}`);
    }

    /**
     * Handle provider distribution update
     */
    handleProviderUpdate(data) {
        if (this.charts.provider && data.providers) {
            this.charts.provider.data.datasets[0].data = Object.values(data.providers);
            this.charts.provider.update('none');
        }
    }

    /**
     * Handle utilization update
     */
    handleUtilizationUpdate(data) {
        if (this.charts.utilization && data.utilization) {
            this.charts.utilization.data.datasets[0].data = Object.values(data.utilization);
            this.charts.utilization.update('none');
        }
    }

    /**
     * Add data point to cost trend chart
     */
    addDataPoint(chartName, data) {
        const chart = this.charts[chartName];
        if (!chart) return;

        chart.data.labels.push(data.time);
        chart.data.datasets[0].data.push(data.total);
        chart.data.datasets[1].data.push(data.lambda);
        chart.data.datasets[2].data.push(data.vm);

        // Limit data points
        if (chart.data.labels.length > this.config.maxDataPoints) {
            chart.data.labels.shift();
            chart.data.datasets.forEach(dataset => dataset.data.shift());
        }

        chart.update('none');
    }

    /**
     * Update metric card display
     */
    updateMetricCard(cardId, value, change) {
        const valueElement = document.getElementById(cardId);
        const changeElement = document.getElementById(cardId + 'Change');
        
        if (valueElement) {
            valueElement.textContent = typeof value === 'number' ? value.toLocaleString() : value;
        }
        
        if (changeElement && change !== undefined) {
            const changeText = change > 0 ? `+${change}%` : `${change}%`;
            changeElement.textContent = changeText;
            changeElement.className = `metric-change ${change >= 0 ? 'positive' : 'negative'}`;
        }
    }

    /**
     * Update connection status indicator
     */
    updateConnectionStatus(connected) {
        const indicator = document.getElementById('connectionStatus');
        if (indicator) {
            indicator.className = connected ? 
                'status-indicator status-online' : 
                'status-indicator status-offline';
        }
    }

    /**
     * Log activity to real-time feed
     */
    logActivity(message) {
        const container = document.getElementById('realTimeData');
        if (!container) return;

        const timestamp = new Date().toLocaleTimeString();
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        logEntry.innerHTML = `<span class="text-muted">[${timestamp}]</span> ${message}`;
        
        container.appendChild(logEntry);
        container.scrollTop = container.scrollHeight;

        // Limit log entries
        while (container.children.length > 100) {
            container.removeChild(container.firstChild);
        }
    }

    /**
     * Add alert to alerts panel
     */
    addAlert(alertData) {
        const container = document.getElementById('alertsContainer');
        if (!container) return;

        const alertElement = document.createElement('div');
        alertElement.className = `alert-item ${alertData.severity || ''} p-3 mb-2`;
        alertElement.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <strong>${alertData.title || 'Alert'}</strong>
                    <div class="small text-muted">${alertData.message}</div>
                </div>
                <small class="text-muted">${alertData.timestamp || 'now'}</small>
            </div>
        `;

        container.insertBefore(alertElement, container.firstChild);

        // Limit alerts displayed
        while (container.children.length > 10) {
            container.removeChild(container.lastChild);
        }
    }

    /**
     * Start periodic updates
     */
    startPeriodicUpdates() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }

        this.updateInterval = setInterval(() => {
            this.updateTimestamp();
            
            // Simulate data if not connected
            if (!this.isConnected) {
                this.simulateRealtimeData();
            }
        }, this.config.updateInterval);
    }

    /**
     * Update timestamp display
     */
    updateTimestamp() {
        const element = document.getElementById('lastUpdated');
        if (element) {
            element.textContent = new Date().toLocaleTimeString();
        }
    }

    /**
     * Simulate real-time data for development/demo
     */
    simulateRealtimeData() {
        const mockData = {
            total_cost: Math.random() * 1000 + 500,
            lambda_cost: Math.random() * 400 + 100,
            vm_cost: Math.random() * 600 + 400,
            cost_savings: Math.random() * 200 + 50,
            total_cost_change: (Math.random() - 0.5) * 10,
            cost_savings_change: Math.random() * 5
        };

        this.handleCostUpdate(mockData);

        // Occasionally simulate alerts
        if (Math.random() < 0.1) {
            this.handleAlert({
                title: 'Cost Threshold Alert',
                message: 'Monthly spending has increased by 15%',
                severity: 'warning',
                timestamp: 'just now'
            });
        }
    }

    /**
     * Handle connection errors
     */
    handleConnectionError() {
        this.isConnected = false;
        this.updateConnectionStatus(false);
        this.logActivity('Connection failed - using simulated data');
        
        // Fall back to simulated data
        this.simulateRealtimeData();
    }

    /**
     * Pause updates when page is hidden
     */
    pauseUpdates() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }

    /**
     * Resume updates when page becomes visible
     */
    resumeUpdates() {
        if (!this.updateInterval) {
            this.startPeriodicUpdates();
        }
    }

    /**
     * Refresh all dashboard data
     */
    refreshAllData() {
        if (this.isConnected && this.socket) {
            this.socket.emit('refresh_data');
            this.logActivity('Data refresh requested');
        } else {
            this.logActivity('Manual refresh - simulating new data');
            this.simulateRealtimeData();
        }
    }

    /**
     * Cleanup resources
     */
    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        
        if (this.socket) {
            this.socket.disconnect();
        }

        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
    }
}

// Export for global use
window.EnterpriseRealTimeDashboard = EnterpriseRealTimeDashboard;