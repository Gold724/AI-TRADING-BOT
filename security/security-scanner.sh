#!/bin/bash

# AI Trading Sentinel - Comprehensive Security Scanner
# Automated vulnerability assessment and security monitoring

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="/var/log/security-scanner"
REPORT_DIR="$PROJECT_ROOT/security/reports"
DATE=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE="$REPORT_DIR/security_report_$DATE.json"
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"
EMAIL_RECIPIENT="${SECURITY_EMAIL:-admin@your-domain.com}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_DIR/scanner.log"
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

# Initialize directories
init_directories() {
    mkdir -p "$LOG_DIR" "$REPORT_DIR"
    chmod 750 "$LOG_DIR" "$REPORT_DIR"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root for comprehensive security scanning"
        exit 1
    fi
}

# Install security tools if not present
install_security_tools() {
    log_info "Checking and installing security tools..."
    
    # Update package list
    apt-get update -qq
    
    # Install essential security tools
    local tools=(
        "nmap"           # Network scanner
        "nikto"          # Web vulnerability scanner
        "lynis"          # System auditing tool
        "rkhunter"       # Rootkit hunter
        "chkrootkit"     # Rootkit checker
        "clamav"         # Antivirus
        "fail2ban"       # Intrusion prevention
        "aide"           # File integrity checker
        "tiger"          # Security audit tool
        "unhide"         # Hidden process detector
        "debsums"        # Package integrity checker
        "tripwire"       # File integrity monitoring
        "ossec-hids"     # Host-based intrusion detection
        "suricata"       # Network threat detection
        "john"           # Password cracker (for testing)
        "hydra"          # Network login cracker (for testing)
        "sqlmap"         # SQL injection testing
        "dirb"           # Web content scanner
        "gobuster"       # Directory/file brute-forcer
        "wpscan"         # WordPress security scanner
        "sslyze"         # SSL/TLS analyzer
        "testssl.sh"     # SSL/TLS tester
    )
    
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_info "Installing $tool..."
            apt-get install -y "$tool" || log_warning "Failed to install $tool"
        fi
    done
    
    # Install additional Python security tools
    pip3 install --quiet bandit safety semgrep || log_warning "Failed to install Python security tools"
    
    # Install Docker security tools
    if command -v docker &> /dev/null; then
        docker pull aquasec/trivy || log_warning "Failed to pull Trivy Docker image"
        docker pull clair/clair || log_warning "Failed to pull Clair Docker image"
    fi
    
    log_success "Security tools installation completed"
}

# System security audit
system_audit() {
    log_info "Starting system security audit..."
    
    local audit_results="$REPORT_DIR/system_audit_$DATE.txt"
    
    {
        echo "=== SYSTEM SECURITY AUDIT REPORT ==="
        echo "Date: $(date)"
        echo "Hostname: $(hostname)"
        echo "Kernel: $(uname -r)"
        echo "Distribution: $(lsb_release -d 2>/dev/null || echo 'Unknown')"
        echo ""
        
        # Lynis system audit
        echo "=== LYNIS SYSTEM AUDIT ==="
        lynis audit system --quiet --no-colors 2>/dev/null || echo "Lynis audit failed"
        echo ""
        
        # Check for rootkits
        echo "=== ROOTKIT DETECTION ==="
        rkhunter --check --skip-keypress --report-warnings-only 2>/dev/null || echo "RKHunter check failed"
        chkrootkit -q 2>/dev/null || echo "Chkrootkit check failed"
        echo ""
        
        # File system integrity
        echo "=== FILE SYSTEM INTEGRITY ==="
        if command -v aide &> /dev/null; then
            aide --check 2>/dev/null || echo "AIDE check failed (may need initialization)"
        fi
        debsums -c 2>/dev/null | head -20 || echo "Debsums check failed"
        echo ""
        
        # Process analysis
        echo "=== PROCESS ANALYSIS ==="
        unhide proc 2>/dev/null | head -10 || echo "Unhide process check failed"
        ps aux --sort=-%cpu | head -10
        echo ""
        
        # Network security
        echo "=== NETWORK SECURITY ==="
        netstat -tuln | grep LISTEN
        ss -tuln | grep LISTEN
        echo ""
        
        # User and permission audit
        echo "=== USER AND PERMISSION AUDIT ==="
        awk -F: '($3 == 0) {print}' /etc/passwd
        find /home -name ".*" -type f -exec ls -la {} \; 2>/dev/null | head -10
        find / -perm -4000 -type f 2>/dev/null | head -10
        echo ""
        
        # Log analysis
        echo "=== LOG ANALYSIS ==="
        tail -20 /var/log/auth.log 2>/dev/null || echo "Auth log not accessible"
        tail -20 /var/log/syslog 2>/dev/null || echo "Syslog not accessible"
        
    } > "$audit_results"
    
    log_success "System audit completed: $audit_results"
}

# Network security scan
network_scan() {
    log_info "Starting network security scan..."
    
    local network_results="$REPORT_DIR/network_scan_$DATE.txt"
    local target_host="${1:-localhost}"
    
    {
        echo "=== NETWORK SECURITY SCAN REPORT ==="
        echo "Target: $target_host"
        echo "Date: $(date)"
        echo ""
        
        # Port scan
        echo "=== PORT SCAN ==="
        nmap -sS -sV -O -A "$target_host" 2>/dev/null || echo "Nmap scan failed"
        echo ""
        
        # SSL/TLS analysis
        echo "=== SSL/TLS ANALYSIS ==="
        if command -v testssl.sh &> /dev/null; then
            testssl.sh --quiet "$target_host":443 2>/dev/null || echo "SSL test failed"
        fi
        if command -v sslyze &> /dev/null; then
            sslyze --regular "$target_host":443 2>/dev/null || echo "SSLyze scan failed"
        fi
        echo ""
        
        # Web vulnerability scan
        echo "=== WEB VULNERABILITY SCAN ==="
        if [[ "$target_host" != "localhost" ]] && [[ "$target_host" != "127.0.0.1" ]]; then
            nikto -h "http://$target_host" -Format txt 2>/dev/null || echo "Nikto scan failed"
        fi
        
    } > "$network_results"
    
    log_success "Network scan completed: $network_results"
}

# Web application security scan
web_app_scan() {
    log_info "Starting web application security scan..."
    
    local webapp_results="$REPORT_DIR/webapp_scan_$DATE.txt"
    local target_url="${1:-http://localhost}"
    
    {
        echo "=== WEB APPLICATION SECURITY SCAN ==="
        echo "Target: $target_url"
        echo "Date: $(date)"
        echo ""
        
        # Directory enumeration
        echo "=== DIRECTORY ENUMERATION ==="
        if command -v gobuster &> /dev/null; then
            gobuster dir -u "$target_url" -w /usr/share/wordlists/dirb/common.txt -q 2>/dev/null | head -20 || echo "Gobuster scan failed"
        fi
        if command -v dirb &> /dev/null; then
            dirb "$target_url" -S -w 2>/dev/null | head -20 || echo "Dirb scan failed"
        fi
        echo ""
        
        # SQL injection testing
        echo "=== SQL INJECTION TESTING ==="
        if command -v sqlmap &> /dev/null; then
            sqlmap -u "$target_url" --batch --level=1 --risk=1 --threads=5 --timeout=10 2>/dev/null | head -20 || echo "SQLMap scan failed"
        fi
        echo ""
        
        # WordPress scan (if applicable)
        echo "=== WORDPRESS SCAN ==="
        if command -v wpscan &> /dev/null; then
            wpscan --url "$target_url" --no-banner --random-user-agent 2>/dev/null | head -20 || echo "WPScan failed (not WordPress or scan error)"
        fi
        
    } > "$webapp_results"
    
    log_success "Web application scan completed: $webapp_results"
}

# Code security analysis
code_analysis() {
    log_info "Starting code security analysis..."
    
    local code_results="$REPORT_DIR/code_analysis_$DATE.txt"
    
    {
        echo "=== CODE SECURITY ANALYSIS ==="
        echo "Project: $PROJECT_ROOT"
        echo "Date: $(date)"
        echo ""
        
        # Python security analysis with Bandit
        echo "=== PYTHON SECURITY ANALYSIS (BANDIT) ==="
        if command -v bandit &> /dev/null; then
            bandit -r "$PROJECT_ROOT" -f txt -ll 2>/dev/null || echo "Bandit analysis failed"
        fi
        echo ""
        
        # Dependency vulnerability check
        echo "=== DEPENDENCY VULNERABILITY CHECK ==="
        if command -v safety &> /dev/null; then
            cd "$PROJECT_ROOT" && safety check 2>/dev/null || echo "Safety check failed"
        fi
        echo ""
        
        # Semgrep static analysis
        echo "=== STATIC CODE ANALYSIS (SEMGREP) ==="
        if command -v semgrep &> /dev/null; then
            cd "$PROJECT_ROOT" && semgrep --config=auto --quiet 2>/dev/null | head -20 || echo "Semgrep analysis failed"
        fi
        echo ""
        
        # Docker image security scan
        echo "=== DOCKER IMAGE SECURITY SCAN ==="
        if command -v docker &> /dev/null && docker images | grep -q "trading-bot"; then
            docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image trading-bot:latest 2>/dev/null || echo "Trivy Docker scan failed"
        fi
        
    } > "$code_results"
    
    log_success "Code analysis completed: $code_results"
}

# Malware scan
malware_scan() {
    log_info "Starting malware scan..."
    
    local malware_results="$REPORT_DIR/malware_scan_$DATE.txt"
    
    {
        echo "=== MALWARE SCAN REPORT ==="
        echo "Date: $(date)"
        echo ""
        
        # Update ClamAV database
        echo "=== CLAMAV MALWARE SCAN ==="
        freshclam --quiet 2>/dev/null || echo "ClamAV database update failed"
        clamscan -r --infected --no-summary "$PROJECT_ROOT" 2>/dev/null || echo "ClamAV scan completed (no threats found or scan failed)"
        echo ""
        
        # Additional malware checks
        echo "=== ADDITIONAL MALWARE CHECKS ==="
        find "$PROJECT_ROOT" -name "*.php" -exec grep -l "eval\|base64_decode\|shell_exec\|system\|passthru\|exec" {} \; 2>/dev/null | head -10 || echo "No suspicious PHP files found"
        find "$PROJECT_ROOT" -name "*.js" -exec grep -l "eval\|document.write\|innerHTML" {} \; 2>/dev/null | head -10 || echo "No suspicious JS files found"
        
    } > "$malware_results"
    
    log_success "Malware scan completed: $malware_results"
}

# Generate comprehensive report
generate_report() {
    log_info "Generating comprehensive security report..."
    
    local summary_file="$REPORT_DIR/security_summary_$DATE.json"
    
    # Create JSON report
    cat > "$summary_file" << EOF
{
    "scan_date": "$(date -Iseconds)",
    "hostname": "$(hostname)",
    "scan_type": "comprehensive",
    "reports": {
        "system_audit": "system_audit_$DATE.txt",
        "network_scan": "network_scan_$DATE.txt",
        "webapp_scan": "webapp_scan_$DATE.txt",
        "code_analysis": "code_analysis_$DATE.txt",
        "malware_scan": "malware_scan_$DATE.txt"
    },
    "critical_findings": [],
    "recommendations": [
        "Review all critical and high-severity findings",
        "Update all system packages and dependencies",
        "Implement additional security controls as needed",
        "Schedule regular security scans"
    ],
    "next_scan": "$(date -d '+1 week' -Iseconds)"
}
EOF

    log_success "Security report generated: $summary_file"
}

# Send notifications
send_notifications() {
    log_info "Sending security scan notifications..."
    
    local summary="Security scan completed on $(hostname) at $(date)"
    local report_count=$(find "$REPORT_DIR" -name "*_$DATE.*" | wc -l)
    
    # Slack notification
    if [[ -n "$SLACK_WEBHOOK_URL" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"🔒 $summary\\nGenerated $report_count security reports. Check $REPORT_DIR for details.\"}" \
            "$SLACK_WEBHOOK_URL" 2>/dev/null || log_warning "Failed to send Slack notification"
    fi
    
    # Email notification
    if command -v mail &> /dev/null; then
        echo "$summary\n\nGenerated $report_count security reports in $REPORT_DIR" | \
            mail -s "Security Scan Report - $(hostname)" "$EMAIL_RECIPIENT" 2>/dev/null || \
            log_warning "Failed to send email notification"
    fi
    
    log_success "Notifications sent"
}

# Cleanup old reports
cleanup_old_reports() {
    log_info "Cleaning up old security reports..."
    
    # Keep reports for 30 days
    find "$REPORT_DIR" -name "*.txt" -mtime +30 -delete 2>/dev/null || true
    find "$REPORT_DIR" -name "*.json" -mtime +30 -delete 2>/dev/null || true
    find "$LOG_DIR" -name "*.log" -mtime +30 -delete 2>/dev/null || true
    
    log_success "Old reports cleaned up"
}

# Main execution
main() {
    log_info "Starting AI Trading Sentinel Security Scanner"
    
    # Initialize
    init_directories
    check_root
    
    # Install tools if needed
    if [[ "${1:-}" == "--install" ]]; then
        install_security_tools
        exit 0
    fi
    
    # Run security scans
    system_audit
    network_scan "${1:-localhost}"
    web_app_scan "${2:-http://localhost}"
    code_analysis
    malware_scan
    
    # Generate reports and notifications
    generate_report
    send_notifications
    cleanup_old_reports
    
    log_success "Security scanning completed successfully"
}

# Error handling
trap 'log_error "Security scan interrupted"; exit 1' INT TERM

# Execute main function
main "$@"