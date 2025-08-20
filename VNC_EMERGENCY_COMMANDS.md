# 🚨 VNC Emergency Commands - One at a Time

## The Problem
VNC copy-paste keeps corrupting. Execute these commands ONE BY ONE.

## Step 1: Stop Services
```bash
sudo systemctl stop nginx
```

## Step 2: Kill Python
```bash
sudo pkill -f python
```

## Step 3: Create Directory
```bash
sudo mkdir -p /var/www/html
```

## Step 4: Create Frontend (Copy this EXACTLY)
```bash
sudo tee /var/www/html/index.html > /dev/null << 'EOF'
<!DOCTYPE html>
<html>
<head><title>AI Trading Sentinel</title></head>
<body>
<h1>AI Trading Sentinel - LIVE</h1>
<p>VNC IP: 5.189.145.177</p>
<p>Bulenox: BX64883 (LIVE)</p>
<p>Status: Active</p>
</body>
</html>
EOF
```

## Step 5: Create Backend (Copy this EXACTLY)
```bash
sudo tee /root/backend.py > /dev/null << 'EOF'
from flask import Flask, jsonify
app = Flask(__name__)
@app.route('/')
def status():
    return jsonify({'status': 'active'})
@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
EOF
```

## Step 6: Start Backend
```bash
sudo python3 /root/backend.py &
```

## Step 7: Start Nginx
```bash
sudo systemctl start nginx
```

## Step 8: Test
```bash
curl http://localhost/
```

## Expected URLs:
- **Frontend**: http://5.189.145.177/
- **Backend**: http://5.189.145.177/api/status
- **Bulenox**: BX64883 (LIVE)

## If Commands Fail:
1. Type each command manually
2. Don't copy-paste multiple lines
3. Wait for each command to complete

**COPY ONE COMMAND AT A TIME!**