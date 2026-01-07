"""Configuration loader module"""
import yaml
from pathlib import Path
from typing import Dict, Any


class ConfigLoader:
    """Load and manage configuration from YAML files"""
    
    def __init__(self, config_path: str = "configs/config.yaml"):
        """
        Initialize config loader
        
        Args:
            config_path: Path to YAML config file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return config
    
    def get(self, key: str, default=None) -> Any:
        """Get config value by dot notation (e.g., 'yolo.confidence_threshold')"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        
        return value
    
    def get_all(self) -> Dict[str, Any]:
        """Get entire configuration"""
        return self.config
    
    def set(self, key: str, value: Any):
        """Set config value by dot notation"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self, output_path: str = None):
        """Save configuration to YAML file"""
        save_path = Path(output_path or self.config_path)
        
        with open(save_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, default_flow_style=False)
