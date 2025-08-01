#!/bin/bash

echo "Stopping AI Trading Sentinel Remote UI services..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Stop the services using docker-compose
docker-compose -f docker-compose.yml -f docker-compose.override.yml down

echo ""
echo "Remote UI services stopped successfully!"