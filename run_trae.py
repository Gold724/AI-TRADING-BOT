import argparse
import logging
import json
import os
from backend.trae_signal_generator import TraeSignalGenerator

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TRA.E_Runner")

def load_config(config_file):
    """Load configuration from file."""
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config file: {str(e)}")
    
    # Default config
    return {
        "polling_interval": 30,
        "api_endpoint": "http://localhost:5000/api/webhook",
        "account_id": "BX64883"
    }

def main():
    parser = argparse.ArgumentParser(description="Run TRA.E Signal Generator")
    parser.add_argument("-c", "--config", type=str, default="trae_config.json", help="Path to config file")
    parser.add_argument("-i", "--interval", type=int, help="Polling interval in seconds")
    parser.add_argument("-e", "--endpoint", type=str, help="API endpoint URL")
    parser.add_argument("-a", "--account", type=str, help="Trading account ID")
    parser.add_argument("-d", "--discord", type=str, help="Discord webhook URL")
    
    args = parser.parse_args()
    
    # Load config
    config = load_config(args.config)
    
    # Override with command line arguments
    if args.interval:
        config["polling_interval"] = args.interval
    if args.endpoint:
        config["api_endpoint"] = args.endpoint
    if args.account:
        config["account_id"] = args.account
    if args.discord:
        config["discord_webhook"] = args.discord
    
    # Initialize and run TRA.E
    logger.info(f"Starting TRA.E with config: {json.dumps(config, indent=2)}")
    trae = TraeSignalGenerator(config)
    trae.run()

if __name__ == "__main__":
    main()