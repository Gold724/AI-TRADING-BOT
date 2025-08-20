# 🎯 VNC Single Commands - Type Manually

## The Issue
VNC copy-paste is completely broken. Type these commands manually.

## Option 1: Use Script (If Copy-Paste Works)
```
bash VNC_MINIMAL_SETUP.sh
```

## Option 2: Manual Commands (Type Each One)

### 1. Stop nginx:
```
sudo systemctl stop nginx
```

### 2. Kill python:
```
sudo pkill -f python
```

### 3. Make directory:
```
sudo mkdir -p /var/www/html
```

### 4. Create simple HTML:
```
echo '<html><body><h1>AI Trading</h1><p>VNC: 5.189.145.177</p></body></html>' | sudo tee /var/www/html/index.html
```

### 5. Create simple backend:
```
echo 'from flask import Flask, jsonify
app = Flask(__name__)
@app.route("/")
def status():
    return jsonify({"status": "active"})
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)' | sudo tee /root/backend.py
```

### 6. Start backend:
```
sudo python3 /root/backend.py &
```

### 7. Start nginx:
```
sudo systemctl start nginx
```

### 8. Test:
```
curl http://localhost/
```

## Expected Result:
- Frontend: http://5.189.145.177/
- Backend working
- Bulenox: BX64883 (LIVE)

## If Still Failing:
1. Check if files exist: `ls -la /var/www/html/`
2. Check nginx status: `sudo systemctl status nginx`
3. Check python process: `ps aux | grep python`

**Type commands manually - don't copy-paste!**