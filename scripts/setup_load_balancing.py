#!/usr/bin/env python3
"""
AI Trading Sentinel - Load Balancing Setup
High availability and performance optimization configuration
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import yaml

class LoadBalancingSetup:
    """Load balancing and high availability setup for AI Trading Sentinel"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.lb_dir = self.project_root / "load_balancing"
        self.nginx_dir = self.lb_dir / "nginx"
        self.haproxy_dir = self.lb_dir / "haproxy"
        self.docker_dir = self.lb_dir / "docker"
        
        # Create directories
        self._create_directories()
        
        print(f"⚖️  Load Balancing Setup initialized")
        print(f"📁 Load balancing directory: {self.lb_dir}")
    
    def _create_directories(self):
        """Create load balancing directories"""
        directories = [
            self.lb_dir,
            self.nginx_dir,
            self.haproxy_dir,
            self.docker_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        print(f"✅ Load balancing directories created")
    
    def create_nginx_load_balancer(self) -> bool:
        """Create Nginx load balancer configuration"""
        print("\n🔄 Creating Nginx load balancer configuration...")
        
        # Main load balancer configuration
        nginx_config = """
# AI Trading Sentinel - Nginx Load Balancer Configuration

# Upstream servers for API
upstream trading_api {
    least_conn;
    
    # Primary API servers
    server 127.0.0.1:5000 weight=3 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:5001 weight=2 max_fails=3 fail_timeout=30s backup;
    
    # Health check
    keepalive 32;
    keepalive_requests 100;
    keepalive_timeout 60s;
}

# Upstream servers for WebSocket
upstream trading_websocket {
    ip_hash;  # Sticky sessions for WebSocket
    
    server 127.0.0.1:5010 weight=1 max_fails=2 fail_timeout=10s;
    server 127.0.0.1:5011 weight=1 max_fails=2 fail_timeout=10s;
}

# Upstream servers for trading bot instances
upstream trading_bot {
    least_conn;
    
    server 127.0.0.1:5020 weight=1 max_fails=2 fail_timeout=30s;
    server 127.0.0.1:5021 weight=1 max_fails=2 fail_timeout=30s;
    server 127.0.0.1:5022 weight=1 max_fails=2 fail_timeout=30s;
}

# Rate limiting zones
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/s;
limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=5r/s;
limit_req_zone $binary_remote_addr zone=ws_limit:10m rate=50r/s;

# Connection limiting
limit_conn_zone $binary_remote_addr zone=conn_limit:10m;

# Caching
proxy_cache_path /var/cache/nginx/trading levels=1:2 keys_zone=trading_cache:10m max_size=1g inactive=60m use_temp_path=off;

# Main server block
server {
    listen 80;
    listen [::]:80;
    server_name _;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name _;
    
    # SSL Configuration
    ssl_certificate /etc/ssl/certs/ai-trading-sentinel.crt;
    ssl_certificate_key /etc/ssl/private/ai-trading-sentinel.key;
    
    # SSL Security
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Connection limits
    limit_conn conn_limit 50;
    
    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
    
    # Load balancer status
    location /lb-status {
        stub_status on;
        access_log off;
        allow 127.0.0.1;
        allow ::1;
        deny all;
    }
    
    # API endpoints with load balancing
    location /api/ {
        limit_req zone=api_limit burst=200 nodelay;
        
        # Proxy settings
        proxy_pass http://trading_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $server_name;
        
        # Load balancer headers
        proxy_set_header X-Load-Balancer "nginx";
        
        # Timeouts
        proxy_connect_timeout 5s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # Buffering
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        
        # Health checks
        proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
        proxy_next_upstream_tries 3;
        proxy_next_upstream_timeout 10s;
        
        # Caching for GET requests
        proxy_cache trading_cache;
        proxy_cache_valid 200 302 5m;
        proxy_cache_valid 404 1m;
        proxy_cache_use_stale error timeout updating http_500 http_502 http_503 http_504;
        proxy_cache_lock on;
        
        # Cache bypass for authenticated requests
        proxy_cache_bypass $http_authorization;
        proxy_no_cache $http_authorization;
    }
    
    # Authentication endpoints with strict rate limiting
    location /api/auth/ {
        limit_req zone=auth_limit burst=10 nodelay;
        
        proxy_pass http://trading_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # No caching for auth endpoints
        proxy_no_cache 1;
        proxy_cache_bypass 1;
        
        # Shorter timeouts for auth
        proxy_connect_timeout 3s;
        proxy_send_timeout 10s;
        proxy_read_timeout 10s;
    }
    
    # WebSocket connections with load balancing
    location /ws {
        limit_req zone=ws_limit burst=100 nodelay;
        
        proxy_pass http://trading_websocket;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket specific settings
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
        proxy_connect_timeout 5s;
        
        # Disable buffering for WebSocket
        proxy_buffering off;
    }
    
    # Bot management endpoints
    location /api/bot/ {
        limit_req zone=api_limit burst=50 nodelay;
        
        proxy_pass http://trading_bot;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Bot-specific timeouts
        proxy_connect_timeout 10s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Static files with caching
    location /static/ {
        alias /opt/ai-trading-sentinel/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        
        # Compression
        gzip on;
        gzip_vary on;
        gzip_types text/css application/javascript application/json image/svg+xml;
    }
    
    # Frontend application
    location / {
        root /opt/ai-trading-sentinel/frontend;
        index index.html;
        try_files $uri $uri/ /index.html;
        
        # Caching for static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            
            # Compression
            gzip on;
            gzip_vary on;
        }
    }
    
    # Error pages
    error_page 502 503 504 /maintenance.html;
    location = /maintenance.html {
        root /opt/ai-trading-sentinel/error_pages;
        internal;
    }
    
    # Logging
    access_log /var/log/nginx/ai-trading-sentinel-lb.access.log;
    error_log /var/log/nginx/ai-trading-sentinel-lb.error.log warn;
}
"""
        
        config_file = self.nginx_dir / "load_balancer.conf"
        with open(config_file, 'w') as f:
            f.write(nginx_config)
        
        # Create upstream health check script
        health_check_script = """
#!/bin/bash
# Nginx Upstream Health Check Script

UPSTREAMS=("127.0.0.1:5000" "127.0.0.1:5001" "127.0.0.1:5010" "127.0.0.1:5011" "127.0.0.1:5020" "127.0.0.1:5021" "127.0.0.1:5022")
LOG_FILE="/var/log/nginx/upstream_health.log"

echo "$(date): Starting upstream health check" >> "$LOG_FILE"

for upstream in "${UPSTREAMS[@]}"; do
    if curl -f -s --connect-timeout 5 "http://$upstream/health" > /dev/null; then
        echo "$(date): $upstream - HEALTHY" >> "$LOG_FILE"
    else
        echo "$(date): $upstream - UNHEALTHY" >> "$LOG_FILE"
        # Send alert (implement your alerting mechanism here)
        # curl -X POST "$SLACK_WEBHOOK" -d "{\"text\": \"Upstream $upstream is unhealthy\"}"
    fi
done

echo "$(date): Health check completed" >> "$LOG_FILE"
"""
        
        health_script = self.nginx_dir / "health_check.sh"
        with open(health_script, 'w') as f:
            f.write(health_check_script)
        
        os.chmod(health_script, 0o755)
        
        print(f"✅ Nginx load balancer configuration created")
        return True
    
    def create_haproxy_config(self) -> bool:
        """Create HAProxy configuration as alternative load balancer"""
        print("\n🔄 Creating HAProxy configuration...")
        
        haproxy_config = """
# AI Trading Sentinel - HAProxy Configuration

global
    daemon
    user haproxy
    group haproxy
    pidfile /var/run/haproxy.pid
    
    # SSL/TLS configuration
    ssl-default-bind-ciphers ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-RSA-AES128-GCM-SHA256
    ssl-default-bind-options ssl-min-ver TLSv1.2 no-tls-tickets
    
    # Logging
    log stdout local0 info
    
    # Stats socket
    stats socket /var/run/haproxy.sock mode 600 level admin
    stats timeout 2m

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms
    
    # Logging
    option httplog
    log global
    
    # Health checks
    option httpchk GET /health
    
    # Error handling
    errorfile 400 /etc/haproxy/errors/400.http
    errorfile 403 /etc/haproxy/errors/403.http
    errorfile 408 /etc/haproxy/errors/408.http
    errorfile 500 /etc/haproxy/errors/500.http
    errorfile 502 /etc/haproxy/errors/502.http
    errorfile 503 /etc/haproxy/errors/503.http
    errorfile 504 /etc/haproxy/errors/504.http

# Frontend for HTTP (redirect to HTTPS)
frontend http_frontend
    bind *:80
    redirect scheme https code 301

# Frontend for HTTPS
frontend https_frontend
    bind *:443 ssl crt /etc/ssl/certs/ai-trading-sentinel.pem
    
    # Security headers
    http-response set-header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
    http-response set-header X-Frame-Options "DENY"
    http-response set-header X-Content-Type-Options "nosniff"
    http-response set-header X-XSS-Protection "1; mode=block"
    
    # Rate limiting (basic)
    stick-table type ip size 100k expire 30s store http_req_rate(10s)
    http-request track-sc0 src
    http-request deny if { sc_http_req_rate(0) gt 100 }
    
    # Route to appropriate backend
    use_backend trading_api if { path_beg /api/ }
    use_backend trading_websocket if { path_beg /ws }
    use_backend trading_static if { path_beg /static/ }
    default_backend trading_frontend

# Backend for API servers
backend trading_api
    balance leastconn
    
    # Health check
    option httpchk GET /api/health
    http-check expect status 200
    
    # Servers
    server api1 127.0.0.1:5000 check weight 3 maxconn 100
    server api2 127.0.0.1:5001 check weight 2 maxconn 100 backup
    
    # Timeouts
    timeout server 30s
    
    # Headers
    http-request set-header X-Load-Balancer "haproxy"
    http-request set-header X-Forwarded-Proto https

# Backend for WebSocket connections
backend trading_websocket
    balance source  # Sticky sessions
    
    # Health check
    option httpchk GET /ws/health
    
    # Servers
    server ws1 127.0.0.1:5010 check weight 1 maxconn 50
    server ws2 127.0.0.1:5011 check weight 1 maxconn 50
    
    # WebSocket specific settings
    timeout tunnel 3600s
    timeout server 3600s

# Backend for static files
backend trading_static
    balance roundrobin
    
    # Servers (can be same as API or separate CDN)
    server static1 127.0.0.1:8080 check weight 1
    server static2 127.0.0.1:8081 check weight 1 backup
    
    # Caching headers
    http-response set-header Cache-Control "public, max-age=31536000"

# Backend for frontend application
backend trading_frontend
    balance roundrobin
    
    # Servers
    server frontend1 127.0.0.1:3000 check weight 1
    server frontend2 127.0.0.1:3001 check weight 1 backup
    
    # SPA routing
    http-request set-path /index.html if { path_reg ^/(?!api|ws|static).* } !{ path_reg \\.[a-zA-Z0-9]+$ }

# Statistics interface
listen stats
    bind *:8404
    stats enable
    stats uri /stats
    stats refresh 30s
    stats admin if TRUE
    
    # Authentication (change credentials)
    stats auth admin:secure_password_here
    
    # Access control
    acl allowed_ips src 127.0.0.1 ::1
    http-request deny unless allowed_ips

"""
        
        config_file = self.haproxy_dir / "haproxy.cfg"
        with open(config_file, 'w') as f:
            f.write(haproxy_config)
        
        print(f"✅ HAProxy configuration created")
        return True
    
    def create_docker_compose_lb(self) -> bool:
        """Create Docker Compose configuration for load balanced deployment"""
        print("\n🐳 Creating Docker Compose load balancing setup...")
        
        docker_compose = {
            "version": "3.8",
            "services": {
                "nginx-lb": {
                    "image": "nginx:alpine",
                    "container_name": "ai-trading-nginx-lb",
                    "ports": ["80:80", "443:443"],
                    "volumes": [
                        "./nginx/load_balancer.conf:/etc/nginx/conf.d/default.conf:ro",
                        "./ssl:/etc/ssl/certs:ro",
                        "nginx_cache:/var/cache/nginx"
                    ],
                    "depends_on": ["trading-api-1", "trading-api-2"],
                    "restart": "unless-stopped",
                    "networks": ["trading-network"]
                },
                "trading-api-1": {
                    "build": {
                        "context": "../",
                        "dockerfile": "Dockerfile.api"
                    },
                    "container_name": "ai-trading-api-1",
                    "environment": [
                        "FLASK_ENV=production",
                        "API_PORT=5000",
                        "INSTANCE_ID=api-1"
                    ],
                    "volumes": [
                        "../logs:/app/logs",
                        "../.env:/app/.env:ro"
                    ],
                    "expose": ["5000"],
                    "restart": "unless-stopped",
                    "networks": ["trading-network"],
                    "healthcheck": {
                        "test": ["CMD", "curl", "-f", "http://localhost:5000/health"],
                        "interval": "30s",
                        "timeout": "10s",
                        "retries": 3,
                        "start_period": "40s"
                    }
                },
                "trading-api-2": {
                    "build": {
                        "context": "../",
                        "dockerfile": "Dockerfile.api"
                    },
                    "container_name": "ai-trading-api-2",
                    "environment": [
                        "FLASK_ENV=production",
                        "API_PORT=5000",
                        "INSTANCE_ID=api-2"
                    ],
                    "volumes": [
                        "../logs:/app/logs",
                        "../.env:/app/.env:ro"
                    ],
                    "expose": ["5000"],
                    "restart": "unless-stopped",
                    "networks": ["trading-network"],
                    "healthcheck": {
                        "test": ["CMD", "curl", "-f", "http://localhost:5000/health"],
                        "interval": "30s",
                        "timeout": "10s",
                        "retries": 3,
                        "start_period": "40s"
                    }
                },
                "trading-bot-1": {
                    "build": {
                        "context": "../",
                        "dockerfile": "Dockerfile.bot"
                    },
                    "container_name": "ai-trading-bot-1",
                    "environment": [
                        "BOT_INSTANCE=bot-1",
                        "BOT_PORT=5020"
                    ],
                    "volumes": [
                        "../logs:/app/logs",
                        "../.env:/app/.env:ro",
                        "/tmp/.X11-unix:/tmp/.X11-unix:rw"
                    ],
                    "expose": ["5020"],
                    "restart": "unless-stopped",
                    "networks": ["trading-network"],
                    "depends_on": ["redis"]
                },
                "trading-bot-2": {
                    "build": {
                        "context": "../",
                        "dockerfile": "Dockerfile.bot"
                    },
                    "container_name": "ai-trading-bot-2",
                    "environment": [
                        "BOT_INSTANCE=bot-2",
                        "BOT_PORT=5021"
                    ],
                    "volumes": [
                        "../logs:/app/logs",
                        "../.env:/app/.env:ro",
                        "/tmp/.X11-unix:/tmp/.X11-unix:rw"
                    ],
                    "expose": ["5021"],
                    "restart": "unless-stopped",
                    "networks": ["trading-network"],
                    "depends_on": ["redis"]
                },
                "redis": {
                    "image": "redis:alpine",
                    "container_name": "ai-trading-redis",
                    "command": "redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}",
                    "volumes": ["redis_data:/data"],
                    "expose": ["6379"],
                    "restart": "unless-stopped",
                    "networks": ["trading-network"]
                },
                "prometheus": {
                    "image": "prom/prometheus:latest",
                    "container_name": "ai-trading-prometheus",
                    "ports": ["9090:9090"],
                    "volumes": [
                        "../monitoring/prometheus_config.yml:/etc/prometheus/prometheus.yml:ro",
                        "prometheus_data:/prometheus"
                    ],
                    "command": [
                        "--config.file=/etc/prometheus/prometheus.yml",
                        "--storage.tsdb.path=/prometheus",
                        "--web.console.libraries=/etc/prometheus/console_libraries",
                        "--web.console.templates=/etc/prometheus/consoles",
                        "--storage.tsdb.retention.time=200h",
                        "--web.enable-lifecycle"
                    ],
                    "restart": "unless-stopped",
                    "networks": ["trading-network"]
                },
                "grafana": {
                    "image": "grafana/grafana:latest",
                    "container_name": "ai-trading-grafana",
                    "ports": ["3001:3000"],
                    "environment": [
                        "GF_SECURITY_ADMIN_PASSWORD=admin123",
                        "GF_USERS_ALLOW_SIGN_UP=false"
                    ],
                    "volumes": [
                        "grafana_data:/var/lib/grafana",
                        "../monitoring/grafana_dashboard.json:/var/lib/grafana/dashboards/trading.json:ro"
                    ],
                    "restart": "unless-stopped",
                    "networks": ["trading-network"]
                }
            },
            "networks": {
                "trading-network": {
                    "driver": "bridge"
                }
            },
            "volumes": {
                "nginx_cache": {},
                "redis_data": {},
                "prometheus_data": {},
                "grafana_data": {}
            }
        }
        
        compose_file = self.docker_dir / "docker-compose.yml"
        with open(compose_file, 'w') as f:
            yaml.dump(docker_compose, f, default_flow_style=False, indent=2)
        
        # Create Dockerfiles
        api_dockerfile = """
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 trading && chown -R trading:trading /app
USER trading

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Expose port
EXPOSE 5000

# Start application
CMD ["python", "src/api/app.py"]
"""
        
        api_dockerfile_path = self.docker_dir / "Dockerfile.api"
        with open(api_dockerfile_path, 'w') as f:
            f.write(api_dockerfile)
        
        bot_dockerfile = """
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for Selenium
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    xvfb \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 trading && chown -R trading:trading /app
USER trading

# Set display for headless browser
ENV DISPLAY=:99

# Expose port
EXPOSE 5020

# Start application
CMD ["python", "src/bot/main.py"]
"""
        
        bot_dockerfile_path = self.docker_dir / "Dockerfile.bot"
        with open(bot_dockerfile_path, 'w') as f:
            f.write(bot_dockerfile)
        
        print(f"✅ Docker Compose load balancing setup created")
        return True
    
    def create_kubernetes_manifests(self) -> bool:
        """Create Kubernetes manifests for scalable deployment"""
        print("\n☸️  Creating Kubernetes manifests...")
        
        k8s_dir = self.lb_dir / "kubernetes"
        k8s_dir.mkdir(exist_ok=True)
        
        # Namespace
        namespace = {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": "ai-trading-sentinel"
            }
        }
        
        # ConfigMap for Nginx
        nginx_configmap = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": "nginx-config",
                "namespace": "ai-trading-sentinel"
            },
            "data": {
                "nginx.conf": "# Nginx configuration would go here"
            }
        }
        
        # Deployment for API
        api_deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": "trading-api",
                "namespace": "ai-trading-sentinel"
            },
            "spec": {
                "replicas": 3,
                "selector": {
                    "matchLabels": {
                        "app": "trading-api"
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": "trading-api"
                        }
                    },
                    "spec": {
                        "containers": [{
                            "name": "trading-api",
                            "image": "ai-trading-sentinel/api:latest",
                            "ports": [{"containerPort": 5000}],
                            "env": [
                                {"name": "FLASK_ENV", "value": "production"},
                                {"name": "REDIS_URL", "value": "redis://redis-service:6379"}
                            ],
                            "resources": {
                                "requests": {
                                    "memory": "256Mi",
                                    "cpu": "250m"
                                },
                                "limits": {
                                    "memory": "512Mi",
                                    "cpu": "500m"
                                }
                            },
                            "livenessProbe": {
                                "httpGet": {
                                    "path": "/health",
                                    "port": 5000
                                },
                                "initialDelaySeconds": 30,
                                "periodSeconds": 10
                            },
                            "readinessProbe": {
                                "httpGet": {
                                    "path": "/health",
                                    "port": 5000
                                },
                                "initialDelaySeconds": 5,
                                "periodSeconds": 5
                            }
                        }]
                    }
                }
            }
        }
        
        # Service for API
        api_service = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": "trading-api-service",
                "namespace": "ai-trading-sentinel"
            },
            "spec": {
                "selector": {
                    "app": "trading-api"
                },
                "ports": [{
                    "protocol": "TCP",
                    "port": 80,
                    "targetPort": 5000
                }],
                "type": "ClusterIP"
            }
        }
        
        # Ingress for load balancing
        ingress = {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "Ingress",
            "metadata": {
                "name": "trading-ingress",
                "namespace": "ai-trading-sentinel",
                "annotations": {
                    "nginx.ingress.kubernetes.io/rewrite-target": "/",
                    "nginx.ingress.kubernetes.io/ssl-redirect": "true",
                    "nginx.ingress.kubernetes.io/rate-limit": "100"
                }
            },
            "spec": {
                "tls": [{
                    "hosts": ["ai-trading-sentinel.local"],
                    "secretName": "trading-tls"
                }],
                "rules": [{
                    "host": "ai-trading-sentinel.local",
                    "http": {
                        "paths": [
                            {
                                "path": "/api",
                                "pathType": "Prefix",
                                "backend": {
                                    "service": {
                                        "name": "trading-api-service",
                                        "port": {"number": 80}
                                    }
                                }
                            },
                            {
                                "path": "/",
                                "pathType": "Prefix",
                                "backend": {
                                    "service": {
                                        "name": "trading-frontend-service",
                                        "port": {"number": 80}
                                    }
                                }
                            }
                        ]
                    }
                }]
            }
        }
        
        # HorizontalPodAutoscaler
        hpa = {
            "apiVersion": "autoscaling/v2",
            "kind": "HorizontalPodAutoscaler",
            "metadata": {
                "name": "trading-api-hpa",
                "namespace": "ai-trading-sentinel"
            },
            "spec": {
                "scaleTargetRef": {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "name": "trading-api"
                },
                "minReplicas": 2,
                "maxReplicas": 10,
                "metrics": [
                    {
                        "type": "Resource",
                        "resource": {
                            "name": "cpu",
                            "target": {
                                "type": "Utilization",
                                "averageUtilization": 70
                            }
                        }
                    },
                    {
                        "type": "Resource",
                        "resource": {
                            "name": "memory",
                            "target": {
                                "type": "Utilization",
                                "averageUtilization": 80
                            }
                        }
                    }
                ]
            }
        }
        
        # Save manifests
        manifests = {
            "namespace.yaml": namespace,
            "nginx-configmap.yaml": nginx_configmap,
            "api-deployment.yaml": api_deployment,
            "api-service.yaml": api_service,
            "ingress.yaml": ingress,
            "hpa.yaml": hpa
        }
        
        for filename, manifest in manifests.items():
            manifest_file = k8s_dir / filename
            with open(manifest_file, 'w') as f:
                yaml.dump(manifest, f, default_flow_style=False, indent=2)
        
        print(f"✅ Kubernetes manifests created")
        return True
    
    def create_load_testing_script(self) -> bool:
        """Create load testing script to validate load balancing"""
        print("\n🧪 Creating load testing script...")
        
        load_test_script = f"""
#!/usr/bin/env python3
"""
AI Trading Sentinel - Load Testing Script
Validate load balancing and performance under load
"""

import asyncio
import aiohttp
import time
import json
import statistics
from typing import List, Dict
from datetime import datetime

class LoadTester:
    def __init__(self, base_url: str = "https://localhost"):
        self.base_url = base_url
        self.results = {{
            "requests": [],
            "errors": [],
            "response_times": [],
            "status_codes": {{}}
        }}
    
    async def make_request(self, session: aiohttp.ClientSession, endpoint: str, method: str = "GET", data: dict = None) -> Dict:
        """Make a single HTTP request"""
        start_time = time.time()
        
        try:
            url = f"{{self.base_url}}{{endpoint}}"
            
            if method == "GET":
                async with session.get(url, ssl=False) as response:
                    content = await response.text()
                    end_time = time.time()
                    
                    result = {{
                        "url": url,
                        "method": method,
                        "status": response.status,
                        "response_time": end_time - start_time,
                        "content_length": len(content),
                        "timestamp": datetime.utcnow().isoformat()
                    }}
                    
                    return result
            
            elif method == "POST":
                async with session.post(url, json=data, ssl=False) as response:
                    content = await response.text()
                    end_time = time.time()
                    
                    result = {{
                        "url": url,
                        "method": method,
                        "status": response.status,
                        "response_time": end_time - start_time,
                        "content_length": len(content),
                        "timestamp": datetime.utcnow().isoformat()
                    }}
                    
                    return result
        
        except Exception as e:
            end_time = time.time()
            error = {{
                "url": f"{{self.base_url}}{{endpoint}}",
                "method": method,
                "error": str(e),
                "response_time": end_time - start_time,
                "timestamp": datetime.utcnow().isoformat()
            }}
            
            return error
    
    async def run_concurrent_requests(self, endpoint: str, concurrent_users: int, requests_per_user: int, method: str = "GET", data: dict = None):
        """Run concurrent requests to test load balancing"""
        print(f"🚀 Starting load test: {{concurrent_users}} users, {{requests_per_user}} requests each")
        print(f"📍 Endpoint: {{endpoint}}")
        
        connector = aiohttp.TCPConnector(limit=concurrent_users * 2)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tasks = []
            
            for user in range(concurrent_users):
                for request in range(requests_per_user):
                    task = self.make_request(session, endpoint, method, data)
                    tasks.append(task)
            
            # Execute all requests concurrently
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            # Process results
            for result in results:
                if isinstance(result, Exception):
                    self.results["errors"].append({{
                        "error": str(result),
                        "timestamp": datetime.utcnow().isoformat()
                    }})
                elif "error" in result:
                    self.results["errors"].append(result)
                else:
                    self.results["requests"].append(result)
                    self.results["response_times"].append(result["response_time"])
                    
                    status = result["status"]
                    self.results["status_codes"][status] = self.results["status_codes"].get(status, 0) + 1
            
            total_time = end_time - start_time
            total_requests = len(self.results["requests"])
            
            print(f"✅ Load test completed in {{total_time:.2f}} seconds")
            print(f"📊 Total requests: {{total_requests}}")
            print(f"⚡ Requests per second: {{total_requests / total_time:.2f}}")
    
    def generate_report(self) -> Dict:
        """Generate comprehensive load test report"""
        if not self.results["response_times"]:
            return {{"error": "No successful requests to analyze"}}
        
        response_times = self.results["response_times"]
        
        report = {{
            "summary": {{
                "total_requests": len(self.results["requests"]),
                "total_errors": len(self.results["errors"]),
                "success_rate": len(self.results["requests"]) / (len(self.results["requests"]) + len(self.results["errors"])) * 100,
                "status_codes": self.results["status_codes"]
            }},
            "performance": {{
                "avg_response_time": statistics.mean(response_times),
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "median_response_time": statistics.median(response_times),
                "p95_response_time": sorted(response_times)[int(len(response_times) * 0.95)],
                "p99_response_time": sorted(response_times)[int(len(response_times) * 0.99)]
            }},
            "errors": self.results["errors"][:10],  # First 10 errors
            "timestamp": datetime.utcnow().isoformat()
        }}
        
        return report
    
    async def test_load_balancing(self):
        """Test various endpoints to validate load balancing"""
        print("\n🔄 Testing Load Balancing Performance")
        print("=" * 50)
        
        # Test scenarios
        scenarios = [
            {{"endpoint": "/health", "users": 50, "requests": 10, "method": "GET"}},
            {{"endpoint": "/api/status", "users": 30, "requests": 5, "method": "GET"}},
            {{"endpoint": "/api/auth/login", "users": 10, "requests": 3, "method": "POST", "data": {{"username": "test", "password": "test"}}}},
            {{"endpoint": "/api/trades", "users": 20, "requests": 8, "method": "GET"}}
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n📋 Scenario {{i}}: {{scenario['endpoint']}}")
            
            await self.run_concurrent_requests(
                scenario["endpoint"],
                scenario["users"],
                scenario["requests"],
                scenario.get("method", "GET"),
                scenario.get("data")
            )
            
            # Brief pause between scenarios
            await asyncio.sleep(2)
        
        # Generate and save report
        report = self.generate_report()
        
        report_file = "{self.lb_dir}/load_test_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📊 Load test report saved: {{report_file}}")
        
        # Print summary
        print(f"\n📈 LOAD TEST SUMMARY")
        print(f"Total Requests: {{report['summary']['total_requests']}}")
        print(f"Success Rate: {{report['summary']['success_rate']:.2f}}%")
        print(f"Average Response Time: {{report['performance']['avg_response_time']:.3f}}s")
        print(f"95th Percentile: {{report['performance']['p95_response_time']:.3f}}s")
        
        return report

async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Trading Sentinel Load Testing')
    parser.add_argument('--url', default='https://localhost', help='Base URL to test')
    parser.add_argument('--users', type=int, default=50, help='Concurrent users')
    parser.add_argument('--requests', type=int, default=10, help='Requests per user')
    parser.add_argument('--endpoint', default='/health', help='Endpoint to test')
    
    args = parser.parse_args()
    
    tester = LoadTester(args.url)
    
    if args.endpoint == 'all':
        await tester.test_load_balancing()
    else:
        await tester.run_concurrent_requests(args.endpoint, args.users, args.requests)
        report = tester.generate_report()
        print(json.dumps(report, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
"""
        
        load_test_file = self.lb_dir / "load_test.py"
        with open(load_test_file, 'w') as f:
            f.write(load_test_script)
        
        os.chmod(load_test_file, 0o755)
        
        print(f"✅ Load testing script created")
        return True
    
    def create_deployment_script(self) -> bool:
        """Create deployment script for load balancing setup"""
        print("\n🚀 Creating load balancing deployment script...")
        
        deployment_script = f"""
#!/bin/bash
# AI Trading Sentinel - Load Balancing Deployment Script

set -e

LB_DIR="{self.lb_dir}"
NGINX_DIR="$LB_DIR/nginx"
DOCKER_DIR="$LB_DIR/docker"

echo "⚖️  Deploying AI Trading Sentinel Load Balancing"
echo "================================================"

# Function to check if command exists
command_exists() {{
    command -v "$1" >/dev/null 2>&1
}}

# Check prerequisites
echo "🔍 Checking prerequisites..."

if ! command_exists nginx; then
    echo "❌ Nginx not found. Installing..."
    sudo apt-get update
    sudo apt-get install -y nginx
fi

if ! command_exists docker; then
    echo "❌ Docker not found. Installing..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
fi

if ! command_exists docker-compose; then
    echo "❌ Docker Compose not found. Installing..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

echo "✅ Prerequisites checked"

# Deploy Nginx configuration
echo "\n📄 Deploying Nginx load balancer..."

if [ -f "$NGINX_DIR/load_balancer.conf" ]; then
    sudo cp "$NGINX_DIR/load_balancer.conf" /etc/nginx/sites-available/ai-trading-sentinel-lb
    sudo ln -sf /etc/nginx/sites-available/ai-trading-sentinel-lb /etc/nginx/sites-enabled/
    
    # Remove default site
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # Test Nginx configuration
    sudo nginx -t
    
    # Reload Nginx
    sudo systemctl reload nginx
    
    echo "✅ Nginx load balancer deployed"
else
    echo "❌ Nginx configuration not found"
    exit 1
fi

# Setup health check cron job
echo "\n🏥 Setting up health checks..."

if [ -f "$NGINX_DIR/health_check.sh" ]; then
    sudo cp "$NGINX_DIR/health_check.sh" /usr/local/bin/
    sudo chmod +x /usr/local/bin/health_check.sh
    
    # Add cron job for health checks (every 5 minutes)
    (crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/health_check.sh") | crontab -
    
    echo "✅ Health checks configured"
fi

# Deploy Docker Compose setup
echo "\n🐳 Deploying Docker Compose setup..."

if [ -f "$DOCKER_DIR/docker-compose.yml" ]; then
    cd "$DOCKER_DIR"
    
    # Build images
    docker-compose build
    
    # Start services
    docker-compose up -d
    
    # Wait for services to be ready
    echo "⏳ Waiting for services to start..."
    sleep 30
    
    # Check service health
    docker-compose ps
    
    echo "✅ Docker Compose setup deployed"
    
    cd - > /dev/null
else
    echo "⚠️  Docker Compose configuration not found, skipping"
fi

# Create systemd service for load balancer management
echo "\n⚙️  Creating systemd service..."

cat > /tmp/ai-trading-lb.service << EOF
[Unit]
Description=AI Trading Sentinel Load Balancer
After=network.target docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$DOCKER_DIR
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/ai-trading-lb.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ai-trading-lb.service

echo "✅ Systemd service created"

# Run load test
echo "\n🧪 Running load test..."

if [ -f "$LB_DIR/load_test.py" ]; then
    cd "$LB_DIR"
    
    # Install Python dependencies for load testing
    pip3 install aiohttp
    
    # Run basic load test
    python3 load_test.py --users 10 --requests 5 --endpoint /health
    
    echo "✅ Load test completed"
    
    cd - > /dev/null
fi

# Display status
echo "\n📊 DEPLOYMENT STATUS"
echo "=================="

echo "\n🔄 Nginx Status:"
sudo systemctl status nginx --no-pager -l

echo "\n🐳 Docker Services:"
if [ -f "$DOCKER_DIR/docker-compose.yml" ]; then
    cd "$DOCKER_DIR"
    docker-compose ps
    cd - > /dev/null
fi

echo "\n🌐 Load Balancer Endpoints:"
echo "  - Main site: https://localhost"
echo "  - API: https://localhost/api/"
echo "  - WebSocket: wss://localhost/ws"
echo "  - Health check: https://localhost/health"
echo "  - Nginx status: https://localhost/lb-status (local only)"

echo "\n✅ Load balancing deployment completed successfully!"
echo "\n📋 Next steps:"
echo "  1. Update DNS records to point to this server"
echo "  2. Install production SSL certificates"
echo "  3. Configure monitoring and alerting"
echo "  4. Run comprehensive load tests"
echo "  5. Set up log rotation and backup"
"""
        
        deployment_file = self.lb_dir / "deploy_load_balancing.sh"
        with open(deployment_file, 'w') as f:
            f.write(deployment_script)
        
        os.chmod(deployment_file, 0o755)
        
        print(f"✅ Load balancing deployment script created")
        return True
    
    def generate_lb_report(self) -> Dict:
        """Generate load balancing setup report"""
        print("\n📋 Generating load balancing report...")
        
        report = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "load_balancing_setup": {
                "nginx_load_balancer": "Configured with upstream servers and health checks",
                "haproxy_alternative": "Alternative load balancer configuration available",
                "docker_compose": "Multi-container setup with load balancing",
                "kubernetes_manifests": "Scalable K8s deployment with HPA",
                "load_testing": "Comprehensive load testing script included",
                "health_monitoring": "Automated health checks and monitoring"
            },
            "features": [
                "Multiple upstream servers with failover",
                "Session persistence for WebSocket connections",
                "Rate limiting and DDoS protection",
                "SSL termination and security headers",
                "Caching for improved performance",
                "Health checks and automatic failover",
                "Horizontal pod autoscaling (K8s)",
                "Load testing and performance validation",
                "Monitoring and alerting integration"
            ],
            "deployment_options": {
                "nginx_only": "Simple Nginx reverse proxy with load balancing",
                "docker_compose": "Containerized deployment with multiple instances",
                "kubernetes": "Scalable cloud-native deployment",
                "haproxy": "Alternative load balancer with advanced features"
            },
            "performance_optimizations": [
                "Connection pooling and keep-alive",
                "Response caching for static content",
                "Gzip compression for text content",
                "HTTP/2 support for improved performance",
                "Load balancing algorithms (least_conn, ip_hash)",
                "Circuit breaker pattern for fault tolerance",
                "Resource limits and auto-scaling"
            ],
            "monitoring_endpoints": {
                "health_check": "/health",
                "load_balancer_status": "/lb-status",
                "haproxy_stats": ":8404/stats",
                "prometheus_metrics": ":9090",
                "grafana_dashboard": ":3001"
            },
            "next_steps": [
                "Deploy load balancing configuration to production",
                "Configure production SSL certificates",
                "Set up DNS load balancing (optional)",
                "Implement CDN for static assets",
                "Configure auto-scaling policies",
                "Set up cross-region failover",
                "Implement blue-green deployment",
                "Configure advanced monitoring and alerting"
            ]
        }
        
        report_file = self.lb_dir / "load_balancing_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✅ Load balancing report generated: {report_file}")
        return report
    
    def setup_load_balancing(self) -> bool:
        """Setup complete load balancing infrastructure"""
        print("\n" + "="*60)
        print("⚖️  AI TRADING SENTINEL - LOAD BALANCING SETUP")
        print("="*60)
        
        success = True
        
        try:
            # Create Nginx load balancer configuration
            success &= self.create_nginx_load_balancer()
            
            # Create HAProxy alternative configuration
            success &= self.create_haproxy_config()
            
            # Create Docker Compose setup
            success &= self.create_docker_compose_lb()
            
            # Create Kubernetes manifests
            success &= self.create_kubernetes_manifests()
            
            # Create load testing script
            success &= self.create_load_testing_script()
            
            # Create deployment script
            success &= self.create_deployment_script()
            
            # Generate report
            report = self.generate_lb_report()
            
            if success:
                print(f"\n✅ Load balancing setup completed successfully!")
                print(f"\n📁 Configuration files created in: {self.lb_dir}")
                print(f"\n🚀 To deploy, run: {self.lb_dir}/deploy_load_balancing.sh")
                print(f"\n📊 Report available: {self.lb_dir}/load_balancing_report.json")
            else:
                print(f"\n❌ Some components failed to setup")
                
        except Exception as e:
            print(f"\n❌ Error during load balancing setup: {e}")
            success = False
        
        return success

def main():
    """Main function for load balancing setup"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Trading Sentinel Load Balancing Setup')
    parser.add_argument('--project-root', help='Project root directory')
    parser.add_argument('--nginx-only', action='store_true', help='Setup Nginx load balancer only')
    parser.add_argument('--docker-only', action='store_true', help='Setup Docker Compose only')
    parser.add_argument('--k8s-only', action='store_true', help='Setup Kubernetes manifests only')
    
    args = parser.parse_args()
    
    # Initialize setup
    lb_setup = LoadBalancingSetup(args.project_root)
    
    if args.nginx_only:
        success = lb_setup.create_nginx_load_balancer()
    elif args.docker_only:
        success = lb_setup.create_docker_compose_lb()
    elif args.k8s_only:
        success = lb_setup.create_kubernetes_manifests()
    else:
        success = lb_setup.setup_load_balancing()
    
    if success:
        print(f"\n🎉 Load balancing setup completed successfully!")
        return 0
    else:
        print(f"\n💥 Load balancing setup failed!")
        return 1

if __name__ == "__main__":
    exit(main())
            
            # Create HAProxy alternative configuration
            success &= self.create_haproxy_config()
            
            # Create