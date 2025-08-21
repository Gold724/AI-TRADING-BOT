#!/bin/bash
"""
AI Trading Sentinel - Multi-Account Scaling Deployment Script
Automated deployment of containerized multi-account trading infrastructure
with Docker, Kubernetes, and cloud provider support.
"""

set -euo pipefail

# =============================================================================
# CONFIGURATION
# =============================================================================

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/var/log/trading-sentinel-scaling-deploy.log"
BACKUP_DIR="/var/backups/trading-sentinel-scaling"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Deployment configuration
DEPLOYMENT_MODE="${DEPLOYMENT_MODE:-docker}"  # docker, kubernetes, docker-swarm
CLOUD_PROVIDER="${CLOUD_PROVIDER:-none}"      # aws, gcp, azure, digitalocean, none
ENVIRONMENT="${ENVIRONMENT:-production}"       # development, staging, production
SCALE_FACTOR="${SCALE_FACTOR:-3}"             # Number of worker nodes
MAX_ACCOUNTS="${MAX_ACCOUNTS:-50}"            # Maximum concurrent accounts

# Resource configuration
DOCKER_REGISTRY="${DOCKER_REGISTRY:-localhost:5000}"
KUBERNETES_NAMESPACE="${KUBERNETES_NAMESPACE:-trading-sentinel}"
REDIS_CLUSTER_SIZE="${REDIS_CLUSTER_SIZE:-3}"
POSTGRESQL_REPLICAS="${POSTGRESQL_REPLICAS:-2}"

# Security configuration
SSL_ENABLED="${SSL_ENABLED:-true}"
VAULT_ENABLED="${VAULT_ENABLED:-false}"
RBAC_ENABLED="${RBAC_ENABLED:-true}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

log_info() {
    log "INFO" "$*"
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_warn() {
    log "WARN" "$*"
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    log "ERROR" "$*"
    echo -e "${RED}[ERROR]${NC} $*"
}

log_success() {
    log "SUCCESS" "$*"
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

check_system_requirements() {
    log_info "Checking system requirements..."
    
    # Check OS
    if ! command -v lsb_release &> /dev/null; then
        log_error "lsb_release not found. Please install lsb-release package"
        exit 1
    fi
    
    local os_name=$(lsb_release -si)
    local os_version=$(lsb_release -sr)
    
    if [[ "$os_name" != "Ubuntu" ]] || [[ "${os_version%%.*}" -lt 20 ]]; then
        log_error "This script requires Ubuntu 20.04 or later"
        exit 1
    fi
    
    # Check resources
    local total_memory=$(free -m | awk 'NR==2{printf "%.0f", $2}')
    local cpu_cores=$(nproc)
    local disk_space=$(df / | awk 'NR==2 {print $4}')
    
    if [[ $total_memory -lt 8192 ]]; then
        log_warn "Recommended minimum 8GB RAM, found ${total_memory}MB"
    fi
    
    if [[ $cpu_cores -lt 4 ]]; then
        log_warn "Recommended minimum 4 CPU cores, found $cpu_cores"
    fi
    
    if [[ $disk_space -lt 52428800 ]]; then  # 50GB in KB
        log_warn "Recommended minimum 50GB disk space"
    fi
    
    log_success "System requirements check completed"
}

create_backup() {
    log_info "Creating backup of existing configuration..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup existing Docker configurations
    if [[ -d "/etc/docker" ]]; then
        cp -r /etc/docker "$BACKUP_DIR/docker_$TIMESTAMP" || true
    fi
    
    # Backup existing Kubernetes configurations
    if [[ -d "/etc/kubernetes" ]]; then
        cp -r /etc/kubernetes "$BACKUP_DIR/kubernetes_$TIMESTAMP" || true
    fi
    
    # Backup existing application configurations
    if [[ -d "/opt/trading-sentinel" ]]; then
        cp -r /opt/trading-sentinel "$BACKUP_DIR/app_$TIMESTAMP" || true
    fi
    
    log_success "Backup created in $BACKUP_DIR"
}

# =============================================================================
# DOCKER INSTALLATION AND CONFIGURATION
# =============================================================================

install_docker() {
    log_info "Installing Docker..."
    
    # Remove old versions
    apt-get remove -y docker docker-engine docker.io containerd runc || true
    
    # Update package index
    apt-get update
    
    # Install dependencies
    apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    # Add Docker's official GPG key
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Add Docker repository
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker Engine
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Start and enable Docker
    systemctl start docker
    systemctl enable docker
    
    # Add current user to docker group
    usermod -aG docker $SUDO_USER || true
    
    log_success "Docker installed successfully"
}

configure_docker() {
    log_info "Configuring Docker for production..."
    
    # Create Docker daemon configuration
    cat > /etc/docker/daemon.json << EOF
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    },
    "storage-driver": "overlay2",
    "storage-opts": [
        "overlay2.override_kernel_check=true"
    ],
    "exec-opts": ["native.cgroupdriver=systemd"],
    "live-restore": true,
    "userland-proxy": false,
    "experimental": false,
    "metrics-addr": "127.0.0.1:9323",
    "default-ulimits": {
        "nofile": {
            "Name": "nofile",
            "Hard": 64000,
            "Soft": 64000
        }
    },
    "max-concurrent-downloads": 10,
    "max-concurrent-uploads": 5,
    "default-shm-size": "64M"
}
EOF
    
    # Configure Docker systemd service
    mkdir -p /etc/systemd/system/docker.service.d
    cat > /etc/systemd/system/docker.service.d/override.conf << EOF
[Service]
ExecStart=
ExecStart=/usr/bin/dockerd -H fd:// --containerd=/run/containerd/containerd.sock
LimitNOFILE=1048576
LimitNPROC=1048576
LimitCORE=infinity
TasksMax=infinity
Delegate=yes
KillMode=process
Restart=always
RestartSec=5
EOF
    
    # Reload and restart Docker
    systemctl daemon-reload
    systemctl restart docker
    
    # Verify Docker installation
    docker --version
    docker compose version
    
    log_success "Docker configured successfully"
}

setup_docker_registry() {
    log_info "Setting up Docker registry..."
    
    if [[ "$DOCKER_REGISTRY" == "localhost:5000" ]]; then
        # Setup local registry
        docker run -d \
            --name registry \
            --restart=always \
            -p 5000:5000 \
            -v /var/lib/registry:/var/lib/registry \
            registry:2
        
        # Configure Docker to use insecure registry
        if ! grep -q "insecure-registries" /etc/docker/daemon.json; then
            jq '. + {"insecure-registries": ["localhost:5000"]}' /etc/docker/daemon.json > /tmp/daemon.json
            mv /tmp/daemon.json /etc/docker/daemon.json
            systemctl restart docker
        fi
    fi
    
    log_success "Docker registry configured"
}

# =============================================================================
# KUBERNETES INSTALLATION AND CONFIGURATION
# =============================================================================

install_kubernetes() {
    if [[ "$DEPLOYMENT_MODE" != "kubernetes" ]]; then
        return 0
    fi
    
    log_info "Installing Kubernetes..."
    
    # Disable swap
    swapoff -a
    sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab
    
    # Load required kernel modules
    cat > /etc/modules-load.d/k8s.conf << EOF
br_netfilter
ip_vs
ip_vs_rr
ip_vs_wrr
ip_vs_sh
nf_conntrack
EOF
    
    modprobe br_netfilter
    modprobe ip_vs
    modprobe ip_vs_rr
    modprobe ip_vs_wrr
    modprobe ip_vs_sh
    modprobe nf_conntrack
    
    # Configure sysctl
    cat > /etc/sysctl.d/k8s.conf << EOF
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
vm.overcommit_memory = 1
kernel.panic = 10
kernel.panic_on_oops = 1
EOF
    
    sysctl --system
    
    # Install kubeadm, kubelet, kubectl
    curl -fsSLo /usr/share/keyrings/kubernetes-archive-keyring.gpg https://packages.cloud.google.com/apt/doc/apt-key.gpg
    echo "deb [signed-by=/usr/share/keyrings/kubernetes-archive-keyring.gpg] https://apt.kubernetes.io/ kubernetes-xenial main" | tee /etc/apt/sources.list.d/kubernetes.list
    
    apt-get update
    apt-get install -y kubelet kubeadm kubectl
    apt-mark hold kubelet kubeadm kubectl
    
    # Configure kubelet
    cat > /etc/default/kubelet << EOF
KUBELET_EXTRA_ARGS=--cgroup-driver=systemd --container-runtime=docker
EOF
    
    systemctl enable kubelet
    
    log_success "Kubernetes installed successfully"
}

setup_kubernetes_cluster() {
    if [[ "$DEPLOYMENT_MODE" != "kubernetes" ]]; then
        return 0
    fi
    
    log_info "Setting up Kubernetes cluster..."
    
    # Initialize cluster
    kubeadm init \
        --pod-network-cidr=10.244.0.0/16 \
        --service-cidr=10.96.0.0/12 \
        --apiserver-advertise-address=$(hostname -I | awk '{print $1}') \
        --node-name=$(hostname)
    
    # Configure kubectl for root
    mkdir -p /root/.kube
    cp -i /etc/kubernetes/admin.conf /root/.kube/config
    chown root:root /root/.kube/config
    
    # Configure kubectl for regular user
    if [[ -n "$SUDO_USER" ]]; then
        mkdir -p /home/$SUDO_USER/.kube
        cp -i /etc/kubernetes/admin.conf /home/$SUDO_USER/.kube/config
        chown $SUDO_USER:$SUDO_USER /home/$SUDO_USER/.kube/config
    fi
    
    # Install Flannel CNI
    kubectl apply -f https://raw.githubusercontent.com/flannel-io/flannel/master/Documentation/kube-flannel.yml
    
    # Remove taint from master node (for single-node setup)
    kubectl taint nodes --all node-role.kubernetes.io/master- || true
    kubectl taint nodes --all node-role.kubernetes.io/control-plane- || true
    
    # Create namespace
    kubectl create namespace "$KUBERNETES_NAMESPACE" || true
    
    log_success "Kubernetes cluster configured"
}

install_helm() {
    if [[ "$DEPLOYMENT_MODE" != "kubernetes" ]]; then
        return 0
    fi
    
    log_info "Installing Helm..."
    
    curl https://baltocdn.com/helm/signing.asc | gpg --dearmor | tee /usr/share/keyrings/helm.gpg > /dev/null
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/helm.gpg] https://baltocdn.com/helm/stable/debian/ all main" | tee /etc/apt/sources.list.d/helm-stable-debian.list
    
    apt-get update
    apt-get install -y helm
    
    # Add common Helm repositories
    helm repo add stable https://charts.helm.sh/stable
    helm repo add bitnami https://charts.bitnami.com/bitnami
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo update
    
    log_success "Helm installed successfully"
}

# =============================================================================
# APPLICATION DEPLOYMENT
# =============================================================================

setup_application_directories() {
    log_info "Setting up application directories..."
    
    # Create main application directory
    mkdir -p /opt/trading-sentinel
    mkdir -p /opt/trading-sentinel/config
    mkdir -p /opt/trading-sentinel/data
    mkdir -p /opt/trading-sentinel/logs
    mkdir -p /opt/trading-sentinel/scripts
    mkdir -p /opt/trading-sentinel/docker
    mkdir -p /opt/trading-sentinel/kubernetes
    
    # Create data directories
    mkdir -p /var/lib/trading-sentinel
    mkdir -p /var/lib/trading-sentinel/accounts
    mkdir -p /var/lib/trading-sentinel/redis
    mkdir -p /var/lib/trading-sentinel/postgresql
    
    # Create log directories
    mkdir -p /var/log/trading-sentinel
    mkdir -p /var/log/trading-sentinel/accounts
    
    # Set permissions
    chown -R 1000:1000 /opt/trading-sentinel
    chown -R 1000:1000 /var/lib/trading-sentinel
    chown -R 1000:1000 /var/log/trading-sentinel
    
    log_success "Application directories created"
}

copy_application_files() {
    log_info "Copying application files..."
    
    # Copy scaling architecture files
    cp "$SCRIPT_DIR/multi-account-architecture.py" /opt/trading-sentinel/
    cp "$SCRIPT_DIR/docker-orchestration.py" /opt/trading-sentinel/
    
    # Copy main application files
    if [[ -f "$PROJECT_ROOT/main.py" ]]; then
        cp "$PROJECT_ROOT/main.py" /opt/trading-sentinel/
    fi
    
    if [[ -f "$PROJECT_ROOT/requirements.txt" ]]; then
        cp "$PROJECT_ROOT/requirements.txt" /opt/trading-sentinel/
    fi
    
    # Copy configuration files
    if [[ -d "$PROJECT_ROOT/config" ]]; then
        cp -r "$PROJECT_ROOT/config"/* /opt/trading-sentinel/config/
    fi
    
    # Copy source code
    if [[ -d "$PROJECT_ROOT/src" ]]; then
        cp -r "$PROJECT_ROOT/src" /opt/trading-sentinel/
    fi
    
    log_success "Application files copied"
}

create_docker_configurations() {
    log_info "Creating Docker configurations..."
    
    # Create main Dockerfile
    cat > /opt/trading-sentinel/docker/Dockerfile << 'EOF'
# AI Trading Sentinel - Production Dockerfile
FROM python:3.11-slim-bullseye

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg2 \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for Playwright
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Create non-root user
RUN groupadd -r trading && useradd -r -g trading -d /app -s /bin/bash trading

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy application code
COPY . .

# Set ownership
RUN chown -R trading:trading /app

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/cache /app/config \
    && chown -R trading:trading /app/logs /app/data /app/cache /app/config

# Switch to non-root user
USER trading

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)"

# Default command
CMD ["python", "main.py"]
EOF

    # Create Docker Compose configuration
    cat > /opt/trading-sentinel/docker/docker-compose.yml << EOF
version: '3.8'

services:
  # Redis Cluster
  redis-master:
    image: redis:7-alpine
    container_name: trading-redis-master
    command: redis-server --appendonly yes --replica-read-only no
    ports:
      - "6379:6379"
    volumes:
      - redis-master-data:/data
    networks:
      - trading-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis-replica-1:
    image: redis:7-alpine
    container_name: trading-redis-replica-1
    command: redis-server --appendonly yes --replicaof redis-master 6379
    depends_on:
      - redis-master
    volumes:
      - redis-replica-1-data:/data
    networks:
      - trading-network
    restart: unless-stopped

  redis-replica-2:
    image: redis:7-alpine
    container_name: trading-redis-replica-2
    command: redis-server --appendonly yes --replicaof redis-master 6379
    depends_on:
      - redis-master
    volumes:
      - redis-replica-2-data:/data
    networks:
      - trading-network
    restart: unless-stopped

  # PostgreSQL Primary
  postgresql-primary:
    image: postgres:15-alpine
    container_name: trading-postgresql-primary
    environment:
      POSTGRES_DB: trading_sentinel
      POSTGRES_USER: trading_user
      POSTGRES_PASSWORD: \${POSTGRES_PASSWORD}
      POSTGRES_REPLICATION_USER: replicator
      POSTGRES_REPLICATION_PASSWORD: \${POSTGRES_REPLICATION_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgresql-primary-data:/var/lib/postgresql/data
      - ./postgresql/postgresql.conf:/etc/postgresql/postgresql.conf
      - ./postgresql/pg_hba.conf:/etc/postgresql/pg_hba.conf
    networks:
      - trading-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U trading_user -d trading_sentinel"]
      interval: 30s
      timeout: 10s
      retries: 3

  # PostgreSQL Replica
  postgresql-replica:
    image: postgres:15-alpine
    container_name: trading-postgresql-replica
    environment:
      POSTGRES_DB: trading_sentinel
      POSTGRES_USER: trading_user
      POSTGRES_PASSWORD: \${POSTGRES_PASSWORD}
      POSTGRES_MASTER_SERVICE: postgresql-primary
    depends_on:
      - postgresql-primary
    volumes:
      - postgresql-replica-data:/var/lib/postgresql/data
    networks:
      - trading-network
    restart: unless-stopped

  # Trading Sentinel Orchestrator
  trading-orchestrator:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    container_name: trading-orchestrator
    environment:
      - DEPLOYMENT_MODE=docker
      - DATABASE_URL=postgresql://trading_user:\${POSTGRES_PASSWORD}@postgresql-primary:5432/trading_sentinel
      - REDIS_URL=redis://redis-master:6379/0
      - MAX_ACCOUNTS=$MAX_ACCOUNTS
      - LOG_LEVEL=INFO
    depends_on:
      - redis-master
      - postgresql-primary
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /opt/trading-sentinel/data:/app/data
      - /opt/trading-sentinel/logs:/app/logs
      - /opt/trading-sentinel/config:/app/config
    networks:
      - trading-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Nginx Load Balancer
  nginx:
    image: nginx:alpine
    container_name: trading-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - trading-orchestrator
    networks:
      - trading-network
    restart: unless-stopped

  # Prometheus Monitoring
  prometheus:
    image: prom/prometheus:latest
    container_name: trading-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    networks:
      - trading-network
    restart: unless-stopped

  # Grafana Dashboard
  grafana:
    image: grafana/grafana:latest
    container_name: trading-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=\${GRAFANA_PASSWORD}
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./grafana/datasources:/etc/grafana/provisioning/datasources
    depends_on:
      - prometheus
    networks:
      - trading-network
    restart: unless-stopped

volumes:
  redis-master-data:
  redis-replica-1-data:
  redis-replica-2-data:
  postgresql-primary-data:
  postgresql-replica-data:
  prometheus-data:
  grafana-data:

networks:
  trading-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
EOF

    # Create environment file template
    cat > /opt/trading-sentinel/docker/.env.template << EOF
# Database Configuration
POSTGRES_PASSWORD=your_secure_postgres_password
POSTGRES_REPLICATION_PASSWORD=your_secure_replication_password

# Monitoring Configuration
GRAFANA_PASSWORD=your_secure_grafana_password

# Application Configuration
MAX_ACCOUNTS=$MAX_ACCOUNTS
ENVIRONMENT=$ENVIRONMENT
LOG_LEVEL=INFO

# Security Configuration
SSL_ENABLED=$SSL_ENABLED
RBAC_ENABLED=$RBAC_ENABLED

# Cloud Configuration
CLOUD_PROVIDER=$CLOUD_PROVIDER
DOCKER_REGISTRY=$DOCKER_REGISTRY
EOF

    log_success "Docker configurations created"
}

create_kubernetes_configurations() {
    if [[ "$DEPLOYMENT_MODE" != "kubernetes" ]]; then
        return 0
    fi
    
    log_info "Creating Kubernetes configurations..."
    
    # Create namespace configuration
    cat > /opt/trading-sentinel/kubernetes/namespace.yaml << EOF
apiVersion: v1
kind: Namespace
metadata:
  name: $KUBERNETES_NAMESPACE
  labels:
    name: $KUBERNETES_NAMESPACE
    app: trading-sentinel
EOF

    # Create ConfigMap
    cat > /opt/trading-sentinel/kubernetes/configmap.yaml << EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: trading-sentinel-config
  namespace: $KUBERNETES_NAMESPACE
data:
  MAX_ACCOUNTS: "$MAX_ACCOUNTS"
  ENVIRONMENT: "$ENVIRONMENT"
  LOG_LEVEL: "INFO"
  DEPLOYMENT_MODE: "kubernetes"
  KUBERNETES_NAMESPACE: "$KUBERNETES_NAMESPACE"
EOF

    # Create Secret
    cat > /opt/trading-sentinel/kubernetes/secret.yaml << EOF
apiVersion: v1
kind: Secret
metadata:
  name: trading-sentinel-secret
  namespace: $KUBERNETES_NAMESPACE
type: Opaque
data:
  postgres-password: $(echo -n "your_secure_postgres_password" | base64)
  redis-password: $(echo -n "your_secure_redis_password" | base64)
  grafana-password: $(echo -n "your_secure_grafana_password" | base64)
EOF

    # Create PostgreSQL deployment
    cat > /opt/trading-sentinel/kubernetes/postgresql.yaml << EOF
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgresql
  namespace: $KUBERNETES_NAMESPACE
spec:
  serviceName: postgresql
  replicas: $POSTGRESQL_REPLICAS
  selector:
    matchLabels:
      app: postgresql
  template:
    metadata:
      labels:
        app: postgresql
    spec:
      containers:
      - name: postgresql
        image: postgres:15-alpine
        env:
        - name: POSTGRES_DB
          value: trading_sentinel
        - name: POSTGRES_USER
          value: trading_user
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: trading-sentinel-secret
              key: postgres-password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgresql-data
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
  volumeClaimTemplates:
  - metadata:
      name: postgresql-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 20Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgresql
  namespace: $KUBERNETES_NAMESPACE
spec:
  selector:
    app: postgresql
  ports:
  - port: 5432
    targetPort: 5432
  clusterIP: None
EOF

    # Create Redis deployment
    cat > /opt/trading-sentinel/kubernetes/redis.yaml << EOF
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis
  namespace: $KUBERNETES_NAMESPACE
spec:
  serviceName: redis
  replicas: $REDIS_CLUSTER_SIZE
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        command: ["redis-server", "--appendonly", "yes"]
        ports:
        - containerPort: 6379
        volumeMounts:
        - name: redis-data
          mountPath: /data
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "1Gi"
            cpu: "500m"
  volumeClaimTemplates:
  - metadata:
      name: redis-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: $KUBERNETES_NAMESPACE
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
  clusterIP: None
EOF

    # Create Trading Sentinel deployment
    cat > /opt/trading-sentinel/kubernetes/trading-sentinel.yaml << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: trading-sentinel
  namespace: $KUBERNETES_NAMESPACE
spec:
  replicas: $SCALE_FACTOR
  selector:
    matchLabels:
      app: trading-sentinel
  template:
    metadata:
      labels:
        app: trading-sentinel
    spec:
      containers:
      - name: trading-sentinel
        image: $DOCKER_REGISTRY/trading-sentinel:latest
        env:
        - name: DATABASE_URL
          value: postgresql://trading_user:$(kubectl get secret trading-sentinel-secret -o jsonpath='{.data.postgres-password}' | base64 -d)@postgresql:5432/trading_sentinel
        - name: REDIS_URL
          value: redis://redis:6379/0
        envFrom:
        - configMapRef:
            name: trading-sentinel-config
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: trading-sentinel
  namespace: $KUBERNETES_NAMESPACE
spec:
  selector:
    app: trading-sentinel
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
EOF

    # Create Ingress
    cat > /opt/trading-sentinel/kubernetes/ingress.yaml << EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: trading-sentinel-ingress
  namespace: $KUBERNETES_NAMESPACE
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - trading-sentinel.local
    secretName: trading-sentinel-tls
  rules:
  - host: trading-sentinel.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: trading-sentinel
            port:
              number: 8000
EOF

    log_success "Kubernetes configurations created"
}

# =============================================================================
# MONITORING AND OBSERVABILITY
# =============================================================================

setup_monitoring() {
    log_info "Setting up monitoring and observability..."
    
    if [[ "$DEPLOYMENT_MODE" == "kubernetes" ]]; then
        # Install Prometheus Operator
        helm install prometheus-operator prometheus-community/kube-prometheus-stack \
            --namespace $KUBERNETES_NAMESPACE \
            --create-namespace \
            --set grafana.adminPassword="your_secure_grafana_password"
    else
        # Docker-based monitoring is handled in docker-compose.yml
        log_info "Monitoring configured in Docker Compose"
    fi
    
    log_success "Monitoring setup completed"
}

# =============================================================================
# SECURITY CONFIGURATION
# =============================================================================

setup_security() {
    log_info "Configuring security settings..."
    
    # Generate SSL certificates if enabled
    if [[ "$SSL_ENABLED" == "true" ]]; then
        mkdir -p /opt/trading-sentinel/ssl
        
        # Generate self-signed certificate for development
        if [[ "$ENVIRONMENT" != "production" ]]; then
            openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                -keyout /opt/trading-sentinel/ssl/server.key \
                -out /opt/trading-sentinel/ssl/server.crt \
                -subj "/C=US/ST=State/L=City/O=Organization/CN=trading-sentinel.local"
        fi
    fi
    
    # Configure firewall
    if command -v ufw &> /dev/null; then
        ufw --force enable
        ufw default deny incoming
        ufw default allow outgoing
        
        # Allow SSH
        ufw allow ssh
        
        # Allow HTTP/HTTPS
        ufw allow 80/tcp
        ufw allow 443/tcp
        
        # Allow application ports
        ufw allow 8000/tcp  # Trading Sentinel API
        ufw allow 3000/tcp  # Grafana
        ufw allow 9090/tcp  # Prometheus
        
        # Allow Docker/Kubernetes ports (internal)
        ufw allow from 172.17.0.0/16
        ufw allow from 172.20.0.0/16
        ufw allow from 10.244.0.0/16
    fi
    
    # Set up log rotation
    cat > /etc/logrotate.d/trading-sentinel << EOF
/var/log/trading-sentinel/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 1000 1000
    postrotate
        systemctl reload rsyslog > /dev/null 2>&1 || true
    endscript
}
EOF
    
    log_success "Security configuration completed"
}

# =============================================================================
# DEPLOYMENT EXECUTION
# =============================================================================

deploy_application() {
    log_info "Deploying Trading Sentinel application..."
    
    cd /opt/trading-sentinel
    
    if [[ "$DEPLOYMENT_MODE" == "kubernetes" ]]; then
        # Deploy to Kubernetes
        kubectl apply -f kubernetes/namespace.yaml
        kubectl apply -f kubernetes/configmap.yaml
        kubectl apply -f kubernetes/secret.yaml
        kubectl apply -f kubernetes/postgresql.yaml
        kubectl apply -f kubernetes/redis.yaml
        
        # Wait for databases to be ready
        kubectl wait --for=condition=ready pod -l app=postgresql -n $KUBERNETES_NAMESPACE --timeout=300s
        kubectl wait --for=condition=ready pod -l app=redis -n $KUBERNETES_NAMESPACE --timeout=300s
        
        # Deploy application
        kubectl apply -f kubernetes/trading-sentinel.yaml
        kubectl apply -f kubernetes/ingress.yaml
        
        # Wait for deployment
        kubectl wait --for=condition=available deployment/trading-sentinel -n $KUBERNETES_NAMESPACE --timeout=300s
        
    else
        # Deploy with Docker Compose
        cd docker
        
        # Generate environment file
        if [[ ! -f .env ]]; then
            cp .env.template .env
            log_warn "Please update the .env file with your secure passwords"
        fi
        
        # Build and start services
        docker compose build
        docker compose up -d
        
        # Wait for services to be healthy
        log_info "Waiting for services to be healthy..."
        sleep 30
        
        # Check service health
        docker compose ps
    fi
    
    log_success "Application deployed successfully"
}

# =============================================================================
# VERIFICATION AND TESTING
# =============================================================================

verify_deployment() {
    log_info "Verifying deployment..."
    
    local success=true
    
    if [[ "$DEPLOYMENT_MODE" == "kubernetes" ]]; then
        # Verify Kubernetes deployment
        if ! kubectl get pods -n $KUBERNETES_NAMESPACE | grep -q "Running"; then
            log_error "Some pods are not running"
            success=false
        fi
        
        if ! kubectl get svc -n $KUBERNETES_NAMESPACE | grep -q "trading-sentinel"; then
            log_error "Trading Sentinel service not found"
            success=false
        fi
        
    else
        # Verify Docker deployment
        if ! docker compose -f /opt/trading-sentinel/docker/docker-compose.yml ps | grep -q "Up"; then
            log_error "Some Docker services are not running"
            success=false
        fi
        
        # Test API endpoint
        if ! curl -f http://localhost:8000/health &> /dev/null; then
            log_warn "API health check failed (service may still be starting)"
        fi
    fi
    
    # Test database connectivity
    if command -v psql &> /dev/null; then
        if ! PGPASSWORD="your_secure_postgres_password" psql -h localhost -U trading_user -d trading_sentinel -c "SELECT 1;" &> /dev/null; then
            log_warn "PostgreSQL connectivity test failed"
        fi
    fi
    
    # Test Redis connectivity
    if command -v redis-cli &> /dev/null; then
        if ! redis-cli -h localhost ping | grep -q "PONG"; then
            log_warn "Redis connectivity test failed"
        fi
    fi
    
    if [[ "$success" == "true" ]]; then
        log_success "Deployment verification completed successfully"
    else
        log_error "Deployment verification failed"
        return 1
    fi
}

generate_deployment_report() {
    log_info "Generating deployment report..."
    
    local report_file="/opt/trading-sentinel/deployment-report-$TIMESTAMP.json"
    
    cat > "$report_file" << EOF
{
    "deployment": {
        "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
        "mode": "$DEPLOYMENT_MODE",
        "environment": "$ENVIRONMENT",
        "cloud_provider": "$CLOUD_PROVIDER",
        "scale_factor": $SCALE_FACTOR,
        "max_accounts": $MAX_ACCOUNTS
    },
    "infrastructure": {
        "docker_version": "$(docker --version 2>/dev/null || echo 'Not installed')",
        "kubernetes_version": "$(kubectl version --client --short 2>/dev/null || echo 'Not installed')",
        "helm_version": "$(helm version --short 2>/dev/null || echo 'Not installed')"
    },
    "system": {
        "os": "$(lsb_release -d | cut -f2)",
        "kernel": "$(uname -r)",
        "cpu_cores": $(nproc),
        "memory_gb": $(free -g | awk 'NR==2{printf "%.1f", $2}'),
        "disk_space_gb": $(df / | awk 'NR==2 {printf "%.1f", $4/1024/1024}')
    },
    "services": {
        "postgresql": {
            "replicas": $POSTGRESQL_REPLICAS,
            "status": "deployed"
        },
        "redis": {
            "cluster_size": $REDIS_CLUSTER_SIZE,
            "status": "deployed"
        },
        "monitoring": {
            "prometheus": "enabled",
            "grafana": "enabled"
        }
    },
    "security": {
        "ssl_enabled": $SSL_ENABLED,
        "rbac_enabled": $RBAC_ENABLED,
        "firewall_configured": true
    },
    "endpoints": {
        "api": "http://localhost:8000",
        "grafana": "http://localhost:3000",
        "prometheus": "http://localhost:9090"
    }
}
EOF
    
    log_success "Deployment report generated: $report_file"
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

main() {
    log_info "Starting AI Trading Sentinel Multi-Account Scaling Deployment"
    log_info "Deployment Mode: $DEPLOYMENT_MODE"
    log_info "Environment: $ENVIRONMENT"
    log_info "Cloud Provider: $CLOUD_PROVIDER"
    
    # Pre-deployment checks
    check_root
    check_system_requirements
    create_backup
    
    # Setup directories and files
    setup_application_directories
    copy_application_files
    
    # Install and configure infrastructure
    install_docker
    configure_docker
    setup_docker_registry
    
    if [[ "$DEPLOYMENT_MODE" == "kubernetes" ]]; then
        install_kubernetes
        setup_kubernetes_cluster
        install_helm
    fi
    
    # Create deployment configurations
    create_docker_configurations
    create_kubernetes_configurations
    
    # Setup monitoring and security
    setup_monitoring
    setup_security
    
    # Deploy application
    deploy_application
    
    # Verify deployment
    verify_deployment
    
    # Generate report
    generate_deployment_report
    
    log_success "AI Trading Sentinel Multi-Account Scaling Deployment completed successfully!"
    
    echo ""
    echo "=============================================================================="
    echo "                    DEPLOYMENT COMPLETED SUCCESSFULLY"
    echo "=============================================================================="
    echo ""
    echo "Deployment Mode: $DEPLOYMENT_MODE"
    echo "Environment: $ENVIRONMENT"
    echo "Max Accounts: $MAX_ACCOUNTS"
    echo ""
    echo "Access URLs:"
    echo "  - Trading Sentinel API: http://localhost:8000"
    echo "  - Grafana Dashboard: http://localhost:3000 (admin/your_secure_grafana_password)"
    echo "  - Prometheus Metrics: http://localhost:9090"
    echo ""
    echo "Configuration Files:"
    echo "  - Application: /opt/trading-sentinel/"
    echo "  - Docker: /opt/trading-sentinel/docker/"
    if [[ "$DEPLOYMENT_MODE" == "kubernetes" ]]; then
        echo "  - Kubernetes: /opt/trading-sentinel/kubernetes/"
    fi
    echo ""
    echo "Logs:"
    echo "  - Deployment: $LOG_FILE"
    echo "  - Application: /var/log/trading-sentinel/"
    echo ""
    echo "Next Steps:"
    echo "  1. Update passwords in configuration files"
    echo "  2. Configure SSL certificates for production"
    echo "  3. Set up monitoring alerts"
    echo "  4. Configure backup strategies"
    echo "  5. Test account deployment and scaling"
    echo ""
    echo "=============================================================================="
}

# Execute main function
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi