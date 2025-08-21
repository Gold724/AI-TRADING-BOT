#!/usr/bin/env python3
"""
AI Trading Sentinel - Interactive Deployment Configuration
TRAE-SentinelOps Configuration Assistant

This script helps users configure their environment variables interactively
for production deployment on Contabo VPS.
"""

import os
import sys
import json
import getpass
from pathlib import Path
from typing import Dict, Optional

class DeploymentConfigurator:
    def __init__(self):
        self.env_file = Path('.env')
        self.config = {}
        self.load_current_config()
    
    def load_current_config(self):
        """Load current .env configuration"""
        if self.env_file.exists():
            with open(self.env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        self.config[key] = value
    
    def prompt_user(self, key: str, description: str, current_value: str = '', 
                   is_password: bool = False, required: bool = True) -> str:
        """Prompt user for configuration value"""
        prompt = f"\n{description}"
        if current_value and not current_value.startswith('YOUR_') and not current_value.startswith('your_'):
            prompt += f" (current: {current_value[:20]}{'...' if len(current_value) > 20 else ''})"
        prompt += f"\n{'[REQUIRED] ' if required else '[OPTIONAL] '}Enter {key}: "
        
        if is_password:
            value = getpass.getpass(prompt)
        else:
            value = input(prompt).strip()
        
        # Keep current value if user presses enter and current value exists
        if not value and current_value and not current_value.startswith('YOUR_') and not current_value.startswith('your_'):
            return current_value
        
        return value
    
    def configure_vps(self):
        """Configure VPS settings"""
        print("\n" + "="*60)
        print("🖥️  VPS CONFIGURATION (Contabo)")
        print("="*60)
        
        self.config['CONTABO_VPS_IP'] = self.prompt_user(
            'CONTABO_VPS_IP',
            'Your Contabo VPS IP address (e.g., 192.168.1.100)',
            self.config.get('CONTABO_VPS_IP', '')
        )
        
        self.config['CONTABO_VPS_USER'] = self.prompt_user(
            'CONTABO_VPS_USER',
            'VPS username (usually "root")',
            self.config.get('CONTABO_VPS_USER', 'root')
        )
        
        default_ssh_path = str(Path.home() / '.ssh' / 'contabo_key')
        self.config['CONTABO_SSH_KEY_PATH'] = self.prompt_user(
            'CONTABO_SSH_KEY_PATH',
            f'Path to your SSH private key\n(Generate with: ssh-keygen -t rsa -b 4096 -f {default_ssh_path})',
            self.config.get('CONTABO_SSH_KEY_PATH', default_ssh_path)
        )
    
    def configure_github(self):
        """Configure GitHub integration"""
        print("\n" + "="*60)
        print("🐙 GITHUB INTEGRATION")
        print("="*60)
        print("Generate token at: https://github.com/settings/tokens")
        print("Required scopes: repo, workflow, admin:repo_hook")
        
        self.config['GITHUB_TOKEN'] = self.prompt_user(
            'GITHUB_TOKEN',
            'GitHub Personal Access Token (starts with ghp_)',
            self.config.get('GITHUB_TOKEN', ''),
            is_password=True
        )
        
        self.config['GITHUB_REPO_URL'] = self.prompt_user(
            'GITHUB_REPO_URL',
            'Your GitHub repository URL',
            self.config.get('GITHUB_REPO_URL', 'https://github.com/YOUR_USERNAME/ai-trading-sentinel.git')
        )
    
    def configure_trading(self):
        """Configure trading platform"""
        print("\n" + "="*60)
        print("📈 TRADING PLATFORM (Bulenox)")
        print("="*60)
        print("Register at: https://bulenox.projectx.com/login")
        
        self.config['BULENOX_USERNAME'] = self.prompt_user(
            'BULENOX_USERNAME',
            'Your Bulenox username',
            self.config.get('BULENOX_USERNAME', '')
        )
        
        self.config['BULENOX_PASSWORD'] = self.prompt_user(
            'BULENOX_PASSWORD',
            'Your Bulenox password',
            self.config.get('BULENOX_PASSWORD', ''),
            is_password=True
        )
    
    def configure_monitoring(self):
        """Configure monitoring and alerts"""
        print("\n" + "="*60)
        print("📊 MONITORING & ALERTS")
        print("="*60)
        
        setup_slack = input("\nSetup Slack notifications? (y/n): ").lower().startswith('y')
        if setup_slack:
            print("Create webhook at: https://api.slack.com/messaging/webhooks")
            self.config['SLACK_WEBHOOK_URL'] = self.prompt_user(
                'SLACK_WEBHOOK_URL',
                'Slack webhook URL',
                self.config.get('SLACK_WEBHOOK_URL', ''),
                required=False
            )
        
        # Keep existing Flask and JWT secrets if they exist and are not placeholders
        flask_secret = self.config.get('FLASK_SECRET_KEY', '')
        if not flask_secret or len(flask_secret) < 32:
            import secrets
            self.config['FLASK_SECRET_KEY'] = secrets.token_hex(32)
            print("✅ Generated new Flask secret key")
        
        jwt_secret = self.config.get('JWT_SECRET_KEY', '')
        if not jwt_secret or len(jwt_secret) < 32:
            import secrets
            import base64
            self.config['JWT_SECRET_KEY'] = base64.b64encode(secrets.token_bytes(32)).decode()
            print("✅ Generated new JWT secret key")
    
    def save_config(self):
        """Save configuration to .env file"""
        env_content = '''# AI Trading Sentinel - Production Environment Variables
# Configured by TRAE-SentinelOps Interactive Setup
# 
# SECURITY WARNING: Keep this file secure and never commit to version control!

# =============================================================================
# VPS DEPLOYMENT CONFIGURATION
# =============================================================================
CONTABO_VPS_IP={CONTABO_VPS_IP}
CONTABO_VPS_USER={CONTABO_VPS_USER}
CONTABO_SSH_KEY_PATH={CONTABO_SSH_KEY_PATH}

# =============================================================================
# GITHUB INTEGRATION
# =============================================================================
GITHUB_TOKEN={GITHUB_TOKEN}
GITHUB_REPO_URL={GITHUB_REPO_URL}

# =============================================================================
# TRADING PLATFORM CREDENTIALS
# =============================================================================
BULENOX_USERNAME={BULENOX_USERNAME}
BULENOX_PASSWORD={BULENOX_PASSWORD}

# =============================================================================
# WEB APPLICATION SECURITY
# =============================================================================
FLASK_SECRET_KEY={FLASK_SECRET_KEY}
JWT_SECRET_KEY={JWT_SECRET_KEY}

# =============================================================================
# MONITORING AND ALERTS
# =============================================================================
SLACK_WEBHOOK_URL={SLACK_WEBHOOK_URL}

# =============================================================================
# PRODUCTION DEPLOYMENT FLAGS
# =============================================================================
FLASK_ENV=production
DEBUG=False
DATABASE_URL=sqlite:///trading_sentinel.db
LOG_LEVEL=INFO

# =============================================================================
# OPTIONAL: TRADING CONFIGURATION
# =============================================================================
TRADING_MAX_RISK_PERCENT=2.0
TRADING_STOP_LOSS_PERCENT=1.0
TRADING_TAKE_PROFIT_PERCENT=2.0
API_RATE_LIMIT=100
API_CORS_ORIGINS=http://localhost:3000,https://your-domain.com
'''.format(**{k: v for k, v in self.config.items()})
        
        with open(self.env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print(f"\n✅ Configuration saved to {self.env_file}")
    
    def test_configuration(self):
        """Test the configuration"""
        print("\n" + "="*60)
        print("🧪 TESTING CONFIGURATION")
        print("="*60)
        
        try:
            # Test SSH connection
            if self.config.get('CONTABO_VPS_IP') and self.config.get('CONTABO_SSH_KEY_PATH'):
                print("\n🔍 Testing SSH connection...")
                ssh_key_path = Path(self.config['CONTABO_SSH_KEY_PATH'])
                if ssh_key_path.exists():
                    print(f"✅ SSH key found: {ssh_key_path}")
                else:
                    print(f"❌ SSH key not found: {ssh_key_path}")
                    print(f"   Generate with: ssh-keygen -t rsa -b 4096 -f {ssh_key_path}")
            
            # Test GitHub token
            if self.config.get('GITHUB_TOKEN'):
                print("\n🔍 Testing GitHub token...")
                import requests
                headers = {'Authorization': f'token {self.config["GITHUB_TOKEN"]}'}
                response = requests.get('https://api.github.com/user', headers=headers)
                if response.status_code == 200:
                    user_data = response.json()
                    print(f"✅ GitHub token valid for user: {user_data.get('login')}")
                else:
                    print(f"❌ GitHub token invalid (status: {response.status_code})")
            
            print("\n🎯 Ready to deploy! Run: python deploy_production.py --test-only")
            
        except Exception as e:
            print(f"⚠️  Test error: {e}")
            print("   Configuration saved, but some tests failed.")
    
    def run_interactive_setup(self):
        """Run the interactive setup process"""
        print("\n" + "="*80)
        print("🚀 AI Trading Sentinel - Interactive Deployment Configuration")
        print("   TRAE-SentinelOps Setup Assistant")
        print("="*80)
        
        print("\nThis wizard will help you configure your production deployment.")
        print("Press Ctrl+C at any time to exit.")
        
        try:
            self.configure_vps()
            self.configure_github()
            self.configure_trading()
            self.configure_monitoring()
            
            print("\n" + "="*60)
            print("📝 CONFIGURATION SUMMARY")
            print("="*60)
            
            summary = {
                'VPS IP': self.config.get('CONTABO_VPS_IP', 'Not set'),
                'VPS User': self.config.get('CONTABO_VPS_USER', 'Not set'),
                'SSH Key': self.config.get('CONTABO_SSH_KEY_PATH', 'Not set'),
                'GitHub Token': '✅ Set' if self.config.get('GITHUB_TOKEN') else '❌ Not set',
                'GitHub Repo': self.config.get('GITHUB_REPO_URL', 'Not set'),
                'Bulenox User': self.config.get('BULENOX_USERNAME', 'Not set'),
                'Bulenox Pass': '✅ Set' if self.config.get('BULENOX_PASSWORD') else '❌ Not set',
                'Slack Webhook': '✅ Set' if self.config.get('SLACK_WEBHOOK_URL') else '❌ Optional',
            }
            
            for key, value in summary.items():
                print(f"{key:15}: {value}")
            
            confirm = input("\nSave this configuration? (y/n): ").lower().startswith('y')
            if confirm:
                self.save_config()
                self.test_configuration()
            else:
                print("Configuration not saved.")
                
        except KeyboardInterrupt:
            print("\n\n❌ Setup cancelled by user.")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Setup error: {e}")
            sys.exit(1)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Configure AI Trading Sentinel deployment')
    parser.add_argument('--interactive', '-i', action='store_true', 
                       help='Run interactive configuration wizard')
    parser.add_argument('--validate', '-v', action='store_true',
                       help='Validate current configuration')
    
    args = parser.parse_args()
    
    configurator = DeploymentConfigurator()
    
    if args.validate:
        configurator.test_configuration()
    elif args.interactive or len(sys.argv) == 1:
        configurator.run_interactive_setup()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()