"""Analytics and statistics module"""
import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime
from collections import defaultdict


class AnalyticsCollector:
    """Collect and analyze statistics"""
    
    def __init__(self):
        """Initialize analytics"""
        self.violations_per_vehicle = defaultdict(int)
        self.violations_per_frame = []
        self.detections_per_frame = []
        self.frames_processed = 0
        self.start_time = None
        self.end_time = None
        # Track unique detected vehicle IDs (to compute total detected vehicles)
        self.seen_vehicles = set()
        # Track confidence scores for average calculation
        self.confidence_scores = []
    
    def record_frame_data(self, frame_num: int, num_detections: int, 
                         num_violations: int):
        """
        Record data for a frame
        
        Args:
            frame_num: Frame number
            num_detections: Number of vehicles detected
            num_violations: Number of violations
        """
        self.frames_processed += 1
        self.detections_per_frame.append({
            'frame': frame_num,
            'count': num_detections
        })
        self.violations_per_frame.append({
            'frame': frame_num,
            'count': num_violations
        })
    
    def record_violation(self, track_id: int):
        """Record a violation for a vehicle"""
        self.violations_per_vehicle[track_id] += 1

    def record_detection(self, track_id: int, confidence: float = None):
        """Record that a vehicle (by track id) was detected at least once"""
        try:
            self.seen_vehicles.add(int(track_id))
        except Exception:
            self.seen_vehicles.add(track_id)
        
        # Track confidence score if provided
        if confidence is not None:
            try:
                conf_val = float(confidence)
                if 0 <= conf_val <= 1:
                    self.confidence_scores.append(conf_val)
            except (ValueError, TypeError):
                pass
    
    def start_timing(self):
        """Start timing"""
        self.start_time = datetime.now()
    
    def end_timing(self):
        """End timing"""
        self.end_time = datetime.now()
    
    def get_duration(self) -> float:
        """Get processing duration in seconds"""
        if self.start_time is None or self.end_time is None:
            return 0
        return (self.end_time - self.start_time).total_seconds()
    
    def get_statistics(self) -> Dict:
        """Get all statistics"""
        total_detections = sum(d['count'] for d in self.detections_per_frame)
        # total_violations = số lần phát hiện vi phạm (cộng theo frame)
        total_violations_frames = sum(v['count'] for v in self.violations_per_frame)
        # total detected unique vehicles
        total_detected_vehicles = len(self.seen_vehicles)
        # total vehicles that committed violations (tracked in violations_per_vehicle)
        violating_vehicles = len([v for v in self.violations_per_vehicle.values() if v > 0])
        # total_violations = số lượng xe vi phạm duy nhất
        total_violations = violating_vehicles
        # For backward-compat, set total_vehicles to total_detected_vehicles
        total_vehicles = total_detected_vehicles
        
        # Calculate average confidence
        avg_confidence = (sum(self.confidence_scores) / len(self.confidence_scores)) if self.confidence_scores else 0
        
        duration = self.get_duration()
        fps = self.frames_processed / duration if duration > 0 else 0
        
        avg_detections = total_detections / self.frames_processed if self.frames_processed > 0 else 0
        avg_violations = total_violations_frames / self.frames_processed if self.frames_processed > 0 else 0
        
        return {
            'frames_processed': self.frames_processed,
            'duration_seconds': duration,
            'fps': fps,
            'total_detections': total_detections,
            'avg_detections_per_frame': avg_detections,
            'total_violations': total_violations,
            'total_violations_frames': total_violations_frames,
            'avg_violations_per_frame': avg_violations,
            'total_vehicles': total_vehicles,
            'total_detected_vehicles': total_detected_vehicles,
            'violating_vehicles': violating_vehicles,
            'violation_rate': (violating_vehicles / total_vehicles) if total_vehicles > 0 else 0,
            'avg_confidence': avg_confidence,
            'violations_per_vehicle': dict(self.violations_per_vehicle),
            'top_violators': sorted(self.violations_per_vehicle.items(), 
                                   key=lambda x: x[1], reverse=True)[:10]
        }
    
    def save_report(self, output_path: str):
        """Save statistics report"""
        stats = self.get_statistics()
        
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
    
    def print_report(self):
        """Print statistics report"""
        stats = self.get_statistics()
        
        print("\n" + "=" * 60)
        print("LANE VIOLATION DETECTION - STATISTICS REPORT")
        print("=" * 60)
        print(f"\nProcessing Information:")
        print(f"  Frames Processed: {stats['frames_processed']}")
        print(f"  Processing Duration: {stats['duration_seconds']:.2f}s")
        print(f"  Processing Speed: {stats['fps']:.2f} FPS")
        
        print(f"\nDetection Statistics:")
        print(f"  Total Detections: {stats['total_detections']}")
        print(f"  Avg Detections/Frame: {stats['avg_detections_per_frame']:.2f}")
        print(f"  Total Vehicles: {stats['total_vehicles']}")
        
        print(f"\nViolation Statistics:")
        print(f"  Total Violations: {stats['total_violations']}")
        print(f"  Avg Violations/Frame: {stats['avg_violations_per_frame']:.2f}")
        print(f"  Violating Vehicles: {stats['violating_vehicles']}")
        print(f"  Violation Rate: {stats['violation_rate']*100:.1f}%")
        
        if stats['top_violators']:
            print(f"\nTop 10 Violators:")
            for rank, (vehicle_id, count) in enumerate(stats['top_violators'], 1):
                print(f"  {rank}. Vehicle #{vehicle_id}: {count} violations")
        
        print("\n" + "=" * 60 + "\n")
