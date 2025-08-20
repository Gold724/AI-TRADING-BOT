# 🎯 Simple Termius Commands

## 🚨 VNC Copy-Paste Issue Detected
Your terminal shows copy-paste corruption. Use these **SIMPLE** commands:

## ⚡ Method 1: Single Command
**Type this EXACTLY in Termius:**

```
bash SSH_DEPLOYMENT_FIX.sh
```

## 🔄 Method 2: If File Not Found
**Type these commands ONE BY ONE:**

```
ls -la SSH*
```

```
chmod +x SSH_DEPLOYMENT_FIX.sh
```

```
bash SSH_DEPLOYMENT_FIX.sh
```

## 🆘 Method 3: Manual Fix
**If script fails, type these commands:**

```
sudo systemctl stop nginx
```

```
sudo pkill -f python
```

```
sudo mkdir -p /var/www/html
```

```
echo "<h1>SSH Fixed: 161.97.112.146</h1>" | sudo tee /var/www/html/index.html
```

```
sudo systemctl start nginx
```

## ✅ Expected Results
**After running commands, you should see:**
- "SSH Deployment Complete!"
- URLs for 161.97.112.146
- Services starting

## 🌐 Test URLs
**Open in browser:**
- http://161.97.112.146/
- http://161.97.112.146/api/status

## 🤖 Bulenox Details
- **Username**: BX64883
- **Password**: XujhMzFf6K
- **IP**: 161.97.112.146 (SSH)

**No more copy-paste issues!**