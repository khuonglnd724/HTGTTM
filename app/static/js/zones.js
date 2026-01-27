/* Zone Management Module */

class ZoneEditor {
    constructor(taskId = null) {
        this.canvas = document.getElementById('zonesCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.currentPolygon = [];
        this.zones = [];
        this.isDrawing = false;
        this.taskId = taskId;
        this.backgroundImage = null;
        
        console.log(`ZoneEditor initialized with taskId: ${taskId}`);
        
        this.setupCanvas();
        this.initEventListeners();
        
        // Load preview image from global state
        if (window.AppState && window.AppState.previewUrl) {
            console.log('AppState found, loading preview:', window.AppState.previewUrl);
            this.loadPreviewImage(window.AppState.previewUrl);
        } else {
            console.warn('No AppState or previewUrl found at initialization');
        }
        
        // Load zones for this task
        this.loadZones();
    }

    setupCanvas() {
        this.canvas.width = 1280;
        this.canvas.height = 720;
        this.ctx.fillStyle = '#1a1a1a';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        this.drawGrid();
    }

    drawGrid() {
        this.ctx.strokeStyle = '#333';
        this.ctx.lineWidth = 1;
        
        for (let x = 0; x < this.canvas.width; x += 40) {
            this.ctx.beginPath();
            this.ctx.moveTo(x, 0);
            this.ctx.lineTo(x, this.canvas.height);
            this.ctx.stroke();
        }
        
        for (let y = 0; y < this.canvas.height; y += 40) {
            this.ctx.beginPath();
            this.ctx.moveTo(0, y);
            this.ctx.lineTo(this.canvas.width, y);
            this.ctx.stroke();
        }
    }

    loadPreviewImage(previewUrl) {
        console.log('Loading preview from:', previewUrl);
        
        if (!previewUrl) {
            console.warn('No preview URL provided');
            return;
        }
        
        const img = new Image();
        
        img.onload = () => {
            console.log('Preview loaded successfully. Size:', img.width, 'x', img.height);
            this.backgroundImage = img;
            this.redraw();
        };
        
        img.onerror = (err) => {
            console.error('Failed to load preview image:', err);
            console.error('Preview URL was:', previewUrl);
        };
        
        img.src = previewUrl;
    }

    initEventListeners() {
        this.canvas.addEventListener('click', (e) => this.handleCanvasClick(e));
        this.canvas.addEventListener('dblclick', (e) => this.handleCanvasDoubleClick(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleCanvasMouseMove(e));
        
        const addBtn = document.getElementById('addZoneBtn');
        const clearBtn = document.getElementById('clearZonesBtn');
        const saveBtn = document.getElementById('saveZoneBtn');
        
        if (addBtn) addBtn.addEventListener('click', () => this.startDrawing());
        if (clearBtn) clearBtn.addEventListener('click', () => this.clearAllZones());
        if (saveBtn) saveBtn.addEventListener('click', () => this.saveCurrentZone());
        
        const closeBtn = document.querySelector('#zoneEditorModal .modal-close');
        if (closeBtn) closeBtn.addEventListener('click', () => this.hideZoneEditor());
    }

    startDrawing() {
        this.isDrawing = true;
        this.currentPolygon = [];
        UI.showToast('Nhấp để thêm điểm. Nhấp đúp để hoàn tất.', 'info');
    }

    handleCanvasClick(e) {
        if (!this.isDrawing) return;
        
        const rect = this.canvas.getBoundingClientRect();
        const x = Math.round((e.clientX - rect.left) * (this.canvas.width / rect.width));
        const y = Math.round((e.clientY - rect.top) * (this.canvas.height / rect.height));
        
        // Validate coordinates are valid numbers
        if (isNaN(x) || isNaN(y) || !isFinite(x) || !isFinite(y)) {
            console.error('Invalid coordinates:', x, y);
            return;
        }
        
        this.currentPolygon.push({ x, y });
        this.redraw();
    }

    handleCanvasDoubleClick(e) {
        if (!this.isDrawing || this.currentPolygon.length < 3) {
            UI.showToast('Cần ít nhất 3 điểm', 'warning');
            return;
        }
        
        e.preventDefault();
        this.isDrawing = false;
        this.showZoneEditor();
    }

    handleCanvasMouseMove(e) {
        if (!this.isDrawing || this.currentPolygon.length === 0) return;
        
        const rect = this.canvas.getBoundingClientRect();
        const x = Math.round((e.clientX - rect.left) * (this.canvas.width / rect.width));
        const y = Math.round((e.clientY - rect.top) * (this.canvas.height / rect.height));
        
        this.redraw();
        
        this.ctx.strokeStyle = '#00ff00';
        this.ctx.setLineDash([5, 5]);
        this.ctx.beginPath();
        const last = this.currentPolygon[this.currentPolygon.length - 1];
        this.ctx.moveTo(last.x, last.y);
        this.ctx.lineTo(x, y);
        this.ctx.stroke();
        this.ctx.setLineDash([]);
    }

    redraw() {
        if (this.backgroundImage) {
            this.ctx.drawImage(this.backgroundImage, 0, 0, this.canvas.width, this.canvas.height);
        } else {
            this.ctx.fillStyle = '#1a1a1a';
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
            this.drawGrid();
        }
        
        this.zones.forEach(zone => this.drawZone(zone, 0.3));
        
        if (this.currentPolygon.length > 0) {
            this.ctx.strokeStyle = '#00ff00';
            this.ctx.fillStyle = 'rgba(0, 255, 0, 0.2)';
            this.ctx.lineWidth = 2;
            
            this.ctx.beginPath();
            this.ctx.moveTo(this.currentPolygon[0].x, this.currentPolygon[0].y);
            
            for (let i = 1; i < this.currentPolygon.length; i++) {
                this.ctx.lineTo(this.currentPolygon[i].x, this.currentPolygon[i].y);
            }
            
            if (!this.isDrawing) {
                this.ctx.closePath();
                this.ctx.fill();
            }
            
            this.ctx.stroke();
            
            this.currentPolygon.forEach(point => {
                this.ctx.fillStyle = '#00ff00';
                this.ctx.beginPath();
                this.ctx.arc(point.x, point.y, 5, 0, Math.PI * 2);
                this.ctx.fill();
            });
        }
    }

    drawZone(zone, alpha = 0.3) {
        const color = zone.color || [0, 255, 0];
        this.ctx.strokeStyle = `rgb(${color[0]}, ${color[1]}, ${color[2]})`;
        this.ctx.fillStyle = `rgba(${color[0]}, ${color[1]}, ${color[2]}, ${alpha})`;
        this.ctx.lineWidth = 2;
        
        this.ctx.beginPath();
        this.ctx.moveTo(zone.polygon[0].x, zone.polygon[0].y);
        for (let i = 1; i < zone.polygon.length; i++) {
            this.ctx.lineTo(zone.polygon[i].x, zone.polygon[i].y);
        }
        this.ctx.closePath();
        this.ctx.fill();
        this.ctx.stroke();
        
        const centroidX = zone.polygon.reduce((sum, p) => sum + p.x, 0) / zone.polygon.length;
        const centroidY = zone.polygon.reduce((sum, p) => sum + p.y, 0) / zone.polygon.length;
        
        this.ctx.fillStyle = '#ffffff';
        this.ctx.font = 'bold 16px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.fillText(zone.name, centroidX, centroidY);
    }

    showZoneEditor() {
        const modal = document.getElementById('zoneEditorModal');
        if (modal) {
            modal.classList.remove('hidden');
            document.getElementById('zoneName').value = '';
            document.querySelectorAll('.vehicle-type-check').forEach(cb => cb.checked = false);
            document.getElementById('zoneColor').value = '#00ff00';
        }
    }

    hideZoneEditor() {
        const modal = document.getElementById('zoneEditorModal');
        if (modal) modal.classList.add('hidden');
    }

    async saveCurrentZone() {
        const name = document.getElementById('zoneName').value.trim();
        const allowedClasses = Array.from(document.querySelectorAll('.vehicle-type-check:checked')).map(cb => cb.value);
        const colorHex = document.getElementById('zoneColor').value;
        
        if (!name) {
            UI.showToast('Vui lòng nhập tên vùng', 'warning');
            return;
        }
        
        if (allowedClasses.length === 0) {
            UI.showToast('Vui lòng chọn ít nhất một loại phương tiện', 'warning');
            return;
        }
        
        // Validate and sanitize polygon data
        const validPolygon = this.currentPolygon.map(point => {
            const x = parseInt(point.x, 10);
            const y = parseInt(point.y, 10);
            
            if (isNaN(x) || isNaN(y) || !isFinite(x) || !isFinite(y)) {
                throw new Error(`Invalid polygon point: x=${point.x}, y=${point.y}`);
            }
            
            return { x, y };
        });
        
        if (validPolygon.length < 3) {
            UI.showToast('Zone must have at least 3 points', 'warning');
            return;
        }
        
        const r = parseInt(colorHex.substr(1, 2), 16);
        const g = parseInt(colorHex.substr(3, 2), 16);
        const b = parseInt(colorHex.substr(5, 2), 16);
        
        const zoneData = {
            zone_id: `zone_${Date.now()}`,
            name: name,
            polygon: validPolygon,
            allowed_classes: allowedClasses,
            color: [r, g, b],
            // Save the canvas base size used when drawing to enable backend rescaling
            base_width: this.canvas.width,
            base_height: this.canvas.height
        };
        
        console.log('Saving zone with data:', JSON.stringify(zoneData, null, 2));
        
        try {
            const endpoint = this.taskId ? `/zones/${this.taskId}` : '/zones';
            console.log(`Saving zone to: ${endpoint}`);
            const response = await api.post(endpoint, zoneData);
            
            UI.showToast('Đã lưu vùng!', 'success');
            this.zones.push(zoneData);
            this.currentPolygon = [];
            this.redraw();
            this.renderZonesList();
            this.hideZoneEditor();
        } catch (error) {
            console.error('Error saving zone:', error);
            UI.showToast('Lỗi: ' + error.message, 'error');
        }
    }

    async loadZones() {
        try {
            const endpoint = this.taskId ? `/zones/${this.taskId}` : '/zones';
            console.log(`Loading zones from: ${endpoint}`);
            const response = await api.get(endpoint);
            
            // Validate loaded zones
            this.zones = (response.zones || []).map(zone => {
                // Ensure polygon points are integers
                if (zone.polygon && Array.isArray(zone.polygon)) {
                    zone.polygon = zone.polygon.map(point => ({
                        x: parseInt(point.x, 10) || 0,
                        y: parseInt(point.y, 10) || 0
                    }));
                }
                return zone;
            });
            
            console.log(`Loaded ${this.zones.length} zones`);
            this.redraw();
            this.renderZonesList();
        } catch (error) {
            console.error('Error loading zones:', error);
        }
    }

    renderZonesList() {
        const container = document.getElementById('zonesList');
        if (!container) return;
        
        if (this.zones.length === 0) {
            container.innerHTML = '<p class="empty-state">Chưa có vùng</p>';
            // Keep main upload process button enabled (so user can still open zone editor),
            // but disable zones-panel process button until zones are created
            UI.setProcessButtons(true, false);
            return;
        }
        
        container.innerHTML = this.zones.map(zone => {
            const zoneId = zone.zone_id || `zone_${Date.now()}_${Math.random()}`;
            return `
                <div class="zone-item">
                    <div class="zone-item-header">
                        <input type="checkbox" checked class="zone-checkbox" data-zone-id="${zoneId}" 
                               style="margin-right: 8px; cursor: pointer; width: 18px; height: 18px;">
                        <span class="zone-item-name">${zone.name}</span>
                        <div class="zone-item-actions">
                            <button class="btn btn-danger small" onclick="window.zoneEditor.deleteZone('${zoneId}')">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                    <div class="zone-item-info">${zone.polygon.length} points</div>
                    <div class="zone-item-classes">
                        ${zone.allowed_classes.map(c => `<span class="zone-class-tag">${c}</span>`).join('')}
                    </div>
                </div>
            `;
        }).join('');

        // Enable both the main and zones-panel process buttons when zones exist
        UI.setProcessButtons(true, true);
    }

    async deleteZone(zoneId) {
        if (!confirm('Xóa vùng này?')) return;
        
        try {
            const endpoint = this.taskId ? `/zones/${this.taskId}/${zoneId}` : `/zones/${zoneId}`;
            await api.delete(endpoint);
            this.zones = this.zones.filter(z => z.zone_id !== zoneId);
            this.redraw();
            this.renderZonesList();
            UI.showToast('Đã xóa vùng', 'success');
        } catch (error) {
            UI.showToast('Error: ' + error.message, 'error');
        }
    }

    async clearAllZones() {
        if (!confirm('Xóa tất cả vùng?')) return;
        
        try {
            for (const zone of this.zones) {
                const endpoint = this.taskId ? `/zones/${this.taskId}/${zone.zone_id}` : `/zones/${zone.zone_id}`;
                await api.delete(endpoint);
            }
            this.zones = [];
            this.currentPolygon = [];
            this.redraw();
            this.renderZonesList();
            UI.showToast('Đã xóa tất cả vùng', 'success');
        } catch (error) {
            UI.showToast('Error: ' + error.message, 'error');
        }
    }
}

// Hook into zone section visibility (UI.showSection is called after menu click)
function initializeZoneEditorOnDisplay() {
    // Called by app.js when zones section is shown
    const taskId = (window.AppState && window.AppState.currentTaskId) ? window.AppState.currentTaskId : null;
    console.log(`Initializing ZoneEditor for taskId: ${taskId}`);
    
    if (!window.zoneEditor || window.zoneEditor.taskId !== taskId) {
        try {
            window.zoneEditor = new ZoneEditor(taskId);
            console.log('ZoneEditor initialized successfully');
        } catch (error) {
            console.error('Error initializing ZoneEditor:', error);
            if (typeof UI !== 'undefined') {
                UI.showToast(`Lỗi khởi tạo quản lý vùng: ${error.message}`, 'error');
            }
        }
    }
}

// Make function available globally
window.initializeZoneEditorOnDisplay = initializeZoneEditorOnDisplay;
