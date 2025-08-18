# 🚀 AI Trading Sentinel - Frontend VPS Deployment Script (PowerShell)
# Deploy React frontend to Contabo VPS with Nginx

param(
    [string]$VpsIp = "161.97.112.146",
    [string]$VpsUser = "root",
    [string]$SshPort = "22"
)

# Configuration
$FrontendDomain = "trading.trae.ai"  # Optional: replace with your domain
$WebRoot = "/var/www/trae-frontend"

# Colors for output
$Red = "`e[31m"
$Green = "`e[32m"
$Yellow = "`e[33m"
$Blue = "`e[34m"
$Reset = "`e[0m"

function Write-Status {
    param([string]$Message)
    Write-Host "${Blue}[INFO]${Reset} $Message"
}

function Write-Success {
    param([string]$Message)
    Write-Host "${Green}[SUCCESS]${Reset} $Message"
}

function Write-Warning {
    param([string]$Message)
    Write-Host "${Yellow}[WARNING]${Reset} $Message"
}

function Write-Error {
    param([string]$Message)
    Write-Host "${Red}[ERROR]${Reset} $Message"
}

Write-Host "🚀 Starting Frontend VPS Deployment..." -ForegroundColor Cyan

# Check if frontend build exists
if (-not (Test-Path "frontend\dist")) {
    Write-Error "Frontend build not found. Please run 'npm run build' in frontend directory first."
    exit 1
}

Write-Status "Frontend build found. Proceeding with deployment..."

# Check if required tools are available
if (-not (Get-Command "scp" -ErrorAction SilentlyContinue)) {
    Write-Error "SCP not found. Please install OpenSSH client or use WSL."
    Write-Host "Install with: Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0" -ForegroundColor Yellow
    exit 1
}

if (-not (Get-Command "ssh" -ErrorAction SilentlyContinue)) {
    Write-Error "SSH not found. Please install OpenSSH client or use WSL."
    Write-Host "Install with: Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0" -ForegroundColor Yellow
    exit 1
}

# Create deployment package using tar (available in Windows 10+)
Write-Status "Creating deployment package..."
if (Test-Path "frontend-dist.tar.gz") {
    Remove-Item "frontend-dist.tar.gz" -Force
}

# Use PowerShell to create tar archive
Set-Location "frontend"
tar -czf "../frontend-dist.tar.gz" -C "." "dist"
Set-Location ".."

if (-not (Test-Path "frontend-dist.tar.gz")) {
    Write-Error "Failed to create deployment package."
    exit 1
}

# Upload frontend build to VPS
Write-Status "Uploading frontend build to VPS..."
try {
    scp -P $SshPort "frontend-dist.tar.gz" "${VpsUser}@${VpsIp}:/tmp/"
    if ($LASTEXITCODE -ne 0) {
        throw "SCP upload failed"
    }
} catch {
    Write-Error "Failed to upload frontend build: $_"
    exit 1
}

# SSH into VPS and setup frontend
Write-Status "Setting up frontend on VPS..."

$SshScript = @'
set -e

# Install Nginx if not already installed
if ! command -v nginx &> /dev/null; then
    echo "Installing Nginx..."
    apt update
    apt install -y nginx
    systemctl enable nginx
fi

# Create web root directory
sudo mkdir -p /var/www/trae-frontend

# Extract frontend build
cd /tmp
tar -xzf frontend-dist.tar.gz
sudo cp -r dist/* /var/www/trae-frontend/
sudo chown -R www-data:www-data /var/www/trae-frontend
sudo chmod -R 755 /var/www/trae-frontend

# Create Nginx configuration
sudo tee /etc/nginx/sites-available/trae-frontend > /dev/null << 'NGINX_CONFIG'
server {
    listen 80;
    listen [::]:80;
    
    server_name 161.97.112.146 trading.trae.ai;
    root /var/www/trae-frontend;
    index index.html;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Handle React Router (SPA)
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API proxy to Flask backend
    location /api/ {
        proxy_pass http://127.0.0.1:5000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    
    # WebSocket proxy for real-time updates
    location /ws {
        proxy_pass http://127.0.0.1:5000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Static assets caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Deny access to hidden files
    location ~ /\. {
        deny all;
    }
}
NGINX_CONFIG

# Enable the site
sudo ln -sf /etc/nginx/sites-available/trae-frontend /etc/nginx/sites-enabled/

# Remove default Nginx site if it exists
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
echo "Testing Nginx configuration..."
sudo nginx -t

# Restart Nginx
echo "Restarting Nginx..."
sudo systemctl restart nginx
sudo systemctl status nginx --no-pager

# Configure firewall for HTTP/HTTPS
echo "Configuring firewall..."
sudo ufw allow 'Nginx Full'
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Cleanup
rm -f /tmp/frontend-dist.tar.gz

echo "✅ Frontend deployment completed successfully!"
echo "🌐 Frontend is now accessible at: http://161.97.112.146"
echo "🔧 Backend API accessible at: http://161.97.112.146/api/"
echo "📡 WebSocket endpoint: ws://161.97.112.146/ws"
'@

try {
    $SshScript | ssh -p $SshPort "${VpsUser}@${VpsIp}" 'bash -s'
    if ($LASTEXITCODE -ne 0) {
        throw "SSH deployment script failed"
    }
} catch {
    Write-Error "Failed to setup frontend on VPS: $_"
    exit 1
}

# Cleanup local files
Remove-Item "frontend-dist.tar.gz" -Force -ErrorAction SilentlyContinue

Write-Success "Frontend deployment completed!"
Write-Success "🌐 Frontend URL: http://$VpsIp"
Write-Success "🔧 API URL: http://$VpsIp/api/"
Write-Success "📡 WebSocket: ws://$VpsIp/ws"

Write-Status "Testing frontend accessibility..."
try {
    $FrontendResponse = Invoke-WebRequest -Uri "http://$VpsIp/" -Method Head -TimeoutSec 10 -ErrorAction Stop
    Write-Host " - Frontend: ✅ Accessible (Status: $($FrontendResponse.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host " - Frontend: ❌ Not accessible" -ForegroundColor Red
}

try {
    $ApiResponse = Invoke-WebRequest -Uri "http://$VpsIp/api/health" -Method Head -TimeoutSec 10 -ErrorAction Stop
    Write-Host " - API: ✅ Accessible (Status: $($ApiResponse.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host " - API: ❌ Not accessible" -ForegroundColor Red
}

Write-Success "🚀 AI Trading Sentinel is now fully deployed in the cloud!"
Write-Host ""
Write-Host "📋 Access Points:" -ForegroundColor Cyan
Write-Host "   Frontend: http://$VpsIp" -ForegroundColor White
Write-Host "   API: http://$VpsIp/api/" -ForegroundColor White
Write-Host "   Health: http://$VpsIp/api/health" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Management Commands:" -ForegroundColor Cyan
Write-Host "   sudo systemctl status nginx" -ForegroundColor White
Write-Host "   sudo systemctl status trae-backend" -ForegroundColor White
Write-Host "   sudo tail -f /var/log/nginx/access.log" -ForegroundColor White
Write-Host "   sudo tail -f /var/log/nginx/error.log" -ForegroundColor White

Write-Host ""
Write-Host "💡 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Access the trading dashboard at http://$VpsIp" -ForegroundColor White
Write-Host "   2. Configure SSL certificate for HTTPS (optional)" -ForegroundColor White
Write-Host "   3. Set up domain name (optional)" -ForegroundColor White
Write-Host "   4. Monitor logs and performance" -ForegroundColor White