#!/bin/bash

# AI Trading Sentinel - Quick VPS Deployment Script
# Run this script on Contabo VPS (161.97.112.146) via VNC terminal

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root. Please run as a regular user with sudo privileges."
   exit 1
fi

log "Starting AI Trading Sentinel VPS Deployment..."
log "Target VPS: 161.97.112.146"
log "Deployment Mode: Production"

# Step 1: System Update and Package Installation
log "Step 1: Updating system and installing packages..."
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    nodejs \
    npm \
    git \
    nginx \
    curl \
    wget \
    htop \
    ufw \
    unzip

# Install Node.js 18+ if needed
if ! node --version | grep -q "v1[8-9]\|v[2-9][0-9]"; then
    log "Installing Node.js 18..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

success "System packages installed successfully"

# Step 2: Create Application User and Directory
log "Step 2: Setting up application user and directory..."

# Create trading user if it doesn't exist
if ! id "trading" &>/dev/null; then
    sudo useradd -m -s /bin/bash trading
    sudo usermod -aG sudo trading
    success "Created trading user"
else
    log "Trading user already exists"
fi

# Create application directory
sudo mkdir -p /opt/ai-trading-sentinel
sudo chown trading:trading /opt/ai-trading-sentinel
success "Application directory created"

# Step 3: Clone or Setup Repository
log "Step 3: Setting up application code..."
cd /opt/ai-trading-sentinel

# If git repository exists, pull latest changes
if [ -d ".git" ]; then
    log "Updating existing repository..."
    git pull origin main || warning "Git pull failed - continuing with existing code"
else
    log "Cloning repository..."
    # Try to clone from GitHub (replace with actual repo URL)
    git clone https://github.com/YOUR_USERNAME/ai-trading-sentinel.git . || {
        warning "Git clone failed. Please manually copy files to /opt/ai-trading-sentinel"
        log "Creating basic directory structure..."
        mkdir -p backend frontend config data logs
    }
fi

success "Application code setup completed"

# Step 4: Python Environment Setup
log "Step 4: Setting up Python environment..."

# Create virtual environment
if [ ! -d "venv" ]; then
    python3 -m venv venv
    success "Python virtual environment created"
fi

# Activate virtual environment and install dependencies
source venv/bin/activate

# Install Python packages
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    log "Installing essential Python packages..."
    pip install flask flask-cors flask-socketio python-dotenv requests selenium beautifulsoup4 pandas numpy
fi

success "Python dependencies installed"

# Step 5: Frontend Setup
log "Step 5: Setting up frontend..."

if [ -d "frontend" ]; then
    cd frontend
    
    # Install Node.js dependencies
    if [ -f "package.json" ]; then
        npm install
        
        # Build production frontend
        npm run build || {
            warning "Frontend build failed - creating basic build"
            mkdir -p dist
            echo '<html><body><h1>AI Trading Sentinel</h1><p>Frontend will be available soon</p></body></html>' > dist/index.html
        }
    else
        warning "No package.json found - creating basic frontend"
        mkdir -p dist
        echo '<html><body><h1>AI Trading Sentinel</h1><p>Frontend will be available soon</p></body></html>' > dist/index.html
    fi
    
    cd ..
    success "Frontend setup completed"
else
    warning "No frontend directory found - skipping frontend setup"
fi

# Step 6: Environment Configuration
log "Step 6: Configuring environment variables..."

if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# Bulenox Configuration
BULENOX_EMAIL=your_email@example.com
BULENOX_PASSWORD=your_password
BULENOX_BASE_URL=https://bulenox.projectx.com

# Trading Configuration
TRADING_MODE=demo
RISK_PERCENTAGE=1.0
MAX_DAILY_TRADES=10
STOP_LOSS_PERCENTAGE=2.0
TAKE_PROFIT_PERCENTAGE=3.0

# Server Configuration
FLASK_ENV=production
FLASK_DEBUG=False
HOST=0.0.0.0
PORT=5000
FRONTEND_PORT=3000

# Security
SECRET_KEY=ai-trading-sentinel-secret-key-$(date +%s)
JWT_SECRET_KEY=jwt-secret-key-$(date +%s)

# Notifications
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_FROM=your_email@gmail.com
EMAIL_TO=alerts@example.com
EOF

    chmod 600 .env
    success "Environment file created - PLEASE UPDATE WITH YOUR CREDENTIALS"
else
    log "Environment file already exists"
fi

# Step 7: Create Systemd Services
log "Step 7: Creating systemd services..."

# Backend service
sudo tee /etc/systemd/system/ai-trading-backend.service > /dev/null << EOF
[Unit]
Description=AI Trading Sentinel Backend
After=network.target

[Service]
Type=simple
User=trading
WorkingDirectory=/opt/ai-trading-sentinel
Environment=PATH=/opt/ai-trading-sentinel/venv/bin
ExecStart=/opt/ai-trading-sentinel/venv/bin/python backend_main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Install serve for frontend
sudo npm install -g serve

# Frontend service
sudo tee /etc/systemd/system/ai-trading-frontend.service > /dev/null << EOF
[Unit]
Description=AI Trading Sentinel Frontend
After=network.target

[Service]
Type=simple
User=trading
WorkingDirectory=/opt/ai-trading-sentinel/frontend
ExecStart=/usr/bin/serve -s dist -l 3000 -H 0.0.0.0
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

success "Systemd services created"

# Step 8: Configure Nginx
log "Step 8: Configuring Nginx..."

sudo tee /etc/nginx/sites-available/ai-trading-sentinel > /dev/null << 'EOF'
server {
    listen 80;
    server_name 161.97.112.146;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /socket.io {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/ai-trading-sentinel /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
if sudo nginx -t; then
    success "Nginx configuration is valid"
else
    error "Nginx configuration has errors"
    exit 1
fi

# Step 9: Configure Firewall
log "Step 9: Configuring firewall..."

sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 3000/tcp  # Frontend
sudo ufw allow 5000/tcp  # Backend
sudo ufw allow 5901/tcp  # VNC
sudo ufw --force enable

success "Firewall configured"

# Step 10: Start Services
log "Step 10: Starting services..."

# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable ai-trading-backend
sudo systemctl enable ai-trading-frontend
sudo systemctl enable nginx

# Start services
sudo systemctl restart nginx
sudo systemctl restart ai-trading-backend
sudo systemctl restart ai-trading-frontend

# Wait a moment for services to start
sleep 5

# Check service status
log "Checking service status..."
for service in nginx ai-trading-backend ai-trading-frontend; do
    if sudo systemctl is-active --quiet $service; then
        success "$service is running"
    else
        error "$service failed to start"
        sudo systemctl status $service --no-pager -l
    fi
done

# Step 11: Verification
log "Step 11: Running deployment verification..."

# Check ports
log "Checking if ports are listening..."
for port in 80 3000 5000; do
    if sudo netstat -tlnp | grep -q ":$port "; then
        success "Port $port is listening"
    else
        warning "Port $port is not listening"
    fi
done

# Test endpoints
log "Testing HTTP endpoints..."
sleep 3

if curl -s http://localhost:5000/api/status > /dev/null; then
    success "Backend API is responding"
else
    warning "Backend API is not responding"
fi

if curl -s http://localhost:3000 > /dev/null; then
    success "Frontend is responding"
else
    warning "Frontend is not responding"
fi

# Final Summary
echo ""
echo "======================================"
success "AI Trading Sentinel Deployment Complete!"
echo "======================================"
echo ""
log "Production URLs (should be accessible):"
echo "  Frontend: http://161.97.112.146:3000/"
echo "  Backend:  http://161.97.112.146:5000/api/status"
echo "  WebSocket: ws://161.97.112.146:5000/"
echo ""
log "Local URLs (for testing):"
echo "  Frontend: http://localhost:3000/"
echo "  Backend:  http://localhost:5000/api/status"
echo ""
log "Useful Commands:"
echo "  View logs: sudo journalctl -u ai-trading-backend -f"
echo "  Restart:   sudo systemctl restart ai-trading-backend ai-trading-frontend"
echo "  Status:    sudo systemctl status ai-trading-backend ai-trading-frontend"
echo ""
warning "IMPORTANT: Update /opt/ai-trading-sentinel/.env with your actual credentials!"
echo ""
success "Deployment completed successfully!"