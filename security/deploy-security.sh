#!/bin/bash

# AI Trading Sentinel - Security Deployment Script
# Automated deployment of comprehensive security infrastructure

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/var/log/security-deployment.log"
BACKUP_DIR="/var/backups/security-config"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Logging functions
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
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

log_header() {
    log "${PURPLE}=== $1 ===${NC}"
}

# Error handling
error_exit() {
    log_error "$1"
    exit 1
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error_exit "This script must be run as root. Use: sudo $0"
    fi
}

# Create backup of existing configuration
create_backup() {
    log_header "Creating Configuration Backup"
    
    mkdir -p "$BACKUP_DIR"
    local backup_timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_file="$BACKUP_DIR/security_backup_$backup_timestamp.tar.gz"
    
    # Backup existing configurations
    tar -czf "$backup_file" \
        /etc/nginx/nginx.conf \
        /etc/fail2ban/ \
        /etc/ssh/sshd_config \
        /etc/ufw/ \
        /etc/iptables/ \
        2>/dev/null || log_warning "Some files may not exist for backup"
    
    log_success "Backup created: $backup_file"
}

# Update system packages
update_system() {
    log_header "Updating System Packages"
    
    apt-get update -y
    apt-get upgrade -y
    apt-get autoremove -y
    apt-get autoclean
    
    log_success "System packages updated"
}

# Install required packages
install_packages() {
    log_header "Installing Security Packages"
    
    local packages=(
        # Core security tools
        "fail2ban"
        "ufw"
        "iptables-persistent"
        "rkhunter"
        "chkrootkit"
        "lynis"
        "aide"
        "clamav"
        "clamav-daemon"
        "clamav-freshclam"
        
        # Network security
        "nmap"
        "netstat-nat"
        "tcpdump"
        "wireshark-common"
        "iftop"
        "nethogs"
        
        # System monitoring
        "htop"
        "iotop"
        "sysstat"
        "psmisc"
        "lsof"
        
        # Web security
        "nginx"
        "nginx-extras"
        "certbot"
        "python3-certbot-nginx"
        
        # Development and analysis tools
        "git"
        "curl"
        "wget"
        "jq"
        "bc"
        "unzip"
        "zip"
        
        # Logging and monitoring
        "rsyslog"
        "logrotate"
        "auditd"
        "acct"
        
        # Mail system (for notifications)
        "postfix"
        "mailutils"
        
        # Additional security tools
        "apparmor"
        "apparmor-utils"
        "tiger"
        "unhide"
        "debsums"
    )
    
    for package in "${packages[@]}"; do
        log_info "Installing $package..."
        if apt-get install -y "$package"; then
            log_success "$package installed successfully"
        else
            log_warning "Failed to install $package, continuing..."
        fi
    done
    
    log_success "Package installation completed"
}

# Configure firewall (UFW)
configure_firewall() {
    log_header "Configuring Firewall (UFW)"
    
    # Reset UFW to defaults
    ufw --force reset
    
    # Set default policies
    ufw default deny incoming
    ufw default allow outgoing
    
    # Allow SSH (be careful!)
    ufw allow ssh
    
    # Allow HTTP and HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # Allow specific application ports
    ufw allow 3000/tcp comment 'React Dev Server'
    ufw allow 5000/tcp comment 'Flask Backend'
    ufw allow 8080/tcp comment 'Alternative HTTP'
    
    # Allow database connections (restrict to localhost)
    ufw allow from 127.0.0.1 to any port 5432 comment 'PostgreSQL'
    ufw allow from 127.0.0.1 to any port 6379 comment 'Redis'
    
    # Rate limiting for SSH
    ufw limit ssh/tcp
    
    # Enable UFW
    ufw --force enable
    
    log_success "Firewall configured and enabled"
}

# Configure Nginx security
configure_nginx_security() {
    log_header "Configuring Nginx Security"
    
    # Backup original nginx.conf
    cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup
    
    # Copy our security configuration
    cp "$SCRIPT_DIR/nginx-security.conf" /etc/nginx/conf.d/security.conf
    
    # Create rate limiting zones directory
    mkdir -p /var/cache/nginx/rate_limit
    chown www-data:www-data /var/cache/nginx/rate_limit
    
    # Test nginx configuration
    if nginx -t; then
        systemctl reload nginx
        log_success "Nginx security configuration applied"
    else
        log_error "Nginx configuration test failed"
        cp /etc/nginx/nginx.conf.backup /etc/nginx/nginx.conf
        return 1
    fi
}

# Configure Fail2Ban
configure_fail2ban() {
    log_header "Configuring Fail2Ban"
    
    # Copy our Fail2Ban configuration
    cp "$SCRIPT_DIR/fail2ban/jail.local" /etc/fail2ban/
    
    # Copy custom filters
    cp "$SCRIPT_DIR/fail2ban/filter.d/"*.conf /etc/fail2ban/filter.d/
    
    # Create custom action for Slack notifications
    cat > /etc/fail2ban/action.d/slack-notify.conf << 'EOF'
[Definition]
actionstart = 
actionstop = 
actioncheck = 
actionban = curl -X POST -H 'Content-type: application/json' --data '{"text":"🚫 Fail2Ban: Banned IP <ip> for <failures> failures in jail <name>"}' <slack_webhook_url>
actionunban = curl -X POST -H 'Content-type: application/json' --data '{"text":"✅ Fail2Ban: Unbanned IP <ip> from jail <name>"}' <slack_webhook_url>

[Init]
slack_webhook_url = 
EOF
    
    # Restart Fail2Ban
    systemctl restart fail2ban
    systemctl enable fail2ban
    
    log_success "Fail2Ban configured and started"
}

# Configure SSH hardening
configure_ssh_hardening() {
    log_header "Configuring SSH Hardening"
    
    # Backup original sshd_config
    cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup
    
    # Apply SSH hardening
    cat >> /etc/ssh/sshd_config << 'EOF'

# AI Trading Sentinel - SSH Security Hardening
Protocol 2
Port 22
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AuthenticationMethods publickey
PermitEmptyPasswords no
ChallengeResponseAuthentication no
UsePAM yes
X11Forwarding no
PrintMotd no
ClientAliveInterval 300
ClientAliveCountMax 2
MaxAuthTries 3
MaxSessions 2
LoginGraceTime 60
AllowUsers ubuntu
DenyUsers root
PermitUserEnvironment no
Compression no
TCPKeepAlive no
AllowAgentForwarding no
AllowTcpForwarding no
GatewayPorts no
PermitTunnel no
Banner /etc/ssh/banner
EOF
    
    # Create SSH banner
    cat > /etc/ssh/banner << 'EOF'
***************************************************************************
                    AI Trading Sentinel - Authorized Access Only
***************************************************************************

This system is for authorized users only. All activities are monitored and
logged. Unauthorized access is strictly prohibited and will be prosecuted
to the full extent of the law.

By accessing this system, you agree to comply with all applicable policies
and procedures. All connections are logged and monitored for security purposes.

***************************************************************************
EOF
    
    # Test SSH configuration
    if sshd -t; then
        systemctl reload sshd
        log_success "SSH hardening applied"
    else
        log_error "SSH configuration test failed"
        cp /etc/ssh/sshd_config.backup /etc/ssh/sshd_config
        return 1
    fi
}

# Configure system hardening
configure_system_hardening() {
    log_header "Configuring System Hardening"
    
    # Kernel parameters for security
    cat > /etc/sysctl.d/99-security.conf << 'EOF'
# AI Trading Sentinel - Security Kernel Parameters

# Network security
net.ipv4.ip_forward = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.secure_redirects = 0
net.ipv4.conf.default.secure_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0
net.ipv6.conf.default.accept_source_route = 0
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1
net.ipv4.tcp_syncookies = 1
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# Memory protection
kernel.dmesg_restrict = 1
kernel.kptr_restrict = 2
kernel.yama.ptrace_scope = 1
kernel.kexec_load_disabled = 1

# File system security
fs.suid_dumpable = 0
fs.protected_hardlinks = 1
fs.protected_symlinks = 1
fs.protected_fifos = 2
fs.protected_regular = 2

# Process security
kernel.core_uses_pid = 1
kernel.ctrl-alt-del = 0
EOF
    
    # Apply sysctl settings
    sysctl -p /etc/sysctl.d/99-security.conf
    
    # Configure login security
    cat > /etc/security/limits.d/99-security.conf << 'EOF'
# AI Trading Sentinel - Security Limits

# Limit core dumps
* hard core 0
* soft core 0

# Limit number of processes
* hard nproc 1000
* soft nproc 1000

# Limit memory usage
* hard as 2097152
* soft as 2097152
EOF
    
    # Configure password policy
    cat > /etc/security/pwquality.conf << 'EOF'
# AI Trading Sentinel - Password Quality

minlen = 12
minclass = 3
maxrepeat = 2
maxclasschars = 0
lcredit = -1
ucredit = -1
dcredit = -1
ocredit = -1
EOF
    
    log_success "System hardening configured"
}

# Install and configure ClamAV
configure_clamav() {
    log_header "Configuring ClamAV Antivirus"
    
    # Stop ClamAV services
    systemctl stop clamav-freshclam || true
    systemctl stop clamav-daemon || true
    
    # Update virus definitions
    freshclam
    
    # Configure ClamAV daemon
    sed -i 's/^Example/#Example/' /etc/clamav/clamd.conf
    sed -i 's/^#LocalSocket /LocalSocket /' /etc/clamav/clamd.conf
    
    # Configure freshclam
    sed -i 's/^Example/#Example/' /etc/clamav/freshclam.conf
    
    # Start and enable services
    systemctl start clamav-freshclam
    systemctl enable clamav-freshclam
    systemctl start clamav-daemon
    systemctl enable clamav-daemon
    
    log_success "ClamAV configured and started"
}

# Configure AIDE (Advanced Intrusion Detection Environment)
configure_aide() {
    log_header "Configuring AIDE File Integrity Monitoring"
    
    # Initialize AIDE database
    aideinit
    
    # Move database to proper location
    mv /var/lib/aide/aide.db.new /var/lib/aide/aide.db
    
    # Create daily AIDE check cron job
    cat > /etc/cron.daily/aide-check << 'EOF'
#!/bin/bash
# AI Trading Sentinel - Daily AIDE Check

AIDE_LOG="/var/log/aide/aide-$(date +%Y%m%d).log"
mkdir -p /var/log/aide

# Run AIDE check
aide --check > "$AIDE_LOG" 2>&1

# Check for changes
if [ $? -ne 0 ]; then
    # Send alert if changes detected
    mail -s "AIDE: File integrity violations detected on $(hostname)" root < "$AIDE_LOG"
fi

# Rotate logs
find /var/log/aide -name "aide-*.log" -mtime +30 -delete
EOF
    
    chmod +x /etc/cron.daily/aide-check
    
    log_success "AIDE configured with daily checks"
}

# Configure audit daemon
configure_auditd() {
    log_header "Configuring Audit Daemon"
    
    # Configure audit rules
    cat > /etc/audit/rules.d/99-security.rules << 'EOF'
# AI Trading Sentinel - Audit Rules

# Delete all existing rules
-D

# Buffer size
-b 8192

# Failure mode (0=silent, 1=printk, 2=panic)
-f 1

# Monitor authentication events
-w /etc/passwd -p wa -k identity
-w /etc/group -p wa -k identity
-w /etc/gshadow -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/security/opasswd -p wa -k identity

# Monitor login/logout events
-w /var/log/lastlog -p wa -k logins
-w /var/run/faillock -p wa -k logins

# Monitor network configuration
-a always,exit -F arch=b64 -S sethostname -S setdomainname -k system-locale
-a always,exit -F arch=b32 -S sethostname -S setdomainname -k system-locale
-w /etc/issue -p wa -k system-locale
-w /etc/issue.net -p wa -k system-locale
-w /etc/hosts -p wa -k system-locale
-w /etc/network -p wa -k system-locale

# Monitor time changes
-a always,exit -F arch=b64 -S adjtimex -S settimeofday -k time-change
-a always,exit -F arch=b32 -S adjtimex -S settimeofday -S stime -k time-change
-a always,exit -F arch=b64 -S clock_settime -k time-change
-a always,exit -F arch=b32 -S clock_settime -k time-change
-w /etc/localtime -p wa -k time-change

# Monitor system calls
-a always,exit -F arch=b64 -S chmod -S fchmod -S fchmodat -F auid>=1000 -F auid!=4294967295 -k perm_mod
-a always,exit -F arch=b32 -S chmod -S fchmod -S fchmodat -F auid>=1000 -F auid!=4294967295 -k perm_mod
-a always,exit -F arch=b64 -S chown -S fchown -S fchownat -S lchown -F auid>=1000 -F auid!=4294967295 -k perm_mod
-a always,exit -F arch=b32 -S chown -S fchown -S fchownat -S lchown -F auid>=1000 -F auid!=4294967295 -k perm_mod

# Monitor file access
-a always,exit -F arch=b64 -S creat -S open -S openat -S truncate -S ftruncate -F exit=-EACCES -F auid>=1000 -F auid!=4294967295 -k access
-a always,exit -F arch=b32 -S creat -S open -S openat -S truncate -S ftruncate -F exit=-EACCES -F auid>=1000 -F auid!=4294967295 -k access
-a always,exit -F arch=b64 -S creat -S open -S openat -S truncate -S ftruncate -F exit=-EPERM -F auid>=1000 -F auid!=4294967295 -k access
-a always,exit -F arch=b32 -S creat -S open -S openat -S truncate -S ftruncate -F exit=-EPERM -F auid>=1000 -F auid!=4294967295 -k access

# Monitor privileged commands
-a always,exit -F path=/usr/bin/passwd -F perm=x -F auid>=1000 -F auid!=4294967295 -k privileged-passwd
-a always,exit -F path=/usr/bin/su -F perm=x -F auid>=1000 -F auid!=4294967295 -k privileged-priv_change
-a always,exit -F path=/usr/bin/sudo -F perm=x -F auid>=1000 -F auid!=4294967295 -k privileged-priv_change

# Make rules immutable
-e 2
EOF
    
    # Restart auditd
    systemctl restart auditd
    systemctl enable auditd
    
    log_success "Audit daemon configured"
}

# Install security monitoring tools
install_security_tools() {
    log_header "Installing Additional Security Tools"
    
    # Install Lynis (security auditing tool)
    if ! command -v lynis &> /dev/null; then
        cd /tmp
        wget https://downloads.cisofy.com/lynis/lynis-3.0.8.tar.gz
        tar -xzf lynis-3.0.8.tar.gz
        mv lynis /opt/
        ln -sf /opt/lynis/lynis /usr/local/bin/lynis
        log_success "Lynis installed"
    fi
    
    # Install RKHunter signatures
    rkhunter --update
    rkhunter --propupd
    
    # Install additional security scanners
    pip3 install --upgrade bandit safety semgrep
    
    log_success "Security tools installed"
}

# Deploy security monitoring
deploy_security_monitoring() {
    log_header "Deploying Security Monitoring"
    
    # Make security scripts executable
    chmod +x "$SCRIPT_DIR/security-scanner.sh"
    chmod +x "$SCRIPT_DIR/security-monitor.sh"
    
    # Install security monitor as systemd service
    cp "$SCRIPT_DIR/security-monitor.service" /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable security-monitor
    
    # Create security monitoring directories
    mkdir -p /var/log/security-monitor
    mkdir -p "$SCRIPT_DIR/reports"
    mkdir -p "$SCRIPT_DIR/alerts"
    
    # Set proper permissions
    chown -R root:root "$SCRIPT_DIR"
    chmod 750 "$SCRIPT_DIR"
    chmod 640 "$SCRIPT_DIR/monitor.conf"
    
    # Start security monitor
    systemctl start security-monitor
    
    log_success "Security monitoring deployed and started"
}

# Configure log monitoring
configure_log_monitoring() {
    log_header "Configuring Log Monitoring"
    
    # Configure rsyslog for centralized logging
    cat > /etc/rsyslog.d/99-security.conf << 'EOF'
# AI Trading Sentinel - Security Logging

# Security events
auth,authpriv.*                 /var/log/auth.log
*.*;auth,authpriv.none          -/var/log/syslog

# Kernel messages
kern.*                          -/var/log/kern.log

# Mail system
mail.*                          -/var/log/mail.log

# Emergency messages
*.emerg                         :omusrmsg:*

# Security alerts to dedicated file
local0.*                        /var/log/security-alerts.log
EOF
    
    # Restart rsyslog
    systemctl restart rsyslog
    
    # Configure logrotate for security logs
    cat > /etc/logrotate.d/security << 'EOF'
/var/log/security-*.log {
    daily
    missingok
    rotate 90
    compress
    delaycompress
    notifempty
    create 640 root adm
    postrotate
        systemctl reload rsyslog
    endscript
}
EOF
    
    log_success "Log monitoring configured"
}

# Create security maintenance script
create_maintenance_script() {
    log_header "Creating Security Maintenance Script"
    
    cat > /usr/local/bin/security-maintenance << 'EOF'
#!/bin/bash
# AI Trading Sentinel - Security Maintenance Script

set -euo pipefail

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a /var/log/security-maintenance.log
}

log "Starting security maintenance..."

# Update virus definitions
log "Updating ClamAV virus definitions..."
freshclam

# Update RKHunter
log "Updating RKHunter..."
rkhunter --update --quiet

# Update AIDE database
log "Updating AIDE database..."
aide --update
mv /var/lib/aide/aide.db.new /var/lib/aide/aide.db

# Run security scans
log "Running security scans..."
/opt/ai-trading-sentinel/security/security-scanner.sh --quiet

# Clean up old logs
log "Cleaning up old logs..."
find /var/log -name "*.log.*.gz" -mtime +90 -delete
find /opt/ai-trading-sentinel/security/reports -name "*.json" -mtime +30 -delete
find /opt/ai-trading-sentinel/security/alerts -name "*.json" -mtime +7 -delete

# Update system packages
log "Checking for security updates..."
apt-get update -qq
security_updates=$(apt list --upgradable 2>/dev/null | grep -i security | wc -l)
if [ "$security_updates" -gt 0 ]; then
    log "Installing $security_updates security updates..."
    DEBIAN_FRONTEND=noninteractive apt-get upgrade -y
fi

log "Security maintenance completed"
EOF
    
    chmod +x /usr/local/bin/security-maintenance
    
    # Create cron job for weekly maintenance
    cat > /etc/cron.weekly/security-maintenance << 'EOF'
#!/bin/bash
/usr/local/bin/security-maintenance
EOF
    
    chmod +x /etc/cron.weekly/security-maintenance
    
    log_success "Security maintenance script created"
}

# Verify security configuration
verify_security_config() {
    log_header "Verifying Security Configuration"
    
    local errors=0
    
    # Check services
    local services=("ufw" "fail2ban" "nginx" "clamav-daemon" "auditd" "security-monitor")
    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service"; then
            log_success "$service is running"
        else
            log_error "$service is not running"
            ((errors++))
        fi
    done
    
    # Check firewall status
    if ufw status | grep -q "Status: active"; then
        log_success "UFW firewall is active"
    else
        log_error "UFW firewall is not active"
        ((errors++))
    fi
    
    # Check Nginx configuration
    if nginx -t &>/dev/null; then
        log_success "Nginx configuration is valid"
    else
        log_error "Nginx configuration has errors"
        ((errors++))
    fi
    
    # Check Fail2Ban jails
    local active_jails=$(fail2ban-client status | grep "Jail list" | cut -d: -f2 | wc -w)
    if [[ "$active_jails" -gt 0 ]]; then
        log_success "Fail2Ban has $active_jails active jails"
    else
        log_warning "No active Fail2Ban jails found"
    fi
    
    # Check file permissions
    local critical_files=(
        "/etc/ssh/sshd_config:600"
        "/etc/fail2ban/jail.local:644"
        "/opt/ai-trading-sentinel/security/monitor.conf:640"
    )
    
    for file_perm in "${critical_files[@]}"; do
        local file=$(echo "$file_perm" | cut -d: -f1)
        local expected_perm=$(echo "$file_perm" | cut -d: -f2)
        
        if [[ -f "$file" ]]; then
            local actual_perm=$(stat -c "%a" "$file")
            if [[ "$actual_perm" == "$expected_perm" ]]; then
                log_success "$file has correct permissions ($actual_perm)"
            else
                log_warning "$file has permissions $actual_perm, expected $expected_perm"
            fi
        else
            log_error "$file does not exist"
            ((errors++))
        fi
    done
    
    if [[ "$errors" -eq 0 ]]; then
        log_success "Security configuration verification completed successfully"
        return 0
    else
        log_error "Security configuration verification found $errors errors"
        return 1
    fi
}

# Generate security report
generate_security_report() {
    log_header "Generating Security Deployment Report"
    
    local report_file="/var/log/security-deployment-report-$(date +%Y%m%d_%H%M%S).json"
    
    cat > "$report_file" << EOF
{
    "deployment_timestamp": "$(date -Iseconds)",
    "hostname": "$(hostname)",
    "os_version": "$(lsb_release -d | cut -f2)",
    "kernel_version": "$(uname -r)",
    "security_components": {
        "firewall": "$(ufw status | head -1)",
        "fail2ban": "$(fail2ban-client status | head -1)",
        "nginx": "$(nginx -v 2>&1)",
        "clamav": "$(clamav-config --version 2>/dev/null || echo 'installed')",
        "aide": "$(aide --version | head -1)",
        "auditd": "$(auditctl -s | grep enabled)"
    },
    "active_services": [
EOF
    
    # Add active services to report
    local first=true
    for service in ufw fail2ban nginx clamav-daemon auditd security-monitor; do
        if systemctl is-active --quiet "$service"; then
            [[ "$first" == "true" ]] && first=false || echo "," >> "$report_file"
            echo "        \"$service\"" >> "$report_file"
        fi
    done
    
    cat >> "$report_file" << EOF
    ],
    "security_policies": {
        "ssh_hardening": true,
        "firewall_enabled": true,
        "intrusion_detection": true,
        "file_integrity_monitoring": true,
        "antivirus_protection": true,
        "audit_logging": true,
        "automated_monitoring": true
    },
    "deployment_status": "completed",
    "next_maintenance": "$(date -d '+1 week' -Iseconds)"
}
EOF
    
    log_success "Security deployment report generated: $report_file"
}

# Main deployment function
main() {
    log_header "AI Trading Sentinel - Security Deployment"
    log_info "Starting comprehensive security deployment..."
    
    # Check prerequisites
    check_root
    
    # Create backup
    create_backup
    
    # System preparation
    update_system
    install_packages
    
    # Core security configuration
    configure_firewall
    configure_ssh_hardening
    configure_system_hardening
    
    # Web security
    configure_nginx_security
    
    # Intrusion detection and prevention
    configure_fail2ban
    
    # Antivirus and malware protection
    configure_clamav
    
    # File integrity monitoring
    configure_aide
    
    # Audit logging
    configure_auditd
    
    # Additional security tools
    install_security_tools
    
    # Monitoring and alerting
    deploy_security_monitoring
    configure_log_monitoring
    
    # Maintenance automation
    create_maintenance_script
    
    # Verification and reporting
    verify_security_config
    generate_security_report
    
    log_header "Security Deployment Completed Successfully"
    log_success "All security components have been deployed and configured"
    log_info "Security monitoring is now active and running"
    log_info "Check /var/log/security-monitor/ for ongoing security alerts"
    log_info "Run 'systemctl status security-monitor' to check monitoring status"
    
    echo -e "\n${GREEN}🛡️  AI Trading Sentinel Security Deployment Complete! 🛡️${NC}\n"
    echo -e "${CYAN}Next steps:${NC}"
    echo -e "${YELLOW}1.${NC} Configure Slack webhook URL in /opt/ai-trading-sentinel/security/monitor.conf"
    echo -e "${YELLOW}2.${NC} Set up email notifications by configuring SECURITY_EMAIL"
    echo -e "${YELLOW}3.${NC} Review firewall rules: sudo ufw status verbose"
    echo -e "${YELLOW}4.${NC} Check security monitor: sudo systemctl status security-monitor"
    echo -e "${YELLOW}5.${NC} Run initial security scan: sudo /opt/ai-trading-sentinel/security/security-scanner.sh"
}

# Execute main function
main "$@"