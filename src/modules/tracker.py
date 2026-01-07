"""Vehicle tracking module"""
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TrackedObject:
    """Represents a tracked object"""
    track_id: int
    detections: List[Dict]
    timestamps: List[float]
    trajectory: List[Tuple[float, float]]
    first_seen: datetime
    last_seen: datetime
    age: int
    hits: int
    consecutive_misses: int


class SimpleTracker:
    """Simple centroid-based tracker"""
    
    def __init__(self, max_distance: float = 100, max_age: int = 30, min_hits: int = 3):
        """
        Initialize tracker
        
        Args:
            max_distance: Maximum distance for matching detections
            max_age: Maximum frames to keep lost track
            min_hits: Frames needed to confirm track
        """
        self.max_distance = max_distance
        self.max_age = max_age
        self.min_hits = min_hits
        self.next_track_id = 1
        self.tracks = {}  # Dict[int, TrackedObject]
    
    def distance(self, point1: Tuple, point2: Tuple) -> float:
        """Calculate Euclidean distance between two points"""
        return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
    
    def match_detections(self, detections: List[Dict]) -> Dict[int, Dict]:
        """
        Match detections to existing tracks
        
        Args:
            detections: List of new detections
            
        Returns:
            Dict mapping track_id to detection
        """
        matched = {}
        used_detections = set()
        
        # Try to match existing tracks
        for track_id, track in self.tracks.items():
            if track.age > self.max_age:
                continue
            
            last_center = track.trajectory[-1] if track.trajectory else None
            if last_center is None:
                continue
            
            best_match_idx = -1
            best_distance = self.max_distance
            
            for i, detection in enumerate(detections):
                if i in used_detections:
                    continue
                
                curr_center = detection['center']
                dist = self.distance(last_center, curr_center)
                
                if dist < best_distance:
                    best_distance = dist
                    best_match_idx = i
            
            if best_match_idx >= 0:
                matched[track_id] = detections[best_match_idx]
                used_detections.add(best_match_idx)
        
        return matched
    
    def update(self, detections: List[Dict], timestamp: float = None) -> Dict[int, TrackedObject]:
        """
        Update tracker with new detections
        
        Args:
            detections: List of new detections
            timestamp: Frame timestamp
            
        Returns:
            Dictionary of active tracks
        """
        if timestamp is None:
            timestamp = datetime.now().timestamp()
        
        # Match detections to existing tracks
        matched = self.match_detections(detections)
        matched_detection_indices = set()
        
        # Update matched tracks
        for track_id, detection in matched.items():
            track = self.tracks[track_id]
            track.detections.append(detection)
            track.timestamps.append(timestamp)
            track.trajectory.append(detection['center'])
            track.last_seen = datetime.now()
            track.hits += 1
            track.consecutive_misses = 0
            track.age += 1
            
            # Keep trajectory size reasonable
            if len(track.trajectory) > 100:
                track.trajectory.pop(0)
                track.detections.pop(0)
                track.timestamps.pop(0)
        
        # Create new tracks for unmatched detections
        for i, detection in enumerate(detections):
            if i not in matched_detection_indices:
                track = TrackedObject(
                    track_id=self.next_track_id,
                    detections=[detection],
                    timestamps=[timestamp],
                    trajectory=[detection['center']],
                    first_seen=datetime.now(),
                    last_seen=datetime.now(),
                    age=1,
                    hits=1,
                    consecutive_misses=0
                )
                self.tracks[self.next_track_id] = track
                self.next_track_id += 1
        
        # Mark unmatched tracks as missing
        for track_id, track in list(self.tracks.items()):
            if track_id not in matched:
                track.consecutive_misses += 1
                track.age += 1
        
        # Remove old tracks
        self.tracks = {tid: track for tid, track in self.tracks.items()
                      if track.age <= self.max_age}
        
        return self.tracks
    
    def get_active_tracks(self) -> Dict[int, TrackedObject]:
        """Get only confirmed tracks"""
        return {tid: track for tid, track in self.tracks.items()
               if track.hits >= self.min_hits and track.age <= self.max_age}
    
    def reset(self):
        """Reset tracker"""
        self.tracks = {}
        self.next_track_id = 1
