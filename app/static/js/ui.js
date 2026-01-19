/* UI Module */

class UI {
    static showSection(sectionName) {
        // Hide all sections
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });

        // Deactivate all menu buttons
        document.querySelectorAll('.menu-btn').forEach(btn => {
            btn.classList.remove('active');
        });

        // Show selected section
        const section = document.getElementById(`${sectionName}-section`);
        if (section) {
            section.classList.add('active');
        }

        // Activate corresponding menu button
        const btn = document.querySelector(`[data-section="${sectionName}"]`);
        if (btn) {
            btn.classList.add('active');
        }
    }

    static showToast(message, type = 'info', duration = 3000) {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.className = `toast show ${type}`;

        setTimeout(() => {
            toast.classList.remove('show');
        }, duration);
    }

    static showModal(title, content, onDownload = null) {
        const modal = document.getElementById('taskModal');
        const modalTitle = document.getElementById('modalTitle');
        const modalBody = document.getElementById('modalBody');
        const downloadBtn = document.getElementById('downloadBtn');

        modalTitle.textContent = title;
        modalBody.innerHTML = content;

        if (onDownload) {
            downloadBtn.classList.remove('hidden');
            downloadBtn.onclick = onDownload;
        } else {
            downloadBtn.classList.add('hidden');
        }

        modal.classList.remove('hidden');
    }

    static closeModal() {
        document.getElementById('taskModal').classList.add('hidden');
    }

    static updateStatus(online = true) {
        const indicator = document.getElementById('statusIndicator');
        const statusText = document.getElementById('statusText');

        if (online) {
            indicator.classList.remove('offline');
            statusText.textContent = 'Trực tuyến';
        } else {
            indicator.classList.add('offline');
            statusText.textContent = 'Không kết nối';
        }
    }

    static renderTaskCard(task) {
        const statusColor = {
            'queued': 'processing',
            'processing': 'processing',
            'completed': 'completed',
            'failed': 'failed'
        };

        const progressPercent = task.progress || 0;

        return `
            <div class="task-card">
                        <div class="task-header">
                    <div class="task-title">${task.task_id}</div>
                    <div class="task-status ${statusColor[task.status]}">${task.status.toUpperCase()}</div>
                </div>
                ${task.status === 'processing' ? `
                    <div class="task-progress">
                        <div class="task-progress-bar">
                            <div class="task-progress-fill" style="width: ${progressPercent}%"></div>
                        </div>
                        <div class="task-progress-text">${progressPercent}%</div>
                    </div>
                ` : ''}
                <div class="task-info">
                    <div class="task-info-item">
                        <span class="task-info-label">Loại:</span>
                        <span>${task.type}</span>
                    </div>
                    <div class="task-info-item">
                        <span class="task-info-label">Trạng thái:</span>
                        <span>${task.status}</span>
                    </div>
                </div>
                <div class="task-actions">
                    <button class="btn btn-secondary small" onclick="app.viewTask('${task.task_id}')">
                        Xem
                    </button>
                    ${task.status === 'completed' ? `
                        <button class="btn btn-primary small" onclick="app.downloadTask('${task.task_id}')">
                            Tải xuống
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
    }

    static renderResultCard(task) {
        const analytics = task.analytics || {};
        const statusColor = {
            'completed': 'success',
            'failed': 'danger'
        };

        const hasVideo = task.result && task.result.stream_url;

        return `
            <div class="task-card">
                <div class="task-header">
                    <div class="task-title">${task.task_id}</div>
                    <div class="task-status ${statusColor[task.status]}">${task.status.toUpperCase()}</div>
                </div>
                <div class="task-info">
                    <div class="task-info-item">
                        <span class="task-info-label">Thời lượng:</span>
                        <span>${analytics.duration_seconds ? analytics.duration_seconds.toFixed(2) + 's' : 'N/A'}</span>
                    </div>
                    <div class="task-info-item">
                        <span class="task-info-label">FPS:</span>
                        <span>${analytics.fps ? analytics.fps.toFixed(2) : 'N/A'}</span>
                    </div>
                    <div class="task-info-item">
                        <span class="task-info-label">Khung:</span>
                        <span>${analytics.frames_processed || 0}</span>
                    </div>
                    <div class="task-info-item">
                        <span class="task-info-label">Vi phạm:</span>
                        <span>${analytics.total_violations || 0}</span>
                    </div>
                </div>
                ${task.error_message ? `
                    <div class="task-info mt-2 text-small" style="color: var(--danger-color);">
                        Lỗi: ${task.error_message}
                    </div>
                ` : ''}
                <div class="task-actions">
                    <button class="btn btn-secondary small" onclick="app.viewTask('${task.task_id}')">
                        Chi tiết
                    </button>
                    ${hasVideo ? `
                        <button class="btn btn-primary small" onclick="app.viewResult('${task.task_id}')">
                            Xem
                        </button>
                    ` : ''}
                    ${task.status === 'completed' ? `
                        <button class="btn btn-primary small" onclick="app.downloadTask('${task.task_id}')">
                            Tải xuống
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
    }

    static showUploadProgress(percent) {
        const progressDiv = document.getElementById('uploadProgress');
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');

        progressDiv.classList.remove('hidden');
        progressFill.style.width = percent + '%';
        progressText.textContent = percent + '%';
    }

    static hideUploadProgress() {
        document.getElementById('uploadProgress').classList.add('hidden');
    }

    static showUploadStatus(message, success = true) {
        const statusDiv = document.getElementById('uploadStatus');
        statusDiv.className = `upload-status ${success ? 'success' : 'error'}`;
        statusDiv.innerHTML = `
            <div>
                <span>${message}</span>
            </div>
        `;
        statusDiv.classList.remove('hidden');
    }

    static hideUploadStatus() {
        document.getElementById('uploadStatus').classList.add('hidden');
    }

    static updateConfidenceSlider(value) {
        const num = Number(value);
        if (Number.isFinite(num)) {
            document.getElementById('confidenceValue').textContent = num.toFixed(1);
        } else {
            document.getElementById('confidenceValue').textContent = value;
        }
    }

    static getFormData() {
        return {
            model: document.getElementById('modelSelect').value,
            confidence: parseFloat(document.getElementById('confidenceSlider').value),
            frame_skip: parseInt(document.getElementById('frameSkipInput')?.value || '1', 10),
            drawConfidence: document.getElementById('drawConfidence').checked,
            drawTrajectories: document.getElementById('drawTrajectories').checked
        };
    }

    static getSettingsData() {
        return {
            'yolo.model_name': document.getElementById('settingsModel').value,
            'yolo.confidence_threshold': parseFloat(document.getElementById('settingsConfidence').value),
            'yolo.device': document.getElementById('settingsDevice').value,
            'lane_detection.canny_threshold1': parseInt(document.getElementById('settingsCanny1').value),
            'lane_detection.canny_threshold2': parseInt(document.getElementById('settingsCanny2').value),
            'lane_detection.hough_threshold': parseInt(document.getElementById('settingsHough').value)
        };
    }

    static setProcessButtonState(enabled) {
        // Backwards-compatible: enable/disable both buttons
        UI.setProcessButtons(enabled, enabled);
    }

    static setProcessButtons(mainEnabled = false, zonesEnabled = false) {
        const btnMain = document.getElementById('processBtn');
        const btnZones = document.getElementById('processZonesBtn');

        const apply = (el, enabled) => {
            if (!el) return;
            if (enabled) {
                el.disabled = false;
                el.classList.remove('disabled');
            } else {
                el.disabled = true;
                el.classList.add('disabled');
            }
        };

        apply(btnMain, mainEnabled);
        apply(btnZones, zonesEnabled);
    }

    static getTaskDetailsHTML(task) {
        const analytics = task.analytics || {};
        
        let html = `
            <h4>Thông tin tác vụ</h4>
            <table style="width: 100%; margin-bottom: 1rem;">
                <tr>
                    <td style="padding: 0.5rem; font-weight: bold;">Task ID:</td>
                    <td style="padding: 0.5rem;">${task.task_id}</td>
                </tr>
                <tr>
                    <td style="padding: 0.5rem; font-weight: bold;">Status:</td>
                    <td style="padding: 0.5rem;">${task.status}</td>
                </tr>
                <tr>
                    <td style="padding: 0.5rem; font-weight: bold;">Type:</td>
                    <td style="padding: 0.5rem;">${task.type || 'video'}</td>
                </tr>
                <tr>
                    <td style="padding: 0.5rem; font-weight: bold;">Start Time:</td>
                    <td style="padding: 0.5rem;">${task.start_time ? new Date(task.start_time).toLocaleString() : 'N/A'}</td>
                </tr>
                <tr>
                    <td style="padding: 0.5rem; font-weight: bold;">End Time:</td>
                    <td style="padding: 0.5rem;">${task.end_time ? new Date(task.end_time).toLocaleString() : 'N/A'}</td>
                </tr>
            </table>
        `;

        if (analytics.frames_processed) {
            html += `
                <h4>Thống kê xử lý</h4>
                <table style="width: 100%; margin-bottom: 1rem;">
                    <tr>
                        <td style="padding: 0.5rem; font-weight: bold;">Frames Processed:</td>
                        <td style="padding: 0.5rem;">${analytics.frames_processed}</td>
                    </tr>
                    <tr>
                        <td style="padding: 0.5rem; font-weight: bold;">Duration:</td>
                        <td style="padding: 0.5rem;">${analytics.duration_seconds?.toFixed(2)}s</td>
                    </tr>
                    <tr>
                        <td style="padding: 0.5rem; font-weight: bold;">FPS:</td>
                        <td style="padding: 0.5rem;">${analytics.fps?.toFixed(2)}</td>
                    </tr>
                    <tr>
                        <td style="padding: 0.5rem; font-weight: bold;">Total Detections:</td>
                        <td style="padding: 0.5rem;">${analytics.total_detections}</td>
                    </tr>
                    <tr>
                        <td style="padding: 0.5rem; font-weight: bold;">Total Violations:</td>
                        <td style="padding: 0.5rem;">${analytics.total_violations}</td>
                    </tr>
                    <tr>
                        <td style="padding: 0.5rem; font-weight: bold;">Violating Vehicles:</td>
                        <td style="padding: 0.5rem;">${analytics.violating_vehicles}</td>
                    </tr>
                    <tr>
                        <td style="padding: 0.5rem; font-weight: bold;">Violation Rate:</td>
                        <td style="padding: 0.5rem;">${(analytics.violation_rate * 100).toFixed(1)}%</td>
                    </tr>
                </table>
            `;
        }

        if (task.error_message) {
            html += `
                <h4 style="color: var(--danger-color);">Lỗi</h4>
                <p>${task.error_message}</p>
            `;
        }

        if (task.result && task.result.stream_url) {
            html += `
                <h4>Video kết quả</h4>
                <video style="width: 100%; max-height: 360px;" controls src="${task.result.stream_url}"></video>
            `;
        }

        return html;
    }
}

// Modal close handlers
document.querySelectorAll('.modal-close').forEach(btn => {
    btn.addEventListener('click', () => UI.closeModal());
});
