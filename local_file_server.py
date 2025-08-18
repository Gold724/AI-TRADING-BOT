#!/usr/bin/env python3
"""
Local HTTP File Server for VNC Frontend Upload
Serves frontend-cloud.zip for easy download to VPS via VNC

Usage:
1. Run this script on Windows: python local_file_server.py
2. In VNC terminal: wget http://YOUR_WINDOWS_IP:8000/frontend-cloud.zip
3. Extract and deploy on VPS
"""

import http.server
import socketserver
import os
import socket
import sys
from pathlib import Path

PORT = 8000
FRONTEND_ZIP = "frontend-cloud.zip"

def get_local_ip():
    """Get the local IP address of this machine"""
    try:
        # Connect to a remote address to determine local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "localhost"

def main():
    print("🚀 AI Trading Sentinel - Local File Server")
    print("===========================================")
    
    # Check if frontend-cloud.zip exists
    if not os.path.exists(FRONTEND_ZIP):
        print(f"❌ Error: {FRONTEND_ZIP} not found in current directory!")
        print(f"Current directory: {os.getcwd()}")
        print("Please ensure frontend-cloud.zip is in the same directory as this script.")
        sys.exit(1)
    
    # Get file size
    file_size = os.path.getsize(FRONTEND_ZIP)
    print(f"✅ Found {FRONTEND_ZIP} ({file_size:,} bytes)")
    
    # Get local IP
    local_ip = get_local_ip()
    
    print(f"\n📡 Starting HTTP server on port {PORT}...")
    print(f"🌐 Local IP: {local_ip}")
    print(f"🔗 Download URL: http://{local_ip}:{PORT}/{FRONTEND_ZIP}")
    print("\n📋 VNC DOWNLOAD COMMANDS:")
    print("=========================")
    print("Execute these commands in your VNC terminal:")
    print(f"")
    print(f"cd /var/www/html")
    print(f"sudo rm -rf *")
    print(f"sudo wget http://{local_ip}:{PORT}/{FRONTEND_ZIP}")
    print(f"sudo unzip {FRONTEND_ZIP}")
    print(f"sudo rm {FRONTEND_ZIP}")
    print(f"sudo chown -R www-data:www-data /var/www/html")
    print(f"sudo chmod -R 755 /var/www/html")
    print(f"ls -la /var/www/html")
    print("")
    print("⚠️  Make sure Windows Firewall allows Python through port 8000")
    print("💡 TIP: Copy-paste the commands above into VNC terminal")
    print("\n🔥 Server starting... Press Ctrl+C to stop")
    print("=" * 50)
    
    # Custom handler to serve files
    class CustomHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            print(f"📥 {self.address_string()} - {format % args}")
        
        def end_headers(self):
            # Add CORS headers for cross-origin requests
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', '*')
            super().end_headers()
    
    try:
        with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
            print(f"✅ Server running at http://{local_ip}:{PORT}/")
            print(f"📁 Serving files from: {os.getcwd()}")
            print(f"🎯 Target file: {FRONTEND_ZIP}")
            print("\n🔄 Waiting for VNC download requests...")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except OSError as e:
        if e.errno == 10048:  # Port already in use
            print(f"❌ Error: Port {PORT} is already in use!")
            print("Try a different port or close the application using port 8000")
        else:
            print(f"❌ Error starting server: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()