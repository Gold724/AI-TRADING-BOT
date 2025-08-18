#!/bin/bash

# TradeBot Sentinel - Deployment Automation Script
# This script provides comprehensive deployment automation and CI/CD pipeline management

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOY_ENV=${DEPLOY_ENV:-production}
DEPLOY_TARGET=${DEPLOY_TARGET:-docker}
GIT_BRANCH=${GIT_BRANCH:-main}
DOCKER_REGISTRY=${DOCKER_REGISTRY:-ghcr.io}
DOCKER_IMAGE_NAME=${DOCKER_IMAGE_NAME:-tradebot-sentinel}
KUBE_NAMESPACE=${KUBE_NAMESPACE:-tradebot}
HEALTH_CHECK_TIMEOUT=${HEALTH_CHECK_TIMEOUT:-300}
ROLLBACK_ON_FAILURE=${ROLLBACK_ON_FAILURE:-true}

# Logging
LOG_DIR="/var/log/tradebot"
DEPLOY_LOG="$LOG_DIR/deployment.log"
ERROR_LOG="$LOG_DIR/deployment-errors.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Logging functions
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case "$level" in
        "INFO")
            echo -e "${BLUE}[$timestamp] [INFO] $message${NC}" | tee -a "$DEPLOY_LOG"
            ;;
        "SUCCESS")
            echo -e "${GREEN}[$timestamp] [SUCCESS] $message${NC}" | tee -a "$DEPLOY_LOG"
            ;;
        "WARNING")
            echo -e "${YELLOW}[$timestamp] [WARNING] $message${NC}" | tee -a "$DEPLOY_LOG"
            ;;
        "ERROR")
            echo -e "${RED}[$timestamp] [ERROR] $message${NC}" | tee -a "$DEPLOY_LOG" | tee -a "$ERROR_LOG"
            ;;
        "DEBUG")
            if [[ "${DEBUG:-false}" == "true" ]]; then
                echo -e "${PURPLE}[$timestamp] [DEBUG] $message${NC}" | tee -a "$DEPLOY_LOG"
            fi
            ;;
    esac
}

# Error handling
error_exit() {
    log "ERROR" "$1"
    if [[ "$ROLLBACK_ON_FAILURE" == "true" ]]; then
        log "INFO" "Initiating rollback due to deployment failure..."
        rollback_deployment
    fi
    exit 1
}

# Trap errors
trap 'error_exit "Deployment failed at line $LINENO"' ERR

# Load environment variables
load_environment() {
    log "INFO" "Loading environment configuration for: $DEPLOY_ENV"
    
    # Load base environment
    if [[ -f "$PROJECT_ROOT/.env" ]]; then
        set -a
        source "$PROJECT_ROOT/.env"
        set +a
        log "SUCCESS" "Base environment loaded"
    fi
    
    # Load environment-specific configuration
    local env_file="$PROJECT_ROOT/.env.$DEPLOY_ENV"
    if [[ -f "$env_file" ]]; then
        set -a
        source "$env_file"
        set +a
        log "SUCCESS" "Environment-specific configuration loaded: $DEPLOY_ENV"
    fi
    
    # Validate required variables
    local required_vars=(
        "DOCKER_REGISTRY"
        "DOCKER_IMAGE_NAME"
        "DATABASE_URL"
        "REDIS_URL"
        "BULENOX_USERNAME"
        "BULENOX_PASSWORD"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            error_exit "Required environment variable $var is not set"
        fi
    done
    
    log "SUCCESS" "Environment validation completed"
}

# Check prerequisites
check_prerequisites() {
    log "INFO" "Checking deployment prerequisites..."
    
    local required_tools=()
    
    case "$DEPLOY_TARGET" in
        "docker")
            required_tools+=("docker" "docker-compose")
            ;;
        "kubernetes")
            required_tools+=("kubectl" "helm")
            ;;
        "systemd")
            required_tools+=("systemctl")
            ;;
    esac
    
    required_tools+=("git" "curl" "jq")
    
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            error_exit "Required tool not found: $tool"
        fi
    done
    
    # Check Docker daemon
    if [[ "$DEPLOY_TARGET" == "docker" ]]; then
        if ! docker info &> /dev/null; then
            error_exit "Docker daemon is not running"
        fi
    fi
    
    # Check Kubernetes connection
    if [[ "$DEPLOY_TARGET" == "kubernetes" ]]; then
        if ! kubectl cluster-info &> /dev/null; then
            error_exit "Cannot connect to Kubernetes cluster"
        fi
    fi
    
    log "SUCCESS" "Prerequisites check completed"
}

# Git operations
update_source_code() {
    log "INFO" "Updating source code from Git repository..."
    
    cd "$PROJECT_ROOT"
    
    # Fetch latest changes
    git fetch origin
    
    # Get current commit hash
    local current_commit=$(git rev-parse HEAD)
    local target_commit=$(git rev-parse "origin/$GIT_BRANCH")
    
    if [[ "$current_commit" == "$target_commit" ]]; then
        log "INFO" "Source code is already up to date"
        return 0
    fi
    
    # Stash local changes if any
    if ! git diff-index --quiet HEAD --; then
        log "WARNING" "Local changes detected, stashing..."
        git stash push -m "Auto-stash before deployment $(date)"
    fi
    
    # Checkout target branch
    git checkout "$GIT_BRANCH"
    git pull origin "$GIT_BRANCH"
    
    log "SUCCESS" "Source code updated to commit: $(git rev-parse --short HEAD)"
    
    # Store commit info for rollback
    echo "$current_commit" > "$LOG_DIR/previous_commit.txt"
    echo "$(git rev-parse HEAD)" > "$LOG_DIR/current_commit.txt"
}

# Build application
build_application() {
    log "INFO" "Building TradeBot Sentinel application..."
    
    cd "$PROJECT_ROOT"
    
    case "$DEPLOY_TARGET" in
        "docker")
            build_docker_image
            ;;
        "kubernetes")
            build_docker_image
            push_docker_image
            ;;
        "systemd")
            build_native_application
            ;;
    esac
    
    log "SUCCESS" "Application build completed"
}

# Build Docker image
build_docker_image() {
    log "INFO" "Building Docker image..."
    
    local image_tag="$DOCKER_REGISTRY/$DOCKER_IMAGE_NAME:$(git rev-parse --short HEAD)"
    local latest_tag="$DOCKER_REGISTRY/$DOCKER_IMAGE_NAME:latest"
    
    # Build multi-stage Docker image
    docker build \
        --target production \
        --build-arg BUILD_ENV="$DEPLOY_ENV" \
        --build-arg GIT_COMMIT="$(git rev-parse HEAD)" \
        --build-arg BUILD_DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        -t "$image_tag" \
        -t "$latest_tag" \
        .
    
    # Store image info
    echo "$image_tag" > "$LOG_DIR/current_image.txt"
    
    log "SUCCESS" "Docker image built: $image_tag"
}

# Push Docker image
push_docker_image() {
    log "INFO" "Pushing Docker image to registry..."
    
    local image_tag=$(cat "$LOG_DIR/current_image.txt")
    local latest_tag="$DOCKER_REGISTRY/$DOCKER_IMAGE_NAME:latest"
    
    # Login to registry if credentials are provided
    if [[ -n "${DOCKER_REGISTRY_USERNAME:-}" && -n "${DOCKER_REGISTRY_PASSWORD:-}" ]]; then
        echo "$DOCKER_REGISTRY_PASSWORD" | docker login "$DOCKER_REGISTRY" -u "$DOCKER_REGISTRY_USERNAME" --password-stdin
    fi
    
    # Push images
    docker push "$image_tag"
    docker push "$latest_tag"
    
    log "SUCCESS" "Docker image pushed: $image_tag"
}

# Build native application
build_native_application() {
    log "INFO" "Building native application..."
    
    # Install Python dependencies
    if [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt
    fi
    
    # Install Node.js dependencies for frontend
    if [[ -f "frontend/package.json" ]]; then
        cd frontend
        npm ci
        npm run build
        cd ..
    fi
    
    # Run tests
    if [[ -f "pytest.ini" || -f "setup.cfg" ]]; then
        python -m pytest tests/ -v
    fi
    
    log "SUCCESS" "Native application built successfully"
}

# Deploy application
deploy_application() {
    log "INFO" "Deploying TradeBot Sentinel application..."
    
    case "$DEPLOY_TARGET" in
        "docker")
            deploy_docker
            ;;
        "kubernetes")
            deploy_kubernetes
            ;;
        "systemd")
            deploy_systemd
            ;;
    esac
    
    log "SUCCESS" "Application deployment completed"
}

# Deploy with Docker Compose
deploy_docker() {
    log "INFO" "Deploying with Docker Compose..."
    
    # Stop existing containers
    if docker-compose ps -q | grep -q .; then
        log "INFO" "Stopping existing containers..."
        docker-compose down --remove-orphans
    fi
    
    # Deploy new version
    docker-compose up -d --build
    
    # Wait for services to be ready
    wait_for_health_check "docker"
    
    log "SUCCESS" "Docker deployment completed"
}

# Deploy to Kubernetes
deploy_kubernetes() {
    log "INFO" "Deploying to Kubernetes..."
    
    local image_tag=$(cat "$LOG_DIR/current_image.txt")
    
    # Create namespace if it doesn't exist
    kubectl create namespace "$KUBE_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    # Update image tag in deployment
    kubectl set image deployment/tradebot-app tradebot-app="$image_tag" -n "$KUBE_NAMESPACE"
    
    # Wait for rollout to complete
    kubectl rollout status deployment/tradebot-app -n "$KUBE_NAMESPACE" --timeout=600s
    
    # Wait for services to be ready
    wait_for_health_check "kubernetes"
    
    log "SUCCESS" "Kubernetes deployment completed"
}

# Deploy with systemd
deploy_systemd() {
    log "INFO" "Deploying with systemd..."
    
    # Stop existing service
    if systemctl is-active --quiet tradebot; then
        log "INFO" "Stopping existing TradeBot service..."
        systemctl stop tradebot
    fi
    
    # Copy application files
    rsync -av --delete "$PROJECT_ROOT/" /opt/tradebot/ --exclude='.git' --exclude='logs' --exclude='__pycache__'
    
    # Update systemd service file
    cp "$PROJECT_ROOT/deployment/tradebot.service" /etc/systemd/system/
    systemctl daemon-reload
    
    # Start service
    systemctl enable tradebot
    systemctl start tradebot
    
    # Wait for service to be ready
    wait_for_health_check "systemd"
    
    log "SUCCESS" "Systemd deployment completed"
}

# Health check functions
wait_for_health_check() {
    local deployment_type="$1"
    log "INFO" "Performing health checks..."
    
    local health_url="http://localhost:8000/health"
    local max_attempts=$((HEALTH_CHECK_TIMEOUT / 10))
    local attempt=1
    
    # Adjust health URL based on deployment type
    case "$deployment_type" in
        "kubernetes")
            # Port-forward for health check
            kubectl port-forward service/tradebot-service 8000:80 -n "$KUBE_NAMESPACE" &
            local port_forward_pid=$!
            sleep 5
            ;;
    esac
    
    while [[ $attempt -le $max_attempts ]]; do
        log "DEBUG" "Health check attempt $attempt/$max_attempts"
        
        if curl -sf "$health_url" > /dev/null 2>&1; then
            log "SUCCESS" "Health check passed"
            
            # Clean up port-forward if used
            if [[ -n "${port_forward_pid:-}" ]]; then
                kill $port_forward_pid 2>/dev/null || true
            fi
            
            return 0
        fi
        
        sleep 10
        ((attempt++))
    done
    
    # Clean up port-forward if used
    if [[ -n "${port_forward_pid:-}" ]]; then
        kill $port_forward_pid 2>/dev/null || true
    fi
    
    error_exit "Health check failed after $max_attempts attempts"
}

# Rollback deployment
rollback_deployment() {
    log "WARNING" "Rolling back deployment..."
    
    case "$DEPLOY_TARGET" in
        "docker")
            rollback_docker
            ;;
        "kubernetes")
            rollback_kubernetes
            ;;
        "systemd")
            rollback_systemd
            ;;
    esac
    
    log "SUCCESS" "Rollback completed"
}

# Rollback Docker deployment
rollback_docker() {
    log "INFO" "Rolling back Docker deployment..."
    
    # Get previous image
    local previous_commit=$(cat "$LOG_DIR/previous_commit.txt" 2>/dev/null || echo "")
    if [[ -n "$previous_commit" ]]; then
        local previous_image="$DOCKER_REGISTRY/$DOCKER_IMAGE_NAME:${previous_commit:0:7}"
        
        # Update docker-compose to use previous image
        sed -i "s|image: .*$DOCKER_IMAGE_NAME:.*|image: $previous_image|g" docker-compose.yml
        
        # Redeploy
        docker-compose up -d
    else
        log "WARNING" "No previous commit found, cannot rollback"
    fi
}

# Rollback Kubernetes deployment
rollback_kubernetes() {
    log "INFO" "Rolling back Kubernetes deployment..."
    
    kubectl rollout undo deployment/tradebot-app -n "$KUBE_NAMESPACE"
    kubectl rollout status deployment/tradebot-app -n "$KUBE_NAMESPACE" --timeout=300s
}

# Rollback systemd deployment
rollback_systemd() {
    log "INFO" "Rolling back systemd deployment..."
    
    # Get previous commit
    local previous_commit=$(cat "$LOG_DIR/previous_commit.txt" 2>/dev/null || echo "")
    if [[ -n "$previous_commit" ]]; then
        cd "$PROJECT_ROOT"
        git checkout "$previous_commit"
        
        # Redeploy
        deploy_systemd
    else
        log "WARNING" "No previous commit found, cannot rollback"
    fi
}

# Database migration
run_database_migration() {
    log "INFO" "Running database migrations..."
    
    case "$DEPLOY_TARGET" in
        "docker")
            docker-compose exec -T tradebot-app python manage.py migrate
            ;;
        "kubernetes")
            kubectl exec -n "$KUBE_NAMESPACE" deployment/tradebot-app -- python manage.py migrate
            ;;
        "systemd")
            cd /opt/tradebot
            python manage.py migrate
            ;;
    esac
    
    log "SUCCESS" "Database migrations completed"
}

# Post-deployment tasks
post_deployment_tasks() {
    log "INFO" "Running post-deployment tasks..."
    
    # Clear application cache
    case "$DEPLOY_TARGET" in
        "docker")
            docker-compose exec -T tradebot-app python manage.py clear_cache || true
            ;;
        "kubernetes")
            kubectl exec -n "$KUBE_NAMESPACE" deployment/tradebot-app -- python manage.py clear_cache || true
            ;;
        "systemd")
            cd /opt/tradebot
            python manage.py clear_cache || true
            ;;
    esac
    
    # Warm up application
    sleep 30
    curl -sf "http://localhost:8000/health" > /dev/null || true
    
    # Send deployment notification
    send_deployment_notification "success"
    
    log "SUCCESS" "Post-deployment tasks completed"
}

# Send deployment notification
send_deployment_notification() {
    local status="$1"
    
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        local color="good"
        local title="Deployment Successful"
        
        if [[ "$status" != "success" ]]; then
            color="danger"
            title="Deployment Failed"
        fi
        
        local payload=$(cat << EOF
{
    "attachments": [
        {
            "color": "$color",
            "title": "$title",
            "fields": [
                {
                    "title": "Environment",
                    "value": "$DEPLOY_ENV",
                    "short": true
                },
                {
                    "title": "Target",
                    "value": "$DEPLOY_TARGET",
                    "short": true
                },
                {
                    "title": "Commit",
                    "value": "$(git rev-parse --short HEAD)",
                    "short": true
                },
                {
                    "title": "Timestamp",
                    "value": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
                    "short": true
                }
            ]
        }
    ]
}
EOF
        )
        
        curl -X POST -H 'Content-type: application/json' \
            --data "$payload" \
            "$SLACK_WEBHOOK_URL" || true
    fi
}

# Cleanup old deployments
cleanup_old_deployments() {
    log "INFO" "Cleaning up old deployments..."
    
    case "$DEPLOY_TARGET" in
        "docker")
            # Remove unused images
            docker image prune -f
            docker system prune -f
            ;;
        "kubernetes")
            # Keep last 3 replica sets
            kubectl patch deployment tradebot-app -n "$KUBE_NAMESPACE" -p '{"spec":{"revisionHistoryLimit":3}}'
            ;;
    esac
    
    # Clean up old logs
    find "$LOG_DIR" -name "*.log" -mtime +30 -delete || true
    
    log "SUCCESS" "Cleanup completed"
}

# Show deployment status
show_deployment_status() {
    echo -e "${CYAN}=== TradeBot Sentinel Deployment Status ===${NC}"
    echo
    
    case "$DEPLOY_TARGET" in
        "docker")
            echo -e "${YELLOW}Docker Containers:${NC}"
            docker-compose ps
            echo
            ;;
        "kubernetes")
            echo -e "${YELLOW}Kubernetes Pods:${NC}"
            kubectl get pods -n "$KUBE_NAMESPACE"
            echo
            echo -e "${YELLOW}Kubernetes Services:${NC}"
            kubectl get services -n "$KUBE_NAMESPACE"
            echo
            ;;
        "systemd")
            echo -e "${YELLOW}Systemd Services:${NC}"
            systemctl status tradebot --no-pager -l
            echo
            ;;
    esac
    
    echo -e "${YELLOW}Recent Deployment Logs:${NC}"
    tail -20 "$DEPLOY_LOG" 2>/dev/null || echo "No deployment logs found"
}

# Show help
show_help() {
    cat << EOF
TradeBot Sentinel Deployment Automation

Usage: $0 <command> [options]

Commands:
  deploy                    Full deployment pipeline
  build                     Build application only
  rollback                  Rollback to previous version
  status                    Show deployment status
  migrate                   Run database migrations
  cleanup                   Clean up old deployments
  help                      Show this help message

Environment Variables:
  DEPLOY_ENV               Deployment environment (default: production)
  DEPLOY_TARGET            Deployment target: docker|kubernetes|systemd (default: docker)
  GIT_BRANCH              Git branch to deploy (default: main)
  DOCKER_REGISTRY         Docker registry URL
  DOCKER_IMAGE_NAME       Docker image name
  KUBE_NAMESPACE          Kubernetes namespace (default: tradebot)
  HEALTH_CHECK_TIMEOUT    Health check timeout in seconds (default: 300)
  ROLLBACK_ON_FAILURE     Auto-rollback on failure (default: true)
  DEBUG                   Enable debug logging (default: false)

Examples:
  $0 deploy                                    # Deploy to production
  DEPLOY_ENV=staging $0 deploy                 # Deploy to staging
  DEPLOY_TARGET=kubernetes $0 deploy           # Deploy to Kubernetes
  DEBUG=true $0 deploy                         # Deploy with debug logging

EOF
}

# Main deployment pipeline
main_deploy() {
    log "SUCCESS" "Starting TradeBot Sentinel deployment pipeline..."
    log "INFO" "Environment: $DEPLOY_ENV, Target: $DEPLOY_TARGET, Branch: $GIT_BRANCH"
    
    load_environment
    check_prerequisites
    update_source_code
    build_application
    run_database_migration
    deploy_application
    post_deployment_tasks
    cleanup_old_deployments
    
    log "SUCCESS" "Deployment pipeline completed successfully!"
    show_deployment_status
}

# Main function
main() {
    case "${1:-help}" in
        "deploy")
            main_deploy
            ;;
        "build")
            load_environment
            check_prerequisites
            update_source_code
            build_application
            ;;
        "rollback")
            load_environment
            rollback_deployment
            ;;
        "status")
            show_deployment_status
            ;;
        "migrate")
            load_environment
            run_database_migration
            ;;
        "cleanup")
            cleanup_old_deployments
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            echo -e "${RED}Unknown command: $1${NC}"
            show_help
            exit 1
            ;;
    esac
}

# Trap cleanup
trap 'log "INFO" "Deployment script interrupted"' INT TERM

# Run main function
main "$@"