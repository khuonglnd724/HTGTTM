/* Main Application Logic */

class App {
    constructor() {
        this.uploadedFile = null;
        this.currentTaskId = null;
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
            UI.showToast('Invalid file type. Please upload a video or image.', 'error');
            return;
        }

        // Validate file size (500MB max)
        if (file.size > 500 * 1024 * 1024) {
            UI.showToast('File is too large. Maximum size is 500MB.', 'error');
            return;
        }

        this.uploadedFile = file;
        UI.setProcessButtonState(true);

        // Show file info
        const fileName = file.name;
        const fileSize = (file.size / 1024 / 1024).toFixed(2) + 'MB';
        UI.showUploadStatus(`File selected: ${fileName} (${fileSize})`, true);
    }

    async startProcessing() {
        if (!this.uploadedFile) {
            UI.showToast('Please select a file first', 'warning');
            return;
        }

        try {
            UI.setProcessButtonState(false);
            UI.showToast('Uploading file...', 'info');

            // Upload file
            const uploadResponse = await api.uploadFile('/upload', this.uploadedFile);
            
            UI.showToast('File uploaded. Starting processing...', 'info');

            // Determine file type
            const fileType = this.uploadedFile.type.startsWith('video') ? 'video' : 'image';

            // Start processing
            const processResponse = await api.post('/process', {
                input_path: uploadResponse.filepath,
                type: fileType
            });

            this.currentTaskId = processResponse.task_id;
            UI.showToast('Processing started!', 'success');

            // Switch to processing view
            UI.showSection('processing');
            this.refreshTasks();
            
            // Start refreshing task status
            this.taskRefreshInterval = setInterval(() => {
                this.refreshTasks();
            }, 1000);

        } catch (error) {
            UI.showToast('Error: ' + error.message, 'error');
            UI.setProcessButtonState(true);
        }
    }

    async refreshTasks() {
        try {
            const data = await api.get('/tasks');
            const tasksList = document.getElementById('tasksList');

            if (!data.tasks || data.tasks.length === 0) {
                tasksList.innerHTML = '<p class="empty-state">No active tasks</p>';
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
                resultsList.innerHTML = '<p class="empty-state">No results yet</p>';
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
                `Task: ${taskId}`,
                content,
                task.status === 'completed' ? () => this.downloadTask(taskId) : null
            );
        } catch (error) {
            UI.showToast('Error loading task details', 'error');
        }
    }

    async downloadTask(taskId) {
        try {
            window.location.href = `/api/download/${taskId}`;
            UI.showToast('Download started!', 'success');
        } catch (error) {
            UI.showToast('Error downloading file', 'error');
        }
    }

    async saveSettings() {
        try {
            const settings = UI.getSettingsData();
            await api.post('/config', settings);
            UI.showToast('Settings saved successfully!', 'success');
        } catch (error) {
            UI.showToast('Error saving settings: ' + error.message, 'error');
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
