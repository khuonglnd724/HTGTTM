"""Main detection pipeline"""
import cv2
import numpy as np
from typing import Dict, List
from pathlib import Path

from src.utils.config_loader import ConfigLoader
from src.utils.logger import Logger
from src.utils.drawing import DrawingUtils
from src.utils.video_processor import VideoProcessor
from src.modules.vehicle_detector import VehicleDetector
from src.modules.lane_detector import LaneDetector
from src.modules.violation_detector import ViolationDetector


class LaneViolationPipeline:
    """Main detection pipeline combining all modules"""
    
    def __init__(self, config_path: str = "configs/config.yaml"):
        """
        Initialize pipeline
        
        Args:
            config_path: Path to configuration file
        """
        self.config = ConfigLoader(config_path)
        Logger.setup("logs")
        
        Logger.info("Initializing Lane Violation Detection Pipeline")
        
        # Initialize modules
        self.vehicle_detector = VehicleDetector(
            model_name=self.config.get('yolo.model_name', 'yolov8m'),
            confidence_threshold=self.config.get('yolo.confidence_threshold', 0.5),
            device=self.config.get('yolo.device', 'cuda')
        )
        
        self.lane_detector = LaneDetector(
            canny_low=self.config.get('lane_detection.canny_threshold1', 50),
            canny_high=self.config.get('lane_detection.canny_threshold2', 150),
            hough_threshold=self.config.get('lane_detection.hough_threshold', 50),
            hough_min_length=self.config.get('lane_detection.hough_min_line_length', 50),
            hough_max_gap=self.config.get('lane_detection.hough_max_line_gap', 10)
        )
        
        self.violation_detector = ViolationDetector(
            violation_threshold=0.3
        )
        
        self.video_processor = VideoProcessor(
            input_source=self.config.get('processing.input_source'),
            output_path=self.config.get('processing.output_path')
        )
        
        self.frame_skip = self.config.get('processing.frame_skip', 1)
        self.draw_trajectories = self.config.get('processing.draw_trajectories', True)
        self.draw_confidence = self.config.get('processing.draw_confidence', True)
        
        self.violation_count = 0
        self.violation_history = {}
        
        Logger.info("Pipeline initialized successfully")
    
    def process_frame(self, frame: np.ndarray, frame_num: int) -> Dict:
        """
        Process single frame
        
        Args:
            frame: Input frame
            frame_num: Frame number
            
        Returns:
            Processing results
        """
        results = {
            'frame_num': frame_num,
            'detections': [],
            'violations': [],
            'lane_boundaries': {}
        }
        
        # Skip frames if configured
        if frame_num % self.frame_skip != 0:
            return results
        
        # Detect lanes
        lane_result = self.lane_detector.detect_lanes(frame)
        lane_boundaries = self.lane_detector.get_lane_boundaries(frame)
        results['lane_boundaries'] = lane_boundaries
        
        # Detect vehicles with tracking
        detection_result = self.vehicle_detector.detect_with_tracking(frame)
        detections = detection_result['detections']
        results['detections'] = detections
        
        # Detect violations
        if detections:
            violations = self.violation_detector.batch_detect_violations(
                detections, lane_boundaries
            )
            results['violations'] = violations
            
            # Count violations
            for violation in violations:
                if violation['is_violating']:
                    self.violation_count += 1
        
        return results
    
    def draw_results(self, frame: np.ndarray, results: Dict) -> np.ndarray:
        """
        Draw detection and violation results on frame
        
        Args:
            frame: Input frame
            results: Processing results
            
        Returns:
            Annotated frame
        """
        frame_copy = frame.copy()
        
        # Draw lane boundaries
        lane_boundaries = results.get('lane_boundaries', {})
        boundaries = lane_boundaries.get('boundaries', [])
        
        for i, boundary in enumerate(boundaries):
            # Draw lane boundaries as vertical lines
            left = int(boundary['left'])
            right = int(boundary['right'])
            h = frame.shape[0]
            
            cv2.line(frame_copy, (left, 0), (left, h), (200, 200, 200), 2)
            cv2.line(frame_copy, (right, 0), (right, h), (200, 200, 200), 2)
        
        # Draw detections and violations
        violations = results.get('violations', [])
        
        for violation_info in violations:
            detection = violation_info['detection']
            box = detection['box']
            track_id = detection['track_id']
            confidence = detection['confidence']
            
            is_violating = violation_info['is_violating']
            
            if is_violating:
                # Draw violation box
                DrawingUtils.draw_alert_box(frame_copy, box, 
                                          message=f"VIOLATION #{track_id}")
                
                # Draw center point in red
                cx, cy = detection['center']
                cv2.circle(frame_copy, (int(cx), int(cy)), 5, (0, 0, 255), -1)
            else:
                # Draw normal detection box
                label = f"ID:{track_id}" if track_id >= 0 else "Unknown"
                color = 'green'
                
                DrawingUtils.draw_box(frame_copy, box, color=color, 
                                    label=label, 
                                    confidence=confidence if self.draw_confidence else None)
                
                # Draw center point in green
                cx, cy = detection['center']
                cv2.circle(frame_copy, (int(cx), int(cy)), 3, (0, 255, 0), -1)
        
        # Draw statistics
        stats_text = [
            f"Frame: {results['frame_num']}",
            f"Detections: {len(results['detections'])}",
            f"Violations: {len([v for v in violations if v['is_violating']])}",
            f"Total Violations: {self.violation_count}"
        ]
        
        y_offset = 30
        for text in stats_text:
            DrawingUtils.draw_text(frame_copy, text, (10, y_offset),
                                 color='white', bg_color='black')
            y_offset += 30
        
        return frame_copy
    
    def run(self):
        """Run the complete pipeline"""
        Logger.info("Starting lane violation detection")
        
        frame_num = 0
        
        try:
            while True:
                frame = self.video_processor.read_frame()
                if frame is None:
                    break
                
                # Process frame
                results = self.process_frame(frame, frame_num)
                
                # Draw results
                annotated_frame = self.draw_results(frame, results)
                
                # Write output
                self.video_processor.write_frame(annotated_frame)
                
                # Display progress
                if frame_num % 30 == 0:
                    Logger.info(f"Processed {frame_num} frames, "
                               f"Violations detected: {self.violation_count}")
                
                frame_num += 1
        
        except KeyboardInterrupt:
            Logger.info("Pipeline interrupted by user")
        except Exception as e:
            Logger.error(f"Pipeline error: {str(e)}")
            raise
        finally:
            self.video_processor.release()
            Logger.info(f"Pipeline completed. Total violations: {self.violation_count}")
    
    def process_image(self, image_path: str, output_path: str = None) -> np.ndarray:
        """
        Process single image
        
        Args:
            image_path: Input image path
            output_path: Output image path (optional)
            
        Returns:
            Annotated image
        """
        frame = cv2.imread(image_path)
        if frame is None:
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Process
        results = self.process_frame(frame, 0)
        
        # Draw
        annotated = self.draw_results(frame, results)
        
        # Save if output path provided
        if output_path:
            cv2.imwrite(output_path, annotated)
            Logger.info(f"Output saved: {output_path}")
        
        return annotated
