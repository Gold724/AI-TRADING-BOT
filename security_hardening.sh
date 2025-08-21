#!/bin/bash

# AI Trading Sentinel - Security Hardening Script
# This script implements comprehensive security measures for production deployment

set -e

echo "🔒 AI Trading Sentinel - Security Hardening"
echo "==========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}This script should not be run as root for security reasons${NC}"
   echo "Please run as a regular user with sudo privileges"
   exit 1
fi

echo -e "${YELLOW}Starting security hardening process...${NC}"

# 1. Update system packages
echo -e "${YELLOW}[1/10] Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y

# 2. Install security tools
echo -e "${YELLOW}[2/10] Installing security tools...${NC}"
sudo apt install -y ufw fail2ban unattended-upgrades apt-listchanges
sudo apt install -y rkhunter chkrootkit lynis
sudo apt install -y logwatch logrotate

# 3. Configure UFW Firewall
echo -e "${YELLOW}[3/10] Configuring UFW firewall...${NC}"
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (custom port if configured)
SSH_PORT=$(grep -E '^Port' /etc/ssh/sshd_config | awk '{print $2}' || echo "22")
sudo ufw allow $SSH_PORT/tcp comment 'SSH'

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp comment 'HTTP'
sudo ufw allow 443/tcp comment 'HTTPS'

# Allow Flask API (only from localhost)
sudo ufw allow from 127.0.0.1 to any port 5000 comment 'Flask API Local'

# Enable firewall
sudo ufw --force enable
echo -e "${GREEN}✓ Firewall configured${NC}"

# 4. Configure Fail2Ban
echo -e "${YELLOW}[4/10] Configuring Fail2Ban...${NC}"
sudo tee /etc/fail2ban/jail.local > /dev/null << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
ignoreip = 127.0.0.1/8 ::1

[sshd]
enabled = true
port = ssh
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

[nginx-noscript]
enabled = true
port = http,https
filter = nginx-noscript
logpath = /var/log/nginx/access.log
maxretry = 6
bantime = 3600

[nginx-badbots]
enabled = true
port = http,https
filter = nginx-badbots
logpath = /var/log/nginx/access.log
maxretry = 2
bantime = 86400
EOF

sudo systemctl enable fail2ban
sudo systemctl restart fail2ban
echo -e "${GREEN}✓ Fail2Ban configured${NC}"

# 5. SSH Hardening
echo -e "${YELLOW}[5/10] Hardening SSH configuration...${NC}"
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup

# Create hardened SSH config
sudo tee /etc/ssh/sshd_config > /dev/null << 'EOF'
# AI Trading Sentinel - Hardened SSH Configuration

# Network
Port 2222
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

# Security
Protocol 2
HostKey /etc/ssh/ssh_host_rsa_key
HostKey /etc/ssh/ssh_host_ecdsa_key
HostKey /etc/ssh/ssh_host_ed25519_key

# Ciphers and algorithms
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com,aes256-ctr,aes192-ctr,aes128-ctr
MACs hmac-sha2-256-etm@openssh.com,hmac-sha2-512-etm@openssh.com,hmac-sha2-256,hmac-sha2-512
KexAlgorithms curve25519-sha256@libssh.org,ecdh-sha2-nistp521,ecdh-sha2-nistp384,ecdh-sha2-nistp256,diffie-hellman-group16-sha512,diffie-hellman-group18-sha512,diffie-hellman-group14-sha256

# Timeouts
ClientAliveInterval 300
ClientAliveCountMax 2
LoginGraceTime 60

# Misc
UseDNS no
X11Forwarding no
AllowTcpForwarding no
GatewayPorts no
PermitTunnel no
Compression no
TCPKeepAlive yes

# Logging
SyslogFacility AUTH
LogLevel VERBOSE

# User restrictions
AllowUsers aitrading
DenyUsers root
EOF

# Test SSH config and restart
sudo sshd -t
if [ $? -eq 0 ]; then
    sudo systemctl restart sshd
    echo -e "${GREEN}✓ SSH hardened (new port: 2222)${NC}"
    echo -e "${YELLOW}⚠️  Remember to update UFW and reconnect using port 2222${NC}"
else
    echo -e "${RED}✗ SSH config test failed, restoring backup${NC}"
    sudo cp /etc/ssh/sshd_config.backup /etc/ssh/sshd_config
    sudo systemctl restart sshd
fi

# 6. Configure automatic security updates
echo -e "${YELLOW}[6/10] Configuring automatic security updates...${NC}"
sudo tee /etc/apt/apt.conf.d/50unattended-upgrades > /dev/null << 'EOF'
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}";
    "${distro_id}:${distro_codename}-security";
    "${distro_id}ESMApps:${distro_codename}-apps-security";
    "${distro_id}ESM:${distro_codename}-infra-security";
};

Unattended-Upgrade::Package-Blacklist {
};

Unattended-Upgrade::DevRelease "false";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::Automatic-Reboot-Time "02:00";
EOF

sudo tee /etc/apt/apt.conf.d/20auto-upgrades > /dev/null << 'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
EOF

echo -e "${GREEN}✓ Automatic security updates configured${NC}"

# 7. Set up log rotation
echo -e "${YELLOW}[7/10] Configuring log rotation...${NC}"
sudo tee /etc/logrotate.d/aitrading > /dev/null << 'EOF'
/home/aitrading/ai-trading-sentinel/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 aitrading aitrading
    postrotate
        systemctl reload aitrading-backend aitrading-bot 2>/dev/null || true
    endscript
}

/var/log/nginx/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload nginx 2>/dev/null || true
    endscript
}
EOF

echo -e "${GREEN}✓ Log rotation configured${NC}"

# 8. File permissions and ownership
echo -e "${YELLOW}[8/10] Setting secure file permissions...${NC}"

# AI Trading Sentinel directory
if [ -d "/home/aitrading/ai-trading-sentinel" ]; then
    sudo chown -R aitrading:aitrading /home/aitrading/ai-trading-sentinel
    sudo chmod -R 755 /home/aitrading/ai-trading-sentinel
    
    # Secure .env file
    if [ -f "/home/aitrading/ai-trading-sentinel/.env" ]; then
        sudo chmod 600 /home/aitrading/ai-trading-sentinel/.env
    fi
    
    # Secure log directory
    if [ -d "/home/aitrading/ai-trading-sentinel/logs" ]; then
        sudo chmod 755 /home/aitrading/ai-trading-sentinel/logs
    fi
fi

echo -e "${GREEN}✓ File permissions secured${NC}"

# 9. System hardening
echo -e "${YELLOW}[9/10] Applying system hardening...${NC}"

# Disable unused network protocols
echo "install dccp /bin/true" | sudo tee -a /etc/modprobe.d/blacklist.conf
echo "install sctp /bin/true" | sudo tee -a /etc/modprobe.d/blacklist.conf
echo "install rds /bin/true" | sudo tee -a /etc/modprobe.d/blacklist.conf
echo "install tipc /bin/true" | sudo tee -a /etc/modprobe.d/blacklist.conf

# Kernel parameter hardening
sudo tee /etc/sysctl.d/99-security.conf > /dev/null << 'EOF'
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
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
net.ipv4.tcp_syncookies = 1

# Memory protection
kernel.dmesg_restrict = 1
kernel.kptr_restrict = 2
kernel.yama.ptrace_scope = 1

# File system protection
fs.protected_hardlinks = 1
fs.protected_symlinks = 1
fs.suid_dumpable = 0
EOF

sudo sysctl -p /etc/sysctl.d/99-security.conf

echo -e "${GREEN}✓ System hardening applied${NC}"

# 10. Create security monitoring script
echo -e "${YELLOW}[10/10] Creating security monitoring script...${NC}"
sudo tee /usr/local/bin/security-check > /dev/null << 'EOF'
#!/bin/bash

# AI Trading Sentinel - Security Check Script

echo "🔍 Security Status Check - $(date)"
echo "======================================"

# Check firewall status
echo "🔥 Firewall Status:"
sudo ufw status numbered
echo

# Check fail2ban status
echo "🚫 Fail2Ban Status:"
sudo fail2ban-client status
echo

# Check SSH connections
echo "🔐 Active SSH Connections:"
who
echo

# Check system updates
echo "📦 System Updates:"
apt list --upgradable 2>/dev/null | wc -l
echo

# Check disk usage
echo "💾 Disk Usage:"
df -h / | tail -1
echo

# Check memory usage
echo "🧠 Memory Usage:"
free -h | grep Mem
echo

# Check running services
echo "⚙️  Critical Services:"
systemctl is-active aitrading-backend aitrading-bot nginx fail2ban ufw
echo

# Check recent login attempts
echo "🔍 Recent Login Attempts (last 10):"
lastb | head -10
echo

# Check for rootkits (quick scan)
echo "🛡️  Quick Rootkit Scan:"
sudo rkhunter --check --sk --quiet
echo "Rootkit scan completed"
EOF

sudo chmod +x /usr/local/bin/security-check

echo -e "${GREEN}✓ Security monitoring script created${NC}"

# Final security report
echo
echo -e "${GREEN}🎉 Security Hardening Complete!${NC}"
echo "================================"
echo
echo -e "${YELLOW}Important Security Notes:${NC}"
echo "• SSH port changed to 2222 (update your connections)"
echo "• Root login disabled"
echo "• Password authentication disabled"
echo "• Firewall enabled with restrictive rules"
echo "• Fail2Ban monitoring active"
echo "• Automatic security updates enabled"
echo "• Log rotation configured"
echo
echo -e "${YELLOW}Security Commands:${NC}"
echo "• Check security status: sudo security-check"
echo "• View firewall rules: sudo ufw status numbered"
echo "• Check fail2ban: sudo fail2ban-client status"
echo "• View SSH logs: sudo journalctl -u ssh"
echo "• Check system logs: sudo tail -f /var/log/syslog"
echo
echo -e "${RED}⚠️  IMPORTANT: Test SSH connection on port 2222 before closing this session!${NC}"
echo "   ssh -p 2222 aitrading@$(hostname -I | awk '{print $1}')"
echo

# Run initial security check
echo -e "${YELLOW}Running initial security check...${NC}"
sudo /usr/local/bin/security-check

echo -e "${GREEN}Security hardening completed successfully!${NC}"