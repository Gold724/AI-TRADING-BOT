# 🔧 TERMIUS SERVICE RESTART GUIDE - AI Trading Sentinel

## 🚨 IMMEDIATE ACTION REQUIRED

The VPS network is restored but Flask backend shows **502 Bad Gateway**. Services need manual restart via Termius.

---

## 📱 STEP 1: Connect via Termius

1. **Open Termius App**
2. **Connect to VPS**: `161.97.112.146`
3. **Login**: `root` + your VPS password
4. **Verify Connection**: You should see the Ubuntu prompt

---

## ⚡ STEP 2: Emergency Service Restart

### Copy-paste these commands one by one:

```bash
# 1. Check current service status
echo "=== CURRENT STATUS - $(date) ==="
sudo systemctl status nginx --no-pager
sudo systemctl status trading-bot --no-pager

# 2. Restart Nginx
echo "🔄 Restarting Nginx..."
sudo systemctl restart nginx
echo "✅ Nginx restarted"

# 3. Restart Trading Bot Service
echo "🔄 Restarting Trading Bot..."
sudo systemctl restart trading-bot
echo "✅ Trading-bot restarted"

# 4. Verify services are running
echo "=== POST-RESTART STATUS ==="
sudo systemctl status nginx --no-pager -l
sudo systemctl status trading-bot --no-pager -l

# 5. Test API endpoint locally
echo "=== TESTING API ENDPOINT ==="
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost/api/status
curl -s http://localhost/api/status | head -20
```

---

## 🔍 STEP 3: Verify External Access

After running the restart commands, test from your local machine:

```powershell
# Test API endpoint
Invoke-WebRequest http://161.97.112.146/api/status

# Should return HTTP 200 OK with JSON response
```

---

## 🚨 TROUBLESHOOTING

### If Trading-Bot Service Fails:
```bash
# Check service logs
sudo journalctl -u trading-bot --no-pager -l -n 50

# Check if Python process is running
ps aux | grep python

# Manual Flask startup (if service fails)
cd /root/ai-trading-sentinel
source venv/bin/activate
python backend_main.py &
```

### If Nginx Fails:
```bash
# Check Nginx configuration
sudo nginx -t

# Check Nginx logs
sudo tail -50 /var/log/nginx/error.log

# Restart with verbose output
sudo systemctl restart nginx -l
```

### If API Still Returns 502:
```bash
# Check if Flask is listening on port 5000
sudo netstat -tlnp | grep 5000

# Check firewall
sudo ufw status

# Check processes
sudo ps aux | grep -E '(python|flask|gunicorn)'
```

---

## ✅ SUCCESS INDICATORS

### ✅ Services Running:
```
● nginx.service - A high performance web server
   Active: active (running)

● trading-bot.service - AI Trading Sentinel Bot
   Active: active (running)
```

### ✅ API Responding:
```
HTTP Status: 200
{"status": "running", "timestamp": "..."}
```

### ✅ External Access:
- `http://161.97.112.146/` → Dashboard loads
- `http://161.97.112.146/api/status` → JSON response

---

## 📋 POST-RESTART CHECKLIST

- [ ] Nginx service active
- [ ] Trading-bot service active  
- [ ] API endpoint returns 200 OK
- [ ] Dashboard accessible externally
- [ ] No 502 errors in browser
- [ ] Flask backend responding

---

## 🔄 NEXT STEPS AFTER SUCCESS

1. **Test Live Trading Integration**
2. **Verify Bulenox Login Workflow**
3. **Check Risk Management Systems**
4. **Setup SSH Key Authentication** (to avoid password prompts)
5. **Configure Automated Monitoring**

---

**⚠️ CRITICAL**: Run these commands in Termius NOW to restore full functionality!