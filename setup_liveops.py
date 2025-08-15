#!/usr/bin/env python3

import os
import sys
import json
import logging
import argparse
from typing import Dict, Any
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("trae.setup_liveops")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="TRAE LiveOps Setup")
    parser.add_argument(
        "--config", 
        type=str, 
        default="config/liveops_config.json",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--env-file", 
        type=str, 
        default=".env",
        help="Path to environment file"
    )
    parser.add_argument(
        "--init-dirs", 
        action="store_true", 
        default=True,
        help="Initialize directories"
    )
    return parser.parse_args()


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from file.
    
    Args:
        config_path (str): Path to configuration file
        
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    try:
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                return json.load(f)
        else:
            logger.warning(f"Configuration file {config_path} not found, using defaults")
            return {}
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return {}


def create_directories(config: Dict[str, Any]):
    """Create necessary directories based on configuration.
    
    Args:
        config (Dict[str, Any]): Configuration dictionary
    """
    try:
        # Create standard directories
        dirs = [
            "logs",
            "data",
            "signals",
            "data/backups"
        ]
        
        # Add directories from config
        if "system" in config:
            if "logs_dir" in config["system"]:
                dirs.append(config["system"]["logs_dir"])
            if "data_dir" in config["system"]:
                dirs.append(config["system"]["data_dir"])
        
        # Add signal source directories
        if "signal_sources" in config and "file_drop" in config["signal_sources"]:
            if config["signal_sources"]["file_drop"].get("enabled", False):
                watch_dir = config["signal_sources"]["file_drop"].get("watch_dir", "signals")
                dirs.append(watch_dir)
                dirs.append(f"{watch_dir}/processed")
        
        # Create directories
        for directory in dirs:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Created directory: {directory}")
        
        return True
    except Exception as e:
        logger.error(f"Error creating directories: {e}")
        return False


def create_env_file(env_file: str):
    """Create environment file if it doesn't exist.
    
    Args:
        env_file (str): Path to environment file
    """
    try:
        if os.path.exists(env_file):
            logger.info(f"Environment file {env_file} already exists, skipping")
            return True
        
        # Check if example file exists
        example_file = "deployment/.env.example"
        if os.path.exists(example_file):
            # Copy example file
            with open(example_file, "r") as src, open(env_file, "w") as dst:
                dst.write(src.read())
            logger.info(f"Created environment file {env_file} from example")
        else:
            # Create basic environment file
            with open(env_file, "w") as f:
                f.write("# TRAE AI Trading Sentinel Environment Configuration\n")
                f.write("TRAE_ENV=production\n")
                f.write("TRAE_PHASE=10\n")
                f.write("TRAE_LIVEOPS=true\n")
                f.write("LOG_LEVEL=INFO\n")
            logger.info(f"Created basic environment file {env_file}")
        
        return True
    except Exception as e:
        logger.error(f"Error creating environment file: {e}")
        return False


def create_data_files():
    """Create necessary data files."""
    try:
        files = [
            ("data/trades.json", "[]\n"),
            ("data/signals.json", "[]\n"),
            ("data/accounts.json", "[]\n"),
            ("data/governance_violations.json", "[]\n")
        ]
        
        for file_path, content in files:
            # Only create if it doesn't exist
            if not os.path.exists(file_path):
                with open(file_path, "w") as f:
                    f.write(content)
                logger.info(f"Created data file: {file_path}")
        
        return True
    except Exception as e:
        logger.error(f"Error creating data files: {e}")
        return False


def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import requests
        import pandas
        import numpy
        import flask
        import dotenv
        import psutil
        import watchdog
        
        logger.info("All core dependencies are installed")
        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        logger.info("Please install required dependencies: pip install -r requirements.txt")
        return False


def check_liveops_files():
    """Check if required LiveOps files exist."""
    required_files = [
        "liveops/stealth_executor.py",
        "liveops/account_manager.py",
        "liveops/heartbeat_monitor.py",
        "liveops/webhook_handler.py",
        "liveops/signal_processor.py",
        "main.py",
        "sentinel_decider.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        logger.error(f"Missing required files: {missing_files}")
        return False
    else:
        logger.info("All required LiveOps files exist")
        return True


def main():
    """Main entry point for TRAE LiveOps Setup."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Load configuration
    config = load_config(args.config)
    
    # Log startup information
    logger.info("Starting TRAE LiveOps Setup")
    
    # Check dependencies
    if not check_dependencies():
        logger.warning("Some dependencies are missing, but continuing setup")
    
    # Check LiveOps files
    if not check_liveops_files():
        logger.error("Required LiveOps files are missing, setup cannot continue")
        return 1
    
    # Create directories
    if args.init_dirs:
        if not create_directories(config):
            logger.error("Failed to create directories")
            return 1
    
    # Create environment file
    if not create_env_file(args.env_file):
        logger.error("Failed to create environment file")
        return 1
    
    # Create data files
    if not create_data_files():
        logger.error("Failed to create data files")
        return 1
    
    # Setup complete
    logger.info("TRAE LiveOps Setup completed successfully")
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Update the .env file with your credentials")
    logger.info("2. Update the config/liveops_config.json file with your settings")
    logger.info("3. Run the system: python main.py")
    logger.info("")
    logger.info("For deployment options, see deployment/README.md")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())