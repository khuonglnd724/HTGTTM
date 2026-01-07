"""Lane violation detection module"""
import numpy as np
from typing import List, Dict, Tuple
from src.utils.logger import Logger


class ViolationDetector:
    """Detect lane violations"""
    
    def __init__(self, violation_threshold: float = 0.3):
        """
        Initialize violation detector
        
        Args:
            violation_threshold: Percentage of vehicle that must be outside lane
        """
        self.violation_threshold = violation_threshold
        self.violation_history = {}  # Track violations per vehicle
    
    def get_vehicle_box_center(self, box: Tuple) -> Tuple[float, float]:
        """Get center of vehicle bounding box"""
        x1, y1, x2, y2 = box
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        return center_x, center_y
    
    def get_vehicle_bottom_center(self, box: Tuple) -> Tuple[float, float]:
        """Get bottom center of vehicle (more accurate for lane detection)"""
        x1, y1, x2, y2 = box
        center_x = (x1 + x2) / 2
        bottom_y = y2  # Bottom of vehicle
        return center_x, bottom_y
    
    def is_in_lane(self, vehicle_box: Tuple, lane_boundaries: Dict) -> bool:
        """
        Check if vehicle is within lane boundaries
        
        Args:
            vehicle_box: (x1, y1, x2, y2) vehicle bounding box
            lane_boundaries: Lane boundary information from LaneDetector
            
        Returns:
            True if vehicle is in lane, False otherwise
        """
        x_center, y_bottom = self.get_vehicle_bottom_center(vehicle_box)
        boundaries = lane_boundaries.get('boundaries', [])
        
        if not boundaries:
            return True  # No lanes detected, assume valid
        
        # Check if vehicle center is within any lane
        for boundary in boundaries:
            left = boundary.get('left', 0)
            right = boundary.get('right', float('inf'))
            
            if left <= x_center <= right:
                return True
        
        return False
    
    def calculate_violation_score(self, vehicle_box: Tuple, 
                                 lane_boundaries: Dict) -> float:
        """
        Calculate how much of vehicle is outside lane
        
        Args:
            vehicle_box: Vehicle bounding box
            lane_boundaries: Lane boundary information
            
        Returns:
            Violation score (0 = fully in lane, 1 = fully out)
        """
        x1, y1, x2, y2 = vehicle_box
        boundaries = lane_boundaries.get('boundaries', [])
        
        if not boundaries:
            return 0
        
        # Calculate how much of vehicle width is outside lanes
        vehicle_width = x2 - x1
        outside_pixels = 0
        
        for x in np.linspace(x1, x2, int(vehicle_width)):
            in_lane = False
            for boundary in boundaries:
                left = boundary.get('left', 0)
                right = boundary.get('right', float('inf'))
                
                if left <= x <= right:
                    in_lane = True
                    break
            
            if not in_lane:
                outside_pixels += 1
        
        violation_score = outside_pixels / int(vehicle_width) if vehicle_width > 0 else 0
        return min(violation_score, 1.0)
    
    def detect_violation(self, vehicle_box: Tuple, track_id: int,
                        lane_boundaries: Dict) -> Dict:
        """
        Detect if vehicle is violating lane rules
        
        Args:
            vehicle_box: Vehicle bounding box
            track_id: Vehicle tracking ID
            lane_boundaries: Lane boundary information
            
        Returns:
            Dictionary with violation information
        """
        violation_score = self.calculate_violation_score(vehicle_box, lane_boundaries)
        is_violating = violation_score > self.violation_threshold
        
        # Update violation history
        if track_id not in self.violation_history:
            self.violation_history[track_id] = {
                'consecutive_violations': 0,
                'total_violations': 0,
                'first_violation_frame': None
            }
        
        if is_violating:
            self.violation_history[track_id]['consecutive_violations'] += 1
            self.violation_history[track_id]['total_violations'] += 1
            if self.violation_history[track_id]['first_violation_frame'] is None:
                self.violation_history[track_id]['first_violation_frame'] = 0
        else:
            self.violation_history[track_id]['consecutive_violations'] = 0
        
        return {
            'track_id': track_id,
            'is_violating': is_violating,
            'violation_score': violation_score,
            'consecutive_violations': self.violation_history[track_id]['consecutive_violations'],
            'total_violations': self.violation_history[track_id]['total_violations']
        }
    
    def batch_detect_violations(self, detections: List[Dict],
                               lane_boundaries: Dict) -> List[Dict]:
        """
        Detect violations for multiple vehicles
        
        Args:
            detections: List of detection dictionaries
            lane_boundaries: Lane boundary information
            
        Returns:
            List of violation detection results
        """
        violations = []
        
        for detection in detections:
            vehicle_box = detection['box']
            track_id = detection.get('track_id', -1)
            
            violation_info = self.detect_violation(vehicle_box, track_id, lane_boundaries)
            violation_info['detection'] = detection
            violations.append(violation_info)
        
        return violations
    
    def cleanup_history(self, max_age: int = 300):
        """
        Clean up tracking history for lost vehicles
        
        Args:
            max_age: Maximum frames to keep history
        """
        to_remove = []
        for track_id, history in self.violation_history.items():
            if history['consecutive_violations'] == 0:
                to_remove.append(track_id)
        
        for track_id in to_remove:
            del self.violation_history[track_id]
