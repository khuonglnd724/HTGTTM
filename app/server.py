"""Flask Web Server for Lane Violation Detection"""
import os
import json
import threading
import cv2
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename

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


class WebServer:
    """Web server for Lane Violation Detection"""
    
    def __init__(self, config_path='configs/config.yaml', port=5000):
        """Initialize web server"""
        self.app = Flask(__name__)
        CORS(self.app)
        
        self.port = port
        self.config_path = config_path
        self.pipeline = None
        
        # Configuration
        self.app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 500  # 500MB max
        self.app.config['UPLOAD_FOLDER'] = 'data/videos'
        self.ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'jpg', 'jpeg', 'png'}
        
        # Task management
        self.tasks = {}
        self.task_counter = 0
        
        Logger.setup('logs')
        Logger.info(f"Web server initialized on port {port}")
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main page"""
            return render_template('index.html')
        
        @self.app.route('/api/status', methods=['GET'])
        def get_status():
            """Get system status"""
            try:
                return jsonify({
                    'status': 'online',
                    'timestamp': datetime.now().isoformat(),
                    'tasks_count': len(self.tasks),
                    'active_tasks': len([t for t in self.tasks.values() if t.status == 'processing'])
                })
            except Exception as e:
                Logger.error(f"Status error: {str(e)}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/api/upload', methods=['POST'])
        def upload_file():
            """Upload video file"""
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
                
                return jsonify({
                    'success': True,
                    'filename': filename,
                    'filepath': str(filepath)
                })
            
            except Exception as e:
                Logger.error(f"Upload error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/process', methods=['POST'])
        def process():
            """Start processing task"""
            try:
                data = request.get_json()
                input_path = data.get('input_path')
                task_type = data.get('type', 'video')
                
                if not input_path:
                    return jsonify({'error': 'No input path provided'}), 400
                
                # Create task
                task_id = f"task_{self.task_counter}"
                self.task_counter += 1
                
                task = ProcessingTask(task_id, input_path, task_type)
                self.tasks[task_id] = task
                
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
                    'task_id': task_id
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
                
                # Convert source (0 for webcam, or RTSP URL)
                if source == '0':
                    source = 0
                
                def generate():
                    """Generate video frames"""
                    pipeline = LaneViolationPipeline(self.config_path)
                    pipeline.vehicle_detector.model_name = model
                    pipeline.vehicle_detector.load_model()
                    
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
            
            # Initialize pipeline
            pipeline = LaneViolationPipeline(self.config_path)
            
            # Set input/output
            input_path = task.input_path
            output_path = f"data/outputs/{task.task_id}_result.mp4"
            
            task.progress = 10
            
            if task.task_type == 'video':
                # Process video
                pipeline.video_processor.input_source = input_path
                pipeline.video_processor.output_path = output_path
                
                # Initialize analytics
                analytics = AnalyticsCollector()
                analytics.start_timing()
                
                frame_count = 0
                
                while True:
                    frame = pipeline.video_processor.read_frame()
                    if frame is None:
                        break
                    
                    results = pipeline.process_frame(frame, frame_count)
                    annotated = pipeline.draw_results(frame, results)
                    pipeline.video_processor.write_frame(annotated)
                    
                    # Update progress
                    frame_count += 1
                    task.progress = min(90, int((frame_count / 300) * 80) + 10)
                
                analytics.end_timing()
                pipeline.video_processor.release()
                
                # Collect stats
                stats = analytics.get_statistics()
                task.analytics = stats
                
            elif task.task_type == 'image':
                # Process image
                pipeline.process_image(input_path, output_path)
                task.analytics = {'frames_processed': 1}
            
            task.progress = 100
            task.result = {
                'output_path': output_path,
                'timestamp': datetime.now().isoformat()
            }
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
