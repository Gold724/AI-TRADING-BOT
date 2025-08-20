# AI Trading Sentinel - Frontend Deployment Script (PowerShell)
# Deploy React frontend to production VPS with Nginx configuration

Write-Host "AI Trading Sentinel - Frontend Deployment" -ForegroundColor Blue
Write-Host "=========================================" -ForegroundColor Blue

# Configuration
$VPS_IP = "185.244.214.70"
$VPS_USER = "root"
$FRONTEND_DIR = "/var/www/ai-trading-sentinel"
$NGINX_CONF = "/etc/nginx/sites-available/ai-trading-sentinel-frontend"

function Write-Info($message) {
    Write-Host "[INFO] $message" -ForegroundColor Cyan
}

function Write-Success($message) {
    Write-Host "[SUCCESS] $message" -ForegroundColor Green
}

function Write-Warning($message) {
    Write-Host "[WARNING] $message" -ForegroundColor Yellow
}

function Write-Error($message) {
    Write-Host "[ERROR] $message" -ForegroundColor Red
}

# Check if build directory exists
if (-not (Test-Path "frontend\dist")) {
    Write-Error "Frontend build directory not found. Please run 'npm run build' first."
    exit 1
}

Write-Info "Frontend build found. Creating deployment package..."

# Create deployment package
if (Test-Path "frontend-deployment.tar.gz") {
    Remove-Item "frontend-deployment.tar.gz" -Force
}

# Use tar command (available in Windows 10+)
try {
    Set-Location "frontend\dist"
    tar -czf "..\..\frontend-deployment.tar.gz" *
    Set-Location "..\.." 
    Write-Success "Deployment package created successfully"
} catch {
    Write-Error "Failed to create deployment package: $_"
    exit 1
}

# Create Nginx configuration content
$nginxConfig = @'
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
'@

# Save Nginx config to file
$nginxConfig | Out-File -FilePath "nginx-frontend.conf" -Encoding UTF8

Write-Info "Deployment package and configuration files ready"
Write-Warning "Manual VPS deployment required due to connection issues"

Write-Host ""
Write-Host "MANUAL DEPLOYMENT STEPS:" -ForegroundColor Yellow
Write-Host "========================" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Upload files to VPS:"
Write-Host "   - frontend-deployment.tar.gz"
Write-Host "   - nginx-frontend.conf"
Write-Host ""
Write-Host "2. Connect to VPS and run these commands:"
Write-Host ""
Write-Host "   sudo mkdir -p /var/www/ai-trading-sentinel"
Write-Host "   cd /var/www/ai-trading-sentinel"
Write-Host "   sudo tar -xzf /path/to/frontend-deployment.tar.gz"
Write-Host "   sudo chown -R www-data:www-data /var/www/ai-trading-sentinel"
Write-Host "   sudo chmod -R 755 /var/www/ai-trading-sentinel"
Write-Host ""
Write-Host "   sudo cp /path/to/nginx-frontend.conf /etc/nginx/sites-available/ai-trading-sentinel-frontend"
Write-Host "   sudo ln -sf /etc/nginx/sites-available/ai-trading-sentinel-frontend /etc/nginx/sites-enabled/"
Write-Host "   sudo rm -f /etc/nginx/sites-enabled/default"
Write-Host ""
Write-Host "   sudo nginx -t"
Write-Host "   sudo systemctl reload nginx"
Write-Host "   sudo systemctl enable nginx"
Write-Host ""
Write-Host "3. Verify deployment:"
Write-Host "   curl -I http://185.244.214.70"
Write-Host "   curl http://185.244.214.70/api/health"
Write-Host ""

Write-Success "Deployment files prepared successfully!"
Write-Host ""
Write-Host "Expected URLs after deployment:" -ForegroundColor Cyan
Write-Host "  Frontend: http://185.244.214.70" -ForegroundColor White
Write-Host "  API: http://185.244.214.70/api/" -ForegroundColor White
Write-Host "  Health Check: http://185.244.214.70/health" -ForegroundColor White
Write-Host ""
Write-Warning "Next Steps:"
Write-Host "  1. Complete manual VPS deployment"
Write-Host "  2. Test frontend functionality"
Write-Host "  3. Configure SSL/HTTPS (optional)"
Write-Host "  4. Setup monitoring and alerts"
Write-Host "  5. Begin live trading with minimal risk"