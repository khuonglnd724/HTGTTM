/* Main Application Logic */

// Safety stub: if `UI` failed to load (syntax error in ui.js), provide minimal fallbacks
if (typeof window.UI === 'undefined') {
    window.UI = {
        showSection: function(name){
            document.querySelectorAll('.content-section').forEach(s=>s.classList.remove('active'));
            const el = document.getElementById(name+'-section'); if (el) el.classList.add('active');
        },
        updateConfidenceSlider: function(v){ const el=document.getElementById('confidenceValue'); if(el) el.textContent = (Number(v)||0).toFixed(1); },
        setProcessButtons: function(mainEnabled=false,zonesEnabled=false){ const btn=document.getElementById('processBtn'); if(btn){ btn.disabled = !mainEnabled; if(!mainEnabled) btn.classList.add('disabled'); else btn.classList.remove('disabled'); } },
        showUploadStatus: function(msg, ok=true){ const st=document.getElementById('uploadStatus'); if(st){ st.className = 'upload-status ' + (ok? 'success':'error'); st.innerHTML = `<div><span>${msg}</span></div>`; st.classList.remove('hidden'); } },
        showToast: function(msg,type='info',dur=3000){ const t=document.getElementById('toast'); if(!t) return; t.textContent = msg; t.className = `toast show ${type}`; setTimeout(()=>{ t.classList.remove('show'); }, dur); },
        renderTaskCard: function(t){ return `<div class="task-card"><div class="task-header"><div class="task-title">${t.task_id}</div></div></div>`; },
        renderResultCard: function(t){ return `<div class="task-card"><div class="task-header"><div class="task-title">${t.task_id}</div></div></div>`; }
    };
}

class App {
    constructor() {
        this.uploadedFile = null;
        this.currentTaskId = null;
        this.previewUrl = null;
        this.uploadedFilePath = null;
        this.taskRefreshInterval = null;
        this.statusCheckInterval = null;

        this.initEventListeners();
        this.checkStatus();
        this.startStatusChecking();

        // Ensure modals are closed on load to avoid overlay blocking clicks
        if (typeof UI !== 'undefined' && typeof UI.closeModal === 'function') {
            UI.closeModal();
        }

        // Hide zones menu until a file is uploaded
        const menuZonesBtn = document.getElementById('menuZonesBtn');
        if (menuZonesBtn) {
            menuZonesBtn.style.display = 'none';
        }
    }

    initEventListeners() {
        // Menu buttons
        document.querySelectorAll('.menu-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const section = e.currentTarget.dataset.section;
                UI.showSection(section);
                if (section === 'processing') this.refreshTasks();
                if (section === 'results') this.refreshResults();
            });
        });

        // Upload area
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');

        uploadArea.addEventListener('click', () => fileInput.click());
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.style.opacity = '0.7';
        });
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.style.opacity = '1';
        });
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.style.opacity = '1';
            this.handleFileSelect(e.dataTransfer.files[0]);
        });

        fileInput.addEventListener('change', (e) => {
            this.handleFileSelect(e.target.files[0]);
        });

        // Confidence slider - update live while dragging
        const confSlider = document.getElementById('confidenceSlider');
        if (confSlider) {
            confSlider.addEventListener('input', (e) => {
                UI.updateConfidenceSlider(e.target.value);
            });
        }

        // Process button: navigate to zones UI or start upload+zones when file present
        const processBtn = document.getElementById('processBtn');
        if (processBtn) processBtn.addEventListener('click', () => {
            if (this.uploadedFile) {
                // If a file is selected, upload it (creates task) then switch to zones
                this.startProcessing();
            } else {
                // No file yet: just open zones editor (task may be null)
                UI.showSection('zones');
                try {
                    const currentTaskId = (window.AppState && window.AppState.currentTaskId) ? window.AppState.currentTaskId : null;
                    if (!window.zoneEditor || window.zoneEditor.taskId !== currentTaskId) {
                        window.zoneEditor = new ZoneEditor(currentTaskId);
                    }
                } catch (e) {
                    console.error('Failed to initialize ZoneEditor:', e);
                }
            }
        });

        // Settings
        document.getElementById('savSettingsBtn').addEventListener('click', () => {
            this.saveSettings();
        });

        // Filter buttons
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.refreshResults();
            });
        });

        // Show Zones section when file is uploaded
        document.getElementById('fileInput')?.addEventListener('change', () => {
            this.showZonesSection();
        });
    }

    async loadVehiclesViolations() {
        try {
            const response = await fetch('/api/violations');
            if (!response.ok) return;
            const data = await response.json();
            const violations = data.violations || [];

            // Group violations by track_id (vehicle)
            const vehicleMap = {};
            violations.forEach(v => {
                const trackId = v.track_id || 'Unknown';
                if (!vehicleMap[trackId]) {
                    vehicleMap[trackId] = {
                        track_id: trackId,
                        vehicle_type: v.vehicle_type || 'Unknown',
                        violations: []
                    };
                }
                vehicleMap[trackId].violations.push(v);
            });

            // Get unique vehicles and count violations
            const vehicles = Object.values(vehicleMap);
            const totalCount = vehicles.length;

            // Update total vehicles count
            const totalViolatingVehicles = document.getElementById('totalViolatingVehicles');
            if (totalViolatingVehicles) {
                totalViolatingVehicles.textContent = totalCount;
            }

            // Render vehicles list
            const vehiclesList = document.getElementById('vehiclesViolatingList');
            if (vehiclesList) {
                if (vehicles.length === 0) {
                    vehiclesList.innerHTML = '<p class="empty-state">Chưa có xe vi phạm</p>';
                } else {
                    vehiclesList.innerHTML = vehicles.map(v => `
                        <div class="vehicle-violation-item">
                            <h4>Xe #${v.track_id}</h4>
                            <p><strong>Loại:</strong> ${v.vehicle_type}</p>
                            <p><strong>Vi phạm:</strong> ${v.violations.length} lần</p>
                        </div>
                    `).join('');
                }
            }
        } catch (error) {
            console.error('Error loading vehicles violations:', error);
        }
    }

    showZonesSection() {
        const zonesSection = document.getElementById('zones-section');
        if (zonesSection) {
            zonesSection.style.display = 'block';
        }
    }

    async handleFileSelect(file) {
        if (!file) return;

        // Validate file type
        const validTypes = ['video/mp4', 'video/avi', 'video/quicktime', 'video/x-matroska', 'image/jpeg', 'image/png'];
        if (!validTypes.some(type => file.type.startsWith(type.split('/')[0]))) {
            UI.showToast('Loại tệp không hợp lệ. Vui lòng tải lên video hoặc hình ảnh.', 'error');
            return;
        }

        // Validate file size (500MB max)
        if (file.size > 500 * 1024 * 1024) {
            UI.showToast('Tệp quá lớn. Kích thước tối đa 500MB.', 'error');
            return;
        }

        this.uploadedFile = file;
        // Enable the upload-page process button so user can navigate to zone editor
        UI.setProcessButtons(true, false);

        // Show file info
        const fileName = file.name;
        const fileSize = (file.size / 1024 / 1024).toFixed(2) + 'MB';
            UI.showUploadStatus(`Đã chọn tệp: ${fileName} (${fileSize})`, true);
    }

    async loadViolationsImages() {
        // Load violations images folder after upload
        try {
            const response = await fetch('/api/violations');
            if (!response.ok) return;
            const data = await response.json();
            const violations = data.violations || [];
            
            // Display images without forcing a section jump
            if (violations.length > 0 && typeof this.renderViolations === 'function') {
                this.renderViolations(violations);
            }
        } catch (e) {
            console.log('Could not auto-load violations:', e.message);
        }
    }

    async startProcessing() {
        if (!this.uploadedFile) {
            UI.showToast('Vui lòng chọn tệp trước', 'warning');
            return;
        }

        try {
            UI.setProcessButtons(false, false);
            UI.showToast('Đang tải tập tin...', 'info');

            // Upload file
            const uploadResponse = await api.uploadFile('/upload', this.uploadedFile);
            
            // Store task ID and preview URL
            this.currentTaskId = uploadResponse.task_id;
            this.uploadedFilePath = uploadResponse.filepath;
            this.previewUrl = uploadResponse.preview_url;
            
            // Store in global state for zones editor
            window.AppState = {
                currentTaskId: this.currentTaskId,
                previewUrl: this.previewUrl,
                uploadedFilePath: this.uploadedFilePath
            };
            
            UI.showToast('Tập tin đã tải lên. Vui lòng định nghĩa vùng trước khi xử lý...', 'info');

            // Update dashboard
            if (window.dashboard) {
                window.dashboard.addActivity('success', `Đã tải lên tập tin: ${this.uploadedFile.name.substring(0, 30)}`);
                setTimeout(() => window.dashboard.loadRealStats(), 500);
            }

            // Switch to zones view for zone definition
            UI.showSection('zones');
            // Ensure zone editor is initialized with current task
            try {
                const currentTaskId = this.currentTaskId;
                if (!window.zoneEditor || window.zoneEditor.taskId !== currentTaskId) {
                    window.zoneEditor = new ZoneEditor(currentTaskId);
                }
            } catch (e) {
                console.error('Failed to initialize ZoneEditor:', e);
            }
            
            // Show frame preview in zones editor if available
            if (uploadResponse.preview_url) {
                const previewImg = document.querySelector('#zonesCanvas');
                if (previewImg) {
                    // Load preview as background in zone editor
                    const img = new Image();
                    img.onload = () => {
                        const canvas = previewImg;
                        const ctx = canvas.getContext('2d');
                        canvas.width = 1280;
                        canvas.height = 720;
                        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                    };
                    img.src = uploadResponse.preview_url;
                }
            }
            // Ensure zones-panel process button remains disabled until zones created
            UI.setProcessButtons(true, false);
            
            // Auto-load violations images folder after 5 seconds
            setTimeout(() => {
                this.loadViolationsImages();
            }, 5000);
        } catch (error) {
            UI.showToast('Lỗi tải lên: ' + error.message, 'error');
            UI.setProcessButtons(true, false);
        }
    }

    async processWithZones() {
        if (!this.currentTaskId) {
            UI.showToast('Chưa chọn tác vụ', 'warning');
            return;
        }

        // Get all checked zones from the zones list
        const checkboxes = document.querySelectorAll('#zonesList .zone-checkbox:checked');
        if (checkboxes.length === 0) {
            UI.showToast('Vui lòng chọn ít nhất một vùng để xử lý', 'warning');
            return;
        }

        const selectedZoneIds = Array.from(checkboxes).map(cb => cb.dataset.zoneId);

        try {
            UI.setProcessButtons(false, false);
            UI.showToast(`Bắt đầu xử lý cho ${selectedZoneIds.length} vùng...`, 'info');

            // Include current form options (model, confidence, frame_skip, draw flags)
            const options = UI.getFormData();

            // Start processing with the current task ID, selected zones and options
            const processResponse = await api.post('/process', {
                task_id: this.currentTaskId,
                selected_zone_ids: selectedZoneIds,
                options: options
            });

            UI.showToast('Đã bắt đầu xử lý!', 'success');

            // Switch to processing view
            UI.showSection('processing');
            this.refreshTasks();
            
            // Update dashboard
            if (window.dashboard) {
                window.dashboard.addActivity('info', `Bắt đầu xử lý: ${selectedZoneIds.length} vùng`);
                setTimeout(() => window.dashboard.loadRealStats(), 500);
            }
            
            // Start refreshing task status
            this.taskRefreshInterval = setInterval(() => {
                this.refreshTasks();
            }, 1000);

        } catch (error) {
            UI.showToast('Lỗi: ' + error.message, 'error');
            UI.setProcessButtons(true, true);
        }
    }

    async refreshTasks() {
        try {
            const data = await api.get('/tasks');
            const tasksList = document.getElementById('tasksList');

            if (!data.tasks || data.tasks.length === 0) {
                tasksList.innerHTML = '<p class="empty-state">Không có tác vụ đang chạy</p>';
                return;
            }

            tasksList.innerHTML = data.tasks.map(task => UI.renderTaskCard(task)).join('');
        } catch (error) {
            console.error('Error refreshing tasks:', error);
        }
    }

    async refreshResults() {
        try {
            const data = await api.get('/tasks');
            const resultsList = document.getElementById('resultsList');
            const activeFilter = document.querySelector('.filter-btn.active')?.dataset.filter || 'all';

            let tasks = data.tasks || [];

            // Filter tasks
            if (activeFilter !== 'all') {
                tasks = tasks.filter(t => {
                    if (activeFilter === 'completed') return t.status === 'completed';
                    if (activeFilter === 'failed') return t.status === 'failed';
                    return true;
                });
            }

            // Only show completed or failed tasks
            tasks = tasks.filter(t => t.status === 'completed' || t.status === 'failed');

            if (tasks.length === 0) {
                resultsList.innerHTML = '<p class="empty-state">Chưa có kết quả</p>';
                return;
            }

            // Fetch detailed info for each task
            const detailedTasks = await Promise.all(
                tasks.map(task => api.get(`/task/${task.task_id}`))
            );

            resultsList.innerHTML = detailedTasks.map(task => UI.renderResultCard(task)).join('');
            
            // Calculate and display statistics
            let totalDetected = 0;
            let totalViolating = 0;
            let totalViolations = 0;
            let totalConfidence = 0;
            let count = 0;
            
            detailedTasks.forEach(task => {
                const analytics = task.analytics || {};
                totalDetected += analytics.total_vehicles || 0;
                totalViolating += analytics.violating_vehicles || 0;
                totalViolations += analytics.total_violations || 0;
                if (analytics.avg_confidence) {
                    totalConfidence += analytics.avg_confidence;
                    count++;
                }
            });
            
            const avgConfidence = count > 0 ? (totalConfidence / count * 100).toFixed(1) : '-';
            
            const totalDetectedEl = document.getElementById('totalDetectedVehicles');
            const totalViolatingEl = document.getElementById('totalViolatingVehicles2');
            const totalViopsEl = document.getElementById('totalViolationsCount');
            const avgAccuracyEl = document.getElementById('avgAccuracyResults');
            
            if (totalDetectedEl) totalDetectedEl.textContent = totalDetected;
            if (totalViolatingEl) totalViolatingEl.textContent = totalViolating;
            if (totalViopsEl) totalViopsEl.textContent = totalViolations;
            if (avgAccuracyEl) avgAccuracyEl.textContent = avgConfidence !== '-' ? avgConfidence + '%' : '-';
        } catch (error) {
            console.error('Error refreshing results:', error);
        }
    }

    async viewTask(taskId) {
        try {
            const task = await api.get(`/task/${taskId}`);
            const content = UI.getTaskDetailsHTML(task);
            
            UI.showModal(
                `Tác vụ: ${taskId}`,
                content,
                task.status === 'completed' ? () => this.downloadTask(taskId) : null
            );
        } catch (error) {
            UI.showToast('Lỗi tải thông tin tác vụ', 'error');
        }
    }

    async viewResult(taskId) {
        try {
            const task = await api.get(`/task/${taskId}`);
            if (!task.result || !task.result.stream_url) {
                UI.showToast('Không tìm thấy video kết quả', 'warning');
                return;
            }
            const content = `
                <h4>Result Video</h4>
                <video style="width: 100%; max-height: 480px;" controls src="${task.result.stream_url}"></video>
            `;
            UI.showModal(`Tác vụ: ${taskId} - Xem trước`, content, () => this.downloadTask(taskId));
        } catch (error) {
            UI.showToast('Lỗi tải kết quả', 'error');
        }
    }

    async downloadTask(taskId) {
        try {
            window.location.href = `/api/download/${taskId}`;
            UI.showToast('Bắt đầu tải xuống!', 'success');
        } catch (error) {
            UI.showToast('Lỗi khi tải xuống', 'error');
        }
    }

    async saveSettings() {
        try {
            const settings = UI.getSettingsData();
            await api.post('/config', settings);
            UI.showToast('Lưu cài đặt thành công!', 'success');
        } catch (error) {
            UI.showToast('Lỗi lưu cài đặt: ' + error.message, 'error');
        }
    }

    async checkStatus() {
        try {
            const data = await api.get('/status');
            UI.updateStatus(true);
        } catch (error) {
            UI.updateStatus(false);
        }
    }

    startStatusChecking() {
        this.statusCheckInterval = setInterval(() => {
            this.checkStatus();
        }, 5000);
    }

    stopTaskRefreshing() {
        if (this.taskRefreshInterval) {
            clearInterval(this.taskRefreshInterval);
        }
    }

    // === NEW FEATURES ===

    async filterViolations() {
        const dateFilter = document.getElementById('violationDateFilter')?.value || 'all';
        const vehicleFilter = document.getElementById('violationVehicleFilter')?.value || 'all';
        const zoneFilter = document.getElementById('violationZoneFilter')?.value || 'all';

        try {
            const data = await api.get(`/violations?date=${dateFilter}&vehicle=${vehicleFilter}&zone=${zoneFilter}`);
            let violations = data.violations || [];
            
            // Apply client-side filtering for vehicle type
            if (vehicleFilter && vehicleFilter !== 'all') {
                // Map filter values to Vietnamese vehicle types
                const vehicleTypeMap = {
                    'car': 'Ô tô',
                    'motorcycle': 'Xe máy',
                    'bus': 'Xe buýt',
                    'truck': 'Xe tải'
                };
                const targetType = vehicleTypeMap[vehicleFilter];
                if (targetType) {
                    violations = violations.filter(v => v.vehicle_type === targetType);
                }
            }
            
            this.renderViolations(violations);
        } catch (error) {
            console.error('Error filtering violations:', error);
            UI.showToast('Lỗi tải danh sách vi phạm', 'error');
        }
    }

    renderViolations(violations) {
        const violationsList = document.getElementById('violationsList');
        if (!violationsList) return;

        if (violations.length === 0) {
            violationsList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-search"></i>
                    <p>Không tìm thấy vi phạm nào</p>
                </div>
            `;
            return;
        }

        // Group violations by vehicle_type
        const grouped = {};
        violations.forEach(v => {
            if (!grouped[v.vehicle_type]) {
                grouped[v.vehicle_type] = [];
            }
            grouped[v.vehicle_type].push(v);
        });

        // Generate HTML for grouped violations
        let html = '';
        for (const [vehicleType, items] of Object.entries(grouped)) {
            html += `
                <div class="violation-group" style="margin-bottom: 2rem;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; font-weight: 600; display: flex; align-items: center; gap: 0.5rem;">
                        <i class="fas fa-car"></i>
                        ${vehicleType} (${items.length} vi phạm)
                    </div>
                    <div class="violation-items">
                        ${items.map(v => `
                            <div class="task-card" style="margin-bottom: 1rem;">
                                <div class="task-header">
                                    <div class="task-title">${v.zone_name}</div>
                                    <span class="task-status failed">${v.violation_type}</span>
                                </div>
                                <div class="task-info">
                                    <div class="task-info-item">
                                        <span class="task-info-label">Thời gian:</span>
                                        <span>${new Date(v.timestamp).toLocaleString('vi-VN')}</span>
                                    </div>
                                    <div class="task-info-item">
                                        <span class="task-info-label">Độ tin cậy:</span>
                                        <span>${(v.confidence * 100).toFixed(1)}%</span>
                                    </div>
                                    <div class="task-info-item">
                                        <span class="task-info-label">Frame:</span>
                                        <span>#${v.frame || 'N/A'}</span>
                                    </div>
                                </div>
                                ${v.snapshot_url ? `<img src="${v.snapshot_url}" alt="Snapshot" style="width: 100%; height: auto; max-width: 600px; border-radius: 0.5rem; margin-top: 1rem; box-shadow: 0 2px 8px rgba(0,0,0,0.1); object-fit: contain;">` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        violationsList.innerHTML = html;
    }

    async exportPDFReport() {
        const period = document.getElementById('pdfReportPeriod')?.value || 'today';
        try {
            UI.showToast('Đang tạo báo cáo PDF...', 'info');
            window.location.href = `/api/export/pdf?period=${period}`;
            UI.showToast('Đã tải báo cáo PDF!', 'success');
            
            if (window.dashboard) {
                dashboard.addActivity('success', `Đã xuất báo cáo PDF (${period})`);
                setTimeout(() => dashboard.loadRealStats(), 1000);
            }
        } catch (error) {
            UI.showToast('Lỗi xuất PDF: ' + error.message, 'error');
        }
    }

    async exportCSVReport() {
        const includeViolations = document.getElementById('csvIncludeViolations')?.checked || false;
        const includeVehicles = document.getElementById('csvIncludeVehicles')?.checked || false;
        const includeZones = document.getElementById('csvIncludeZones')?.checked || false;

        try {
            UI.showToast('Đang tạo báo cáo CSV...', 'info');
            const params = new URLSearchParams({
                violations: includeViolations,
                vehicles: includeVehicles,
                zones: includeZones
            });
            window.location.href = `/api/export/csv?${params}`;
            UI.showToast('Đã tải báo cáo CSV!', 'success');
            
            if (window.dashboard) {
                dashboard.addActivity('success', 'Đã xuất báo cáo CSV');
                setTimeout(() => dashboard.loadRealStats(), 1000);
            }
        } catch (error) {
            UI.showToast('Lỗi xuất CSV: ' + error.message, 'error');
        }
    }

    async exportViolationClips() {
        const format = document.getElementById('clipsFormat')?.value || 'full';
        try {
            UI.showToast('Đang tạo hình ảnh vi phạm...', 'info');
            window.location.href = `/api/export/clips?format=${format}`;
            UI.showToast('Đã tải hình ảnh vi phạm!', 'success');
            
            if (window.dashboard) {
                dashboard.addActivity('success', `Đã xuất hình ảnh (${format})`);
                setTimeout(() => dashboard.loadRealStats(), 1000);
            }
        } catch (error) {
            UI.showToast('Lỗi xuất hình ảnh: ' + error.message, 'error');
        }
    }

    async exportVideoClips() {
        try {
            UI.showToast('Đang cắt video vi phạm (5s mỗi clip)...', 'info');
            window.location.href = '/api/export/video-clips';
            
            // Show longer timeout for video processing
            setTimeout(() => {
                UI.showToast('Đã tải video clips vi phạm!', 'success');
                
                if (window.dashboard) {
                    dashboard.addActivity('success', 'Đã xuất video clip vi phạm (5s)');
                    setTimeout(() => dashboard.loadRealStats(), 1000);
                }
            }, 2000);
        } catch (error) {
            UI.showToast('Lỗi xuất video: ' + error.message, 'error');
        }
    }

    async exportFullReport() {
        const period = document.getElementById('fullReportPeriod')?.value || 'today';
        try {
            UI.showToast('Đang tạo báo cáo đầy đủ...', 'info');
            window.location.href = `/api/export/full?period=${period}`;
            UI.showToast('Đã tải báo cáo đầy đủ!', 'success');
            
            if (window.dashboard) {
                dashboard.addActivity('success', `Đã xuất báo cáo đầy đủ (${period})`);
                setTimeout(() => dashboard.loadRealStats(), 1000);
            }
        } catch (error) {
            UI.showToast('Lỗi xuất báo cáo: ' + error.message, 'error');
        }
    }
}

// Initialize app when DOM is ready
let app;

function initApp() {
    app = new App();
    console.log('Lane Violation Detection System initialized');
}

// Check if DOM is already loaded, otherwise wait for DOMContentLoaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    // DOM is already loaded
    initApp();
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (app) {
        app.stopTaskRefreshing();
    }
});
