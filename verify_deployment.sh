#!/bin/bash
# AI Trading Sentinel - Deployment Verification Script
# Verify that all services are running correctly after deployment

set -e

echo "🔍 AI Trading Sentinel - Deployment Verification"
echo "==============================================="

# Configuration
VPS_IP=$(curl -s ifconfig.me 2>/dev/null || echo "localhost")
BACKEND_PORT="8080"
FRONTEND_PORT="80"
MONITORING_PORT="3000"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✅ PASS${NC}: $message"
    elif [ "$status" = "FAIL" ]; then
        echo -e "${RED}❌ FAIL${NC}: $message"
    elif [ "$status" = "WARN" ]; then
        echo -e "${YELLOW}⚠️  WARN${NC}: $message"
    else
        echo -e "${BLUE}ℹ️  INFO${NC}: $message"
    fi
}

# Test counter
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

run_test() {
    local test_name=$1
    local test_command=$2
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo ""
    echo -e "${BLUE}Testing: $test_name${NC}"
    
    if eval "$test_command"; then
        print_status "PASS" "$test_name"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        print_status "FAIL" "$test_name"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

# Test 1: System Services
test_system_services() {
    echo "Checking system services..."
    
    # Check Nginx
    if systemctl is-active --quiet nginx; then
        print_status "PASS" "Nginx service is running"
    else
        print_status "FAIL" "Nginx service is not running"
        return 1
    fi
    
    # Check backend service (if configured)
    if systemctl list-units --full -all | grep -Fq "ai-trading-sentinel-backend.service"; then
        if systemctl is-active --quiet ai-trading-sentinel-backend; then
            print_status "PASS" "Backend service is running"
        else
            print_status "FAIL" "Backend service is not running"
            return 1
        fi
    else
        print_status "WARN" "Backend service not configured as systemd service"
    fi
    
    # Check monitoring service
    if systemctl list-units --full -all | grep -Fq "ai-trading-monitoring.service"; then
        if systemctl is-active --quiet ai-trading-monitoring; then
            print_status "PASS" "Monitoring service is running"
        else
            print_status "FAIL" "Monitoring service is not running"
            return 1
        fi
    else
        print_status "WARN" "Monitoring service not configured"
    fi
    
    return 0
}

# Test 2: Network Connectivity
test_network_connectivity() {
    echo "Testing network connectivity..."
    
    # Test frontend (port 80)
    if curl -s -f "http://localhost/" > /dev/null; then
        print_status "PASS" "Frontend accessible on port 80"
    else
        print_status "FAIL" "Frontend not accessible on port 80"
        return 1
    fi
    
    # Test backend API (port 8080)
    if curl -s -f "http://localhost:8080/health" > /dev/null; then
        print_status "PASS" "Backend API accessible on port 8080"
    elif curl -s -f "http://localhost:8080/" > /dev/null; then
        print_status "PASS" "Backend accessible on port 8080 (no health endpoint)"
    else
        print_status "FAIL" "Backend not accessible on port 8080"
        return 1
    fi
    
    # Test monitoring dashboard (port 3000)
    if curl -s -f "http://localhost:3000/health" > /dev/null; then
        print_status "PASS" "Monitoring dashboard accessible on port 3000"
    elif curl -s -f "http://localhost:3000/" > /dev/null; then
        print_status "PASS" "Monitoring dashboard accessible on port 3000"
    else
        print_status "WARN" "Monitoring dashboard not accessible on port 3000"
    fi
    
    return 0
}

# Test 3: File Permissions and Structure
test_file_structure() {
    echo "Checking file structure and permissions..."
    
    # Check frontend files
    if [ -d "/var/www/html" ] && [ "$(ls -A /var/www/html)" ]; then
        print_status "PASS" "Frontend files exist in /var/www/html"
    else
        print_status "FAIL" "Frontend files missing in /var/www/html"
        return 1
    fi
    
    # Check Nginx configuration
    if [ -f "/etc/nginx/sites-available/ai-trading-sentinel" ]; then
        print_status "PASS" "Nginx configuration file exists"
    else
        print_status "FAIL" "Nginx configuration file missing"
        return 1
    fi
    
    # Check if site is enabled
    if [ -L "/etc/nginx/sites-enabled/ai-trading-sentinel" ]; then
        print_status "PASS" "Nginx site is enabled"
    else
        print_status "FAIL" "Nginx site is not enabled"
        return 1
    fi
    
    # Check monitoring scripts
    if [ -d "/opt/ai-trading-sentinel/scripts" ]; then
        print_status "PASS" "Monitoring scripts directory exists"
    else
        print_status "WARN" "Monitoring scripts directory missing"
    fi
    
    return 0
}

# Test 4: API Endpoints
test_api_endpoints() {
    echo "Testing API endpoints..."
    
    # Test backend health endpoint
    HEALTH_RESPONSE=$(curl -s "http://localhost:8080/health" 2>/dev/null || echo "")
    if [ -n "$HEALTH_RESPONSE" ]; then
        print_status "PASS" "Backend health endpoint responding"
        echo "    Response: $HEALTH_RESPONSE"
    else
        print_status "WARN" "Backend health endpoint not responding"
    fi
    
    # Test monitoring API
    MONITOR_RESPONSE=$(curl -s "http://localhost:3000/api/status" 2>/dev/null || echo "")
    if [ -n "$MONITOR_RESPONSE" ]; then
        print_status "PASS" "Monitoring API responding"
        echo "    Response: $MONITOR_RESPONSE"
    else
        print_status "WARN" "Monitoring API not responding"
    fi
    
    return 0
}

# Test 5: Log Files
test_log_files() {
    echo "Checking log files..."
    
    # Check Nginx logs
    if [ -f "/var/log/nginx/access.log" ]; then
        print_status "PASS" "Nginx access log exists"
        RECENT_REQUESTS=$(tail -n 5 /var/log/nginx/access.log 2>/dev/null | wc -l)
        echo "    Recent requests: $RECENT_REQUESTS"
    else
        print_status "WARN" "Nginx access log not found"
    fi
    
    # Check application logs
    if [ -d "/var/log/ai-trading-sentinel" ]; then
        print_status "PASS" "Application log directory exists"
        LOG_COUNT=$(find /var/log/ai-trading-sentinel -name "*.log" | wc -l)
        echo "    Log files found: $LOG_COUNT"
    else
        print_status "WARN" "Application log directory not found"
    fi
    
    return 0
}

# Test 6: System Resources
test_system_resources() {
    echo "Checking system resources..."
    
    # CPU usage
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}' | sed 's/us,//')
    echo "    CPU Usage: ${CPU_USAGE}%"
    
    # Memory usage
    MEMORY_INFO=$(free -h | grep Mem)
    echo "    Memory: $MEMORY_INFO"
    
    # Disk usage
    DISK_USAGE=$(df -h / | awk 'NR==2{print $5}')
    echo "    Disk Usage: $DISK_USAGE"
    
    # Load average
    LOAD_AVG=$(uptime | awk -F'load average:' '{print $2}')
    echo "    Load Average:$LOAD_AVG"
    
    print_status "INFO" "System resources checked"
    return 0
}

# Test 7: Port Accessibility
test_port_accessibility() {
    echo "Testing port accessibility..."
    
    # Test if ports are listening
    if netstat -tuln | grep -q ":80 "; then
        print_status "PASS" "Port 80 is listening"
    else
        print_status "FAIL" "Port 80 is not listening"
        return 1
    fi
    
    if netstat -tuln | grep -q ":8080 "; then
        print_status "PASS" "Port 8080 is listening"
    else
        print_status "WARN" "Port 8080 is not listening"
    fi
    
    if netstat -tuln | grep -q ":3000 "; then
        print_status "PASS" "Port 3000 is listening"
    else
        print_status "WARN" "Port 3000 is not listening"
    fi
    
    return 0
}

# Main verification process
main() {
    echo ""
    echo "Starting deployment verification..."
    echo "VPS IP: $VPS_IP"
    echo ""
    
    # Run all tests
    run_test "System Services" "test_system_services"
    run_test "Network Connectivity" "test_network_connectivity"
    run_test "File Structure" "test_file_structure"
    run_test "API Endpoints" "test_api_endpoints"
    run_test "Log Files" "test_log_files"
    run_test "System Resources" "test_system_resources"
    run_test "Port Accessibility" "test_port_accessibility"
    
    # Summary
    echo ""
    echo "==============================================="
    echo "🔍 DEPLOYMENT VERIFICATION SUMMARY"
    echo "==============================================="
    echo "Total Tests: $TOTAL_TESTS"
    echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
    echo -e "Failed: ${RED}$FAILED_TESTS${NC}"
    echo ""
    
    if [ $FAILED_TESTS -eq 0 ]; then
        print_status "PASS" "All critical tests passed! 🎉"
        echo ""
        echo "🌐 Access URLs:"
        echo "   Frontend: http://$VPS_IP/"
        echo "   Backend API: http://$VPS_IP:8080/"
        echo "   Monitoring: http://$VPS_IP:3000/"
        echo ""
        echo "✅ Deployment verification completed successfully!"
        exit 0
    else
        print_status "FAIL" "Some tests failed. Please review and fix issues."
        echo ""
        echo "🔧 Troubleshooting:"
        echo "   • Check service status: systemctl status nginx"
        echo "   • Check logs: tail -f /var/log/nginx/error.log"
        echo "   • Restart services: sudo systemctl restart nginx"
        echo ""
        exit 1
    fi
}

# Run main function
main