#!/bin/bash
# Trae AI Trading Sentinel System Monitor
# Collects system metrics and sends to monitoring stack

set -euo pipefail

# Configuration
METRICS_FILE="/var/log/trae-sentinel/system-metrics.log"
PROMETHEUS_PUSHGATEWAY="http://localhost:9091"
JOB_NAME="trae-system-monitor"
INSTANCE_NAME=$(hostname)
ALERT_THRESHOLD_CPU=85
ALERT_THRESHOLD_MEMORY=90
ALERT_THRESHOLD_DISK=85

# Logging function
log_metric() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >> "$METRICS_FILE"
}

# Get CPU usage
get_cpu_usage() {
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')
    echo "${cpu_usage:-0}"
}

# Get memory usage
get_memory_usage() {
    local mem_total=$(free | grep '^Mem:' | awk '{print $2}')
    local mem_used=$(free | grep '^Mem:' | awk '{print $3}')
    local mem_percent=$(echo "scale=2; $mem_used * 100 / $mem_total" | bc)
    echo "${mem_percent:-0}"
}

# Get disk usage
get_disk_usage() {
    local disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    echo "${disk_usage:-0}"
}

# Get network stats
get_network_stats() {
    local interface=$(ip route | grep default | awk '{print $5}' | head -1)
    if [[ -n "$interface" ]]; then
        local rx_bytes=$(cat "/sys/class/net/$interface/statistics/rx_bytes")
        local tx_bytes=$(cat "/sys/class/net/$interface/statistics/tx_bytes")
        echo "rx:$rx_bytes tx:$tx_bytes"
    else
        echo "rx:0 tx:0"
    fi
}

# Get load average
get_load_average() {
    local load_1min=$(uptime | awk -F'load average:' '{print $2}' | awk -F',' '{print $1}' | tr -d ' ')
    echo "${load_1min:-0}"
}

# Get process count
get_process_count() {
    local total_processes=$(ps aux | wc -l)
    local trae_processes=$(pgrep -f "python.*main.py" | wc -l)
    echo "total:$total_processes trae:$trae_processes"
}

# Get trading bot specific metrics
get_trading_metrics() {
    local api_response=$(curl -s -w "%{http_code}" -o /dev/null "http://localhost:5000/api/health" 2>/dev/null || echo "000")
    local bot_status="down"
    
    if [[ "$api_response" == "200" ]]; then
        bot_status="up"
    fi
    
    # Check if main process is running
    local main_pid=$(pgrep -f "python.*main.py" | head -1 || echo "0")
    local main_status="down"
    
    if [[ "$main_pid" != "0" ]] && ps -p "$main_pid" > /dev/null 2>&1; then
        main_status="up"
        
        # Get process memory and CPU usage
        local proc_mem=$(ps -o rss= -p "$main_pid" 2>/dev/null | awk '{print $1/1024}' || echo "0")
        local proc_cpu=$(ps -o pcpu= -p "$main_pid" 2>/dev/null | tr -d ' ' || echo "0")
        
        echo "api:$bot_status main:$main_status pid:$main_pid mem:${proc_mem}MB cpu:${proc_cpu}%"
    else
        echo "api:$bot_status main:$main_status pid:0 mem:0MB cpu:0%"
    fi
}

# Get Docker container stats (if monitoring stack is running)
get_docker_stats() {
    if command -v docker &> /dev/null && docker info &> /dev/null; then
        local running_containers=$(docker ps -q | wc -l)
        local total_containers=$(docker ps -a -q | wc -l)
        
        # Check monitoring containers
        local prometheus_status="down"
        local grafana_status="down"
        local alertmanager_status="down"
        
        if docker ps --format "table {{.Names}}" | grep -q "prometheus"; then
            prometheus_status="up"
        fi
        
        if docker ps --format "table {{.Names}}" | grep -q "grafana"; then
            grafana_status="up"
        fi
        
        if docker ps --format "table {{.Names}}" | grep -q "alertmanager"; then
            alertmanager_status="up"
        fi
        
        echo "running:$running_containers total:$total_containers prometheus:$prometheus_status grafana:$grafana_status alertmanager:$alertmanager_status"
    else
        echo "running:0 total:0 prometheus:down grafana:down alertmanager:down"
    fi
}

# Send metrics to Prometheus Pushgateway (if available)
send_to_prometheus() {
    local cpu_usage=$1
    local mem_usage=$2
    local disk_usage=$3
    local load_avg=$4
    
    if command -v curl &> /dev/null; then
        # Create metrics payload
        local metrics=""
        metrics+="# HELP trae_system_cpu_usage_percent CPU usage percentage\n"
        metrics+="# TYPE trae_system_cpu_usage_percent gauge\n"
        metrics+="trae_system_cpu_usage_percent{instance=\"$INSTANCE_NAME\"} $cpu_usage\n"
        
        metrics+="# HELP trae_system_memory_usage_percent Memory usage percentage\n"
        metrics+="# TYPE trae_system_memory_usage_percent gauge\n"
        metrics+="trae_system_memory_usage_percent{instance=\"$INSTANCE_NAME\"} $mem_usage\n"
        
        metrics+="# HELP trae_system_disk_usage_percent Disk usage percentage\n"
        metrics+="# TYPE trae_system_disk_usage_percent gauge\n"
        metrics+="trae_system_disk_usage_percent{instance=\"$INSTANCE_NAME\"} $disk_usage\n"
        
        metrics+="# HELP trae_system_load_average_1min Load average 1 minute\n"
        metrics+="# TYPE trae_system_load_average_1min gauge\n"
        metrics+="trae_system_load_average_1min{instance=\"$INSTANCE_NAME\"} $load_avg\n"
        
        # Send to pushgateway (ignore errors)
        echo -e "$metrics" | curl -s --data-binary @- "$PROMETHEUS_PUSHGATEWAY/metrics/job/$JOB_NAME/instance/$INSTANCE_NAME" > /dev/null 2>&1 || true
    fi
}

# Check for alerts and send notifications
check_alerts() {
    local cpu_usage=$1
    local mem_usage=$2
    local disk_usage=$3
    
    local alerts=""
    
    # CPU alert
    if (( $(echo "$cpu_usage > $ALERT_THRESHOLD_CPU" | bc -l) )); then
        alerts+="HIGH CPU: ${cpu_usage}% (threshold: ${ALERT_THRESHOLD_CPU}%) "
    fi
    
    # Memory alert
    if (( $(echo "$mem_usage > $ALERT_THRESHOLD_MEMORY" | bc -l) )); then
        alerts+="HIGH MEMORY: ${mem_usage}% (threshold: ${ALERT_THRESHOLD_MEMORY}%) "
    fi
    
    # Disk alert
    if (( $(echo "$disk_usage > $ALERT_THRESHOLD_DISK" | bc -l) )); then
        alerts+="HIGH DISK: ${disk_usage}% (threshold: ${ALERT_THRESHOLD_DISK}%) "
    fi
    
    if [[ -n "$alerts" ]]; then
        log_metric "ALERT: $alerts"
        
        # Send to syslog
        logger -t "trae-monitor" "ALERT: $alerts"
        
        # Optional: Send to Slack webhook (if configured)
        if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
            curl -s -X POST -H 'Content-type: application/json' \
                --data "{\"text\":\"🚨 Trae Sentinel Alert: $alerts\"}" \
                "$SLACK_WEBHOOK_URL" > /dev/null 2>&1 || true
        fi
    fi
}

# Generate system report
generate_report() {
    local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    local cpu_usage=$1
    local mem_usage=$2
    local disk_usage=$3
    local load_avg=$4
    local network_stats=$5
    local process_stats=$6
    local trading_metrics=$7
    local docker_stats=$8
    
    cat << EOF
=== Trae AI Trading Sentinel System Report ===
Timestamp: $timestamp
Instance: $INSTANCE_NAME

System Resources:
  CPU Usage: ${cpu_usage}%
  Memory Usage: ${mem_usage}%
  Disk Usage: ${disk_usage}%
  Load Average (1min): $load_avg

Network Stats:
  $network_stats

Process Stats:
  $process_stats

Trading Bot Status:
  $trading_metrics

Docker Containers:
  $docker_stats

Uptime: $(uptime -p)
Kernel: $(uname -r)
=== End Report ===
EOF
}

# Main monitoring function
main() {
    # Ensure log directory exists
    mkdir -p "$(dirname "$METRICS_FILE")"
    
    # Collect metrics
    local cpu_usage=$(get_cpu_usage)
    local mem_usage=$(get_memory_usage)
    local disk_usage=$(get_disk_usage)
    local load_avg=$(get_load_average)
    local network_stats=$(get_network_stats)
    local process_stats=$(get_process_count)
    local trading_metrics=$(get_trading_metrics)
    local docker_stats=$(get_docker_stats)
    
    # Log metrics
    log_metric "CPU:${cpu_usage}% MEM:${mem_usage}% DISK:${disk_usage}% LOAD:${load_avg} NET:[$network_stats] PROC:[$process_stats] TRADE:[$trading_metrics] DOCKER:[$docker_stats]"
    
    # Send to Prometheus (if available)
    send_to_prometheus "$cpu_usage" "$mem_usage" "$disk_usage" "$load_avg"
    
    # Check for alerts
    check_alerts "$cpu_usage" "$mem_usage" "$disk_usage"
    
    # Generate detailed report (if requested)
    if [[ "${1:-}" == "--report" ]]; then
        generate_report "$cpu_usage" "$mem_usage" "$disk_usage" "$load_avg" "$network_stats" "$process_stats" "$trading_metrics" "$docker_stats"
    fi
    
    # Cleanup old logs (keep last 1000 lines)
    if [[ -f "$METRICS_FILE" ]]; then
        tail -n 1000 "$METRICS_FILE" > "${METRICS_FILE}.tmp" && mv "${METRICS_FILE}.tmp" "$METRICS_FILE"
    fi
}

# Handle command line arguments
case "${1:-}" in
    --report)
        main --report
        ;;
    --help)
        echo "Usage: $0 [--report] [--help]"
        echo "  --report  Generate detailed system report"
        echo "  --help    Show this help message"
        ;;
    *)
        main
        ;;
esac