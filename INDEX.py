"""
Lane Violation Detection System - Complete Project Index
Hệ thống nhận diện các phương tiện sai làn trong tham gia giao thông
"""

# ============================================================================
# PROJECT STRUCTURE AND FILE GUIDE
# ============================================================================

PROJECT_FILES = {
    # Main entry points
    'main.py': {
        'description': 'Main entry point for the application',
        'usage': 'python main.py --input video.mp4 --output result.mp4',
        'args': [
            '--config: Path to configuration file',
            '--input: Input video file or camera index',
            '--output: Output video file path',
            '--image: Process single image instead of video',
            '--model: YOLO model to use'
        ]
    },
    
    'test.py': {
        'description': 'Test script to verify installation',
        'usage': 'python test.py --mode modules',
        'modes': ['modules', 'image']
    },
    
    'examples.py': {
        'description': 'Advanced usage examples',
        'usage': 'python examples.py',
        'includes': [
            'Basic video processing',
            'Image processing',
            'Custom configuration',
            'Frame-by-frame processing',
            'Webcam real-time processing',
            'Analytics collection',
            'Custom drawing',
            'Batch processing',
            'Model performance comparison'
        ]
    },
    
    # Installation scripts
    'install.bat': {
        'description': 'Automated installation for Windows',
        'usage': 'install.bat',
        'os': 'Windows'
    },
    
    'install.sh': {
        'description': 'Automated installation for Linux/Mac',
        'usage': 'bash install.sh',
        'os': 'Linux, macOS'
    },
    
    # Configuration
    'configs/config.yaml': {
        'description': 'Main system configuration',
        'sections': [
            'YOLO settings (model, confidence, device)',
            'Lane detection parameters',
            'Vehicle tracking settings',
            'Processing settings',
            'Alert configuration'
        ]
    },
    
    # Core modules
    'src/pipeline.py': {
        'description': 'Main processing pipeline',
        'class': 'LaneViolationPipeline',
        'methods': [
            'process_frame()',
            'draw_results()',
            'run()',
            'process_image()'
        ]
    },
    
    'src/modules/vehicle_detector.py': {
        'description': 'YOLOv8-based vehicle detection',
        'class': 'VehicleDetector',
        'methods': [
            'detect()',
            'detect_with_tracking()',
            'get_model_info()'
        ]
    },
    
    'src/modules/lane_detector.py': {
        'description': 'Lane detection using image processing',
        'class': 'LaneDetector',
        'methods': [
            'detect_lanes()',
            'get_lane_boundaries()',
            'preprocess_image()',
            'detect_edges()',
            'group_lines()'
        ]
    },
    
    'src/modules/violation_detector.py': {
        'description': 'Lane violation detection logic',
        'class': 'ViolationDetector',
        'methods': [
            'detect_violation()',
            'batch_detect_violations()',
            'calculate_violation_score()',
            'is_in_lane()'
        ]
    },
    
    'src/modules/tracker.py': {
        'description': 'Vehicle tracking module',
        'class': 'SimpleTracker',
        'methods': [
            'update()',
            'get_active_tracks()',
            'reset()'
        ]
    },
    
    # Utilities
    'src/utils/config_loader.py': {
        'description': 'Configuration management',
        'class': 'ConfigLoader',
        'methods': ['get()', 'set()', 'save()']
    },
    
    'src/utils/logger.py': {
        'description': 'Logging system',
        'class': 'Logger',
        'methods': ['info()', 'debug()', 'warning()', 'error()']
    },
    
    'src/utils/drawing.py': {
        'description': 'Visualization utilities',
        'class': 'DrawingUtils',
        'methods': [
            'draw_box()',
            'draw_lines()',
            'draw_polygon()',
            'draw_trajectory()',
            'draw_text()',
            'draw_alert_box()'
        ]
    },
    
    'src/utils/video_processor.py': {
        'description': 'Video input/output handling',
        'class': 'VideoProcessor',
        'methods': [
            'read_frame()',
            'write_frame()',
            'release()',
            'get_properties()'
        ]
    },
    
    'src/utils/analytics.py': {
        'description': 'Statistics and analytics',
        'class': 'AnalyticsCollector',
        'methods': [
            'record_frame_data()',
            'get_statistics()',
            'save_report()',
            'print_report()'
        ]
    },
    
    # Documentation
    'README.md': {
        'description': 'Full project documentation',
        'sections': [
            'Features overview',
            'Project structure',
            'Installation guide',
            'Usage examples',
            'Configuration guide',
            'Architecture explanation',
            'Troubleshooting'
        ]
    },
    
    'QUICKSTART.md': {
        'description': 'Quick start guide',
        'language': 'Vietnamese & English',
        'sections': [
            'Installation steps',
            'Running examples',
            'Model selection',
            'Troubleshooting'
        ]
    },
    
    'PROJECT_SUMMARY.md': {
        'description': 'Comprehensive project overview',
        'includes': [
            'Full feature list',
            'Technology stack',
            'Performance metrics',
            'Customization guide',
            'Learning resources'
        ]
    },
    
    'API_REFERENCE.md': {
        'description': 'Complete API documentation',
        'sections': [
            'Class references',
            'Method signatures',
            'Data structures',
            'Usage examples'
        ]
    },
    
    # Dependencies
    'requirements.txt': {
        'description': 'Python package dependencies',
        'packages': [
            'ultralytics (YOLOv8)',
            'opencv-python',
            'torch (PyTorch)',
            'numpy',
            'pyyaml'
        ]
    }
}

# ============================================================================
# QUICK REFERENCE
# ============================================================================

QUICK_START = """
1. INSTALLATION (Windows)
   ===========================
   install.bat
   venv\\Scripts\\activate.bat
   
2. RUN SYSTEM
   ===========================
   python main.py --input data/videos/sample.mp4
   
3. PROCESS IMAGE
   ===========================
   python main.py --image path/to/image.jpg
   
4. WEBCAM
   ===========================
   python main.py --input 0
   
5. RUN EXAMPLES
   ===========================
   python examples.py
"""

COMMAND_REFERENCE = {
    'Process Video': 'python main.py --input video.mp4 --output result.mp4',
    'Process Image': 'python main.py --image image.jpg --output result.jpg',
    'Webcam': 'python main.py --input 0',
    'Custom Model': 'python main.py --input video.mp4 --model yolov8l',
    'Custom Config': 'python main.py --config configs/custom.yaml --input video.mp4',
    'Run Tests': 'python test.py --mode modules',
    'Run Examples': 'python examples.py',
    'Activate venv': 'venv\\Scripts\\activate.bat'
}

MODEL_INFO = {
    'yolov8n': {'speed': '⚡ Fastest', 'accuracy': 'Basic', 'vram': '2GB'},
    'yolov8s': {'speed': '⚡ Fast', 'accuracy': 'Good', 'vram': '3GB'},
    'yolov8m': {'speed': '⚖️ Balanced', 'accuracy': 'Better', 'vram': '5GB'},
    'yolov8l': {'speed': '🐢 Slow', 'accuracy': 'Very Good', 'vram': '7GB'},
    'yolov8x': {'speed': '🐌 Slowest', 'accuracy': 'Excellent', 'vram': '10GB'},
}

DIRECTORY_STRUCTURE = """
lane_violation_detection/
├── main.py                         [Entry point]
├── test.py                         [Testing]
├── examples.py                     [Advanced examples]
├── requirements.txt                [Dependencies]
│
├── configs/
│   └── config.yaml                [Configuration]
│
├── src/
│   ├── pipeline.py                [Main pipeline]
│   ├── modules/                   [Detection modules]
│   │   ├── vehicle_detector.py
│   │   ├── lane_detector.py
│   │   ├── violation_detector.py
│   │   └── tracker.py
│   └── utils/                     [Utilities]
│       ├── config_loader.py
│       ├── logger.py
│       ├── drawing.py
│       ├── video_processor.py
│       └── analytics.py
│
├── data/
│   ├── videos/                    [Input videos]
│   ├── models/                    [YOLO models cache]
│   └── outputs/                   [Results]
│
├── logs/                          [Log files]
│
└── docs/                          [Documentation]
    ├── README.md
    ├── QUICKSTART.md
    ├── PROJECT_SUMMARY.md
    └── API_REFERENCE.md
"""

# ============================================================================
# KEY CONFIGURATIONS
# ============================================================================

CONFIG_EXAMPLES = {
    'Fast Processing': {
        'yolo.model_name': 'yolov8n',
        'processing.frame_skip': 2,
        'yolo.device': 'cuda'
    },
    'High Accuracy': {
        'yolo.model_name': 'yolov8l',
        'yolo.confidence_threshold': 0.4,
        'processing.frame_skip': 1,
        'yolo.device': 'cuda'
    },
    'CPU Only': {
        'yolo.model_name': 'yolov8s',
        'yolo.device': 'cpu',
        'processing.frame_skip': 3
    }
}

# ============================================================================
# TROUBLESHOOTING GUIDE
# ============================================================================

TROUBLESHOOTING = {
    'Low Detection Rate': {
        'cause': 'Not enough detections found',
        'solutions': [
            'Lower confidence_threshold to 0.3-0.4',
            'Use larger model (yolov8l, yolov8x)',
            'Ensure good video quality',
            'Check lighting conditions'
        ]
    },
    'Slow Processing': {
        'cause': 'Low FPS',
        'solutions': [
            'Use smaller model (yolov8n, yolov8s)',
            'Increase frame_skip to 2 or 3',
            'Use GPU instead of CPU',
            'Lower input resolution'
        ]
    },
    'False Lane Detections': {
        'cause': 'Inaccurate lane detection',
        'solutions': [
            'Adjust canny_threshold1 and canny_threshold2',
            'Increase hough_threshold',
            'Improve lighting',
            'Use clearer road markings'
        ]
    },
    'CUDA Not Found': {
        'cause': 'GPU not available',
        'solutions': [
            'Check NVIDIA driver: nvidia-smi',
            'Update PyTorch with CUDA support',
            'Use CPU mode: device: "cpu"'
        ]
    },
    'Out of Memory': {
        'cause': 'Insufficient VRAM',
        'solutions': [
            'Use smaller model',
            'Reduce input resolution',
            'Increase frame_skip',
            'Use CPU instead of GPU'
        ]
    }
}

# ============================================================================
# USAGE PATTERNS
# ============================================================================

USAGE_EXAMPLES = {
    'Basic': """
from src.pipeline import LaneViolationPipeline

pipeline = LaneViolationPipeline()
pipeline.run()
    """,
    
    'Custom Input/Output': """
from src.pipeline import LaneViolationPipeline

pipeline = LaneViolationPipeline()
pipeline.video_processor.input_source = 'video.mp4'
pipeline.video_processor.output_path = 'result.mp4'
pipeline.run()
    """,
    
    'Frame by Frame': """
from src.pipeline import LaneViolationPipeline

pipeline = LaneViolationPipeline()

while True:
    frame = pipeline.video_processor.read_frame()
    if frame is None:
        break
    
    results = pipeline.process_frame(frame, frame_num)
    annotated = pipeline.draw_results(frame, results)
    pipeline.video_processor.write_frame(annotated)
    """,
    
    'With Analytics': """
from src.pipeline import LaneViolationPipeline
from src.utils.analytics import AnalyticsCollector

pipeline = LaneViolationPipeline()
analytics = AnalyticsCollector()

analytics.start_timing()
# ... process frames ...
analytics.end_timing()
analytics.print_report()
    """
}

# ============================================================================
# DOCUMENTATION INDEX
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Lane Violation Detection System - Project Index")
    print("=" * 70)
    print("\n📚 DOCUMENTATION:")
    print("  - README.md: Full documentation and guide")
    print("  - QUICKSTART.md: Quick start guide")
    print("  - PROJECT_SUMMARY.md: Project overview")
    print("  - API_REFERENCE.md: Complete API documentation")
    print("  - This file: Project index and reference")
    
    print("\n📁 DIRECTORY STRUCTURE:")
    print(DIRECTORY_STRUCTURE)
    
    print("\n⚡ QUICK START:")
    print(QUICK_START)
    
    print("\n📋 KEY COMMANDS:")
    for cmd_name, cmd in COMMAND_REFERENCE.items():
        print(f"  {cmd_name}:")
        print(f"    {cmd}")
    
    print("\n🚀 MODELS AVAILABLE:")
    for model, info in MODEL_INFO.items():
        print(f"  {model}: Speed={info['speed']}, Accuracy={info['accuracy']}, VRAM={info['vram']}")
    
    print("\n💡 FOR MORE INFORMATION:")
    print("  See README.md for full documentation")
    print("  See QUICKSTART.md for installation and basic usage")
    print("  See API_REFERENCE.md for detailed API documentation")
    print("\n" + "=" * 70)
