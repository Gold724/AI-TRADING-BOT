#!/usr/bin/env python3
"""
🔐 TradeBot Sentinel - Secure Environment Setup Script

This script helps you securely configure environment variables for cloud deployment.
It provides interactive prompts, validation, and secure credential handling.

Usage:
    python setup_environment.py
    python setup_environment.py --cloud-provider aws
    python setup_environment.py --validate-only

Author: TradeBot Sentinel Team
Version: 1.0.0
"""

import os
import sys
import json
import base64
import secrets
import argparse
import getpass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("⚠️  Warning: cryptography package not installed. Encryption features disabled.")
    print("   Install with: pip install cryptography")


class EnvironmentSetup:
    """Secure environment configuration manager."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.env_template_path = self.project_root / ".env.template"
        self.env_path = self.project_root / ".env"
        self.secrets_path = self.project_root / ".secrets"
        
        # Color codes for terminal output
        self.colors = {
            'red': '\033[91m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'purple': '\033[95m',
            'cyan': '\033[96m',
            'white': '\033[97m',
            'bold': '\033[1m',
            'end': '\033[0m'
        }
    
    def print_colored(self, message: str, color: str = 'white') -> None:
        """Print colored message to terminal."""
        print(f"{self.colors.get(color, '')}{message}{self.colors['end']}")
    
    def print_header(self, title: str) -> None:
        """Print formatted header."""
        self.print_colored("\n" + "="*60, 'cyan')
        self.print_colored(f"🔐 {title}", 'bold')
        self.print_colored("="*60, 'cyan')
    
    def validate_url(self, url: str) -> bool:
        """Validate URL format."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def validate_email(self, email: str) -> bool:
        """Basic email validation."""
        return '@' in email and '.' in email.split('@')[1]
    
    def generate_secret_key(self, length: int = 32) -> str:
        """Generate a secure random key."""
        return secrets.token_urlsafe(length)
    
    def generate_encryption_key(self) -> str:
        """Generate a Fernet encryption key."""
        if CRYPTO_AVAILABLE:
            return Fernet.generate_key().decode()
        else:
            return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
    
    def prompt_secure_input(self, prompt: str, is_password: bool = False, 
                           validator=None, default: str = None) -> str:
        """Prompt for secure input with validation."""
        while True:
            if is_password:
                value = getpass.getpass(f"{prompt}: ")
            else:
                display_prompt = f"{prompt}"
                if default:
                    display_prompt += f" [{default}]"
                display_prompt += ": "
                value = input(display_prompt).strip()
                
                if not value and default:
                    value = default
            
            if not value:
                self.print_colored("❌ This field is required!", 'red')
                continue
            
            if validator and not validator(value):
                self.print_colored("❌ Invalid format! Please try again.", 'red')
                continue
            
            return value
    
    def setup_core_settings(self) -> Dict[str, str]:
        """Setup core application settings."""
        self.print_header("Core Application Settings")
        
        settings = {}
        
        # Environment type
        env_type = input("Environment type [production/staging/development] (production): ").strip()
        settings['ENVIRONMENT'] = env_type or 'production'
        
        # Debug mode
        debug = input("Enable debug mode? [y/N]: ").strip().lower()
        settings['DEBUG'] = 'true' if debug == 'y' else 'false'
        
        # Application URLs
        if settings['ENVIRONMENT'] != 'development':
            settings['APP_URL'] = self.prompt_secure_input(
                "Application URL (e.g., https://your-domain.com)",
                validator=self.validate_url
            )
            settings['API_BASE_URL'] = self.prompt_secure_input(
                "API Base URL (e.g., https://api.your-domain.com)",
                validator=self.validate_url
            )
        
        return settings
    
    def setup_trading_credentials(self) -> Dict[str, str]:
        """Setup trading platform credentials."""
        self.print_header("Trading Platform Credentials")
        
        credentials = {}
        
        self.print_colored("🔑 Enter your Bulenox trading platform credentials:", 'yellow')
        
        credentials['BULENOX_USERNAME'] = self.prompt_secure_input("Bulenox Username")
        credentials['BULENOX_PASSWORD'] = self.prompt_secure_input("Bulenox Password", is_password=True)
        
        # Optional API key
        api_key = input("Bulenox API Key (optional): ").strip()
        if api_key:
            credentials['BULENOX_API_KEY'] = api_key
        
        # Base URL
        base_url = input("Bulenox Base URL [https://bulenox.projectx.com]: ").strip()
        credentials['BULENOX_BASE_URL'] = base_url or 'https://bulenox.projectx.com'
        
        return credentials
    
    def setup_cloud_provider(self, provider: str = None) -> Dict[str, str]:
        """Setup cloud provider credentials."""
        self.print_header("Cloud Provider Configuration")
        
        if not provider:
            self.print_colored("Select your cloud provider:", 'cyan')
            print("1. AWS (Amazon Web Services)")
            print("2. GCP (Google Cloud Platform)")
            print("3. Azure (Microsoft Azure)")
            print("4. Skip cloud provider setup")
            
            choice = input("Enter choice [1-4]: ").strip()
            provider_map = {'1': 'aws', '2': 'gcp', '3': 'azure', '4': 'skip'}
            provider = provider_map.get(choice, 'skip')
        
        if provider == 'skip':
            return {}
        
        credentials = {}
        
        if provider == 'aws':
            self.print_colored("🌩️ AWS Configuration:", 'yellow')
            credentials['AWS_ACCESS_KEY_ID'] = self.prompt_secure_input("AWS Access Key ID")
            credentials['AWS_SECRET_ACCESS_KEY'] = self.prompt_secure_input("AWS Secret Access Key", is_password=True)
            credentials['AWS_REGION'] = self.prompt_secure_input("AWS Region", default="us-east-1")
            credentials['AWS_S3_BUCKET'] = self.prompt_secure_input("S3 Bucket Name (optional)", default="")
        
        elif provider == 'gcp':
            self.print_colored("☁️ Google Cloud Configuration:", 'yellow')
            credentials['GOOGLE_CLOUD_PROJECT'] = self.prompt_secure_input("GCP Project ID")
            credentials['GOOGLE_APPLICATION_CREDENTIALS'] = self.prompt_secure_input(
                "Service Account JSON Path", default="/path/to/service-account.json"
            )
        
        elif provider == 'azure':
            self.print_colored("🔷 Azure Configuration:", 'yellow')
            credentials['AZURE_SUBSCRIPTION_ID'] = self.prompt_secure_input("Azure Subscription ID")
            credentials['AZURE_CLIENT_ID'] = self.prompt_secure_input("Azure Client ID")
            credentials['AZURE_CLIENT_SECRET'] = self.prompt_secure_input("Azure Client Secret", is_password=True)
            credentials['AZURE_TENANT_ID'] = self.prompt_secure_input("Azure Tenant ID")
        
        return credentials
    
    def setup_notifications(self) -> Dict[str, str]:
        """Setup notification services."""
        self.print_header("Notification Services")
        
        notifications = {}
        
        # Telegram
        setup_telegram = input("Setup Telegram notifications? [y/N]: ").strip().lower()
        if setup_telegram == 'y':
            self.print_colored("📱 Telegram Setup:", 'yellow')
            print("1. Message @BotFather on Telegram to create a bot")
            print("2. Message @userinfobot to get your chat ID")
            
            notifications['TELEGRAM_BOT_TOKEN'] = self.prompt_secure_input("Telegram Bot Token")
            notifications['TELEGRAM_CHAT_ID'] = self.prompt_secure_input("Telegram Chat ID")
            notifications['TELEGRAM_ENABLED'] = 'true'
        
        # Email
        setup_email = input("Setup email notifications? [y/N]: ").strip().lower()
        if setup_email == 'y':
            self.print_colored("📧 Email Setup:", 'yellow')
            notifications['EMAIL_USERNAME'] = self.prompt_secure_input(
                "Email address", validator=self.validate_email
            )
            notifications['EMAIL_PASSWORD'] = self.prompt_secure_input(
                "Email app password", is_password=True
            )
            notifications['EMAIL_FROM'] = notifications['EMAIL_USERNAME']
            notifications['EMAIL_TO'] = self.prompt_secure_input(
                "Recipient email", validator=self.validate_email
            )
            notifications['EMAIL_ENABLED'] = 'true'
        
        return notifications
    
    def setup_security(self) -> Dict[str, str]:
        """Setup security configurations."""
        self.print_header("Security Configuration")
        
        security = {}
        
        # Generate JWT secret
        self.print_colored("🔐 Generating security keys...", 'yellow')
        security['JWT_SECRET_KEY'] = self.generate_secret_key(64)
        security['JWT_ALGORITHM'] = 'HS256'
        security['JWT_EXPIRATION_HOURS'] = '24'
        
        # API key
        security['API_KEY'] = self.generate_secret_key(32)
        
        # Encryption key
        if CRYPTO_AVAILABLE:
            security['ENCRYPTION_KEY'] = self.generate_encryption_key()
            security['DATA_ENCRYPTION_ENABLED'] = 'true'
        
        self.print_colored("✅ Security keys generated successfully!", 'green')
        
        return security
    
    def write_env_file(self, config: Dict[str, str]) -> None:
        """Write configuration to .env file."""
        self.print_header("Writing Configuration")
        
        # Backup existing .env file
        if self.env_path.exists():
            backup_path = self.env_path.with_suffix('.env.backup')
            self.env_path.rename(backup_path)
            self.print_colored(f"📋 Existing .env backed up to {backup_path}", 'yellow')
        
        # Write new .env file
        with open(self.env_path, 'w') as f:
            f.write("# 🔐 TradeBot Sentinel - Environment Configuration\n")
            f.write("# Generated by setup_environment.py\n")
            f.write(f"# Created: {os.popen('date').read().strip()}\n\n")
            
            for key, value in config.items():
                f.write(f"{key}={value}\n")
        
        # Set secure permissions
        os.chmod(self.env_path, 0o600)
        
        self.print_colored(f"✅ Configuration written to {self.env_path}", 'green')
        self.print_colored("🔒 File permissions set to 600 (owner read/write only)", 'green')
    
    def validate_configuration(self) -> bool:
        """Validate the current configuration."""
        self.print_header("Configuration Validation")
        
        if not self.env_path.exists():
            self.print_colored("❌ .env file not found!", 'red')
            return False
        
        # Load and validate configuration
        config = {}
        with open(self.env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key] = value
        
        # Required fields
        required_fields = [
            'BULENOX_USERNAME', 'BULENOX_PASSWORD', 'JWT_SECRET_KEY'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in config or not config[field]:
                missing_fields.append(field)
        
        if missing_fields:
            self.print_colored(f"❌ Missing required fields: {', '.join(missing_fields)}", 'red')
            return False
        
        # Validate URLs
        url_fields = ['APP_URL', 'API_BASE_URL', 'BULENOX_BASE_URL']
        for field in url_fields:
            if field in config and config[field] and not self.validate_url(config[field]):
                self.print_colored(f"❌ Invalid URL format for {field}: {config[field]}", 'red')
                return False
        
        # Validate emails
        email_fields = ['EMAIL_USERNAME', 'EMAIL_FROM', 'EMAIL_TO']
        for field in email_fields:
            if field in config and config[field] and not self.validate_email(config[field]):
                self.print_colored(f"❌ Invalid email format for {field}: {config[field]}", 'red')
                return False
        
        self.print_colored("✅ Configuration validation passed!", 'green')
        return True
    
    def run_interactive_setup(self, cloud_provider: str = None) -> None:
        """Run the interactive setup process."""
        self.print_colored("\n🚀 Welcome to TradeBot Sentinel Environment Setup!", 'bold')
        self.print_colored("This wizard will help you configure your environment securely.\n", 'cyan')
        
        config = {}
        
        # Core settings
        config.update(self.setup_core_settings())
        
        # Trading credentials
        config.update(self.setup_trading_credentials())
        
        # Cloud provider
        config.update(self.setup_cloud_provider(cloud_provider))
        
        # Notifications
        config.update(self.setup_notifications())
        
        # Security
        config.update(self.setup_security())
        
        # Write configuration
        self.write_env_file(config)
        
        # Final validation
        if self.validate_configuration():
            self.print_colored("\n🎉 Environment setup completed successfully!", 'green')
            self.print_colored("\n📋 Next steps:", 'cyan')
            print("1. Review your .env file")
            print("2. Test your configuration with: python tradebot_sentinel.py --help")
            print("3. Deploy to your cloud provider")
            print("4. Set up monitoring and alerts")
        else:
            self.print_colored("\n❌ Setup completed with validation errors.", 'red')
            self.print_colored("Please review and fix the issues above.", 'yellow')


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="TradeBot Sentinel Environment Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--cloud-provider',
        choices=['aws', 'gcp', 'azure'],
        help='Pre-select cloud provider'
    )
    
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate existing configuration'
    )
    
    args = parser.parse_args()
    
    setup = EnvironmentSetup()
    
    if args.validate_only:
        success = setup.validate_configuration()
        sys.exit(0 if success else 1)
    else:
        setup.run_interactive_setup(args.cloud_provider)


if __name__ == '__main__':
    main()