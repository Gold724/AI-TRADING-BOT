#!/bin/bash
# Trae AI Trading Sentinel Health Check Script
# Monitors system health and trading bot status

set -euo pipefail

# Configuration
LOG_FILE="/var/log/trae-sentinel/health-check.log"
PID_FILE="/var/run/trae-sentinel/trae.pid"
API_ENDPOINT="http://localhost:5000/api/health"
MAX_MEMORY_MB=1800  # 1.8GB threshold
MAX_CPU_PERCENT=80
MAX_RESPONSE_TIME=5000  # 5 seconds

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$LOG_FILE"
}

# Check if process is running
check_process() {
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            log "✓ Trading bot process is running (PID: $pid)"
            return 0
        else
            error "✗ PID file exists but process is not running"
            rm -f "$PID_FILE"
            return 1
        fi
    else
        error "✗ PID file not found"
        return 1
    fi
}

# Check memory usage
check_memory() {
    local memory_mb=$(ps -o pid,rss -p $(cat "$PID_FILE" 2>/dev/null || echo "0") 2>/dev/null | tail -1 | awk '{print $2/1024}' || echo "0")
    if (( $(echo "$memory_mb > $MAX_MEMORY_MB" | bc -l) )); then
        error "✗ High memory usage: ${memory_mb}MB (threshold: ${MAX_MEMORY_MB}MB)"
        return 1
    else
        log "✓ Memory usage normal: ${memory_mb}MB"
        return 0
    fi
}

# Check CPU usage
check_cpu() {
    local cpu_percent=$(ps -o pid,pcpu -p $(cat "$PID_FILE" 2>/dev/null || echo "0") 2>/dev/null | tail -1 | awk '{print $2}' || echo "0")
    if (( $(echo "$cpu_percent > $MAX_CPU_PERCENT" | bc -l) )); then
        error "✗ High CPU usage: ${cpu_percent}% (threshold: ${MAX_CPU_PERCENT}%)"
        return 1
    else
        log "✓ CPU usage normal: ${cpu_percent}%"
        return 0
    fi
}

# Check API health
check_api() {
    local response_time=$(curl -w "%{time_total}" -s -o /dev/null "$API_ENDPOINT" 2>/dev/null || echo "999")
    local response_time_ms=$(echo "$response_time * 1000" | bc -l | cut -d. -f1)
    
    if [[ $response_time_ms -gt $MAX_RESPONSE_TIME ]]; then
        error "✗ API response slow: ${response_time_ms}ms (threshold: ${MAX_RESPONSE_TIME}ms)"
        return 1
    else
        log "✓ API response time normal: ${response_time_ms}ms"
        return 0
    fi
}

# Check disk space
check_disk() {
    local disk_usage=$(df /opt/trae-sentinel | tail -1 | awk '{print $5}' | sed 's/%//')
    if [[ $disk_usage -gt 85 ]]; then
        error "✗ High disk usage: ${disk_usage}%"
        return 1
    else
        log "✓ Disk usage normal: ${disk_usage}%"
        return 0
    fi
}

# Check log file sizes
check_logs() {
    local log_size=$(du -sm /var/log/trae-sentinel/ 2>/dev/null | cut -f1 || echo "0")
    if [[ $log_size -gt 500 ]]; then
        error "✗ Log directory size large: ${log_size}MB"
        # Rotate logs if too large
        find /var/log/trae-sentinel/ -name "*.log" -size +100M -exec gzip {} \;
        return 1
    else
        log "✓ Log size normal: ${log_size}MB"
        return 0
    fi
}

# Main health check
main() {
    log "Starting health check..."
    
    local failed_checks=0
    
    check_process || ((failed_checks++))
    check_memory || ((failed_checks++))
    check_cpu || ((failed_checks++))
    check_api || ((failed_checks++))
    check_disk || ((failed_checks++))
    check_logs || ((failed_checks++))
    
    if [[ $failed_checks -eq 0 ]]; then
        log "✓ All health checks passed"
        # Update systemd watchdog
        systemd-notify --status="Healthy: All checks passed"
        exit 0
    else
        error "✗ $failed_checks health check(s) failed"
        systemd-notify --status="Unhealthy: $failed_checks checks failed"
        
        # If critical failures, restart the service
        if [[ $failed_checks -ge 3 ]]; then
            error "Critical failure threshold reached. Requesting service restart..."
            systemctl restart trae.service
        fi
        
        exit 1
    fi
}

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Run main function
main "$@"