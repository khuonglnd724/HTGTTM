"""Video processing and pipeline"""
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Dict
from src.utils.logger import Logger


class VideoProcessor:
    """Handle video input/output processing"""
    
    def __init__(self, input_source: str, output_path: str = None):
        """
        Initialize video processor
        
        Args:
            input_source: Video file path, camera index (0), or RTSP stream
            output_path: Output video file path
        """
        self.input_source = input_source
        self.output_path = output_path
        self.cap = None
        self.writer = None
        self.frame_count = 0
        self.fps = 30
        self.width = 1280
        self.height = 720
        
        self._setup_input()
    
    def _setup_input(self):
        """Setup video input"""
        # Try to open video source
        if isinstance(self.input_source, str) and (self.input_source.startswith('http') or 
                                                   self.input_source.startswith('rtsp')):
            # RTSP stream
            self.cap = cv2.VideoCapture(self.input_source)
        else:
            # Video file or camera
            try:
                source = int(self.input_source)  # Try as camera index
            except (ValueError, TypeError):
                source = str(self.input_source)  # Use as file path
            
            self.cap = cv2.VideoCapture(source)
        
        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open video source: {self.input_source}")
        
        # Get video properties
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS)) or 30
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1280
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 720
        total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
        
        Logger.info(f"Video input: {self.input_source}")
        Logger.info(f"Resolution: {self.width}x{self.height}, FPS: {self.fps}, Frames: {total_frames}")
    
    def _setup_output(self):
        """Setup video output"""
        if self.output_path is None:
            return
        
        output_dir = Path(self.output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Use MP4V codec
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.writer = cv2.VideoWriter(self.output_path, fourcc, self.fps,
                                     (self.width, self.height))
        
        if not self.writer.isOpened():
            Logger.error(f"Failed to create video writer: {self.output_path}")
            self.writer = None
        else:
            Logger.info(f"Output video: {self.output_path}")
    
    def read_frame(self) -> Optional[np.ndarray]:
        """
        Read next frame from video
        
        Returns:
            Frame array or None if video ended
        """
        if self.cap is None:
            return None
        
        ret, frame = self.cap.read()
        if ret:
            self.frame_count += 1
            return frame
        return None
    
    def write_frame(self, frame: np.ndarray):
        """
        Write frame to output video
        
        Args:
            frame: Frame to write
        """
        if self.output_path is None:
            return
        
        if self.writer is None:
            self._setup_output()
        
        if self.writer is not None and self.writer.isOpened():
            # Resize if needed
            if frame.shape[1] != self.width or frame.shape[0] != self.height:
                frame = cv2.resize(frame, (self.width, self.height))
            
            self.writer.write(frame)
    
    def release(self):
        """Release video resources"""
        if self.cap:
            self.cap.release()
        if self.writer:
            self.writer.release()
        
        Logger.info(f"Processed {self.frame_count} frames")
    
    def get_properties(self) -> Dict:
        """Get video properties"""
        return {
            'fps': self.fps,
            'width': self.width,
            'height': self.height,
            'frame_count': self.frame_count
        }
