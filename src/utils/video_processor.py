"""Video processing and pipeline"""
import cv2
import numpy as np
try:
    import imageio
except Exception:
    imageio = None
from pathlib import Path
from typing import Optional, Dict
from src.utils.logger import Logger


class VideoProcessor:
    """Handle video input/output processing"""
    
    def __init__(self, input_source: str = None, output_path: str = None):
        """
        Initialize video processor
        
        Args:
            input_source: Video file path, JPG/PNG file path, camera index (0), or RTSP stream (optional)
            output_path: Output video file path
        """
        self._input_source = input_source
        self._output_path = output_path
        self.cap = None
        self.writer = None
        self.imageio_writer = None
        self.frame_count = 0
        self.write_failures = 0  # Track consecutive write failures
        self.is_image = False  # Flag for image input
        self.fps = 30
        self.width = 1280
        self.height = 720
        
        # Only setup input if source is provided
        if self._input_source is not None:
            self._setup_input()
        
        # Setup output writer if output path provided AND input was set (need video properties)
        if self._output_path is not None and self._input_source is not None:
            self._setup_output()
    
    @property
    def output_path(self):
        """Get output path"""
        return self._output_path
    
    @output_path.setter
    def output_path(self, value):
        """Set output path and initialize writer if input is already set"""
        self._output_path = value
        # If input is already set, we can initialize the output writer now
        if value is not None and self.cap is not None:
            # Close existing writer if any
            if self.writer is not None:
                self.writer.release()
                self.writer = None
            if self.imageio_writer is not None:
                self.imageio_writer.close()
                self.imageio_writer = None
            # Setup new output
            self._setup_output()
    
    @property
    def input_source(self):
        """Get input source"""
        return self._input_source
    
    @input_source.setter
    def input_source(self, value):
        """Set input source and re-initialize video capture"""
        self._input_source = value
        # Close existing capture if any
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        # Re-setup with new source
        self._setup_input()
    
    def _setup_input(self):
        """Setup video input"""
        # Try to open video source
        if isinstance(self._input_source, str) and (self._input_source.startswith('http') or 
                                                   self._input_source.startswith('rtsp')):
            # RTSP stream
            self.cap = cv2.VideoCapture(self._input_source)
        else:
            # Video file or camera
            try:
                source = int(self._input_source)  # Try as camera index
            except (ValueError, TypeError):
                source = str(self._input_source)  # Use as file path
            
            self.cap = cv2.VideoCapture(source)
        
        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open video source: {self._input_source}")
        
        # Get video properties
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS)) or 30
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1280
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 720
        total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
        
        Logger.info(f"Video input: {self._input_source}")
        Logger.info(f"Resolution: {self.width}x{self.height}, FPS: {self.fps}, Frames: {total_frames}")
    
    def _setup_output(self):
        """Setup video output"""
        if self._output_path is None:
            return
        
        output_dir = Path(self._output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Prefer H.264 (avc1) for web playback, fallback to mp4v, then MJPG .avi
        def try_writer(path: str, fourcc_code: str):
            fourcc = cv2.VideoWriter_fourcc(*fourcc_code)
            writer = cv2.VideoWriter(path, fourcc, self.fps, (self.width, self.height))
            return writer if writer.isOpened() else None

        # Attempt avc1
        writer = try_writer(self._output_path, 'avc1')
        codec_used = 'avc1'
        
        if writer is None:
            # Fallback to mp4v
            writer = try_writer(self._output_path, 'mp4v')
            codec_used = 'mp4v'
        
        if writer is None:
            # Final fallback: MJPG in AVI container
            avi_path = str(Path(self._output_path).with_suffix('.avi'))
            writer = try_writer(avi_path, 'MJPG')
            if writer is not None:
                Logger.warning(f"Falling back to MJPG AVI output: {avi_path}")
                self._output_path = avi_path
                codec_used = 'MJPG'
        
        self.writer = writer
        if self.writer is None:
            Logger.warning(f"OpenCV writer failed; attempting imageio-ffmpeg for: {self._output_path}")
            # Fallback to imageio (requires imageio + imageio-ffmpeg)
            if imageio is not None:
                try:
                    # Ensure MP4 extension for H.264 output
                    mp4_path = str(Path(self._output_path).with_suffix('.mp4'))
                    self._output_path = mp4_path
                    Logger.info(f"Initializing imageio-ffmpeg writer with: fps={max(1, self.fps)}, size={self.width}x{self.height}, codec=libx264")
                    # Note: Don't specify pixelformat, let FFmpeg auto-select compatible format
                    self.imageio_writer = imageio.get_writer(
                        mp4_path,
                        format='ffmpeg',
                        mode='I',
                        fps=max(1, self.fps),
                        codec='libx264',
                        quality=8
                    )
                    Logger.info(f"✓ ImageIO FFmpeg writer initialized (libx264): {mp4_path}")
                    Logger.info(f"Writer object: {type(self.imageio_writer)}")
                except Exception as e:
                    self.imageio_writer = None
                    Logger.error(f"Failed to initialize imageio-ffmpeg writer: {e}")
                    raise RuntimeError(f"All video writers failed. Cannot create output video: {self._output_path}") from e
            else:
                Logger.error("imageio not available; install imageio and imageio-ffmpeg for H.264 output")
                raise RuntimeError("All video writers failed. OpenCV codecs unavailable and imageio not installed.")
        else:
            Logger.info(f"Output video initialized ({codec_used}): {self._output_path}")
    
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
            frame: Frame to write (BGR format from OpenCV)
        """
        if self._output_path is None:
            Logger.warning("Cannot write frame: output_path is None")
            return
        
        if self.writer is None and self.imageio_writer is None:
            Logger.info("No writer available, calling _setup_output()")
            self._setup_output()
        
        # Safety check - raise error if both writers still None after setup
        if self.writer is None and self.imageio_writer is None:
            raise RuntimeError("No video writer available. Cannot write frames.")
        
        # Ensure frame is numpy array and correct size
        if not isinstance(frame, np.ndarray):
            Logger.error(f"Invalid frame type: {type(frame)}")
            return
        
        if frame.shape[1] != self.width or frame.shape[0] != self.height:
            frame = cv2.resize(frame, (self.width, self.height))
        
        # OpenCV path
        if self.writer is not None and self.writer.isOpened():
            success = self.writer.write(frame)
            if not success:
                self.write_failures += 1
                Logger.error(f"Failed to write frame via OpenCV (failure #{self.write_failures})")
                
                # After 3 consecutive failures, fallback to imageio
                if self.write_failures >= 3:
                    Logger.warning(f"OpenCV writer failed {self.write_failures} times, falling back to imageio-ffmpeg")
                    self.writer.release()
                    self.writer = None
                    
                    # Try imageio fallback
                    if imageio is not None:
                        try:
                            mp4_path = str(Path(self._output_path).with_suffix('.mp4'))
                            self._output_path = mp4_path
                            Logger.info(f"Initializing imageio-ffmpeg writer with: fps={max(1, self.fps)}, size={self.width}x{self.height}, codec=libx264")
                            self.imageio_writer = imageio.get_writer(
                                mp4_path,
                                format='ffmpeg',
                                mode='I',
                                fps=max(1, self.fps),
                                codec='libx264',
                                quality=8
                            )
                            Logger.info(f"[OK] ImageIO FFmpeg writer initialized (libx264): {mp4_path}")
                            self.write_failures = 0  # Reset counter
                            
                            # Write this frame via imageio
                            if frame.dtype != np.uint8:
                                frame = np.clip(frame, 0, 255).astype(np.uint8)
                            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            self.imageio_writer.append_data(rgb)
                            self.frame_count += 1
                            return
                        except Exception as e:
                            Logger.error(f"Imageio fallback also failed: {e}")
                            raise RuntimeError(f"Both OpenCV and imageio writers failed") from e
                    else:
                        raise RuntimeError("OpenCV writer failed and imageio not available")
            else:
                self.write_failures = 0  # Reset on success
                self.frame_count += 1  # Track written frames
            return
        
        # ImageIO path - must convert BGR to RGB
        if self.imageio_writer is not None:
            try:
                if self.frame_count == 0:
                    Logger.info("Using ImageIO writer for video output")
                
                # Convert BGR (OpenCV) to RGB for imageio
                if frame.dtype != np.uint8:
                    frame = np.clip(frame, 0, 255).astype(np.uint8)
                
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.imageio_writer.append_data(rgb)
                self.frame_count += 1  # Track written frames AFTER successful write
                
                # Log every 100 frames to confirm writes are happening
                if self.frame_count % 100 == 0:
                    Logger.info(f"ImageIO writer: {self.frame_count} frames written")
            except Exception as e:
                Logger.error(f"Failed to write frame via imageio-ffmpeg (frame {self.frame_count}): {e}")
                import traceback
                Logger.error(f"Traceback: {traceback.format_exc()}")
                raise
    
    def release(self):
        """Release video resources and ensure file is completely written"""
        try:
            # Close image writer first (FFmpeg-based, needs explicit close)
            if self.imageio_writer:
                Logger.info(f"Closing ImageIO writer for: {self._output_path}")
                try:
                    self.imageio_writer.close()
                    Logger.info(f"ImageIO writer closed successfully")
                except Exception as e:
                    Logger.error(f"Error closing imageio writer: {e}")
                self.imageio_writer = None
            
            # Close OpenCV writer
            if self.writer:
                Logger.info(f"Releasing OpenCV writer")
                self.writer.release()
                self.writer = None
            
            # Close input
            if self.cap:
                Logger.info(f"Releasing video capture")
                self.cap.release()
                self.cap = None
            
            # Wait a moment to ensure disk writes complete
            import time
            time.sleep(0.5)
            
            # Verify output file exists and has size
            if self._output_path:
                output_path_obj = Path(self._output_path)
                if output_path_obj.exists():
                    file_size = output_path_obj.stat().st_size
                    Logger.info(f"[OK] Output video finalized: {self._output_path} (Size: {file_size} bytes)")
                    if file_size == 0:
                        Logger.warning(f"Warning: Output video is empty (0 bytes)!")
                else:
                    Logger.warning(f"Warning: Output video file not found: {self._output_path}")
            
            Logger.info(f"Processed {self.frame_count} frames total")
            
        except Exception as e:
            Logger.error(f"Error during release: {e}")
    
    def get_properties(self) -> Dict:
        """Get video properties"""
        return {
            'fps': self.fps,
            'width': self.width,
            'height': self.height,
            'frame_count': self.frame_count
        }
