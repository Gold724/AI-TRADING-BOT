#!/bin/bash
echo "Stopping services..."
sudo systemctl stop nginx
sudo pkill -f python
echo "Creating files..."
sudo mkdir -p /var/www/html
echo '<html><body><h1>AI Trading Sentinel</h1><p>VNC: 5.189.145.177</p><p>Bulenox: BX64883</p></body></html>' | sudo tee /var/www/html/index.html
echo 'from flask import Flask, jsonify
app = Flask(__name__)
@app.route("/")
def status():
    return jsonify({"status": "active", "vnc": "5.189.145.177"})
@app.route("/health")
def health():
    return jsonify({"status": "healthy"})
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)' | sudo tee /root/backend.py
echo "Starting services..."
sudo python3 /root/backend.py &
sudo systemctl start nginx
sleep 2
echo "Testing..."
curl http://localhost/
echo "Done. Check: http://5.189.145.177/"