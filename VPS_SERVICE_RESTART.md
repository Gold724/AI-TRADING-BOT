# 🔄 VPS SERVICE RESTART - Post Network Recovery

## ✅ NETWORK STATUS: RESTORED
- **Ping to 8.8.8.8**: ✅ Working (3-4ms latency)
- **HTTP requests**: ✅ Working (Google accessible)
- **Network interface**: ✅ eth0 configured with 161.97.112.146/18

---

## 🚀 RESTART ALL SERVICES

**Copy/paste these commands in VPS console:**

```bash
# 1. Restart SSH service
sudo systemctl restart ssh
sudo systemctl status ssh

# 2. Restart Nginx web server
sudo systemctl restart nginx
sudo systemctl status nginx

# 3. Restart trading bot service
sudo systemctl restart trading-bot
sudo systemctl status trading-bot

# 4. Check all services are running
sudo systemctl status ssh nginx trading-bot

# 5. Verify ports are listening
ss -tlnp | grep -E ':22|:80|:443|:5000'

# 6. Test internal connectivity
curl -I http://localhost/
curl http://localhost/api/status
```

---

## 🔍 VERIFICATION TESTS

### Internal Tests (on VPS)
```bash
# Test web server
curl -I http://localhost/
# Expected: HTTP/1.1 200 OK

# Test API endpoint
curl http://localhost/api/status
# Expected: JSON response with bot status

# Test SSH is listening
ss -tlnp | grep :22
# Expected: LISTEN on port 22
```

### External Tests (from your computer)
```powershell
# Test ping
ping 161.97.112.146
# Expected: Replies with <10ms

# Test SSH port
Test-NetConnection 161.97.112.146 -Port 22
# Expected: TcpTestSucceeded: True

# Test web dashboard
Invoke-WebRequest http://161.97.112.146/
# Expected: StatusCode 200
```

---

## 🎯 SUCCESS INDICATORS

**All services restored when:**
- ✅ SSH: `systemctl status ssh` shows "active (running)"
- ✅ Nginx: `systemctl status nginx` shows "active (running)"
- ✅ Trading Bot: `systemctl status trading-bot` shows "active (running)"
- ✅ External ping works from your computer
- ✅ Termius connects successfully
- ✅ Web dashboard loads: http://161.97.112.146/
- ✅ API responds: http://161.97.112.146/api/status

---

## 🔧 IF SERVICES FAIL TO START

### SSH Issues
```bash
# Check SSH config
sudo sshd -t
# Fix any config errors
sudo nano /etc/ssh/sshd_config
```

### Nginx Issues
```bash
# Test Nginx config
sudo nginx -t
# Check error logs
sudo tail -f /var/log/nginx/error.log
```

### Trading Bot Issues
```bash
# Check service logs
sudo journalctl -u trading-bot -f
# Check Python environment
cd /opt/ai-trading-sentinel
source venv/bin/activate
python -c "import flask; print('Flask OK')"
```

---

## 📱 NEXT STEPS

1. **Test Termius Connection**: Try connecting from your computer
2. **Verify Web Dashboard**: Open http://161.97.112.146/ in browser
3. **Check API Endpoints**: Test all trading bot APIs
4. **Monitor Logs**: Watch for any errors in service logs
5. **Run Trading Tests**: Execute end-to-end trading workflow

---

**🎉 RECOVERY COMPLETE**: Once all services show "active (running)" and external tests pass, your AI Trading Sentinel is fully operational!