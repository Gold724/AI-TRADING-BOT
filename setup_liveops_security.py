#!/usr/bin/env python3

import os
import sys
import json
import logging
import argparse
import secrets
import hashlib
import base64
from pathlib import Path
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("trae.setup_liveops_security")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="TRAE LiveOps Security Setup")
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
        "--generate-keys", 
        action="store_true", 
        default=True,
        help="Generate new API keys"
    )
    parser.add_argument(
        "--setup-https", 
        action="store_true", 
        default=False,
        help="Set up HTTPS with self-signed certificates"
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


def save_config(config: Dict[str, Any], config_path: str) -> bool:
    """Save configuration to file.
    
    Args:
        config (Dict[str, Any]): Configuration dictionary
        config_path (str): Path to configuration file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # Save configuration
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Configuration saved to {config_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        return False


def generate_api_key() -> str:
    """Generate a secure API key.
    
    Returns:
        str: Generated API key
    """
    # Generate a random token
    token = secrets.token_bytes(32)
    
    # Convert to base64 for easier handling
    api_key = base64.urlsafe_b64encode(token).decode('utf-8').rstrip('=')
    
    return api_key


def generate_jwt_secret() -> str:
    """Generate a secure JWT secret.
    
    Returns:
        str: Generated JWT secret
    """
    # Generate a random token
    token = secrets.token_bytes(64)
    
    # Convert to base64 for easier handling
    jwt_secret = base64.urlsafe_b64encode(token).decode('utf-8').rstrip('=')
    
    return jwt_secret


def update_env_file(env_file: str, env_vars: Dict[str, str]) -> bool:
    """Update environment file with new variables.
    
    Args:
        env_file (str): Path to environment file
        env_vars (Dict[str, str]): Environment variables to add/update
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Read existing file if it exists
        env_content = ""
        if os.path.exists(env_file):
            with open(env_file, "r") as f:
                env_content = f.read()
        
        # Update or add environment variables
        for key, value in env_vars.items():
            # Check if variable already exists
            if f"{key}=" in env_content:
                # Replace existing variable
                lines = env_content.split('\n')
                for i, line in enumerate(lines):
                    if line.startswith(f"{key}="):
                        lines[i] = f"{key}={value}"
                env_content = '\n'.join(lines)
            else:
                # Add new variable
                env_content += f"\n{key}={value}"
        
        # Write updated content
        with open(env_file, "w") as f:
            f.write(env_content.strip() + "\n")
        
        logger.info(f"Environment file {env_file} updated")
        return True
    except Exception as e:
        logger.error(f"Error updating environment file: {e}")
        return False


def setup_api_security(config: Dict[str, Any], env_file: str, generate_keys: bool) -> bool:
    """Set up API security with JWT and API keys.
    
    Args:
        config (Dict[str, Any]): Configuration dictionary
        env_file (str): Path to environment file
        generate_keys (bool): Whether to generate new keys
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Initialize security section if it doesn't exist
        if "security" not in config:
            config["security"] = {}
        
        # Set up JWT authentication
        if "jwt" not in config["security"]:
            config["security"]["jwt"] = {}
        
        config["security"]["jwt"]["enabled"] = True
        config["security"]["jwt"]["expiration_seconds"] = 86400  # 24 hours
        
        # Set up API key authentication
        if "api_keys" not in config["security"]:
            config["security"]["api_keys"] = {}
        
        config["security"]["api_keys"]["enabled"] = True
        
        # Generate new keys if requested
        env_vars = {}
        
        if generate_keys:
            # Generate JWT secret
            jwt_secret = generate_jwt_secret()
            env_vars["TRAE_JWT_SECRET"] = jwt_secret
            
            # Generate API key
            api_key = generate_api_key()
            env_vars["TRAE_API_KEY"] = api_key
            
            logger.info("Generated new security keys")
        
        # Update environment file
        if env_vars and not update_env_file(env_file, env_vars):
            return False
        
        # Update webhook configuration to require authentication
        if "signal_sources" in config and "webhook" in config["signal_sources"]:
            config["signal_sources"]["webhook"]["require_auth"] = True
            config["signal_sources"]["webhook"]["auth_method"] = "api_key"  # or "jwt"
        
        logger.info("API security configuration updated")
        return True
    except Exception as e:
        logger.error(f"Error setting up API security: {e}")
        return False


def generate_self_signed_cert():
    """Generate self-signed SSL certificate for HTTPS.
    
    Returns:
        tuple: (cert_path, key_path) if successful, (None, None) otherwise
    """
    try:
        from OpenSSL import crypto
        
        # Create certificates directory
        cert_dir = os.path.join(os.getcwd(), "config", "certs")
        os.makedirs(cert_dir, exist_ok=True)
        
        # Paths for certificate and key
        cert_path = os.path.join(cert_dir, "server.crt")
        key_path = os.path.join(cert_dir, "server.key")
        
        # Check if certificate already exists
        if os.path.exists(cert_path) and os.path.exists(key_path):
            logger.info("SSL certificate already exists, skipping generation")
            return cert_path, key_path
        
        # Create a key pair
        k = crypto.PKey()
        k.generate_key(crypto.TYPE_RSA, 2048)
        
        # Create a self-signed cert
        cert = crypto.X509()
        cert.get_subject().C = "US"
        cert.get_subject().ST = "State"
        cert.get_subject().L = "City"
        cert.get_subject().O = "TRAE AI"
        cert.get_subject().OU = "Trading Sentinel"
        cert.get_subject().CN = "localhost"
        cert.set_serial_number(1000)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(10*365*24*60*60)  # 10 years
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(k)
        cert.sign(k, 'sha256')
        
        # Write certificate and key to files
        with open(cert_path, "wb") as f:
            f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
        
        with open(key_path, "wb") as f:
            f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))
        
        # Set appropriate permissions
        os.chmod(cert_path, 0o644)
        os.chmod(key_path, 0o600)
        
        logger.info(f"Self-signed SSL certificate generated at {cert_path}")
        return cert_path, key_path
    except ImportError:
        logger.error("PyOpenSSL not installed. Install with: pip install pyopenssl")
        return None, None
    except Exception as e:
        logger.error(f"Error generating self-signed certificate: {e}")
        return None, None


def setup_https(config: Dict[str, Any]) -> bool:
    """Set up HTTPS with self-signed certificates.
    
    Args:
        config (Dict[str, Any]): Configuration dictionary
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Generate self-signed certificate
        cert_path, key_path = generate_self_signed_cert()
        if not cert_path or not key_path:
            return False
        
        # Update webhook configuration to use HTTPS
        if "signal_sources" in config and "webhook" in config["signal_sources"]:
            config["signal_sources"]["webhook"]["use_https"] = True
            config["signal_sources"]["webhook"]["cert_path"] = cert_path
            config["signal_sources"]["webhook"]["key_path"] = key_path
        
        logger.info("HTTPS configuration updated")
        return True
    except Exception as e:
        logger.error(f"Error setting up HTTPS: {e}")
        return False


def main():
    """Main entry point for TRAE LiveOps Security Setup."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Load configuration
    config = load_config(args.config)
    
    # Log startup information
    logger.info("Starting TRAE LiveOps Security Setup")
    
    # Set up API security
    if not setup_api_security(config, args.env_file, args.generate_keys):
        logger.error("Failed to set up API security")
        return 1
    
    # Set up HTTPS if requested
    if args.setup_https:
        if not setup_https(config):
            logger.error("Failed to set up HTTPS")
            return 1
    
    # Save updated configuration
    if not save_config(config, args.config):
        logger.error("Failed to save configuration")
        return 1
    
    # Setup complete
    logger.info("TRAE LiveOps Security Setup completed successfully")
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Restart the LiveOps system to apply security changes")
    logger.info("2. Use the API key or JWT token for authentication")
    if args.setup_https:
        logger.info("3. Access the webhook endpoint using HTTPS")
    logger.info("")
    logger.info("Security notes:")
    logger.info("- Keep your API keys and JWT secret secure")
    logger.info("- Rotate keys regularly for enhanced security")
    logger.info("- Consider using a reverse proxy for production deployments")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())