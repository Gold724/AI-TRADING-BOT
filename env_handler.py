#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Environment Variables Handler for TradeBot Sentinel

This module handles loading, validation, and management of environment variables
for the Bulenox trading automation system.

Author: TradeBot Sentinel Team
Version: 1.0.0
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from dotenv import load_dotenv
except ImportError:
    print("Installing python-dotenv...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-dotenv"])
    from dotenv import load_dotenv

class EnvironmentHandler:
    """Handles environment variable loading and validation for TradeBot Sentinel."""
    
    def __init__(self, env_file: Optional[str] = None):
        """Initialize the environment handler.
        
        Args:
            env_file: Path to the .env file. If None, looks for .env in current directory.
        """
        self.env_file = env_file or ".env"
        self.required_vars = {
            "BULENOX_USERNAME": "Bulenox platform username",
            "BULENOX_PASSWORD": "Bulenox platform password"
        }
        self.optional_vars = {
            "AUTO_EXECUTE": ("True", "Auto-execute detected trades"),
            "SIMULATION": ("False", "Run in simulation mode"),
            "MAX_RETRIES": ("3", "Maximum retries for element selection"),
            "RETRY_DELAY": ("2000", "Delay between retries in milliseconds"),
            "PAGE_TIMEOUT": ("30000", "Page load timeout in milliseconds"),
            "HEADLESS": ("true", "Run browser in headless mode"),
            "LOG_LEVEL": ("INFO", "Logging level"),
            "SCREENSHOT_ON_ERROR": ("true", "Take screenshots on errors")
        }
        
    def load_environment(self) -> Dict[str, Any]:
        """Load environment variables from .env file and system environment.
        
        Returns:
            Dictionary containing all loaded environment variables.
            
        Raises:
            FileNotFoundError: If .env file is not found.
            ValueError: If required environment variables are missing.
        """
        # Check if .env file exists
        env_path = Path(self.env_file)
        if not env_path.exists():
            print(f"Warning: {self.env_file} not found. Please copy .env.example to .env and configure it.")
            print("Checking system environment variables...")
        else:
            # Load .env file
            load_dotenv(env_path)
            print(f"Loaded environment variables from {self.env_file}")
        
        # Validate required variables
        missing_vars = []
        for var_name, description in self.required_vars.items():
            if not os.getenv(var_name):
                missing_vars.append(f"{var_name} ({description})")
        
        if missing_vars:
            print("\n❌ Missing required environment variables:")
            for var in missing_vars:
                print(f"  - {var}")
            print("\nPlease set these variables in your .env file or system environment.")
            raise ValueError(f"Missing required environment variables: {', '.join([v.split(' ')[0] for v in missing_vars])}")
        
        # Load all variables
        env_vars = {}
        
        # Required variables
        for var_name in self.required_vars.keys():
            env_vars[var_name] = os.getenv(var_name)
        
        # Optional variables with defaults
        for var_name, (default_value, description) in self.optional_vars.items():
            value = os.getenv(var_name, default_value)
            # Convert boolean strings
            if value.lower() in ('true', 'false'):
                env_vars[var_name] = value.lower() == 'true'
            # Convert numeric strings
            elif value.isdigit():
                env_vars[var_name] = int(value)
            else:
                env_vars[var_name] = value
        
        print("\n✅ Environment variables loaded successfully:")
        print(f"  - Username: {env_vars['BULENOX_USERNAME'][:3]}***")
        print(f"  - Password: {'*' * len(env_vars['BULENOX_PASSWORD'])}")
        print(f"  - Auto Execute: {env_vars['AUTO_EXECUTE']}")
        print(f"  - Simulation Mode: {env_vars['SIMULATION']}")
        print(f"  - Headless Mode: {env_vars['HEADLESS']}")
        print(f"  - Max Retries: {env_vars['MAX_RETRIES']}")
        
        return env_vars
    
    def validate_credentials(self, username: str, password: str) -> bool:
        """Validate that credentials are not placeholder values.
        
        Args:
            username: Bulenox username
            password: Bulenox password
            
        Returns:
            True if credentials appear valid, False otherwise.
        """
        placeholder_values = [
            'your_username', 'your_username_here', 'username',
            'your_password', 'your_password_here', 'password',
            '', None
        ]
        
        if username in placeholder_values or password in placeholder_values:
            print("\n❌ Credentials appear to be placeholder values.")
            print("Please update your .env file with actual Bulenox credentials.")
            return False
        
        if len(username) < 3 or len(password) < 6:
            print("\n❌ Credentials appear to be too short.")
            print("Please verify your Bulenox credentials.")
            return False
        
        return True
    
    def create_env_file(self) -> None:
        """Create a .env file from .env.example if it doesn't exist."""
        env_path = Path(".env")
        example_path = Path(".env.example")
        
        if env_path.exists():
            print(".env file already exists.")
            return
        
        if not example_path.exists():
            print("❌ .env.example file not found. Cannot create .env file.")
            return
        
        # Copy .env.example to .env
        with open(example_path, 'r', encoding='utf-8') as src:
            content = src.read()
        
        with open(env_path, 'w', encoding='utf-8') as dst:
            dst.write(content)
        
        print("✅ Created .env file from .env.example")
        print("Please edit .env file and add your actual Bulenox credentials.")

def get_environment() -> Dict[str, Any]:
    """Convenience function to load environment variables.
    
    Returns:
        Dictionary containing all loaded environment variables.
    """
    handler = EnvironmentHandler()
    return handler.load_environment()

def main():
    """Main function for testing environment variable loading."""
    print("TradeBot Sentinel - Environment Variables Handler")
    print("=" * 50)
    
    try:
        handler = EnvironmentHandler()
        
        # Create .env file if it doesn't exist
        handler.create_env_file()
        
        # Load environment variables
        env_vars = handler.load_environment()
        
        # Validate credentials
        if handler.validate_credentials(env_vars['BULENOX_USERNAME'], env_vars['BULENOX_PASSWORD']):
            print("\n✅ All environment variables are properly configured!")
        else:
            print("\n❌ Please update your credentials in the .env file.")
            
    except Exception as e:
        print(f"\n❌ Error loading environment: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()