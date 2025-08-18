#!/bin/bash

# TradeBot Sentinel - Health Monitoring Script
# Continuous monitoring and alerting for production deployment

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="${SCRIPT_DIR}/health-monitor.conf"
LOG_FILE="/var/log/tradebot-health-monitor.log"
PID_FILE="/var/run/tradebot-health-monitor.pid"
ALERT_COOLDOWN=300  # 5 minutes between same alerts
CHECK_INTERVAL=60   # Check every minute
MAX_LOG_SIZE=10485760  # 10MB

# Default thresholds (can be overridden in config file)
CPU_THRESHOLD=80
MEMORY_THRESHOLD=85
DISK_THRESHOLD=90
LOAD_THRESHOLD=4.0
API_TIMEOUT=10
MAX_FAILED_TRADES=5
MAX_ERROR_RATE=10  # errors per minute

# Alert channels
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"
EMAIL_RECIPIENTS="${EMAIL_RECIPIENTS:-}"
SMTP_HOST="${SMTP_HOST:-}"
SMTP_USERNAME="${SMTP_USERNAME:-}"
SMTP_PASSWORD="${SMTP_PASSWORD:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Alert tracking
declare -A LAST_ALERT_TIME
declare -A ALERT_COUNT

# Load configuration if exists
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
fi

# Logging functions
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
    
    # Also output to console if not running as daemon
    if [ "${DAEMON_MODE:-false}" != "true" ]; then
        case "$level" in
            "ERROR") echo -e "${RED}[$level]${NC} $message" ;;
            "WARN") echo -e "${YELLOW}[$level]${NC} $message" ;;
            "INFO") echo -e "${BLUE}[$level]${NC} $message" ;;
            "SUCCESS") echo -e "${GREEN}[$level]${NC} $message" ;;
            *) echo "[$level] $message" ;;
        esac
    fi
}

log_info() { log "INFO" "$@"; }
log_warn() { log "WARN" "$@"; }
log_error() { log "ERROR" "$@"; }
log_success() { log "SUCCESS" "$@"; }

# Function to rotate logs
rotate_logs() {
    if [ -f "$LOG_FILE" ] && [ $(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null || echo 0) -gt $MAX_LOG_SIZE ]; then
        mv "$LOG_FILE" "${LOG_FILE}.old"
        touch "$LOG_FILE"
        log_info "Log file rotated"
    fi
}

# Function to send Slack alert
send_slack_alert() {
    local severity="$1"
    local title="$2"
    local message="$3"
    local color="danger"
    
    [ -z "$SLACK_WEBHOOK_URL" ] && return 0
    
    case "$severity" in
        "critical") color="danger" ;;
        "warning") color="warning" ;;
        "info") color="good" ;;
    esac
    
    local payload=$(cat <<EOF
{
    "attachments": [
        {
            "color": "$color",
            "title": "TradeBot Alert: $title",
            "text": "$message",
            "fields": [
                {
                    "title": "Severity",
                    "value": "$severity",
                    "short": true
                },
                {
                    "title": "Host",
                    "value": "$(hostname)",
                    "short": true
                },
                {
                    "title": "Time",
                    "value": "$(date)",
                    "short": false
                }
            ]
        }
    ]
}
EOF
    )
    
    curl -X POST -H 'Content-type: application/json' \
        --data "$payload" \
        --max-time 10 \
        "$SLACK_WEBHOOK_URL" >/dev/null 2>&1 || log_warn "Failed to send Slack alert"
}

# Function to send email alert
send_email_alert() {
    local severity="$1"
    local title="$2"
    local message="$3"
    
    [ -z "$EMAIL_RECIPIENTS" ] || [ -z "$SMTP_HOST" ] && return 0
    
    local subject="TradeBot Alert [$severity]: $title"
    local body="TradeBot Sentinel Alert\n\nSeverity: $severity\nHost: $(hostname)\nTime: $(date)\n\nMessage:\n$message\n\nSystem Status:\n$(uptime)\n"
    
    # Use Python to send email
    python3 -c "
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

try:
    smtp_host = '$SMTP_HOST'
    smtp_username = '$SMTP_USERNAME'
    smtp_password = '$SMTP_PASSWORD'
    recipients = '$EMAIL_RECIPIENTS'.split(',')
    
    msg = MIMEMultipart()
    msg['From'] = smtp_username
    msg['To'] = ', '.join(recipients)
    msg['Subject'] = '$subject'
    
    msg.attach(MIMEText('$body', 'plain'))
    
    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_host, 587) as server:
        server.starttls(context=context)
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_username, recipients, msg.as_string())
    
    print('Email sent successfully')
except Exception as e:
    print(f'Failed to send email: {e}')
" 2>/dev/null || log_warn "Failed to send email alert"
}

# Function to send alert with cooldown
send_alert() {
    local alert_key="$1"
    local severity="$2"
    local title="$3"
    local message="$4"
    
    local current_time=$(date +%s)
    local last_alert=${LAST_ALERT_TIME[$alert_key]:-0}
    
    # Check cooldown period
    if [ $((current_time - last_alert)) -lt $ALERT_COOLDOWN ]; then
        return 0
    fi
    
    # Update alert tracking
    LAST_ALERT_TIME[$alert_key]=$current_time
    ALERT_COUNT[$alert_key]=$((${ALERT_COUNT[$alert_key]:-0} + 1))
    
    log_warn "ALERT: $title - $message"
    
    # Send to configured channels
    send_slack_alert "$severity" "$title" "$message"
    send_email_alert "$severity" "$title" "$message"
}

# Function to check system resources
check_system_resources() {
    local alerts_sent=0
    
    # CPU usage
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1 | cut -d',' -f1)
    if (( $(echo "$cpu_usage > $CPU_THRESHOLD" | bc -l) )); then
        send_alert "high_cpu" "warning" "High CPU Usage" "CPU usage is ${cpu_usage}% (threshold: ${CPU_THRESHOLD}%)"
        alerts_sent=1
    fi
    
    # Memory usage
    local memory_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    if (( $(echo "$memory_usage > $MEMORY_THRESHOLD" | bc -l) )); then
        send_alert "high_memory" "warning" "High Memory Usage" "Memory usage is ${memory_usage}% (threshold: ${MEMORY_THRESHOLD}%)"
        alerts_sent=1
    fi
    
    # Disk usage
    local disk_usage=$(df / | tail -1 | awk '{print $5}' | cut -d'%' -f1)
    if [ "$disk_usage" -gt "$DISK_THRESHOLD" ]; then
        send_alert "high_disk" "critical" "High Disk Usage" "Disk usage is ${disk_usage}% (threshold: ${DISK_THRESHOLD}%)"
        alerts_sent=1
    fi
    
    # Load average
    local load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | cut -d',' -f1)
    if (( $(echo "$load_avg > $LOAD_THRESHOLD" | bc -l) )); then
        send_alert "high_load" "warning" "High System Load" "Load average is $load_avg (threshold: $LOAD_THRESHOLD)"
        alerts_sent=1
    fi
    
    return $alerts_sent
}

# Function to check TradeBot service
check_tradebot_service() {
    local alerts_sent=0
    
    # Check if service is running
    if ! systemctl is-active --quiet tradebot-sentinel; then
        send_alert "service_down" "critical" "TradeBot Service Down" "TradeBot Sentinel service is not running"
        alerts_sent=1
        
        # Try to restart service
        log_info "Attempting to restart TradeBot service..."
        if systemctl restart tradebot-sentinel; then
            log_success "TradeBot service restarted successfully"
            send_alert "service_restarted" "info" "Service Restarted" "TradeBot Sentinel service was automatically restarted"
        else
            send_alert "restart_failed" "critical" "Service Restart Failed" "Failed to restart TradeBot Sentinel service"
        fi
    fi
    
    # Check for recent errors in logs
    local error_count=$(journalctl -u tradebot-sentinel --since "1 minute ago" --no-pager | grep -i "error\|exception\|failed" | wc -l)
    if [ "$error_count" -gt "$MAX_ERROR_RATE" ]; then
        local recent_errors=$(journalctl -u tradebot-sentinel --since "1 minute ago" --no-pager | grep -i "error\|exception\|failed" | tail -3)
        send_alert "high_error_rate" "warning" "High Error Rate" "$error_count errors in the last minute:\n$recent_errors"
        alerts_sent=1
    fi
    
    return $alerts_sent
}

# Function to check API health
check_api_health() {
    local alerts_sent=0
    local base_url="http://localhost:8000"
    
    # Health endpoint check
    local health_response=$(curl -s --max-time "$API_TIMEOUT" "$base_url/health" || echo "ERROR")
    if [[ "$health_response" == "ERROR" ]] || [[ ! "$health_response" =~ "ok" ]]; then
        send_alert "api_health_failed" "critical" "API Health Check Failed" "Health endpoint is not responding correctly"
        alerts_sent=1
    fi
    
    # API status check
    local status_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$API_TIMEOUT" "$base_url/api/status" || echo "000")
    if [ "$status_code" != "200" ]; then
        send_alert "api_status_failed" "warning" "API Status Check Failed" "Status endpoint returned HTTP $status_code"
        alerts_sent=1
    fi
    
    return $alerts_sent
}

# Function to check database connectivity
check_database() {
    local alerts_sent=0
    
    if [ -z "${DATABASE_URL:-}" ]; then
        return 0
    fi
    
    # Test database connection
    if ! python3 -c "
import os
import psycopg2
from urllib.parse import urlparse

db_url = os.environ.get('DATABASE_URL')
try:
    parsed = urlparse(db_url)
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        user=parsed.username,
        password=parsed.password,
        database=parsed.path[1:] if parsed.path else 'postgres',
        connect_timeout=10
    )
    cursor = conn.cursor()
    cursor.execute('SELECT 1')
    cursor.fetchone()
    conn.close()
except Exception as e:
    print(f'Database error: {e}')
    exit(1)
" 2>/dev/null; then
        send_alert "database_connection" "critical" "Database Connection Failed" "Cannot connect to PostgreSQL database"
        alerts_sent=1
    fi
    
    return $alerts_sent
}

# Function to check Redis connectivity
check_redis() {
    local alerts_sent=0
    
    if [ -z "${REDIS_URL:-}" ]; then
        return 0
    fi
    
    # Test Redis connection
    if ! python3 -c "
import os
import redis

redis_url = os.environ.get('REDIS_URL')
try:
    r = redis.from_url(redis_url, socket_connect_timeout=10)
    r.ping()
except Exception as e:
    print(f'Redis error: {e}')
    exit(1)
" 2>/dev/null; then
        send_alert "redis_connection" "critical" "Redis Connection Failed" "Cannot connect to Redis server"
        alerts_sent=1
    fi
    
    return $alerts_sent
}

# Function to check trading performance
check_trading_performance() {
    local alerts_sent=0
    
    # Check for failed trades in the last hour
    local failed_trades=$(journalctl -u tradebot-sentinel --since "1 hour ago" --no-pager | grep -i "trade.*failed\|order.*failed" | wc -l)
    if [ "$failed_trades" -gt "$MAX_FAILED_TRADES" ]; then
        send_alert "high_trade_failures" "warning" "High Trade Failure Rate" "$failed_trades failed trades in the last hour (threshold: $MAX_FAILED_TRADES)"
        alerts_sent=1
    fi
    
    # Check for login failures
    local login_failures=$(journalctl -u tradebot-sentinel --since "1 hour ago" --no-pager | grep -i "login.*failed\|authentication.*failed" | wc -l)
    if [ "$login_failures" -gt 0 ]; then
        send_alert "login_failures" "critical" "Broker Login Failures" "$login_failures login failures detected in the last hour"
        alerts_sent=1
    fi
    
    return $alerts_sent
}

# Function to check security events
check_security() {
    local alerts_sent=0
    
    # Check for SSH brute force attempts
    local ssh_failures=$(journalctl --since "1 hour ago" --no-pager | grep -i "failed password\|invalid user" | wc -l)
    if [ "$ssh_failures" -gt 10 ]; then
        send_alert "ssh_brute_force" "warning" "SSH Brute Force Detected" "$ssh_failures failed SSH login attempts in the last hour"
        alerts_sent=1
    fi
    
    # Check Fail2Ban bans
    if systemctl is-active --quiet fail2ban; then
        local recent_bans=$(journalctl -u fail2ban --since "1 hour ago" --no-pager | grep "Ban" | wc -l)
        if [ "$recent_bans" -gt 5 ]; then
            send_alert "high_fail2ban_activity" "info" "High Fail2Ban Activity" "$recent_bans IP addresses banned in the last hour"
            alerts_sent=1
        fi
    fi
    
    return $alerts_sent
}

# Function to perform all health checks
perform_health_checks() {
    local total_alerts=0
    
    log_info "Starting health checks..."
    
    # Load environment
    if [ -f "$PROJECT_ROOT/.env" ]; then
        set -a
        source "$PROJECT_ROOT/.env"
        set +a
    fi
    
    # Run all checks
    check_system_resources && total_alerts=$((total_alerts + $?))
    check_tradebot_service && total_alerts=$((total_alerts + $?))
    check_api_health && total_alerts=$((total_alerts + $?))
    check_database && total_alerts=$((total_alerts + $?))
    check_redis && total_alerts=$((total_alerts + $?))
    check_trading_performance && total_alerts=$((total_alerts + $?))
    check_security && total_alerts=$((total_alerts + $?))
    
    if [ "$total_alerts" -eq 0 ]; then
        log_info "All health checks passed"
    else
        log_warn "Health checks completed with $total_alerts alerts"
    fi
    
    return $total_alerts
}

# Function to run as daemon
run_daemon() {
    log_info "Starting TradeBot health monitor daemon (PID: $$)"
    echo $$ > "$PID_FILE"
    
    # Set up signal handlers
    trap 'log_info "Received SIGTERM, shutting down..."; rm -f "$PID_FILE"; exit 0' TERM
    trap 'log_info "Received SIGINT, shutting down..."; rm -f "$PID_FILE"; exit 0' INT
    
    DAEMON_MODE=true
    
    while true; do
        rotate_logs
        perform_health_checks
        sleep "$CHECK_INTERVAL"
    done
}

# Function to stop daemon
stop_daemon() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            log_info "Stopping health monitor daemon (PID: $pid)"
            kill "$pid"
            rm -f "$PID_FILE"
            log_success "Health monitor daemon stopped"
        else
            log_warn "PID file exists but process not running"
            rm -f "$PID_FILE"
        fi
    else
        log_warn "Health monitor daemon is not running"
    fi
}

# Function to show daemon status
show_status() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            log_info "Health monitor daemon is running (PID: $pid)"
            return 0
        else
            log_warn "PID file exists but process not running"
            rm -f "$PID_FILE"
            return 1
        fi
    else
        log_info "Health monitor daemon is not running"
        return 1
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 {start|stop|restart|status|check|test-alert}"
    echo ""
    echo "Commands:"
    echo "  start       Start the health monitor daemon"
    echo "  stop        Stop the health monitor daemon"
    echo "  restart     Restart the health monitor daemon"
    echo "  status      Show daemon status"
    echo "  check       Run health checks once"
    echo "  test-alert  Send a test alert"
    echo ""
    echo "Configuration file: $CONFIG_FILE"
    echo "Log file: $LOG_FILE"
}

# Function to test alerts
test_alert() {
    log_info "Sending test alert..."
    send_alert "test_alert" "info" "Test Alert" "This is a test alert from TradeBot health monitor on $(hostname)"
    log_success "Test alert sent"
}

# Main function
main() {
    local command="${1:-}"
    
    # Create log directory if it doesn't exist
    mkdir -p "$(dirname "$LOG_FILE")"
    
    case "$command" in
        "start")
            if show_status >/dev/null 2>&1; then
                log_warn "Health monitor daemon is already running"
                exit 1
            fi
            run_daemon
            ;;
        "stop")
            stop_daemon
            ;;
        "restart")
            stop_daemon
            sleep 2
            run_daemon
            ;;
        "status")
            show_status
            ;;
        "check")
            perform_health_checks
            ;;
        "test-alert")
            test_alert
            ;;
        "")
            show_usage
            exit 1
            ;;
        *)
            log_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"