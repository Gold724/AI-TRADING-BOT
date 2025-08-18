#!/bin/bash

# TradeBot Sentinel - Security Hardening Script
# This script implements comprehensive security measures for cloud deployment

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SSH_PORT=${SSH_PORT:-2222}
VPN_PORT=${VPN_PORT:-1194}
ALLOWED_IPS_FILE="/etc/tradebot/allowed_ips.txt"
SSH_KEY_DIR="/etc/tradebot/ssh-keys"
VPN_CONFIG_DIR="/etc/openvpn"
FAIL2BAN_CONFIG="/etc/fail2ban/jail.local"
UFW_RULES_FILE="/etc/tradebot/ufw-rules.sh"

# Logging
LOG_FILE="/var/log/tradebot-security.log"
exec 1> >(tee -a "$LOG_FILE")
exec 2> >(tee -a "$LOG_FILE" >&2)

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root"
    fi
}

# Update system packages
update_system() {
    log "Updating system packages..."
    apt-get update -y
    apt-get upgrade -y
    apt-get autoremove -y
    apt-get autoclean
}

# Install security packages
install_security_packages() {
    log "Installing security packages..."
    apt-get install -y \
        ufw \
        fail2ban \
        unattended-upgrades \
        apt-listchanges \
        logwatch \
        rkhunter \
        chkrootkit \
        aide \
        auditd \
        openssh-server \
        openvpn \
        easy-rsa \
        iptables-persistent \
        netfilter-persistent \
        psad \
        clamav \
        clamav-daemon \
        lynis \
        nmap \
        tcpdump \
        wireshark-common
}

# Configure SSH hardening
configure_ssh() {
    log "Configuring SSH hardening..."
    
    # Backup original SSH config
    cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup.$(date +%Y%m%d_%H%M%S)
    
    # Create SSH hardening config
    cat > /etc/ssh/sshd_config << EOF
# TradeBot Sentinel SSH Configuration
# Security hardened SSH configuration

# Network
Port $SSH_PORT
AddressFamily inet
ListenAddress 0.0.0.0

# Protocol
Protocol 2

# Host Keys
HostKey /etc/ssh/ssh_host_rsa_key
HostKey /etc/ssh/ssh_host_ecdsa_key
HostKey /etc/ssh/ssh_host_ed25519_key

# Ciphers and keying
RekeyLimit default none
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com,aes256-ctr,aes192-ctr,aes128-ctr
MACs hmac-sha2-256-etm@openssh.com,hmac-sha2-512-etm@openssh.com,hmac-sha2-256,hmac-sha2-512
KexAlgorithms curve25519-sha256@libssh.org,diffie-hellman-group16-sha512,diffie-hellman-group18-sha512,diffie-hellman-group14-sha256

# Logging
SyslogFacility AUTHPRIV
LogLevel VERBOSE

# Authentication
LoginGraceTime 30
PermitRootLogin no
StrictModes yes
MaxAuthTries 3
MaxSessions 2
MaxStartups 2

# Public key authentication
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys

# Password authentication (disabled)
PasswordAuthentication no
PermitEmptyPasswords no
ChallengeResponseAuthentication no

# Kerberos options
KerberosAuthentication no
KerberosOrLocalPasswd no
KerberosTicketCleanup yes

# GSSAPI options
GSSAPIAuthentication no
GSSAPICleanupCredentials yes

# Disable unused authentication methods
UsePAM yes
X11Forwarding no
X11DisplayOffset 10
PrintMotd no
PrintLastLog yes
TCPKeepAlive yes
Compression delayed
ClientAliveInterval 300
ClientAliveCountMax 2
UseDNS no
PidFile /var/run/sshd.pid
MaxStartups 2
Banner /etc/ssh/banner

# Allow only specific users
AllowUsers tradebot
DenyUsers root

# Subsystem
Subsystem sftp /usr/lib/openssh/sftp-server -f AUTHPRIV -l INFO
EOF

    # Create SSH banner
    cat > /etc/ssh/banner << EOF
***************************************************************************
                    AUTHORIZED ACCESS ONLY
                   TradeBot Sentinel System
***************************************************************************

This system is for authorized users only. All activities are monitored
and logged. Unauthorized access is strictly prohibited and will be
prosecuted to the full extent of the law.

***************************************************************************
EOF

    # Create SSH key directory
    mkdir -p "$SSH_KEY_DIR"
    chmod 700 "$SSH_KEY_DIR"
    
    # Generate new SSH host keys
    ssh-keygen -A
    
    # Set proper permissions
    chmod 600 /etc/ssh/ssh_host_*_key
    chmod 644 /etc/ssh/ssh_host_*_key.pub
    
    # Restart SSH service
    systemctl restart sshd
    systemctl enable sshd
    
    log "SSH hardening completed. New SSH port: $SSH_PORT"
}

# Configure UFW firewall
configure_firewall() {
    log "Configuring UFW firewall..."
    
    # Reset UFW to defaults
    ufw --force reset
    
    # Set default policies
    ufw default deny incoming
    ufw default allow outgoing
    
    # Allow SSH on custom port
    ufw allow $SSH_PORT/tcp comment 'SSH'
    
    # Allow HTTP/HTTPS for web interface
    ufw allow 80/tcp comment 'HTTP'
    ufw allow 443/tcp comment 'HTTPS'
    
    # Allow monitoring ports (restrict to specific IPs later)
    ufw allow 3000/tcp comment 'Grafana'
    ufw allow 9090/tcp comment 'Prometheus'
    ufw allow 9093/tcp comment 'Alertmanager'
    ufw allow 3100/tcp comment 'Loki'
    
    # Allow VPN
    ufw allow $VPN_PORT/udp comment 'OpenVPN'
    
    # Allow Docker network
    ufw allow from 172.16.0.0/12
    ufw allow from 10.0.0.0/8
    
    # Rate limiting for SSH
    ufw limit $SSH_PORT/tcp
    
    # Enable UFW
    ufw --force enable
    
    # Create UFW rules script for easy management
    cat > "$UFW_RULES_FILE" << 'EOF'
#!/bin/bash
# TradeBot Sentinel UFW Rules Management

case "$1" in
    "allow-ip")
        if [[ -n "$2" ]]; then
            ufw allow from "$2" comment "Allowed IP: $2"
            echo "$2" >> /etc/tradebot/allowed_ips.txt
            echo "Added IP: $2"
        else
            echo "Usage: $0 allow-ip <IP_ADDRESS>"
        fi
        ;;
    "deny-ip")
        if [[ -n "$2" ]]; then
            ufw deny from "$2"
            sed -i "/^$2$/d" /etc/tradebot/allowed_ips.txt
            echo "Denied IP: $2"
        else
            echo "Usage: $0 deny-ip <IP_ADDRESS>"
        fi
        ;;
    "list")
        ufw status numbered
        ;;
    "reset")
        ufw --force reset
        echo "Firewall rules reset"
        ;;
    *)
        echo "Usage: $0 {allow-ip|deny-ip|list|reset} [IP_ADDRESS]"
        exit 1
        ;;
esac
EOF
    
    chmod +x "$UFW_RULES_FILE"
    
    log "UFW firewall configured successfully"
}

# Configure Fail2Ban
configure_fail2ban() {
    log "Configuring Fail2Ban..."
    
    cat > "$FAIL2BAN_CONFIG" << EOF
[DEFAULT]
# Ban settings
bantime = 3600
findtime = 600
maxretry = 3
backend = systemd

# Email settings
destemail = admin@tradebot-sentinel.com
sender = fail2ban@tradebot-sentinel.com
mta = sendmail
action = %(action_mwl)s

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
bantime = 3600

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 5
bantime = 3600

[tradebot-auth]
enabled = true
filter = tradebot-auth
logpath = /var/log/tradebot/auth.log
maxretry = 3
bantime = 7200

[docker-auth]
enabled = true
filter = docker-auth
logpath = /var/log/docker/auth.log
maxretry = 3
bantime = 3600
EOF

    # Create custom filters
    mkdir -p /etc/fail2ban/filter.d
    
    # TradeBot authentication filter
    cat > /etc/fail2ban/filter.d/tradebot-auth.conf << 'EOF'
[Definition]
failregex = ^.*Authentication failed for user .* from <HOST>.*$
            ^.*Invalid login attempt from <HOST>.*$
            ^.*Brute force attempt detected from <HOST>.*$
ignoreregex =
EOF

    # Docker authentication filter
    cat > /etc/fail2ban/filter.d/docker-auth.conf << 'EOF'
[Definition]
failregex = ^.*Authentication failed.*from <HOST>.*$
            ^.*Invalid credentials.*from <HOST>.*$
ignoreregex =
EOF

    # Start and enable Fail2Ban
    systemctl restart fail2ban
    systemctl enable fail2ban
    
    log "Fail2Ban configured successfully"
}

# Setup OpenVPN server
setup_openvpn() {
    log "Setting up OpenVPN server..."
    
    # Create OpenVPN directory structure
    mkdir -p "$VPN_CONFIG_DIR/server"
    mkdir -p "$VPN_CONFIG_DIR/client"
    mkdir -p "/etc/tradebot/vpn-clients"
    
    # Initialize PKI
    cd /etc/openvpn
    make-cadir easy-rsa
    cd easy-rsa
    
    # Configure PKI variables
    cat > vars << EOF
set_var EASYRSA_REQ_COUNTRY    "US"
set_var EASYRSA_REQ_PROVINCE   "CA"
set_var EASYRSA_REQ_CITY       "San Francisco"
set_var EASYRSA_REQ_ORG        "TradeBot Sentinel"
set_var EASYRSA_REQ_EMAIL      "admin@tradebot-sentinel.com"
set_var EASYRSA_REQ_OU         "IT Department"
set_var EASYRSA_KEY_SIZE       2048
set_var EASYRSA_ALGO           rsa
set_var EASYRSA_CA_EXPIRE      3650
set_var EASYRSA_CERT_EXPIRE    365
EOF

    # Initialize PKI and build CA
    ./easyrsa init-pki
    ./easyrsa --batch build-ca nopass
    
    # Generate server certificate and key
    ./easyrsa --batch build-server-full server nopass
    
    # Generate Diffie-Hellman parameters
    ./easyrsa gen-dh
    
    # Generate TLS-auth key
    openvpn --genkey --secret pki/ta.key
    
    # Copy certificates to OpenVPN directory
    cp pki/ca.crt "$VPN_CONFIG_DIR/server/"
    cp pki/issued/server.crt "$VPN_CONFIG_DIR/server/"
    cp pki/private/server.key "$VPN_CONFIG_DIR/server/"
    cp pki/dh.pem "$VPN_CONFIG_DIR/server/"
    cp pki/ta.key "$VPN_CONFIG_DIR/server/"
    
    # Create OpenVPN server configuration
    cat > "$VPN_CONFIG_DIR/server.conf" << EOF
# TradeBot Sentinel OpenVPN Server Configuration

# Network settings
port $VPN_PORT
proto udp
dev tun

# Certificates and keys
ca /etc/openvpn/server/ca.crt
cert /etc/openvpn/server/server.crt
key /etc/openvpn/server/server.key
dh /etc/openvpn/server/dh.pem
tls-auth /etc/openvpn/server/ta.key 0

# Network configuration
server 10.8.0.0 255.255.255.0
ifconfig-pool-persist /var/log/openvpn/ipp.txt

# Push routes to clients
push "redirect-gateway def1 bypass-dhcp"
push "dhcp-option DNS 8.8.8.8"
push "dhcp-option DNS 8.8.4.4"

# Client configuration
client-to-client
duplicate-cn
keepalive 10 120

# Security settings
cipher AES-256-CBC
auth SHA256
tls-version-min 1.2
tls-cipher TLS-ECDHE-RSA-WITH-AES-256-GCM-SHA384:TLS-ECDHE-ECDSA-WITH-AES-256-GCM-SHA384

# Logging
status /var/log/openvpn/openvpn-status.log
log-append /var/log/openvpn/openvpn.log
verb 3
mute 20

# Performance
fast-io
sndbuf 0
rcvbuf 0

# User and group
user nobody
group nogroup

# Persistence
persist-key
persist-tun
EOF

    # Create log directory
    mkdir -p /var/log/openvpn
    
    # Enable IP forwarding
    echo 'net.ipv4.ip_forward=1' >> /etc/sysctl.conf
    sysctl -p
    
    # Configure iptables for VPN
    iptables -t nat -A POSTROUTING -s 10.8.0.0/24 -o eth0 -j MASQUERADE
    iptables -A INPUT -i tun+ -j ACCEPT
    iptables -A FORWARD -i tun+ -j ACCEPT
    iptables -A FORWARD -i tun+ -o eth0 -m state --state RELATED,ESTABLISHED -j ACCEPT
    iptables -A FORWARD -i eth0 -o tun+ -m state --state RELATED,ESTABLISHED -j ACCEPT
    
    # Save iptables rules
    iptables-save > /etc/iptables/rules.v4
    
    # Start and enable OpenVPN
    systemctl start openvpn@server
    systemctl enable openvpn@server
    
    log "OpenVPN server configured successfully"
}

# Create VPN client configuration
create_vpn_client() {
    local client_name="$1"
    
    if [[ -z "$client_name" ]]; then
        error "Client name is required"
    fi
    
    log "Creating VPN client configuration for: $client_name"
    
    cd /etc/openvpn/easy-rsa
    
    # Generate client certificate
    ./easyrsa --batch build-client-full "$client_name" nopass
    
    # Create client configuration
    cat > "/etc/tradebot/vpn-clients/$client_name.ovpn" << EOF
client
dev tun
proto udp
remote $(curl -s ifconfig.me) $VPN_PORT
resolv-retry infinite
nobind
persist-key
persist-tun
remote-cert-tls server
cipher AES-256-CBC
auth SHA256
verb 3
mute 20

<ca>
$(cat pki/ca.crt)
</ca>

<cert>
$(cat pki/issued/$client_name.crt)
</cert>

<key>
$(cat pki/private/$client_name.key)
</key>

<tls-auth>
$(cat pki/ta.key)
</tls-auth>
key-direction 1
EOF

    log "Client configuration created: /etc/tradebot/vpn-clients/$client_name.ovpn"
}

# Configure automatic security updates
configure_auto_updates() {
    log "Configuring automatic security updates..."
    
    # Configure unattended-upgrades
    cat > /etc/apt/apt.conf.d/50unattended-upgrades << 'EOF'
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}";
    "${distro_id}:${distro_codename}-security";
    "${distro_id}ESMApps:${distro_codename}-apps-security";
    "${distro_id}ESM:${distro_codename}-infra-security";
};

Unattended-Upgrade::Package-Blacklist {
    "docker-ce";
    "docker-ce-cli";
    "containerd.io";
    "kubernetes*";
};

Unattended-Upgrade::DevRelease "false";
Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";
Unattended-Upgrade::Remove-New-Unused-Dependencies "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::Automatic-Reboot-WithUsers "false";
Unattended-Upgrade::Automatic-Reboot-Time "02:00";
Unattended-Upgrade::SyslogEnable "true";
Unattended-Upgrade::SyslogFacility "daemon";
Unattended-Upgrade::Verbose "true";
EOF

    # Enable automatic updates
    cat > /etc/apt/apt.conf.d/20auto-upgrades << 'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Download-Upgradeable-Packages "1";
APT::Periodic::AutocleanInterval "7";
APT::Periodic::Unattended-Upgrade "1";
EOF

    # Configure logwatch
    sed -i 's/^Output = stdout/Output = mail/' /etc/logwatch/conf/logwatch.conf
    sed -i 's/^Format = text/Format = html/' /etc/logwatch/conf/logwatch.conf
    sed -i 's/^MailTo = root/MailTo = admin@tradebot-sentinel.com/' /etc/logwatch/conf/logwatch.conf
    
    log "Automatic security updates configured"
}

# Configure system auditing
configure_auditing() {
    log "Configuring system auditing..."
    
    # Configure auditd rules
    cat > /etc/audit/rules.d/tradebot.rules << 'EOF'
# TradeBot Sentinel Audit Rules

# Delete all existing rules
-D

# Buffer size
-b 8192

# Failure mode (0=silent, 1=printk, 2=panic)
-f 1

# Monitor authentication events
-w /etc/passwd -p wa -k identity
-w /etc/group -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/sudoers -p wa -k identity

# Monitor SSH configuration
-w /etc/ssh/sshd_config -p wa -k ssh_config
-w /etc/ssh/ -p wa -k ssh_config

# Monitor system configuration
-w /etc/hosts -p wa -k network_config
-w /etc/network/ -p wa -k network_config
-w /etc/iptables/ -p wa -k network_config

# Monitor TradeBot files
-w /opt/tradebot/ -p wa -k tradebot_files
-w /etc/tradebot/ -p wa -k tradebot_config
-w /var/log/tradebot/ -p wa -k tradebot_logs

# Monitor Docker
-w /var/lib/docker/ -p wa -k docker
-w /etc/docker/ -p wa -k docker

# Monitor system calls
-a always,exit -F arch=b64 -S execve -k exec
-a always,exit -F arch=b32 -S execve -k exec

# Monitor file access
-a always,exit -F arch=b64 -S open -S openat -S creat -k file_access
-a always,exit -F arch=b32 -S open -S openat -S creat -k file_access

# Monitor network connections
-a always,exit -F arch=b64 -S socket -S connect -S accept -k network
-a always,exit -F arch=b32 -S socket -S connect -S accept -k network

# Make rules immutable
-e 2
EOF

    # Restart auditd
    systemctl restart auditd
    systemctl enable auditd
    
    log "System auditing configured"
}

# Configure intrusion detection
configure_intrusion_detection() {
    log "Configuring intrusion detection..."
    
    # Configure AIDE (Advanced Intrusion Detection Environment)
    aide --init
    mv /var/lib/aide/aide.db.new /var/lib/aide/aide.db
    
    # Create AIDE check script
    cat > /etc/cron.daily/aide-check << 'EOF'
#!/bin/bash
# AIDE integrity check

AIDE_LOG="/var/log/aide/aide.log"
mkdir -p "$(dirname "$AIDE_LOG")"

# Run AIDE check
aide --check > "$AIDE_LOG" 2>&1

# Check for changes
if [ $? -ne 0 ]; then
    # Send alert email
    mail -s "AIDE Integrity Check Alert - $(hostname)" admin@tradebot-sentinel.com < "$AIDE_LOG"
fi

# Rotate logs
find /var/log/aide/ -name "*.log" -mtime +30 -delete
EOF

    chmod +x /etc/cron.daily/aide-check
    
    # Configure rkhunter
    rkhunter --update
    rkhunter --propupd
    
    # Create rkhunter check script
    cat > /etc/cron.daily/rkhunter-check << 'EOF'
#!/bin/bash
# Rootkit Hunter check

RKH_LOG="/var/log/rkhunter/rkhunter.log"
mkdir -p "$(dirname "$RKH_LOG")"

# Run rkhunter check
rkhunter --check --skip-keypress --report-warnings-only > "$RKH_LOG" 2>&1

# Check for warnings
if [ -s "$RKH_LOG" ]; then
    # Send alert email
    mail -s "Rootkit Hunter Alert - $(hostname)" admin@tradebot-sentinel.com < "$RKH_LOG"
fi

# Update rkhunter database
rkhunter --update
EOF

    chmod +x /etc/cron.daily/rkhunter-check
    
    # Configure ClamAV
    freshclam
    
    # Create ClamAV scan script
    cat > /etc/cron.daily/clamav-scan << 'EOF'
#!/bin/bash
# ClamAV virus scan

CLAM_LOG="/var/log/clamav/scan.log"
mkdir -p "$(dirname "$CLAM_LOG")"

# Update virus definitions
freshclam --quiet

# Scan important directories
clamscan -r --bell -i /opt/tradebot/ /etc/tradebot/ /home/ --log="$CLAM_LOG"

# Check for infections
if grep -q "FOUND" "$CLAM_LOG"; then
    # Send alert email
    mail -s "ClamAV Virus Detection Alert - $(hostname)" admin@tradebot-sentinel.com < "$CLAM_LOG"
fi
EOF

    chmod +x /etc/cron.daily/clamav-scan
    
    log "Intrusion detection configured"
}

# Create security monitoring script
create_security_monitor() {
    log "Creating security monitoring script..."
    
    cat > /usr/local/bin/tradebot-security-monitor << 'EOF'
#!/bin/bash
# TradeBot Sentinel Security Monitor

SECURITY_LOG="/var/log/tradebot/security-monitor.log"
ALERT_EMAIL="admin@tradebot-sentinel.com"

# Create log directory
mkdir -p "$(dirname "$SECURITY_LOG")"

# Function to log and alert
log_alert() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo "[$timestamp] [$level] $message" >> "$SECURITY_LOG"
    
    if [[ "$level" == "CRITICAL" ]]; then
        echo "$message" | mail -s "CRITICAL Security Alert - $(hostname)" "$ALERT_EMAIL"
    fi
}

# Check for failed login attempts
check_failed_logins() {
    local failed_count=$(grep "Failed password" /var/log/auth.log | grep "$(date '+%b %d')" | wc -l)
    
    if [[ $failed_count -gt 10 ]]; then
        log_alert "WARNING" "High number of failed login attempts: $failed_count"
    fi
}

# Check for root login attempts
check_root_logins() {
    local root_attempts=$(grep "root" /var/log/auth.log | grep "$(date '+%b %d')" | wc -l)
    
    if [[ $root_attempts -gt 0 ]]; then
        log_alert "CRITICAL" "Root login attempts detected: $root_attempts"
    fi
}

# Check disk usage
check_disk_usage() {
    local usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [[ $usage -gt 90 ]]; then
        log_alert "CRITICAL" "Disk usage critical: ${usage}%"
    elif [[ $usage -gt 80 ]]; then
        log_alert "WARNING" "Disk usage high: ${usage}%"
    fi
}

# Check memory usage
check_memory_usage() {
    local mem_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    
    if [[ $mem_usage -gt 90 ]]; then
        log_alert "CRITICAL" "Memory usage critical: ${mem_usage}%"
    elif [[ $mem_usage -gt 80 ]]; then
        log_alert "WARNING" "Memory usage high: ${mem_usage}%"
    fi
}

# Check for suspicious processes
check_suspicious_processes() {
    local suspicious_procs=$(ps aux | grep -E "(nc|netcat|nmap|tcpdump|wireshark)" | grep -v grep | wc -l)
    
    if [[ $suspicious_procs -gt 0 ]]; then
        log_alert "WARNING" "Suspicious processes detected: $suspicious_procs"
    fi
}

# Check network connections
check_network_connections() {
    local external_conns=$(netstat -an | grep ESTABLISHED | grep -v "127.0.0.1\|10.\|172.\|192.168." | wc -l)
    
    if [[ $external_conns -gt 50 ]]; then
        log_alert "WARNING" "High number of external connections: $external_conns"
    fi
}

# Check TradeBot service status
check_tradebot_status() {
    if ! systemctl is-active --quiet tradebot; then
        log_alert "CRITICAL" "TradeBot service is not running"
    fi
}

# Main monitoring loop
main() {
    log_alert "INFO" "Security monitor started"
    
    check_failed_logins
    check_root_logins
    check_disk_usage
    check_memory_usage
    check_suspicious_processes
    check_network_connections
    check_tradebot_status
    
    log_alert "INFO" "Security monitor completed"
}

# Run main function
main
EOF

    chmod +x /usr/local/bin/tradebot-security-monitor
    
    # Create systemd timer for security monitoring
    cat > /etc/systemd/system/tradebot-security-monitor.service << 'EOF'
[Unit]
Description=TradeBot Security Monitor
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/tradebot-security-monitor
User=root
Group=root
EOF

    cat > /etc/systemd/system/tradebot-security-monitor.timer << 'EOF'
[Unit]
Description=Run TradeBot Security Monitor every 5 minutes
Requires=tradebot-security-monitor.service

[Timer]
OnCalendar=*:0/5
Persistent=true

[Install]
WantedBy=timers.target
EOF

    systemctl daemon-reload
    systemctl enable tradebot-security-monitor.timer
    systemctl start tradebot-security-monitor.timer
    
    log "Security monitoring configured"
}

# Create security management script
create_security_management() {
    log "Creating security management script..."
    
    cat > /usr/local/bin/tradebot-security << 'EOF'
#!/bin/bash
# TradeBot Sentinel Security Management Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/var/log/tradebot/security-management.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}" | tee -a "$LOG_FILE"
}

# Show security status
show_status() {
    echo "=== TradeBot Sentinel Security Status ==="
    echo
    
    # Firewall status
    echo "Firewall Status:"
    ufw status | head -10
    echo
    
    # Fail2Ban status
    echo "Fail2Ban Status:"
    fail2ban-client status
    echo
    
    # SSH status
    echo "SSH Status:"
    systemctl status sshd --no-pager -l
    echo
    
    # VPN status
    echo "OpenVPN Status:"
    systemctl status openvpn@server --no-pager -l
    echo
    
    # Security services
    echo "Security Services:"
    systemctl is-active auditd fail2ban ufw openvpn@server
    echo
    
    # Recent security events
    echo "Recent Security Events (last 24 hours):"
    grep "$(date -d '1 day ago' '+%b %d')\|$(date '+%b %d')" /var/log/tradebot/security-monitor.log | tail -10
}

# Add allowed IP
add_allowed_ip() {
    local ip="$1"
    
    if [[ -z "$ip" ]]; then
        error "IP address is required"
        return 1
    fi
    
    # Validate IP format
    if ! [[ "$ip" =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        error "Invalid IP address format: $ip"
        return 1
    fi
    
    # Add to UFW
    ufw allow from "$ip" comment "Allowed IP: $ip"
    
    # Add to allowed IPs file
    echo "$ip" >> /etc/tradebot/allowed_ips.txt
    
    log "Added allowed IP: $ip"
}

# Remove allowed IP
remove_allowed_ip() {
    local ip="$1"
    
    if [[ -z "$ip" ]]; then
        error "IP address is required"
        return 1
    fi
    
    # Remove from UFW
    ufw delete allow from "$ip"
    
    # Remove from allowed IPs file
    sed -i "/^$ip$/d" /etc/tradebot/allowed_ips.txt
    
    log "Removed allowed IP: $ip"
}

# Create VPN client
create_vpn_client() {
    local client_name="$1"
    
    if [[ -z "$client_name" ]]; then
        error "Client name is required"
        return 1
    fi
    
    # Check if client already exists
    if [[ -f "/etc/tradebot/vpn-clients/$client_name.ovpn" ]]; then
        error "Client $client_name already exists"
        return 1
    fi
    
    # Generate client certificate and configuration
    cd /etc/openvpn/easy-rsa
    ./easyrsa --batch build-client-full "$client_name" nopass
    
    # Create client configuration
    cat > "/etc/tradebot/vpn-clients/$client_name.ovpn" << EOF
client
dev tun
proto udp
remote $(curl -s ifconfig.me) 1194
resolv-retry infinite
nobind
persist-key
persist-tun
remote-cert-tls server
cipher AES-256-CBC
auth SHA256
verb 3
mute 20

<ca>
$(cat pki/ca.crt)
</ca>

<cert>
$(cat pki/issued/$client_name.crt)
</cert>

<key>
$(cat pki/private/$client_name.key)
</key>

<tls-auth>
$(cat pki/ta.key)
</tls-auth>
key-direction 1
EOF

    log "VPN client configuration created: /etc/tradebot/vpn-clients/$client_name.ovpn"
}

# Revoke VPN client
revoke_vpn_client() {
    local client_name="$1"
    
    if [[ -z "$client_name" ]]; then
        error "Client name is required"
        return 1
    fi
    
    # Revoke certificate
    cd /etc/openvpn/easy-rsa
    ./easyrsa --batch revoke "$client_name"
    ./easyrsa gen-crl
    
    # Copy CRL to OpenVPN directory
    cp pki/crl.pem /etc/openvpn/server/
    
    # Remove client configuration
    rm -f "/etc/tradebot/vpn-clients/$client_name.ovpn"
    
    # Restart OpenVPN to load new CRL
    systemctl restart openvpn@server
    
    log "VPN client revoked: $client_name"
}

# Run security scan
run_security_scan() {
    log "Running security scan..."
    
    # Run Lynis security audit
    lynis audit system --quick
    
    # Run rkhunter
    rkhunter --check --skip-keypress --report-warnings-only
    
    # Run ClamAV scan
    clamscan -r --bell -i /opt/tradebot/ /etc/tradebot/
    
    log "Security scan completed"
}

# Show help
show_help() {
    echo "TradeBot Sentinel Security Management"
    echo
    echo "Usage: $0 <command> [options]"
    echo
    echo "Commands:"
    echo "  status                    Show security status"
    echo "  allow-ip <ip>            Add allowed IP address"
    echo "  deny-ip <ip>             Remove allowed IP address"
    echo "  create-vpn <name>        Create VPN client configuration"
    echo "  revoke-vpn <name>        Revoke VPN client certificate"
    echo "  scan                     Run security scan"
    echo "  help                     Show this help message"
    echo
}

# Main function
main() {
    case "$1" in
        "status")
            show_status
            ;;
        "allow-ip")
            add_allowed_ip "$2"
            ;;
        "deny-ip")
            remove_allowed_ip "$2"
            ;;
        "create-vpn")
            create_vpn_client "$2"
            ;;
        "revoke-vpn")
            revoke_vpn_client "$2"
            ;;
        "scan")
            run_security_scan
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
EOF

    chmod +x /usr/local/bin/tradebot-security
    
    log "Security management script created"
}

# Main execution
main() {
    log "Starting TradeBot Sentinel security hardening..."
    
    check_root
    
    # Create necessary directories
    mkdir -p /etc/tradebot
    mkdir -p /var/log/tradebot
    mkdir -p /opt/tradebot
    
    # Run security hardening steps
    update_system
    install_security_packages
    configure_ssh
    configure_firewall
    configure_fail2ban
    setup_openvpn
    configure_auto_updates
    configure_auditing
    configure_intrusion_detection
    create_security_monitor
    create_security_management
    
    # Create initial VPN client for admin
    create_vpn_client "admin"
    
    log "Security hardening completed successfully!"
    log "SSH port changed to: $SSH_PORT"
    log "VPN port: $VPN_PORT"
    log "Admin VPN config: /etc/tradebot/vpn-clients/admin.ovpn"
    log "Security management: /usr/local/bin/tradebot-security"
    
    warn "IMPORTANT: Make sure to:"
    warn "1. Download the admin VPN configuration before disconnecting"
    warn "2. Test SSH access on port $SSH_PORT before closing this session"
    warn "3. Configure your email settings for security alerts"
    warn "4. Review and customize firewall rules as needed"
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi