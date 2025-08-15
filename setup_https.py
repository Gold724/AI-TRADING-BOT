#!/usr/bin/env python3

import os
import sys
import json
import argparse
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("trae.setup_https")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Setup HTTPS for TRAE AI Trading Sentinel")
    parser.add_argument("--config", type=str, default="config/liveops_config.json", help="Path to configuration file")
    parser.add_argument("--domain", type=str, help="Domain name for the certificate")
    parser.add_argument("--email", type=str, help="Email address for Let's Encrypt registration")
    parser.add_argument("--self-signed", action="store_true", help="Generate self-signed certificate instead of using Let's Encrypt")
    parser.add_argument("--cert-dir", type=str, default="certs", help="Directory to store certificates")
    parser.add_argument("--force", action="store_true", help="Force certificate generation even if certificates already exist")
    
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


def create_cert_directory(cert_dir: str) -> bool:
    """Create directory for certificates.
    
    Args:
        cert_dir (str): Directory path
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        os.makedirs(cert_dir, exist_ok=True)
        logger.info(f"Certificate directory created: {cert_dir}")
        return True
    except Exception as e:
        logger.error(f"Error creating certificate directory: {e}")
        return False


def generate_self_signed_cert(domain: str, cert_dir: str) -> bool:
    """Generate self-signed SSL certificate using OpenSSL.
    
    Args:
        domain (str): Domain name for the certificate
        cert_dir (str): Directory to store certificates
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create certificate directory
        if not create_cert_directory(cert_dir):
            return False
        
        # Generate private key
        key_path = os.path.join(cert_dir, f"{domain}.key")
        cert_path = os.path.join(cert_dir, f"{domain}.crt")
        
        # Check if certificates already exist
        if os.path.exists(key_path) and os.path.exists(cert_path):
            logger.info(f"Certificates already exist for {domain}")
            return True
        
        # Create OpenSSL configuration file
        openssl_config = f"""
        [req]
        default_bits = 2048
        prompt = no
        default_md = sha256
        distinguished_name = dn
        x509_extensions = v3_req
        
        [dn]
        C = US
        ST = State
        L = City
        O = TRAE AI Trading Sentinel
        OU = LiveOps
        CN = {domain}
        
        [v3_req]
        subjectAltName = @alt_names
        basicConstraints = CA:FALSE
        keyUsage = nonRepudiation, digitalSignature, keyEncipherment
        
        [alt_names]
        DNS.1 = {domain}
        DNS.2 = www.{domain}
        DNS.3 = localhost
        IP.1 = 127.0.0.1
        """
        
        config_path = os.path.join(cert_dir, "openssl.cnf")
        with open(config_path, "w") as f:
            f.write(openssl_config)
        
        # Generate private key and certificate
        cmd = f"openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout {key_path} -out {cert_path} -config {config_path}"
        subprocess.run(cmd, shell=True, check=True)
        
        logger.info(f"Self-signed certificate generated for {domain}")
        logger.info(f"Private key: {key_path}")
        logger.info(f"Certificate: {cert_path}")
        
        return True
    except Exception as e:
        logger.error(f"Error generating self-signed certificate: {e}")
        return False


def setup_lets_encrypt(domain: str, email: str, cert_dir: str) -> bool:
    """Setup Let's Encrypt certificate using certbot.
    
    Args:
        domain (str): Domain name for the certificate
        email (str): Email address for Let's Encrypt registration
        cert_dir (str): Directory to store certificates
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if certbot is installed
        try:
            subprocess.run(["certbot", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("Certbot is not installed. Please install certbot first.")
            logger.info("On Ubuntu/Debian: sudo apt-get install certbot")
            logger.info("On CentOS/RHEL: sudo yum install certbot")
            logger.info("On Windows: pip install certbot")
            return False
        
        # Create certificate directory
        if not create_cert_directory(cert_dir):
            return False
        
        # Run certbot to obtain certificate
        cmd = [
            "certbot", "certonly", "--standalone",
            "--agree-tos", "--non-interactive",
            "--preferred-challenges", "http",
            "--email", email,
            "--domain", domain,
            "--cert-path", os.path.join(cert_dir, f"{domain}.crt"),
            "--key-path", os.path.join(cert_dir, f"{domain}.key")
        ]
        
        subprocess.run(cmd, check=True)
        
        logger.info(f"Let's Encrypt certificate obtained for {domain}")
        return True
    except Exception as e:
        logger.error(f"Error setting up Let's Encrypt certificate: {e}")
        return False


def update_config_for_https(config: Dict[str, Any], domain: str, cert_dir: str) -> Dict[str, Any]:
    """Update configuration for HTTPS.
    
    Args:
        config (Dict[str, Any]): Configuration dictionary
        domain (str): Domain name for the certificate
        cert_dir (str): Directory to store certificates
        
    Returns:
        Dict[str, Any]: Updated configuration dictionary
    """
    try:
        # Ensure webhook section exists
        if "signal_sources" not in config:
            config["signal_sources"] = {}
        
        if "webhook" not in config["signal_sources"]:
            config["signal_sources"]["webhook"] = {}
        
        # Update webhook configuration
        webhook_config = config["signal_sources"]["webhook"]
        webhook_config["enabled"] = True
        webhook_config["use_https"] = True
        webhook_config["cert_path"] = os.path.join(cert_dir, f"{domain}.crt")
        webhook_config["key_path"] = os.path.join(cert_dir, f"{domain}.key")
        webhook_config["domain"] = domain
        
        # Update API configuration
        if "api" not in config:
            config["api"] = {}
        
        config["api"]["use_https"] = True
        config["api"]["cert_path"] = os.path.join(cert_dir, f"{domain}.crt")
        config["api"]["key_path"] = os.path.join(cert_dir, f"{domain}.key")
        config["api"]["domain"] = domain
        
        logger.info("Configuration updated for HTTPS")
        return config
    except Exception as e:
        logger.error(f"Error updating configuration for HTTPS: {e}")
        return config


def main():
    """Main function."""
    args = parse_args()
    
    # Load configuration
    config = load_config(args.config)
    if not config:
        logger.error(f"Failed to load configuration from {args.config}")
        sys.exit(1)
    
    # Create certificate directory
    if not create_cert_directory(args.cert_dir):
        logger.error("Failed to create certificate directory")
        sys.exit(1)
    
    # Check if domain is provided
    if not args.domain:
        logger.error("Domain name is required")
        logger.info("Use --domain to specify the domain name")
        sys.exit(1)
    
    # Generate certificate
    if args.self_signed:
        success = generate_self_signed_cert(args.domain, args.cert_dir)
    else:
        if not args.email:
            logger.error("Email address is required for Let's Encrypt")
            logger.info("Use --email to specify the email address")
            sys.exit(1)
        
        success = setup_lets_encrypt(args.domain, args.email, args.cert_dir)
    
    if not success:
        logger.error("Failed to generate certificate")
        sys.exit(1)
    
    # Update configuration
    config = update_config_for_https(config, args.domain, args.cert_dir)
    
    # Save configuration
    if not save_config(config, args.config):
        logger.error("Failed to save configuration")
        sys.exit(1)
    
    logger.info("HTTPS setup completed successfully")
    logger.info(f"Domain: {args.domain}")
    logger.info(f"Certificate directory: {args.cert_dir}")
    logger.info(f"Configuration file: {args.config}")
    
    # Print next steps
    logger.info("\nNext steps:")
    logger.info("1. Restart the TRAE AI Trading Sentinel to apply the changes")
    logger.info("2. Make sure port 443 is open in your firewall")
    logger.info("3. If using Let's Encrypt, set up auto-renewal for the certificate")


if __name__ == "__main__":
    main()