"""Flask Web Server for Lane Violation Detection"""
import os
import json
import threading
import cv2
import io
import csv
import zipfile
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from pathlib import Path
import sys

# Ensure project root is on sys.path so imports like `from src...` work
# Project root is two levels up from this file (workspace root)
try:
    project_root = str(Path(__file__).resolve().parent.parent)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
except Exception:
    pass
from flask import Flask, render_template, request, jsonify, send_file, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestedRangeNotSatisfiable

from src.pipeline import LaneViolationPipeline
from src.utils.logger import Logger
from src.utils.analytics import AnalyticsCollector


class ProcessingTask:
    """Represents a processing task"""
    def __init__(self, task_id, input_path, task_type='video'):
        self.task_id = task_id
        self.input_path = input_path
        self.task_type = task_type
        self.status = 'queued'  # queued, processing, completed, failed
        self.progress = 0
        self.start_time = None
        self.end_time = None
        self.error_message = None
        self.result = None
        self.analytics = None
        self.selected_zone_ids = []  # Zones to focus processing on


class WebServer:
    """Web server for Lane Violation Detection"""
    
    def __init__(self, config_path='configs/config.yaml', port=5000):
        """Initialize web server"""
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Get project root (parent of app directory)
        self.project_root = Path(__file__).parent.parent
        
        self.port = port
        self.config_path = config_path
        self.pipeline = None
        
        # Configuration
        self.app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 500  # 500MB max
        self.app.config['UPLOAD_FOLDER'] = str(self.project_root / 'data' / 'videos')
        self.ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'jpg', 'jpeg', 'png'}
        
        # Task management
        self.tasks = {}
        self.task_counter = 0
        
        Logger.setup('logs')
        Logger.info(f"Web server initialized on port {port}")
        
        # Setup routes
        self._setup_routes()
    
    def _generate_violations_pdf(self):
        """Helper function to generate PDF with violations"""
        try:
            # Get violations by scanning files directly
            import re
            base = Path.cwd() / 'data' / 'outputs' / 'violations'
            if not base.exists():
                return None

            all_violations = []
            seen_violations = set()
            
            for task_dir in base.iterdir():
                if not task_dir.is_dir():
                    continue
                task_id = task_dir.name
                
                for file in sorted(task_dir.iterdir()):
                    if not file.is_file():
                        continue
                    name = file.name
                    # Only process violation_crop to avoid duplicate entries
                    if not name.startswith('violation_crop'):
                        continue
                    
                    # Parse track_id, vehicle_type, and frame number
                    track_id = None
                    vehicle_type = 'Xe khác'
                    frame = None
                    try:
                        track_m = re.search(r'track(\d+)', name)
                        vtype_m = re.search(r'track\d+_(\w+)_frame', name)
                        frame_m = re.search(r'frame(\d+)', name)
                        
                        if track_m:
                            track_id = int(track_m.group(1))
                        if frame_m:
                            frame = int(frame_m.group(1))
                        
                        if vtype_m:
                            vtype_code = vtype_m.group(1).lower()
                            vtype_map = {
                                'otto': 'Ô tô',
                                'xemay': 'Xe máy',
                                'xebuyt': 'Xe buýt',
                                'xetai': 'Xe tải',
                                'khac': 'Xe khác'
                            }
                            vehicle_type = vtype_map.get(vtype_code, 'Xe khác')
                    except Exception:
                        pass
                    
                    # Avoid duplicates
                    violation_key = f"{task_id}_{track_id}_{frame}"
                    if violation_key in seen_violations:
                        continue
                    seen_violations.add(violation_key)
                    
                    mtime = datetime.fromtimestamp(file.stat().st_mtime).isoformat()
                    all_violations.append({
                        'id': name,
                        'task_id': task_id,
                        'filename': name,
                        'track_id': track_id,
                        'frame': frame,
                        'timestamp': mtime,
                        'vehicle_type': vehicle_type,
                        'zone_name': 'Unknown',
                        'violation_type': 'Lane',
                        'confidence': 0.95
                    })
            
            if not all_violations:
                return None

            # Resolve both crop and full paths
            def resolve_image_paths(v):
                task_id = v.get('task_id')
                fname = str(v.get('filename'))
                base_dir = Path.cwd() / 'data' / 'outputs' / 'violations' / str(task_id)
                crop_path = base_dir / fname
                
                import re
                track_match = re.search(r'track(\d+)', fname)
                full_path = None
                if track_match and base_dir.exists():
                    track_id = track_match.group(1)
                    for file in base_dir.iterdir():
                        if file.name.startswith('violation_full_') and f'track{track_id}_' in file.name:
                            full_path = file
                            break
                
                return (
                    crop_path if crop_path.exists() else None,
                    full_path,
                )

            # Group by vehicle type
            grouped_by_type = {}
            for v in all_violations:
                vt = v.get('vehicle_type') or 'Xe khác'
                grouped_by_type.setdefault(vt, []).append(v)

            # Load fonts
            def load_font(size):
                try:
                    return ImageFont.truetype("C:/Windows/Fonts/arial.ttf", size)
                except Exception:
                    try:
                        return ImageFont.truetype("Arial.ttf", size)
                    except Exception:
                        return ImageFont.load_default()

            title_font = load_font(48)
            header_font = load_font(32)
            body_font = load_font(24)

            # Summary metrics
            unique_tracks = len({v.get('track_id') for v in all_violations if v.get('track_id') is not None})
            type_counts = {vt: len(items) for vt, items in grouped_by_type.items()}
            total_detected = 0
            try:
                for t in self.tasks.values():
                    stats = getattr(t, 'analytics', None)
                    if isinstance(stats, dict):
                        total_detected += int(stats.get('total_detected_vehicles', 0))
            except Exception:
                pass

            # Build pages
            pages = []
            page_size = (1240, 1754)
            summary = Image.new('RGB', page_size, 'white')
            draw = ImageDraw.Draw(summary)
            y = 120
            draw.text((100, y), "BÁO CÁO VI PHẠM LÀN", fill='black', font=title_font); y += 90
            draw.text((100, y), f"Tổng số vi phạm: {len(all_violations)}", fill='black', font=header_font); y += 60
            draw.text((100, y), f"Số lượng xe vi phạm: {unique_tracks}", fill='black', font=header_font); y += 60
            draw.text((100, y), f"Số lượng xe đếm được: {total_detected}", fill='black', font=header_font); y += 80
            draw.text((100, y), "Phân loại theo loại xe:", fill='black', font=header_font); y += 50
            for vt, cnt in sorted(type_counts.items(), key=lambda x: -x[1]):
                draw.text((140, y), f"- {vt}: {cnt}", fill='black', font=body_font); y += 35
            pages.append(summary)

            # Per vehicle type groups
            for vt, items in grouped_by_type.items():
                sorted_items = sorted(items, key=lambda v: v.get('timestamp',''))
                for v in sorted_items[:50]:
                    crop_path, full_path = resolve_image_paths(v)
                    if not crop_path and not full_path:
                        continue

                    crop_img = None
                    full_img = None
                    try:
                        if crop_path:
                            crop_img = Image.open(str(crop_path)).convert('RGB')
                    except Exception:
                        crop_img = None
                    try:
                        if full_path:
                            full_img = Image.open(str(full_path)).convert('RGB')
                    except Exception:
                        full_img = None

                    margin = 80
                    header_h = 240
                    max_w = page_size[0] - 2*margin
                    available_h = page_size[1] - header_h - margin
                    gap = 30

                    if crop_img and full_img:
                        slot_h = (available_h - gap) // 2
                        crop_img.thumbnail((max_w, slot_h), Image.Resampling.LANCZOS)
                        full_img.thumbnail((max_w, slot_h), Image.Resampling.LANCZOS)
                    else:
                        one_img = crop_img or full_img
                        one_img.thumbnail((max_w, available_h), Image.Resampling.LANCZOS)

                    page = Image.new('RGB', page_size, 'white')
                    pd = ImageDraw.Draw(page)
                    pd.text((margin, 40), f"{vt}", fill='black', font=header_font)
                    pd.text((margin, 100), f"Thời gian: {v.get('timestamp','')}", fill='black', font=body_font)
                    pd.text((margin, 140), f"Zone: {v.get('zone_name','')}", fill='black', font=body_font)
                    conf = v.get('confidence')
                    if conf is not None:
                        pd.text((margin, 180), f"Độ tin cậy: {float(conf)*100:.1f}%", fill='black', font=body_font)

                    current_y = header_h
                    if crop_img:
                        paste_x = margin + int((max_w - crop_img.width) / 2)
                        page.paste(crop_img, (paste_x, current_y))
                        current_y += crop_img.height + gap

                    if full_img:
                        paste_x = margin + int((max_w - full_img.width) / 2)
                        page.paste(full_img, (paste_x, current_y))

                    pages.append(page)

            mem = io.BytesIO()
            first, rest = pages[0], pages[1:]
            first.save(mem, format='PDF', save_all=True, append_images=rest, quality=95, dpi=(150, 150))
            mem.seek(0)
            return mem.getvalue()
        except Exception as e:
            Logger.error(f"Generate PDF error: {e}")
            return None
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main page"""
            return render_template('index.html')
        
        @self.app.route('/api/status', methods=['GET'])
        def get_status():
            """Get system status with aggregated analytics"""
            try:
                tasks_count = len(self.tasks)
                active_tasks = len([t for t in self.tasks.values() if getattr(t, 'status', None) == 'processing'])

                # Aggregate analytics across tasks
                total_detected = 0
                total_violations = 0
                processed_videos = 0
                durations = []
                try:
                    for t in self.tasks.values():
                        if getattr(t, 'status', None) == 'completed':
                            processed_videos += 1
                        stats = getattr(t, 'analytics', None)
                        if isinstance(stats, dict):
                            total_detected += int(stats.get('total_detected_vehicles', 0))
                            total_violations += int(stats.get('total_violations', 0))
                            dur = float(stats.get('duration_seconds', 0))
                            if dur > 0:
                                durations.append(dur)
                except Exception:
                    pass

                # Fallback: count violations by scanning output folder
                try:
                    violations_dir = Path.cwd() / 'data' / 'outputs' / 'violations'
                    if violations_dir.exists():
                        unique_keys = set()
                        for task_dir in violations_dir.iterdir():
                            if not task_dir.is_dir():
                                continue
                            for f in task_dir.iterdir():
                                name = f.name
                                if not name.startswith('violation_crop'):
                                    continue
                                import re
                                track_m = re.search(r'track(\d+)', name)
                                frame_m = re.search(r'frame(\d+)', name)
                                key = (task_dir.name, track_m.group(1) if track_m else None, frame_m.group(1) if frame_m else None)
                                unique_keys.add(key)
                        total_violations = len(unique_keys)
                except Exception:
                    pass

                avg_process_time = (sum(durations) / len(durations)) if durations else 0.0

                return jsonify({
                    'status': 'online',
                    'timestamp': datetime.now().isoformat(),
                    'tasks_count': tasks_count,
                    'active_tasks': active_tasks,
                    'total_detected_vehicles': total_detected,
                    'total_violations': total_violations,
                    'processed_videos': processed_videos,
                    'avg_process_time_seconds': avg_process_time
                })
            except Exception as e:
                Logger.error(f"Status error: {str(e)}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/api/upload', methods=['POST'])
        def upload_file():
            """Upload video file and extract first frame for zone drawing"""
            try:
                if 'file' not in request.files:
                    return jsonify({'error': 'No file provided'}), 400
                
                file = request.files['file']
                if file.filename == '':
                    return jsonify({'error': 'No file selected'}), 400
                
                if not self._allowed_file(file.filename):
                    return jsonify({'error': 'File type not allowed'}), 400
                
                # Create upload directory if not exists
                upload_dir = Path(self.app.config['UPLOAD_FOLDER'])
                upload_dir.mkdir(parents=True, exist_ok=True)
                
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
                filename = timestamp + filename
                
                filepath = upload_dir / filename
                file.save(str(filepath))
                
                Logger.info(f"File uploaded: {filename}")
                
                # Extract first frame for zone drawing
                frame_preview_path = None
                try:
                    video = cv2.VideoCapture(str(filepath))
                    if video.isOpened():
                        ret, frame = video.read()
                        if ret:
                            # Resize to fit browser
                            frame_resized = cv2.resize(frame, (1280, 720))
                            frame_preview_path = str(upload_dir / f"{filename}_preview.jpg")
                            cv2.imwrite(frame_preview_path, frame_resized)
                            Logger.info(f"Frame preview saved: {frame_preview_path}")
                        video.release()
                except Exception as e:
                    Logger.warning(f"Error extracting frame preview: {str(e)}")
                
                # Create task immediately
                task_id = f"task_{self.task_counter}"
                self.task_counter += 1
                
                # Create task-specific directory for zones
                task_dir = Path(self.app.config['UPLOAD_FOLDER']).parent / 'tasks' / task_id
                task_dir.mkdir(parents=True, exist_ok=True)
                
                task = ProcessingTask(task_id, str(filepath), task_type='video')
                self.tasks[task_id] = task
                
                Logger.info(f"Task created during upload: {task_id}")
                
                return jsonify({
                    'success': True,
                    'filename': filename,
                    'filepath': str(filepath),
                    'preview_url': f'/api/preview/{filename}_preview.jpg' if frame_preview_path else None,
                    'task_id': task_id
                })
            
            except Exception as e:
                Logger.error(f"Upload error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/create-task', methods=['POST'])
        def create_task():
            """Create a new task (called after upload)"""
            try:
                data = request.get_json()
                filename = data.get('filename')
                
                if not filename:
                    return jsonify({'error': 'No filename provided'}), 400
                
                # Create task
                task_id = f"task_{self.task_counter}"
                self.task_counter += 1
                
                # Create task-specific directory for zones
                task_dir = Path(self.app.config['UPLOAD_FOLDER']).parent / 'tasks' / task_id
                task_dir.mkdir(parents=True, exist_ok=True)
                
                task = ProcessingTask(task_id, f"{self.app.config['UPLOAD_FOLDER']}/{filename}")
                self.tasks[task_id] = task
                
                Logger.info(f"Task created: {task_id} for {filename}")
                
                return jsonify({
                    'success': True,
                    'task_id': task_id
                })
            
            except Exception as e:
                Logger.error(f"Create task error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/preview/<filename>', methods=['GET'])
        def get_preview(filename):
            """Get video frame preview for zone drawing"""
            try:
                # Use the absolute path from config
                preview_path = Path(self.app.config['UPLOAD_FOLDER']) / filename
                Logger.info(f"Looking for preview at: {preview_path}")
                
                if not preview_path.exists():
                    Logger.error(f"Preview not found: {preview_path}")
                    return jsonify({'error': 'Preview not found'}), 404
                
                return send_file(
                    str(preview_path),
                    mimetype='image/jpeg',
                    as_attachment=False
                )
            except Exception as e:
                Logger.error(f"Preview error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/process', methods=['POST'])
        def process():
            """Start processing task - called AFTER zones are defined"""
            try:
                data = request.get_json()
                task_id = data.get('task_id')
                selected_zone_ids = data.get('selected_zone_ids', [])
                
                if not task_id:
                    return jsonify({'error': 'Missing task_id'}), 400
                
                # Task must already exist from upload
                if task_id not in self.tasks:
                    return jsonify({'error': f'Task {task_id} not found'}), 404

                task = self.tasks[task_id]

                # Validate that task-specific zones exist and are non-empty
                task_zones_path = Path('data/tasks') / task_id / 'zones.json'
                if not task_zones_path.exists():
                    return jsonify({'error': 'No zones defined for this task. Create at least one zone before processing.'}), 400

                try:
                    with open(task_zones_path, 'r', encoding='utf-8') as f:
                        zones_payload = json.load(f)
                    zones_list = zones_payload.get('zones', []) if isinstance(zones_payload, dict) else []
                except Exception as e:
                    Logger.error(f"Error reading zones for {task_id}: {e}")
                    return jsonify({'error': 'Failed to read zones for task; cannot start processing.'}), 500

                if not zones_list:
                    return jsonify({'error': 'Zone list is empty. Create at least one zone before processing.'}), 400

                # Store selected zone IDs in task for zone-filtered processing
                if selected_zone_ids and isinstance(selected_zone_ids, list):
                    # Validate selected ids exist in zone list
                    available_ids = {z.get('zone_id') for z in zones_list}
                    invalid = [z for z in selected_zone_ids if z not in available_ids]
                    if invalid:
                        return jsonify({'error': f'Selected zone ids not found: {invalid}'}), 400
                    task.selected_zone_ids = selected_zone_ids
                    Logger.info(f"[{task_id}] Selected zones for processing: {selected_zone_ids}")
                else:
                    # Default to all zones if not explicitly provided
                    task.selected_zone_ids = [z.get('zone_id') for z in zones_list]
                    Logger.info(f"[{task_id}] No zones explicitly selected; defaulting to all zones: {task.selected_zone_ids}")
                
                # Store processing options (model, confidence, frame_skip, etc.) if provided
                options = data.get('options', {}) if isinstance(data, dict) else {}
                task.options = options

                # Start processing in background
                thread = threading.Thread(
                    target=self._process_task,
                    args=(task_id,)
                )
                thread.daemon = True
                thread.start()
                
                Logger.info(f"Processing started: {task_id}")
                
                return jsonify({
                    'success': True,
                    'task_id': task_id,
                    'selected_zone_ids': selected_zone_ids
                })
            
            except Exception as e:
                Logger.error(f"Process error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/stream', methods=['GET'])
        def stream():
            """Real-time video stream from webcam/RTSP"""
            try:
                source = request.args.get('source', '0')
                model = request.args.get('model', 'yolov8m')
                use_global_zones = request.args.get('use_global_zones', '0') == '1'
                zones_param = request.args.get('zones')  # comma-separated zone ids when streaming
                
                # Convert source (0 for webcam, or RTSP URL)
                if source == '0':
                    source = 0
                else:
                    # Handle file path - convert to absolute path
                    source_path = Path(source)
                    if not source_path.is_absolute():
                        # If relative path, resolve from project root
                        source_path = Path.cwd() / source
                    
                    # Validate file exists
                    if not source_path.exists():
                        Logger.error(f"Video file not found: {source_path}")
                        return jsonify({'error': f'Video file not found: {source_path}'}), 404
                    
                    source = str(source_path)
                    Logger.info(f"Opening video file: {source}")
                
                def generate():
                    """Generate video frames"""
                    # Initialize pipeline; when streaming we may optionally use global zones
                    pipeline = LaneViolationPipeline(self.config_path)
                    pipeline.vehicle_detector.model_name = model
                    pipeline.vehicle_detector.load_model()

                    # Enforce zones when required: either use global zones or provided zone ids
                    if pipeline.require_zones:
                        if use_global_zones:
                            if not pipeline.zone_manager or len(pipeline.zone_manager.zones) == 0:
                                Logger.error("Streaming rejected: global zones not configured")
                                return
                            # Use all global zones by default
                            pipeline.selected_zone_ids = [z.zone_id for z in pipeline.zone_manager.zones]
                        else:
                            # zones_param must be provided
                            if not zones_param:
                                Logger.error("Streaming rejected: must provide 'zones' param or set use_global_zones=1")
                                return
                            requested = [z.strip() for z in zones_param.split(',') if z.strip()]
                            if not pipeline.zone_manager or len(pipeline.zone_manager.zones) == 0:
                                Logger.error("Streaming rejected: no global zones available to validate requested zones")
                                return
                            available = {z.zone_id for z in pipeline.zone_manager.zones}
                            invalid = [z for z in requested if z not in available]
                            if invalid:
                                Logger.error(f"Streaming rejected: requested zones not found: {invalid}")
                                return
                            pipeline.selected_zone_ids = requested
                    
                    video = cv2.VideoCapture(source)
                    if not video.isOpened():
                        Logger.error(f"Cannot open video source: {source}")
                        return
                    
                    frame_count = 0
                    while True:
                        ret, frame = video.read()
                        if not ret:
                            break
                        
                        # Process frame
                        results = pipeline.process_frame(frame, frame_count)
                        annotated = pipeline.draw_results(frame, results)
                        
                        # Encode frame
                        ret, buffer = cv2.imencode('.jpg', annotated)
                        frame_bytes = buffer.tobytes()
                        
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n'
                               b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n\r\n'
                               + frame_bytes + b'\r\n')
                        
                        frame_count += 1
                    
                    video.release()
                
                return Response(generate(),
                               mimetype='multipart/x-mixed-replace; boundary=frame')
            
            except Exception as e:
                Logger.error(f"Stream error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/task/<task_id>', methods=['GET'])
        def get_task(task_id):
            """Get task status"""
            try:
                if task_id not in self.tasks:
                    return jsonify({'error': 'Task not found'}), 404
                
                task = self.tasks[task_id]
                
                return jsonify({
                    'task_id': task.task_id,
                    'status': task.status,
                    'progress': task.progress,
                    'start_time': task.start_time.isoformat() if task.start_time else None,
                    'end_time': task.end_time.isoformat() if task.end_time else None,
                    'error_message': task.error_message,
                    'result': task.result,
                    'analytics': task.analytics
                })
            
            except Exception as e:
                Logger.error(f"Get task error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/tasks', methods=['GET'])
        def get_tasks():
            """Get all tasks"""
            try:
                tasks_list = []
                for task in self.tasks.values():
                    tasks_list.append({
                        'task_id': task.task_id,
                        'status': task.status,
                        'progress': task.progress,
                        'type': task.task_type
                    })
                
                return jsonify({'tasks': tasks_list})
            
            except Exception as e:
                Logger.error(f"Get tasks error: {str(e)}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/violation-snapshot/<task_subdir>/<filename>', methods=['GET'])
        def get_violation_snapshot(task_subdir, filename):
            """Serve saved violation snapshot images"""
            try:
                snapshot_path = Path.cwd() / 'data' / 'outputs' / 'violations' / task_subdir / filename
                Logger.info(f"Serving violation snapshot: {snapshot_path}")
                if not snapshot_path.exists():
                    return jsonify({'error': 'Snapshot not found'}), 404

                return send_file(str(snapshot_path), mimetype='image/jpeg', as_attachment=False)
            except Exception as e:
                Logger.error(f"Snapshot serve error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/download/<task_id>', methods=['GET'])
        def download_result(task_id):
            """Download processed video"""
            try:
                if task_id not in self.tasks:
                    return jsonify({'error': 'Task not found'}), 404
                
                task = self.tasks[task_id]
                if task.status != 'completed' or not task.result:
                    return jsonify({'error': 'Task not completed'}), 400
                
                result_path = Path(task.result['output_path'])
                if not result_path.exists():
                    return jsonify({'error': 'Result file not found'}), 404
                
                return send_file(
                    str(result_path),
                    as_attachment=True,
                    download_name=result_path.name
                )
            
            except Exception as e:
                Logger.error(f"Download error: {str(e)}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/result/<task_id>/stream', methods=['GET'])
        def stream_result(task_id):
            """Stream processed video for inline playback"""
            try:
                if task_id not in self.tasks:
                    return jsonify({'error': 'Task not found'}), 404
                task = self.tasks[task_id]
                if task.status != 'completed' or not task.result:
                    return jsonify({'error': 'Task not completed'}), 400

                result_path = Path(task.result['output_path'])
                if not result_path.exists():
                    return jsonify({'error': 'Result file not found'}), 404

                # Use send_file with conditional support for range requests (Flask>=2.0)
                # Pick mimetype based on extension
                ext = result_path.suffix.lower()
                mime = 'video/mp4' if ext == '.mp4' else 'video/x-msvideo'
                try:
                    return send_file(
                        str(result_path),
                        mimetype=mime,
                        as_attachment=False,
                        conditional=True
                    )
                except RequestedRangeNotSatisfiable as rr:
                    # Client requested an invalid range (416) - return proper status
                    Logger.warning(f"Stream result range not satisfiable for {task_id}: {rr}")
                    return Response(status=416)
            except Exception as e:
                Logger.error(f"Stream result error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/config', methods=['GET'])
        def get_config():
            """Get current configuration"""
            try:
                from src.utils.config_loader import ConfigLoader
                config = ConfigLoader(self.config_path)
                return jsonify(config.get_all())
            except Exception as e:
                Logger.error(f"Config error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/config', methods=['POST'])
        def update_config():
            """Update configuration"""
            try:
                from src.utils.config_loader import ConfigLoader
                data = request.get_json()
                config = ConfigLoader(self.config_path)
                
                # Update config values
                for key, value in data.items():
                    config.set(key, value)
                
                config.save(self.config_path)
                Logger.info("Configuration updated")
                
                return jsonify({'success': True})
            except Exception as e:
                Logger.error(f"Config update error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/zones/<task_id>', methods=['GET'])
        def get_zones_for_task(task_id):
            """Get zones for specific task/video"""
            try:
                task_zones_path = Path('data/tasks') / task_id / 'zones.json'
                
                if not task_zones_path.exists():
                    return jsonify({
                        'success': True,
                        'zones': []
                    })
                
                with open(task_zones_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                return jsonify({
                    'success': True,
                    'zones': data.get('zones', [])
                })
            except Exception as e:
                Logger.error(f"Get zones error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/zones/<task_id>', methods=['POST'])
        def add_zone_for_task(task_id):
            """Add zone to specific task/video"""
            try:
                data = request.get_json()
                
                # Create task zones directory
                task_zones_dir = Path('data/tasks') / task_id
                task_zones_dir.mkdir(parents=True, exist_ok=True)
                task_zones_path = task_zones_dir / 'zones.json'
                
                # Load existing zones
                zones_data = {'zones': []}
                if task_zones_path.exists():
                    with open(task_zones_path, 'r', encoding='utf-8') as f:
                        zones_data = json.load(f)
                
                # Add new zone
                zone = {
                    'zone_id': data['zone_id'],
                    'name': data['name'],
                    'polygon': data['polygon'],
                    'allowed_classes': data['allowed_classes'],
                    'color': data.get('color', [0, 255, 0]),
                    'base_width': data.get('base_width'),
                    'base_height': data.get('base_height')
                }
                
                # Check if zone exists, replace if so
                zones_data['zones'] = [z for z in zones_data.get('zones', []) if z['zone_id'] != zone['zone_id']]
                zones_data['zones'].append(zone)
                
                # Save zones
                with open(task_zones_path, 'w', encoding='utf-8') as f:
                    json.dump(zones_data, f, indent=2, ensure_ascii=False)
                
                Logger.info(f"Zone added to {task_id}: {zone['name']}")
                
                return jsonify({
                    'success': True,
                    'zone': zone
                })
            except Exception as e:
                Logger.error(f"Add zone error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/zones/<task_id>/<zone_id>', methods=['DELETE'])
        def delete_zone_for_task(task_id, zone_id):
            """Delete zone from specific task"""
            try:
                task_zones_path = Path('data/tasks') / task_id / 'zones.json'
                
                if not task_zones_path.exists():
                    return jsonify({'error': 'No zones found'}), 404
                
                with open(task_zones_path, 'r', encoding='utf-8') as f:
                    zones_data = json.load(f)
                
                # Remove zone
                zones_data['zones'] = [z for z in zones_data.get('zones', []) if z['zone_id'] != zone_id]
                
                # Save updated zones
                with open(task_zones_path, 'w', encoding='utf-8') as f:
                    json.dump(zones_data, f, indent=2, ensure_ascii=False)
                
                Logger.info(f"Zone deleted from {task_id}: {zone_id}")
                
                return jsonify({'success': True})
            except Exception as e:
                Logger.error(f"Delete zone error: {str(e)}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/violations', methods=['GET'])
        def list_violations():
            """List available violations with vehicle classification"""
            try:
                task_filter = request.args.get('task')
                start_date = request.args.get('start_date')
                end_date = request.args.get('end_date')

                base = Path.cwd() / 'data' / 'outputs' / 'violations'
                if not base.exists():
                    return jsonify({'violations': []})

                violations = []
                seen_violations = set()  # Track to avoid duplicates (crop + full)
                
                for task_dir in base.iterdir():
                    if not task_dir.is_dir():
                        continue
                    task_id = task_dir.name
                    if task_filter and task_filter != task_id:
                        continue

                    for file in task_dir.iterdir():
                        if not file.is_file():
                            continue
                        name = file.name
                        # Only process violation_crop to avoid duplicate entries (full images are for PDF)
                        if not name.startswith('violation_crop'):
                            continue

                        # Parse track_id, vehicle_type, and frame number from filename
                        # Format: violation_crop_track{track_id}_{vehicle_type}_frame{frame_num}.jpg
                        track_id = None
                        vehicle_type = 'Xe khác'
                        frame = None
                        try:
                            import re
                            track_m = re.search(r'track(\d+)', name)
                            vtype_m = re.search(r'track\d+_(\w+)_frame', name)
                            frame_m = re.search(r'frame(\d+)', name)
                            
                            if track_m:
                                track_id = int(track_m.group(1))
                            if frame_m:
                                frame = int(frame_m.group(1))
                            
                            # Map vehicle type code to Vietnamese
                            if vtype_m:
                                vtype_code = vtype_m.group(1).lower()
                                vtype_map = {
                                    'otto': 'Ô tô',
                                    'xemay': 'Xe máy',
                                    'xebuyt': 'Xe buýt',
                                    'xetai': 'Xe tải',
                                    'khac': 'Xe khác'
                                }
                                vehicle_type = vtype_map.get(vtype_code, 'Xe khác')
                        except Exception:
                            pass

                        # Create unique key to avoid duplicate entries
                        violation_key = f"{task_id}_{track_id}_{frame}"
                        if violation_key in seen_violations:
                            continue
                        seen_violations.add(violation_key)

                        mtime = datetime.fromtimestamp(file.stat().st_mtime).isoformat()

                        violations.append({
                            'id': name,
                            'task_id': task_id,
                            'filename': name,
                            'track_id': track_id,
                            'frame': frame,
                            'timestamp': mtime,
                            'vehicle_type': vehicle_type,
                            'zone_name': 'Zone 1',
                            'violation_type': 'Vi phạm làn đường',
                            'confidence': 0.92,
                            'snapshot_url': f'/api/violation-snapshot/{task_id}/{name}'
                        })

                # Optional date filtering
                if start_date or end_date:
                    def in_range(v):
                        ts = v.get('timestamp')
                        if not ts:
                            return False
                        try:
                            t = datetime.fromisoformat(ts)
                        except Exception:
                            return False
                        if start_date:
                            try:
                                if t < datetime.fromisoformat(start_date):
                                    return False
                            except Exception:
                                pass
                        if end_date:
                            try:
                                if t > datetime.fromisoformat(end_date):
                                    return False
                            except Exception:
                                pass
                        return True

                    violations = [v for v in violations if in_range(v)]

                return jsonify({'violations': violations})
            except Exception as e:
                Logger.error(f"List violations error: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/export/csv', methods=['GET'])
        def export_csv():
            """Export violations metadata as CSV"""
            try:
                # Reuse list_violations logic by calling functionally
                resp = list_violations()
                if resp.status_code != 200:
                    return resp
                data = resp.get_json()
                rows = data.get('violations', [])

                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(['id', 'task_id', 'filename', 'frame', 'timestamp', 'vehicle_type', 'zone_name', 'violation_type', 'confidence', 'snapshot_url'])
                for r in rows:
                    writer.writerow([
                        r.get('id'), r.get('task_id'), r.get('filename'), r.get('frame'), r.get('timestamp'),
                        r.get('vehicle_type'), r.get('zone_name'), r.get('violation_type'), r.get('confidence'), r.get('snapshot_url')
                    ])

                mem = io.BytesIO()
                mem.write(output.getvalue().encode('utf-8'))
                mem.seek(0)
                return send_file(mem, as_attachment=True, download_name='violations.csv', mimetype='text/csv')
            except Exception as e:
                Logger.error(f"Export CSV error: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/export/pdf', methods=['GET'])
        def export_pdf():
            """Export violation full-size images into a single PDF"""
            try:
                pdf_data = self._generate_violations_pdf()
                if not pdf_data:
                    return jsonify({'error': 'No violations found'}), 404
                
                mem = io.BytesIO(pdf_data)
                mem.seek(0)
                return send_file(mem, as_attachment=True, download_name='violations.pdf', mimetype='application/pdf')
            except Exception as e:
                Logger.error(f"Export PDF error: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/export/clips', methods=['GET'])
        def export_clips():
            """Export all violation crop images as a ZIP"""
            try:
                export_format = request.args.get('format', 'crop').lower().strip()
                base = Path.cwd() / 'data' / 'outputs' / 'violations'
                if not base.exists():
                    return jsonify({'error': 'No violations found'}), 404

                prefix_map = {
                    'crop': 'violation_crop',
                    'full': 'violation_full'
                }
                prefix = prefix_map.get(export_format, 'violation_crop')
                download_name = 'violation_clips_crop.zip' if prefix == 'violation_crop' else 'violation_clips_full.zip'

                mem = io.BytesIO()
                with zipfile.ZipFile(mem, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for task_dir in base.iterdir():
                        if not task_dir.is_dir():
                            continue
                        for file in task_dir.iterdir():
                            if file.is_file() and file.name.startswith(prefix):
                                arcname = f"{task_dir.name}/{file.name}"
                                zf.write(str(file), arcname)

                mem.seek(0)
                return send_file(mem, as_attachment=True, download_name=download_name, mimetype='application/zip')
            except Exception as e:
                Logger.error(f"Export clips error: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/export/video-clips', methods=['GET'])
        def export_video_clips():
            """Export violation video clips (5s each) from source videos"""
            try:
                clip_duration = 5  # 5 seconds per clip
                base = Path.cwd() / 'data' / 'outputs' / 'violations'
                videos_dir = Path.cwd() / 'data' / 'videos'
                
                if not base.exists():
                    return jsonify({'error': 'No violations found'}), 404

                mem = io.BytesIO()
                with zipfile.ZipFile(mem, 'w', zipfile.ZIP_DEFLATED) as zf:
                    clip_count = 0
                    
                    # Scan all violations and extract their metadata
                    for task_dir in base.iterdir():
                        if not task_dir.is_dir():
                            continue
                        
                        task_id = task_dir.name
                        
                        # Find the source video for this task
                        source_video = None
                        for task_obj_id, task_obj in self.tasks.items():
                            if task_obj_id == task_id:
                                source_video = task_obj.input_path
                                break
                        
                        if not source_video or not Path(source_video).exists():
                            # Try to find video by pattern
                            for vid_file in videos_dir.glob('*.mp4'):
                                if task_id in vid_file.name:
                                    source_video = str(vid_file)
                                    break
                        
                        if not source_video or not Path(source_video).exists():
                            # Try to use any available video
                            available_videos = list(videos_dir.glob('*.mp4'))
                            if available_videos:
                                source_video = str(available_videos[0])
                                Logger.info(f"Source video not in task object, using available: {source_video}")
                            else:
                                Logger.warning(f"Source video not found for task {task_id}")
                                continue
                        
                        # Process each violation image to extract frame info
                        # Use violation_full for better quality
                        for file in sorted(task_dir.iterdir()):
                            if not file.is_file() or not file.name.startswith('violation_full'):
                                continue
                            
                            # Parse frame number from filename (e.g., violation_crop_frame245_...)
                            frame_num = None
                            import re
                            m = re.search(r'frame(\d+)', file.name)
                            if m:
                                frame_num = int(m.group(1))
                            
                            if frame_num is None:
                                Logger.warning(f"Could not extract frame number from {file.name}")
                                continue
                            
                            try:
                                # Open source video and extract clip around this frame
                                cap = cv2.VideoCapture(str(source_video))
                                if not cap.isOpened():
                                    Logger.warning(f"Cannot open video: {source_video}")
                                    continue
                                
                                fps = cap.get(cv2.CAP_PROP_FPS) or 30
                                frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                                frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                                
                                # Calculate start/end frames (2.5s before and after violation)
                                frames_before = int(2.5 * fps)
                                frames_after = int(2.5 * fps)
                                start_frame = max(0, frame_num - frames_before)
                                end_frame = frame_num + frames_after
                                
                                # Temp output file for this clip
                                clip_name = f"clip_{task_id}_{file.name.replace('.jpg', '.mp4')}"
                                temp_clip_path = Path.cwd() / 'data' / 'outputs' / clip_name
                                
                                writer = cv2.VideoWriter(str(temp_clip_path), fourcc, fps, (frame_width, frame_height))
                                
                                # Extract frames
                                cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
                                current_frame = start_frame
                                frames_written = 0
                                
                                while current_frame <= end_frame:
                                    ret, frame = cap.read()
                                    if not ret:
                                        break
                                    writer.write(frame)
                                    current_frame += 1
                                    frames_written += 1
                                
                                cap.release()
                                writer.release()
                                
                                # Add to ZIP
                                if temp_clip_path.exists() and frames_written > 0:
                                    arcname = f"violations/{task_id}/{clip_name}"
                                    zf.write(str(temp_clip_path), arcname)
                                    temp_clip_path.unlink()  # Delete temp file
                                    clip_count += 1
                                    Logger.info(f"Added video clip: {arcname} ({frames_written} frames)")
                                else:
                                    if temp_clip_path.exists():
                                        temp_clip_path.unlink()
                                    Logger.warning(f"Failed to create clip for frame {frame_num}")
                            
                            except Exception as e:
                                Logger.warning(f"Error creating clip for {file.name}: {e}")
                                continue
                
                if clip_count == 0:
                    return jsonify({'error': 'No video clips could be generated'}), 404
                
                mem.seek(0)
                return send_file(mem, as_attachment=True, download_name='violation_video_clips.zip', mimetype='application/zip')
            except Exception as e:
                Logger.error(f"Export video clips error: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/export/full', methods=['GET'])
        def export_full():
            """Export full-size violation images and result videos as ZIP"""
            try:
                base = Path.cwd() / 'data' / 'outputs'
                if not base.exists():
                    return jsonify({'error': 'No outputs found'}), 404

                mem = io.BytesIO()
                with zipfile.ZipFile(mem, 'w', zipfile.ZIP_DEFLATED) as zf:
                    # --- CSV report ---
                    try:
                        # Reuse list_violations logic to get rows
                        resp = list_violations()
                        if hasattr(resp, 'status_code') and resp.status_code != 200:
                            return resp
                        data = resp.get_json()
                        rows = data.get('violations', []) if isinstance(data, dict) else []

                        output = io.StringIO()
                        writer = csv.writer(output)
                        writer.writerow(['id', 'task_id', 'filename', 'track_id', 'frame', 'timestamp', 'vehicle_type', 'zone_name', 'violation_type', 'confidence', 'snapshot_url'])
                        for r in rows:
                            writer.writerow([
                                r.get('id'), r.get('task_id'), r.get('filename'), r.get('track_id'), r.get('frame'), r.get('timestamp'),
                                r.get('vehicle_type'), r.get('zone_name'), r.get('violation_type'), r.get('confidence'), r.get('snapshot_url')
                            ])
                        zf.writestr('reports/violations.csv', output.getvalue())
                    except Exception as csv_err:
                        Logger.warning(f"Full export: failed to generate CSV: {csv_err}")

                    # --- PDF report (reuse export_pdf logic) ---
                    try:
                        pdf_data = self._generate_violations_pdf()
                        if pdf_data:
                            zf.writestr('reports/violations.pdf', pdf_data)
                    except Exception as pdf_err:
                        Logger.warning(f"Full export: failed to generate PDF: {pdf_err}")

                    # Add full violation images
                    vdir = base / 'violations'
                    if vdir.exists():
                        for task_dir in vdir.iterdir():
                            if not task_dir.is_dir():
                                continue
                            for file in task_dir.iterdir():
                                if file.is_file() and file.name.startswith('violation_full'):
                                    arcname = f"violations/{task_dir.name}/{file.name}"
                                    zf.write(str(file), arcname)

                    # Add result videos
                    for file in base.iterdir():
                        if file.is_file() and (file.name.endswith('_result.mp4') or file.name.endswith('_result.avi')):
                            zf.write(str(file), f"videos/{file.name}")

                mem.seek(0)
                return send_file(mem, as_attachment=True, download_name='full_report.zip', mimetype='application/zip')
            except Exception as e:
                Logger.error(f"Export full error: {e}")
                return jsonify({'error': str(e)}), 500
    
    def _allowed_file(self, filename):
        """Check if file type is allowed"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS
    
    def _process_task(self, task_id):
        """Process a task in background"""
        task = self.tasks[task_id]
        
        try:
            task.status = 'processing'
            task.start_time = datetime.now()
            task.progress = 0
            
            # Initialize pipeline with task_id for task-specific zone loading
            Logger.info(f"[Task {task_id}] Initializing pipeline with config: {self.config_path}")
            # Do not open video during pipeline init; set later after validating path
            pipeline = LaneViolationPipeline(self.config_path, input_source=None, output_path=None, task_id=task_id)
            # Apply per-task options if present (e.g., model, confidence, frame_skip, draw flags)
            try:
                task_options = getattr(task, 'options', {}) or {}
                if task_options:
                    Logger.info(f"[Task {task_id}] Applying task options: {task_options}")
                    # Model selection
                    model_name = task_options.get('model')
                    if model_name:
                        pipeline.vehicle_detector.model_name = model_name
                        try:
                            pipeline.vehicle_detector.load_model()
                            Logger.info(f"[Task {task_id}] Vehicle detector loaded model: {model_name}")
                        except Exception as e:
                            Logger.warning(f"[Task {task_id}] Failed to load specified model '{model_name}': {e}")
                    # Confidence threshold
                    if 'confidence' in task_options:
                        try:
                            pipeline.vehicle_detector.confidence_threshold = float(task_options.get('confidence', pipeline.vehicle_detector.confidence_threshold))
                        except Exception:
                            pass
                    # Frame skip
                    if 'frame_skip' in task_options:
                        try:
                            fs = int(task_options.get('frame_skip', pipeline.frame_skip))
                            pipeline.frame_skip = max(1, fs)
                            Logger.info(f"[Task {task_id}] Frame skip set to: {pipeline.frame_skip}")
                        except Exception:
                            pass
                    # Draw flags
                    if 'drawConfidence' in task_options:
                        pipeline.draw_confidence = bool(task_options.get('drawConfidence'))
                    if 'drawTrajectories' in task_options:
                        pipeline.draw_trajectories = bool(task_options.get('drawTrajectories'))
            except Exception as e:
                Logger.warning(f"[Task {task_id}] Error applying task options: {e}")
            Logger.info(f"[Task {task_id}] Pipeline initialized with task-specific zones")

            # Double-check zones loaded in pipeline; fail early if none present
            try:
                if not pipeline.zone_manager or len(pipeline.zone_manager.zones) == 0:
                    raise RuntimeError('No zones configured for this task. Create at least one zone before processing.')
            except Exception as e:
                raise RuntimeError(f"Zone validation failed: {e}")
            
            # Set input/output - resolve to absolute paths
            input_path = task.input_path
            Logger.info(f"[Task {task_id}] Original input_path: {input_path}")
            
            input_path_obj = Path(input_path)
            if not input_path_obj.is_absolute():
                input_path = str(Path.cwd() / input_path)
                Logger.info(f"[Task {task_id}] Converted to absolute: {input_path}")
            
            # Validate input file exists
            if not Path(input_path).exists():
                raise FileNotFoundError(f"Input file not found: {input_path}")
            
            Logger.info(f"[Task {task_id}] Input file validated: {input_path}")
            
            # Create output directory if needed
            output_dir = Path.cwd() / "data/outputs"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / f"{task.task_id}_result.mp4")
            
            Logger.info(f"[Task {task_id}] Setting video source to: {input_path}")
            # Set input source - this will trigger the property setter to open the video
            pipeline.video_processor.input_source = input_path
            Logger.info(f"[Task {task_id}] Video source set successfully")
            
            pipeline.video_processor.output_path = output_path
            
            # Rescale zones to match the actual video resolution so coordinates align
            try:
                vw, vh = pipeline.video_processor.width, pipeline.video_processor.height
                pipeline.zone_manager.rescale_to(vw, vh)
                Logger.info(f"[Task {task_id}] Zones rescaled to video size: {vw}x{vh}")
            except Exception as e:
                Logger.warning(f"[Task {task_id}] Failed to rescale zones: {e}")
            
            # Store selected zone IDs in pipeline for zone-filtered processing
            if hasattr(task, 'selected_zone_ids') and task.selected_zone_ids:
                pipeline.selected_zone_ids = task.selected_zone_ids
                Logger.info(f"[Task {task_id}] Pipeline configured for zone-filtered processing: {task.selected_zone_ids}")
            
            Logger.info(f"[Task {task_id}] Processing: input={input_path}, output={output_path}")
            task.progress = 10
            
            if task.task_type == 'video':
                # Process video
                pipeline.video_processor.input_source = input_path
                pipeline.video_processor.output_path = output_path
                
                # Get total frames for progress calculation
                total_frames = pipeline.video_processor.cap.get(cv2.CAP_PROP_FRAME_COUNT) if pipeline.video_processor.cap else 1
                Logger.info(f"[Task {task_id}] Total frames to process: {total_frames}")

                # Read and validate first frame to avoid producing empty videos
                first_frame = pipeline.video_processor.read_frame()
                if first_frame is None:
                    raise RuntimeError(f"[Task {task_id}] Could not read first frame from: {input_path}")
                
                # Initialize analytics
                
                analytics = AnalyticsCollector()
                analytics.start_timing()
                
                frame_count = 0
                
                # Process the first frame already read
                try:
                    results = pipeline.process_frame(first_frame, frame_count)
                    annotated = pipeline.draw_results(first_frame, results)
                    pipeline.video_processor.write_frame(annotated)
                    detections_count = len(results.get('detections', []))
                    # Record unique detected vehicles for analytics
                    try:
                        for det in results.get('detections', []):
                            tid = det.get('track_id')
                            if tid is not None:
                                try:
                                    analytics.record_detection(int(tid))
                                except Exception:
                                    analytics.record_detection(tid)
                    except Exception:
                        pass

                    violations_count = len([v for v in results.get('violations', []) if v.get('is_confirmed')])
                    analytics.record_frame_data(frame_count, detections_count, violations_count)
                    for v in results.get('violations', []):
                        if v.get('is_confirmed') and v.get('track_id') is not None:
                            try:
                                analytics.record_violation(int(v['track_id']))
                            except Exception:
                                analytics.record_violation(v['track_id'])
                except Exception as frame_error:
                    Logger.warning(f"[Task {task_id}] Error processing frame {frame_count}: {str(frame_error)}")
                frame_count += 1

                while True:
                    frame = pipeline.video_processor.read_frame()
                    if frame is None:
                        break
                    
                    try:
                        results = pipeline.process_frame(frame, frame_count)
                        annotated = pipeline.draw_results(frame, results)
                        pipeline.video_processor.write_frame(annotated)

                        # Record unique detected vehicles for analytics
                        try:
                            for det in results.get('detections', []):
                                tid = det.get('track_id')
                                if tid is not None:
                                    try:
                                        analytics.record_detection(int(tid))
                                    except Exception:
                                        analytics.record_detection(tid)
                        except Exception:
                            pass

                        # Record analytics per frame
                        detections_count = len(results.get('detections', []))
                        violations_count = len([v for v in results.get('violations', []) if v.get('is_confirmed')])
                        analytics.record_frame_data(frame_count, detections_count, violations_count)
                        for v in results.get('violations', []):
                            if v.get('is_confirmed') and v.get('track_id') is not None:
                                try:
                                    analytics.record_violation(int(v['track_id']))
                                except Exception:
                                    analytics.record_violation(v['track_id'])
                    except Exception as frame_error:
                        Logger.warning(f"[Task {task_id}] Error processing frame {frame_count}: {str(frame_error)}")
                        # Continue to next frame even if one fails
                        pass
                    
                    # Update progress - calculate based on actual total frames
                    frame_count += 1
                    if total_frames > 0:
                        progress = int((frame_count / total_frames) * 90) + 10
                        task.progress = min(90, progress)
                    
                    if frame_count % 100 == 0:
                        Logger.info(f"[Task {task_id}] Processed {frame_count}/{int(total_frames)} frames, progress: {task.progress}%")
                
                Logger.info(f"[Task {task_id}] Frame processing complete. Total frames: {frame_count}")
                
                # Release resources and ensure file is written
                try:
                    pipeline.video_processor.release()
                    Logger.info(f"[Task {task_id}] Video processor released successfully")
                    # Give the system a moment to ensure all writes are flushed
                    import time
                    time.sleep(1)
                except Exception as release_error:
                    Logger.error(f"[Task {task_id}] Error releasing video processor: {str(release_error)}")
                    raise
                
                # Collect stats
                analytics.end_timing()
                stats = analytics.get_statistics()
                task.analytics = stats
                Logger.info(f"[Task {task_id}] Analytics: {stats}")
                
            elif task.task_type == 'image':
                # Process image: rescale zones to image size and save annotated image
                img = cv2.imread(input_path)
                if img is None:
                    raise RuntimeError(f"[Task {task_id}] Failed to read image: {input_path}")
                ih, iw = img.shape[0], img.shape[1]
                try:
                    pipeline.zone_manager.rescale_to(iw, ih)
                    Logger.info(f"[Task {task_id}] Zones rescaled to image size: {iw}x{ih}")
                except Exception as e:
                    Logger.warning(f"[Task {task_id}] Failed to rescale zones for image: {e}")
                
                # Build image output path with proper extension
                img_ext = Path(input_path).suffix.lower() or '.jpg'
                img_out = Path(output_dir) / f"{task.task_id}_result{img_ext}"
                pipeline.process_image(input_path, str(img_out))
                task.analytics = {'frames_processed': 1}
            
            task.progress = 100
            # Use actual output path (may have changed due to codec fallback)
            if task.task_type == 'image':
                actual_output = str(img_out)
            else:
                actual_output = pipeline.video_processor.output_path or output_path

            # Collect saved violation snapshots from pipeline (if any)
            snapshots_list = []
            try:
                saved = getattr(pipeline, 'saved_violation_snapshots', {}) or {}
                for tid, info in saved.items():
                    # Normalize both legacy string URL and new metadata dict
                    try:
                        first_frame = pipeline.violation_detector.violation_history.get(int(tid), {}).get('first_violation_frame')
                    except Exception:
                        first_frame = pipeline.violation_detector.violation_history.get(tid, {}).get('first_violation_frame')

                    if isinstance(info, dict):
                        snapshots_list.append({
                            'track_id': tid,
                            'snapshot_url': info.get('snapshot_full') or info.get('snapshot'),
                            'snapshot_crop_url': info.get('snapshot_crop'),
                            'bbox': info.get('bbox'),
                            'image_width': info.get('image_width'),
                            'image_height': info.get('image_height'),
                            'first_violation_frame': info.get('first_violation_frame') or first_frame
                        })
                    else:
                        snapshots_list.append({
                            'track_id': tid,
                            'snapshot_url': info,
                            'snapshot_crop_url': None,
                            'bbox': None,
                            'image_width': None,
                            'image_height': None,
                            'first_violation_frame': first_frame
                        })
            except Exception as e:
                Logger.warning(f"[{task_id}] Failed collecting snapshots: {e}")

            task.result = {
                'output_path': actual_output,
                'timestamp': datetime.now().isoformat(),
                'stream_url': f"/api/result/{task_id}/stream",
                'snapshots': snapshots_list
            }

            # Include snapshots in analytics report for frontend convenience
            try:
                if isinstance(task.analytics, dict):
                    task.analytics['snapshots'] = snapshots_list
            except Exception:
                pass
            task.status = 'completed'
            
            Logger.info(f"Task completed: {task_id}")
        
        except Exception as e:
            task.status = 'failed'
            task.error_message = str(e)
            Logger.error(f"Task failed: {task_id} - {str(e)}")
        
        finally:
            task.end_time = datetime.now()
    
    def run(self, debug=False):
        """Run the web server"""
        Logger.info(f"Starting web server on http://localhost:{self.port}")
        self.app.run(host='0.0.0.0', port=self.port, debug=debug, threaded=True)


def create_app(config_path='configs/config.yaml', port=5000):
    """Create and configure Flask app"""
    server = WebServer(config_path, port)
    return server.app, server

if __name__ == '__main__':
    server = WebServer()
    server.run(debug=False)