# run.py
# !/usr/bin/env python3
"""
LLM Firewall - Main entry point

This script runs the LLM Firewall API server with command-line options.
"""

import os
import sys
import argparse
import logging
from src.api.api import FirewallAPI


def main():
    """Main entry point for the LLM Firewall"""

    parser = argparse.ArgumentParser(description="LLM Firewall - Content safety filtering API")

    # Configuration options
    parser.add_argument(
        "--config",
        help="Path to configuration file",
        default=os.environ.get("LLM_FIREWALL_CONFIG", "config/config.json")
    )

    # Server options
    parser.add_argument(
        "--host",
        help="API server host",
        default=os.environ.get("LLM_FIREWALL_HOST", "0.0.0.0")
    )
    parser.add_argument(
        "--port",
        help="API server port",
        type=int,
        default=int(os.environ.get("LLM_FIREWALL_PORT", "5001"))
    )
    parser.add_argument(
        "--debug",
        help="Enable debug mode",
        action="store_true",
        default=os.environ.get("LLM_FIREWALL_DEBUG", "false").lower() == "true"
    )

    # Logging options
    parser.add_argument(
        "--log-level",
        help="Logging level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=os.environ.get("LLM_FIREWALL_LOG_LEVEL", "INFO")
    )
    parser.add_argument(
        "--log-file",
        help="Path to log file",
        default=os.environ.get("LLM_FIREWALL_LOG_FILE", "logs/firewall.log")
    )

    # Parse arguments
    args = parser.parse_args()

    # Configure logging
    log_dir = os.path.dirname(args.log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(args.log_file),
            logging.StreamHandler()
        ]
    )

    # Create config dict from command-line options
    config_override = {
        "api": {
            "host": args.host,
            "port": args.port,
            "debug": args.debug,
            "log_level": args.log_level
        }
    }

    # Initialize and run API
    try:
        api = FirewallAPI(args.config)
        # Apply command-line overrides
        api.config["api"].update(config_override["api"])

        logging.info(f"Starting LLM Firewall API on {args.host}:{args.port}")
        api.run()
    except Exception as e:
        logging.critical(f"Failed to start API server: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()