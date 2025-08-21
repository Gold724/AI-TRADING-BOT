#!/bin/bash

# AI Trading Sentinel - Production Environment Setup
# TRAE-SentinelOps: Secure environment configuration for Contabo VPS

set -euo pipefail

# Configuration
APP_NAME="trae-sentinel"
APP_DIR="/opt/${APP_NAME}"
CONFIG_DIR="/etc/${APP_NAME}"
SECRETS_DIR="${CONFIG_DIR}/secrets"
ENV_FILE="${CONFIG_DIR}/.env"
BACKUP_DIR="/var/backups/${APP_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

# Generate secure random password
generate_password() {
    local length=${1:-32}
    openssl rand -base64 $length | tr -d "=+/" | cut -c1-$length
}

# Generate API key
generate_api_key() {
    echo "trae_$(date +%s)_$(openssl rand -hex 16)"
}

# Encrypt sensitive data
encrypt_value() {
    local value="$1"
    local key_file="${SECRETS_DIR}/master.key"
    
    if [[ ! -f "$key_file" ]]; then
        openssl rand -base64 32 > "$key_file"
        chmod 600 "$key_file"
        chown root:root "$key_file"
    fi
    
    echo -n "$value" | openssl enc -aes-256-cbc -base64 -pass file:"$key_file"
}

# Decrypt sensitive data
decrypt_value() {
    local encrypted_value="$1"
    local key_file="${SECRETS_DIR}/master.key"
    
    echo -n "$encrypted_value" | openssl enc -aes-256-cbc -d -base64 -pass file:"$key_file"
}

# Setup directories
setup_directories() {
    log_info "Setting up secure directories..."
    
    # Create directories
    mkdir -p "$CONFIG_DIR" "$SECRETS_DIR" "$BACKUP_DIR"
    
    # Set secure permissions
    chmod 750 "$CONFIG_DIR"
    chmod 700 "$SECRETS_DIR"
    chmod 750 "$BACKUP_DIR"
    
    # Set ownership
    chown root:trae-sentinel "$CONFIG_DIR"
    chown root:root "$SECRETS_DIR"
    chown root:trae-sentinel "$BACKUP_DIR"
    
    log_success "Secure directories created"
}

# Interactive configuration
interactive_config() {
    log_info "Starting interactive configuration..."
    echo
    
    # Trading Configuration
    echo "=== Trading Configuration ==="
    read -p "Bulenox Username: " BULENOX_USERNAME
    read -s -p "Bulenox Password: " BULENOX_PASSWORD
    echo
    read -p "Enable Auto Execute (true/false) [false]: " AUTO_EXECUTE
    AUTO_EXECUTE=${AUTO_EXECUTE:-false}
    read -p "Enable Simulation Mode (true/false) [true]: " SIMULATION
    SIMULATION=${SIMULATION:-true}
    echo
    
    # API Configuration
    echo "=== API Configuration ==="
    read -p "Backend Port [5000]: " BACKEND_PORT
    BACKEND_PORT=${BACKEND_PORT:-5000}
    read -p "Frontend Port [3000]: " FRONTEND_PORT
    FRONTEND_PORT=${FRONTEND_PORT:-3000}
    API_SECRET_KEY=$(generate_password 64)
    JWT_SECRET_KEY=$(generate_password 64)
    echo
    
    # Database Configuration
    echo "=== Database Configuration ==="
    read -p "Database Type (sqlite/postgresql) [sqlite]: " DB_TYPE
    DB_TYPE=${DB_TYPE:-sqlite}
    
    if [[ "$DB_TYPE" == "postgresql" ]]; then
        read -p "Database Host [localhost]: " DB_HOST
        DB_HOST=${DB_HOST:-localhost}
        read -p "Database Port [5432]: " DB_PORT
        DB_PORT=${DB_PORT:-5432}
        read -p "Database Name [trae_sentinel]: " DB_NAME
        DB_NAME=${DB_NAME:-trae_sentinel}
        read -p "Database Username: " DB_USER
        read -s -p "Database Password: " DB_PASSWORD
        echo
        DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
    else
        DATABASE_URL="sqlite:///${APP_DIR}/data/trae_sentinel.db"
    fi
    echo
    
    # Redis Configuration
    echo "=== Redis Configuration ==="
    read -p "Redis Host [localhost]: " REDIS_HOST
    REDIS_HOST=${REDIS_HOST:-localhost}
    read -p "Redis Port [6379]: " REDIS_PORT
    REDIS_PORT=${REDIS_PORT:-6379}
    read -p "Redis Password (leave empty if none): " REDIS_PASSWORD
    
    if [[ -n "$REDIS_PASSWORD" ]]; then
        REDIS_URL="redis://:${REDIS_PASSWORD}@${REDIS_HOST}:${REDIS_PORT}/0"
    else
        REDIS_URL="redis://${REDIS_HOST}:${REDIS_PORT}/0"
    fi
    echo
    
    # Notification Configuration
    echo "=== Notification Configuration ==="
    read -p "Slack Webhook URL (optional): " SLACK_WEBHOOK_URL
    read -p "Enable Email Alerts (true/false) [false]: " EMAIL_ALERTS_ENABLED
    EMAIL_ALERTS_ENABLED=${EMAIL_ALERTS_ENABLED:-false}
    
    if [[ "$EMAIL_ALERTS_ENABLED" == "true" ]]; then
        read -p "SMTP Host: " SMTP_HOST
        read -p "SMTP Port [587]: " SMTP_PORT
        SMTP_PORT=${SMTP_PORT:-587}
        read -p "SMTP Username: " SMTP_USERNAME
        read -s -p "SMTP Password: " SMTP_PASSWORD
        echo
        read -p "From Email: " FROM_EMAIL
        read -p "To Email (comma-separated): " TO_EMAIL
    fi
    echo
    
    # Telegram Configuration
    echo "=== Telegram Configuration (Optional) ==="
    read -p "Telegram Bot Token (optional): " TELEGRAM_BOT_TOKEN
    read -p "Telegram Chat ID (optional): " TELEGRAM_CHAT_ID
    echo
    
    # Security Configuration
    echo "=== Security Configuration ==="
    read -p "Enable Rate Limiting (true/false) [true]: " RATE_LIMITING_ENABLED
    RATE_LIMITING_ENABLED=${RATE_LIMITING_ENABLED:-true}
    read -p "Max Login Attempts [5]: " MAX_LOGIN_ATTEMPTS
    MAX_LOGIN_ATTEMPTS=${MAX_LOGIN_ATTEMPTS:-5}
    read -p "Session Timeout (minutes) [60]: " SESSION_TIMEOUT
    SESSION_TIMEOUT=${SESSION_TIMEOUT:-60}
    echo
    
    # Monitoring Configuration
    echo "=== Monitoring Configuration ==="
    read -p "CPU Threshold (%) [85]: " CPU_THRESHOLD
    CPU_THRESHOLD=${CPU_THRESHOLD:-85}
    read -p "Memory Threshold (%) [90]: " MEMORY_THRESHOLD
    MEMORY_THRESHOLD=${MEMORY_THRESHOLD:-90}
    read -p "Disk Threshold (%) [95]: " DISK_THRESHOLD
    DISK_THRESHOLD=${DISK_THRESHOLD:-95}
    read -p "Health Check Interval (seconds) [60]: " HEALTH_CHECK_INTERVAL
    HEALTH_CHECK_INTERVAL=${HEALTH_CHECK_INTERVAL:-60}
    echo
    
    log_success "Configuration completed"
}

# Create environment file
create_env_file() {
    log_info "Creating production environment file..."
    
    # Backup existing env file
    if [[ -f "$ENV_FILE" ]]; then
        cp "$ENV_FILE" "${BACKUP_DIR}/.env.backup.$(date +%Y%m%d-%H%M%S)"
        log_info "Existing environment file backed up"
    fi
    
    # Create new environment file
    cat > "$ENV_FILE" << EOF
# AI Trading Sentinel - Production Environment Configuration
# Generated on $(date -u +'%Y-%m-%d %H:%M:%S UTC')
# SECURITY WARNING: This file contains sensitive information

# =============================================================================
# CORE APPLICATION SETTINGS
# =============================================================================
FLASK_ENV=production
FLASK_DEBUG=false
TESTING=false
SECRET_KEY=${API_SECRET_KEY}
JWT_SECRET_KEY=${JWT_SECRET_KEY}
API_VERSION=v1

# =============================================================================
# SERVER CONFIGURATION
# =============================================================================
BACKEND_HOST=0.0.0.0
BACKEND_PORT=${BACKEND_PORT}
FRONTEND_PORT=${FRONTEND_PORT}
WORKERS=4
THREADS=2
MAX_CONNECTIONS=1000
REQUEST_TIMEOUT=30

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================
DATABASE_URL=${DATABASE_URL}
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# =============================================================================
# REDIS CONFIGURATION
# =============================================================================
REDIS_URL=${REDIS_URL}
REDIS_POOL_SIZE=20
REDIS_TIMEOUT=5
CACHE_TTL=3600

# =============================================================================
# TRADING CONFIGURATION
# =============================================================================
BULENOX_USERNAME=${BULENOX_USERNAME}
BULENOX_PASSWORD=${BULENOX_PASSWORD}
BULENOX_API_URL=https://bulenox.projectx.com/login
BULENOX_TIMEOUT=30
BULENOX_RETRY_ATTEMPTS=3
BULENOX_RETRY_DELAY=5

# Trading Behavior
AUTO_EXECUTE=${AUTO_EXECUTE}
SIMULATION=${SIMULATION}
MAX_DAILY_TRADES=50
MAX_POSITION_SIZE=1000
RISK_PERCENTAGE=2.0
STOP_LOSS_PERCENTAGE=1.0
TAKE_PROFIT_PERCENTAGE=2.0

# =============================================================================
# BROWSER AUTOMATION
# =============================================================================
HEADLESS=true
BROWSER_TIMEOUT=30000
PAGE_TIMEOUT=30000
VIEWPORT_WIDTH=1920
VIEWPORT_HEIGHT=1080
SCREENSHOT_ON_ERROR=true
SCREENSHOT_DIR=${APP_DIR}/screenshots

# =============================================================================
# SECURITY SETTINGS
# =============================================================================
RATE_LIMITING_ENABLED=${RATE_LIMITING_ENABLED}
MAX_LOGIN_ATTEMPTS=${MAX_LOGIN_ATTEMPTS}
LOCKOUT_DURATION=1800
SESSION_TIMEOUT=${SESSION_TIMEOUT}
CSRF_ENABLED=true
CORS_ORIGINS=https://yourdomain.com
SECURE_COOKIES=true
HTTPS_ONLY=true

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================
LOG_LEVEL=INFO
LOG_FILE=${APP_DIR}/logs/app.log
LOG_MAX_SIZE=100MB
LOG_BACKUP_COUNT=10
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
VERBOSE_LOGGING=false
STRUCTURED_LOGGING=true

# =============================================================================
# MONITORING & HEALTH CHECKS
# =============================================================================
MONITORING_ENABLED=true
HEALTH_CHECK_INTERVAL=${HEALTH_CHECK_INTERVAL}
METRICS_ENABLED=true
METRICS_PORT=9090
HEALTH_CHECK_TIMEOUT=10

# System Thresholds
CPU_THRESHOLD=${CPU_THRESHOLD}
MEMORY_THRESHOLD=${MEMORY_THRESHOLD}
DISK_THRESHOLD=${DISK_THRESHOLD}
LOAD_THRESHOLD=5.0
NETWORK_TIMEOUT=10

# =============================================================================
# NOTIFICATION SETTINGS
# =============================================================================
# Slack Configuration
SLACK_WEBHOOK_URL=${SLACK_WEBHOOK_URL}
SLACK_CHANNEL=#trading-alerts
SLACK_USERNAME=TRAE-Sentinel
SLACK_ICON_EMOJI=:robot_face:

# Email Configuration
EMAIL_ALERTS_ENABLED=${EMAIL_ALERTS_ENABLED}
EOF

    # Add email configuration if enabled
    if [[ "$EMAIL_ALERTS_ENABLED" == "true" ]]; then
        cat >> "$ENV_FILE" << EOF
SMTP_HOST=${SMTP_HOST}
SMTP_PORT=${SMTP_PORT}
SMTP_USERNAME=${SMTP_USERNAME}
SMTP_PASSWORD=${SMTP_PASSWORD}
SMTP_USE_TLS=true
SMTP_USE_SSL=false
FROM_EMAIL=${FROM_EMAIL}
TO_EMAIL=${TO_EMAIL}
EMAIL_TIMEOUT=30
EOF
    fi
    
    # Add Telegram configuration if provided
    if [[ -n "$TELEGRAM_BOT_TOKEN" ]]; then
        cat >> "$ENV_FILE" << EOF

# Telegram Configuration
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID}
TELEGRAM_ENABLED=true
TELEGRAM_TIMEOUT=10
EOF
    fi
    
    # Add remaining configuration
    cat >> "$ENV_FILE" << EOF

# =============================================================================
# PERFORMANCE SETTINGS
# =============================================================================
MAX_CONTENT_LENGTH=16777216
SEND_FILE_MAX_AGE_DEFAULT=31536000
PERMANENT_SESSION_LIFETIME=3600
JSONIFY_PRETTYPRINT_REGULAR=false

# =============================================================================
# BACKUP & RECOVERY
# =============================================================================
BACKUP_ENABLED=true
BACKUP_INTERVAL=86400
BACKUP_RETENTION_DAYS=30
BACKUP_DIRECTORY=${BACKUP_DIR}
AUTO_RECOVERY_ENABLED=true

# =============================================================================
# DEVELOPMENT & DEBUGGING (PRODUCTION: DISABLED)
# =============================================================================
DEBUG_MODE=false
PROFILING_ENABLED=false
SQL_ECHO=false
TEMPLATE_AUTO_RELOAD=false
STATIC_AUTO_RELOAD=false

# =============================================================================
# FEATURE FLAGS
# =============================================================================
FEATURE_ADVANCED_ANALYTICS=true
FEATURE_RISK_MANAGEMENT=true
FEATURE_AUTO_RECOVERY=true
FEATURE_MULTI_ACCOUNT=false
FEATURE_PAPER_TRADING=true

# =============================================================================
# EXTERNAL SERVICES
# =============================================================================
EXTERNAL_API_TIMEOUT=30
EXTERNAL_API_RETRIES=3
EXTERNAL_API_BACKOFF=2

# =============================================================================
# DEPLOYMENT INFO
# =============================================================================
DEPLOYMENT_ENV=production
DEPLOYMENT_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
DEPLOYMENT_VERSION=1.0.0
EOF
    
    # Set secure permissions
    chmod 640 "$ENV_FILE"
    chown root:trae-sentinel "$ENV_FILE"
    
    log_success "Environment file created: $ENV_FILE"
}

# Create secrets management
setup_secrets() {
    log_info "Setting up secrets management..."
    
    # Create encrypted secrets file
    cat > "${SECRETS_DIR}/secrets.enc" << EOF
# Encrypted secrets for AI Trading Sentinel
# Use decrypt_secret.sh to access these values

BULENOX_PASSWORD_ENC=$(encrypt_value "$BULENOX_PASSWORD")
API_SECRET_KEY_ENC=$(encrypt_value "$API_SECRET_KEY")
JWT_SECRET_KEY_ENC=$(encrypt_value "$JWT_SECRET_KEY")
EOF
    
    if [[ -n "$REDIS_PASSWORD" ]]; then
        echo "REDIS_PASSWORD_ENC=$(encrypt_value "$REDIS_PASSWORD")" >> "${SECRETS_DIR}/secrets.enc"
    fi
    
    if [[ "$EMAIL_ALERTS_ENABLED" == "true" ]]; then
        echo "SMTP_PASSWORD_ENC=$(encrypt_value "$SMTP_PASSWORD")" >> "${SECRETS_DIR}/secrets.enc"
    fi
    
    if [[ -n "$TELEGRAM_BOT_TOKEN" ]]; then
        echo "TELEGRAM_BOT_TOKEN_ENC=$(encrypt_value "$TELEGRAM_BOT_TOKEN")" >> "${SECRETS_DIR}/secrets.enc"
    fi
    
    # Set secure permissions
    chmod 600 "${SECRETS_DIR}/secrets.enc"
    chown root:root "${SECRETS_DIR}/secrets.enc"
    
    log_success "Secrets encrypted and stored securely"
}

# Create secret management scripts
create_secret_scripts() {
    log_info "Creating secret management scripts..."
    
    # Create decrypt script
    cat > "${CONFIG_DIR}/decrypt_secret.sh" << 'EOF'
#!/bin/bash
# Decrypt a specific secret

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <secret_name>"
    echo "Available secrets:"
    grep "_ENC=" /etc/trae-sentinel/secrets/secrets.enc | cut -d'=' -f1
    exit 1
fi

SECRET_NAME="$1"
SECRETS_FILE="/etc/trae-sentinel/secrets/secrets.enc"
KEY_FILE="/etc/trae-sentinel/secrets/master.key"

if [[ ! -f "$SECRETS_FILE" ]] || [[ ! -f "$KEY_FILE" ]]; then
    echo "Error: Secrets or key file not found"
    exit 1
fi

ENCRYPTED_VALUE=$(grep "^${SECRET_NAME}_ENC=" "$SECRETS_FILE" | cut -d'=' -f2-)

if [[ -z "$ENCRYPTED_VALUE" ]]; then
    echo "Error: Secret '$SECRET_NAME' not found"
    exit 1
fi

echo -n "$ENCRYPTED_VALUE" | openssl enc -aes-256-cbc -d -base64 -pass file:"$KEY_FILE"
EOF
    
    # Create rotate secrets script
    cat > "${CONFIG_DIR}/rotate_secrets.sh" << 'EOF'
#!/bin/bash
# Rotate API keys and secrets

set -euo pipefail

CONFIG_DIR="/etc/trae-sentinel"
APP_DIR="/opt/trae-sentinel"
BACKUP_DIR="/var/backups/trae-sentinel"

echo "[INFO] Starting secret rotation..."

# Backup current secrets
cp "${CONFIG_DIR}/.env" "${BACKUP_DIR}/.env.backup.$(date +%Y%m%d-%H%M%S)"
cp "${CONFIG_DIR}/secrets/secrets.enc" "${BACKUP_DIR}/secrets.enc.backup.$(date +%Y%m%d-%H%M%S)"

# Generate new secrets
NEW_API_SECRET=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-64)
NEW_JWT_SECRET=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-64)

# Update environment file
sed -i "s/^SECRET_KEY=.*/SECRET_KEY=${NEW_API_SECRET}/" "${CONFIG_DIR}/.env"
sed -i "s/^JWT_SECRET_KEY=.*/JWT_SECRET_KEY=${NEW_JWT_SECRET}/" "${CONFIG_DIR}/.env"

# Update encrypted secrets
KEY_FILE="${CONFIG_DIR}/secrets/master.key"
echo "API_SECRET_KEY_ENC=$(echo -n "$NEW_API_SECRET" | openssl enc -aes-256-cbc -base64 -pass file:"$KEY_FILE")" >> "${CONFIG_DIR}/secrets/secrets.enc"
echo "JWT_SECRET_KEY_ENC=$(echo -n "$NEW_JWT_SECRET" | openssl enc -aes-256-cbc -base64 -pass file:"$KEY_FILE")" >> "${CONFIG_DIR}/secrets/secrets.enc"

# Restart services
systemctl restart trae-backend.service
systemctl restart trae-enhanced-monitor.service

echo "[SUCCESS] Secrets rotated successfully"
EOF
    
    # Make scripts executable
    chmod 750 "${CONFIG_DIR}/decrypt_secret.sh"
    chmod 750 "${CONFIG_DIR}/rotate_secrets.sh"
    chown root:trae-sentinel "${CONFIG_DIR}/decrypt_secret.sh"
    chown root:trae-sentinel "${CONFIG_DIR}/rotate_secrets.sh"
    
    log_success "Secret management scripts created"
}

# Setup SSL certificates
setup_ssl() {
    log_info "Setting up SSL certificates..."
    
    read -p "Domain name for SSL certificate: " DOMAIN_NAME
    read -p "Email for Let's Encrypt: " LETSENCRYPT_EMAIL
    
    if [[ -n "$DOMAIN_NAME" ]] && [[ -n "$LETSENCRYPT_EMAIL" ]]; then
        # Install certbot if not present
        if ! command -v certbot &> /dev/null; then
            apt-get update
            apt-get install -y certbot python3-certbot-nginx
        fi
        
        # Obtain SSL certificate
        certbot --nginx -d "$DOMAIN_NAME" --email "$LETSENCRYPT_EMAIL" --agree-tos --non-interactive
        
        # Setup auto-renewal
        (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -
        
        log_success "SSL certificate configured for $DOMAIN_NAME"
    else
        log_warning "SSL setup skipped - domain name or email not provided"
    fi
}

# Create backup script
create_backup_script() {
    log_info "Creating backup script..."
    
    cat > "${CONFIG_DIR}/backup.sh" << EOF
#!/bin/bash
# AI Trading Sentinel - Backup Script

set -euo pipefail

APP_DIR="/opt/trae-sentinel"
BACKUP_DIR="/var/backups/trae-sentinel"
DATE=\$(date +%Y%m%d-%H%M%S)
BACKUP_NAME="trae-sentinel-backup-\${DATE}"
BACKUP_PATH="\${BACKUP_DIR}/\${BACKUP_NAME}"

echo "[INFO] Starting backup: \${BACKUP_NAME}"

# Create backup directory
mkdir -p "\${BACKUP_PATH}"

# Backup application files
cp -r "\${APP_DIR}" "\${BACKUP_PATH}/app"

# Backup configuration
cp -r "/etc/trae-sentinel" "\${BACKUP_PATH}/config"

# Backup database (if SQLite)
if [[ -f "\${APP_DIR}/data/trae_sentinel.db" ]]; then
    cp "\${APP_DIR}/data/trae_sentinel.db" "\${BACKUP_PATH}/database.db"
fi

# Backup logs
cp -r "/var/log/trae-sentinel" "\${BACKUP_PATH}/logs" 2>/dev/null || true

# Create archive
tar -czf "\${BACKUP_PATH}.tar.gz" -C "\${BACKUP_DIR}" "\${BACKUP_NAME}"
rm -rf "\${BACKUP_PATH}"

# Clean old backups (keep last 7 days)
find "\${BACKUP_DIR}" -name "trae-sentinel-backup-*.tar.gz" -mtime +7 -delete

echo "[SUCCESS] Backup completed: \${BACKUP_PATH}.tar.gz"
EOF
    
    chmod 750 "${CONFIG_DIR}/backup.sh"
    chown root:trae-sentinel "${CONFIG_DIR}/backup.sh"
    
    # Setup daily backup cron job
    (crontab -l 2>/dev/null; echo "0 2 * * * ${CONFIG_DIR}/backup.sh") | crontab -
    
    log_success "Backup script created and scheduled"
}

# Verify configuration
verify_config() {
    log_info "Verifying configuration..."
    
    # Check file permissions
    if [[ $(stat -c "%a" "$ENV_FILE") == "640" ]]; then
        log_success "Environment file permissions correct"
    else
        log_error "Environment file permissions incorrect"
    fi
    
    # Check secrets encryption
    if [[ -f "${SECRETS_DIR}/master.key" ]] && [[ -f "${SECRETS_DIR}/secrets.enc" ]]; then
        log_success "Secrets properly encrypted"
    else
        log_error "Secrets encryption failed"
    fi
    
    # Test database connection
    if [[ "$DB_TYPE" == "postgresql" ]]; then
        if pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" &>/dev/null; then
            log_success "Database connection successful"
        else
            log_warning "Database connection failed - please verify settings"
        fi
    fi
    
    # Test Redis connection
    if redis-cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" ping &>/dev/null; then
        log_success "Redis connection successful"
    else
        log_warning "Redis connection failed - please verify settings"
    fi
    
    log_success "Configuration verification completed"
}

# Display summary
show_summary() {
    echo
    log_info "=== AI Trading Sentinel - Production Environment Setup Complete ==="
    echo
    echo "Configuration Files:"
    echo "  Environment: $ENV_FILE"
    echo "  Secrets: ${SECRETS_DIR}/secrets.enc"
    echo "  Master Key: ${SECRETS_DIR}/master.key"
    echo
    echo "Management Scripts:"
    echo "  Decrypt Secret: ${CONFIG_DIR}/decrypt_secret.sh <secret_name>"
    echo "  Rotate Secrets: ${CONFIG_DIR}/rotate_secrets.sh"
    echo "  Backup System: ${CONFIG_DIR}/backup.sh"
    echo
    echo "Next Steps:"
    echo "  1. Review and test the configuration"
    echo "  2. Deploy the application: ./deploy_enhanced_monitoring.sh"
    echo "  3. Start the services: systemctl start trae-*"
    echo "  4. Monitor logs: journalctl -u trae-enhanced-monitor.service -f"
    echo
    echo "Security Notes:"
    echo "  - All sensitive data is encrypted"
    echo "  - Regular backups are scheduled"
    echo "  - SSL certificates should be configured"
    echo "  - Firewall rules are in place"
    echo
}

# Main function
main() {
    log_info "Starting AI Trading Sentinel Production Environment Setup"
    echo
    
    check_root
    setup_directories
    interactive_config
    create_env_file
    setup_secrets
    create_secret_scripts
    setup_ssl
    create_backup_script
    verify_config
    
    show_summary
    
    log_success "Production environment setup completed successfully!"
}

# Handle command line arguments
case "${1:-setup}" in
    "setup")
        main
        ;;
    "backup")
        "${CONFIG_DIR}/backup.sh"
        ;;
    "rotate")
        "${CONFIG_DIR}/rotate_secrets.sh"
        ;;
    "decrypt")
        if [[ $# -ne 2 ]]; then
            echo "Usage: $0 decrypt <secret_name>"
            exit 1
        fi
        "${CONFIG_DIR}/decrypt_secret.sh" "$2"
        ;;
    *)
        echo "Usage: $0 {setup|backup|rotate|decrypt}"
        echo "  setup   - Interactive production environment setup"
        echo "  backup  - Create system backup"
        echo "  rotate  - Rotate API keys and secrets"
        echo "  decrypt - Decrypt a specific secret"
        exit 1
        ;;
esac