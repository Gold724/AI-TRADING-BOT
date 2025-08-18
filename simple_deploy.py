#!/usr/bin/env python3
"""
Simple Deployment Script for Bulenox Trading Bot
Executes deployment to Contabo VPS with minimal configuration
"""

import json
import sys
import os
import argparse
import logging
from pathlib import Path

# Configure logging with ASCII-safe format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('deployment.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def load_config(config_file):
    """Load deployment configuration from JSON file"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.info(f"Configuration loaded from {config_file}")
        return config
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_file}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in configuration file: {e}")
        return None

def validate_config(config):
    """Validate required configuration fields"""
    required_fields = [
        'vps_connection.host',
        'github_repository.url',
        'environment_variables.BULENOX_USERNAME',
        'environment_variables.BULENOX_PASSWORD'
    ]
    
    missing_fields = []
    
    for field in required_fields:
        keys = field.split('.')
        current = config
        
        try:
            for key in keys:
                current = current[key]
            
            # Check if value is placeholder
            if isinstance(current, str) and (
                current.startswith('YOUR_') or 
                current.startswith('your_') or
                current == '' or
                'placeholder' in current.lower()
            ):
                missing_fields.append(field)
                
        except (KeyError, TypeError):
            missing_fields.append(field)
    
    if missing_fields:
        logger.error(f"Missing or invalid configuration fields: {missing_fields}")
        logger.error("Please update your configuration file with actual values.")
        return False
    
    logger.info("Configuration validation passed")
    return True

def check_ssh_connection(config):
    """Test SSH connection to VPS"""
    try:
        import paramiko
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        connection_params = {
            'hostname': config['vps_connection']['host'],
            'port': config['vps_connection'].get('port', 22),
            'username': config['vps_connection']['username']
        }
        
        # Use SSH key if provided
        if 'key_file' in config['vps_connection'] and config['vps_connection']['key_file']:
            key_file = config['vps_connection']['key_file']
            if os.path.exists(key_file):
                connection_params['key_filename'] = key_file
            else:
                logger.warning(f"SSH key file not found: {key_file}")
        
        # Use password if provided
        if 'password' in config['vps_connection'] and config['vps_connection']['password']:
            connection_params['password'] = config['vps_connection']['password']
        
        logger.info(f"Testing SSH connection to {config['vps_connection']['host']}...")
        ssh.connect(**connection_params, timeout=30)
        
        # Test command execution
        stdin, stdout, stderr = ssh.exec_command('echo "SSH connection successful"')
        result = stdout.read().decode().strip()
        
        ssh.close()
        logger.info(f"SSH connection test passed: {result}")
        return True
        
    except ImportError:
        logger.error("paramiko library not installed. Run: pip install paramiko")
        return False
    except Exception as e:
        logger.error(f"SSH connection failed: {e}")
        logger.error("Please check your VPS connection settings and SSH key configuration.")
        return False

def execute_deployment_script(config, dry_run=False):
    """Execute the main deployment script"""
    try:
        # Import the main deployment module
        from deploy_to_contabo_vps import ContaboVPSDeployer
        
        deployer = ContaboVPSDeployer(config)
        
        if dry_run:
            logger.info("Executing deployment in DRY RUN mode...")
            return deployer.validate_prerequisites()
        else:
            logger.info("Executing full deployment...")
            return deployer.deploy()
            
    except ImportError as e:
        logger.error(f"Deployment module not found: {e}")
        logger.error("Make sure deploy_to_contabo_vps.py is in the current directory.")
        return False
    except Exception as e:
        logger.error(f"Deployment execution failed: {e}")
        return False

def create_sample_config():
    """Create a sample configuration file"""
    sample_config = {
        "deployment_info": {
            "project_name": "bulenox-trading-bot",
            "version": "2.0.0",
            "environment": "production"
        },
        "vps_connection": {
            "host": "YOUR_CONTABO_VPS_IP",
            "port": 22,
            "username": "root",
            "key_file": "/path/to/your/ssh/key"
        },
        "github_repository": {
            "url": "https://github.com/yourusername/ai-trading-sentinel.git",
            "branch": "main"
        },
        "environment_variables": {
            "BULENOX_USERNAME": "YOUR_BULENOX_USERNAME",
            "BULENOX_PASSWORD": "YOUR_BULENOX_PASSWORD",
            "FLASK_SECRET_KEY": "your-random-secret-key",
            "ALERT_EMAIL": "your-email@domain.com"
        }
    }
    
    config_file = "deployment_config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(sample_config, f, indent=2)
    
    logger.info(f"Sample configuration created: {config_file}")
    logger.info("Please edit this file with your actual VPS and account details.")
    return config_file

def main():
    parser = argparse.ArgumentParser(description='Deploy Bulenox Trading Bot to Contabo VPS')
    parser.add_argument('--config', default='deployment_config.json', 
                       help='Configuration file path')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Test configuration without deploying')
    parser.add_argument('--create-config', action='store_true',
                       help='Create sample configuration file')
    parser.add_argument('--test-ssh', action='store_true',
                       help='Test SSH connection only')
    
    args = parser.parse_args()
    
    # Create sample config if requested
    if args.create_config:
        create_sample_config()
        return 0
    
    # Check if config file exists
    if not os.path.exists(args.config):
        logger.error(f"Configuration file not found: {args.config}")
        logger.info("Run with --create-config to create a sample configuration file.")
        return 1
    
    # Load and validate configuration
    config = load_config(args.config)
    if not config:
        return 1
    
    if not validate_config(config):
        logger.error("Configuration validation failed. Please fix the issues above.")
        return 1
    
    # Test SSH connection if requested or before deployment
    if args.test_ssh or not args.dry_run:
        if not check_ssh_connection(config):
            logger.error("SSH connection test failed. Please fix connection issues.")
            return 1
    
    # Execute deployment
    success = execute_deployment_script(config, args.dry_run)
    
    if success:
        if args.dry_run:
            logger.info("Dry run completed successfully. Ready for deployment!")
        else:
            logger.info("Deployment completed successfully!")
            logger.info("Your Bulenox trading bot is now running on Contabo VPS.")
        return 0
    else:
        logger.error("Deployment failed. Check the logs above for details.")
        return 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info("Deployment interrupted by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)