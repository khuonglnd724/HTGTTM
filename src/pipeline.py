"""Main detection pipeline"""
import cv2
import numpy as np
from typing import Dict, List
from pathlib import Path

from src.utils.config_loader import ConfigLoader
from src.utils.logger import Logger
from src.utils.drawing import DrawingUtils
from src.utils.video_processor import VideoProcessor
from src.utils.zone_manager import ZoneManager
from src.modules.vehicle_detector import VehicleDetector
from src.modules.lane_detector import LaneDetector
from src.modules.violation_detector import ViolationDetector


class LaneViolationPipeline:
    """Main detection pipeline combining all modules"""
    
    def __init__(self, config_path: str = "configs/config.yaml", input_source=None, output_path=None, task_id=None):
        """
        Initialize pipeline
        
        Args:
            config_path: Path to configuration file
            input_source: Optional override for video input; if None, do not open here
            output_path: Optional override for output path
            task_id: Task ID for loading task-specific zones
        """
        self.config = ConfigLoader(config_path)
        self.task_id = task_id
        self.selected_zone_ids = []  # Zones to focus processing on (can be multiple)
        Logger.setup("logs")
        
        Logger.info("Initializing Lane Violation Detection Pipeline")
        
        # Initialize modules with performance settings
        self.vehicle_detector = VehicleDetector(
            model_name=self.config.get('yolo.model_name', 'yolov8m'),
            confidence_threshold=self.config.get('yolo.confidence_threshold', 0.5),
            device=self.config.get('yolo.device', 'cuda'),
            half_precision=self.config.get('yolo.half_precision', True),
            input_size=self.config.get('yolo.input_size', 640)
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
        
        # Initialize zone manager with task-specific zones
        task_zones_path = f"data/tasks/{task_id}/zones.json" if task_id else 'configs/zones.json'
        self.zone_manager = ZoneManager(task_zones_path)
        Logger.info(f"Loaded {len(self.zone_manager.zones)} detection zones from {task_zones_path}")
        
        # If no override provided, default to None here to avoid opening sample video prematurely
        resolved_input = input_source if input_source is not None else None
        resolved_output = output_path if output_path is not None else self.config.get('processing.output_path')
        
        self.video_processor = VideoProcessor(
            input_source=resolved_input,
            output_path=resolved_output
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
        
        # Filter detections by selected zones if specified
        if self.selected_zone_ids and len(self.selected_zone_ids) > 0:
            filtered_detections = []
            for detection in detections:
                # Get vehicle center point
                cx, cy = detection['center']
                
                # Check if center is inside ANY of the selected zones
                in_any_zone = False
                for zone_id in self.selected_zone_ids:
                    zone = self.zone_manager.get_zone(zone_id)
                    if zone and zone.contains_point((cx, cy)):
                        in_any_zone = True
                        break
                
                if in_any_zone:
                    filtered_detections.append(detection)
                    Logger.debug(f"Frame {frame_num}: Vehicle {detection['track_id']} in selected zones")
                else:
                    Logger.debug(f"Frame {frame_num}: Vehicle {detection['track_id']} outside all selected zones")
            
            detections = filtered_detections
            Logger.debug(f"Frame {frame_num}: Filtered detections {len(detection_result['detections'])} -> {len(detections)}")
        
        results['detections'] = detections
        
        # Detect violations (both lane-based and zone-based)
        # Pass selected_zone_ids to only check violations in those zones
        if detections:
            violations = self.violation_detector.batch_detect_violations(
                detections, lane_boundaries, self.zone_manager,
                selected_zone_ids=self.selected_zone_ids
            )
            results['violations'] = violations
            
            # Count violations (only if confirmed by consecutive frames)
            for violation in violations:
                if violation['is_violating'] and violation.get('consecutive_violations', 0) >= 3:
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
        
        # Draw zones: only selected zones if specified, otherwise all zones
        if self.selected_zone_ids and len(self.selected_zone_ids) > 0:
            # Draw only the selected zones with highlight
            for zone_id in self.selected_zone_ids:
                zone = self.zone_manager.get_zone(zone_id)
                if zone:
                    # Draw selected zone with highlight using alpha blending
                    polygon = np.array(zone.polygon, dtype=np.int32)
                    
                    # Create overlay for transparent fill
                    overlay = frame_copy.copy()
                    cv2.fillPoly(overlay, [polygon], (0, 255, 255))  # Yellow fill
                    cv2.addWeighted(overlay, 0.2, frame_copy, 0.8, 0, frame_copy)  # 20% opacity
                    
                    # Draw border
                    cv2.polylines(frame_copy, [polygon], True, (0, 255, 255), 3)  # Yellow border
                    
                    # Add zone label
                    if zone.polygon:
                        x, y = zone.polygon[0]
                        cv2.putText(frame_copy, zone.name, (int(x), int(y)-10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                    Logger.debug(f"Drew selected zone: {zone_id}")
        else:
            # Draw all zones (default behavior if no selection)
            if len(self.zone_manager.zones) > 0:
                frame_copy = self.zone_manager.draw_zones(frame_copy, alpha=0.25)
        
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
            consecutive = violation_info.get('consecutive_violations', 0)
            
            # Only show VIOLATION label if detected in 3+ consecutive frames
            if is_violating and consecutive >= 3:
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
        # Count only confirmed violations (3+ consecutive frames)
        confirmed_violations = [v for v in violations if v['is_violating'] and v.get('consecutive_violations', 0) >= 3]
        stats_text = [
            f"Frame: {results['frame_num']}",
            f"Detections: {len(results['detections'])}",
            f"Violations: {len(confirmed_violations)}",
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
