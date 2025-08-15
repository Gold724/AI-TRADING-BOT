#!/usr/bin/env python3
"""
AI Trading Sentinel - Remote UI Deployment Script

This script automates the deployment of the AI Trading Sentinel with remote UI capabilities
to a Vast.ai instance. It configures the necessary environment variables for remote access,
establishes an SSH connection, and sets up both the trading bot and frontend.
"""

import argparse
import os
import subprocess

from dotenv import load_dotenv

# Parse command line arguments
parser = argparse.ArgumentParser(
    description="Deploy AI Trading Sentinel with Remote UI to Vast.ai"
)
parser.add_argument(
    "--dry-run",
    action="store_true",
    help="Validate configuration without connecting to the server",
)
parser.add_argument(
    "--frontend-only", action="store_true", help="Only deploy the frontend UI"
)
parser.add_argument(
    "--backend-only", action="store_true", help="Only deploy the backend API"
)
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
required_vars = [
    "VAST_INSTANCE_IP",
    "SSH_KEY_PATH",
    "GITHUB_REPO",
    "GITHUB_USERNAME",
    "GITHUB_PAT",
]
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    print(
        f"❌ Error: Missing required environment variables: {', '.join(missing_vars)}"
    )
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
print("🚀 AI Trading Sentinel - Remote UI Deployment")
print(f"📡 Target: {SSH_USER}@{IP}:{SSH_PORT}")
print(f"📂 Project Directory: {PROJECT_DIR}")
print(f"🔑 Using SSH key: {SSH_KEY}")
print(f"📦 Repository: {REPO.replace(PAT, '********') if PAT in REPO else REPO}")

# Determine what to deploy
deploy_backend = not args.frontend_only
deploy_frontend = not args.backend_only

if deploy_backend and deploy_frontend:
    print("📦 Deploying both backend API and frontend UI")
elif deploy_backend:
    print("📦 Deploying backend API only")
elif deploy_frontend:
    print("📦 Deploying frontend UI only")

# Commands to run on the remote server
commands = f"""
cd ~
echo "🧹 Removing any existing project directory..."
rm -rf {PROJECT_DIR}

echo "📥 Cloning repository..."
git clone {clone_url} {PROJECT_DIR}

cd {PROJECT_DIR}

"""

# Add backend deployment commands if needed
if deploy_backend:
    commands += f"""
echo "🐍 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "⚙️ Configuring environment variables..."
echo "FLASK_HOST=0.0.0.0" >> .env
echo "FLASK_PORT=5000" >> .env
echo "CORS_ORIGINS=*" >> .env

echo "🚀 Launching the cloud API as a background daemon..."
nohup python cloud_main.py > cloud_api.log 2>&1 &

echo "✅ Backend API deployment complete! Running on http://{IP}:5000"
echo "📊 To monitor the API, use: tail -f cloud_api.log"

# Get the process ID of the running API
ps aux | grep "[p]ython cloud_main.py"
"""

# Add frontend deployment commands if needed
if deploy_frontend:
    commands += f"""
echo "🌐 Setting up frontend..."
cd frontend

echo "📦 Installing Node.js dependencies..."
npm install

echo "⚙️ Configuring frontend for remote API..."
echo "REACT_APP_API_URL=http://{IP}:5000" > .env

echo "🏗️ Building frontend..."
npm run build

echo "🚀 Installing serve to host the frontend..."
npm install -g serve

echo "🚀 Launching the frontend UI as a background daemon..."
nohup serve -s dist -l 3000 > frontend.log 2>&1 &

echo "✅ Frontend UI deployment complete! Available at http://{IP}:3000"
echo "📊 To monitor the frontend, use: tail -f frontend.log"

# Get the process ID of the running frontend
ps aux | grep "[s]erve -s dist"
"""

# If dry run, just print the configuration and exit
if args.dry_run:
    print("\n🔍 DRY RUN MODE - Configuration validated successfully")
    print("\n📋 Commands that would be executed on the server:")
    print("-------------------------------------------")
    # Print commands with PAT masked
    masked_commands = commands.replace(PAT, "********") if PAT else commands
    print(masked_commands)
    print("-------------------------------------------")
    print("\n✅ Dry run completed. No connection was made to the server.")
    print(
        "🔒 Remember: Your .env file contains sensitive information. Keep it secure and excluded from Git commits."
    )
    exit(0)

try:
    # Run the SSH command
    print("\n📡 Connecting to Vast.ai instance...")
    result = subprocess.run(
        [
            "ssh",
            "-i",
            SSH_KEY,
            "-p",
            SSH_PORT,
            f"{SSH_USER}@{IP}",
            f'bash -c "{commands}"',
        ],
        capture_output=True,
        text=True,
    )

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

        if deploy_backend:
            print(f"📊 Backend API available at: http://{IP}:5000")
            print(
                "   To monitor the API, SSH into the instance and run: tail -f cloud_api.log"
            )

        if deploy_frontend:
            print(f"🌐 Frontend UI available at: http://{IP}:3000")
            print(
                "   To monitor the frontend, SSH into the instance and run: tail -f frontend.log"
            )

        print("\n🔗 To connect the local frontend to the remote API:")
        print(f"   1. Open the frontend in your browser: http://localhost:3000")
        print(f"   2. Set the API Endpoint to: http://{IP}:5000")
    else:
        print(f"\n❌ Deployment failed with return code {result.returncode}")

except Exception as e:
    print(f"\n❌ Error during deployment: {str(e)}")

print(
    "\n🔒 Remember: Your .env file contains sensitive information. Keep it secure and excluded from Git commits."
)
