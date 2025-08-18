#!/usr/bin/env python3
"""
AI Trading Sentinel - Deployment Verification Script
Tests VNC, frontend, backend, and web access connectivity

Usage: python verify_deployment.py
"""

import requests
import socket
import subprocess
import sys
import time
from urllib.parse import urljoin
import json

VPS_IP = "161.97.112.146"
VNC_PORT = 5901
WEB_PORT = 80
API_PORT = 5000
TIMEOUT = 10

def test_port_connectivity(host, port, service_name):
    """Test if a port is accessible"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✅ {service_name}: Port {port} is accessible")
            return True
        else:
            print(f"❌ {service_name}: Port {port} is not accessible")
            return False
    except Exception as e:
        print(f"❌ {service_name}: Connection error - {e}")
        return False

def test_http_endpoint(url, service_name, expected_content=None):
    """Test HTTP endpoint accessibility"""
    try:
        response = requests.get(url, timeout=TIMEOUT)
        
        if response.status_code == 200:
            print(f"✅ {service_name}: HTTP {response.status_code} - {len(response.content)} bytes")
            
            if expected_content:
                if expected_content.lower() in response.text.lower():
                    print(f"✅ {service_name}: Expected content found")
                else:
                    print(f"⚠️  {service_name}: Expected content not found")
            
            return True, response
        else:
            print(f"❌ {service_name}: HTTP {response.status_code} - {response.reason}")
            return False, response
            
    except requests.exceptions.ConnectTimeout:
        print(f"❌ {service_name}: Connection timeout")
        return False, None
    except requests.exceptions.ConnectionError:
        print(f"❌ {service_name}: Connection refused")
        return False, None
    except Exception as e:
        print(f"❌ {service_name}: Error - {e}")
        return False, None

def test_api_endpoints(base_url):
    """Test various API endpoints"""
    endpoints = [
        ("/api/health", "Health Check"),
        ("/api/status", "Bot Status"),
        ("/api/trades", "Trade History"),
        ("/api/config", "Configuration")
    ]
    
    results = {}
    
    for endpoint, name in endpoints:
        url = urljoin(base_url, endpoint)
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ API {name}: Available")
                results[endpoint] = True
            else:
                print(f"⚠️  API {name}: HTTP {response.status_code}")
                results[endpoint] = False
        except Exception:
            print(f"❌ API {name}: Not accessible")
            results[endpoint] = False
    
    return results

def ping_host(host):
    """Ping the host to test basic connectivity"""
    try:
        if sys.platform.startswith('win'):
            result = subprocess.run(['ping', '-n', '4', host], 
                                  capture_output=True, text=True, timeout=15)
        else:
            result = subprocess.run(['ping', '-c', '4', host], 
                                  capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            print(f"✅ Ping: {host} is reachable")
            return True
        else:
            print(f"❌ Ping: {host} is not reachable")
            return False
    except Exception as e:
        print(f"❌ Ping: Error - {e}")
        return False

def main():
    print("🔍 AI Trading Sentinel - Deployment Verification")
    print("=================================================")
    print(f"Target VPS: {VPS_IP}")
    print(f"Testing connectivity and services...\n")
    
    results = {
        'ping': False,
        'vnc': False,
        'web': False,
        'api': False,
        'frontend': False
    }
    
    # Test 1: Basic connectivity
    print("🌐 STEP 1: Basic Connectivity")
    print("-----------------------------")
    results['ping'] = ping_host(VPS_IP)
    print()
    
    # Test 2: VNC Server
    print("🖥️  STEP 2: VNC Server")
    print("----------------------")
    results['vnc'] = test_port_connectivity(VPS_IP, VNC_PORT, "VNC Server")
    if results['vnc']:
        print(f"🔗 VNC Connection: vnc://{VPS_IP}:{VNC_PORT}")
    print()
    
    # Test 3: Web Server (Nginx)
    print("🌐 STEP 3: Web Server")
    print("---------------------")
    web_url = f"http://{VPS_IP}"
    web_success, web_response = test_http_endpoint(web_url, "Web Server", "trading")
    results['web'] = web_success
    
    if web_success and web_response:
        # Check if it's serving frontend content
        content = web_response.text.lower()
        frontend_indicators = ['react', 'trading', 'dashboard', 'sentinel', 'app']
        
        found_indicators = [ind for ind in frontend_indicators if ind in content]
        if found_indicators:
            print(f"✅ Frontend: Detected indicators - {', '.join(found_indicators)}")
            results['frontend'] = True
        else:
            print(f"⚠️  Frontend: No clear indicators found")
    print()
    
    # Test 4: Backend API
    print("🔌 STEP 4: Backend API")
    print("----------------------")
    api_base = f"http://{VPS_IP}"
    
    # Test direct API port
    api_port_accessible = test_port_connectivity(VPS_IP, API_PORT, "API Direct Port")
    
    # Test API through Nginx proxy
    api_results = test_api_endpoints(api_base)
    results['api'] = any(api_results.values())
    print()
    
    # Test 5: WebSocket (if applicable)
    print("📡 STEP 5: WebSocket Support")
    print("----------------------------")
    ws_url = f"ws://{VPS_IP}/ws"
    print(f"🔗 WebSocket URL: {ws_url}")
    print("⚠️  WebSocket testing requires specialized client - manual verification needed")
    print()
    
    # Summary Report
    print("📊 DEPLOYMENT SUMMARY")
    print("=====================")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for service, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {service.upper()}: {'PASS' if status else 'FAIL'}")
    
    print(f"\n🎯 Overall Score: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
    
    if passed_tests == total_tests:
        print("🎉 DEPLOYMENT SUCCESSFUL! All services are operational.")
        print(f"🚀 Access your AI Trading Sentinel at: {web_url}")
    elif passed_tests >= total_tests * 0.7:
        print("⚠️  DEPLOYMENT PARTIALLY SUCCESSFUL. Some issues need attention.")
        print("Check the failed services above and verify VNC deployment steps.")
    else:
        print("❌ DEPLOYMENT FAILED. Multiple services are not accessible.")
        print("Please review VNC setup and deployment steps.")
    
    print("\n🔧 TROUBLESHOOTING TIPS")
    print("=======================")
    
    if not results['ping']:
        print("• Check VPS is running and network connectivity")
        print("• Verify VPS IP address is correct")
    
    if not results['vnc']:
        print("• Ensure VNC server is running: systemctl status vncserver@1")
        print("• Check VNC port 5901 is not blocked by firewall")
    
    if not results['web']:
        print("• Verify Nginx is running: systemctl status nginx")
        print("• Check Nginx configuration and port 80 access")
        print("• Ensure frontend files are in /var/www/html/")
    
    if not results['api']:
        print("• Check Flask backend is running on port 5000")
        print("• Verify Nginx proxy configuration for /api/ routes")
        print("• Check backend logs for errors")
    
    if not results['frontend']:
        print("• Verify frontend-cloud.zip was extracted properly")
        print("• Check file permissions in /var/www/html/")
        print("• Ensure index.html exists and is readable")
    
    print("\n📋 NEXT STEPS")
    print("=============")
    if passed_tests >= total_tests * 0.8:
        print("1. 🎮 Test trading bot functionality")
        print("2. 🔒 Set up HTTPS with Let's Encrypt")
        print("3. 📊 Configure monitoring and alerts")
        print("4. 🔐 Review security settings")
    else:
        print("1. 🔧 Fix failed services using VNC access")
        print("2. 📋 Re-run deployment verification")
        print("3. 📞 Check VNC deployment guide for troubleshooting")
    
    print(f"\n🔗 Quick Access Links:")
    print(f"• Trading Dashboard: {web_url}")
    print(f"• VNC Remote Access: vnc://{VPS_IP}:{VNC_PORT}")
    print(f"• API Health Check: {web_url}/api/health")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)