"""Logging utility module"""
import logging
from pathlib import Path
from datetime import datetime


class Logger:
    """Custom logger for the application"""
    
    _logger = None
    
    @classmethod
    def setup(cls, log_dir: str = "logs", log_file: str = None):
        """
        Setup logger configuration
        
        Args:
            log_dir: Directory to save logs
            log_file: Log filename (auto-generated if None)
        """
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        if log_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = f"lane_detection_{timestamp}.log"
        
        log_filepath = log_path / log_file
        
        # Create logger
        logger = logging.getLogger("LaneDetection")
        logger.setLevel(logging.DEBUG)
        
        # File handler
        file_handler = logging.FileHandler(log_filepath)
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        cls._logger = logger
        return logger
    
    @classmethod
    def get_logger(cls):
        """Get logger instance"""
        if cls._logger is None:
            cls.setup()
        return cls._logger
    
    @classmethod
    def info(cls, message: str):
        """Log info message"""
        cls.get_logger().info(message)
    
    @classmethod
    def debug(cls, message: str):
        """Log debug message"""
        cls.get_logger().debug(message)
    
    @classmethod
    def warning(cls, message: str):
        """Log warning message"""
        cls.get_logger().warning(message)
    
    @classmethod
    def error(cls, message: str):
        """Log error message"""
        cls.get_logger().error(message)
    
    @classmethod
    def critical(cls, message: str):
        """Log critical message"""
        cls.get_logger().critical(message)
