#!/bin/bash

# AI Trading Sentinel - Security Monitor Daemon
# Continuous security monitoring and threat detection

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PID_FILE="/var/run/security-monitor.pid"
LOG_DIR="/var/log/security-monitor"
CONFIG_FILE="$SCRIPT_DIR/monitor.conf"
DAEMON_USER="root"
DAEMON_NAME="security-monitor"

# Default configuration
MONITOR_INTERVAL=300  # 5 minutes
ALERT_THRESHOLD_HIGH=10
ALERT_THRESHOLD_CRITICAL=5
MAX_LOG_SIZE="100M"
LOG_RETENTION_DAYS=30

# Load configuration if exists
[[ -f "$CONFIG_FILE" ]] && source "$CONFIG_FILE"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_DIR/monitor.log"
}

log_error() {
    log "${RED}ERROR: $1${NC}"
}

log_warning() {
    log "${YELLOW}WARNING: $1${NC}"
}

log_info() {
    log "${BLUE}INFO: $1${NC}"
}

log_success() {
    log "${GREEN}SUCCESS: $1${NC}"
}

# Initialize monitoring environment
init_monitor() {
    # Create directories
    mkdir -p "$LOG_DIR" "$SCRIPT_DIR/reports" "$SCRIPT_DIR/alerts"
    chmod 750 "$LOG_DIR" "$SCRIPT_DIR/reports" "$SCRIPT_DIR/alerts"
    
    # Setup log rotation
    cat > "/etc/logrotate.d/security-monitor" << EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 640 root root
    maxsize $MAX_LOG_SIZE
    postrotate
        systemctl reload security-monitor || true
    endscript
}
EOF
    
    log_info "Security monitor initialized"
}

# Check if daemon is running
is_running() {
    [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null
}

# Start daemon
start_daemon() {
    if is_running; then
        log_warning "Security monitor is already running (PID: $(cat "$PID_FILE"))"
        return 1
    fi
    
    log_info "Starting security monitor daemon..."
    
    # Initialize environment
    init_monitor
    
    # Start monitoring in background
    nohup bash -c '
        trap "rm -f $PID_FILE; exit" INT TERM EXIT
        echo $$ > "$PID_FILE"
        
        while true; do
            monitor_security
            sleep "$MONITOR_INTERVAL"
        done
    ' >> "$LOG_DIR/daemon.log" 2>&1 &
    
    # Wait a moment and check if it started successfully
    sleep 2
    if is_running; then
        log_success "Security monitor started (PID: $(cat "$PID_FILE"))"
        return 0
    else
        log_error "Failed to start security monitor"
        return 1
    fi
}

# Stop daemon
stop_daemon() {
    if ! is_running; then
        log_warning "Security monitor is not running"
        return 1
    fi
    
    log_info "Stopping security monitor daemon..."
    
    local pid=$(cat "$PID_FILE")
    kill "$pid" 2>/dev/null || true
    
    # Wait for graceful shutdown
    local count=0
    while is_running && [[ $count -lt 30 ]]; do
        sleep 1
        ((count++))
    done
    
    # Force kill if still running
    if is_running; then
        log_warning "Force killing security monitor"
        kill -9 "$pid" 2>/dev/null || true
    fi
    
    rm -f "$PID_FILE"
    log_success "Security monitor stopped"
}

# Reload daemon
reload_daemon() {
    if ! is_running; then
        log_error "Security monitor is not running"
        return 1
    fi
    
    log_info "Reloading security monitor configuration..."
    kill -HUP "$(cat "$PID_FILE")" 2>/dev/null || true
    log_success "Security monitor reloaded"
}

# Get daemon status
status_daemon() {
    if is_running; then
        local pid=$(cat "$PID_FILE")
        local uptime=$(ps -o etime= -p "$pid" 2>/dev/null | tr -d ' ' || echo "unknown")
        log_info "Security monitor is running (PID: $pid, Uptime: $uptime)"
        return 0
    else
        log_warning "Security monitor is not running"
        return 1
    fi
}

# Core security monitoring function
monitor_security() {
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local alert_file="$SCRIPT_DIR/alerts/alert_$timestamp.json"
    local alerts_count=0
    
    log_info "Running security monitoring cycle..."
    
    # Initialize alert structure
    cat > "$alert_file" << EOF
{
    "timestamp": "$(date -Iseconds)",
    "hostname": "$(hostname)",
    "alerts": [],
    "summary": {
        "total_alerts": 0,
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0
    }
}
EOF
    
    # Monitor system resources
    monitor_system_resources "$alert_file"
    
    # Monitor network connections
    monitor_network_connections "$alert_file"
    
    # Monitor file integrity
    monitor_file_integrity "$alert_file"
    
    # Monitor process anomalies
    monitor_process_anomalies "$alert_file"
    
    # Monitor log files for threats
    monitor_log_threats "$alert_file"
    
    # Monitor fail2ban status
    monitor_fail2ban_status "$alert_file"
    
    # Check for security updates
    check_security_updates "$alert_file"
    
    # Process alerts and send notifications
    process_alerts "$alert_file"
    
    log_info "Security monitoring cycle completed"
}

# Monitor system resources
monitor_system_resources() {
    local alert_file="$1"
    
    # CPU usage
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    if (( $(echo "$cpu_usage > 90" | bc -l) )); then
        add_alert "$alert_file" "high" "system" "High CPU usage: ${cpu_usage}%"
    fi
    
    # Memory usage
    local mem_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    if (( $(echo "$mem_usage > 90" | bc -l) )); then
        add_alert "$alert_file" "high" "system" "High memory usage: ${mem_usage}%"
    fi
    
    # Disk usage
    while IFS= read -r line; do
        local usage=$(echo "$line" | awk '{print $5}' | cut -d'%' -f1)
        local mount=$(echo "$line" | awk '{print $6}')
        if [[ "$usage" -gt 90 ]]; then
            add_alert "$alert_file" "high" "system" "High disk usage on $mount: ${usage}%"
        fi
    done < <(df -h | grep -E '^/dev/')
    
    # Load average
    local load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | cut -d',' -f1)
    local cpu_cores=$(nproc)
    if (( $(echo "$load_avg > $cpu_cores * 2" | bc -l) )); then
        add_alert "$alert_file" "medium" "system" "High load average: $load_avg (cores: $cpu_cores)"
    fi
}

# Monitor network connections
monitor_network_connections() {
    local alert_file="$1"
    
    # Check for suspicious connections
    local suspicious_connections=$(netstat -tuln | grep -E ':(22|80|443|3306|5432|6379|27017)' | wc -l)
    if [[ "$suspicious_connections" -gt 100 ]]; then
        add_alert "$alert_file" "medium" "network" "High number of network connections: $suspicious_connections"
    fi
    
    # Check for foreign connections to sensitive ports
    while IFS= read -r line; do
        local foreign_ip=$(echo "$line" | awk '{print $5}' | cut -d':' -f1)
        if [[ "$foreign_ip" != "127.0.0.1" ]] && [[ "$foreign_ip" != "0.0.0.0" ]] && [[ "$foreign_ip" != "::1" ]]; then
            add_alert "$alert_file" "low" "network" "Foreign connection detected: $line"
        fi
    done < <(netstat -tn | grep -E ':(22|3306|5432|6379|27017)' | grep ESTABLISHED)
}

# Monitor file integrity
monitor_file_integrity() {
    local alert_file="$1"
    
    # Check critical system files
    local critical_files=(
        "/etc/passwd"
        "/etc/shadow"
        "/etc/sudoers"
        "/etc/ssh/sshd_config"
        "/etc/nginx/nginx.conf"
        "$PROJECT_ROOT/.env"
    )
    
    for file in "${critical_files[@]}"; do
        if [[ -f "$file" ]]; then
            local current_hash=$(sha256sum "$file" | cut -d' ' -f1)
            local hash_file="$SCRIPT_DIR/.hashes/$(basename "$file").hash"
            
            mkdir -p "$SCRIPT_DIR/.hashes"
            
            if [[ -f "$hash_file" ]]; then
                local stored_hash=$(cat "$hash_file")
                if [[ "$current_hash" != "$stored_hash" ]]; then
                    add_alert "$alert_file" "critical" "integrity" "File integrity violation: $file"
                fi
            else
                echo "$current_hash" > "$hash_file"
            fi
        fi
    done
}

# Monitor process anomalies
monitor_process_anomalies() {
    local alert_file="$1"
    
    # Check for suspicious processes
    local suspicious_processes=(
        "nc" "netcat" "ncat"
        "telnet" "rsh" "rlogin"
        "wget" "curl" "lynx"
        "python" "perl" "ruby" "php"
        "gcc" "g++" "make"
        "nmap" "masscan" "zmap"
        "sqlmap" "nikto" "dirb"
    )
    
    for process in "${suspicious_processes[@]}"; do
        if pgrep -f "$process" > /dev/null; then
            local pid=$(pgrep -f "$process" | head -1)
            local cmdline=$(ps -p "$pid" -o cmd --no-headers 2>/dev/null || echo "unknown")
            add_alert "$alert_file" "medium" "process" "Suspicious process detected: $process (PID: $pid, CMD: $cmdline)"
        fi
    done
    
    # Check for processes running as root
    local root_processes=$(ps -eo user,pid,cmd | grep -E '^root' | wc -l)
    if [[ "$root_processes" -gt 50 ]]; then
        add_alert "$alert_file" "low" "process" "High number of root processes: $root_processes"
    fi
}

# Monitor log files for threats
monitor_log_threats() {
    local alert_file="$1"
    
    # Check auth.log for failed logins
    if [[ -f "/var/log/auth.log" ]]; then
        local failed_logins=$(grep "Failed password" /var/log/auth.log | tail -100 | wc -l)
        if [[ "$failed_logins" -gt 10 ]]; then
            add_alert "$alert_file" "high" "auth" "High number of failed login attempts: $failed_logins"
        fi
    fi
    
    # Check nginx error log
    if [[ -f "/var/log/nginx/error.log" ]]; then
        local nginx_errors=$(grep -E "(error|crit|alert|emerg)" /var/log/nginx/error.log | tail -100 | wc -l)
        if [[ "$nginx_errors" -gt 20 ]]; then
            add_alert "$alert_file" "medium" "web" "High number of Nginx errors: $nginx_errors"
        fi
    fi
    
    # Check for kernel messages
    if [[ -f "/var/log/kern.log" ]]; then
        local kernel_errors=$(grep -E "(error|panic|oops|bug)" /var/log/kern.log | tail -100 | wc -l)
        if [[ "$kernel_errors" -gt 5 ]]; then
            add_alert "$alert_file" "high" "system" "Kernel errors detected: $kernel_errors"
        fi
    fi
}

# Monitor fail2ban status
monitor_fail2ban_status() {
    local alert_file="$1"
    
    if command -v fail2ban-client &> /dev/null; then
        # Check if fail2ban is running
        if ! systemctl is-active --quiet fail2ban; then
            add_alert "$alert_file" "critical" "security" "Fail2ban service is not running"
        else
            # Check banned IPs
            local banned_ips=$(fail2ban-client status | grep -o "Currently banned:.*" | awk '{print $3}' || echo "0")
            if [[ "$banned_ips" -gt 50 ]]; then
                add_alert "$alert_file" "medium" "security" "High number of banned IPs: $banned_ips"
            fi
        fi
    fi
}

# Check for security updates
check_security_updates() {
    local alert_file="$1"
    
    # Check for available security updates
    apt-get update -qq 2>/dev/null || true
    local security_updates=$(apt list --upgradable 2>/dev/null | grep -i security | wc -l)
    
    if [[ "$security_updates" -gt 0 ]]; then
        add_alert "$alert_file" "medium" "updates" "Security updates available: $security_updates"
    fi
}

# Add alert to alert file
add_alert() {
    local alert_file="$1"
    local severity="$2"
    local category="$3"
    local message="$4"
    local timestamp=$(date -Iseconds)
    
    # Create temporary file for JSON manipulation
    local temp_file=$(mktemp)
    
    # Add alert to JSON structure
    jq --arg severity "$severity" \
       --arg category "$category" \
       --arg message "$message" \
       --arg timestamp "$timestamp" \
       '.alerts += [{
           "severity": $severity,
           "category": $category,
           "message": $message,
           "timestamp": $timestamp
       }] | .summary.total_alerts += 1 | .summary[$severity] += 1' \
       "$alert_file" > "$temp_file" && mv "$temp_file" "$alert_file"
    
    log_warning "ALERT [$severity/$category]: $message"
}

# Process alerts and send notifications
process_alerts() {
    local alert_file="$1"
    
    local total_alerts=$(jq -r '.summary.total_alerts' "$alert_file")
    local critical_alerts=$(jq -r '.summary.critical' "$alert_file")
    local high_alerts=$(jq -r '.summary.high' "$alert_file")
    
    # Send notifications based on alert severity
    if [[ "$critical_alerts" -gt 0 ]] || [[ "$high_alerts" -gt "$ALERT_THRESHOLD_HIGH" ]]; then
        send_alert_notification "$alert_file" "urgent"
    elif [[ "$total_alerts" -gt 0 ]]; then
        send_alert_notification "$alert_file" "normal"
    fi
    
    # Clean up old alert files
    find "$SCRIPT_DIR/alerts" -name "alert_*.json" -mtime +7 -delete 2>/dev/null || true
}

# Send alert notifications
send_alert_notification() {
    local alert_file="$1"
    local urgency="$2"
    
    local hostname=$(hostname)
    local timestamp=$(date)
    local total_alerts=$(jq -r '.summary.total_alerts' "$alert_file")
    local critical_alerts=$(jq -r '.summary.critical' "$alert_file")
    local high_alerts=$(jq -r '.summary.high' "$alert_file")
    
    local message="🚨 Security Alert - $hostname\n\nTimestamp: $timestamp\nTotal Alerts: $total_alerts\nCritical: $critical_alerts\nHigh: $high_alerts\n\nCheck $alert_file for details."
    
    # Slack notification
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        local emoji="⚠️"
        [[ "$urgency" == "urgent" ]] && emoji="🚨"
        
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$emoji $message\"}" \
            "$SLACK_WEBHOOK_URL" 2>/dev/null || log_warning "Failed to send Slack notification"
    fi
    
    # Email notification
    if command -v mail &> /dev/null && [[ -n "${SECURITY_EMAIL:-}" ]]; then
        echo -e "$message" | mail -s "Security Alert - $hostname" "$SECURITY_EMAIL" 2>/dev/null || \
            log_warning "Failed to send email notification"
    fi
}

# Main function
main() {
    case "${1:-}" in
        start)
            start_daemon
            ;;
        stop)
            stop_daemon
            ;;
        restart)
            stop_daemon
            sleep 2
            start_daemon
            ;;
        reload)
            reload_daemon
            ;;
        status)
            status_daemon
            ;;
        monitor)
            # Run single monitoring cycle (for testing)
            monitor_security
            ;;
        install)
            # Install as systemd service
            cp "$SCRIPT_DIR/security-monitor.service" "/etc/systemd/system/"
            systemctl daemon-reload
            systemctl enable security-monitor
            log_success "Security monitor service installed"
            ;;
        *)
            echo "Usage: $0 {start|stop|restart|reload|status|monitor|install}"
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"