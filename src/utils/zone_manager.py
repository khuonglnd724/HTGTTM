"""Zone management for lane violation detection"""
import json
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from src.utils.logger import Logger


class Zone:
    """Represents a detection zone with vehicle class restrictions"""
    
    def __init__(self, zone_id: str, name: str, polygon: List[Tuple[int, int]], 
                 allowed_classes: List[str], color: Tuple[int, int, int] = (0, 255, 0),
                 base_width: Optional[int] = None, base_height: Optional[int] = None):
        """
        Initialize zone
        
        Args:
            zone_id: Unique zone identifier
            name: Zone name
            polygon: List of (x, y) points defining the zone
            allowed_classes: List of allowed vehicle classes (e.g., ['car', 'motorcycle'])
            color: Zone color for visualization (B, G, R)
            base_width: Original canvas width used when creating the zone (for rescaling)
            base_height: Original canvas height used when creating the zone (for rescaling)
        """
        self.zone_id = zone_id
        self.name = name
        self.polygon = polygon
        self.allowed_classes = allowed_classes
        self.color = color
        self.base_width = base_width
        self.base_height = base_height
        
        # Cache numpy array for faster contains_point checks
        self._polygon_array = np.array(self.polygon, dtype=np.int32)
        
        # Precompute bounding box for fast rejection
        if polygon:
            points = np.array(polygon)
            self._bbox_min = points.min(axis=0)
            self._bbox_max = points.max(axis=0)
        else:
            self._bbox_min = np.array([0, 0])
            self._bbox_max = np.array([0, 0])
    
    def contains_point(self, point: Tuple[float, float]) -> bool:
        """Check if point is inside zone polygon with fast rejection"""
        x, y = point
        
        # Fast bounding box rejection test
        if x < self._bbox_min[0] or x > self._bbox_max[0] or \
           y < self._bbox_min[1] or y > self._bbox_max[1]:
            return False
        
        # Use cached numpy array for polygon test
        return cv2.pointPolygonTest(self._polygon_array, (float(x), float(y)), False) >= 0
    
    def is_vehicle_allowed(self, vehicle_class: str) -> bool:
        """Check if vehicle class is allowed in this zone"""
        return vehicle_class in self.allowed_classes
    
    def update_cache(self):
        """Update cached polygon array and bounding box after polygon changes"""
        self._polygon_array = np.array(self.polygon, dtype=np.int32)
        if self.polygon:
            points = np.array(self.polygon)
            self._bbox_min = points.min(axis=0)
            self._bbox_max = points.max(axis=0)
        else:
            self._bbox_min = np.array([0, 0])
            self._bbox_max = np.array([0, 0])

    def to_dict(self) -> Dict:
        """Convert zone to dictionary"""
        return {
            'zone_id': self.zone_id,
            'name': self.name,
            'polygon': self.polygon,
            'allowed_classes': self.allowed_classes,
            'color': list(self.color),
            'base_width': self.base_width,
            'base_height': self.base_height
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Zone':
        """Create zone from dictionary"""
        # Handle polygon format: can be list of tuples or list of {x,y} dicts
        polygon = data['polygon']
        if polygon and isinstance(polygon[0], dict):
            # Convert {x, y} format to (x, y) tuples
            polygon = [(int(p.get('x', 0)), int(p.get('y', 0))) for p in polygon]
        else:
            # Already in tuple format
            polygon = [tuple(p) for p in polygon]
        
        return cls(
            zone_id=data['zone_id'],
            name=data['name'],
            polygon=polygon,
            allowed_classes=data['allowed_classes'],
            color=tuple(data.get('color', [0, 255, 0])),
            base_width=data.get('base_width'),
            base_height=data.get('base_height')
        )


class ZoneManager:
    """Manage detection zones"""
    
    def __init__(self, config_path: str = "configs/zones.json"):
        """
        Initialize zone manager
        
        Args:
            config_path: Path to zone configuration file
        """
        self.config_path = Path(config_path)
        self.zones: List[Zone] = []
        self.load_zones()
    
    def add_zone(self, zone: Zone):
        """Add a new zone"""
        # Check for duplicate zone_id
        if any(z.zone_id == zone.zone_id for z in self.zones):
            Logger.warning(f"Zone {zone.zone_id} already exists, replacing")
            self.zones = [z for z in self.zones if z.zone_id != zone.zone_id]
        
        self.zones.append(zone)
        Logger.info(f"Added zone: {zone.name} ({zone.zone_id})")
    
    def remove_zone(self, zone_id: str) -> bool:
        """Remove zone by ID"""
        initial_count = len(self.zones)
        self.zones = [z for z in self.zones if z.zone_id != zone_id]
        removed = len(self.zones) < initial_count
        
        if removed:
            Logger.info(f"Removed zone: {zone_id}")
        
        return removed
    
    def get_zone(self, zone_id: str) -> Optional[Zone]:
        """Get zone by ID"""
        for zone in self.zones:
            if zone.zone_id == zone_id:
                return zone
        return None
    
    def get_zones_at_point(self, point: Tuple[float, float]) -> List[Zone]:
        """Get all zones containing the point"""
        return [zone for zone in self.zones if zone.contains_point(point)]
    
    def check_violation(self, vehicle_center: Tuple[float, float], 
                       vehicle_class: str,
                       selected_zone_ids: List[str] = None) -> Dict:
        """
        Check if vehicle violates zone restrictions
        
        Args:
            vehicle_center: (x, y) center point of vehicle
            vehicle_class: Vehicle class name
            selected_zone_ids: Only check violations in these zones
            
        Returns:
            Dictionary with violation information
        """
        zones_at_point = self.get_zones_at_point(vehicle_center)
        
        # Filter to only selected zones if specified
        if selected_zone_ids:
            zones_at_point = [z for z in zones_at_point if z.zone_id in selected_zone_ids]
        
        if not zones_at_point:
            # Not in any selected zone - no violation
            return {
                'is_violating': False,
                'violation_type': None,
                'zones': []
            }
        
        # Check if vehicle is allowed in all zones it occupies
        violating_zones = []
        for zone in zones_at_point:
            if not zone.is_vehicle_allowed(vehicle_class):
                violating_zones.append({
                    'zone_id': zone.zone_id,
                    'zone_name': zone.name,
                    'allowed_classes': zone.allowed_classes,
                    'vehicle_class': vehicle_class
                })
        
        return {
            'is_violating': len(violating_zones) > 0,
            'violation_type': 'wrong_lane_zone' if violating_zones else None,
            'zones': violating_zones,
            'total_zones': len(zones_at_point)
        }
    
    def draw_zones(self, frame: np.ndarray, alpha: float = 0.3) -> np.ndarray:
        """
        Draw zones on frame with transparency
        
        Args:
            frame: Input frame
            alpha: Transparency (0=transparent, 1=opaque)
            
        Returns:
            Frame with zones drawn
        """
        overlay = frame.copy()
        
        for zone in self.zones:
            # Draw filled polygon
            pts = np.array(zone.polygon, dtype=np.int32)
            cv2.fillPoly(overlay, [pts], zone.color)
            
            # Draw border
            cv2.polylines(frame, [pts], True, zone.color, 2)
            
            # Draw zone name
            if len(zone.polygon) > 0:
                centroid_x = int(np.mean([p[0] for p in zone.polygon]))
                centroid_y = int(np.mean([p[1] for p in zone.polygon]))
                
                # Background for text
                text = f"{zone.name}"
                (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                cv2.rectangle(frame, (centroid_x - 5, centroid_y - th - 5),
                            (centroid_x + tw + 5, centroid_y + 5), (0, 0, 0), -1)
                cv2.putText(frame, text, (centroid_x, centroid_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Blend overlay with original
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
        
        return frame
    
    def save_zones(self):
        """Save zones to configuration file"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'zones': [zone.to_dict() for zone in self.zones],
            'version': '1.0'
        }
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        Logger.info(f"Saved {len(self.zones)} zones to {self.config_path}")
    
    def load_zones(self):
        """Load zones from configuration file"""
        if not self.config_path.exists():
            Logger.info(f"No zone config found at {self.config_path}, starting with empty zones")
            return
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.zones = [Zone.from_dict(z) for z in data.get('zones', [])]
            Logger.info(f"Loaded {len(self.zones)} zones from {self.config_path}")
        
        except Exception as e:
            Logger.error(f"Error loading zones: {str(e)}")
            self.zones = []

    def rescale_to(self, target_width: int, target_height: int):
        """Rescale all zones from their base size to the target frame size.
        If base size is missing, zones are assumed to already be in target scale.
        """
        if target_width <= 0 or target_height <= 0:
            Logger.warning("Invalid target size for rescaling zones")
            return
        
        for zone in self.zones:
            if zone.base_width and zone.base_height and zone.base_width > 0 and zone.base_height > 0:
                sx = float(target_width) / float(zone.base_width)
                sy = float(target_height) / float(zone.base_height)
                zone.polygon = [
                    (int(round(p[0] * sx)), int(round(p[1] * sy))) for p in zone.polygon
                ]
                # Update cached arrays after rescaling
                zone.update_cache()
                Logger.info(f"Rescaled zone {zone.zone_id} '{zone.name}' by factors sx={sx:.3f}, sy={sy:.3f}")
            else:
                # No base size; assume already correct scale
                Logger.debug(f"Zone {zone.zone_id} has no base size; skipping rescale")
    
    def clear_zones(self):
        """Clear all zones"""
        self.zones = []
        Logger.info("Cleared all zones")
    
    def get_all_zones(self) -> List[Dict]:
        """Get all zones as dictionaries"""
        return [zone.to_dict() for zone in self.zones]
