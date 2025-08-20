#!/bin/bash
sudo systemctl stop nginx
sudo pkill -f python
sudo mkdir -p /var/www/html
sudo tee /var/www/html/index.html > /dev/null << 'EOF'
<!DOCTYPE html>
<html>
<head><title>AI Trading Sentinel - VNC</title></head>
<body>
<h1>AI Trading Sentinel - LIVE</h1>
<p>VNC IP: 5.189.145.177</p>
<p>SSH IP: 161.97.112.146</p>
<p>Bulenox: BX64883 (LIVE)</p>
<p>Status: Active</p>
</body>
</html>
EOF
sudo tee /root/backend.py > /dev/null << 'EOF'
from flask import Flask, jsonify
app = Flask(__name__)
@app.route('/')
def status():
    return jsonify({'status': 'active', 'vnc': '5.189.145.177', 'bulenox': 'BX64883'})
@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})
@app.route('/api/status')
def api_status():
    return jsonify({'status': 'active', 'vnc': '5.189.145.177', 'bulenox': 'BX64883'})
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
EOF
sudo tee /etc/nginx/sites-available/default > /dev/null << 'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;
    root /var/www/html;
    index index.html;
    location / {
        try_files $uri $uri/ =404;
    }
    location /api/ {
        proxy_pass http://127.0.0.1:5001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF
sudo python3 /root/backend.py &
sudo systemctl start nginx
sleep 3
curl http://localhost/
curl http://localhost/api/status
echo "VNC URLs:"
echo "Frontend: http://5.189.145.177/"
echo "Backend: http://5.189.145.177/api/status"
echo "Bulenox: BX64883 (LIVE)"