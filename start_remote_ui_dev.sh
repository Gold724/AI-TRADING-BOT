#!/bin/bash

echo "Starting AI Trading Sentinel Remote UI in development mode..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Start the services using docker-compose with the override file
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d

echo ""
echo "Remote UI started successfully!"
echo ""
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:5000"
echo ""
echo "Press Enter to view logs (Ctrl+C to exit logs)..."
read

docker-compose -f docker-compose.yml -f docker-compose.override.yml logs -f