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

        if (modalTitle) modalTitle.textContent = title;
        if (modalBody) modalBody.innerHTML = content;

        if (onDownload) {
            downloadBtn.classList.remove('hidden');
            downloadBtn.onclick = onDownload;
        } else {
            downloadBtn.classList.add('hidden');
        }

        if (modal) modal.classList.remove('hidden');
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

        const statusText = {
            'queued': 'CHỜ',
            'processing': 'ĐANG XỬ LÝ',
            'completed': 'HOÀN THÀNH',
            'failed': 'THẤT BẠI'
        };

        const progressPercent = task.progress || 0;

        return `
            <div class="task-card">
                        <div class="task-header">
                    <div class="task-title">${task.task_id}</div>
                    <div class="task-status ${statusColor[task.status]}">${statusText[task.status] || task.status.toUpperCase()}</div>
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

        const statusText = {
            'completed': 'HOÀN THÀNH',
            'failed': 'THẤT BẠI'
        };

        const hasVideo = task.result && task.result.stream_url;

        return `
            <div class="task-card">
                <div class="task-header">
                    <div class="task-title">${task.task_id}</div>
                    <div class="task-status ${statusColor[task.status]}">${statusText[task.status] || task.status.toUpperCase()}</div>
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
                        <td style="padding: 0.5rem; font-weight: bold;">Tổng số phương tiện phát hiện:</td>
                        <td style="padding: 0.5rem;">${analytics.total_vehicles || 0}</td>
                    </tr>
                    <tr>
                        <td style="padding: 0.5rem; font-weight: bold;">Tổng số phương tiện vi phạm:</td>
                        <td style="padding: 0.5rem;">${analytics.violating_vehicles || 0}</td>
                    </tr>
                    <tr>
                        <td style="padding: 0.5rem; font-weight: bold;">Tỷ lệ vi phạm:</td>
                        <td style="padding: 0.5rem;">${(() => {
                            const viol = Number(analytics.violating_vehicles || 0);
                            const denom = Number(analytics.total_vehicles || analytics.total_detections || 0);
                            const pct = denom > 0 ? (viol / denom) * 100 : 0;
                            return pct.toFixed(1) + '%';
                        })()}</td>
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

        // Show saved violation snapshots if available
        if (task.result && task.result.snapshots && task.result.snapshots.length > 0) {
            const snapshotsJson = JSON.stringify(task.result.snapshots || []);
            html += `
                <h4>Ảnh vi phạm</h4>
                <div class="snapshot-gallery" style="display:flex;flex-wrap:wrap;gap:8px;">
                    ${task.result.snapshots.map((s, i) => `
                        <div style="width:120px;">
                            <img src="${s.snapshot_url}" onclick='UI.openSnapshotGallery(${snapshotsJson}, ${i})' 
                                 style="width:120px;height:80px;object-fit:cover;border:1px solid #ccc;border-radius:4px;cursor:pointer;"/>
                            <div style="font-size:12px;margin-top:4px;">ID:${s.track_id}</div>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        return html;
    }
}

// Snapshot viewer (modal-like) methods
UI.openSnapshotGallery = function(snapshots, startIndex = 0) {
    if (!Array.isArray(snapshots) || snapshots.length === 0) return;
    this._snapshotData = snapshots;
    this._snapshotIndex = Math.max(0, Math.min(startIndex, snapshots.length - 1));

    // Create viewer DOM if missing
    if (!document.getElementById('snapshotViewer')) {
    const viewer = document.createElement('div');
        viewer.id = 'snapshotViewer';
        viewer.style.position = 'fixed';
        viewer.style.left = 0;
        viewer.style.top = 0;
        viewer.style.width = '100%';
        viewer.style.height = '100%';
        viewer.style.background = 'rgba(0,0,0,0.7)';
        viewer.style.display = 'flex';
        viewer.style.alignItems = 'center';
        viewer.style.justifyContent = 'center';
        viewer.style.zIndex = 9999;

        viewer.innerHTML = `
            <div id="snapshotInner" style="position:relative;max-width:90%;max-height:90%;background:#222;padding:10px;border-radius:6px;">
                <button id="snapshotClose" style="position:absolute;right:8px;top:8px;z-index:10;background:transparent;border:none;color:#fff;font-size:22px;">×</button>
                <div style="display:flex;align-items:center;gap:12px;">
                    <button id="snapshotPrev" class="btn" style="height:40px;">◀</button>
                    <div style="flex:1;text-align:center;position:relative;">
                        <div id="snapshotCanvasWrapper" style="position:relative;display:inline-block;">
                            <img id="snapshotImage" src="" style="display:block;max-width:100%;max-height:70vh;border-radius:4px;" />
                            <canvas id="snapshotOverlay" style="position:absolute;left:0;top:0;pointer-events:none;border-radius:4px;"></canvas>
                        </div>
                        <div id="snapshotCaption" style="color:#fff;margin-top:8px;font-size:14px;"></div>
                    </div>
                    <button id="snapshotNext" class="btn" style="height:40px;">▶</button>
                </div>
            </div>
        `;

        document.body.appendChild(viewer);

        // Attach handlers
        document.getElementById('snapshotClose').addEventListener('click', () => UI.closeSnapshotGallery());
        document.getElementById('snapshotPrev').addEventListener('click', () => UI.showSnapshot(UI._snapshotIndex - 1));
        document.getElementById('snapshotNext').addEventListener('click', () => UI.showSnapshot(UI._snapshotIndex + 1));
        // Close when clicking outside inner box
        viewer.addEventListener('click', (e) => {
            if (e.target === viewer) UI.closeSnapshotGallery();
        });

        // Keyboard navigation (left/right/esc)
        UI._snapshotKeyHandler = function(e) {
            if (!document.getElementById('snapshotViewer')) return;
            if (e.key === 'ArrowLeft') {
                UI.showSnapshot(UI._snapshotIndex - 1);
            } else if (e.key === 'ArrowRight') {
                UI.showSnapshot(UI._snapshotIndex + 1);
            } else if (e.key === 'Escape') {
                UI.closeSnapshotGallery();
            }
        };
        document.addEventListener('keydown', UI._snapshotKeyHandler);
    }

    UI.showSnapshot(this._snapshotIndex);
};

    UI.showSnapshot = function(index) {
    const data = this._snapshotData || [];
    if (!data || data.length === 0) return;
    // Wrap index
    if (index < 0) index = data.length - 1;
    if (index >= data.length) index = 0;
    this._snapshotIndex = index;

    const item = data[index];
    const img = document.getElementById('snapshotImage');
    const caption = document.getElementById('snapshotCaption');
    const canvas = document.getElementById('snapshotOverlay');

    if (img && caption && item) {
        // Update caption with counter
        caption.innerHTML = `ID: <strong>${item.track_id}</strong> — ${index + 1} / ${data.length}`;

        // Load image then draw bbox overlay (if bbox available)
        img.onload = function() {
            // Size the canvas to match displayed image size
            const wrapper = document.getElementById('snapshotCanvasWrapper');
            const rect = img.getBoundingClientRect();
            // Use image display size
            const dispW = img.clientWidth;
            const dispH = img.clientHeight;

            canvas.width = dispW;
            canvas.height = dispH;
            canvas.style.width = dispW + 'px';
            canvas.style.height = dispH + 'px';
            canvas.style.left = img.offsetLeft + 'px';
            canvas.style.top = img.offsetTop + 'px';

            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // Check for bounding box fields: support item.bbox or item.box (x1,y1,x2,y2)
            const bboxCandidates = item.bbox || item.box || item.box_xyxy || item.xyxy || null;
            if (Array.isArray(bboxCandidates) && bboxCandidates.length >= 4) {
                let [x1, y1, x2, y2] = bboxCandidates.map(Number);

                // Determine if coords are relative (0..1)
                const isRelative = (x1 > 0 && x1 <= 1) && (y1 > 0 && y1 <= 1);

                // Determine natural size to scale if coords are absolute
                const natW = img.naturalWidth || dispW;
                const natH = img.naturalHeight || dispH;

                const scaleX = dispW / natW;
                const scaleY = dispH / natH;

                if (isRelative) {
                    x1 = x1 * dispW;
                    y1 = y1 * dispH;
                    x2 = x2 * dispW;
                    y2 = y2 * dispH;
                } else {
                    x1 = x1 * scaleX;
                    y1 = y1 * scaleY;
                    x2 = x2 * scaleX;
                    y2 = y2 * scaleY;
                }

                // Draw rectangle
                ctx.strokeStyle = 'rgba(255,80,80,0.95)';
                ctx.lineWidth = Math.max(2, Math.round(Math.min(dispW, dispH) / 200));
                ctx.fillStyle = 'rgba(255,80,80,0.12)';
                ctx.beginPath();
                ctx.rect(x1, y1, Math.max(1, x2 - x1), Math.max(1, y2 - y1));
                ctx.fill();
                ctx.stroke();
            }
        };

        img.src = item.snapshot_url;
    }
};

UI.closeSnapshotGallery = function() {
    const viewer = document.getElementById('snapshotViewer');
    if (viewer) {
        viewer.remove();
        // clear cached data
        this._snapshotData = null;
        this._snapshotIndex = 0;
        // remove keyboard handler if present
        if (this._snapshotKeyHandler) {
            try { document.removeEventListener('keydown', this._snapshotKeyHandler); } catch (e) {}
            this._snapshotKeyHandler = null;
        }
    }
};

// Modal close handlers
document.querySelectorAll('.modal-close').forEach(btn => {
    btn.addEventListener('click', () => UI.closeModal());
});
