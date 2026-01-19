"""Drawing utilities for visualization"""
import cv2
import numpy as np
from typing import List, Tuple, Dict


class DrawingUtils:
    """Utility functions for drawing on images"""
    
    # Colors in BGR format
    COLORS = {
        'red': (0, 0, 255),
        'green': (0, 255, 0),
        'blue': (255, 0, 0),
        'yellow': (0, 255, 255),
        'cyan': (255, 255, 0),
        'magenta': (255, 0, 255),
        'white': (255, 255, 255),
        'black': (0, 0, 0),
        'orange': (0, 165, 255),
        'purple': (128, 0, 128)
    }
    
    @staticmethod
    def draw_box(image: np.ndarray, box: Tuple, color: str = 'green', 
                 thickness: int = 2, label: str = None, confidence: float = None,
                 text_color: str = 'white') -> np.ndarray:
        """
        Draw bounding box on image
        
        Args:
            image: Input image
            box: (x1, y1, x2, y2) coordinates
            color: Color name from COLORS dict
            thickness: Line thickness
            label: Optional label text
            confidence: Optional confidence score
            
        Returns:
            Image with drawn box
        """
        x1, y1, x2, y2 = [int(v) for v in box]
        color_bgr = DrawingUtils.COLORS.get(color, DrawingUtils.COLORS['green'])
        
        # Draw rectangle
        cv2.rectangle(image, (x1, y1), (x2, y2), color_bgr, thickness)
        
        # Draw label if provided
        if label:
            text = label
            if confidence:
                text += f" {confidence:.2f}"
            
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            font_thickness = 1
            
            text_size = cv2.getTextSize(text, font, font_scale, font_thickness)[0]
            text_x = x1
            text_y = y1 - 5 if y1 > 20 else y2 + 20
            
            # Draw background rectangle for text
            cv2.rectangle(image, 
                        (text_x - 2, text_y - text_size[1] - 5),
                        (text_x + text_size[0] + 2, text_y + 5),
                        color_bgr, -1)
            
            # Draw text with configurable text color
            text_bgr = DrawingUtils.COLORS.get(text_color, DrawingUtils.COLORS['white'])
            cv2.putText(image, text, (text_x, text_y), font, 
                       font_scale, text_bgr, font_thickness)
        
        return image
    
    @staticmethod
    def draw_lines(image: np.ndarray, lines: List[Tuple], color: str = 'yellow',
                  thickness: int = 2) -> np.ndarray:
        """
        Draw lines on image
        
        Args:
            image: Input image
            lines: List of [(x1, y1, x2, y2), ...] coordinates
            color: Color name
            thickness: Line thickness
            
        Returns:
            Image with drawn lines
        """
        color_bgr = DrawingUtils.COLORS.get(color, DrawingUtils.COLORS['yellow'])
        
        for line in lines:
            x1, y1, x2, y2 = [int(v) for v in line]
            cv2.line(image, (x1, y1), (x2, y2), color_bgr, thickness)
        
        return image
    
    @staticmethod
    def draw_polygon(image: np.ndarray, points: List[Tuple], color: str = 'yellow',
                    thickness: int = 2, fill: bool = False, alpha: float = 0.3) -> np.ndarray:
        """
        Draw polygon on image
        
        Args:
            image: Input image
            points: List of (x, y) vertices
            color: Color name
            thickness: Line thickness
            fill: Whether to fill polygon
            alpha: Transparency for filled polygon
            
        Returns:
            Image with drawn polygon
        """
        color_bgr = DrawingUtils.COLORS.get(color, DrawingUtils.COLORS['yellow'])
        pts = np.array(points, dtype=np.int32).reshape((-1, 1, 2))
        
        if fill:
            overlay = image.copy()
            cv2.fillPoly(overlay, [pts], color_bgr)
            cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0, image)
        else:
            cv2.polylines(image, [pts], True, color_bgr, thickness)
        
        return image
    
    @staticmethod
    def draw_trajectory(image: np.ndarray, points: List[Tuple], color: str = 'blue',
                       thickness: int = 2) -> np.ndarray:
        """
        Draw trajectory as connected points
        
        Args:
            image: Input image
            points: List of (x, y) coordinates
            color: Color name
            thickness: Line thickness
            
        Returns:
            Image with drawn trajectory
        """
        color_bgr = DrawingUtils.COLORS.get(color, DrawingUtils.COLORS['blue'])
        
        for i in range(1, len(points)):
            x1, y1 = int(points[i-1][0]), int(points[i-1][1])
            x2, y2 = int(points[i][0]), int(points[i][1])
            cv2.line(image, (x1, y1), (x2, y2), color_bgr, thickness)
            cv2.circle(image, (x2, y2), 3, color_bgr, -1)
        
        return image
    
    @staticmethod
    def draw_text(image: np.ndarray, text: str, position: Tuple, 
                 color: str = 'white', font_scale: float = 0.8,
                 thickness: int = 2, bg_color: str = 'black') -> np.ndarray:
        """
        Draw text on image with background
        
        Args:
            image: Input image
            text: Text to draw
            position: (x, y) position
            color: Text color name
            font_scale: Font scale
            thickness: Text thickness
            bg_color: Background color name
            
        Returns:
            Image with drawn text
        """
        font = cv2.FONT_HERSHEY_SIMPLEX
        text_color = DrawingUtils.COLORS.get(color, DrawingUtils.COLORS['white'])
        bg_color_bgr = DrawingUtils.COLORS.get(bg_color, DrawingUtils.COLORS['black'])
        
        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
        x, y = position
        
        # Draw background
        cv2.rectangle(image, (x - 5, y - text_size[1] - 5),
                     (x + text_size[0] + 5, y + 5), bg_color_bgr, -1)
        
        # Draw text
        cv2.putText(image, text, (x, y), font, font_scale, text_color, thickness)
        
        return image
    
    @staticmethod
    def draw_alert_box(image: np.ndarray, box: Tuple, message: str = "VIOLATION",
                      thickness: int = 3) -> np.ndarray:
        """
        Draw alert/violation box
        
        Args:
            image: Input image
            box: (x1, y1, x2, y2) coordinates
            message: Alert message
            thickness: Line thickness
            
        Returns:
            Image with alert box
        """
        x1, y1, x2, y2 = [int(v) for v in box]
        
        # Draw red blinking box
        cv2.rectangle(image, (x1, y1), (x2, y2), DrawingUtils.COLORS['red'], thickness)
        
        # Draw alert text
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.8
        font_thickness = 2
        text_size = cv2.getTextSize(message, font, font_scale, font_thickness)[0]
        
        text_x = x1
        text_y = max(y1 - 10, 30)
        
        # Draw background for text
        cv2.rectangle(image, (text_x - 2, text_y - text_size[1] - 5),
                     (text_x + text_size[0] + 2, text_y + 5),
                     DrawingUtils.COLORS['red'], -1)
        
        # Draw text
        cv2.putText(image, message, (text_x, text_y), font, font_scale,
                   DrawingUtils.COLORS['white'], font_thickness)
        
        return image
