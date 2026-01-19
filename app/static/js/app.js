/* Main Application Logic */

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

        // Confidence slider
        document.getElementById('confidenceSlider').addEventListener('change', (e) => {
            UI.updateConfidenceSlider(e.target.value);
        });

        // Process button
        document.getElementById('processBtn').addEventListener('click', () => {
            this.startProcessing();
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
        UI.setProcessButtonState(true);

        // Show file info
        const fileName = file.name;
        const fileSize = (file.size / 1024 / 1024).toFixed(2) + 'MB';
            UI.showUploadStatus(`Đã chọn tệp: ${fileName} (${fileSize})`, true);
    }

    async startProcessing() {
        if (!this.uploadedFile) {
            UI.showToast('Vui lòng chọn tệp trước', 'warning');
            return;
        }

        try {
            UI.setProcessButtonState(false);
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
        } catch (error) {
            UI.showToast('Lỗi tải lên: ' + error.message, 'error');
            UI.setProcessButtonState(true);
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
            UI.setProcessButtonState(false);
            UI.showToast(`Bắt đầu xử lý cho ${selectedZoneIds.length} vùng...`, 'info');

            // Start processing with the current task ID and selected zones
            const processResponse = await api.post('/process', {
                task_id: this.currentTaskId,
                selected_zone_ids: selectedZoneIds
            });

            UI.showToast('Đã bắt đầu xử lý!', 'success');

            // Switch to processing view
            UI.showSection('processing');
            this.refreshTasks();
            
            // Start refreshing task status
            this.taskRefreshInterval = setInterval(() => {
                this.refreshTasks();
            }, 1000);

        } catch (error) {
            UI.showToast('Lỗi: ' + error.message, 'error');
            UI.setProcessButtonState(true);
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
}

// Initialize app when DOM is ready
let app;

document.addEventListener('DOMContentLoaded', () => {
    app = new App();
    console.log('Lane Violation Detection System initialized');
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (app) {
        app.stopTaskRefreshing();
    }
});
