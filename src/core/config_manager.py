# config_manager.py
import os
import json
import logging
from logging.handlers import RotatingFileHandler


class ConfigManager:
    """Manager for loading and validating configuration"""

    def __init__(self, config_path=None):
        """
        Initialize the config manager

        Args:
            config_path (str, optional): Path to custom config file
        """
        self.default_config_path = "config/config.json"
        self.default_config = {
            "keyword_filter": {
                "enabled": True,
                "blacklist_file": None,
                "short_circuit": True
            },
            "guards": [
                {
                    "type": "llama_guard",
                    "enabled": True,
                    "model_name": "llama-guard3",
                    "threshold": 0.5
                },
                {
                    "type": "granite_guard",
                    "enabled": True,
                    "model_name": "granite3-guardian:8b",
                    "threshold": 0.5
                }
            ],
            "api": {
                "host": "0.0.0.0",
                "port": 5000,
                "debug": False,
                "log_level": "INFO"
            }
        }

        self.config = self.default_config.copy()

        # Load custom config if provided, otherwise use default
        config_to_load = config_path or self.default_config_path
        if os.path.exists(config_to_load):
            self.load_config(config_to_load)

        # Setup logging
        self.setup_logging()

    def load_config(self, config_path):
        """
        Load configuration from a JSON file

        Args:
            config_path (str): Path to config file
        """
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    custom_config = json.load(f)

                # Merge with default config
                self._deep_update(self.config, custom_config)
                logging.info(f"Loaded custom config from {config_path}")
            else:
                logging.warning(f"Config file {config_path} not found. Using default.")
        except Exception as e:
            logging.error(f"Error loading config: {str(e)}")

    def _deep_update(self, target, source):
        """
        Deep update the target dict with source dict

        Args:
            target (dict): Target dictionary to update
            source (dict): Source dictionary with new values
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value

    def setup_logging(self):
        """Configure logging based on settings"""
        log_level_str = self.config.get("api", {}).get("log_level", "INFO")
        log_level = getattr(logging, log_level_str, logging.INFO)

        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)

        # Configure logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                RotatingFileHandler(
                    "logs/firewall.log",
                    maxBytes=10485760,  # 10 MB
                    backupCount=5
                ),
                logging.StreamHandler()
            ]
        )

    def get_config(self):
        """Get the current configuration"""
        return self.config