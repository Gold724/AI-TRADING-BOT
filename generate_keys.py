#!/usr/bin/env python3

import os
import secrets
import string
import base64
from cryptography.fernet import Fernet

def generate_flask_secret_key(length=32):
    """Generate a secure random key for Flask's secret_key"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_fernet_key():
    """Generate a Fernet key for encryption"""
    return Fernet.generate_key().decode()

def update_env_file():
    """Update .env file with generated keys"""
    # Check if .env file exists
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            # Copy example file
            with open('.env.example', 'r') as example_file:
                env_content = example_file.read()
        else:
            # Create minimal content
            env_content = "# AI Trading Sentinel Environment Variables\n\n"
    else:
        # Read existing content
        with open('.env', 'r') as env_file:
            env_content = env_file.read()
    
    # Generate keys
    flask_key = generate_flask_secret_key()
    fernet_key = generate_fernet_key()
    
    # Update FLASK_SECRET_KEY
    if 'FLASK_SECRET_KEY=' in env_content:
        env_content = env_content.replace(
            'FLASK_SECRET_KEY=generate_a_secure_random_key', 
            f'FLASK_SECRET_KEY={flask_key}'
        )
    else:
        env_content += f"\nFLASK_SECRET_KEY={flask_key}\n"
    
    # Update ENCRYPTION_KEY
    if 'ENCRYPTION_KEY=' in env_content:
        env_content = env_content.replace(
            'ENCRYPTION_KEY=generate_a_secure_fernet_key', 
            f'ENCRYPTION_KEY={fernet_key}'
        )
    else:
        env_content += f"\nENCRYPTION_KEY={fernet_key}\n"
    
    # Write updated content
    with open('.env', 'w') as env_file:
        env_file.write(env_content)
    
    print("\nGenerated and updated security keys in .env file:")
    print(f"FLASK_SECRET_KEY={flask_key}")
    print(f"ENCRYPTION_KEY={fernet_key}")
    print("\nKeep these keys secure and do not share them!")

if __name__ == "__main__":
    print("AI Trading Sentinel - Security Key Generator")
    print("===========================================\n")
    
    try:
        update_env_file()
        print("\nKey generation completed successfully!")
    except Exception as e:
        print(f"\nError generating keys: {e}")
        print("\nManual key generation:")
        print(f"FLASK_SECRET_KEY={generate_flask_secret_key()}")
        print(f"ENCRYPTION_KEY={generate_fernet_key()}")
        print("\nAdd these keys to your .env file manually.")