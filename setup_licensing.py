#!/usr/bin/env python3

import os
import sys
import json
import uuid
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("trae.setup_licensing")

# Define license tiers
LICENSE_TIERS = {
    "free": {
        "name": "Free Tier",
        "description": "Signals only, no execution",
        "features": {
            "signals": True,
            "manual_execution": False,
            "auto_execution": False,
            "stealth_mode": False,
            "ai_assisted_trading": False,
            "dreamer_mode": False,
            "multi_account": False,
            "max_accounts": 1,
            "max_signals_per_day": 10
        }
    },
    "standard": {
        "name": "Standard Tier",
        "description": "Manual execution via dashboard",
        "features": {
            "signals": True,
            "manual_execution": True,
            "auto_execution": False,
            "stealth_mode": False,
            "ai_assisted_trading": False,
            "dreamer_mode": True,
            "multi_account": True,
            "max_accounts": 2,
            "max_signals_per_day": 50
        }
    },
    "pro": {
        "name": "Pro Tier",
        "description": "Auto execution with webhooks",
        "features": {
            "signals": True,
            "manual_execution": True,
            "auto_execution": True,
            "stealth_mode": False,
            "ai_assisted_trading": False,
            "dreamer_mode": True,
            "multi_account": True,
            "max_accounts": 5,
            "max_signals_per_day": 100
        }
    },
    "elite": {
        "name": "Elite Tier",
        "description": "Stealth mode with secure AI-assisted trading",
        "features": {
            "signals": True,
            "manual_execution": True,
            "auto_execution": True,
            "stealth_mode": True,
            "ai_assisted_trading": True,
            "dreamer_mode": True,
            "multi_account": True,
            "max_accounts": -1,  # Unlimited
            "max_signals_per_day": -1  # Unlimited
        }
    }
}


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Setup licensing for TRAE AI Trading Sentinel")
    parser.add_argument("--config", type=str, default="config/liveops_config.json", help="Path to configuration file")
    parser.add_argument("--license-key", type=str, help="License key to activate")
    parser.add_argument("--generate-key", type=str, choices=["free", "standard", "pro", "elite"], help="Generate a new license key for the specified tier")
    parser.add_argument("--list-keys", action="store_true", help="List all license keys")
    parser.add_argument("--revoke-key", type=str, help="Revoke a license key")
    parser.add_argument("--force", action="store_true", help="Force operation without confirmation")
    
    return parser.parse_args()


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from file.
    
    Args:
        config_path (str): Path to configuration file
        
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        logger.info(f"Configuration loaded from {config_path}")
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return {}


def save_config(config: Dict[str, Any], config_path: str) -> bool:
    """Save configuration to file.
    
    Args:
        config (Dict[str, Any]): Configuration dictionary
        config_path (str): Path to configuration file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        logger.info(f"Configuration saved to {config_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        return False


def load_license_data(config: Dict[str, Any]) -> Dict[str, Any]:
    """Load license data from file.
    
    Args:
        config (Dict[str, Any]): Configuration dictionary
        
    Returns:
        Dict[str, Any]: License data dictionary
    """
    license_file = config.get("licensing", {}).get("license_file", "config/licenses.json")
    
    try:
        if os.path.exists(license_file):
            with open(license_file, "r") as f:
                license_data = json.load(f)
            logger.info(f"License data loaded from {license_file}")
            return license_data
        else:
            logger.info(f"License file {license_file} not found, creating new")
            return {
                "licenses": [],
                "active_license": None
            }
    except Exception as e:
        logger.error(f"Error loading license data: {e}")
        return {
            "licenses": [],
            "active_license": None
        }


def save_license_data(license_data: Dict[str, Any], config: Dict[str, Any]) -> bool:
    """Save license data to file.
    
    Args:
        license_data (Dict[str, Any]): License data dictionary
        config (Dict[str, Any]): Configuration dictionary
        
    Returns:
        bool: True if successful, False otherwise
    """
    license_file = config.get("licensing", {}).get("license_file", "config/licenses.json")
    
    try:
        os.makedirs(os.path.dirname(license_file), exist_ok=True)
        with open(license_file, "w") as f:
            json.dump(license_data, f, indent=2)
        logger.info(f"License data saved to {license_file}")
        return True
    except Exception as e:
        logger.error(f"Error saving license data: {e}")
        return False


def generate_license_key(tier: str) -> str:
    """Generate a new license key for the specified tier.
    
    Args:
        tier (str): License tier
        
    Returns:
        str: License key
    """
    # Generate a UUID-based license key with tier prefix
    license_key = f"TRAE-{tier.upper()}-{str(uuid.uuid4()).replace('-', '')}"
    return license_key


def add_license(license_data: Dict[str, Any], tier: str, license_key: str, expiry_days: int = 365) -> Dict[str, Any]:
    """Add a new license to the license data.
    
    Args:
        license_data (Dict[str, Any]): License data dictionary
        tier (str): License tier
        license_key (str): License key
        expiry_days (int, optional): Number of days until license expires. Defaults to 365.
        
    Returns:
        Dict[str, Any]: Updated license data dictionary
    """
    # Create license object
    license_obj = {
        "key": license_key,
        "tier": tier,
        "features": LICENSE_TIERS[tier]["features"],
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(days=expiry_days)).isoformat(),
        "active": True
    }
    
    # Add license to license data
    license_data["licenses"].append(license_obj)
    
    return license_data


def activate_license(license_data: Dict[str, Any], license_key: str) -> Dict[str, Any]:
    """Activate a license.
    
    Args:
        license_data (Dict[str, Any]): License data dictionary
        license_key (str): License key
        
    Returns:
        Dict[str, Any]: Updated license data dictionary
    """
    # Find license
    license_obj = None
    for lic in license_data["licenses"]:
        if lic["key"] == license_key:
            license_obj = lic
            break
    
    if not license_obj:
        logger.error(f"License key {license_key} not found")
        return license_data
    
    # Check if license is active
    if not license_obj["active"]:
        logger.error(f"License key {license_key} is not active")
        return license_data
    
    # Check if license is expired
    expires_at = datetime.fromisoformat(license_obj["expires_at"])
    if expires_at < datetime.now():
        logger.error(f"License key {license_key} is expired")
        return license_data
    
    # Set active license
    license_data["active_license"] = license_obj
    
    return license_data


def revoke_license(license_data: Dict[str, Any], license_key: str) -> Dict[str, Any]:
    """Revoke a license.
    
    Args:
        license_data (Dict[str, Any]): License data dictionary
        license_key (str): License key
        
    Returns:
        Dict[str, Any]: Updated license data dictionary
    """
    # Find license
    license_obj = None
    license_index = -1
    for i, lic in enumerate(license_data["licenses"]):
        if lic["key"] == license_key:
            license_obj = lic
            license_index = i
            break
    
    if not license_obj:
        logger.error(f"License key {license_key} not found")
        return license_data
    
    # Revoke license
    license_data["licenses"][license_index]["active"] = False
    
    # If active license is revoked, set active license to None
    if license_data["active_license"] and license_data["active_license"]["key"] == license_key:
        license_data["active_license"] = None
    
    return license_data


def update_config_for_license(config: Dict[str, Any], license_obj: Dict[str, Any]) -> Dict[str, Any]:
    """Update configuration based on license features.
    
    Args:
        config (Dict[str, Any]): Configuration dictionary
        license_obj (Dict[str, Any]): License object
        
    Returns:
        Dict[str, Any]: Updated configuration dictionary
    """
    # Ensure licensing section exists
    if "licensing" not in config:
        config["licensing"] = {}
    
    # Set license information
    config["licensing"]["tier"] = license_obj["tier"]
    config["licensing"]["features"] = license_obj["features"]
    config["licensing"]["expires_at"] = license_obj["expires_at"]
    
    # Update feature flags based on license
    features = license_obj["features"]
    
    # Update signal sources
    if "signal_sources" not in config:
        config["signal_sources"] = {}
    
    # Update webhook configuration
    if "webhook" not in config["signal_sources"]:
        config["signal_sources"]["webhook"] = {}
    
    config["signal_sources"]["webhook"]["enabled"] = features["signals"]
    
    # Update auto execution
    if "auto_execution" not in config:
        config["auto_execution"] = {}
    
    config["auto_execution"]["enabled"] = features["auto_execution"]
    
    # Update stealth mode
    if "stealth_mode" not in config:
        config["stealth_mode"] = {}
    
    config["stealth_mode"]["enabled"] = features["stealth_mode"]
    
    # Update AI assisted trading
    if "ai_assisted_trading" not in config:
        config["ai_assisted_trading"] = {}
    
    config["ai_assisted_trading"]["enabled"] = features["ai_assisted_trading"]
    
    # Update dreamer mode
    if "dreamer_mode" not in config:
        config["dreamer_mode"] = {}
    
    config["dreamer_mode"]["enabled"] = features["dreamer_mode"]
    
    # Update account limits
    if "account_limits" not in config:
        config["account_limits"] = {}
    
    config["account_limits"]["max_accounts"] = features["max_accounts"]
    
    # Update signal limits
    if "signal_limits" not in config:
        config["signal_limits"] = {}
    
    config["signal_limits"]["max_signals_per_day"] = features["max_signals_per_day"]
    
    return config


def list_licenses(license_data: Dict[str, Any]):
    """List all licenses.
    
    Args:
        license_data (Dict[str, Any]): License data dictionary
    """
    if not license_data["licenses"]:
        logger.info("No licenses found")
        return
    
    logger.info("Licenses:")
    for i, lic in enumerate(license_data["licenses"]):
        active_str = "ACTIVE" if lic["active"] else "REVOKED"
        current_str = "CURRENT" if license_data["active_license"] and license_data["active_license"]["key"] == lic["key"] else ""
        expires_at = datetime.fromisoformat(lic["expires_at"])
        expired_str = "EXPIRED" if expires_at < datetime.now() else ""
        
        logger.info(f"{i+1}. {lic['key']} - {LICENSE_TIERS[lic['tier']]['name']} - {active_str} {current_str} {expired_str}")
        logger.info(f"   Created: {lic['created_at']}")
        logger.info(f"   Expires: {lic['expires_at']}")
        logger.info(f"   Features: {', '.join([k for k, v in lic['features'].items() if v and not isinstance(v, int)])}")
        logger.info("")


def setup_licensing(config: Dict[str, Any]):
    """Setup licensing configuration.
    
    Args:
        config (Dict[str, Any]): Configuration dictionary
        
    Returns:
        Dict[str, Any]: Updated configuration dictionary
    """
    # Ensure licensing section exists
    if "licensing" not in config:
        config["licensing"] = {}
    
    # Set license file path
    if "license_file" not in config["licensing"]:
        config["licensing"]["license_file"] = "config/licenses.json"
    
    # Set default tier to free
    if "tier" not in config["licensing"]:
        config["licensing"]["tier"] = "free"
        config["licensing"]["features"] = LICENSE_TIERS["free"]["features"]
    
    return config


def main():
    """Main function."""
    args = parse_args()
    
    # Load configuration
    config = load_config(args.config)
    if not config:
        logger.error(f"Failed to load configuration from {args.config}")
        sys.exit(1)
    
    # Setup licensing configuration
    config = setup_licensing(config)
    
    # Save configuration
    if not save_config(config, args.config):
        logger.error("Failed to save configuration")
        sys.exit(1)
    
    # Load license data
    license_data = load_license_data(config)
    
    # Process command line arguments
    if args.generate_key:
        # Generate a new license key
        tier = args.generate_key
        license_key = generate_license_key(tier)
        
        # Add license to license data
        license_data = add_license(license_data, tier, license_key)
        
        # Save license data
        if not save_license_data(license_data, config):
            logger.error("Failed to save license data")
            sys.exit(1)
        
        logger.info(f"Generated new {LICENSE_TIERS[tier]['name']} license key: {license_key}")
    
    elif args.license_key:
        # Activate license
        license_data = activate_license(license_data, args.license_key)
        
        # Check if license was activated
        if not license_data["active_license"] or license_data["active_license"]["key"] != args.license_key:
            logger.error(f"Failed to activate license key {args.license_key}")
            sys.exit(1)
        
        # Update configuration for license
        config = update_config_for_license(config, license_data["active_license"])
        
        # Save configuration
        if not save_config(config, args.config):
            logger.error("Failed to save configuration")
            sys.exit(1)
        
        # Save license data
        if not save_license_data(license_data, config):
            logger.error("Failed to save license data")
            sys.exit(1)
        
        logger.info(f"Activated {LICENSE_TIERS[license_data['active_license']['tier']]['name']} license")
    
    elif args.revoke_key:
        # Revoke license
        license_data = revoke_license(license_data, args.revoke_key)
        
        # Save license data
        if not save_license_data(license_data, config):
            logger.error("Failed to save license data")
            sys.exit(1)
        
        logger.info(f"Revoked license key {args.revoke_key}")
        
        # If active license was revoked, update configuration to free tier
        if not license_data["active_license"]:
            config["licensing"]["tier"] = "free"
            config["licensing"]["features"] = LICENSE_TIERS["free"]["features"]
            
            # Save configuration
            if not save_config(config, args.config):
                logger.error("Failed to save configuration")
                sys.exit(1)
            
            logger.info("Downgraded to Free Tier")
    
    elif args.list_keys:
        # List licenses
        list_licenses(license_data)
    
    else:
        # No arguments provided, show current license status
        if license_data["active_license"]:
            tier = license_data["active_license"]["tier"]
            expires_at = datetime.fromisoformat(license_data["active_license"]["expires_at"])
            days_left = (expires_at - datetime.now()).days
            
            logger.info(f"Current license: {LICENSE_TIERS[tier]['name']}")
            logger.info(f"License key: {license_data['active_license']['key']}")
            logger.info(f"Expires: {license_data['active_license']['expires_at']} ({days_left} days left)")
            logger.info(f"Features: {', '.join([k for k, v in license_data['active_license']['features'].items() if v and not isinstance(v, int)])}")
        else:
            logger.info("No active license. Using Free Tier.")
            logger.info(f"Features: {', '.join([k for k, v in LICENSE_TIERS['free']['features'].items() if v and not isinstance(v, int)])}")
        
        # Show available commands
        logger.info("\nAvailable commands:")
        logger.info("  --generate-key [tier]  Generate a new license key")
        logger.info("  --license-key [key]    Activate a license key")
        logger.info("  --revoke-key [key]     Revoke a license key")
        logger.info("  --list-keys           List all license keys")


if __name__ == "__main__":
    main()