#!/usr/bin/env python3
"""
AI Trading Sentinel - Vast.ai Deployment Script

This script automates the deployment of the AI Trading Sentinel to a Vast.ai instance.
It loads environment variables, establishes an SSH connection, and sets up the trading bot.
"""

import os
import subprocess
import argparse
from dotenv import load_dotenv

# Parse command line arguments
parser = argparse.ArgumentParser(description='Deploy AI Trading Sentinel to Vast.ai')
parser.add_argument('--dry-run', action='store_true', help='Validate configuration without connecting to the server')
args = parser.parse_args()

# Load environment variables from .env file
load_dotenv()

# Get required environment variables
IP = os.getenv("VAST_INSTANCE_IP")
SSH_USER = os.getenv("SSH_USER", "vast")
SSH_KEY = os.getenv("SSH_KEY_PATH")
SSH_PORT = os.getenv("SSH_PORT", "22")
REPO = os.getenv("GITHUB_REPO")
PAT = os.getenv("GITHUB_PAT")
USERNAME = os.getenv("GITHUB_USERNAME")
PROJECT_DIR = os.getenv("PROJECT_DIR", "ai-trading-sentinel")

# Validate required environment variables
required_vars = ["VAST_INSTANCE_IP", "SSH_KEY_PATH", "GITHUB_REPO", "GITHUB_USERNAME", "GITHUB_PAT"]
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    print(f"❌ Error: Missing required environment variables: {', '.join(missing_vars)}")
    print("Please check your .env file and ensure all required variables are set.")
    exit(1)

# Verify SSH key exists
if not os.path.exists(SSH_KEY):
    print(f"❌ Error: SSH key not found at {SSH_KEY}")
    print("Please check your SSH_KEY_PATH in the .env file.")
    exit(1)

# Replace https:// with authenticated GitHub clone format
clone_url = REPO.replace("https://", f"https://{USERNAME}:{PAT}@")

# Print deployment information
print("🚀 AI Trading Sentinel - Vast.ai Deployment")
print(f"📡 Target: {SSH_USER}@{IP}:{SSH_PORT}")
print(f"📂 Project Directory: {PROJECT_DIR}")
print(f"🔑 Using SSH key: {SSH_KEY}")
print(f"📦 Repository: {REPO.replace(PAT, '********')}")

# Commands to run on the remote server
commands = f"""
cd ~
echo "🧹 Removing any existing project directory..."
rm -rf {PROJECT_DIR}

echo "📥 Cloning repository..."
git clone {clone_url} {PROJECT_DIR}

cd {PROJECT_DIR}

echo "🐍 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "🚀 Launching the trading bot as a background daemon..."
nohup python backend/main.py > bot.log 2>&1 &

echo "✅ Deployment complete! Bot is running in the background."
echo "📊 To monitor the bot, use: tail -f bot.log"

# Get the process ID of the running bot
ps aux | grep "[p]ython backend/main.py"
"""

# If dry run, just print the configuration and exit
if args.dry_run:
    print("\n🔍 DRY RUN MODE - Configuration validated successfully")
    print("\n📋 Commands that would be executed on the server:")
    print("-------------------------------------------")
    # Print commands with PAT masked
    masked_commands = commands.replace(PAT, "********")
    print(masked_commands)
    print("-------------------------------------------")
    print("\n✅ Dry run completed. No connection was made to the server.")
    print("🔒 Remember: Your .env file contains sensitive information. Keep it secure and excluded from Git commits.")
    exit(0)

try:
    # Run the SSH command
    print("\n📡 Connecting to Vast.ai instance...")
    result = subprocess.run([
        "ssh", "-i", SSH_KEY, "-p", SSH_PORT, f"{SSH_USER}@{IP}",
        f'bash -c "{commands}"'
    ], capture_output=True, text=True)
    
    # Print the output
    if result.stdout:
        print("\n📤 Output:")
        print(result.stdout)
    
    # Print any errors
    if result.stderr:
        print("\n⚠️ Errors:")
        print(result.stderr)
    
    # Check if the deployment was successful
    if result.returncode == 0:
        print("\n✅ Deployment successful!")
        print("📊 To monitor the bot, SSH into the instance and run: tail -f bot.log")
    else:
        print(f"\n❌ Deployment failed with return code {result.returncode}")

except Exception as e:
    print(f"\n❌ Error during deployment: {str(e)}")

print("\n🔒 Remember: Your .env file contains sensitive information. Keep it secure and excluded from Git commits.")