# 🆘 VPS Manual Setup - Type Each Command

## 🚨 CRITICAL: SSH_DEPLOYMENT_FIX.sh Not Found on VPS

**The script exists locally but not on your VPS. Type these commands ONE BY ONE:**

### Step 1: Check Current Directory
```
pwd
```

### Step 2: List Files
```
ls -la
```

### Step 3: Create the Script Manually
```
cat > SSH_DEPLOYMENT_FIX.sh << 'EOF'
#!/bin/bash
echo "Starting SSH Deployment..."
sudo systemctl stop nginx 2>/dev/null
sudo pkill -f python 2>/dev/null
sudo mkdir -p /var/www/html
echo "<h1>SSH Fixed: 161.97.112.146</h1><p>Bulenox: BX64883</p>" | sudo tee /var/www/html/index.html
sudo systemctl start nginx
echo "SSH Deployment Complete!"
echo "Test: http://161.97.112.146/"
EOF
```

### Step 4: Make Executable
```
chmod +x SSH_DEPLOYMENT_FIX.sh
```

### Step 5: Run Script
```
bash SSH_DEPLOYMENT_FIX.sh
```

### Step 6: Test
```
curl http://localhost/
```

## 🌐 Expected Result
- "SSH Deployment Complete!"
- "Test: http://161.97.112.146/"
- HTML content with "SSH Fixed: 161.97.112.146"

## 🤖 Bulenox Details
- **Username**: BX64883
- **Password**: XujhMzFf6K
- **IP**: 161.97.112.146

**Type each command carefully - no copy-paste!**