#!/bin/bash
# AI Trading Sentinel Docker Build and Run Script

set -e

# Default values
DOCKER_IMAGE="sentinel-bot"
CONTAINER_NAME="sentinel-runner"
DOCKERFILE="Dockerfile.sentinel"
PORT=5000

# Display help message
show_help() {
    echo "AI Trading Sentinel Docker Helper Script"
    echo ""
    echo "Usage: $0 [options] [command]"
    echo ""
    echo "Commands:"
    echo "  build       Build the Docker image"
    echo "  run         Run the Docker container"
    echo "  stop        Stop the running container"
    echo "  logs        Show container logs"
    echo "  status      Check container status"
    echo "  restart     Restart the container"
    echo "  clean       Remove container and image"
    echo "  all         Build and run in one command"
    echo ""
    echo "Options:"
    echo "  -h, --help                Show this help message"
    echo "  -i, --image NAME          Set Docker image name (default: $DOCKER_IMAGE)"
    echo "  -c, --container NAME      Set container name (default: $CONTAINER_NAME)"
    echo "  -f, --dockerfile FILE     Set Dockerfile to use (default: $DOCKERFILE)"
    echo "  -p, --port PORT           Set host port to map (default: $PORT)"
    echo ""
    echo "Example:"
    echo "  $0 --port 8080 all        Build and run with port 8080"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -i|--image)
            DOCKER_IMAGE="$2"
            shift 2
            ;;
        -c|--container)
            CONTAINER_NAME="$2"
            shift 2
            ;;
        -f|--dockerfile)
            DOCKERFILE="$2"
            shift 2
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        build|run|stop|logs|status|restart|clean|all)
            COMMAND="$1"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Check if command is provided
if [ -z "$COMMAND" ]; then
    echo "Error: No command specified"
    show_help
    exit 1
fi

# Function to build Docker image
build_image() {
    echo "Building Docker image: $DOCKER_IMAGE from $DOCKERFILE"
    docker build -t "$DOCKER_IMAGE" -f "$DOCKERFILE" .
    echo "Build completed successfully"
}

# Function to run Docker container
run_container() {
    echo "Running container: $CONTAINER_NAME from image: $DOCKER_IMAGE on port: $PORT"
    
    # Check if container already exists
    if docker ps -a --format '{{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
        echo "Container $CONTAINER_NAME already exists. Stopping and removing..."
        docker stop "$CONTAINER_NAME" 2>/dev/null || true
        docker rm "$CONTAINER_NAME" 2>/dev/null || true
    fi
    
    # Create necessary directories
    mkdir -p logs temp_chrome_profile
    
    # Run the container
    docker run -d \
        --name "$CONTAINER_NAME" \
        -p "$PORT:5000" \
        -v "$(pwd)/logs:/app/logs" \
        -v "$(pwd)/.env:/app/.env" \
        -v "$(pwd)/temp_chrome_profile:/app/temp_chrome_profile" \
        --restart unless-stopped \
        "$DOCKER_IMAGE"
    
    echo "Container started. Access the API at http://localhost:$PORT"
    echo "View logs with: $0 logs"
}

# Function to stop container
stop_container() {
    echo "Stopping container: $CONTAINER_NAME"
    docker stop "$CONTAINER_NAME"
    echo "Container stopped"
}

# Function to show container logs
show_logs() {
    echo "Showing logs for container: $CONTAINER_NAME"
    docker logs -f "$CONTAINER_NAME"
}

# Function to check container status
check_status() {
    echo "Checking status of container: $CONTAINER_NAME"
    
    if docker ps --format '{{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
        echo "Container is running"
        docker ps --filter "name=$CONTAINER_NAME" --format "table {{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
        
        # Check health status if available
        HEALTH=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}N/A{{end}}' "$CONTAINER_NAME")
        echo "Health status: $HEALTH"
    else
        echo "Container is not running"
        
        # Check if container exists but is stopped
        if docker ps -a --format '{{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
            echo "Container exists but is stopped"
            docker ps -a --filter "name=$CONTAINER_NAME" --format "table {{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
        else
            echo "Container does not exist"
        fi
    fi
}

# Function to restart container
restart_container() {
    echo "Restarting container: $CONTAINER_NAME"
    docker restart "$CONTAINER_NAME"
    echo "Container restarted"
}

# Function to clean up container and image
clean_up() {
    echo "Cleaning up container and image"
    
    # Stop and remove container if it exists
    if docker ps -a --format '{{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
        echo "Removing container: $CONTAINER_NAME"
        docker stop "$CONTAINER_NAME" 2>/dev/null || true
        docker rm "$CONTAINER_NAME"
    fi
    
    # Remove image if it exists
    if docker images --format '{{.Repository}}' | grep -q "^$DOCKER_IMAGE$"; then
        echo "Removing image: $DOCKER_IMAGE"
        docker rmi "$DOCKER_IMAGE"
    fi
    
    echo "Clean up completed"
}

# Execute command
case $COMMAND in
    build)
        build_image
        ;;
    run)
        run_container
        ;;
    stop)
        stop_container
        ;;
    logs)
        show_logs
        ;;
    status)
        check_status
        ;;
    restart)
        restart_container
        ;;
    clean)
        clean_up
        ;;
    all)
        build_image
        run_container
        ;;
    *)
        echo "Unknown command: $COMMAND"
        show_help
        exit 1
        ;;
esac

exit 0