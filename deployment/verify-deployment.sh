#!/bin/bash

# TradeBot Sentinel - Deployment Verification Script
# This script verifies that all deployment components are working correctly

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/tmp/tradebot-deployment-verification.log"
TEST_TIMEOUT=30

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "$LOG_FILE"
}

# Test results tracking
TEST_RESULTS=()
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to run a test and track results
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_result="${3:-0}"  # Default to expecting success (0)
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    log_info "Running test: $test_name"
    
    if eval "$test_command" >> "$LOG_FILE" 2>&1; then
        if [ "$expected_result" -eq 0 ]; then
            log_success "✓ $test_name"
            TEST_RESULTS+=("PASS: $test_name")
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            log_error "✗ $test_name (expected failure but got success)"
            TEST_RESULTS+=("FAIL: $test_name (expected failure)")
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
    else
        if [ "$expected_result" -ne 0 ]; then
            log_success "✓ $test_name (expected failure)"
            TEST_RESULTS+=("PASS: $test_name (expected failure)")
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            log_error "✗ $test_name"
            TEST_RESULTS+=("FAIL: $test_name")
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
    fi
}

# Function to check if a service is running
check_service() {
    local service_name="$1"
    if systemctl is-active --quiet "$service_name"; then
        return 0
    else
        return 1
    fi
}

# Function to check if a port is listening
check_port() {
    local port="$1"
    local host="${2:-localhost}"
    if timeout "$TEST_TIMEOUT" bash -c "</dev/tcp/$host/$port"; then
        return 0
    else
        return 1
    fi
}

# Function to check HTTP endpoint
check_http_endpoint() {
    local url="$1"
    local expected_status="${2:-200}"
    local response_code
    
    response_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$TEST_TIMEOUT" "$url" || echo "000")
    
    if [ "$response_code" = "$expected_status" ]; then
        return 0
    else
        log_error "HTTP check failed: $url returned $response_code, expected $expected_status"
        return 1
    fi
}

# Function to verify environment variables
verify_environment() {
    log_info "Verifying environment configuration..."
    
    local env_file="$PROJECT_ROOT/.env"
    if [ ! -f "$env_file" ]; then
        log_error "Environment file not found: $env_file"
        return 1
    fi
    
    # Check required environment variables
    local required_vars=(
        "DATABASE_URL"
        "REDIS_URL"
        "FLASK_SECRET_KEY"
        "ENVIRONMENT"
    )
    
    source "$env_file"
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            log_error "Required environment variable not set: $var"
            return 1
        fi
    done
    
    log_success "Environment configuration verified"
    return 0
}

# Function to verify database connectivity
verify_database() {
    log_info "Verifying database connectivity..."
    
    if [ -z "${DATABASE_URL:-}" ]; then
        log_error "DATABASE_URL not set"
        return 1
    fi
    
    # Try to connect to database
    python3 -c "
import os
import psycopg2
from urllib.parse import urlparse

db_url = os.environ.get('DATABASE_URL')
if not db_url:
    exit(1)

try:
    parsed = urlparse(db_url)
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        user=parsed.username,
        password=parsed.password,
        database=parsed.path[1:] if parsed.path else 'postgres'
    )
    cursor = conn.cursor()
    cursor.execute('SELECT 1')
    cursor.fetchone()
    conn.close()
    print('Database connection successful')
except Exception as e:
    print(f'Database connection failed: {e}')
    exit(1)
" 2>/dev/null
}

# Function to verify Redis connectivity
verify_redis() {
    log_info "Verifying Redis connectivity..."
    
    if [ -z "${REDIS_URL:-}" ]; then
        log_error "REDIS_URL not set"
        return 1
    fi
    
    # Try to connect to Redis
    python3 -c "
import os
import redis
from urllib.parse import urlparse

redis_url = os.environ.get('REDIS_URL')
if not redis_url:
    exit(1)

try:
    r = redis.from_url(redis_url)
    r.ping()
    print('Redis connection successful')
except Exception as e:
    print(f'Redis connection failed: {e}')
    exit(1)
" 2>/dev/null
}

# Function to verify TradeBot service
verify_tradebot_service() {
    log_info "Verifying TradeBot service..."
    
    # Check if service is running
    if ! check_service "tradebot-sentinel"; then
        log_error "TradeBot service is not running"
        return 1
    fi
    
    # Check service logs for errors
    local recent_errors
    recent_errors=$(journalctl -u tradebot-sentinel --since "5 minutes ago" --no-pager | grep -i "error\|exception\|failed" | wc -l)
    
    if [ "$recent_errors" -gt 0 ]; then
        log_warning "Found $recent_errors recent errors in TradeBot service logs"
        journalctl -u tradebot-sentinel --since "5 minutes ago" --no-pager | grep -i "error\|exception\|failed" | tail -5
    fi
    
    log_success "TradeBot service is running"
    return 0
}

# Function to verify web frontend
verify_frontend() {
    log_info "Verifying web frontend..."
    
    # Check if frontend service is running (if using systemd)
    if systemctl list-units --type=service | grep -q "tradebot-frontend"; then
        if ! check_service "tradebot-frontend"; then
            log_warning "Frontend service is not running"
        fi
    fi
    
    # Check if Nginx is serving the frontend
    if check_service "nginx"; then
        log_success "Nginx is running"
    else
        log_warning "Nginx is not running"
    fi
    
    return 0
}

# Function to verify API endpoints
verify_api_endpoints() {
    log_info "Verifying API endpoints..."
    
    local base_url="http://localhost:8000"
    
    # Health check endpoint
    if check_http_endpoint "$base_url/health"; then
        log_success "Health endpoint is responding"
    else
        log_error "Health endpoint is not responding"
        return 1
    fi
    
    # API status endpoint
    if check_http_endpoint "$base_url/api/status"; then
        log_success "API status endpoint is responding"
    else
        log_warning "API status endpoint is not responding"
    fi
    
    return 0
}

# Function to verify security configuration
verify_security() {
    log_info "Verifying security configuration..."
    
    # Check firewall status
    if command -v ufw >/dev/null 2>&1; then
        if ufw status | grep -q "Status: active"; then
            log_success "UFW firewall is active"
        else
            log_warning "UFW firewall is not active"
        fi
    fi
    
    # Check Fail2Ban status
    if check_service "fail2ban"; then
        log_success "Fail2Ban is running"
    else
        log_warning "Fail2Ban is not running"
    fi
    
    # Check SSH configuration
    if grep -q "PasswordAuthentication no" /etc/ssh/sshd_config 2>/dev/null; then
        log_success "SSH password authentication is disabled"
    else
        log_warning "SSH password authentication may be enabled"
    fi
    
    return 0
}

# Function to verify monitoring
verify_monitoring() {
    log_info "Verifying monitoring setup..."
    
    # Check if monitoring services are running
    local monitoring_services=("prometheus" "grafana-server" "alertmanager")
    
    for service in "${monitoring_services[@]}"; do
        if systemctl list-units --type=service | grep -q "$service"; then
            if check_service "$service"; then
                log_success "$service is running"
            else
                log_warning "$service is not running"
            fi
        fi
    done
    
    return 0
}

# Function to verify backup system
verify_backups() {
    log_info "Verifying backup system..."
    
    local backup_dir="/opt/tradebot-backups"
    
    if [ -d "$backup_dir" ]; then
        local recent_backups
        recent_backups=$(find "$backup_dir" -name "*.tar.gz" -mtime -1 | wc -l)
        
        if [ "$recent_backups" -gt 0 ]; then
            log_success "Found $recent_backups recent backups"
        else
            log_warning "No recent backups found"
        fi
    else
        log_warning "Backup directory not found: $backup_dir"
    fi
    
    return 0
}

# Function to run performance tests
verify_performance() {
    log_info "Running basic performance tests..."
    
    # Check system resources
    local cpu_usage
    local memory_usage
    local disk_usage
    
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    memory_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    disk_usage=$(df / | tail -1 | awk '{print $5}' | cut -d'%' -f1)
    
    log_info "System resources: CPU: ${cpu_usage}%, Memory: ${memory_usage}%, Disk: ${disk_usage}%"
    
    # Check if resources are within acceptable limits
    if (( $(echo "$cpu_usage > 80" | bc -l) )); then
        log_warning "High CPU usage: ${cpu_usage}%"
    fi
    
    if (( $(echo "$memory_usage > 80" | bc -l) )); then
        log_warning "High memory usage: ${memory_usage}%"
    fi
    
    if [ "$disk_usage" -gt 80 ]; then
        log_warning "High disk usage: ${disk_usage}%"
    fi
    
    return 0
}

# Function to generate verification report
generate_report() {
    log_info "Generating verification report..."
    
    local report_file="/tmp/tradebot-verification-report-$(date +%Y%m%d-%H%M%S).txt"
    
    {
        echo "TradeBot Sentinel Deployment Verification Report"
        echo "Generated: $(date)"
        echo "======================================================"
        echo ""
        echo "Test Summary:"
        echo "Total Tests: $TOTAL_TESTS"
        echo "Passed: $PASSED_TESTS"
        echo "Failed: $FAILED_TESTS"
        echo "Success Rate: $(( PASSED_TESTS * 100 / TOTAL_TESTS ))%"
        echo ""
        echo "Detailed Results:"
        for result in "${TEST_RESULTS[@]}"; do
            echo "  $result"
        done
        echo ""
        echo "System Information:"
        echo "Hostname: $(hostname)"
        echo "OS: $(lsb_release -d 2>/dev/null | cut -f2 || echo "Unknown")"
        echo "Kernel: $(uname -r)"
        echo "Uptime: $(uptime -p)"
        echo ""
        echo "Service Status:"
        systemctl status tradebot-sentinel --no-pager -l || echo "TradeBot service not found"
        echo ""
        echo "Recent Logs (last 20 lines):"
        journalctl -u tradebot-sentinel --no-pager -n 20 || echo "No logs available"
    } > "$report_file"
    
    log_success "Verification report generated: $report_file"
    
    # Also display summary
    echo ""
    echo "======================================================"
    echo "VERIFICATION SUMMARY"
    echo "======================================================"
    echo "Total Tests: $TOTAL_TESTS"
    echo "Passed: $PASSED_TESTS"
    echo "Failed: $FAILED_TESTS"
    echo "Success Rate: $(( PASSED_TESTS * 100 / TOTAL_TESTS ))%"
    
    if [ "$FAILED_TESTS" -eq 0 ]; then
        log_success "All tests passed! Deployment is healthy."
        return 0
    else
        log_error "$FAILED_TESTS tests failed. Please review the issues above."
        return 1
    fi
}

# Main verification function
main() {
    log_info "Starting TradeBot Sentinel deployment verification..."
    log_info "Log file: $LOG_FILE"
    
    # Clear previous log
    > "$LOG_FILE"
    
    # Load environment if available
    if [ -f "$PROJECT_ROOT/.env" ]; then
        set -a
        source "$PROJECT_ROOT/.env"
        set +a
    fi
    
    # Run all verification tests
    run_test "Environment Configuration" "verify_environment"
    run_test "Database Connectivity" "verify_database"
    run_test "Redis Connectivity" "verify_redis"
    run_test "TradeBot Service" "verify_tradebot_service"
    run_test "Web Frontend" "verify_frontend"
    run_test "API Endpoints" "verify_api_endpoints"
    run_test "Security Configuration" "verify_security"
    run_test "Monitoring Setup" "verify_monitoring"
    run_test "Backup System" "verify_backups"
    run_test "Performance Check" "verify_performance"
    
    # Generate final report
    generate_report
}

# Script usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -v, --verbose  Enable verbose output"
    echo "  -q, --quiet    Suppress non-error output"
    echo "  --report-only  Generate report from existing log"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run full verification"
    echo "  $0 --verbose          # Run with verbose output"
    echo "  $0 --report-only      # Generate report only"
}

# Parse command line arguments
VERBOSE=false
QUIET=false
REPORT_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -q|--quiet)
            QUIET=true
            shift
            ;;
        --report-only)
            REPORT_ONLY=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Adjust logging based on options
if [ "$QUIET" = true ]; then
    exec 1>/dev/null
fi

# Run verification or generate report
if [ "$REPORT_ONLY" = true ]; then
    generate_report
else
    main
fi

exit $?