# firewall_service.py
import os
import sys
import time
import logging
import json
import datetime
from src.licensing.license_manager import LicenseManager
from src.core.firewall import LLMFirewall
from src.api.api import FirewallAPI


class FirewallService:
    """
    Main service class that initializes and runs the firewall
    with license validation and security checks.
    """

    def __init__(self, config_path=None, license_path=None):
        """
        Initialize the firewall service.

        Args:
            config_path (str, optional): Path to the config file
            license_path (str, optional): Path to the license file
        """
        self.config_path = config_path or os.environ.get("LLM_FIREWALL_CONFIG", "config.json")
        self.license_path = license_path or os.environ.get("LLM_FIREWALL_LICENSE", "license.key")
        self.master_secret = os.environ.get("LLM_FIREWALL_SECRET", "default-master-secret")

        # Setup logging
        self._setup_logging()

        # Initialize license manager
        self.license_manager = LicenseManager(self.master_secret)

        # Validate license
        self.is_licensed, self.license_message, self.license_data = self._validate_license()

        if not self.is_licensed:
            logging.error(f"License validation failed: {self.license_message}")
            print(f"ERROR: License validation failed: {self.license_message}")
            sys.exit(1)

        # Load configuration
        self.config = self._load_config()

        # Initialize firewall
        self._init_firewall()

    def _setup_logging(self):
        """Configure logging."""
        os.makedirs("logs", exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("logs/firewall_service.log"),
                logging.StreamHandler()
            ]
        )

    def _validate_license(self):
        """
        Validate the license file.

        Returns:
            tuple: (is_valid, message, license_data)
        """
        # Try to load license from file
        license_key = self.license_manager.load_license_from_file(self.license_path)

        if not license_key:
            return False, "No license key found.", None

        # Validate the license
        return self.license_manager.validate_license(license_key)

    def _load_config(self):
        """
        Load configuration from file.

        Returns:
            dict: Configuration dictionary
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            else:
                logging.warning(f"Config file {self.config_path} not found. Using default.")
                return {}
        except Exception as e:
            logging.error(f"Error loading config: {str(e)}")
            return {}

    def _init_firewall(self):
        """Initialize the firewall API."""
        try:
            self.api = FirewallAPI(self.config_path)

            # Add license check middleware to the Flask app
            @self.api.app.before_request
            def check_license():
                # Re-validate license on each request (could be optimized with caching)
                is_valid, message, _ = self._validate_license()
                if not is_valid:
                    from flask import jsonify
                    return jsonify({
                        "error": "License validation failed",
                        "message": message
                    }), 403

        except Exception as e:
            logging.error(f"Error initializing firewall: {str(e)}")
            sys.exit(1)

    def run(self):
        """Run the firewall service."""
        try:
            # Log startup information
            logging.info(f"Starting LLM Firewall Service with license: {self.license_data['customer_id']}")
            logging.info(f"License valid until: {self.license_data['expires_at']}")

            # Start license check background thread
            self._start_license_check_thread()

            # Run the API
            api_config = self.api.config.get("api", {})
            host = api_config.get("host", "0.0.0.0")
            port = api_config.get("port", 5000)
            debug = api_config.get("debug", False)

            logging.info(f"Starting API server on {host}:{port}")
            self.api.app.run(host=host, port=port, debug=debug)

        except Exception as e:
            logging.error(f"Error running firewall service: {str(e)}")
            sys.exit(1)

    def _start_license_check_thread(self):
        """Start a background thread to periodically check license validity."""
        import threading

        def check_license_thread():
            while True:
                # Check license every hour
                time.sleep(3600)

                is_valid, message, _ = self._validate_license()
                if not is_valid:
                    logging.error(f"License check failed: {message}")
                    # Force shutdown on license expiry
                    os._exit(1)

        # Start the thread
        thread = threading.Thread(target=check_license_thread, daemon=True)
        thread.start()


# Main entry point
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="LLM Firewall Service")
    parser.add_argument("--config", help="Path to config file")
    parser.add_argument("--license", help="Path to license file")
    parser.add_argument("--secret", help="Master secret for license validation")

    args = parser.parse_args()

    # Set environment variables if provided
    if args.config:
        os.environ["LLM_FIREWALL_CONFIG"] = args.config
    if args.license:
        os.environ["LLM_FIREWALL_LICENSE"] = args.license
    if args.secret:
        os.environ["LLM_FIREWALL_SECRET"] = args.secret

    # Initialize and run service
    service = FirewallService()