#!/bin/bash

# AI Trading Sentinel - Security Hardening Script
# Production security configuration for Contabo VPS
# Run as root: sudo bash security_hardening.sh

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
LOG_FILE="/var/log/security_hardening.log"
exec 1> >(tee -a "$LOG_FILE")
exec 2> >(tee -a "$LOG_FILE" >&2)

echo -e "${BLUE}=== AI Trading Sentinel Security Hardening ===${NC}"
echo "Started at: $(date)"
echo "Log file: $LOG_FILE"
echo

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root${NC}"
   exit 1
fi

# Configuration variables
APP_USER="trading-sentinel"
APP_DIR="/opt/ai-trading-sentinel"
SSH_PORT="2222"
ALLOWED_USERS="ubuntu,$APP_USER"
FAIL2BAN_MAXRETRY="3"
FAIL2BAN_BANTIME="3600"

# Function to print status
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Update system packages
update_system() {
    print_info "Updating system packages..."
    apt-get update -y
    apt-get upgrade -y
    apt-get autoremove -y
    apt-get autoclean
    print_status "System updated"
}

# Configure SSH security
configure_ssh() {
    print_info "Configuring SSH security..."
    
    # Backup original SSH config
    cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup.$(date +%Y%m%d_%H%M%S)
    
    # SSH hardening configuration
    cat > /etc/ssh/sshd_config << EOF
# AI Trading Sentinel SSH Configuration
# Security hardened for production use

# Network
Port $SSH_PORT
AddressFamily inet
ListenAddress 0.0.0.0

# Authentication
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AuthenticationMethods publickey
MaxAuthTries 3
MaxSessions 2
MaxStartups 2

# User restrictions
AllowUsers $ALLOWED_USERS
DenyUsers root

# Protocol settings
Protocol 2
HostKey /etc/ssh/ssh_host_rsa_key
HostKey /etc/ssh/ssh_host_ecdsa_key
HostKey /etc/ssh/ssh_host_ed25519_key

# Encryption
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com,aes256-ctr,aes192-ctr,aes128-ctr
MACs hmac-sha2-256-etm@openssh.com,hmac-sha2-512-etm@openssh.com,hmac-sha2-256,hmac-sha2-512
KexAlgorithms curve25519-sha256@libssh.org,ecdh-sha2-nistp521,ecdh-sha2-nistp384,ecdh-sha2-nistp256,diffie-hellman-group16-sha512,diffie-hellman-group18-sha512,diffie-hellman-group14-sha256

# Timeouts
ClientAliveInterval 300
ClientAliveCountMax 2
LoginGraceTime 30

# Logging
SyslogFacility AUTHPRIV
LogLevel VERBOSE

# Features
X11Forwarding no
AllowTcpForwarding no
AllowAgentForwarding no
GatewayPorts no
PermitTunnel no
PermitUserEnvironment no
Compression no
UseDNS no
PrintMotd no
PrintLastLog yes
TCPKeepAlive yes
UsePrivilegeSeparation yes
StrictModes yes
IgnoreRhosts yes
HostbasedAuthentication no
PermitEmptyPasswords no
ChallengeResponseAuthentication no
KerberosAuthentication no
GSSAPIAuthentication no

# Subsystems
Subsystem sftp /usr/lib/openssh/sftp-server -l INFO
EOF

    # Test SSH configuration
    if sshd -t; then
        print_status "SSH configuration is valid"
        systemctl restart sshd
        print_status "SSH service restarted on port $SSH_PORT"
    else
        print_error "SSH configuration is invalid, restoring backup"
        cp /etc/ssh/sshd_config.backup.* /etc/ssh/sshd_config
        exit 1
    fi
}

# Setup SSH keys for application user
setup_ssh_keys() {
    print_info "Setting up SSH keys for $APP_USER..."
    
    if ! id "$APP_USER" &>/dev/null; then
        useradd -m -s /bin/bash "$APP_USER"
        usermod -aG sudo "$APP_USER"
        print_status "Created user: $APP_USER"
    fi
    
    # Create SSH directory
    sudo -u "$APP_USER" mkdir -p "/home/$APP_USER/.ssh"
    sudo -u "$APP_USER" chmod 700 "/home/$APP_USER/.ssh"
    
    # Generate SSH key pair if not exists
    if [[ ! -f "/home/$APP_USER/.ssh/id_rsa" ]]; then
        sudo -u "$APP_USER" ssh-keygen -t rsa -b 4096 -f "/home/$APP_USER/.ssh/id_rsa" -N ""
        print_status "Generated SSH key pair for $APP_USER"
    fi
    
    # Set proper permissions
    sudo -u "$APP_USER" chmod 600 "/home/$APP_USER/.ssh/id_rsa"
    sudo -u "$APP_USER" chmod 644 "/home/$APP_USER/.ssh/id_rsa.pub"
    
    print_warning "Public key for $APP_USER:"
    cat "/home/$APP_USER/.ssh/id_rsa.pub"
    echo
}

# Configure UFW firewall
configure_firewall() {
    print_info "Configuring UFW firewall..."
    
    # Install UFW if not present
    if ! command_exists ufw; then
        apt-get install -y ufw
    fi
    
    # Reset UFW to defaults
    ufw --force reset
    
    # Default policies
    ufw default deny incoming
    ufw default allow outgoing
    
    # SSH access
    ufw allow "$SSH_PORT"/tcp comment "SSH"
    
    # HTTP/HTTPS
    ufw allow 80/tcp comment "HTTP"
    ufw allow 443/tcp comment "HTTPS"
    
    # Application specific ports
    ufw allow 8000/tcp comment "API Server"
    ufw allow 3000/tcp comment "Frontend"
    
    # Monitoring ports (restrict to localhost)
    ufw allow from 127.0.0.1 to any port 9090 comment "Prometheus"
    ufw allow from 127.0.0.1 to any port 3001 comment "Grafana"
    ufw allow from 127.0.0.1 to any port 9100 comment "Node Exporter"
    
    # Database ports (localhost only)
    ufw allow from 127.0.0.1 to any port 5432 comment "PostgreSQL"
    ufw allow from 127.0.0.1 to any port 6379 comment "Redis"
    
    # Rate limiting for SSH
    ufw limit "$SSH_PORT"/tcp
    
    # Enable UFW
    ufw --force enable
    
    print_status "UFW firewall configured and enabled"
    ufw status verbose
}

# Install and configure Fail2Ban
setup_fail2ban() {
    print_info "Setting up Fail2Ban..."
    
    # Install Fail2Ban
    apt-get install -y fail2ban
    
    # Create custom jail configuration
    cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
# Ban settings
bantime = $FAIL2BAN_BANTIME
findtime = 600
maxretry = $FAIL2BAN_MAXRETRY

# Email notifications (configure if needed)
# destemail = admin@yourdomain.com
# sender = fail2ban@yourdomain.com
# action = %(action_mwl)s

# Ignore local IPs
ignoreip = 127.0.0.1/8 ::1 10.0.0.0/8 172.16.0.0/12 192.168.0.0/16

[sshd]
enabled = true
port = $SSH_PORT
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 3

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 5

[nginx-botsearch]
enabled = true
filter = nginx-botsearch
logpath = /var/log/nginx/access.log
maxretry = 2
bantime = 7200
EOF

    # Create custom filter for trading bot
    cat > /etc/fail2ban/filter.d/trading-sentinel.conf << EOF
[Definition]
failregex = ^.*\[.*\] .*Failed login attempt from <HOST>.*$
            ^.*\[.*\] .*Suspicious activity from <HOST>.*$
            ^.*\[.*\] .*Rate limit exceeded from <HOST>.*$
ignoreregex =
EOF

    # Add trading bot jail
    cat >> /etc/fail2ban/jail.local << EOF

[trading-sentinel]
enabled = true
filter = trading-sentinel
logpath = /var/log/ai-trading-sentinel/api.log
maxretry = 5
bantime = 1800
EOF

    # Start and enable Fail2Ban
    systemctl enable fail2ban
    systemctl restart fail2ban
    
    print_status "Fail2Ban configured and started"
}

# Secure kernel parameters
configure_kernel_security() {
    print_info "Configuring kernel security parameters..."
    
    cat > /etc/sysctl.d/99-security.conf << EOF
# AI Trading Sentinel Security Configuration

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

# ICMP security
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1

# SYN flood protection
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.tcp_synack_retries = 2
net.ipv4.tcp_syn_retries = 5

# IP spoofing protection
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# Log suspicious packets
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1

# Memory protection
kernel.dmesg_restrict = 1
kernel.kptr_restrict = 2
kernel.yama.ptrace_scope = 1

# Process security
fs.suid_dumpable = 0
kernel.core_uses_pid = 1

# Network tuning for performance
net.core.rmem_default = 262144
net.core.rmem_max = 16777216
net.core.wmem_default = 262144
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 65536 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.core.netdev_max_backlog = 5000
EOF

    # Apply sysctl settings
    sysctl -p /etc/sysctl.d/99-security.conf
    
    print_status "Kernel security parameters configured"
}

# Configure file permissions and ownership
secure_file_permissions() {
    print_info "Securing file permissions..."
    
    # Secure /tmp
    chmod 1777 /tmp
    
    # Secure application directory
    if [[ -d "$APP_DIR" ]]; then
        chown -R "$APP_USER:$APP_USER" "$APP_DIR"
        find "$APP_DIR" -type f -name "*.py" -exec chmod 644 {} \;
        find "$APP_DIR" -type f -name "*.sh" -exec chmod 755 {} \;
        find "$APP_DIR" -type d -exec chmod 755 {} \;
        
        # Secure sensitive files
        if [[ -f "$APP_DIR/.env" ]]; then
            chmod 600 "$APP_DIR/.env"
            chown "$APP_USER:$APP_USER" "$APP_DIR/.env"
        fi
    fi
    
    # Secure log directory
    mkdir -p /var/log/ai-trading-sentinel
    chown -R "$APP_USER:$APP_USER" /var/log/ai-trading-sentinel
    chmod 755 /var/log/ai-trading-sentinel
    
    print_status "File permissions secured"
}

# Setup automatic security updates
setup_auto_updates() {
    print_info "Setting up automatic security updates..."
    
    # Install unattended-upgrades
    apt-get install -y unattended-upgrades apt-listchanges
    
    # Configure automatic updates
    cat > /etc/apt/apt.conf.d/50unattended-upgrades << EOF
Unattended-Upgrade::Allowed-Origins {
    "\${distro_id}:\${distro_codename}-security";
    "\${distro_id}ESMApps:\${distro_codename}-apps-security";
    "\${distro_id}ESM:\${distro_codename}-infra-security";
};

Unattended-Upgrade::Package-Blacklist {
    // Add packages to blacklist if needed
};

Unattended-Upgrade::DevRelease "false";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Remove-New-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::Automatic-Reboot-Time "02:00";

// Email notifications
// Unattended-Upgrade::Mail "admin@yourdomain.com";
Unattended-Upgrade::MailOnlyOnError "true";
EOF

    # Enable automatic updates
    cat > /etc/apt/apt.conf.d/20auto-upgrades << EOF
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Download-Upgradeable-Packages "1";
APT::Periodic::AutocleanInterval "7";
APT::Periodic::Unattended-Upgrade "1";
EOF

    # Start and enable the service
    systemctl enable unattended-upgrades
    systemctl start unattended-upgrades
    
    print_status "Automatic security updates configured"
}

# Install and configure AIDE (Advanced Intrusion Detection Environment)
setup_aide() {
    print_info "Setting up AIDE for file integrity monitoring..."
    
    # Install AIDE
    apt-get install -y aide
    
    # Configure AIDE
    cat > /etc/aide/aide.conf << EOF
# AI Trading Sentinel AIDE Configuration

# Database locations
database=file:/var/lib/aide/aide.db
database_out=file:/var/lib/aide/aide.db.new

# Gzip the database
gzip_dbout=yes

# Report settings
report_url=file:/var/log/aide/aide.log
report_url=stdout

# Rules
Full = p+i+n+u+g+s+b+m+c+md5+sha1+sha256+rmd160+tiger+haval+gost+crc32
Dir = p+i+n+u+g
Lnk = p+i+n+u+g+l

# Directories to monitor
/boot Full
/bin Full
/sbin Full
/lib Full
/lib64 Full
/usr/bin Full
/usr/sbin Full
/usr/lib Full
/usr/local/bin Full
/etc Full
$APP_DIR Full
/var/log/ai-trading-sentinel Dir

# Exclude temporary and variable files
!/tmp
!/var/tmp
!/var/log/.*
!/var/run/.*
!/var/spool/.*
!/proc
!/sys
!/dev
EOF

    # Initialize AIDE database
    aideinit
    
    # Create daily check cron job
    cat > /etc/cron.daily/aide-check << EOF
#!/bin/bash
# Daily AIDE integrity check

/usr/bin/aide --check 2>&1 | /usr/bin/logger -t aide
EOF
    
    chmod +x /etc/cron.daily/aide-check
    
    print_status "AIDE file integrity monitoring configured"
}

# Setup log monitoring and rotation
setup_log_monitoring() {
    print_info "Setting up log monitoring and rotation..."
    
    # Configure logrotate for application logs
    cat > /etc/logrotate.d/ai-trading-sentinel << EOF
/var/log/ai-trading-sentinel/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $APP_USER $APP_USER
    postrotate
        systemctl reload ai-trading-sentinel || true
    endscript
}

/var/log/aide/*.log {
    weekly
    missingok
    rotate 12
    compress
    delaycompress
    notifempty
    create 644 root root
}
EOF

    # Setup rsyslog for centralized logging
    cat >> /etc/rsyslog.d/50-ai-trading-sentinel.conf << EOF
# AI Trading Sentinel logging
:programname, isequal, "trading-sentinel" /var/log/ai-trading-sentinel/syslog.log
& stop
:programname, isequal, "aide" /var/log/aide/aide.log
& stop
EOF

    systemctl restart rsyslog
    
    print_status "Log monitoring and rotation configured"
}

# Create security monitoring script
create_security_monitor() {
    print_info "Creating security monitoring script..."
    
    cat > /usr/local/bin/security-monitor.sh << 'EOF'
#!/bin/bash
# AI Trading Sentinel Security Monitor

LOG_FILE="/var/log/security-monitor.log"
ALERT_EMAIL="admin@yourdomain.com"  # Configure if needed

# Function to log with timestamp
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Check for failed SSH attempts
check_ssh_failures() {
    local failures=$(grep "Failed password" /var/log/auth.log | grep "$(date '+%b %d')" | wc -l)
    if [[ $failures -gt 10 ]]; then
        log_message "WARNING: $failures SSH login failures detected today"
    fi
}

# Check for unusual network connections
check_network_connections() {
    local suspicious_connections=$(netstat -tuln | grep -E ":(22|80|443|8000|3000)" | wc -l)
    if [[ $suspicious_connections -gt 20 ]]; then
        log_message "INFO: $suspicious_connections active network connections"
    fi
}

# Check system load
check_system_load() {
    local load=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    if (( $(echo "$load > 5.0" | bc -l) )); then
        log_message "WARNING: High system load detected: $load"
    fi
}

# Check disk usage
check_disk_usage() {
    local disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [[ $disk_usage -gt 90 ]]; then
        log_message "CRITICAL: Disk usage is $disk_usage%"
    fi
}

# Check for rootkit indicators
check_rootkit_indicators() {
    if command -v rkhunter >/dev/null 2>&1; then
        rkhunter --check --sk --nocolors 2>/dev/null | grep -i "warning\|infected" && \
            log_message "WARNING: Rootkit indicators detected"
    fi
}

# Main monitoring function
main() {
    log_message "Starting security monitoring check"
    
    check_ssh_failures
    check_network_connections
    check_system_load
    check_disk_usage
    check_rootkit_indicators
    
    log_message "Security monitoring check completed"
}

main
EOF

    chmod +x /usr/local/bin/security-monitor.sh
    
    # Add to cron for hourly execution
    echo "0 * * * * root /usr/local/bin/security-monitor.sh" >> /etc/crontab
    
    print_status "Security monitoring script created"
}

# Install additional security tools
install_security_tools() {
    print_info "Installing additional security tools..."
    
    # Install security packages
    apt-get install -y \
        rkhunter \
        chkrootkit \
        lynis \
        clamav \
        clamav-daemon \
        apparmor \
        apparmor-utils \
        auditd \
        acct
    
    # Update ClamAV database
    freshclam
    
    # Configure rkhunter
    rkhunter --update
    rkhunter --propupd
    
    # Enable AppArmor
    systemctl enable apparmor
    systemctl start apparmor
    
    # Enable audit daemon
    systemctl enable auditd
    systemctl start auditd
    
    print_status "Security tools installed and configured"
}

# Create security summary report
create_security_summary() {
    print_info "Creating security configuration summary..."
    
    cat > /root/security-summary.txt << EOF
=== AI Trading Sentinel Security Configuration Summary ===
Generated: $(date)

SSH Configuration:
- Port: $SSH_PORT
- Root login: Disabled
- Password authentication: Disabled
- Key-based authentication: Enabled
- Allowed users: $ALLOWED_USERS

Firewall (UFW):
- Status: $(ufw status | head -1)
- SSH port: $SSH_PORT/tcp
- HTTP: 80/tcp
- HTTPS: 443/tcp
- API: 8000/tcp
- Frontend: 3000/tcp

Fail2Ban:
- Status: $(systemctl is-active fail2ban)
- SSH jail: Enabled
- Max retry: $FAIL2BAN_MAXRETRY
- Ban time: $FAIL2BAN_BANTIME seconds

Security Tools:
- AIDE: File integrity monitoring
- RKHunter: Rootkit detection
- ClamAV: Antivirus
- AppArmor: Mandatory access control
- Auditd: System auditing

Automatic Updates:
- Security updates: Enabled
- Reboot: Manual (recommended)

Monitoring:
- Security monitor: /usr/local/bin/security-monitor.sh
- Log rotation: Configured
- AIDE checks: Daily

Important Files:
- SSH config: /etc/ssh/sshd_config
- UFW rules: /etc/ufw/
- Fail2Ban config: /etc/fail2ban/jail.local
- Security logs: /var/log/security-monitor.log
- AIDE config: /etc/aide/aide.conf

Next Steps:
1. Test SSH access with new port: ssh -p $SSH_PORT user@server
2. Configure email notifications for alerts
3. Review and customize security policies
4. Schedule regular security audits with Lynis
5. Monitor logs regularly

Security Checklist:
[ ] SSH key authentication working
[ ] Firewall rules tested
[ ] Fail2Ban monitoring active
[ ] Log rotation working
[ ] Security tools updated
[ ] Backup and recovery tested
[ ] SSL certificates configured
[ ] Application security reviewed
EOF

    print_status "Security summary created: /root/security-summary.txt"
}

# Main execution
main() {
    echo -e "${BLUE}Starting security hardening process...${NC}"
    echo
    
    # Execute hardening steps
    update_system
    configure_ssh
    setup_ssh_keys
    configure_firewall
    setup_fail2ban
    configure_kernel_security
    secure_file_permissions
    setup_auto_updates
    setup_aide
    setup_log_monitoring
    create_security_monitor
    install_security_tools
    create_security_summary
    
    echo
    echo -e "${GREEN}=== Security Hardening Complete ===${NC}"
    echo -e "${YELLOW}IMPORTANT NOTES:${NC}"
    echo -e "${YELLOW}1. SSH port changed to $SSH_PORT${NC}"
    echo -e "${YELLOW}2. Root login disabled${NC}"
    echo -e "${YELLOW}3. Password authentication disabled${NC}"
    echo -e "${YELLOW}4. Firewall enabled with restrictive rules${NC}"
    echo -e "${YELLOW}5. Review /root/security-summary.txt for details${NC}"
    echo
    echo -e "${RED}WARNING: Test SSH access before closing this session!${NC}"
    echo -e "${RED}New SSH command: ssh -p $SSH_PORT $APP_USER@$(hostname -I | awk '{print $1}')${NC}"
    echo
    
    print_status "Security hardening completed successfully"
    print_info "Log file: $LOG_FILE"
    print_info "Summary: /root/security-summary.txt"
}

# Run main function
main "$@"