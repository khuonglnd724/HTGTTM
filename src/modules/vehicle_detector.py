"""Vehicle detection module using YOLO"""
import cv2
import numpy as np
import torch
from typing import List, Tuple, Dict
from ultralytics import YOLO
from src.utils.logger import Logger


class VehicleDetector:
    """YOLO-based vehicle detector with performance optimizations"""
    
    # Vehicle class indices in YOLO coco dataset
    VEHICLE_CLASSES = {2, 3, 5, 7}  # car, motorcycle, bus, truck
    
    def __init__(self, model_name: str = "yolov8m", confidence_threshold: float = 0.5,
                 device: str = "cuda", half_precision: bool = True, input_size: int = 640):
        """
        Initialize vehicle detector
        
        Args:
            model_name: YOLOv8 model name (n, s, m, l, x)
            confidence_threshold: Confidence threshold for detections
            device: Device to run model on (cuda or cpu)
            half_precision: Use FP16 for faster GPU inference
            input_size: YOLO input size (smaller = faster)
        """
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        self.input_size = input_size
        
        # Auto-detect CUDA availability and support device spec like 'cuda', 'cuda:0', 'cpu', or 'auto'
        cuda_available = torch.cuda.is_available()
        if device == "auto":
            device = "cuda" if cuda_available else "cpu"
            Logger.info(f"Auto-detected device: {device}")

        # Normalize device string
        device = str(device).lower()
        if device.startswith('cuda') and not cuda_available:
            Logger.warning("Requested CUDA device but CUDA not available, falling back to CPU")
            device = 'cpu'

        # Accept forms: 'cuda', 'cuda:0', 'cpu'
        self.device = device
        # half precision only when using CUDA (any cuda device string)
        self.half_precision = bool(half_precision) and self.device.startswith('cuda')
        
        Logger.info(f"Loading YOLOv8 model: {model_name} on device={self.device}")
        # Load model (deferred to load_model method for flexibility)
        self.model = None
        try:
            self.load_model()
        except Exception as e:
            Logger.error(f"Failed to load model during init: {e}")
    
    def detect(self, image: np.ndarray) -> Dict:
        """
        Detect vehicles in image
        
        Args:
            image: Input image (BGR format)
            
        Returns:
            Dictionary with detections and metadata
        """
        # Run inference
        results = self.model(image, conf=self.confidence_threshold, verbose=False)
        result = results[0]
        
        # Process detections
        detections = []
        
        if result.boxes is not None:
            for box in result.boxes:
                cls_id = int(box.cls)
                
                # Filter for vehicle classes only
                if cls_id in self.VEHICLE_CLASSES:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = float(box.conf)
                    class_name = self.model.names[cls_id]
                    track_id = int(box.id) if box.id is not None else -1
                    
                    detection = {
                        'box': (x1, y1, x2, y2),
                        'confidence': confidence,
                        'class_id': cls_id,
                        'class_name': class_name,
                        'track_id': track_id,
                        'center': ((x1 + x2) / 2, (y1 + y2) / 2)
                    }
                    detections.append(detection)
        
        return {
            'detections': detections,
            'image_shape': image.shape,
            'num_detections': len(detections)
        }

    def load_model(self):
        """(Re)load model from current `self.model_name` and move to configured device."""
        Logger.info(f"Loading YOLOv8 model: {self.model_name}")
        # Some ultralytics wrappers accept device in the constructor; try to pass it
        try:
            self.model = YOLO(f"{self.model_name}.pt")
            # Move model to device if supported
            try:
                self.model.to(self.device)
            except Exception:
                # Some YOLO wrappers auto-manage device; ignore if not supported
                pass
        except Exception as e:
            Logger.error(f"Error initializing YOLO model: {e}")
            raise

        if self.half_precision:
            Logger.info("FP16 half precision enabled for CUDA device")
        Logger.info(f"Model loaded successfully on {self.device} (input_size={self.input_size})")
    
    def detect_with_tracking(self, image: np.ndarray) -> Dict:
        """
        Detect vehicles with tracking
        
        Args:
            image: Input image
            
        Returns:
            Detection results with tracking IDs
        """
        # Use imgsz for faster inference with smaller input
        results = self.model.track(
            image, 
            conf=self.confidence_threshold, 
            persist=True, 
            verbose=False,
            imgsz=self.input_size,
            half=self.half_precision
        )
        result = results[0]
        
        detections = []
        
        if result.boxes is not None:
            for box in result.boxes:
                cls_id = int(box.cls)
                
                if cls_id in self.VEHICLE_CLASSES:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = float(box.conf)
                    class_name = self.model.names[cls_id]
                    track_id = int(box.id) if box.id is not None else -1
                    
                    detection = {
                        'box': (x1, y1, x2, y2),
                        'confidence': confidence,
                        'class_id': cls_id,
                        'class_name': class_name,
                        'track_id': track_id,
                        'center': ((x1 + x2) / 2, (y1 + y2) / 2)
                    }
                    detections.append(detection)
        
        return {
            'detections': detections,
            'image_shape': image.shape,
            'num_detections': len(detections)
        }
    
    def get_model_info(self) -> Dict:
        """Get model information"""
        return {
            'model_name': self.model_name,
            'confidence_threshold': self.confidence_threshold,
            'device': self.device,
            'num_classes': len(self.model.names),
            'class_names': self.model.names
        }
