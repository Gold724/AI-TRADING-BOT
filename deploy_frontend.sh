#!/bin/bash

# AI Trading Sentinel - Frontend Deployment Script
# Deploy React frontend to production VPS with Nginx configuration

set -e

echo "🚀 AI Trading Sentinel - Frontend Deployment"
echo "============================================="

# Configuration
VPS_IP="185.244.214.70"
VPS_USER="root"
FRONTEND_DIR="/var/www/ai-trading-sentinel"
NGINX_CONF="/etc/nginx/sites-available/ai-trading-sentinel-frontend"
NGINX_ENABLED="/etc/nginx/sites-enabled/ai-trading-sentinel-frontend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if build directory exists
if [ ! -d "frontend/dist" ]; then
    log_error "Frontend build directory not found. Please run 'npm run build' first."
    exit 1
fi

log_info "Building production frontend..."
cd frontend
npm run build
cd ..

log_info "Creating deployment package..."
tar -czf frontend-deployment.tar.gz -C frontend/dist .

log_info "Uploading frontend files to VPS..."
scp frontend-deployment.tar.gz ${VPS_USER}@${VPS_IP}:/tmp/

log_info "Configuring frontend on VPS..."
ssh ${VPS_USER}@${VPS_IP} << 'EOF'
    set -e
    
    echo "📦 Setting up frontend directory..."
    mkdir -p /var/www/ai-trading-sentinel
    cd /var/www/ai-trading-sentinel
    
    # Backup existing files if they exist
    if [ -d "backup" ]; then
        rm -rf backup
    fi
    if [ "$(ls -A . 2>/dev/null)" ]; then
        mkdir -p backup
        mv * backup/ 2>/dev/null || true
    fi
    
    # Extract new frontend files
    tar -xzf /tmp/frontend-deployment.tar.gz
    rm /tmp/frontend-deployment.tar.gz
    
    # Set proper permissions
    chown -R www-data:www-data /var/www/ai-trading-sentinel
    chmod -R 755 /var/www/ai-trading-sentinel
    
    echo "🔧 Configuring Nginx..."
    
    # Create Nginx configuration for frontend
    cat > /etc/nginx/sites-available/ai-trading-sentinel-frontend << 'NGINX_EOF'
server {
    listen 80;
    server_name 185.244.214.70;
    
    # Frontend static files
    location / {
        root /var/www/ai-trading-sentinel;
        index index.html;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # API proxy to Flask backend
    location /api/ {
        proxy_pass http://127.0.0.1:8080/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8080/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private must-revalidate auth;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/javascript;
}
NGINX_EOF
    
    # Enable the site
    ln -sf /etc/nginx/sites-available/ai-trading-sentinel-frontend /etc/nginx/sites-enabled/
    
    # Remove default Nginx site if it exists
    rm -f /etc/nginx/sites-enabled/default
    
    # Test Nginx configuration
    echo "🧪 Testing Nginx configuration..."
    nginx -t
    
    # Reload Nginx
    echo "🔄 Reloading Nginx..."
    systemctl reload nginx
    
    # Ensure Nginx is running
    systemctl enable nginx
    systemctl start nginx
    
    echo "✅ Frontend deployment completed successfully!"
    echo "📊 Frontend accessible at: http://185.244.214.70"
    echo "🔗 API endpoints at: http://185.244.214.70/api/"
EOF

log_success "Frontend deployment completed!"
log_info "Cleaning up local files..."
rm -f frontend-deployment.tar.gz

log_success "🎉 Deployment Summary:"
echo "  • Frontend: http://185.244.214.70"
echo "  • API: http://185.244.214.70/api/"
echo "  • Health Check: http://185.244.214.70/health"
echo ""
log_info "🔍 To verify deployment:"
echo "  curl -I http://185.244.214.70"
echo "  curl http://185.244.214.70/api/health"
echo ""
log_warning "📝 Next Steps:"
echo "  1. Test frontend functionality"
echo "  2. Configure SSL/HTTPS (optional)"
echo "  3. Setup monitoring and alerts"
echo "  4. Begin live trading with minimal risk"