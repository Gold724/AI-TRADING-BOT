#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script for GitHub integration functionality

This script tests the GitHub integration module to ensure it can properly
check for updates, pull updates, and handle various error conditions.

Usage:
    python test_github_integration.py
"""

import os
import sys
import time
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("github-integration-test")

# Load environment variables
load_dotenv()

# Import GitHub integration module
try:
    from utils.github_integration import (
        check_for_updates,
        pull_updates,
        validate_github_config,
        construct_github_url
    )
    logger.info("Successfully imported GitHub integration module")
except ImportError as e:
    logger.error(f"Failed to import GitHub integration module: {e}")
    logger.error("Make sure utils/github_integration.py exists and is properly implemented")
    sys.exit(1)

def test_validate_github_config():
    """Test GitHub configuration validation"""
    logger.info("Testing GitHub configuration validation...")
    
    # Get GitHub configuration from environment variables
    github_username = os.getenv("GITHUB_USERNAME")
    github_pat = os.getenv("GITHUB_PAT")
    github_repo = os.getenv("GITHUB_REPO")
    
    # Log configuration (masking PAT)
    logger.info(f"GitHub Username: {github_username}")
    if github_pat:
        masked_pat = github_pat[:4] + "*" * (len(github_pat) - 8) + github_pat[-4:] if len(github_pat) > 8 else "****"
        logger.info(f"GitHub PAT: {masked_pat}")
    else:
        logger.info("GitHub PAT: Not set")
    logger.info(f"GitHub Repo: {github_repo}")
    
    # Validate configuration
    try:
        is_valid = validate_github_config()
        if is_valid:
            logger.info("✅ GitHub configuration is valid")
        else:
            logger.error("❌ GitHub configuration is invalid")
    except Exception as e:
        logger.error(f"❌ Error validating GitHub configuration: {e}")

def test_construct_github_url():
    """Test GitHub URL construction"""
    logger.info("Testing GitHub URL construction...")
    
    try:
        url = construct_github_url()
        # Mask PAT in URL for logging
        masked_url = url
        if "@" in url:
            parts = url.split("@")
            if ":" in parts[0]:
                protocol_user, pat = parts[0].split(":")
                masked_pat = pat[:4] + "*" * (len(pat) - 8) + pat[-4:] if len(pat) > 8 else "****"
                masked_url = f"{protocol_user}:{masked_pat}@{parts[1]}"
        
        logger.info(f"Constructed GitHub URL: {masked_url}")
        logger.info("✅ GitHub URL construction successful")
    except Exception as e:
        logger.error(f"❌ Error constructing GitHub URL: {e}")

def test_check_for_updates():
    """Test checking for updates"""
    logger.info("Testing check for updates...")
    
    try:
        updates_available = check_for_updates()
        if updates_available:
            logger.info("✅ Updates are available")
        else:
            logger.info("✅ No updates available")
    except Exception as e:
        logger.error(f"❌ Error checking for updates: {e}")

def test_pull_updates():
    """Test pulling updates (only if updates are available)"""
    logger.info("Testing pull updates...")
    
    try:
        # First check if updates are available
        updates_available = check_for_updates()
        
        if updates_available:
            logger.info("Updates are available, attempting to pull...")
            
            # Ask for confirmation before pulling updates
            confirm = input("Updates are available. Do you want to pull them? (y/n): ")
            if confirm.lower() != 'y':
                logger.info("Skipping pull updates test")
                return
            
            success = pull_updates()
            if success:
                logger.info("✅ Successfully pulled updates")
            else:
                logger.error("❌ Failed to pull updates")
        else:
            logger.info("No updates available, skipping pull test")
    except Exception as e:
        logger.error(f"❌ Error pulling updates: {e}")

def run_tests():
    """Run all tests"""
    logger.info("Starting GitHub integration tests")
    
    # Run tests
    test_validate_github_config()
    print("\n" + "-"*50 + "\n")
    
    test_construct_github_url()
    print("\n" + "-"*50 + "\n")
    
    test_check_for_updates()
    print("\n" + "-"*50 + "\n")
    
    test_pull_updates()
    
    logger.info("All tests completed")

if __name__ == "__main__":
    run_tests()