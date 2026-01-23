"""Main detection pipeline"""
import cv2
import numpy as np
from typing import Dict, List
from pathlib import Path
from collections import OrderedDict

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
        
        # Base consecutive frames required to confirm violation at frame_skip=1
        self.confirmation_base = int(self.config.get('processing.confirmation_base', 3))

        self.violation_count = 0
        self.violation_history = {}
        # Temporal smoothing for lane boundaries to reduce jitter
        self.prev_boundaries = None
        self.boundary_alpha = float(self.config.get('processing.boundary_alpha', 0.6))

        # Store saved violation snapshots: track_id -> relative URL
        self.saved_violation_snapshots = {}

        # Small frame buffer to allow saving an earlier frame (first violation)
        # Key: frame_num -> frame (numpy array). Use OrderedDict to pop oldest.
        self.frame_buffer = OrderedDict()
        self.frame_buffer_max = int(self.config.get('processing.frame_buffer', 12))

        # Workflow flags
        # Require at least one zone to be defined before vehicle tracking/violation processing
        # This disables automatic lane detection as the primary method.
        self.require_zones = True
        # Zone presence tracking: keep recent track_ids that were in-zone
        self.zone_presence = {}  # track_id -> last_frame_seen_in_zone
        self.zone_grace_frames = int(self.config.get('tracking.zone_grace_frames', 3))
        
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
        # Store frame in ring buffer to allow saving earlier frames (e.g., first violation frame)
        try:
            # keep a shallow copy reference; avoid copying large arrays unnecessarily
            self.frame_buffer[frame_num] = frame.copy()
            # trim buffer
            while len(self.frame_buffer) > self.frame_buffer_max:
                self.frame_buffer.popitem(last=False)
        except Exception:
            pass

        # Skip frames if configured
        if frame_num % self.frame_skip != 0:
            return results
        
        # Enforce zone-first workflow
        # If zones are required, skip automatic lane detection and require zones to be present
        if self.require_zones:
            if not self.zone_manager or len(self.zone_manager.zones) == 0:
                Logger.warning("No zones configured. Create zones before running pipeline. Skipping frame processing.")
                return results

            # If user didn't specify selected zones, default to all configured zones
            if not self.selected_zone_ids:
                self.selected_zone_ids = [z.zone_id for z in self.zone_manager.zones]
                Logger.debug(f"No selected zones specified; defaulting to all zones: {self.selected_zone_ids}")

            # Do not run automatic lane detection when zones are used
            lane_boundaries = {
                'boundaries': [],
                'num_lanes': 0,
                'image_width': frame.shape[1],
                'image_height': frame.shape[0]
            }
            results['lane_boundaries'] = lane_boundaries
        else:
            # Fallback to original lane detection flow when zones are not enforced
            lane_result = self.lane_detector.detect_lanes(frame)
            lane_boundaries = self.lane_detector.get_lane_boundaries(frame)

            # Temporal smoothing of lane boundaries to reduce jitter (simple EMA)
            current_bounds = lane_boundaries.get('boundaries', [])
            if self.prev_boundaries is None or len(self.prev_boundaries) != len(current_bounds):
                # Initialize previous boundaries
                # Make a deep copy of current bounds
                self.prev_boundaries = [dict(b) for b in current_bounds]
            else:
                # Smooth each boundary element
                alpha = self.boundary_alpha
                for i in range(len(current_bounds)):
                    curr = current_bounds[i]
                    prev = self.prev_boundaries[i]
                    # Smooth numeric fields if present
                    try:
                        prev_left = float(prev.get('left', 0))
                        prev_right = float(prev.get('right', 0))
                        curr_left = float(curr.get('left', prev_left))
                        curr_right = float(curr.get('right', prev_right))
                        prev['left'] = int(round(alpha * curr_left + (1 - alpha) * prev_left))
                        prev['right'] = int(round(alpha * curr_right + (1 - alpha) * prev_right))
                        # Update center and width
                        prev['center'] = (prev['left'] + prev['right']) / 2
                        prev['width'] = prev['right'] - prev['left']
                    except Exception:
                        # If smoothing fails, fallback to current
                        self.prev_boundaries[i] = dict(curr)

            lane_boundaries['boundaries'] = self.prev_boundaries
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
                track_id = int(detection.get('track_id', -1)) if detection.get('track_id') is not None else -1

                # Check if center is inside ANY of the selected zones
                in_any_zone = False
                for zone_id in self.selected_zone_ids:
                    zone = self.zone_manager.get_zone(zone_id)
                    if zone and zone.contains_point((cx, cy)):
                        in_any_zone = True
                        # update presence
                        if track_id >= 0:
                            self.zone_presence[track_id] = frame_num
                        break

                # Allow brief exits: if we recently saw this track in the zone, keep it for a grace period
                if not in_any_zone and track_id >= 0:
                    last_seen = self.zone_presence.get(track_id)
                    if last_seen is not None and (frame_num - last_seen) <= self.zone_grace_frames:
                        in_any_zone = True

                if in_any_zone:
                    filtered_detections.append(detection)
                    Logger.debug(f"Frame {frame_num}: Vehicle {detection.get('track_id', -1)} in selected zones")
                else:
                    Logger.debug(f"Frame {frame_num}: Vehicle {detection.get('track_id', -1)} outside all selected zones")
            
            detections = filtered_detections
            Logger.debug(f"Frame {frame_num}: Filtered detections {len(detection_result['detections'])} -> {len(detections)}")
        
        results['detections'] = detections
        
        # Detect violations (both lane-based and zone-based)
        # Pass selected_zone_ids to only check violations in those zones
        if detections:
            violations = self.violation_detector.batch_detect_violations(
                detections, lane_boundaries, self.zone_manager,
                selected_zone_ids=self.selected_zone_ids,
                frame_num=frame_num
            )
            results['violations'] = violations

            # Determine dynamic confirmation threshold based on frame_skip
            # Mapping: require 3 consecutive frames at frame_skip=1 (default behavior),
            # reduce to 2 for moderate frame skips, and 1 for large skips.
            try:
                fs = int(self.frame_skip)
            except Exception:
                fs = 1

            if fs <= 0:
                confirm_required = self.confirmation_base
            elif fs <= 2:
                # For low frame skips, keep the base confirmation (3)
                confirm_required = max(1, int(self.confirmation_base))
            elif fs <= 5:
                # Moderate frame skips: reduce requirement to 2
                confirm_required = 2
            else:
                # High frame skips: single confirmation
                confirm_required = 1

            Logger.debug(f"Frame {frame_num}: confirmation threshold={confirm_required} (frame_skip={self.frame_skip})")

            # Iterate violations and handle confirmed cases
            for violation in violations:
                try:
                    is_violating = violation.get('is_violating', False)
                    consecutive = int(violation.get('consecutive_violations', 0))
                    track_id = int(violation.get('track_id', -1)) if violation.get('track_id') is not None else -1

                    # Mark whether this violation is considered "confirmed" based on consecutive frames
                    violation['is_confirmed'] = bool(is_violating and (consecutive >= confirm_required))

                    # Only count and snapshot when confirmed by consecutive frames
                    if violation.get('is_confirmed'):
                        self.violation_count += 1

                        # Save one set of snapshots per track_id (full annotated + cropped vehicle)
                        if track_id not in self.saved_violation_snapshots:
                            try:
                                out_base = Path.cwd() / 'data' / 'outputs' / 'violations'
                                subdir = self.task_id if self.task_id else 'default'
                                save_dir = out_base / subdir
                                save_dir.mkdir(parents=True, exist_ok=True)

                                # Get vehicle class name from detection
                                detection = violation.get('detection') or {}
                                class_id = int(detection.get('class_id', -1)) if detection.get('class_id') is not None else -1
                                class_name = detection.get('class_name', 'unknown')
                                
                                # Map YOLO class_id to Vietnamese vehicle names
                                # COCO classes: 2=car, 3=motorcycle, 5=bus, 7=truck
                                vehicle_type_map = {
                                    2: 'otto',      # car
                                    3: 'xemay',     # motorcycle
                                    5: 'xebuyt',    # bus
                                    7: 'xetai'      # truck
                                }
                                vehicle_type = vehicle_type_map.get(class_id, 'khac')

                                # Create annotated full-frame for snapshot (use current frame)
                                annotated = self.draw_results(frame, results)
                                filename_full = f"violation_full_track{track_id}_{vehicle_type}_frame{frame_num}.jpg"
                                out_path_full = save_dir / filename_full
                                cv2.imwrite(str(out_path_full), annotated)
                                rel_url_full = f"/api/violation-snapshot/{subdir}/{filename_full}"

                                # Determine best frame for cropping: prefer first_violation_frame if buffered
                                first_frame_idx = None
                                try:
                                    first_frame_idx = self.violation_detector.violation_history.get(int(track_id), {}).get('first_violation_frame')
                                except Exception:
                                    first_frame_idx = self.violation_detector.violation_history.get(track_id, {}).get('first_violation_frame')

                                if first_frame_idx is not None and first_frame_idx in self.frame_buffer:
                                    crop_source = self.frame_buffer[first_frame_idx]
                                    crop_frame_num = first_frame_idx
                                else:
                                    crop_source = frame
                                    crop_frame_num = frame_num

                                # Crop vehicle box from crop_source using detection bbox if available
                                box = detection.get('box') if detection else None
                                crop_url = None
                                meta_bbox = None
                                if box and isinstance(box, (list, tuple)) and len(box) >= 4:
                                    x1, y1, x2, y2 = [int(round(float(v))) for v in box[:4]]
                                    h_src, w_src = crop_source.shape[0], crop_source.shape[1]
                                    # add padding (10% of box size)
                                    bw = max(1, x2 - x1)
                                    bh = max(1, y2 - y1)
                                    pad_x = int(bw * 0.15)
                                    pad_y = int(bh * 0.15)
                                    cx1 = max(0, x1 - pad_x)
                                    cy1 = max(0, y1 - pad_y)
                                    cx2 = min(w_src - 1, x2 + pad_x)
                                    cy2 = min(h_src - 1, y2 + pad_y)

                                    try:
                                        crop = crop_source[cy1:cy2, cx1:cx2]
                                        filename_crop = f"violation_crop_track{track_id}_{vehicle_type}_frame{crop_frame_num}.jpg"
                                        out_path_crop = save_dir / filename_crop
                                        cv2.imwrite(str(out_path_crop), crop)
                                        rel_url_crop = f"/api/violation-snapshot/{subdir}/{filename_crop}"
                                        crop_url = rel_url_crop
                                        meta_bbox = [int(cx1), int(cy1), int(cx2), int(cy2)]
                                    except Exception as e:
                                        Logger.warning(f"[{self.task_id}] Failed to create crop for track {track_id}: {e}")

                                # Build snapshot metadata (include bbox and source frame info)
                                snapshot_info = {
                                    'track_id': track_id,
                                    'snapshot_full': rel_url_full,
                                    'snapshot_crop': crop_url,
                                    'bbox': meta_bbox,
                                    'image_width': int(frame.shape[1]),
                                    'image_height': int(frame.shape[0]),
                                    'first_violation_frame': first_frame_idx
                                }

                                violation['snapshot'] = snapshot_info
                                self.saved_violation_snapshots[track_id] = snapshot_info
                                Logger.info(f"Saved violation snapshots for track {track_id}: {out_path_full}")
                            except Exception as e:
                                Logger.error(f"Failed saving violation snapshot for track {track_id}: {e}")
                except Exception:
                    # Ensure violations processing does not abort pipeline
                    Logger.debug("Error processing a violation entry; continuing")

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
                                    confidence=confidence if self.draw_confidence else None,
                                    text_color='black')
                
                # Draw center point in green
                cx, cy = detection['center']
                cv2.circle(frame_copy, (int(cx), int(cy)), 3, (0, 255, 0), -1)
        
        # Draw statistics
        # Count only confirmed violations according to same dynamic threshold logic
        try:
            fs = int(self.frame_skip)
        except Exception:
            fs = 1

        if fs <= 0:
            stats_confirm_required = 3
        elif fs <= 5:
            stats_confirm_required = max(1, int(round(5.0 - (fs - 1) * (3.0 / 4.0))))
        else:
            stats_confirm_required = 1

        confirmed_violations = [v for v in violations if v['is_violating'] and v.get('consecutive_violations', 0) >= stats_confirm_required]
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
