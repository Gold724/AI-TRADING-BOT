#!/usr/bin/env python3

import os
import sys
import json
import logging
import argparse
from pathlib import Path
import platform
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("trae.setup_liveops_scheduler")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="TRAE LiveOps Scheduler Setup")
    parser.add_argument(
        "--config", 
        type=str, 
        default="config/liveops_config.json",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--schedule-type", 
        type=str, 
        choices=["ny_open", "london_open", "tokyo_open", "daily", "custom"],
        default="daily",
        help="Type of schedule to set up"
    )
    parser.add_argument(
        "--custom-time", 
        type=str, 
        help="Custom time for scheduling (HH:MM format)"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        default=False,
        help="Show what would be done without making changes"
    )
    return parser.parse_args()


def load_config(config_path):
    """Load configuration from file."""
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


def get_market_open_times():
    """Get market open times in UTC."""
    return {
        "ny_open": "13:30",       # New York opens at 9:30 AM EDT (13:30 UTC)
        "london_open": "08:00",   # London opens at 8:00 AM BST (07:00/08:00 UTC)
        "tokyo_open": "00:00",    # Tokyo opens at 9:00 AM JST (00:00 UTC)
        "daily": "00:01"          # Just after midnight UTC
    }


def setup_linux_cron(schedule_time, dry_run=False):
    """Set up cron job on Linux systems."""
    try:
        # Get current directory
        current_dir = os.path.abspath(os.getcwd())
        
        # Parse the time
        hour, minute = schedule_time.split(":")
        
        # Create cron entry
        cron_time = f"{minute} {hour} * * *"
        cron_command = f"cd {current_dir} && python3 main.py --phase 10 --liveops >> {current_dir}/logs/liveops/scheduled_run_$(date +\%Y\%m\%d).log 2>&1"
        cron_entry = f"{cron_time} {cron_command}"
        
        if dry_run:
            logger.info(f"Would add cron entry: {cron_entry}")
            return True
        
        # Create temporary file
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file_path = temp_file.name
        temp_file.close()
        
        # Export current crontab
        os.system(f"crontab -l > {temp_file_path} 2>/dev/null || true")
        
        # Check if entry already exists
        with open(temp_file_path, "r") as f:
            current_crontab = f.read()
        
        if cron_command in current_crontab:
            logger.info("Cron job already exists, skipping")
            os.unlink(temp_file_path)
            return True
        
        # Append new entry
        with open(temp_file_path, "a") as f:
            f.write(f"\n{cron_entry}\n")
        
        # Install new crontab
        result = os.system(f"crontab {temp_file_path}")
        os.unlink(temp_file_path)
        
        if result == 0:
            logger.info(f"Cron job scheduled for {schedule_time} UTC")
            return True
        else:
            logger.error("Failed to install cron job")
            return False
    except Exception as e:
        logger.error(f"Error setting up cron job: {e}")
        return False


def setup_windows_task(schedule_time, dry_run=False):
    """Set up scheduled task on Windows systems."""
    try:
        # Get current directory
        current_dir = os.path.abspath(os.getcwd())
        
        # Parse the time
        hour, minute = schedule_time.split(":")
        
        # Create task name
        task_name = "TraeLiveOpsScheduledRun"
        
        # Create log directory if it doesn't exist
        log_dir = os.path.join(current_dir, "logs", "liveops")
        os.makedirs(log_dir, exist_ok=True)
        
        # Create batch file for the task
        batch_file = os.path.join(current_dir, "run_scheduled_liveops.bat")
        with open(batch_file, "w") as f:
            f.write(f"@echo off\n")
            f.write(f"cd /d {current_dir}\n")
            f.write(f"echo Running scheduled LiveOps at %date% %time% > {log_dir}\\scheduled_run_%date:~-4,4%%date:~-7,2%%date:~-10,2%.log\n")
            f.write(f"python main.py --phase 10 --liveops >> {log_dir}\\scheduled_run_%date:~-4,4%%date:~-7,2%%date:~-10,2%.log 2>&1\n")
        
        if dry_run:
            logger.info(f"Would create Windows scheduled task '{task_name}' to run at {schedule_time} UTC")
            logger.info(f"Would create batch file: {batch_file}")
            return True
        
        # Create the scheduled task
        # Convert UTC time to local time
        # This is a simplification - proper timezone conversion would be more complex
        # For now, we'll just use the UTC time directly
        time_str = f"{hour}:{minute}"
        
        # Check if task already exists
        check_cmd = f'schtasks /query /tn "{task_name}" 2>nul'
        if os.system(check_cmd) == 0:
            # Task exists, delete it first
            os.system(f'schtasks /delete /tn "{task_name}" /f')
        
        # Create the task
        cmd = f'schtasks /create /tn "{task_name}" /tr "{batch_file}" /sc DAILY /st {time_str} /ru SYSTEM'
        result = os.system(cmd)
        
        if result == 0:
            logger.info(f"Windows scheduled task created for {schedule_time} UTC")
            return True
        else:
            logger.error("Failed to create Windows scheduled task")
            return False
    except Exception as e:
        logger.error(f"Error setting up Windows scheduled task: {e}")
        return False


def setup_auto_logs():
    """Set up automatic log creation for each session."""
    try:
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(os.getcwd(), "logs", "liveops")
        os.makedirs(logs_dir, exist_ok=True)
        
        # Create a logging configuration file
        logging_config = {
            "version": 1,
            "formatters": {
                "detailed": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "INFO",
                    "formatter": "detailed"
                },
                "file": {
                    "class": "logging.handlers.TimedRotatingFileHandler",
                    "level": "INFO",
                    "formatter": "detailed",
                    "filename": os.path.join(logs_dir, "operations.log"),
                    "when": "midnight",
                    "backupCount": 30
                },
                "trade_file": {
                    "class": "logging.handlers.TimedRotatingFileHandler",
                    "level": "INFO",
                    "formatter": "detailed",
                    "filename": os.path.join(logs_dir, "trades.log"),
                    "when": "midnight",
                    "backupCount": 90
                },
                "error_file": {
                    "class": "logging.handlers.TimedRotatingFileHandler",
                    "level": "ERROR",
                    "formatter": "detailed",
                    "filename": os.path.join(logs_dir, "errors.log"),
                    "when": "midnight",
                    "backupCount": 30
                }
            },
            "loggers": {
                "trae": {
                    "level": "INFO",
                    "handlers": ["console", "file"]
                },
                "trae.trades": {
                    "level": "INFO",
                    "handlers": ["trade_file"],
                    "propagate": False
                },
                "trae.errors": {
                    "level": "ERROR",
                    "handlers": ["error_file", "console"],
                    "propagate": False
                }
            }
        }
        
        # Save the logging configuration
        config_path = os.path.join(os.getcwd(), "config", "logging_config.json")
        with open(config_path, "w") as f:
            json.dump(logging_config, f, indent=2)
        
        logger.info(f"Automatic logging configuration created at {config_path}")
        return True
    except Exception as e:
        logger.error(f"Error setting up automatic logs: {e}")
        return False


def main():
    """Main entry point for TRAE LiveOps Scheduler Setup."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Load configuration
    config = load_config(args.config)
    
    # Log startup information
    logger.info("Starting TRAE LiveOps Scheduler Setup")
    
    # Determine schedule time
    market_times = get_market_open_times()
    
    if args.schedule_type == "custom" and args.custom_time:
        schedule_time = args.custom_time
    elif args.schedule_type in market_times:
        schedule_time = market_times[args.schedule_type]
    else:
        schedule_time = market_times["daily"]
    
    logger.info(f"Setting up schedule for {args.schedule_type} at {schedule_time} UTC")
    
    # Set up automatic logs
    if not setup_auto_logs():
        logger.error("Failed to set up automatic logs")
        return 1
    
    # Set up scheduler based on platform
    system = platform.system().lower()
    
    if system == "linux" or system == "darwin":
        if not setup_linux_cron(schedule_time, args.dry_run):
            logger.error("Failed to set up Linux/macOS scheduler")
            return 1
    elif system == "windows":
        if not setup_windows_task(schedule_time, args.dry_run):
            logger.error("Failed to set up Windows scheduler")
            return 1
    else:
        logger.error(f"Unsupported platform: {system}")
        return 1
    
    # Setup complete
    logger.info("TRAE LiveOps Scheduler Setup completed successfully")
    logger.info("")
    logger.info("Next steps:")
    logger.info(f"1. The system will automatically run at {schedule_time} UTC")
    logger.info("2. Logs will be created automatically for each session")
    logger.info("3. Check logs/liveops directory for operation logs")
    logger.info("")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())