"""Lane detection module"""
import cv2
import numpy as np
from typing import List, Tuple, Dict
from src.utils.logger import Logger


class LaneDetector:
    """Lane detection using image processing"""
    
    def __init__(self, canny_low: int = 50, canny_high: int = 150,
                 hough_threshold: int = 50, hough_min_length: int = 50,
                 hough_max_gap: int = 10):
        """
        Initialize lane detector
        
        Args:
            canny_low: Lower threshold for Canny edge detection
            canny_high: Upper threshold for Canny edge detection
            hough_threshold: Hough line threshold
            hough_min_length: Minimum line length
            hough_max_gap: Maximum gap in line
        """
        self.canny_low = canny_low
        self.canny_high = canny_high
        self.hough_threshold = hough_threshold
        self.hough_min_length = hough_min_length
        self.hough_max_gap = hough_max_gap
        
        Logger.info("Lane detector initialized")
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for lane detection
        
        Args:
            image: Input BGR image
            
        Returns:
            Processed image
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(blurred)
        
        return enhanced
    
    def detect_edges(self, image: np.ndarray) -> np.ndarray:
        """
        Detect edges using Canny edge detection
        
        Args:
            image: Preprocessed image
            
        Returns:
            Edge map
        """
        edges = cv2.Canny(image, self.canny_low, self.canny_high)
        return edges
    
    def region_of_interest(self, image: np.ndarray, vertices: List[Tuple] = None) -> np.ndarray:
        """
        Apply region of interest mask
        
        Args:
            image: Input image
            vertices: ROI vertices (if None, uses bottom half of image)
            
        Returns:
            Masked image
        """
        if vertices is None:
            h, w = image.shape[:2]
            vertices = [
                (0, h),
                (w / 4, h / 2),
                (3 * w / 4, h / 2),
                (w, h)
            ]
        
        mask = np.zeros_like(image)
        vertices = np.array([vertices], dtype=np.int32)
        
        if len(image.shape) == 2:
            cv2.fillPoly(mask, vertices, 255)
        else:
            cv2.fillPoly(mask, vertices, (255, 255, 255))
        
        masked = cv2.bitwise_and(image, mask)
        return masked
    
    def detect_lanes(self, image: np.ndarray) -> Dict:
        """
        Detect lanes in image
        
        Args:
            image: Input BGR image
            
        Returns:
            Dictionary with lane information
        """
        # Preprocess
        preprocessed = self.preprocess_image(image)
        
        # Detect edges
        edges = self.detect_edges(preprocessed)
        
        # Apply ROI
        roi = self.region_of_interest(edges)
        
        # Detect lines using Hough transform
        lines = cv2.HoughLinesP(roi, rho=1, theta=np.pi/180,
                               threshold=self.hough_threshold,
                               minLineLength=self.hough_min_length,
                               maxLineGap=self.hough_max_gap)
        
        lane_lines = []
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                
                # Filter nearly horizontal or vertical lines
                angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
                if 20 < abs(angle) < 160:  # Lane lines should be angled
                    lane_lines.append((x1, y1, x2, y2))
        
        return {
            'lines': lane_lines,
            'edges': edges,
            'roi_mask': roi,
            'num_lanes': len(lane_lines)
        }
    
    def group_lines(self, lines: List[Tuple], image_width: int) -> List[List[Tuple]]:
        """
        Group detected lines into lanes
        
        Args:
            lines: List of detected lines
            image_width: Width of image
            
        Returns:
            Grouped lines by lane
        """
        if not lines:
            return []
        
        # Sort lines by x coordinate
        lines_sorted = sorted(lines, key=lambda l: (l[0] + l[2]) / 2)
        
        lanes = []
        current_lane = [lines_sorted[0]]
        
        for i in range(1, len(lines_sorted)):
            line = lines_sorted[i]
            prev_line = lines_sorted[i - 1]
            
            # Calculate distance between line centers
            curr_x = (line[0] + line[2]) / 2
            prev_x = (prev_line[0] + prev_line[2]) / 2
            distance = abs(curr_x - prev_x)
            
            if distance < image_width / 8:  # Group if close
                current_lane.append(line)
            else:
                lanes.append(current_lane)
                current_lane = [line]
        
        lanes.append(current_lane)
        return lanes
    
    def get_lane_boundaries(self, image: np.ndarray) -> Dict:
        """
        Get lane boundaries for violation detection
        
        Args:
            image: Input BGR image
            
        Returns:
            Lane boundary information
        """
        h, w = image.shape[:2]
        
        detection_result = self.detect_lanes(image)
        lines = detection_result['lines']
        
        # Group lines into lanes
        lanes = self.group_lines(lines, w)
        
        # Create lane boundaries
        boundaries = []
        for lane_lines in lanes:
            if lane_lines:
                # Get leftmost and rightmost points
                all_x = []
                for x1, y1, x2, y2 in lane_lines:
                    all_x.extend([x1, x2])
                
                left_x = min(all_x)
                right_x = max(all_x)
                boundaries.append({
                    'left': left_x,
                    'right': right_x,
                    'center': (left_x + right_x) / 2,
                    'width': right_x - left_x
                })
        
        return {
            'boundaries': boundaries,
            'num_lanes': len(boundaries),
            'image_width': w,
            'image_height': h
        }
