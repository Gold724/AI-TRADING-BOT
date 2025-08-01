#!/bin/bash

echo "Checking AI Trading Sentinel Remote UI services status..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check the status of the services using docker-compose
docker-compose -f docker-compose.yml -f docker-compose.override.yml ps

echo ""
echo "Checking container logs (last 10 lines):"
echo ""

echo "Sentinel Bot logs:"
echo "-------------------------------"
docker-compose -f docker-compose.yml -f docker-compose.override.yml logs --tail=10 sentinel-bot

echo ""
echo "Frontend logs:"
echo "-------------------------------"
docker-compose -f docker-compose.yml -f docker-compose.override.yml logs --tail=10 frontend

echo ""
echo "Press Enter to exit..."
read