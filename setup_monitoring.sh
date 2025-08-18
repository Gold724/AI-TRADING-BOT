#!/bin/bash

# TradeBot Sentinel - Cloud Monitoring Setup Script
# This script sets up comprehensive monitoring for the TradeBot Sentinel in cloud environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MONITORING_DIR="/opt/tradebot-monitoring"
PROMETHEUS_VERSION="2.40.0"
GRAFANA_VERSION="9.3.0"
NODE_EXPORTER_VERSION="1.5.0"
ALERTMANAGER_VERSION="0.25.0"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root"
        exit 1
    fi
}

# Function to detect OS
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    else
        print_error "Cannot detect OS"
        exit 1
    fi
    print_status "Detected OS: $OS $VER"
}

# Function to install dependencies
install_dependencies() {
    print_status "Installing dependencies..."
    
    if [[ $OS == *"Ubuntu"* ]] || [[ $OS == *"Debian"* ]]; then
        apt-get update
        apt-get install -y wget curl tar systemd adduser libfontconfig1
    elif [[ $OS == *"CentOS"* ]] || [[ $OS == *"Red Hat"* ]] || [[ $OS == *"Rocky"* ]]; then
        yum update -y
        yum install -y wget curl tar systemd fontconfig
    else
        print_warning "Unsupported OS. Please install dependencies manually."
    fi
}

# Function to create monitoring user
create_monitoring_user() {
    print_status "Creating monitoring users..."
    
    # Create prometheus user
    if ! id "prometheus" &>/dev/null; then
        useradd --no-create-home --shell /bin/false prometheus
        print_success "Created prometheus user"
    fi
    
    # Create grafana user
    if ! id "grafana" &>/dev/null; then
        useradd --no-create-home --shell /bin/false grafana
        print_success "Created grafana user"
    fi
    
    # Create node_exporter user
    if ! id "node_exporter" &>/dev/null; then
        useradd --no-create-home --shell /bin/false node_exporter
        print_success "Created node_exporter user"
    fi
}

# Function to create directories
create_directories() {
    print_status "Creating monitoring directories..."
    
    mkdir -p $MONITORING_DIR/{prometheus,grafana,node_exporter,alertmanager}
    mkdir -p /etc/{prometheus,grafana,alertmanager}
    mkdir -p /var/lib/{prometheus,grafana,alertmanager}
    mkdir -p /var/log/{prometheus,grafana,alertmanager}
    
    # Set permissions
    chown -R prometheus:prometheus /etc/prometheus /var/lib/prometheus /var/log/prometheus
    chown -R grafana:grafana /etc/grafana /var/lib/grafana /var/log/grafana
    chown -R prometheus:prometheus /etc/alertmanager /var/lib/alertmanager /var/log/alertmanager
    
    print_success "Created monitoring directories"
}

# Function to install Prometheus
install_prometheus() {
    print_status "Installing Prometheus $PROMETHEUS_VERSION..."
    
    cd $MONITORING_DIR/prometheus
    wget https://github.com/prometheus/prometheus/releases/download/v$PROMETHEUS_VERSION/prometheus-$PROMETHEUS_VERSION.linux-amd64.tar.gz
    tar xvf prometheus-$PROMETHEUS_VERSION.linux-amd64.tar.gz
    
    cp prometheus-$PROMETHEUS_VERSION.linux-amd64/prometheus /usr/local/bin/
    cp prometheus-$PROMETHEUS_VERSION.linux-amd64/promtool /usr/local/bin/
    
    chown prometheus:prometheus /usr/local/bin/prometheus
    chown prometheus:prometheus /usr/local/bin/promtool
    
    # Copy configuration
    if [[ -f "$(dirname "$0")/prometheus.yml" ]]; then
        cp "$(dirname "$0")/prometheus.yml" /etc/prometheus/
        chown prometheus:prometheus /etc/prometheus/prometheus.yml
    fi
    
    # Create systemd service
    cat > /etc/systemd/system/prometheus.service << EOF
[Unit]
Description=Prometheus
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/usr/local/bin/prometheus \\
    --config.file /etc/prometheus/prometheus.yml \\
    --storage.tsdb.path /var/lib/prometheus/ \\
    --web.console.templates=/etc/prometheus/consoles \\
    --web.console.libraries=/etc/prometheus/console_libraries \\
    --web.listen-address=0.0.0.0:9090 \\
    --web.enable-lifecycle

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable prometheus
    
    print_success "Prometheus installed successfully"
}

# Function to install Node Exporter
install_node_exporter() {
    print_status "Installing Node Exporter $NODE_EXPORTER_VERSION..."
    
    cd $MONITORING_DIR/node_exporter
    wget https://github.com/prometheus/node_exporter/releases/download/v$NODE_EXPORTER_VERSION/node_exporter-$NODE_EXPORTER_VERSION.linux-amd64.tar.gz
    tar xvf node_exporter-$NODE_EXPORTER_VERSION.linux-amd64.tar.gz
    
    cp node_exporter-$NODE_EXPORTER_VERSION.linux-amd64/node_exporter /usr/local/bin/
    chown node_exporter:node_exporter /usr/local/bin/node_exporter
    
    # Create systemd service
    cat > /etc/systemd/system/node_exporter.service << EOF
[Unit]
Description=Node Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable node_exporter
    
    print_success "Node Exporter installed successfully"
}

# Function to install Grafana
install_grafana() {
    print_status "Installing Grafana $GRAFANA_VERSION..."
    
    if [[ $OS == *"Ubuntu"* ]] || [[ $OS == *"Debian"* ]]; then
        wget -q -O - https://packages.grafana.com/gpg.key | apt-key add -
        echo "deb https://packages.grafana.com/oss/deb stable main" | tee -a /etc/apt/sources.list.d/grafana.list
        apt-get update
        apt-get install -y grafana
    elif [[ $OS == *"CentOS"* ]] || [[ $OS == *"Red Hat"* ]] || [[ $OS == *"Rocky"* ]]; then
        cat > /etc/yum.repos.d/grafana.repo << EOF
[grafana]
name=grafana
baseurl=https://packages.grafana.com/oss/rpm
repo_gpgcheck=1
enabled=1
gpgcheck=1
gpgkey=https://packages.grafana.com/gpg.key
EOF
        yum install -y grafana
    fi
    
    # Configure Grafana
    cat > /etc/grafana/grafana.ini << EOF
[server]
http_port = 3000
domain = localhost

[security]
admin_user = admin
admin_password = tradebot123

[database]
type = sqlite3
path = grafana.db

[session]
provider = file

[analytics]
reporting_enabled = false
check_for_updates = false

[log]
mode = file
level = info
EOF
    
    # Copy dashboard if exists
    if [[ -d "$(dirname "$0")/grafana/dashboards" ]]; then
        mkdir -p /var/lib/grafana/dashboards
        cp -r "$(dirname "$0")/grafana/dashboards"/* /var/lib/grafana/dashboards/
        chown -R grafana:grafana /var/lib/grafana/dashboards
    fi
    
    systemctl daemon-reload
    systemctl enable grafana-server
    
    print_success "Grafana installed successfully"
}

# Function to install Alertmanager
install_alertmanager() {
    print_status "Installing Alertmanager $ALERTMANAGER_VERSION..."
    
    cd $MONITORING_DIR/alertmanager
    wget https://github.com/prometheus/alertmanager/releases/download/v$ALERTMANAGER_VERSION/alertmanager-$ALERTMANAGER_VERSION.linux-amd64.tar.gz
    tar xvf alertmanager-$ALERTMANAGER_VERSION.linux-amd64.tar.gz
    
    cp alertmanager-$ALERTMANAGER_VERSION.linux-amd64/alertmanager /usr/local/bin/
    cp alertmanager-$ALERTMANAGER_VERSION.linux-amd64/amtool /usr/local/bin/
    
    chown prometheus:prometheus /usr/local/bin/alertmanager
    chown prometheus:prometheus /usr/local/bin/amtool
    
    # Create basic configuration
    cat > /etc/alertmanager/alertmanager.yml << EOF
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alertmanager@tradebot.local'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
- name: 'web.hook'
  webhook_configs:
  - url: 'http://127.0.0.1:5001/'
EOF
    
    chown prometheus:prometheus /etc/alertmanager/alertmanager.yml
    
    # Create systemd service
    cat > /etc/systemd/system/alertmanager.service << EOF
[Unit]
Description=Alertmanager
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/usr/local/bin/alertmanager \\
    --config.file /etc/alertmanager/alertmanager.yml \\
    --storage.path /var/lib/alertmanager/

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable alertmanager
    
    print_success "Alertmanager installed successfully"
}

# Function to configure firewall
configure_firewall() {
    print_status "Configuring firewall..."
    
    if command -v ufw &> /dev/null; then
        ufw allow 9090/tcp  # Prometheus
        ufw allow 3000/tcp  # Grafana
        ufw allow 9100/tcp  # Node Exporter
        ufw allow 9093/tcp  # Alertmanager
        print_success "UFW firewall configured"
    elif command -v firewall-cmd &> /dev/null; then
        firewall-cmd --permanent --add-port=9090/tcp
        firewall-cmd --permanent --add-port=3000/tcp
        firewall-cmd --permanent --add-port=9100/tcp
        firewall-cmd --permanent --add-port=9093/tcp
        firewall-cmd --reload
        print_success "Firewalld configured"
    else
        print_warning "No firewall detected. Please configure manually."
    fi
}

# Function to start services
start_services() {
    print_status "Starting monitoring services..."
    
    systemctl start prometheus
    systemctl start node_exporter
    systemctl start grafana-server
    systemctl start alertmanager
    
    # Wait for services to start
    sleep 10
    
    # Check service status
    if systemctl is-active --quiet prometheus; then
        print_success "Prometheus is running on port 9090"
    else
        print_error "Prometheus failed to start"
    fi
    
    if systemctl is-active --quiet node_exporter; then
        print_success "Node Exporter is running on port 9100"
    else
        print_error "Node Exporter failed to start"
    fi
    
    if systemctl is-active --quiet grafana-server; then
        print_success "Grafana is running on port 3000"
    else
        print_error "Grafana failed to start"
    fi
    
    if systemctl is-active --quiet alertmanager; then
        print_success "Alertmanager is running on port 9093"
    else
        print_error "Alertmanager failed to start"
    fi
}

# Function to setup Grafana datasources and dashboards
setup_grafana() {
    print_status "Setting up Grafana datasources and dashboards..."
    
    # Wait for Grafana to be ready
    sleep 30
    
    # Add Prometheus datasource
    curl -X POST \
        -H "Content-Type: application/json" \
        -d '{
            "name": "Prometheus",
            "type": "prometheus",
            "url": "http://localhost:9090",
            "access": "proxy",
            "isDefault": true
        }' \
        http://admin:tradebot123@localhost:3000/api/datasources
    
    print_success "Grafana setup completed"
}

# Function to create monitoring summary
create_summary() {
    print_status "Creating monitoring summary..."
    
    cat > /opt/tradebot-monitoring/MONITORING_INFO.txt << EOF
TradeBot Sentinel - Monitoring Setup Summary
==========================================

Services Status:
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/tradebot123)
- Node Exporter: http://localhost:9100
- Alertmanager: http://localhost:9093

Configuration Files:
- Prometheus: /etc/prometheus/prometheus.yml
- Grafana: /etc/grafana/grafana.ini
- Alertmanager: /etc/alertmanager/alertmanager.yml

Data Directories:
- Prometheus: /var/lib/prometheus
- Grafana: /var/lib/grafana
- Alertmanager: /var/lib/alertmanager

Log Files:
- Prometheus: /var/log/prometheus
- Grafana: /var/log/grafana
- Alertmanager: /var/log/alertmanager

Service Management:
- Start all: systemctl start prometheus grafana-server node_exporter alertmanager
- Stop all: systemctl stop prometheus grafana-server node_exporter alertmanager
- Restart all: systemctl restart prometheus grafana-server node_exporter alertmanager
- Status: systemctl status prometheus grafana-server node_exporter alertmanager

Firewall Ports:
- 9090: Prometheus
- 3000: Grafana
- 9100: Node Exporter
- 9093: Alertmanager

Setup completed on: $(date)
EOF
    
    print_success "Monitoring summary created at /opt/tradebot-monitoring/MONITORING_INFO.txt"
}

# Main execution
main() {
    print_status "Starting TradeBot Sentinel monitoring setup..."
    
    check_root
    detect_os
    install_dependencies
    create_monitoring_user
    create_directories
    install_prometheus
    install_node_exporter
    install_grafana
    install_alertmanager
    configure_firewall
    start_services
    setup_grafana
    create_summary
    
    print_success "\n=== TradeBot Sentinel Monitoring Setup Complete ==="
    print_status "Access your monitoring services:"
    print_status "- Prometheus: http://$(hostname -I | awk '{print $1}'):9090"
    print_status "- Grafana: http://$(hostname -I | awk '{print $1}'):3000 (admin/tradebot123)"
    print_status "- Node Exporter: http://$(hostname -I | awk '{print $1}'):9100"
    print_status "- Alertmanager: http://$(hostname -I | awk '{print $1}'):9093"
    print_status "\nFor detailed information, see: /opt/tradebot-monitoring/MONITORING_INFO.txt"
}

# Run main function
main "$@"