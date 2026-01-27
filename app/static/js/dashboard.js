/* Dashboard Module with Charts */

class Dashboard {
    constructor() {
        this.vehicleChart = null;
        this.trendChart = null;
        this.stats = {
            totalVehicles: 0,
            totalViolations: 0,
            accuracy: 0,
            avgConfidence: 0,
            processedVideos: 0
        };
        
        this.initDarkMode();
    }

    initDarkMode() {
        const darkModeToggle = document.getElementById('darkModeToggle');
        if (!darkModeToggle) return;

        // Load saved preference
        const darkMode = localStorage.getItem('darkMode') === 'true';
        if (darkMode) {
            document.body.classList.add('dark-mode');
            darkModeToggle.innerHTML = '<i class="fas fa-sun"></i>';
        }

        darkModeToggle.addEventListener('click', () => {
            document.body.classList.toggle('dark-mode');
            const isDark = document.body.classList.contains('dark-mode');
            localStorage.setItem('darkMode', isDark);
            darkModeToggle.innerHTML = isDark ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
            
            // Update charts colors
            this.updateChartsTheme();
        });
    }

    initCharts() {
        this.initVehicleChart();
        this.initTrendChart();
    }

    async initVehicleChart() {
        const ctx = document.getElementById('vehicleViolationsChart');
        if (!ctx) return;

        const isDark = document.body.classList.contains('dark-mode');
        const textColor = isDark ? '#d1d5db' : '#6b7280';
        const gridColor = isDark ? '#374151' : '#e5e7eb';

        // Load real violations and group by vehicle type
        let counts = { 'Ô tô': 0, 'Xe máy': 0, 'Xe buýt': 0, 'Xe tải': 0 };
        try {
            const resp = await fetch('/api/violations');
            if (resp.ok) {
                const data = await resp.json();
                const violations = data.violations || [];
                violations.forEach(v => {
                    const vt = v.vehicle_type || 'Xe khác';
                    if (counts[vt] === undefined) counts[vt] = 0;
                    counts[vt]++;
                });
            }
        } catch (e) {
            console.warn('Vehicle chart: fallback to zeros', e);
        }

        this.vehicleChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: Object.keys(counts),
                datasets: [{
                    label: 'Số vi phạm',
                    data: Object.values(counts),
                    backgroundColor: [
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(139, 92, 246, 0.8)',
                        'rgba(16, 185, 129, 0.8)',
                        'rgba(245, 158, 11, 0.8)'
                    ],
                    borderColor: [
                        'rgb(59, 130, 246)',
                        'rgb(139, 92, 246)',
                        'rgb(16, 185, 129)',
                        'rgb(245, 158, 11)'
                    ],
                    borderWidth: 2,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: isDark ? '#1f2937' : '#ffffff',
                        titleColor: textColor,
                        bodyColor: textColor,
                        borderColor: gridColor,
                        borderWidth: 1,
                        padding: 12,
                        boxPadding: 6,
                        usePointStyle: true
                    }
                },
                scales: {
                    y: { beginAtZero: true, ticks: { color: textColor }, grid: { color: gridColor } },
                    x: { ticks: { color: textColor }, grid: { display: false } }
                }
            }
        });
    }

    async initTrendChart() {
        const ctx = document.getElementById('violationTrendChart');
        if (!ctx) return;

        const isDark = document.body.classList.contains('dark-mode');
        const textColor = isDark ? '#d1d5db' : '#6b7280';
        const gridColor = isDark ? '#374151' : '#e5e7eb';

        // Compute violations per weekday from real data
        const weekdayLabels = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'];
        const weekdayCounts = [0,0,0,0,0,0,0];
        try {
            const resp = await fetch('/api/violations');
            if (resp.ok) {
                const data = await resp.json();
                (data.violations || []).forEach(v => {
                    if (!v.timestamp) return;
                    try {
                        const d = new Date(v.timestamp);
                        // JS: 0=Sun .. 6=Sat ; map to VN labels
                        const idx = (d.getDay() + 6) % 7; // Mon=0 .. Sun=6
                        weekdayCounts[idx]++;
                    } catch {}
                });
            }
        } catch (e) { console.warn('Trend chart: fallback to zeros', e); }

        this.trendChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: weekdayLabels,
                datasets: [{
                    label: 'Vi phạm',
                    data: weekdayCounts,
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: 'rgb(59, 130, 246)',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 5,
                    pointHoverRadius: 7
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: isDark ? '#1f2937' : '#ffffff',
                        titleColor: textColor,
                        bodyColor: textColor,
                        borderColor: gridColor,
                        borderWidth: 1,
                        padding: 12,
                        boxPadding: 6,
                        usePointStyle: true
                    }
                },
                scales: {
                    y: { beginAtZero: true, ticks: { color: textColor }, grid: { color: gridColor } },
                    x: { ticks: { color: textColor }, grid: { color: gridColor, display: true } }
                }
            }
        });
    }

    updateChartsTheme() {
        if (this.vehicleChart) {
            this.vehicleChart.destroy();
            this.initVehicleChart();
        }
        if (this.trendChart) {
            this.trendChart.destroy();
            this.initTrendChart();
        }
    }

    updateStats(stats) {
        // Update stat cards
        if (stats.totalVehicles !== undefined) {
            document.getElementById('totalVehicles').textContent = stats.totalVehicles.toLocaleString();
        }
        if (stats.totalViolations !== undefined) {
            document.getElementById('totalViolations').textContent = stats.totalViolations.toLocaleString();
        }
        if (stats.accuracy !== undefined) {
            document.getElementById('accuracy').textContent = stats.accuracy.toFixed(1) + '%';
        }
        if (stats.processedVideos !== undefined) {
            document.getElementById('processedVideos').textContent = stats.processedVideos.toLocaleString();
        }
        if (stats.avgConfidence !== undefined) {
            document.getElementById('avgConfidence').textContent = stats.avgConfidence.toFixed(1) + '%';
            const confEl = document.getElementById('confidenceTrend');
            if (confEl) {
                if (stats.avgConfidence >= 90) {
                    confEl.textContent = 'Rất cao';
                } else if (stats.avgConfidence >= 80) {
                    confEl.textContent = 'Cao';
                } else if (stats.avgConfidence >= 70) {
                    confEl.textContent = 'Bình thường';
                } else {
                    confEl.textContent = 'Cần cải thiện';
                }
            }
        }
        if (stats.topViolationType !== undefined) {
            document.getElementById('topViolationType').textContent = stats.topViolationType || '-';
            document.getElementById('violationTypeCount').textContent = (stats.topViolationTypeCount || 0) + ' lần';
        }
    }

    addActivity(type, title, time = 'Vừa xong') {
        const activityList = document.getElementById('recentActivity');
        if (!activityList) return;

        const iconClasses = {
            info: 'activity-icon-info fa-info-circle',
            success: 'activity-icon-success fa-check-circle',
            warning: 'activity-icon-warning fa-exclamation-triangle',
            danger: 'activity-icon-danger fa-times-circle'
        };

        const iconClass = iconClasses[type] || iconClasses.info;
        const [bgClass, iconName] = iconClass.split(' ');

        const activityItem = document.createElement('div');
        activityItem.className = 'activity-item';
        activityItem.innerHTML = `
            <div class="activity-icon ${bgClass}">
                <i class="fas ${iconName}"></i>
            </div>
            <div class="activity-content">
                <div class="activity-title">${title}</div>
                <div class="activity-time">${time}</div>
            </div>
        `;

        // Remove initial "system ready" message if exists
        const emptyState = activityList.querySelector('.activity-item');
        if (emptyState && emptyState.querySelector('.activity-title').textContent === 'Hệ thống sẵn sàng') {
            activityList.innerHTML = '';
        }

        activityList.insertBefore(activityItem, activityList.firstChild);

        // Keep only last 10 activities
        while (activityList.children.length > 10) {
            activityList.removeChild(activityList.lastChild);
        }
    }

    updateTopViolations(violations) {
        const topViolationsList = document.getElementById('topViolations');
        if (!topViolationsList || !violations || violations.length === 0) return;

        topViolationsList.innerHTML = violations.slice(0, 5).map((v, index) => `
            <div class="top-violation-item">
                <div class="violation-rank">${index + 1}</div>
                <div class="violation-info">
                    <div class="violation-zone">${v.zone}</div>
                    <div class="violation-count">${v.count} vi phạm</div>
                </div>
            </div>
        `).join('');
    }

    updateTopVehicles(violations) {
        const topVehiclesList = document.getElementById('topVehicles');
        if (!topVehiclesList || !violations || violations.length === 0) return;

        // Count violations by vehicle (track_id)
        const vehicleMap = {};
        violations.forEach(v => {
            const vehicleId = v.track_id != null ? v.track_id : (v.id || `vehicle_${Math.random()}`);
            if (!vehicleMap[vehicleId]) {
                vehicleMap[vehicleId] = {
                    id: vehicleId,
                    violations: 0,
                    type: v.vehicle_type || 'Không xác định',
                    lastTime: v.timestamp || ''
                };
            }
            vehicleMap[vehicleId].violations++;
        });

        // Sort by violation count
        const topVehicles = Object.values(vehicleMap)
            .sort((a, b) => b.violations - a.violations)
            .slice(0, 5);

        if (topVehicles.length === 0) {
            topVehiclesList.innerHTML = '<div class="empty-state" style="padding: 2rem; text-align: center; font-size: 0.875rem;"><p>Chưa có dữ liệu</p></div>';
            return;
        }

        topVehiclesList.innerHTML = topVehicles.map((v, index) => `
            <div class="top-violation-item">
                <div class="violation-rank">${index + 1}</div>
                <div class="violation-info">
                    <div class="violation-zone" style="font-weight: 600;">${v.type}</div>
                    <div class="violation-count">${v.violations} vi phạm</div>
                </div>
            </div>
        `).join('');
    }

    async loadRealStats() {
        // Load real statistics from API
        try {
            // Fetch violations list to count total violations
            const violationsResp = await fetch('/api/violations');
            if (violationsResp.ok) {
                const violationsData = await violationsResp.json();
                const violations = violationsData.violations || [];
                this.stats.totalViolations = violations.length;
                
                // Calculate average confidence (from detection confidences)
                if (violations.length > 0) {
                    const totalConfidence = violations.reduce((sum, v) => sum + (v.confidence || 0), 0);
                    this.stats.avgConfidence = (totalConfidence / violations.length) * 100;
                    // Update accuracy based on actual detections
                    this.stats.accuracy = this.stats.avgConfidence;
                } else {
                    this.stats.avgConfidence = 0;
                    this.stats.accuracy = 0;
                }

                // Find most common violation type
                const violationTypeMap = {};
                violations.forEach(v => {
                    const vtype = v.violation_type || 'Không xác định';
                    violationTypeMap[vtype] = (violationTypeMap[vtype] || 0) + 1;
                });
                
                if (Object.keys(violationTypeMap).length > 0) {
                    const topType = Object.entries(violationTypeMap)
                        .sort((a, b) => b[1] - a[1])[0];
                    this.stats.topViolationType = topType[0];
                    this.stats.topViolationTypeCount = topType[1];
                } else {
                    this.stats.topViolationType = '-';
                    this.stats.topViolationTypeCount = 0;
                }
                
                // Update top vehicles display
                this.updateTopVehicles(violations);
            }

            // Fetch tasks to count processed videos
            const tasksResp = await fetch('/api/tasks');
            if (tasksResp.ok) {
                const tasksData = await tasksResp.json();
                const tasks = tasksData.tasks || [];
                this.stats.processedVideos = tasks.filter(t => t.status === 'completed').length;
            }

            // Fetch server status for system info
            const statusResp = await fetch('/api/status');
            if (statusResp.ok) {
                const statusData = await statusResp.json();
                // Map backend metrics to dashboard
                this.stats.totalVehicles = statusData.total_detected_vehicles || 0;
                this.stats.totalViolations = statusData.total_violations || this.stats.totalViolations;
                this.stats.processedVideos = statusData.processed_videos || this.stats.processedVideos;
                const avgSec = statusData.avg_process_time_seconds || 0;
                const timeEl = document.getElementById('avgProcessTime');
                if (timeEl) timeEl.textContent = `~${Math.round(avgSec)}s`;
                this.addActivity('success', 'Hệ thống sẵn sàng', 'Ngay bây giờ');
            }

            // Update UI with real stats
            this.updateStats(this.stats);
        } catch (e) {
            console.error('Failed to load real stats:', e);
        }
    }
}

// Initialize dashboard when DOM is ready
let dashboard;
document.addEventListener('DOMContentLoaded', async () => {
    dashboard = new Dashboard();
    
    // Wait a bit for section to be visible before initializing charts
    setTimeout(() => {
        dashboard.initCharts();
    }, 500);
    
    // Load real data from API
    dashboard.loadRealStats();
});
