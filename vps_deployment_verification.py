#!/usr/bin/env python3
"""
AI Trading Sentinel - VPS Deployment Verification Script
Run this script on the Contabo VPS after deployment to verify all services are working.

Usage:
    python3 vps_deployment_verification.py
"""

import requests
import subprocess
import socket
import time
import sys
from datetime import datetime

# VPS Configuration
VPS_IP = "161.97.112.146"
FRONTEND_PORT = 3000
BACKEND_PORT = 5000
NGINX_PORT = 80

# Colors for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    NC = '\033[0m'  # No Color

def log(message, color=Colors.BLUE):
    """Print colored log message with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"{color}[{timestamp}]{Colors.NC} {message}")

def success(message):
    """Print success message"""
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}")

def warning(message):
    """Print warning message"""
    print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")

def error(message):
    """Print error message"""
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")

def check_port_listening(port, host='localhost'):
    """Check if a port is listening"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        return False

def check_systemd_service(service_name):
    """Check if a systemd service is active"""
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', service_name],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0 and result.stdout.strip() == 'active'
    except Exception as e:
        return False

def check_http_endpoint(url, timeout=10):
    """Check if HTTP endpoint is responding"""
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code == 200, response.status_code
    except requests.exceptions.RequestException as e:
        return False, str(e)

def get_service_logs(service_name, lines=10):
    """Get recent logs from a systemd service"""
    try:
        result = subprocess.run(
            ['journalctl', '-u', service_name, '-n', str(lines), '--no-pager'],
            capture_output=True,
            text=True,
            timeout=15
        )
        return result.stdout if result.returncode == 0 else f"Error getting logs: {result.stderr}"
    except Exception as e:
        return f"Exception getting logs: {str(e)}"

def main():
    """Main verification function"""
    print(f"{Colors.CYAN}" + "="*60 + f"{Colors.NC}")
    print(f"{Colors.WHITE}AI Trading Sentinel - VPS Deployment Verification{Colors.NC}")
    print(f"{Colors.CYAN}" + "="*60 + f"{Colors.NC}")
    print()
    
    log(f"Verifying deployment on VPS: {VPS_IP}")
    print()
    
    # Test results storage
    results = {
        'systemd_services': {},
        'port_checks': {},
        'http_endpoints': {},
        'overall_status': 'UNKNOWN'
    }
    
    # 1. Check Systemd Services
    log("Step 1: Checking systemd services...")
    services = ['nginx', 'ai-trading-backend', 'ai-trading-frontend']
    
    for service in services:
        is_active = check_systemd_service(service)
        results['systemd_services'][service] = is_active
        
        if is_active:
            success(f"{service} is active and running")
        else:
            error(f"{service} is not active")
            # Show recent logs for failed services
            log(f"Recent logs for {service}:")
            logs = get_service_logs(service, 5)
            print(f"{Colors.YELLOW}{logs}{Colors.NC}")
    
    print()
    
    # 2. Check Port Listening
    log("Step 2: Checking if ports are listening...")
    ports = {
        'Nginx (HTTP)': NGINX_PORT,
        'Frontend': FRONTEND_PORT,
        'Backend API': BACKEND_PORT
    }
    
    for name, port in ports.items():
        is_listening = check_port_listening(port)
        results['port_checks'][name] = is_listening
        
        if is_listening:
            success(f"{name} is listening on port {port}")
        else:
            error(f"{name} is NOT listening on port {port}")
    
    print()
    
    # 3. Check HTTP Endpoints
    log("Step 3: Testing HTTP endpoints...")
    
    endpoints = {
        'Frontend (Local)': f'http://localhost:{FRONTEND_PORT}',
        'Backend API (Local)': f'http://localhost:{BACKEND_PORT}/api/status',
        'Frontend (External)': f'http://{VPS_IP}:{FRONTEND_PORT}',
        'Backend API (External)': f'http://{VPS_IP}:{BACKEND_PORT}/api/status',
        'Nginx Proxy (External)': f'http://{VPS_IP}'
    }
    
    for name, url in endpoints.items():
        log(f"Testing {name}: {url}")
        is_ok, status = check_http_endpoint(url)
        results['http_endpoints'][name] = {'ok': is_ok, 'status': status}
        
        if is_ok:
            success(f"{name} is responding (Status: {status})")
        else:
            error(f"{name} is not responding (Error: {status})")
        
        time.sleep(1)  # Small delay between requests
    
    print()
    
    # 4. Overall Assessment
    log("Step 4: Overall deployment assessment...")
    
    # Count successful checks
    services_ok = sum(results['systemd_services'].values())
    ports_ok = sum(results['port_checks'].values())
    endpoints_ok = sum(1 for ep in results['http_endpoints'].values() if ep['ok'])
    
    total_services = len(results['systemd_services'])
    total_ports = len(results['port_checks'])
    total_endpoints = len(results['http_endpoints'])
    
    print(f"{Colors.PURPLE}Assessment Summary:{Colors.NC}")
    print(f"  Systemd Services: {services_ok}/{total_services} active")
    print(f"  Port Listening:   {ports_ok}/{total_ports} listening")
    print(f"  HTTP Endpoints:   {endpoints_ok}/{total_endpoints} responding")
    print()
    
    # Determine overall status
    if services_ok == total_services and ports_ok == total_ports and endpoints_ok >= 3:
        results['overall_status'] = 'SUCCESS'
        success("🎉 DEPLOYMENT SUCCESSFUL! All services are running properly.")
        print()
        print(f"{Colors.GREEN}Production URLs are now ACTIVE:{Colors.NC}")
        print(f"  Frontend: http://{VPS_IP}:{FRONTEND_PORT}/")
        print(f"  Backend:  http://{VPS_IP}:{BACKEND_PORT}/api/status")
        print(f"  WebSocket: ws://{VPS_IP}:{BACKEND_PORT}/")
        print(f"  Nginx Proxy: http://{VPS_IP}/")
        
    elif services_ok >= 2 and ports_ok >= 2:
        results['overall_status'] = 'PARTIAL'
        warning("⚠️  PARTIAL SUCCESS: Some services are running, but issues detected.")
        print()
        print("Troubleshooting steps:")
        print("1. Check service logs: sudo journalctl -u [service-name] -f")
        print("2. Restart failed services: sudo systemctl restart [service-name]")
        print("3. Check firewall: sudo ufw status")
        print("4. Verify .env configuration")
        
    else:
        results['overall_status'] = 'FAILED'
        error("❌ DEPLOYMENT FAILED: Critical services are not running.")
        print()
        print("Immediate actions required:")
        print("1. Check deployment logs: sudo journalctl -xe")
        print("2. Verify system resources: htop")
        print("3. Re-run deployment script: ./vps_quick_deploy.sh")
        print("4. Check .env file configuration")
    
    print()
    
    # 5. Additional Information
    log("Additional system information:")
    
    try:
        # System uptime
        uptime_result = subprocess.run(['uptime'], capture_output=True, text=True, timeout=5)
        if uptime_result.returncode == 0:
            print(f"  System uptime: {uptime_result.stdout.strip()}")
        
        # Disk usage
        df_result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True, timeout=5)
        if df_result.returncode == 0:
            lines = df_result.stdout.strip().split('\n')
            if len(lines) >= 2:
                print(f"  Disk usage: {lines[1]}")
        
        # Memory usage
        free_result = subprocess.run(['free', '-h'], capture_output=True, text=True, timeout=5)
        if free_result.returncode == 0:
            lines = free_result.stdout.strip().split('\n')
            if len(lines) >= 2:
                print(f"  Memory: {lines[1]}")
                
    except Exception as e:
        warning(f"Could not get system information: {e}")
    
    print()
    print(f"{Colors.CYAN}" + "="*60 + f"{Colors.NC}")
    print(f"{Colors.WHITE}Verification completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.NC}")
    print(f"{Colors.CYAN}" + "="*60 + f"{Colors.NC}")
    
    # Return appropriate exit code
    if results['overall_status'] == 'SUCCESS':
        return 0
    elif results['overall_status'] == 'PARTIAL':
        return 1
    else:
        return 2

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Verification interrupted by user{Colors.NC}")
        sys.exit(130)
    except Exception as e:
        error(f"Verification failed with exception: {e}")
        sys.exit(1)