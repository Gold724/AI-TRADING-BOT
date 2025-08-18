#!/bin/bash
# Kubernetes Deployment Script for TradeBot Sentinel
# Provides automated deployment with auto-scaling and health checks

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="tradebot"
APP_NAME="tradebot-sentinel"
DOCKER_IMAGE="tradebot-sentinel:latest"
KUBECTL_TIMEOUT="300s"
HEALTH_CHECK_RETRIES=30
HEALTH_CHECK_DELAY=10

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    # Check Docker (for building images)
    if ! command -v docker &> /dev/null; then
        log_warning "Docker is not installed. Assuming image is already built."
    fi
    
    # Check required files
    local required_files=(
        "tradebot-config.yaml"
        "tradebot-deployment.yaml"
        "tradebot-service.yaml"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            log_error "Required file not found: $file"
            exit 1
        fi
    done
    
    log_success "Prerequisites check passed"
}

build_docker_image() {
    if command -v docker &> /dev/null; then
        log_info "Building Docker image..."
        
        # Check if Dockerfile exists
        if [[ -f "../Dockerfile.cloud" ]]; then
            docker build -f ../Dockerfile.cloud -t "$DOCKER_IMAGE" ..
        elif [[ -f "../Dockerfile" ]]; then
            docker build -f ../Dockerfile -t "$DOCKER_IMAGE" ..
        else
            log_warning "No Dockerfile found. Assuming image is already built."
            return
        fi
        
        log_success "Docker image built successfully"
    else
        log_warning "Docker not available. Skipping image build."
    fi
}

create_namespace() {
    log_info "Creating namespace: $NAMESPACE"
    
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_warning "Namespace $NAMESPACE already exists"
    else
        kubectl create namespace "$NAMESPACE"
        log_success "Namespace $NAMESPACE created"
    fi
    
    # Label namespace for monitoring
    kubectl label namespace "$NAMESPACE" name="$NAMESPACE" --overwrite
    kubectl label namespace "$NAMESPACE" component="trading-bot" --overwrite
}

setup_secrets() {
    log_info "Setting up secrets and configurations..."
    
    # Check if .env file exists for secret generation
    if [[ -f "../.env" ]]; then
        log_info "Found .env file. Generating secrets from environment variables..."
        
        # Create a temporary secret file
        cat > temp-secrets.yaml << EOF
apiVersion: v1
kind: Secret
metadata:
  name: tradebot-secrets
  namespace: $NAMESPACE
type: Opaque
stringData:
EOF
        
        # Add environment variables to secret
        while IFS='=' read -r key value; do
            # Skip comments and empty lines
            [[ $key =~ ^#.*$ ]] && continue
            [[ -z $key ]] && continue
            
            # Remove quotes from value
            value=$(echo "$value" | sed 's/^"\|"$//g')
            echo "  $key: \"$value\"" >> temp-secrets.yaml
        done < ../.env
        
        # Apply the generated secret
        kubectl apply -f temp-secrets.yaml
        rm temp-secrets.yaml
        
        log_success "Secrets created from .env file"
    else
        log_warning "No .env file found. Using default secrets from tradebot-config.yaml"
    fi
}

deploy_resources() {
    log_info "Deploying Kubernetes resources..."
    
    # Apply configurations in order
    local resources=(
        "tradebot-config.yaml"
        "tradebot-deployment.yaml"
        "tradebot-service.yaml"
    )
    
    for resource in "${resources[@]}"; do
        log_info "Applying $resource..."
        kubectl apply -f "$resource" --timeout="$KUBECTL_TIMEOUT"
        log_success "Applied $resource"
    done
}

wait_for_deployment() {
    log_info "Waiting for deployment to be ready..."
    
    # Wait for deployment to be available
    kubectl wait --for=condition=available deployment/$APP_NAME \
        --namespace="$NAMESPACE" \
        --timeout="$KUBECTL_TIMEOUT"
    
    # Wait for pods to be ready
    kubectl wait --for=condition=ready pod \
        --selector=app=$APP_NAME \
        --namespace="$NAMESPACE" \
        --timeout="$KUBECTL_TIMEOUT"
    
    log_success "Deployment is ready"
}

perform_health_checks() {
    log_info "Performing health checks..."
    
    local retries=0
    local max_retries=$HEALTH_CHECK_RETRIES
    
    while [[ $retries -lt $max_retries ]]; do
        # Get pod name
        local pod_name=$(kubectl get pods -n "$NAMESPACE" -l app="$APP_NAME" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
        
        if [[ -n "$pod_name" ]]; then
            # Check health endpoint
            if kubectl exec -n "$NAMESPACE" "$pod_name" -- curl -f http://localhost:8001/health/ready &> /dev/null; then
                log_success "Health check passed"
                return 0
            fi
        fi
        
        retries=$((retries + 1))
        log_info "Health check attempt $retries/$max_retries failed. Retrying in ${HEALTH_CHECK_DELAY}s..."
        sleep $HEALTH_CHECK_DELAY
    done
    
    log_error "Health checks failed after $max_retries attempts"
    return 1
}

setup_monitoring() {
    log_info "Setting up monitoring resources..."
    
    # Check if Prometheus Operator is installed
    if kubectl get crd servicemonitors.monitoring.coreos.com &> /dev/null; then
        log_info "Prometheus Operator detected. ServiceMonitor will be created."
    else
        log_warning "Prometheus Operator not found. ServiceMonitor will not work without it."
    fi
    
    # Apply monitoring configurations if they exist
    if [[ -f "monitoring-config.yaml" ]]; then
        kubectl apply -f monitoring-config.yaml
        log_success "Monitoring configuration applied"
    fi
}

setup_ingress() {
    log_info "Setting up ingress..."
    
    # Check if ingress controller is available
    if kubectl get ingressclass nginx &> /dev/null; then
        log_info "Nginx ingress controller detected"
    elif kubectl get ingressclass traefik &> /dev/null; then
        log_info "Traefik ingress controller detected"
    else
        log_warning "No ingress controller detected. Ingress may not work."
    fi
    
    # Check if cert-manager is available for SSL
    if kubectl get crd certificates.cert-manager.io &> /dev/null; then
        log_info "cert-manager detected. SSL certificates will be automatically managed."
    else
        log_warning "cert-manager not found. SSL certificates will need manual setup."
    fi
}

show_deployment_info() {
    log_info "Deployment Information:"
    echo
    
    # Show deployment status
    echo "📊 Deployment Status:"
    kubectl get deployment -n "$NAMESPACE" -l app="$APP_NAME"
    echo
    
    # Show pods
    echo "🚀 Pods:"
    kubectl get pods -n "$NAMESPACE" -l app="$APP_NAME" -o wide
    echo
    
    # Show services
    echo "🌐 Services:"
    kubectl get services -n "$NAMESPACE" -l app="$APP_NAME"
    echo
    
    # Show HPA status
    echo "📈 Horizontal Pod Autoscaler:"
    kubectl get hpa -n "$NAMESPACE" -l app="$APP_NAME" 2>/dev/null || echo "HPA not found"
    echo
    
    # Show ingress
    echo "🔗 Ingress:"
    kubectl get ingress -n "$NAMESPACE" -l app="$APP_NAME" 2>/dev/null || echo "Ingress not found"
    echo
    
    # Show useful commands
    echo "📋 Useful Commands:"
    echo "  View logs:        kubectl logs -n $NAMESPACE -l app=$APP_NAME -f"
    echo "  Scale deployment: kubectl scale deployment/$APP_NAME --replicas=3 -n $NAMESPACE"
    echo "  Port forward:     kubectl port-forward -n $NAMESPACE svc/$APP_NAME-service 8000:8000"
    echo "  Health check:     kubectl exec -n $NAMESPACE deployment/$APP_NAME -- curl http://localhost:8001/health"
    echo "  Delete:           kubectl delete namespace $NAMESPACE"
    echo
}

cleanup_deployment() {
    log_info "Cleaning up deployment..."
    
    # Delete namespace (this will delete all resources in it)
    kubectl delete namespace "$NAMESPACE" --timeout="$KUBECTL_TIMEOUT" || true
    
    log_success "Cleanup completed"
}

scale_deployment() {
    local replicas=${1:-2}
    log_info "Scaling deployment to $replicas replicas..."
    
    kubectl scale deployment/$APP_NAME --replicas="$replicas" -n "$NAMESPACE"
    kubectl wait --for=condition=available deployment/$APP_NAME \
        --namespace="$NAMESPACE" \
        --timeout="$KUBECTL_TIMEOUT"
    
    log_success "Deployment scaled to $replicas replicas"
}

show_logs() {
    log_info "Showing application logs..."
    kubectl logs -n "$NAMESPACE" -l app="$APP_NAME" -f --tail=100
}

show_metrics() {
    log_info "Showing deployment metrics..."
    
    # Get pod metrics if metrics-server is available
    if kubectl top pods -n "$NAMESPACE" &> /dev/null; then
        echo "📊 Pod Resource Usage:"
        kubectl top pods -n "$NAMESPACE" -l app="$APP_NAME"
        echo
    fi
    
    # Show HPA metrics
    if kubectl get hpa -n "$NAMESPACE" -l app="$APP_NAME" &> /dev/null; then
        echo "📈 HPA Metrics:"
        kubectl describe hpa -n "$NAMESPACE" -l app="$APP_NAME"
        echo
    fi
}

# Main execution
main() {
    local action=${1:-deploy}
    
    case $action in
        "deploy")
            log_info "Starting TradeBot Sentinel deployment..."
            check_prerequisites
            build_docker_image
            create_namespace
            setup_secrets
            deploy_resources
            wait_for_deployment
            perform_health_checks
            setup_monitoring
            setup_ingress
            show_deployment_info
            log_success "Deployment completed successfully!"
            ;;
        
        "cleanup")
            cleanup_deployment
            ;;
        
        "scale")
            local replicas=${2:-2}
            scale_deployment "$replicas"
            ;;
        
        "logs")
            show_logs
            ;;
        
        "status")
            show_deployment_info
            ;;
        
        "metrics")
            show_metrics
            ;;
        
        "health")
            perform_health_checks
            ;;
        
        "restart")
            log_info "Restarting deployment..."
            kubectl rollout restart deployment/$APP_NAME -n "$NAMESPACE"
            wait_for_deployment
            perform_health_checks
            log_success "Deployment restarted successfully"
            ;;
        
        "update")
            log_info "Updating deployment..."
            build_docker_image
            kubectl set image deployment/$APP_NAME tradebot-app="$DOCKER_IMAGE" -n "$NAMESPACE"
            kubectl rollout status deployment/$APP_NAME -n "$NAMESPACE" --timeout="$KUBECTL_TIMEOUT"
            perform_health_checks
            log_success "Deployment updated successfully"
            ;;
        
        "help")
            echo "Usage: $0 [action] [options]"
            echo
            echo "Actions:"
            echo "  deploy          Deploy the TradeBot Sentinel (default)"
            echo "  cleanup         Remove all resources"
            echo "  scale [N]       Scale deployment to N replicas (default: 2)"
            echo "  logs            Show application logs"
            echo "  status          Show deployment status"
            echo "  metrics         Show resource metrics"
            echo "  health          Perform health checks"
            echo "  restart         Restart the deployment"
            echo "  update          Update deployment with new image"
            echo "  help            Show this help message"
            echo
            ;;
        
        *)
            log_error "Unknown action: $action"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Execute main function with all arguments
main "$@"