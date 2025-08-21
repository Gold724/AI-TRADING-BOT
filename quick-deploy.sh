#!/bin/bash

# 🚀 AI Trading Sentinel - Quick 5-Step Production Deployment
# TRAE-SentinelOps: Complete automated deployment for Contabo VPS

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Configuration
SERVER_IP="${1:-localhost}"
DOMAIN="${2:-}"
ENVIRONMENT="production"

log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}✓ $1${NC}"
}

warn() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

error() {
    echo -e "${RED}✗ $1${NC}"
    exit 1
}

header() {
    echo -e "\n${PURPLE}$1${NC}"
    echo -e "${PURPLE}$(echo $1 | sed 's/./=/g')${NC}"
}

# Step 1: Deploy to Contabo VPS
deploy_to_vps() {
    header "STEP 1: Deploy to Contabo VPS"
    
    log "Running production deployment script..."
    
    if [[ -f "deploy/deploy-production.sh" ]]; then
        chmod +x deploy/deploy-production.sh
        
        if [[ $EUID -eq 0 ]]; then
            ./deploy/deploy-production.sh
        else
            sudo ./deploy/deploy-production.sh
        fi
        
        success "Production deployment completed"
    else
        error "deploy/deploy-production.sh not found"
    fi
}

# Step 2: Configure credentials
configure_credentials() {
    header "STEP 2: Configure Credentials"
    
    local env_file=".env"
    local env_template=".env.template"
    
    if [[ ! -f "$env_template" ]]; then
        error ".env.template not found"
    fi
    
    if [[ ! -f "$env_file" ]]; then
        log "Creating .env file from template..."
        cp "$env_template" "$env_file"
        
        # Generate secure keys
        SECRET_KEY=$(openssl rand -hex 32)
        JWT_SECRET=$(openssl rand -hex 32)
        ENCRYPTION_KEY=$(openssl rand -hex 32)
        
        # Update .env with generated keys
        sed -i "s/your-secret-key-here/$SECRET_KEY/g" "$env_file"
        sed -i "s/your-jwt-secret-key-here/$JWT_SECRET/g" "$env_file"
        sed -i "s/your-encryption-key-here/$ENCRYPTION_KEY/g" "$env_file"
        
        # Set production environment
        sed -i "s/ENVIRONMENT=.*/ENVIRONMENT=production/g" "$env_file"
        sed -i "s/DEBUG=.*/DEBUG=false/g" "$env_file"
        sed -i "s/TRADING_ENABLED=.*/TRADING_ENABLED=false/g" "$env_file"
        
        success ".env file created with secure keys"
    else
        success ".env file already exists"
    fi
    
    # Set proper permissions
    chmod 600 "$env_file"
    
    warn "IMPORTANT: Update broker credentials in .env file:"
    echo -e "${YELLOW}  - BROKER_USERNAME=your-broker-username${NC}"
    echo -e "${YELLOW}  - BROKER_PASSWORD=your-broker-password${NC}"
    echo -e "${YELLOW}  - BROKER_URL=https://your-broker-platform.com${NC}"
    echo -e "${YELLOW}  - BROKER_API_KEY=your-api-key${NC}"
    echo -e "${YELLOW}  - BROKER_API_SECRET=your-api-secret${NC}"
    
    read -p "Press Enter after updating broker credentials in .env file..."
}

# Step 3: Validate deployment
validate_deployment() {
    header "STEP 3: Validate Deployment"
    
    log "Running deployment validation..."
    
    if [[ -f "scripts/validate_deployment.py" ]]; then
        if python3 scripts/validate_deployment.py --environment production; then
            success "Deployment validation passed"
        else
            error "Deployment validation failed - fix issues before proceeding"
        fi
    else
        warn "Validation script not found, skipping validation"
    fi
}

# Step 4: Monitor system
setup_monitoring() {
    header "STEP 4: Monitor System"
    
    log "Setting up monitoring access..."
    
    # Start monitoring stack if not running
    if command -v docker-compose &> /dev/null; then
        if [[ -f "docker-compose.monitoring.yml" ]]; then
            docker-compose -f docker-compose.monitoring.yml up -d
            sleep 10
            success "Monitoring stack started"
        fi
    fi
    
    # Check if Grafana is accessible
    if curl -s "http://localhost:3000" > /dev/null; then
        success "Grafana is accessible at http://$SERVER_IP:3000"
        echo -e "${BLUE}  Default login: admin/admin${NC}"
        echo -e "${YELLOW}  ⚠ Change default password after first login${NC}"
    else
        warn "Grafana not accessible - check monitoring stack"
    fi
    
    # Check Prometheus
    if curl -s "http://localhost:9090" > /dev/null; then
        success "Prometheus is accessible at http://$SERVER_IP:9090"
    else
        warn "Prometheus not accessible"
    fi
    
    echo -e "\n${BLUE}Key Monitoring URLs:${NC}"
    echo -e "${BLUE}  • Grafana Dashboard: http://$SERVER_IP:3000${NC}"
    echo -e "${BLUE}  • Prometheus Metrics: http://$SERVER_IP:9090${NC}"
    echo -e "${BLUE}  • Alertmanager: http://$SERVER_IP:9093${NC}"
    echo -e "${BLUE}  • Application Health: http://$SERVER_IP/health${NC}"
}

# Step 5: Start trading
start_trading() {
    header "STEP 5: Start Trading"
    
    log "Preparing to start trading operations..."
    
    # Start application services
    if command -v systemctl &> /dev/null; then
        if systemctl is-enabled trae.service &> /dev/null; then
            systemctl start trae.service
            sleep 5
            
            if systemctl is-active trae.service &> /dev/null; then
                success "Trading service started successfully"
            else
                error "Failed to start trading service"
            fi
        else
            warn "Systemd service not configured - starting manually"
            
            # Start backend
            if [[ -f "backend_main.py" ]]; then
                nohup python3 backend_main.py > logs/backend.log 2>&1 &
                success "Backend started"
            fi
            
            # Start main bot (but keep trading disabled initially)
            if [[ -f "main.py" ]]; then
                nohup python3 main.py > logs/main.log 2>&1 &
                success "Main bot started (trading disabled)"
            fi
        fi
    fi
    
    # Check service health
    sleep 10
    if curl -s "http://localhost:5000/api/health" > /dev/null; then
        success "API health check passed"
    else
        warn "API health check failed - check service logs"
    fi
    
    warn "TRADING IS CURRENTLY DISABLED FOR SAFETY"
    echo -e "\n${YELLOW}To enable live trading:${NC}"
    echo -e "${YELLOW}1. Monitor system for 24 hours to ensure stability${NC}"
    echo -e "${YELLOW}2. Verify all broker credentials are working${NC}"
    echo -e "${YELLOW}3. Test with small position sizes first${NC}"
    echo -e "${YELLOW}4. Set TRADING_ENABLED=true in .env file${NC}"
    echo -e "${YELLOW}5. Restart the service: systemctl restart trae.service${NC}"
}

# Display final summary
show_summary() {
    header "🚀 DEPLOYMENT COMPLETE"
    
    echo -e "\n${GREEN}AI Trading Sentinel has been successfully deployed!${NC}\n"
    
    echo -e "${BLUE}📊 Access URLs:${NC}"
    echo -e "  • Frontend: http://$SERVER_IP"
    echo -e "  • API: http://$SERVER_IP/api"
    echo -e "  • Health Check: http://$SERVER_IP/health"
    echo -e "  • Grafana: http://$SERVER_IP:3000 (admin/admin)"
    echo -e "  • Prometheus: http://$SERVER_IP:9090"
    
    echo -e "\n${BLUE}🔧 Useful Commands:${NC}"
    echo -e "  • Check status: systemctl status trae.service"
    echo -e "  • View logs: journalctl -u trae.service -f"
    echo -e "  • Restart bot: systemctl restart trae.service"
    echo -e "  • Validate: python scripts/validate_deployment.py --environment production"
    echo -e "  • Monitor: /opt/ai-trading-sentinel/scripts/system-monitor.sh --report"
    
    echo -e "\n${RED}⚠️  IMPORTANT NEXT STEPS:${NC}"
    echo -e "  1. Change Grafana default password (admin/admin)"
    echo -e "  2. Update broker credentials in .env file"
    echo -e "  3. Monitor system stability for 24 hours"
    echo -e "  4. Test with demo account before live trading"
    echo -e "  5. Enable trading: TRADING_ENABLED=true in .env"
    
    echo -e "\n${GREEN}🎉 Ready for 24/7 automated trading operations!${NC}"
}

# Main execution
main() {
    echo -e "${PURPLE}"
    echo "██████╗ ██████╗  █████╗ ███████╗    ███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗     "
    echo "╚══██╔══╝██╔══██╗██╔══██╗██╔════╝    ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║     "
    echo "   ██║   ██████╔╝███████║█████╗      ███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║     "
    echo "   ██║   ██╔══██╗██╔══██║██╔══╝      ╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║     "
    echo "   ██║   ██║  ██║██║  ██║███████╗    ███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗███████╗"
    echo "   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝    ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝"
    echo -e "${NC}"
    echo -e "${BLUE}🚀 AI Trading Sentinel - 5-Step Production Deployment${NC}"
    echo -e "${BLUE}TRAE-SentinelOps: Automated 24/7 Trading Operations${NC}\n"
    
    if [[ "$SERVER_IP" == "localhost" ]]; then
        warn "Using localhost - for remote deployment, run: ./quick-deploy.sh YOUR_SERVER_IP"
    fi
    
    # Execute 5-step deployment process
    deploy_to_vps
    configure_credentials
    validate_deployment
    setup_monitoring
    start_trading
    show_summary
    
    log "Deployment completed successfully! 🎉"
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi