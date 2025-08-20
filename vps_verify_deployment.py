#!/usr/bin/env python3
"""
VPS Deployment Verification Script
Run this on the Contabo VPS after deployment to verify all services are working
"""

import requests
import subprocess
import sys
import time
import socket
from datetime import datetime

def print_status(message, status="INFO"):
    """Print formatted status message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    colors = {
        "INFO": "\033[94m",
        "SUCCESS": "\033[92m",
        "WARNING": "\033[93m",
        "ERROR": "\033[91m",
        "RESET": "\033[0m"
    }
    color = colors.get(status, colors["INFO"])
    print(f"{color}[{timestamp}] {status}: {message}{colors['RESET']}")

def check_port(host, port, timeout=5):
    """Check if a port is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print_status(f"Error checking port {port}: {e}", "ERROR")
        return False

def check_service_status(service_name):
    """Check systemd service status"""
    try:
        result = subprocess.run(
            ["systemctl", "is-active", service_name],
            capture_output=True,
            text=True
        )
        return result.stdout.strip() == "active"
    except Exception as e:
        print_status(f"Error checking service {service_name}: {e}", "ERROR")
        return False

def check_http_endpoint(url, timeout=10):
    """Check if HTTP endpoint is responding"""
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code == 200
    except Exception as e:
        print_status(f"Error checking {url}: {e}", "ERROR")
        return False

def main():
    """Main verification function"""
    print_status("Starting AI Trading Sentinel Deployment Verification", "INFO")
    print("=" * 60)
    
    # Check system services
    print_status("Checking System Services...", "INFO")
    services = [
        "ai-trading-backend",
        "ai-trading-frontend",
        "nginx"
    ]
    
    service_results = {}
    for service in services:
        is_active = check_service_status(service)
        service_results[service] = is_active
        status = "SUCCESS" if is_active else "ERROR"
        print_status(f"Service {service}: {'Active' if is_active else 'Inactive'}", status)
    
    # Check ports
    print_status("Checking Network Ports...", "INFO")
    ports = {
        3000: "Frontend",
        5000: "Backend API",
        80: "Nginx HTTP",
        22: "SSH"
    }
    
    port_results = {}
    for port, description in ports.items():
        is_open = check_port("localhost", port)
        port_results[port] = is_open
        status = "SUCCESS" if is_open else "ERROR"
        print_status(f"Port {port} ({description}): {'Open' if is_open else 'Closed'}", status)
    
    # Check HTTP endpoints
    print_status("Checking HTTP Endpoints...", "INFO")
    endpoints = {
        "http://localhost:5000/api/status": "Backend API Status",
        "http://localhost:5000/api/health": "Backend Health Check",
        "http://localhost:3000": "Frontend Application"
    }
    
    endpoint_results = {}
    for url, description in endpoints.items():
        is_responding = check_http_endpoint(url)
        endpoint_results[url] = is_responding
        status = "SUCCESS" if is_responding else "ERROR"
        print_status(f"{description}: {'Responding' if is_responding else 'Not Responding'}", status)
    
    # External accessibility check
    print_status("Checking External Accessibility...", "INFO")
    external_endpoints = {
        "http://161.97.112.146:5000/api/status": "External Backend API",
        "http://161.97.112.146:3000": "External Frontend"
    }
    
    external_results = {}
    for url, description in external_endpoints.items():
        is_responding = check_http_endpoint(url)
        external_results[url] = is_responding
        status = "SUCCESS" if is_responding else "WARNING"
        print_status(f"{description}: {'Accessible' if is_responding else 'Not Accessible'}", status)
    
    # Summary
    print("=" * 60)
    print_status("Deployment Verification Summary", "INFO")
    
    total_checks = len(service_results) + len(port_results) + len(endpoint_results)
    passed_checks = (
        sum(service_results.values()) + 
        sum(port_results.values()) + 
        sum(endpoint_results.values())
    )
    
    print_status(f"Total Checks: {total_checks}", "INFO")
    print_status(f"Passed Checks: {passed_checks}", "SUCCESS" if passed_checks == total_checks else "WARNING")
    print_status(f"Failed Checks: {total_checks - passed_checks}", "ERROR" if passed_checks != total_checks else "SUCCESS")
    
    # Recommendations
    if passed_checks != total_checks:
        print_status("Recommendations:", "WARNING")
        
        for service, is_active in service_results.items():
            if not is_active:
                print_status(f"  - Restart service: sudo systemctl restart {service}", "WARNING")
        
        for port, is_open in port_results.items():
            if not is_open:
                print_status(f"  - Check if service is running on port {port}", "WARNING")
        
        for url, is_responding in endpoint_results.items():
            if not is_responding:
                print_status(f"  - Check service logs for {url}", "WARNING")
    
    # Service logs command
    print_status("Useful Commands:", "INFO")
    print("  View backend logs: sudo journalctl -u ai-trading-backend -f")
    print("  View frontend logs: sudo journalctl -u ai-trading-frontend -f")
    print("  Restart all services: sudo systemctl restart ai-trading-backend ai-trading-frontend")
    print("  Check firewall: sudo ufw status")
    print("  Check processes: sudo netstat -tlnp | grep -E ':(3000|5000)'")
    
    return passed_checks == total_checks

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_status("Verification interrupted by user", "WARNING")
        sys.exit(1)
    except Exception as e:
        print_status(f"Verification failed with error: {e}", "ERROR")
        sys.exit(1)