#!/bin/bash

# AI Trading Sentinel - Backup and Recovery Script
# Comprehensive backup solution for production deployment

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-/home/aitrading/ai-trading-sentinel}"
BACKUP_ROOT="${BACKUP_ROOT:-/home/aitrading/backups}"
S3_BUCKET="${S3_BUCKET:-}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
MAX_LOCAL_BACKUPS="${MAX_LOCAL_BACKUPS:-10}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
LOG_FILE="${BACKUP_ROOT}/backup.log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_info() {
    log "INFO: $1"
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    log "SUCCESS: $1"
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    log "WARNING: $1"
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    log "ERROR: $1"
    echo -e "${RED}❌ $1${NC}"
}

# Check dependencies
check_dependencies() {
    local deps=("tar" "gzip" "rsync" "systemctl")
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            log_error "Required dependency '$dep' not found"
            exit 1
        fi
    done
    
    # Check for AWS CLI if S3 backup is configured
    if [[ -n "$S3_BUCKET" ]] && ! command -v "aws" &> /dev/null; then
        log_warning "AWS CLI not found, S3 backup disabled"
        S3_BUCKET=""
    fi
}

# Create backup directory structure
setup_backup_dirs() {
    local dirs=(
        "$BACKUP_ROOT"
        "$BACKUP_ROOT/daily"
        "$BACKUP_ROOT/weekly"
        "$BACKUP_ROOT/monthly"
        "$BACKUP_ROOT/config"
        "$BACKUP_ROOT/logs"
        "$BACKUP_ROOT/data"
    )
    
    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
    done
}

# Stop services safely
stop_services() {
    log_info "Stopping AI Trading Sentinel services..."
    
    local services=("aitrading-bot" "aitrading-monitor")
    
    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service"; then
            log_info "Stopping $service..."
            sudo systemctl stop "$service"
            
            # Wait for graceful shutdown
            local timeout=30
            while systemctl is-active --quiet "$service" && [[ $timeout -gt 0 ]]; do
                sleep 1
                ((timeout--))
            done
            
            if systemctl is-active --quiet "$service"; then
                log_warning "$service did not stop gracefully, forcing stop"
                sudo systemctl kill "$service"
            fi
        fi
    done
}

# Start services
start_services() {
    log_info "Starting AI Trading Sentinel services..."
    
    local services=("aitrading-backend" "aitrading-bot" "aitrading-monitor")
    
    for service in "${services[@]}"; do
        log_info "Starting $service..."
        sudo systemctl start "$service"
        
        # Wait for service to be ready
        local timeout=30
        while ! systemctl is-active --quiet "$service" && [[ $timeout -gt 0 ]]; do
            sleep 1
            ((timeout--))
        done
        
        if systemctl is-active --quiet "$service"; then
            log_success "$service started successfully"
        else
            log_error "Failed to start $service"
        fi
    done
}

# Create application backup
backup_application() {
    local backup_type="$1"
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_name="aitrading_${backup_type}_${timestamp}"
    local backup_dir="$BACKUP_ROOT/$backup_type"
    local backup_file="$backup_dir/${backup_name}.tar.gz"
    
    log_info "Creating $backup_type backup: $backup_name"
    
    # Create temporary backup directory
    local temp_dir="/tmp/${backup_name}"
    mkdir -p "$temp_dir"
    
    # Copy application files
    log_info "Backing up application files..."
    rsync -av --exclude='*.pyc' --exclude='__pycache__' \
          --exclude='node_modules' --exclude='.git' \
          --exclude='temp/*' --exclude='logs/*.log' \
          "$PROJECT_ROOT/" "$temp_dir/app/"
    
    # Backup configuration
    log_info "Backing up configuration..."
    mkdir -p "$temp_dir/config"
    cp "$PROJECT_ROOT/.env" "$temp_dir/config/" 2>/dev/null || true
    cp "$PROJECT_ROOT/.env.production" "$temp_dir/config/" 2>/dev/null || true
    
    # Backup systemd services
    mkdir -p "$temp_dir/systemd"
    cp /etc/systemd/system/aitrading-*.service "$temp_dir/systemd/" 2>/dev/null || true
    
    # Backup nginx configuration
    mkdir -p "$temp_dir/nginx"
    cp /etc/nginx/sites-available/aitrading-sentinel.conf "$temp_dir/nginx/" 2>/dev/null || true
    
    # Backup data directory
    if [[ -d "$PROJECT_ROOT/data" ]]; then
        log_info "Backing up data directory..."
        rsync -av "$PROJECT_ROOT/data/" "$temp_dir/data/"
    fi
    
    # Backup recent logs
    log_info "Backing up recent logs..."
    mkdir -p "$temp_dir/logs"
    find "$PROJECT_ROOT/logs" -name "*.log" -mtime -7 -exec cp {} "$temp_dir/logs/" \; 2>/dev/null || true
    
    # Create backup metadata
    cat > "$temp_dir/backup_info.json" << EOF
{
    "backup_name": "$backup_name",
    "backup_type": "$backup_type",
    "timestamp": "$(date -Iseconds)",
    "hostname": "$(hostname)",
    "project_root": "$PROJECT_ROOT",
    "git_commit": "$(cd "$PROJECT_ROOT" && git rev-parse HEAD 2>/dev/null || echo 'unknown')",
    "git_branch": "$(cd "$PROJECT_ROOT" && git branch --show-current 2>/dev/null || echo 'unknown')",
    "system_info": {
        "os": "$(lsb_release -d 2>/dev/null | cut -f2 || uname -s)",
        "kernel": "$(uname -r)",
        "architecture": "$(uname -m)"
    }
}
EOF
    
    # Create compressed archive
    log_info "Creating compressed archive..."
    tar -czf "$backup_file" -C "/tmp" "$backup_name"
    
    # Cleanup temporary directory
    rm -rf "$temp_dir"
    
    # Verify backup
    if [[ -f "$backup_file" ]]; then
        local size=$(du -h "$backup_file" | cut -f1)
        log_success "Backup created successfully: $backup_file ($size)"
        
        # Upload to S3 if configured
        if [[ -n "$S3_BUCKET" ]]; then
            upload_to_s3 "$backup_file" "$backup_type/$backup_name.tar.gz"
        fi
        
        return 0
    else
        log_error "Failed to create backup: $backup_file"
        return 1
    fi
}

# Upload backup to S3
upload_to_s3() {
    local local_file="$1"
    local s3_key="$2"
    
    log_info "Uploading backup to S3: s3://$S3_BUCKET/$s3_key"
    
    if aws s3 cp "$local_file" "s3://$S3_BUCKET/$s3_key" --storage-class STANDARD_IA; then
        log_success "Backup uploaded to S3 successfully"
    else
        log_error "Failed to upload backup to S3"
    fi
}

# Clean old backups
cleanup_old_backups() {
    log_info "Cleaning up old backups..."
    
    # Clean local backups
    for backup_type in "daily" "weekly" "monthly"; do
        local backup_dir="$BACKUP_ROOT/$backup_type"
        
        if [[ -d "$backup_dir" ]]; then
            # Keep only the most recent backups
            local count=$(ls -1 "$backup_dir"/*.tar.gz 2>/dev/null | wc -l)
            
            if [[ $count -gt $MAX_LOCAL_BACKUPS ]]; then
                local to_delete=$((count - MAX_LOCAL_BACKUPS))
                log_info "Removing $to_delete old $backup_type backups"
                
                ls -1t "$backup_dir"/*.tar.gz | tail -n "$to_delete" | xargs rm -f
            fi
        fi
    done
    
    # Clean S3 backups if configured
    if [[ -n "$S3_BUCKET" ]]; then
        log_info "Cleaning old S3 backups (older than $RETENTION_DAYS days)"
        
        local cutoff_date=$(date -d "$RETENTION_DAYS days ago" '+%Y-%m-%d')
        
        aws s3 ls "s3://$S3_BUCKET/" --recursive | while read -r line; do
            local file_date=$(echo "$line" | awk '{print $1}')
            local file_key=$(echo "$line" | awk '{print $4}')
            
            if [[ "$file_date" < "$cutoff_date" ]]; then
                log_info "Deleting old S3 backup: $file_key"
                aws s3 rm "s3://$S3_BUCKET/$file_key"
            fi
        done
    fi
}

# Restore from backup
restore_backup() {
    local backup_file="$1"
    local restore_dir="${2:-$PROJECT_ROOT}"
    
    if [[ ! -f "$backup_file" ]]; then
        log_error "Backup file not found: $backup_file"
        return 1
    fi
    
    log_info "Restoring from backup: $backup_file"
    
    # Stop services
    stop_services
    
    # Create restore directory
    local temp_restore="/tmp/restore_$(date '+%Y%m%d_%H%M%S')"
    mkdir -p "$temp_restore"
    
    # Extract backup
    log_info "Extracting backup..."
    tar -xzf "$backup_file" -C "$temp_restore"
    
    # Find the backup directory
    local backup_dir=$(find "$temp_restore" -maxdepth 1 -type d -name "aitrading_*" | head -1)
    
    if [[ -z "$backup_dir" ]]; then
        log_error "Invalid backup file structure"
        rm -rf "$temp_restore"
        return 1
    fi
    
    # Backup current installation
    local current_backup="$BACKUP_ROOT/pre_restore_$(date '+%Y%m%d_%H%M%S').tar.gz"
    log_info "Creating backup of current installation: $current_backup"
    tar -czf "$current_backup" -C "$(dirname "$restore_dir")" "$(basename "$restore_dir")"
    
    # Restore application files
    log_info "Restoring application files..."
    rsync -av --delete "$backup_dir/app/" "$restore_dir/"
    
    # Restore configuration
    if [[ -d "$backup_dir/config" ]]; then
        log_info "Restoring configuration..."
        cp "$backup_dir/config/"* "$restore_dir/" 2>/dev/null || true
    fi
    
    # Restore systemd services
    if [[ -d "$backup_dir/systemd" ]]; then
        log_info "Restoring systemd services..."
        sudo cp "$backup_dir/systemd/"*.service /etc/systemd/system/ 2>/dev/null || true
        sudo systemctl daemon-reload
    fi
    
    # Restore nginx configuration
    if [[ -d "$backup_dir/nginx" ]]; then
        log_info "Restoring nginx configuration..."
        sudo cp "$backup_dir/nginx/"*.conf /etc/nginx/sites-available/ 2>/dev/null || true
        sudo nginx -t && sudo systemctl reload nginx
    fi
    
    # Restore data
    if [[ -d "$backup_dir/data" ]]; then
        log_info "Restoring data directory..."
        rsync -av "$backup_dir/data/" "$restore_dir/data/"
    fi
    
    # Set proper permissions
    chown -R aitrading:aitrading "$restore_dir"
    chmod +x "$restore_dir"/*.py
    
    # Cleanup
    rm -rf "$temp_restore"
    
    # Start services
    start_services
    
    log_success "Restore completed successfully"
}

# Health check after backup/restore
health_check() {
    log_info "Performing health check..."
    
    # Check services
    local services=("aitrading-backend" "aitrading-bot" "aitrading-monitor")
    local failed_services=()
    
    for service in "${services[@]}"; do
        if ! systemctl is-active --quiet "$service"; then
            failed_services+=("$service")
        fi
    done
    
    if [[ ${#failed_services[@]} -gt 0 ]]; then
        log_error "Health check failed - services not running: ${failed_services[*]}"
        return 1
    fi
    
    # Check API endpoint
    if command -v curl &> /dev/null; then
        if curl -sf "http://localhost:5000/api/health" > /dev/null; then
            log_success "API health check passed"
        else
            log_error "API health check failed"
            return 1
        fi
    fi
    
    log_success "Health check passed"
    return 0
}

# Main backup function
run_backup() {
    local backup_type="${1:-daily}"
    
    log_info "Starting $backup_type backup process..."
    
    # Check dependencies
    check_dependencies
    
    # Setup backup directories
    setup_backup_dirs
    
    # Stop services for consistent backup
    stop_services
    
    # Create backup
    if backup_application "$backup_type"; then
        log_success "Backup completed successfully"
    else
        log_error "Backup failed"
        start_services
        exit 1
    fi
    
    # Start services
    start_services
    
    # Health check
    if ! health_check; then
        log_error "Post-backup health check failed"
        exit 1
    fi
    
    # Cleanup old backups
    cleanup_old_backups
    
    log_success "Backup process completed successfully"
}

# Show usage
show_usage() {
    cat << EOF
AI Trading Sentinel - Backup and Recovery Script

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    backup [daily|weekly|monthly]  Create a backup (default: daily)
    restore <backup_file>          Restore from backup file
    list                          List available backups
    cleanup                       Clean old backups
    health                        Perform health check

Environment Variables:
    PROJECT_ROOT      Project directory (default: /home/aitrading/ai-trading-sentinel)
    BACKUP_ROOT       Backup directory (default: /home/aitrading/backups)
    S3_BUCKET         S3 bucket for remote backups
    RETENTION_DAYS    Days to keep S3 backups (default: 30)
    MAX_LOCAL_BACKUPS Maximum local backups to keep (default: 10)

Examples:
    $0 backup daily
    $0 restore /home/aitrading/backups/daily/aitrading_daily_20240101_120000.tar.gz
    $0 list
    $0 cleanup

EOF
}

# List available backups
list_backups() {
    log_info "Available backups:"
    
    for backup_type in "daily" "weekly" "monthly"; do
        local backup_dir="$BACKUP_ROOT/$backup_type"
        
        if [[ -d "$backup_dir" ]]; then
            echo -e "\n${BLUE}$backup_type backups:${NC}"
            
            if ls "$backup_dir"/*.tar.gz &> /dev/null; then
                for backup in "$backup_dir"/*.tar.gz; do
                    local size=$(du -h "$backup" | cut -f1)
                    local date=$(stat -c %y "$backup" | cut -d' ' -f1)
                    echo "  $(basename "$backup") ($size, $date)"
                done
            else
                echo "  No backups found"
            fi
        fi
    done
}

# Main script
main() {
    case "${1:-}" in
        "backup")
            run_backup "${2:-daily}"
            ;;
        "restore")
            if [[ -z "${2:-}" ]]; then
                log_error "Backup file required for restore"
                show_usage
                exit 1
            fi
            restore_backup "$2" "${3:-}"
            ;;
        "list")
            list_backups
            ;;
        "cleanup")
            cleanup_old_backups
            ;;
        "health")
            health_check
            ;;
        "help"|"--help"|"")
            show_usage
            ;;
        *)
            log_error "Unknown command: $1"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"