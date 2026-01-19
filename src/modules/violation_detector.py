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
                        lane_boundaries: Dict, zone_manager=None, 
                        vehicle_class: str = None,
                        selected_zone_ids: List[str] = None,
                        frame_num: int = None) -> Dict:
        """
        Detect if vehicle is violating lane rules or zone restrictions
        
        Args:
            vehicle_box: Vehicle bounding box
            track_id: Vehicle tracking ID
            lane_boundaries: Lane boundary information
            zone_manager: ZoneManager instance for zone-based detection
            vehicle_class: Vehicle class name for zone checking
            selected_zone_ids: Only check these zones for violations
            
        Returns:
            Dictionary with violation information
        """
        # Check lane-based violation (disabled when using zone-based detection)
        violation_score = 0
        is_lane_violating = False
        
        # Only use lane-based detection if no zones are selected
        if not selected_zone_ids or len(selected_zone_ids) == 0:
            violation_score = self.calculate_violation_score(vehicle_box, lane_boundaries)
            is_lane_violating = violation_score > self.violation_threshold
        
        # Check zone-based violation (only in selected zones)
        is_zone_violating = False
        zone_violation_info = None
        
        if zone_manager and vehicle_class and selected_zone_ids:
            vehicle_center = self.get_vehicle_bottom_center(vehicle_box)
            zone_violation_info = zone_manager.check_violation(
                vehicle_center, vehicle_class, selected_zone_ids
            )
            is_zone_violating = zone_violation_info['is_violating']
        
        # Combined violation status
        is_violating = is_lane_violating or is_zone_violating
        
        # Update violation history (track_id may be -1 for untracked detections)
        if track_id not in self.violation_history:
            self.violation_history[track_id] = {
                'consecutive_violations': 0,
                'total_violations': 0,
                'first_violation_frame': None
            }

        if is_violating:
            self.violation_history[track_id]['consecutive_violations'] += 1
            self.violation_history[track_id]['total_violations'] += 1
            # Record the first frame where a violation was observed (for snapshot)
            if self.violation_history[track_id]['first_violation_frame'] is None:
                self.violation_history[track_id]['first_violation_frame'] = frame_num
        else:
            self.violation_history[track_id]['consecutive_violations'] = 0
        
        return {
            'track_id': track_id,
            'is_violating': is_violating,
            'lane_violation': is_lane_violating,
            'zone_violation': is_zone_violating,
            'violation_score': violation_score,
            'zone_info': zone_violation_info,
            'consecutive_violations': self.violation_history[track_id]['consecutive_violations'],
            'total_violations': self.violation_history[track_id]['total_violations']
        }
    
    def batch_detect_violations(self, detections: List[Dict],
                               lane_boundaries: Dict, zone_manager=None,
                               selected_zone_ids: List[str] = None,
                               frame_num: int = None) -> List[Dict]:
        """
        Detect violations for multiple vehicles
        
        Args:
            detections: List of detection dictionaries
            lane_boundaries: Lane boundary information
            zone_manager: ZoneManager instance for zone-based detection
            selected_zone_ids: List of zone IDs to check violations in (only these zones)
            
        Returns:
            List of violation detection results
        """
        violations = []
        
        for detection in detections:
            vehicle_box = detection['box']
            track_id = detection.get('track_id', -1)
            vehicle_class = detection.get('class_name', 'unknown')
            
            violation_info = self.detect_violation(
                vehicle_box, track_id, lane_boundaries, 
                zone_manager, vehicle_class, selected_zone_ids,
                frame_num=frame_num
            )
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
