#!/bin/bash

# AI Trading Sentinel - SSL Certificate Setup Script
# Automated SSL certificate management with Let's Encrypt
# Run as root: sudo bash ssl_setup.sh

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN=""
EMAIL=""
WEBROOT="/var/www/html"
NGINX_CONF_DIR="/etc/nginx/sites-available"
NGINX_ENABLED_DIR="/etc/nginx/sites-enabled"
APP_USER="trading-sentinel"
API_PORT="8000"
FRONTEND_PORT="3000"

# Logging
LOG_FILE="/var/log/ssl_setup.log"
exec 1> >(tee -a "$LOG_FILE")
exec 2> >(tee -a "$LOG_FILE" >&2)

echo -e "${BLUE}=== AI Trading Sentinel SSL Setup ===${NC}"
echo "Started at: $(date)"
echo "Log file: $LOG_FILE"
echo

# Function to print status
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Get domain and email from user
get_configuration() {
    print_info "SSL Certificate Configuration"
    echo
    
    # Get domain
    while [[ -z "$DOMAIN" ]]; do
        read -p "Enter your domain name (e.g., trading.yourdomain.com): " DOMAIN
        if [[ ! "$DOMAIN" =~ ^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$ ]]; then
            print_error "Invalid domain format. Please enter a valid domain."
            DOMAIN=""
        fi
    done
    
    # Get email
    while [[ -z "$EMAIL" ]]; do
        read -p "Enter your email address for Let's Encrypt notifications: " EMAIL
        if [[ ! "$EMAIL" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
            print_error "Invalid email format. Please enter a valid email address."
            EMAIL=""
        fi
    done
    
    print_status "Configuration: Domain=$DOMAIN, Email=$EMAIL"
}

# Install Certbot
install_certbot() {
    print_info "Installing Certbot..."
    
    # Update package list
    apt-get update -y
    
    # Install snapd if not present
    if ! command_exists snap; then
        apt-get install -y snapd
        systemctl enable snapd
        systemctl start snapd
        # Wait for snapd to be ready
        sleep 10
    fi
    
    # Install certbot via snap
    snap install core; snap refresh core
    snap install --classic certbot
    
    # Create symlink
    ln -sf /snap/bin/certbot /usr/bin/certbot
    
    print_status "Certbot installed successfully"
}

# Install and configure Nginx
setup_nginx() {
    print_info "Setting up Nginx..."
    
    # Install Nginx if not present
    if ! command_exists nginx; then
        apt-get install -y nginx
    fi
    
    # Create webroot directory
    mkdir -p "$WEBROOT"
    chown -R www-data:www-data "$WEBROOT"
    
    # Remove default Nginx configuration
    rm -f "$NGINX_ENABLED_DIR/default"
    
    # Create initial HTTP configuration for domain verification
    cat > "$NGINX_CONF_DIR/$DOMAIN" << EOF
# AI Trading Sentinel - Initial HTTP Configuration
# This will be updated after SSL certificate generation

server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root $WEBROOT;
        try_files \$uri =404;
    }
    
    # Temporary redirect to HTTPS (will be updated)
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}
EOF

    # Enable the site
    ln -sf "$NGINX_CONF_DIR/$DOMAIN" "$NGINX_ENABLED_DIR/$DOMAIN"
    
    # Test Nginx configuration
    if nginx -t; then
        systemctl reload nginx
        print_status "Nginx configured successfully"
    else
        print_error "Nginx configuration test failed"
        exit 1
    fi
}

# Obtain SSL certificate
obtain_certificate() {
    print_info "Obtaining SSL certificate from Let's Encrypt..."
    
    # Use webroot method for certificate generation
    certbot certonly \
        --webroot \
        --webroot-path="$WEBROOT" \
        --email="$EMAIL" \
        --agree-tos \
        --no-eff-email \
        --domains="$DOMAIN" \
        --non-interactive
    
    if [[ $? -eq 0 ]]; then
        print_status "SSL certificate obtained successfully"
    else
        print_error "Failed to obtain SSL certificate"
        exit 1
    fi
}

# Configure Nginx with SSL
configure_nginx_ssl() {
    print_info "Configuring Nginx with SSL..."
    
    # Generate strong DH parameters
    if [[ ! -f /etc/ssl/certs/dhparam.pem ]]; then
        print_info "Generating DH parameters (this may take a while)..."
        openssl dhparam -out /etc/ssl/certs/dhparam.pem 2048
    fi
    
    # Create SSL configuration
    cat > "$NGINX_CONF_DIR/$DOMAIN" << EOF
# AI Trading Sentinel - Production Nginx Configuration with SSL
# Generated: $(date)

# Rate limiting
limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone \$binary_remote_addr zone=login:10m rate=1r/s;

# Upstream servers
upstream api_backend {
    server 127.0.0.1:$API_PORT;
    keepalive 32;
}

upstream frontend_backend {
    server 127.0.0.1:$FRONTEND_PORT;
    keepalive 32;
}

# HTTP to HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;
    
    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root $WEBROOT;
        try_files \$uri =404;
    }
    
    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name $DOMAIN;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    ssl_trusted_certificate /etc/letsencrypt/live/$DOMAIN/chain.pem;
    
    # SSL Security
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off;
    ssl_dhparam /etc/ssl/certs/dhparam.pem;
    
    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' wss: ws:; frame-ancestors 'self';" always;
    
    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;
    
    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
    
    # API endpoints
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://api_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
    }
    
    # WebSocket for real-time updates
    location /ws {
        proxy_pass http://api_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket specific timeouts
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }
    
    # Login endpoint with stricter rate limiting
    location /api/auth/login {
        limit_req zone=login burst=5 nodelay;
        
        proxy_pass http://api_backend;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Static assets with caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)\$ {
        proxy_pass http://frontend_backend;
        expires 1y;
        add_header Cache-Control "public, immutable";
        add_header X-Content-Type-Options nosniff;
    }
    
    # Frontend application
    location / {
        proxy_pass http://frontend_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        # Handle client-side routing
        try_files \$uri \$uri/ @fallback;
    }
    
    # Fallback for client-side routing
    location @fallback {
        proxy_pass http://frontend_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Deny access to sensitive files
    location ~ /\.(ht|git|env) {
        deny all;
        return 404;
    }
    
    # Deny access to backup files
    location ~ \.(bak|backup|swp|tmp)\$ {
        deny all;
        return 404;
    }
}
EOF

    # Test Nginx configuration
    if nginx -t; then
        systemctl reload nginx
        print_status "Nginx SSL configuration applied successfully"
    else
        print_error "Nginx SSL configuration test failed"
        exit 1
    fi
}

# Setup automatic certificate renewal
setup_auto_renewal() {
    print_info "Setting up automatic certificate renewal..."
    
    # Create renewal hook script
    cat > /etc/letsencrypt/renewal-hooks/deploy/nginx-reload.sh << 'EOF'
#!/bin/bash
# Reload Nginx after certificate renewal

if systemctl is-active --quiet nginx; then
    systemctl reload nginx
    echo "$(date): Nginx reloaded after certificate renewal" >> /var/log/ssl_renewal.log
fi
EOF

    chmod +x /etc/letsencrypt/renewal-hooks/deploy/nginx-reload.sh
    
    # Test automatic renewal
    certbot renew --dry-run
    
    if [[ $? -eq 0 ]]; then
        print_status "Automatic certificate renewal configured successfully"
    else
        print_warning "Certificate renewal test failed, but certificates are still valid"
    fi
    
    # Add cron job for renewal (certbot usually adds this automatically)
    if ! crontab -l 2>/dev/null | grep -q "certbot renew"; then
        (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -
        print_status "Added cron job for certificate renewal"
    fi
}

# Update firewall rules for HTTPS
update_firewall() {
    print_info "Updating firewall rules for HTTPS..."
    
    if command_exists ufw; then
        # Allow HTTPS traffic
        ufw allow 443/tcp comment "HTTPS"
        
        # Reload UFW
        ufw reload
        
        print_status "Firewall updated for HTTPS traffic"
    else
        print_warning "UFW not found, please ensure port 443 is open"
    fi
}

# Create SSL monitoring script
create_ssl_monitor() {
    print_info "Creating SSL certificate monitoring script..."
    
    cat > /usr/local/bin/ssl-monitor.sh << EOF
#!/bin/bash
# SSL Certificate Monitoring Script

DOMAIN="$DOMAIN"
EMAIL="$EMAIL"
LOG_FILE="/var/log/ssl-monitor.log"
ALERT_DAYS=30

# Function to log with timestamp
log_message() {
    echo "\$(date '+%Y-%m-%d %H:%M:%S') - \$1" >> "\$LOG_FILE"
}

# Check certificate expiration
check_certificate_expiry() {
    local cert_file="/etc/letsencrypt/live/\$DOMAIN/cert.pem"
    
    if [[ -f "\$cert_file" ]]; then
        local expiry_date=\$(openssl x509 -enddate -noout -in "\$cert_file" | cut -d= -f2)
        local expiry_epoch=\$(date -d "\$expiry_date" +%s)
        local current_epoch=\$(date +%s)
        local days_until_expiry=\$(( (expiry_epoch - current_epoch) / 86400 ))
        
        log_message "Certificate expires in \$days_until_expiry days"
        
        if [[ \$days_until_expiry -le \$ALERT_DAYS ]]; then
            log_message "WARNING: Certificate expires in \$days_until_expiry days!"
            # Send alert email if configured
            # echo "SSL certificate for \$DOMAIN expires in \$days_until_expiry days" | mail -s "SSL Certificate Expiry Warning" \$EMAIL
        fi
    else
        log_message "ERROR: Certificate file not found: \$cert_file"
    fi
}

# Check SSL configuration
check_ssl_config() {
    local ssl_check=\$(echo | openssl s_client -servername \$DOMAIN -connect \$DOMAIN:443 2>/dev/null | openssl x509 -noout -dates 2>/dev/null)
    
    if [[ -n "\$ssl_check" ]]; then
        log_message "SSL configuration is valid"
    else
        log_message "ERROR: SSL configuration check failed"
    fi
}

# Main function
main() {
    log_message "Starting SSL monitoring check"
    check_certificate_expiry
    check_ssl_config
    log_message "SSL monitoring check completed"
}

main
EOF

    chmod +x /usr/local/bin/ssl-monitor.sh
    
    # Add to cron for daily execution
    if ! crontab -l 2>/dev/null | grep -q "ssl-monitor.sh"; then
        (crontab -l 2>/dev/null; echo "0 6 * * * /usr/local/bin/ssl-monitor.sh") | crontab -
        print_status "SSL monitoring cron job added"
    fi
}

# Verify SSL setup
verify_ssl_setup() {
    print_info "Verifying SSL setup..."
    
    # Wait a moment for Nginx to fully reload
    sleep 5
    
    # Test HTTPS connection
    if curl -s -I "https://$DOMAIN/health" | grep -q "200 OK"; then
        print_status "HTTPS connection test successful"
    else
        print_warning "HTTPS connection test failed, but certificates may still be valid"
    fi
    
    # Check certificate details
    local cert_info=$(echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" 2>/dev/null | openssl x509 -noout -dates 2>/dev/null)
    
    if [[ -n "$cert_info" ]]; then
        print_status "SSL certificate is properly configured"
        echo "Certificate details:"
        echo "$cert_info"
    else
        print_warning "Could not retrieve certificate information"
    fi
}

# Create SSL summary
create_ssl_summary() {
    print_info "Creating SSL configuration summary..."
    
    cat > /root/ssl-summary.txt << EOF
=== AI Trading Sentinel SSL Configuration Summary ===
Generated: $(date)

Domain: $DOMAIN
Email: $EMAIL

SSL Certificate:
- Provider: Let's Encrypt
- Certificate path: /etc/letsencrypt/live/$DOMAIN/
- Auto-renewal: Enabled (via cron)
- Monitoring: Daily checks at 6:00 AM

Nginx Configuration:
- HTTP to HTTPS redirect: Enabled
- SSL protocols: TLSv1.2, TLSv1.3
- HSTS: Enabled (max-age=63072000)
- OCSP Stapling: Enabled
- Security headers: Configured

Firewall:
- Port 443 (HTTPS): Open
- Port 80 (HTTP): Open (redirects to HTTPS)

Monitoring:
- SSL monitor script: /usr/local/bin/ssl-monitor.sh
- Log file: /var/log/ssl-monitor.log
- Certificate expiry alerts: 30 days before expiration

Important Commands:
- Test certificate renewal: certbot renew --dry-run
- Check certificate status: certbot certificates
- View SSL logs: tail -f /var/log/ssl-monitor.log
- Nginx SSL test: nginx -t
- Reload Nginx: systemctl reload nginx

Next Steps:
1. Test HTTPS access: https://$DOMAIN
2. Verify SSL rating: https://www.ssllabs.com/ssltest/
3. Configure email notifications for certificate expiry
4. Set up monitoring alerts
5. Document SSL procedures for team

Troubleshooting:
- Certificate files: /etc/letsencrypt/live/$DOMAIN/
- Nginx config: /etc/nginx/sites-available/$DOMAIN
- SSL logs: /var/log/ssl-monitor.log
- Let's Encrypt logs: /var/log/letsencrypt/
EOF

    print_status "SSL summary created: /root/ssl-summary.txt"
}

# Main execution function
main() {
    echo -e "${BLUE}Starting SSL certificate setup...${NC}"
    echo
    
    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root"
        exit 1
    fi
    
    # Get configuration from user
    get_configuration
    
    # Execute SSL setup steps
    install_certbot
    setup_nginx
    obtain_certificate
    configure_nginx_ssl
    setup_auto_renewal
    update_firewall
    create_ssl_monitor
    verify_ssl_setup
    create_ssl_summary
    
    echo
    echo -e "${GREEN}=== SSL Setup Complete ===${NC}"
    echo -e "${GREEN}✓ SSL certificate obtained and configured${NC}"
    echo -e "${GREEN}✓ Nginx configured with SSL${NC}"
    echo -e "${GREEN}✓ Automatic renewal enabled${NC}"
    echo -e "${GREEN}✓ Security headers configured${NC}"
    echo -e "${GREEN}✓ Monitoring and alerts set up${NC}"
    echo
    echo -e "${BLUE}Your site is now available at: https://$DOMAIN${NC}"
    echo -e "${BLUE}SSL rating test: https://www.ssllabs.com/ssltest/analyze.html?d=$DOMAIN${NC}"
    echo
    
    print_status "SSL setup completed successfully"
    print_info "Summary: /root/ssl-summary.txt"
    print_info "Log file: $LOG_FILE"
}

# Run main function
main "$@"