#!/bin/bash

# AI Trading Sentinel Ubuntu Deployment Script
# This script sets up and deploys the AI Trading Sentinel on Ubuntu

set -e  # Exit on error

echo "========================================"
echo "AI Trading Sentinel - Ubuntu Deployment"
echo "========================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Installing Docker..."
    sudo apt-get update
    sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
    sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io
    sudo systemctl enable docker
    sudo systemctl start docker
    sudo usermod -aG docker $USER
    echo "Docker installed successfully!"
    echo "Please log out and log back in to apply group changes, then run this script again."
    exit 0
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose not found. Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.3/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "Docker Compose installed successfully!"
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "Please edit the .env file with your credentials before continuing."
    echo "Run 'nano .env' to edit the file."
    exit 0
fi

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p backend/logs/screenshots
mkdir -p temp_chrome_profile
mkdir -p temp_chrome_profile_futures

# Build and start the containers
echo "Building and starting Docker containers..."
docker-compose build
docker-compose up -d

# Setup Chrome profile for Selenium
echo "Setting up Chrome profile for Selenium..."
docker-compose exec backend python setup_chrome_profile_ubuntu.py

# Check for QuantConnect integration
if grep -q "QC_API_KEY" .env && grep -q "QC_PROJECT_ID" .env; then
    echo "QuantConnect integration detected. Testing integration..."
    docker-compose exec backend python test_quantconnect.py
else
    echo "QuantConnect integration not configured. Skipping test."
    echo "To enable QuantConnect integration, uncomment and set QC_API_KEY and QC_PROJECT_ID in your .env file."
fi

# Check if services are running
echo "Checking if services are running..."
sleep 5
if docker-compose ps | grep -q "Up"; then
    echo "Services are running!"
    echo "Backend API: http://localhost:5000"
    echo "Frontend: http://localhost:5173"
    echo "\nTo view logs: docker-compose logs -f"
    echo "To stop services: docker-compose down"
else
    echo "Error: Services failed to start. Check logs with: docker-compose logs"
    exit 1
fi

echo "\nDeployment completed successfully!"