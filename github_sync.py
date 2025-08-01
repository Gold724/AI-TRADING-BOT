#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GitHub Sync for AI Trading Sentinel

This script provides synchronization between the local AI Trading Sentinel
instance and the GitHub repository. It can be used to:
- Check for updates
- Pull updates
- Push local changes
- Sync trading results
- Create issues for errors or bugs

It integrates with the heartbeat system to provide status updates.
"""

import os
import sys
import argparse
import logging
import json
from datetime import datetime
from pathlib import Path

# Add the parent directory to the path so we can import the utils module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the GitHub integration module
from utils.github_integration import (
    validate_github_config,
    check_for_updates,
    pull_updates,
    push_changes,
    create_github_issue,
    sync_trading_results,
    update_heartbeat_status
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('logs', 'github_sync.log'))
    ]
)
logger = logging.getLogger('github_sync')

def setup_logging():
    """Ensure the logs directory exists"""
    os.makedirs('logs', exist_ok=True)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='GitHub Sync for AI Trading Sentinel')
    
    # Create a subparser for different commands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Check for updates command
    check_parser = subparsers.add_parser('check', help='Check for updates')
    
    # Pull updates command
    pull_parser = subparsers.add_parser('pull', help='Pull updates')
    
    # Push changes command
    push_parser = subparsers.add_parser('push', help='Push local changes')
    push_parser.add_argument('--message', '-m', required=True, help='Commit message')
    
    # Sync trading results command
    sync_parser = subparsers.add_parser('sync', help='Sync trading results')
    sync_parser.add_argument('--file', '-f', required=True, help='Path to the trading results file')
    
    # Create issue command
    issue_parser = subparsers.add_parser('issue', help='Create a GitHub issue')
    issue_parser.add_argument('--title', '-t', required=True, help='Issue title')
    issue_parser.add_argument('--body', '-b', required=True, help='Issue body')
    issue_parser.add_argument('--labels', '-l', nargs='+', help='Issue labels')
    
    return parser.parse_args()

def main():
    """Main function"""
    # Setup logging
    setup_logging()
    
    # Parse arguments
    args = parse_arguments()
    
    # Validate GitHub configuration
    if not validate_github_config():
        logger.error("GitHub configuration is invalid. Please check your .env file.")
        sys.exit(1)
    
    # Execute the requested command
    if args.command == 'check':
        updates_available, details = check_for_updates()
        if updates_available:
            logger.info(f"Updates available:\n{details}")
            print(f"\n! Updates available:\n{details}")
        else:
            logger.info(details)
            print(f"\n✓ {details}")
    
    elif args.command == 'pull':
        success, result = pull_updates()
        if success:
            logger.info(f"Updates pulled successfully:\n{result}")
            print(f"\n✓ Updates pulled successfully")
        else:
            logger.error(f"Failed to pull updates:\n{result}")
            print(f"\n✗ Failed to pull updates:\n{result}")
    
    elif args.command == 'push':
        success, result = push_changes(args.message)
        if success:
            logger.info(f"Changes pushed successfully:\n{result}")
            print(f"\n✓ Changes pushed successfully")
        else:
            logger.error(f"Failed to push changes:\n{result}")
            print(f"\n✗ Failed to push changes:\n{result}")
    
    elif args.command == 'sync':
        success, result = sync_trading_results(args.file)
        if success:
            logger.info(f"Trading results synced successfully:\n{result}")
            print(f"\n✓ Trading results synced successfully")
        else:
            logger.error(f"Failed to sync trading results:\n{result}")
            print(f"\n✗ Failed to sync trading results:\n{result}")
    
    elif args.command == 'issue':
        success, result = create_github_issue(args.title, args.body, args.labels)
        if success:
            logger.info(f"GitHub issue created successfully:\n{result}")
            print(f"\n✓ GitHub issue created successfully:\n{result}")
        else:
            logger.error(f"Failed to create GitHub issue:\n{result}")
            print(f"\n✗ Failed to create GitHub issue:\n{result}")
    
    else:
        # If no command is provided, show help
        print("\nAI Trading Sentinel - GitHub Sync")
        print("=================================\n")
        print("Available commands:")
        print("  check  - Check for updates")
        print("  pull   - Pull updates")
        print("  push   - Push local changes")
        print("  sync   - Sync trading results")
        print("  issue  - Create a GitHub issue\n")
        print("Use --help with any command for more information.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n! Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.exception("An unexpected error occurred")
        print(f"\n✗ An unexpected error occurred: {str(e)}")
        
        # Update heartbeat status
        update_heartbeat_status("error", {"error": str(e)})
        
        sys.exit(1)